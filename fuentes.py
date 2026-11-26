
import pandas as pd
import json
import requests
from pathlib import Path


def extraer_fuentes(ruta_base):

    ruta_base = Path(ruta_base)

    # 1. Restaurantes
    restaurantes = pd.read_excel(
        ruta_base / "restaurantes.xlsx",
        header=2
    )

    # 2. Riders
    with open(
        ruta_base / "riders_api.json",
        encoding="utf-8"
    ) as f:
        riders_json = json.load(f)

    riders = pd.json_normalize(riders_json["data"])

    riders = riders.rename(columns={
        "id": "rider_id",
        "perfil.nombre": "nombre",
        "perfil.vehiculo": "vehiculo"
    })

    riders["alta"] = pd.to_datetime(riders["alta"])

    # 3. Zonas
    zonas = pd.read_csv(ruta_base / "zonas.csv")

    # 4. Clima
    with open(
        ruta_base / "clima_cbba_2025.json",
        encoding="utf-8"
    ) as f:
        clima_json = json.load(f)

    clima = pd.DataFrame(clima_json["daily"])

    clima = clima.rename(columns={
        "time": "fecha",
        "temperature_2m_mean": "temperatura_media",
        "precipitation_sum": "lluvia_mm"
    })

    clima["fecha"] = pd.to_datetime(clima["fecha"])

    # 5. Feriados
    url = "https://date.nager.at/api/v3/PublicHolidays/2025/BO"

    try:
        respuesta = requests.get(url, timeout=15)
        respuesta.raise_for_status()

        feriados_json = respuesta.json()

        if not isinstance(feriados_json, list) or not feriados_json:
            raise ValueError("Respuesta inválida o vacía")

        fuente_feriados = "api"

    except (requests.RequestException, ValueError):

        with open(
            ruta_base / "feriados_bo_2025_respaldo.json",
            encoding="utf-8"
        ) as f:
            feriados_json = json.load(f)

        fuente_feriados = "respaldo"

    feriados = pd.DataFrame(feriados_json)

    feriados = feriados[
        ["date", "localName", "countryCode", "global"]
    ].copy()

    feriados = feriados.rename(columns={
        "date": "fecha",
        "localName": "nombre_feriado",
        "countryCode": "pais",
        "global": "nacional"
    })

    feriados["fecha"] = pd.to_datetime(feriados["fecha"])

    return restaurantes, riders, zonas, clima, feriados, fuente_feriados
