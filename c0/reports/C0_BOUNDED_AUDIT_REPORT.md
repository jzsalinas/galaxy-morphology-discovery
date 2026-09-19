# Auditoría acotada C0-C — 2026-09-18

## OBSERVED

Resultado de salida: **C — SEMANTIC/PROVENANCE BLOCK IS NOT IDENTIFIABLE WITH AVAILABLE EVIDENCE**. Estado formal C0-C: **INCONCLUSIVE**. Decisión global: **STOP**, por addendum vinculante. No se declara que los datos sean incorrectos ni se impone igualdad bit a bit como requisito nuevo.

Se preservaron C0_CACHED_SUPPORT_OK y sus 36 checkpoints; no se repitió ningún lote. Se ejecutó únicamente el protocolo nuevo C0_BOUNDED_AUDIT_PROTOCOL.md: cuatro imágenes sintéticas 12×12, dos ejemplos cacheados rank3/g y rank5/g, lectura de resúmenes y fuentes locales. Sentinel técnico C0_BOUNDED_AUDIT_TESTS_OK; log c0/logs/C0_BOUNDED_AUDIT.log. Resultados/procedencia: C0_BOUNDED_AUDIT_RESULTS.json; implementación: c0_pipeline/bounded_audit.py. Lectura medida 16069990 bytes, sin adquisiciones. Ledger antes/después idéntico: 465348528 bytes, 383 solicitudes de datos, 936 HTTP totales.

Se mantienen 33/36 arrays con soporte candidato completo; rank5 g/r/z con 768 píxeles ausentes cada uno. Los 2356992 píxeles comunes previamente evaluados no establecen cobertura universal del servicio ni exhaustividad de bricks.

## DOCUMENTED

Autoridades: GALAXY_RESEARCH_SEED.md, CODEX_PHASE_C0_SPEC.md, C0_EXECUTION_DECISION_001.md y protocolo normal. Fuentes externas usadas exclusivamente como snapshots locales: S6.raw (documentación oficial de productos DR5), S7.raw (URLs del viewer), VIEWER_HOME.raw, VIEWER_views.py/urls.py/cutouts.py, ASTROMETRY_resample.py/lanczos.i. URLs originales, UTC, HTTP, hashes y commits están en C0_NORMAL_CODE_SOURCES.json y se anclan nuevamente en los resultados de auditoría. No se consultó la red.

S6.raw, líneas 1999–2003, documenta nanomaggies por píxel y Lanczos-3 en imágenes coadd. Es el remuestreo de construcción del producto, no acreditación del operador posterior del viewer. La fuente candidata de este último documenta otra etapa: WCS destino, muestreo desde recortes, acumulación y FITS.

Viewer candidato d1b54504be1a8d9037989af14f0befacf96bf4b6; astrometry candidato d20a0503739e74b02418cde2e7d65013dadac579. Son snapshots públicos independientes. Su integridad no establece que esa combinación haya servido los archivos descargados.

## INFERRED

Una distinción del código predice el patrón de divergencia analítico/LUT: truncamiento entero de coordenadas negativas admitidas produce desplazamientos menores de -0.5; la LUT recorta el índice de bin, pero conserva una fracción fuera de [0,1], extrapolando la última pareja de filas. El kernel analítico evalúa directamente la función en ese desplazamiento. La réplica de muestras al borde del crop no elimina esta distinción. Los tests apoyan este mecanismo local sin modificar el operador.

La estrecha compatibilidad numérica de LUT con los cutouts es evidencia empírica del subconjunto, no certificado de calibración o implementación desplegada. Ningún operador se escoge por menor residual.

## UNRESOLVED

No se establece una cota independiente que cubra el residual LUT-servicio: faltan identidad funcional suficiente de WCS, spline, pesos, biblioteca matemática/compilación y configuración efectiva. No se demuestra causalidad de cada exceso de residual en borde/solapamiento ni equivalencia funcional exacta de arrays completos.

No se verifican versión del viewer desplegado, dependencia astrometry desplegada, configuración DR5 efectiva ni reglas exhaustivas de selección de bricks del servicio. El normal FITS carece de BUNIT; falta evidencia independiente suficiente que conecte las unidades documentadas del coadd con la ruta numérica efectivamente usada para ese FITS. La ausencia de metadata no equivale por sí sola a unidad incorrecta. Es una limitación de demostración bajo el protocolo, no un FAIL empírico.

