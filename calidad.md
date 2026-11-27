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

## Finalidad de la capa bronce

Trazabilidad: permite conocer el origen de cada registro y conservar los datos sin limpiar.
Reprocesamiento: permite volver a aplicar las transformaciones sin perder la información original.

## Reglas de limpieza (capa plata)

Empezamos con 76.232 filas en bronce. Al quitar los 900 duplicados de abril quedaron 75.332 pedidos únicos.
Después sacamos 140 pedidos de un restaurante que no está en el catálogo y quedaron 75.192 pedidos en plata.
En total hay 1.040 filas en rechazos_pedidos.

| Mes | Problema | Filas | Regla que apliqué |
|---|---|---:|---|
| Enero | La fecha venía como número de segundos | 6.103 | Detecté los valores que eran solo dígitos y los convertí a fecha. No resté la zona horaria porque ya venían en hora de Bolivia |
| Febrero | El monto venía como texto, por ejemplo Bs 15,00 | 5.806 | Quité el Bs y los espacios, cambié la coma por punto y lo pasé a número |
| Abril | Pedidos repetidos | 900 | Me quedé con la fila del estado final y mandé la copia en_camino a rechazos_pedidos |
| Junio | Zonas escritas de varias formas como SACABA, cala cala o Quilla | 951 | Pasé todo a minúsculas sin tildes, espacios ni guiones y lo comparé con zonas.csv. Quilla lo agregué a mano |
| Agosto | Tiempos de 999 minutos y negativos | 160 | Dejé el tiempo vacío y marqué la fila como tiempo_invalido. El pedido se queda |
| Septiembre | Calificaciones de 1 a 10 desde el 15/09 | 2.299 | Desde esa fecha dividí entre 2 y redondeé hacia arriba |
| Noviembre | El archivo era JSON y la calificación venía como 5.0 | 6.936 | Lo leí como texto en bronce y lo pasé a número en plata |
| Diciembre | Columna nueva version_app y riders vacíos | 7.884 y 300 | Se quedan así y los vacíos quedan como nulos |
| Todos | Restaurante R041 que no está en el catálogo | 140 | Los saqué de plata  |
| Bronce | Vacíos guardados como texto <NA> | 300 riders y 67.448 en version_app |

## Decisiones del equipo

### Decisión 1: pedidos del restaurante R041 (no existe en el catálogo)

**Qué encontramos.** 140 pedidos son del restaurante R041 que no aparece en restaurantes.xlsx.

**Qué decidimos.** Excluirlos y registrarlos en rechazos_pedidos con el motivo
restaurante_no_existe_en_catalogo
**Por qué.**
Sin catálogo no podemos calcular comisión ni tipo de cocina.
Un pedido de un restaurante que no podemos identificar no se puede asociar a un responsable ni auditar.

**Qué costo tiene.** Los totales bajan de 75.332 pedidos y Bs 4.421.271 a 75.192 pedidos y Bs 4.413.314.

**Pendiente.** Pedir a Comercial que confirme qué es R041
### Decisión 2: tiempos de 999 y negativos

No borré los pedidos, solo dejé vacío el tiempo. El cliente sí compró y si borraba las 160 filas
cambiaba el total de ventas.

### Decisión 3: regla de pandera más importante para Valeria

La regla más importante es que pedido_id sea único. Si falla, se cuentan pedidos y ventas de más.
Pasó en abril: 900 pedidos estaban dos veces y sin quitarlos las ventas habrían sido Bs 4.473.518 en vez
de Bs 4.421.271, unos Bs 52.000 de más. Valeria usa estos totales para decidir cuánto crece el negocio y
dónde invertir, y con cifras infladas podría decidir mal. Las otras reglas cuidan análisis puntuales,
pero esta cuida todos los números a la vez.

