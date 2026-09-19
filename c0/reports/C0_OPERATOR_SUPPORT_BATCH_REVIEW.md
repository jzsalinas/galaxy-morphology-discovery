# Revisión del diagnóstico A/B humano — 2026-09-18

## OBSERVED

C0_OPERATOR_SUPPORT_OK confirmado. Los 36 checkpoints se verificaron contra el resumen; hashes de JSON/NPZ, procedencia, copia de implementación y orden de los diez objetos primarios antes de ranks 3/5 coinciden. No se ejecutó nuevamente el lote. El lote registró 147269237 bytes leídos y 45946072 escritos. Los contadores de red permanecen en 465348528 bytes, 383 solicitudes de datos y 936 HTTP totales.

### A — operador, soporte común parcial

| Variante prefijada | L2 relativo mínimo | Mediana | Máximo |
|---|---:|---:|---:|
| Analítica | 7.2041e-7 | 2.1340e-6 | 5.9655e-6 |
| Coordenadas float32 | 7.9843e-8 | 1.4467e-7 | 4.4965e-7 |
| LUT C, coordenadas directas | 4.6086e-8 | 7.2052e-8 | 9.7444e-8 |
| LUT C, spline local | 4.6086e-8 | 7.0530e-8 | 8.6876e-8 |

La energía residual de la última variante es 0.00011650–0.01012845 veces la de la referencia analítica: reducción de 98.9872–99.9883%, sin ajustes. La spline local no mejora la norma frente a coordenadas directas en 14/36 combinaciones. No se selecciona retrospectivamente una variante por menor residual.

Ninguna combinación tiene igualdad exacta en todo el soporte común. De 2050500 píxeles comparados, 971265 tienen residual cero; 539232 positivo y 540003 negativo. RMS agregado 1.08762e-8, en unidades numéricas del array, no certificadas para el cutout. La diferencia por invertir el orden de bricks es cero en este subconjunto; con una o dos contribuciones esto no prueba invariancia para más bricks.

| Partición descriptiva | Píxeles | RMS de residual LUT/spline |
|---|---:|---:|
| Borde de tres píxeles | 5460 | 4.28473e-8 |
| Interior | 2045040 | 1.06633e-8 |
| Solapamiento candidato | 175500 | 1.59153e-8 |
| Un solo brick candidato | 1875000 | 1.02788e-8 |

El soporte no cubre todos los bordes. La máscara común sigue siendo parcial: 62500 píxeles por banda para los diez objetos primarios, 40750 para rank 3 y 17750 para rank 5. No se confunde el soporte disponible según B con píxeles efectivamente comparados en A.

RMS por banda: g=8.96542e-9, r=7.42972e-9, z=1.48086e-8. En cuartiles de intensidad observada, Q0/Q1/Q2/Q3: 7.70277e-10, 4.07928e-10, 4.86338e-10, 2.17294e-8. El cuartil superior concentra mayor error absoluto; eso no identifica por sí solo su causa. Los cuatro cuadrantes tienen RMS entre 2.66841e-9 y 1.55209e-8; no se concluye ausencia de estructura espacial a partir de una norma global. Desgloses por objeto, intensidad de referencia, distribuciones firmadas y coordenadas están en el resumen/NPZ conservados.

### B — soporte disponible frente al comparado

Para 33/36 combinaciones, el inventario encuentra todo el soporte candidato en los fragmentos y píxeles locales existentes. Esto incluye rank 3. Aún falta extraer/reutilizar ese soporte para contrastar el cutout completo: el inventario no realizó tal contraste.

Para rank 5, g/r/z, hay soporte local para 64768/65536 píxeles por banda; faltan muestras necesarias para 768 por banda. Cierre condicionado al modelo conocido: 172146 bytes, repartidos en los seis intervalos siguientes, extremos inclusivos. URL completa, ETag, tamaño total, hashes de caché y heap están en C0_OPERATOR_SUPPORT_BATCH_INVENTORY.json.

