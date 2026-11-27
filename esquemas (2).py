import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema


def construir_esquema(zonas, catalogo):
    return DataFrameSchema(
        {
            "pedido_id": Column(str, Check.str_matches(r"^P\d{6}$"), unique=True),
            "fecha_hora": Column(pa.DateTime, Check.in_range(pd.Timestamp("2025-01-01"),
                                                             pd.Timestamp("2025-12-31 23:59:59"))),
            "zona_entrega": Column(str, Check.isin(list(zonas))),
            "rider_id": Column(str, Check.str_matches(r"^RD\d{3}$"), nullable=True),
            "monto_bs": Column(float, Check.gt(0)),
            "costo_envio_bs": Column(float, Check.ge(0)),
            "propina_bs": Column(float, Check.ge(0)),
            "tiempo_entrega_min": Column(float, Check.in_range(1, 120), nullable=True),
            "estado": Column(str, Check.isin(["entregado", "cancelado"])),
            "calificacion": Column(float, Check.in_range(1, 5), nullable=True),
            "metodo_pago": Column(str, Check.isin(["QR", "efectivo", "tarjeta"])),
            "cod_rest": Column(str, Check.isin(catalogo["cod_rest"].tolist())),
        },
        checks=[
            Check(lambda df: ~((df["estado"] == "cancelado") & df["tiempo_entrega_min"].notna()),
                  error="cancelado_con_tiempo_de_entrega"),
            Check(lambda df: ~((df["estado"] == "cancelado") & df["calificacion"].notna()),
                  error="cancelado_con_calificacion"),
        ],
        strict=False,
    )


def validar(plata, zonas, catalogo):
    """Valida con lazy=True: junta todos los errores. Lanza SchemaErrors si algo falla."""
    construir_esquema(zonas, catalogo).validate(plata, lazy=True)
    return True
