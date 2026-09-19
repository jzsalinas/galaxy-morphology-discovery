# C0-C — protocolo previo al contraste del cutout normal

Fecha: 2026-09-17. No modifica seed ni especificación. Subconjunto congelado: ranks 1–12, g/r/z; ningún ajuste por morfología ni elección de interpolador por menor residual.

## Criterios de decisión (antes de experimentar)

PASS requiere los criterios de §11 C0-C: al menos 95/96 recuperables, tres bandas, centro dentro de un píxel, WCS/release/unidad verificables y contraste compatible con coadd salvo remuestreo documentado. La equivalencia Range–subimage no satisface por sí sola el último requisito.

INCONCLUSIVE al cerrar la investigación si la procedencia del operador, calibración o compatibilidad no puede resolverse con evidencia suficiente. Un código público sin vínculo demostrado con el servicio es evidencia de implementación candidata, no prueba de despliegue. Una comparación limitada al interior no prueba los bordes. Según addendum, una decisión formal INCONCLUSIVE implica STOP.

FAIL si se demuestra release incorrecta/no verificable, menos de 90 recuperables, unidades opacas o incompatibilidad con el coadd que no explica una transformación documentada. Un residual frente a una implementación candidata no demuestra por sí solo incompatibilidad del dato: puede indicar operador no identificado. No se ajustarán parámetros para rescatar el resultado.

REVISE solo según especificación: 90–94 recuperables, cabeceras incompletas o discrepancias explicables por servicio, con propuesta explícita de extracción desde bricks; no se aplica migración silenciosa. El Gate no se decide antes de terminar las verificaciones necesarias.

## Secuencia y límites

1. Inspeccionar documentación ya preservada y cabeceras/procedencia. Consultas ligeras de documentación/código oficial únicamente si faltan, mediante ledger acumulado, sin descargar imágenes nuevas. Congelar commit y hashes. Distinguir construcción del coadd y remuestreo del viewer.
2. Identificar rutas de código: selección de escala, kernels y soporte, WCS, combinación de bricks, máscaras/NaN/bordes y factores de área/unidades. Registrar lo no observable del despliegue.
3. Diseñar reproducción offline usando primero cutouts, subimágenes y fragmentos Range existentes. Excluir de cualquier comparación cuantitativa los píxeles cuyo soporte de entrada no está disponible, contando explícitamente exclusiones. No tratar exclusión como equivalencia global.
4. Fijar operador y criterio numérico derivado de su precisión antes del contraste; no elegir tolerancia ni interpolador observando residuales. Si no puede fijarse, limitarse a caracterización, sin declarar equivalencia.
5. Smoke mínimo directo; procesamiento del subconjunto completo mediante CLI humana por política bulk. No SDSS, Tractor, nexp, máscara ni PSF en esta etapa.

Toda reproducción guardará hashes de entradas/código, parámetros, fracciones comparadas, residuales por banda/objeto, discrepancias y limitaciones. Presupuesto acumulado inicial: 464265663 bytes y 383 solicitudes de datos. Las consultas documentales también cargarán bytes. Ningún contador se reinicia.

## Referencia numérica fijada antes del smoke

Se ejecutará exclusivamente una referencia analítica Lanczos-3 normalizada, soporte 7×7, WCS TAN evaluada por Astropy en cada píxel, acumulación float64 y media de contribuciones finitas de los bricks presentes en las subimágenes ya adquiridas. No reproduce la LUT C, las coordenadas float32/spline, el orden/selección de bricks ni la precisión del despliegue. No es una búsqueda de kernels.

Se registrarán igualdad exacta, residual máximo, RMS, L2 relativo, media firmada y cuantiles absolutos, sin ajuste de ganancia, offset, centro ni normalización. No existe tolerancia de aceptación científica para esta aproximación: sus residuales no asignan PASS/FAIL a C0-C. Incluso igualdad exacta de esta referencia no demuestra por sí sola procedencia desplegada ni equivalencia de píxeles excluidos. El diagnóstico sirve para determinar qué evidencia adicional hace falta.

Soporte desconocido de cualquiera de los bricks disponibles => píxel excluido, nunca rellenado como si fuera borde físico del coadd. Soporte conocido con NaN => contribución no finita; se cuenta separadamente. La referencia de combinación sigue el código candidato: media de contribuciones finitas, cero si no queda ninguna; cero no significa cobertura válida. No se presume conservación del flujo integrado por normalizar el kernel.
