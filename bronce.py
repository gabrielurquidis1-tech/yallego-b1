
import pandas as pd
import json
from pathlib import Path

def cargar_bronce(con, ruta_pedidos):

    archivos = sorted(Path(ruta_pedidos).glob("*"))
    dataframes = []

    for archivo in archivos:

        # Leer CSV sin convertir sus valores a números
        if archivo.suffix == ".csv":
            df = pd.read_csv(
                archivo,
                dtype=str,
                keep_default_na=False,
                na_values=[""]
            )

        # Leer JSON como texto
        elif archivo.suffix == ".json":
            with open(archivo, encoding="utf-8") as f:
                df = pd.DataFrame(
                    json.load(f),
                    dtype="string"
                )

        else:
            continue

        # Registrar la procedencia de cada fila
        df["archivo_origen"] = archivo.name

        dataframes.append(df)

    # Consolidar todos los meses
    bronce = pd.concat(
        dataframes,
        ignore_index=True
    ).astype("string")

    # Registrar el DataFrame en DuckDB
    con.register("df_bronce", bronce)

    # Crear o reemplazar la tabla
    con.execute("""
        CREATE OR REPLACE TABLE bronce_pedidos AS
        SELECT * FROM df_bronce
    """)

    con.unregister("df_bronce")

    return bronce