## DISCRIMINATING TEST RESULTS

T1 — mecanismo predeclarado. En x=-0.75, y=4.25, rampa sintética: analytic=-0.0532407213 y LUT=-0.0737234056. Impulso: 0.9468896386 frente a 0.9661778808. Checker: 0.0968516779 frente a 0.0807253122. En coordenadas nominales las diferencias son mucho menores. Constante1 produce 1 en analítico y 1.0000030994 en LUT extrapolada: tampoco se presume preservación exacta de constantes en esa ruta. Las coordenadas sintéticas son binarias exactas; por eso analytic y float_coords coinciden aquí, lo que aísla el mecanismo de evaluación/clipping y no demuestra ausencia general de errores de coordenadas.

Trasladar el origen del crop a (100,200) con coordenadas relativas conservadas no cambia las salidas: el kernel ve límites del array, no su identidad astronómica. Los ejemplos reales examinados tienen sus bordes relevantes coincidentes con límites del brick; esto no discrimina ambos tipos de borde en esos ejemplos. La mezcla de dos contribuciones es invariante al invertir el orden en el test; tres contribuciones [1e20,-1e20,1] dan media float32 0.3333333433 frente a 0 en orden invertido. No generalizar invariancia observada con dos bricks.

T2 — contraste de predicción geométrica con diferencias entre ramas ya cacheadas, sin remuestrear imágenes:

| Ejemplo | Píxeles fuera del intervalo nominal | Energía float_coords−direct_lut dentro | Energía fuera |
|---|---:|---:|---:|
| rank3/g | 256 | 2.44249171e-6 | 9.54009632e-12 |
| rank5/g | 253 | 6.08536806e-7 | 1.63555002e-13 |

Máscaras calculadas desde headers/geometría antes de leer diferencias. La concentración apoya la predicción cualitativa preespecificada. No fue un ajuste al residual remoto, ni una nueva tolerancia. No se produjo una predicción pixel a pixel independiente de la magnitud total: por tanto no se reclama explicación cuantitativa completa del servicio ni de todas las bandas. Las estadísticas analytic−direct_lut, límites de crop/brick y solapamientos están preservadas en JSON.

T3 — estructura existente. LUT/direct L2 relativo 4.62122e-8–9.66217e-8; LUT/spline local 4.62187e-8–8.68841e-8. Ninguna combinación exacta global. LUT/spline: 1111404 residuos cero, 622199 positivos, 623389 negativos; RMS total 1.03987e-8. Borde3=1.42944e-8, interior=1.01764e-8; solapamiento=1.52834e-8, single-brick=9.85404e-9. Cuartiles observados Q0–Q3: 7.88634e-10, 4.13049e-10, 5.02950e-10, 2.07723e-8. RMS por cuadrante entre 2.46827e-9 y 1.55126e-8. Métricas por objeto/banda, signos, intensidad de referencia y cuatro variantes quedan en existing_structure del JSON, sin agregación que borre esos desgloses. Estos patrones son descriptivos, no causales.

La cota clásica gamma_n=n*u/(1-n*u), u=2^-24, sirve condicionalmente para operaciones con redondeo y sin overflow/underflow relevantes. Para suma ponderada interviene la suma de magnitudes de términos; una división añade dependencia del normalizador. Sin controlar pesos, sus errores de LUT/libm, coordenadas, normalizador y operaciones del servicio no puede convertirse en una cota de su residual. No se calculó una tolerancia científica a partir del residual observado. A queda parcialmente explicada, no resuelta de forma general.

T4 — la inspección documental conserva el hiato entre implementación pública candidata y la ruta efectivamente desplegada. No aparece en el registro de procedencia una atestación independiente de esa ruta/unidades. Resultado de B: insuficiente bajo criterios congelados. No se inicia una búsqueda abierta de más tests.

## PROVENANCE CHAIN

