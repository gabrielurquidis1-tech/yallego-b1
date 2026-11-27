import pandas as pd
def _limpiar_columnas(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df.dropna(how="all").reset_index(drop=True)


def cargar_plata_fuentes(con, restaurantes, riders, zonas, clima, feriados, fuente_feriados):
    """Crea las tablas plata de las fuentes complementarias en DuckDB."""

    rest = _limpiar_columnas(restaurantes).drop_duplicates()
    con.register("df_rest", rest)
    con.execute("CREATE OR REPLACE TABLE plata_restaurantes AS SELECT * FROM df_rest")
    con.unregister("df_rest")

    rid = _limpiar_columnas(riders).drop_duplicates(subset=["rider_id"])
    con.register("df_rid", rid)
    con.execute("CREATE OR REPLACE TABLE plata_riders AS SELECT * FROM df_rid")
    con.unregister("df_rid")

    zon = _limpiar_columnas(zonas).drop_duplicates()
    con.register("df_zon", zon)
    con.execute("CREATE OR REPLACE TABLE plata_zonas AS SELECT * FROM df_zon")
    con.unregister("df_zon")

    cli = _limpiar_columnas(clima)
    cli["fecha"] = pd.to_datetime(cli["fecha"]).dt.date
    con.register("df_cli", cli)
    con.execute("CREATE OR REPLACE TABLE plata_clima AS SELECT * FROM df_cli")
    con.unregister("df_cli")

    fer = _limpiar_columnas(feriados)
    fer["fecha"] = pd.to_datetime(fer["fecha"]).dt.date
    fer["fuente"] = fuente_feriados
    con.register("df_fer", fer)
    con.execute("CREATE OR REPLACE TABLE plata_feriados AS SELECT * FROM df_fer")
    con.unregister("df_fer")


def construir_oro(con):
    """Crea oro_diario y oro_pedidos_enriquecido a partir de las tablas plata."""

    con.execute("""
        CREATE OR REPLACE TABLE oro_diario AS
        WITH calendario AS (
            SELECT CAST(d AS DATE) AS fecha
            FROM generate_series(DATE '2025-01-01', DATE '2025-12-31', INTERVAL 1 DAY) AS t(d)
        ),
        pedidos AS (
            SELECT
                CAST(fecha_hora AS DATE)                                  AS fecha,
                COUNT(*)                                                  AS pedidos,
                COUNT(*) FILTER (WHERE estado = 'entregado')              AS pedidos_entregados,
                COUNT(*) FILTER (WHERE estado = 'cancelado')              AS pedidos_cancelados,
                SUM(monto_bs)                                             AS gmv,
                SUM(costo_envio_bs) FILTER (WHERE estado = 'entregado')   AS envios_bs,
                AVG(tiempo_entrega_min)                                   AS tiempo_prom_min,
                AVG(calificacion)                                         AS calificacion_prom
            FROM plata_pedidos
            GROUP BY 1
        ),
        feriados AS (SELECT DISTINCT fecha FROM plata_feriados)
        SELECT
            c.fecha,
            COALESCE(p.pedidos, 0)             AS pedidos,
            COALESCE(p.pedidos_entregados, 0)  AS pedidos_entregados,
            COALESCE(p.pedidos_cancelados, 0)  AS pedidos_cancelados,
            COALESCE(p.gmv, 0)                 AS gmv,
            COALESCE(p.envios_bs, 0)           AS envios_bs,
            p.tiempo_prom_min,
            p.calificacion_prom,
            cl.lluvia_mm,
            (cl.lluvia_mm >= 1)                AS dia_lluvioso,
            (f.fecha IS NOT NULL)              AS feriado,
            dayofweek(c.fecha)                 AS dia_semana,
            (dayofweek(c.fecha) = 3)           AS es_miercoles,
            (c.fecha >= DATE '2025-07-02')     AS post_promo,
            (dayofweek(c.fecha) = 3 AND c.fecha >= DATE '2025-07-02') AS promo_miercoles
        FROM calendario c
        LEFT JOIN pedidos p       ON p.fecha = c.fecha
        LEFT JOIN plata_clima cl  ON cl.fecha = c.fecha
        LEFT JOIN feriados f      ON f.fecha = c.fecha
        ORDER BY c.fecha
    """)

    cols_r = [c for c in con.sql("SELECT * FROM plata_restaurantes LIMIT 0").columns if c != "cod_rest"]
    cols_d = [c for c in con.sql("SELECT * FROM plata_riders LIMIT 0").columns if c != "rider_id"]
    sel_r = ", ".join(f'r."{c}" AS rest_{c}' for c in cols_r)
    sel_d = ", ".join(f'd."{c}" AS rider_{c}' for c in cols_d)

    con.execute(f"""
        CREATE OR REPLACE TABLE oro_pedidos_enriquecido AS
        SELECT
            p.*,
            CAST(p.fecha_hora AS DATE)  AS fecha,
            hour(p.fecha_hora)          AS hora,
            dayofweek(p.fecha_hora)     AS dia_semana,
            cl.lluvia_mm,
            {sel_r},
            {sel_d}
        FROM plata_pedidos p
        LEFT JOIN plata_clima cl        ON cl.fecha = CAST(p.fecha_hora AS DATE)
        LEFT JOIN plata_restaurantes r  ON r.cod_rest = p.cod_rest
        LEFT JOIN plata_riders d        ON d.rider_id = p.rider_id
    """)
