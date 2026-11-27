import re
import unicodedata

import numpy as np
import pandas as pd

VACIOS_TEXTO = ["<NA>", "nan", "NaN", "None", "null", ""]


def _clave(x):
    """minúsculas, sin tildes, sin espacios ni guiones: 'Cala-Cala ' -> 'calacala'"""
    x = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode()
    return re.sub(r"[\s\-_]+", "", x.lower())


def limpiar(bronce, zonas, catalogo):
    """bronce (todo texto) -> (plata, rechazos).
    zonas: lista de las 12 zonas oficiales. catalogo: DataFrame de restaurantes.xlsx (con cod_rest)."""
    plata = bronce.copy().reset_index(drop=True)

    # 1) fechas (enero viene como epoch en segundos)
    s = plata["fecha_hora"].astype("string").str.strip()
    es_epoch = s.str.fullmatch(r"\d{9,11}").fillna(False)
    fechas = pd.Series(pd.NaT, index=plata.index, dtype="datetime64[ns]")
    fechas[es_epoch] = pd.to_datetime(s[es_epoch].astype("int64"), unit="s")
    fechas[~es_epoch] = pd.to_datetime(s[~es_epoch], errors="coerce")
    plata["fecha_hora"] = fechas

    # 2) montos (febrero: "Bs 15,00")
    m = plata["monto_bs"].astype("string").str.strip()
    m = m.str.replace(r"(?i)bs\.?", "", regex=True)
    m = m.str.replace(r"\s", "", regex=True)
    m = m.str.replace(",", ".", regex=False)
    plata["monto_bs"] = pd.to_numeric(m, errors="coerce").astype("float64")

    # 3) zonas (junio: apodos y mayúsculas)
    mapa = {_clave(z): z for z in zonas}
    mapa["quilla"] = "Quillacollo"
    plata["zona_entrega"] = plata["zona_entrega"].map(
        lambda x: mapa.get(_clave(x)) if pd.notna(x) else None)

    # 4) duplicados (abril: gana el estado final sobre "en_camino")
    prioridad = plata["estado"].map({"entregado": 0, "cancelado": 0, "en_camino": 1}).fillna(2)
    ordenado = plata.assign(_p=prioridad).sort_values(["pedido_id", "_p"], kind="stable")
    es_copia = ordenado.duplicated("pedido_id", keep="first")
    descartadas = ordenado[es_copia].drop(columns="_p").assign(
        motivo="duplicado_estado_intermedio_en_camino")
    plata = ordenado[~es_copia].drop(columns="_p").reset_index(drop=True)

    # 5) numéricos y tiempos imposibles (agosto)
    for c in ["costo_envio_bs", "propina_bs", "tiempo_entrega_min", "calificacion"]:
        plata[c] = pd.to_numeric(plata[c], errors="coerce").astype("float64")
    malo = plata["tiempo_entrega_min"].notna() & (
        (plata["tiempo_entrega_min"] <= 0) | (plata["tiempo_entrega_min"] > 120))
    plata["tiempo_invalido"] = malo
    plata.loc[malo, "tiempo_entrega_min"] = np.nan

    # 6) escala 1-10 de septiembre (desde el 15/09)
    sep = plata["archivo_origen"].str.contains("_09")
    en_escala_10 = sep & (plata["fecha_hora"] >= "2025-09-15")
    plata.loc[en_escala_10, "calificacion"] = np.ceil(plata.loc[en_escala_10, "calificacion"] / 2)

    # 7) vacíos guardados como texto "<NA>" en la bronce -> vacío real
    cols_texto = plata.select_dtypes(exclude=["number", "datetime", "bool"]).columns
    for c in cols_texto:
        plata[c] = plata[c].where(~plata[c].isin(VACIOS_TEXTO), None)

    # 8) restaurantes que no existen en el catálogo (R041): se sacan y se registran
    huerf = ~plata["cod_rest"].isin(catalogo["cod_rest"])
    huerfanos = plata[huerf].assign(motivo="restaurante_no_existe_en_catalogo")
    plata = plata[~huerf].reset_index(drop=True)

    # rechazos: todo como texto, con vacíos reales
    rechazos = pd.concat([descartadas, huerfanos], ignore_index=True).astype(str)
    rechazos = rechazos.mask(rechazos.isin(["<NA>", "nan", "NaT", "None"]))
    return plata, rechazos