| Brick | Banda | Primer byte | Último byte | Bytes |
|---|---|---:|---:|---:|
| 1949p190 | g | 8335334 | 8345282 | 9949 |
| 1949p190 | r | 8760970 | 8772763 | 11794 |
| 1949p190 | z | 10370289 | 10382915 | 12627 |
| 1951p190 | g | 8604864 | 8645075 | 40212 |
| 1951p190 | r | 8763291 | 8810434 | 47144 |
| 1951p190 | z | 10920730 | 10971149 | 50420 |

Cada intervalo del brick 1951p190 completaría por sí solo el soporte de 531 píxeles de su banda. Otros 237 requieren también el intervalo correspondiente de 1949p190; este último por sí solo no completa ningún píxel. No sumar coberturas marginales como si fueran independientes. Ambos juntos completan los 768 por banda bajo el modelo candidato.

Los seis recursos tienen un intento restante cada uno bajo la política conservadora actual (HEAD y rangos anteriores ya contabilizados). Los intervalos no repiten bytes cacheados y están dentro de presupuesto; un fallo adicional podría agotar el recurso. No se flexibilizó esa política.

## DOCUMENTED

El protocolo exige >=95/96 objetos recuperables, bandas, centro dentro de un píxel, release/WCS/unidad verificables y contraste compatible salvo remuestreo documentado para PASS. No hay tolerancia científica nueva para aceptar estos residuales.

FAIL requiere la evidencia adversa congelada (menos de 90 recuperables, release no verificable, unidades opacas o incompatibilidad con el coadd). Un residual frente a una implementación no idéntica no establece esa incompatibilidad por sí solo. Si al cerrar la investigación no se resuelve semántica/procedencia/calibración suficiente, INCONCLUSIVE implica STOP según addendum. REVISE conserva las condiciones de cabeceras incompletas/discrepancia explicable y propuesta explícita de extracción desde bricks; no se aplica una migración silenciosa.

## INFERRED

Las transiciones prefijadas del operador reducen reproduciblemente gran parte de la discrepancia de la referencia analítica. Esto demuestra cambios numéricos al incorporar detalles conocidos; no demuestra atribución causal exclusiva del residual original a float32/LUT ni identidad del servicio. El residual final sigue sin estar explicado por una cota de error independiente del resultado.

En este inventario concreto, el mínimo condicionado de peticiones es seis: hacen falta bytes de seis URLs distintas y una petición single-range por URL alcanza la cota inferior. No se necesita suponer multipart para alcanzar esa cota. El campo genérico absolute_minimum_requests del inventario deja abierta la cuestión en general; esa cautela no impide esta deducción particular. Los 172146 bytes son payload mínimo del modelo de tiles/soporte conocido, no una prueba de que toda ruta posible del servicio requiera esa adquisición.

## UNRESOLVED y decisión previa a adquirir

No se ha demostrado equivalencia funcional exacta completa, identidad de versión desplegada, equivalencia de spline local/FITPACK y WCS Astropy/astrometry.net, selección exhaustiva de bricks ni unidades del cutout normal. La compatibilidad numérica observada no certifica esas propiedades.

C0-C sigue PENDING. La evidencia actual no basta para PASS y este diagnóstico no demuestra FAIL. No se cierra formalmente el Gate como INCONCLUSIVE mientras queda pendiente el contraste explícitamente identificado; si se cierra sin resolverlo, corresponde INCONCLUSIVE/STOP.

Siguiente paso científicamente justificado: aprovechar primero el soporte ya cacheado para contrastar interior, bordes y solapamientos sin nuevas adquisiciones, manteniendo las variantes y registrando soporte ausente de rank 5. Es un diagnóstico nuevo de soporte ampliado, no repetición del lote anterior. Su ejecución bulk requerirá otro handoff humano. Solo después de revisar ese contraste se podrá decidir si recuperar los seis intervalos aporta evidencia necesaria para C0-C o deja intacto un bloqueo semántico que obligue a cerrar INCONCLUSIVE.

No se prepara ni ejecuta adquisición en esta revisión. Ningún tamaño pequeño convierte automáticamente una descarga en científicamente necesaria. SDSS y los demás productos permanecen fuera de esta etapa.
