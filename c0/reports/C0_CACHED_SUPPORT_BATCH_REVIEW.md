# Revisión del soporte cacheado — 2026-09-18

## OBSERVED

Confirmado C0_CACHED_SUPPORT_OK, exit 0. Verificados 36 checkpoints JSON/NPZ por SHA256, igualdad de cada resultado con el resumen, orden congelado y hashes de archivos de procedencia contra disco. No se repitió el lote. IO registrado: 492583555 bytes leídos y 108855059 escritos. Red sin cambios: 465348528 bytes, 383 solicitudes de datos, 936 HTTP totales. Resumen derivado: C0_CACHED_SUPPORT_BATCH_ACCEPTANCE.json; resultados originales: C0_CACHED_SUPPORT_BATCH_RESULTS.json. La aceptación es técnica del diagnóstico, no del Gate.

Se evaluaron 2356992 píxeles comunes: 65536 para cada una de 33 combinaciones, incluyendo rank3; 64768 para cada banda de rank5. En spline_lut, soporte completo coincide con evaluado; no hay exclusiones por no finitud ni ausencia total de candidatos. Rank5 mantiene 768 píxeles sin soporte por banda. Son regiones del modelo candidato de bricks conocidos, no prueba de exhaustividad de selección del servicio.

| Variante prefijada | L2 relativo mínimo | Máximo |
|---|---:|---:|
| analytic | 6.93151e-7 | 4.65506e-4 |
| float_coords | 7.98441e-8 | 4.65474e-4 |
| direct_lut | 4.62122e-8 | 9.66217e-8 |
| spline_lut | 4.62187e-8 | 8.68841e-8 |

Ninguna variante alcanza igualdad exacta en toda una combinación. Para spline_lut: 1111404 píxeles exactos, 622199 positivos y 623389 negativos; RMS agregado 1.03987e-8, en unidades numéricas del array todavía no certificadas. No se selecciona ganador retrospectivamente.

| Partición spline_lut | Píxeles | RMS |
|---|---:|---:|
| Borde3 | 106992 | 1.42944e-8 |
| Interior | 2250000 | 1.01764e-8 |
| Solapamiento candidato | 190521 | 1.52834e-8 |
| Un brick candidato | 2166471 | 9.85404e-9 |

Persisten descriptivamente mayor RMS de borde y solapamiento. Q0–Q3 de intensidad observada: 7.88634e-10, 4.13049e-10, 5.02950e-10, 2.07723e-8; sigue predominando error absoluto en Q3 para esta variante. No prueban causas. Distribuciones firmadas, cuadrantes, intensidad de referencia y desgloses por objeto/banda permanecen en resultados originales.

Las variantes analíticas no mantienen el comportamiento del dominio parcial: los mayores residuales aparecen en ranks3/5, incluyendo rank3 con soporte completo. RMS analítico en solapamiento 2.17820e-5 frente a 1.90216e-7 en un brick. No se extrapola la reducción de energía del lote A/B ni se atribuye este patrón al kernel, clipping o aritmética sin una prueba discriminante. La extensión de dominio y clipping fue predeclarada; tampoco se asume que la norma anterior y la nueva representen idéntico dominio de comparación.

## DOCUMENTED

Se utilizan exclusivamente protocolo normal, addendum, plan A/B, protocolo cached-support, reportes Range y snapshots de fuentes previamente preservados. No hubo consulta externa nueva. El código público candidato distingue construcción del coadd y remuestreo posterior del viewer; los commits preservados no acreditan despliegue. La spline local no es certificación de FITPACK/astrometry.net.

PASS exige criterios congelados de recuperabilidad, bandas, centro, release/WCS/unidad verificables y compatibilidad salvo remuestreo documentado. No existe tolerancia científica nueva para aprobar estos residuales. REVISE requiere las condiciones originales y propuesta explícita de extracción; FAIL requiere evidencia adversa original, no solamente discrepancia con una aproximación candidata. INCONCLUSIVE formal al cierre implica STOP según addendum.

## INFERRED

El soporte ampliado aporta evidencia de compatibilidad numérica con las rutas LUT candidatas sobre 33 arrays completos y tres arrays parciales. No demuestra equivalencia funcional exacta ni conservación de flujo, calibración, selección global de bricks o identidad desplegada. Las incertidumbres no se concentran únicamente en rank5: existen residuales no nulos en combinaciones completas y limitaciones semánticas compartidas.

## UNRESOLVED y siguiente decisión

Faltan explicación independiente/cota del residual final, procedencia funcional suficientemente documentada, vínculo de versión/configuración desplegada, equivalencia WCS/spline y unidades del cutout normal. La divergencia descriptiva de las variantes analíticas en soporte ampliado necesita auditoría antes de atribuir causas; no justifica cambiar parámetros o umbrales.

Los seis rangos (172146 bytes) serían útiles exclusivamente para cerrar los 768 píxeles ausentes por banda de rank5 bajo el modelo candidato. No hay evidencia de que sean necesarios ahora para decidir la cuestión semántica; son incapaces por sí solos de resolver despliegue, unidades o selección exhaustiva. No se prepara ni ejecuta adquisición. El menor coste no demuestra necesidad científica.

C0-C permanece PENDING en esta revisión diagnóstica: no hay fundamento para PASS ni demostración de FAIL. Próximo paso justificado sin red: auditoría acotada de las ramas analítica/LUT en bordes del recorte y de la evidencia documental ya preservada, fijando cualquier prueba discriminante antes de ejecutarla. Esto no autoriza nuevos lotes, ajustes ni fases dependientes. Si se cierra la investigación sin resolver la semántica exigida, corresponde INCONCLUSIVE y STOP; no mantener PENDING como sustituto indefinido de esa decisión.

Alcance de equivalencia exacta conservado: únicamente regiones nativas oficiales versus subimage del subconjunto Range y layouts soportados. Este diagnóstico no extiende esa equivalencia al cutout normal.
