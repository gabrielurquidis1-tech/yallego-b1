from pathlib import Path
import duckdb

from bronce import cargar_bronce
from fuentes import extraer_fuentes
from plata import limpiar
from esquemas import validar as validar_esquema
from oro import cargar_plata_fuentes, construir_oro

# AJUSTAR: carpetas donde quedó el zip descomprimido
RUTA_PEDIDOS = "YaLlego/raw/pedidos"
RUTA_FUENTES = "YaLlego"
COL_ZONA = "zona"          # AJUSTAR: nombre de la columna de zonas.csv con el nombre de la zona
DB = "yallego.duckdb"


def extraer(con):
    bronce = cargar_bronce(con, RUTA_PEDIDOS)
    restaurantes, riders, zonas, clima, feriados, fuente = extraer_fuentes(RUTA_FUENTES)
    print(f"Bronce: {len(bronce)} filas | feriados desde: {fuente}")
    return bronce, restaurantes, riders, zonas, clima, feriados, fuente


def transformar(bronce, restaurantes, zonas):
    zonas_lista = zonas[COL_ZONA].tolist()
    plata, rechazos = limpiar(bronce, zonas_lista, restaurantes)
    return plata, rechazos, zonas_lista

def validar(plata, zonas_lista, restaurantes):
    validar_esquema(plata, zonas_lista, restaurantes)   # lanza error si algo falla
    print("Pandera: plata_pedidos validada")


def cargar(con, plata, rechazos, restaurantes, riders, zonas, clima, feriados, fuente):
    con.register("df_plata", plata)
    con.execute("CREATE OR REPLACE TABLE plata_pedidos AS SELECT * FROM df_plata")
    con.unregister("df_plata")

    con.register("df_rech", rechazos)
    con.execute("CREATE OR REPLACE TABLE rechazos_pedidos AS SELECT * FROM df_rech")
    con.unregister("df_rech")

    cargar_plata_fuentes(con, restaurantes, riders, zonas, clima, feriados, fuente)
    construir_oro(con)
def main():
    # Empezar desde cero (idempotencia)
    for f in (DB, DB + ".wal"):
        Path(f).unlink(missing_ok=True)
    con = duckdb.connect(DB)

    bronce, restaurantes, riders, zonas, clima, feriados, fuente = extraer(con)
    plata, rechazos, zonas_lista = transformar(bronce, restaurantes, zonas)
    validar(plata, zonas_lista, restaurantes)
    cargar(con, plata, rechazos, restaurantes, riders, zonas, clima, feriados, fuente)

    print("\n=== Filas por tabla ===")
    for t in con.sql("SHOW TABLES").fetchall():
        n = con.sql(f"SELECT COUNT(*) FROM {t[0]}").fetchone()[0]
        print(f"{t[0]}: {n}")
    con.close()


if __name__ == "__main__":
    main()