| Enlace o propiedad | Clasificación | Evidencia y alcance |
|---|---|---|
| Producto oficial DR5 nativo y unidad | VERIFIED | URLs/ETag/Range y headers; BUNIT=nanomaggy, S6 documenta nanomaggies/píxel; solo regiones/layouts examinados |
| Región oficial → subimage nativa | VERIFIED | Igualdad exacta y WCS en subconjunto Range; no se extiende a normal |
| DR5 → capa viewer | DOCUMENTED CANDIDATE | Selección decals-dr5 y ruta DR5 en VIEWER_views; paths/configuración realmente desplegados UNKNOWN |
| Capa → WCS/remuestreo | DOCUMENTED CANDIDATE | Astrometry L3, spline step25/margin12, float32, clipping y LUT preservados; combinación desplegada UNKNOWN |
| Remuestreo → acumulación | DOCUMENTED CANDIDATE | Rechazo no finitos y pesos1 en ruta candidata; orden/selección efectivos UNKNOWN |
| Acumulación → FITS | DOCUMENTED CANDIDATE | get_images_only evita RGB/asinh; copia a cube float32 y fitsio.write, líneas 2257–2304 |
| Cabecera normal release/bandas/WCS | VERIFIED | FITS recuperados DR5/grz/TAN; no certifica por sí sola cadena de píxeles |
| Compatibilidad con operador candidato | INFERRED | Compatibilidad numérica observada; identidad funcional no establecida |
| Commit viewer y astrometry desplegados | UNKNOWN | No atestación en evidencia preservada |
| Configuración y selección de bricks efectivas | UNKNOWN | Código candidato y bricks observados no son inventario del despliegue |
| Valores tras remuestreo | DOCUMENTED CANDIDATE | Ruta candidata hace combinación/cast/escritura sin RGB; ausencia de otras modificaciones desplegadas UNKNOWN |
| Cutout normal calibrado DR5 bajo contrato | UNKNOWN | No verificado suficientemente; no se promueve compatibilidad a calibración |

## UNIT SEMANTICS

1. **Herencia dimensional esperada:** una combinación lineal normalizada con coeficientes adimensionales conserva la dimensión de los valores de entrada. Eso es condicional al operador y no demuestra conservación del flujo integrado sobre rejillas, área de píxel ni validez en cobertura ausente. El contraejemplo constante muestra que incluso normalización numérica exacta no es universal.
2. **Compatibilidad empírica:** los números LUT y normal son próximos en el dominio comparado; esto respalda una escala compatible, sin determinar de manera independiente la semántica de calibración.
3. **Semántica documentada:** S6 documenta coadds; S7 y código describen rutas candidatas. El material preservado no fija suficientemente la cadena de unidades del servicio normal realmente usado.
4. **Metadata verificada:** BUNIT nativo existe; BUNIT normal falta. No se inventa ni inserta BUNIT en FITS originales. No se certifican nanomaggies/píxel para el normal mediante herencia supuesta.

## C0-C EXIT ANALYSIS

Categoría única **C**. No existe, entre los tests acotados identificados, uno que permita discriminar el bloqueo documental a partir de más píxeles. La falta no se reduce a 768 píxeles de rank5. Los seis rangos/172146 bytes serían solo ampliación de cobertura y quedan **innecesarios para resolver este C0-C**, sin preparar handoff ni adquisición.

Estado formal **INCONCLUSIVE**, no PASS (semántica insuficientemente verificada), no FAIL (no demostración de dato adverso bajo criterios originales), ni REVISE automático. Una extracción alternativa nativa sería una propuesta explícita de contrato/metodología, no equivalencia ya probada ni reparación silenciosa; queda fuera de esta ejecución. No se exige conocer un commit exacto como requisito nuevo: se constata que tampoco hay otra evidencia independiente suficiente del operador/unidades que cierre el protocolo.

El addendum prescribe INCONCLUSIVE en C0-C → **STOP**. Se detienen adquisiciones/análisis dependientes. No SDSS, Tractor, nexp, máscaras, PSF ni C1. Se conservan los éxitos A/B y la equivalencia nativa limitada; no se autoriza materialización ni se genera DATA_CONTRACT_DRAFT. Cualquier reapertura requerirá nueva evidencia independiente o revisión explícita autorizada del protocolo, no otra secuencia de comparaciones ajustadas.
