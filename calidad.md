# Calidad de datos - YaLlegó Delivery

## Diagnóstico de los archivos originales

| Mes        | Problema                           |   Observado |
|:-----------|:-----------------------------------|------------:|
| Enero      | Timestamp Unix                     |        6103 |
| Febrero    | Montos como texto                  |        5806 |
| Abril      | Duplicados por pedido_id           |         900 |
| Junio      | Zonas inconsistentes               |         951 |
| Agosto     | Tiempos negativos o de 999 minutos |         160 |
| Septiembre | Calificaciones en nueva escala     |        2299 |
| Noviembre  | Registros en formato JSON          |        6936 |
| Diciembre  | Columna adicional version_app      |        7884 |
| Diciembre  | Riders faltantes                   |         300 |


## ¿Qué mes me pareció más raro y por qué?

El mes mas raro es septiembre porque presenta un problema de calidad difícil de detectar: el cambio en la escala de calificación de 1–5 a 1–10.
A diferencia de los duplicados o los formatos incorrectos, este problema no necesariamente genera errores al ejecutar el código, pero puede distorsionar silenciosamente los resultados del análisis.
Además, algunas calificaciones de la nueva escala son inferiores o iguales a 5, por lo que no basta con identificar los valores superiores a 5.

## Reglas de limpieza y justificaciones

Pendiente de completar durante la capa plata.

## Finalidad de la capa bronce

Trazabilidad: permite conocer el origen de cada registro y conservar los datos sin limpiar.
Reprocesamiento: permite volver a aplicar las transformaciones sin perder la información original.
