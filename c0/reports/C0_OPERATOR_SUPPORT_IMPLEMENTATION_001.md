# Implementación offline A/B lista para ejecución humana

## OBSERVED

Se retomó el prototipo cuyo SHA-256 coincide con recovery_operator_001/recovery.json. Las copias de recuperación, protocolos, manifiestos y checkpoints humanos anteriores se conservaron sin modificación. No se reparó Git, no se repitió C0_NORMAL_BATCH ni otra etapa humana.

Se completó operator_support.py con CLI --help/--dry-run/--smoke/--run, guard de red, límites de payload IO, orden congelado, lectura segura de descriptores y payloads, métricas A, inventario B, checkpoints content-addressed, hashes de entrada/salida, procedencia del compilador y resultados/status/logs. Los checkpoints se confirman después de escribir payloads; se conservan restos de interrupciones.

El lector de descriptores valida layout RICE 2D, forma y cardinalidad de tiles, longitud/dtype de fila, tabla completa en prefijo, THEAP/PCOUNT contra tamaño total y descriptores no negativos dentro del heap. Payloads ambiguos/vacíos se rechazan. El inventario resta intervalos cacheados, reutiliza regiones nativas ya validadas, deduplica por URL/ETag y no descarga envolventes.

A compara referencia analítica, coordenadas float32, LUT C y spline local+LUT; registra la intersección conocida sin ajustar máscaras por residual. El clipping usa límites de la región candidata del brick, no los límites arbitrarios del recorte local. Registra rechazo de contribuciones no finitas, ceros sin contribución y efecto del orden invertido. Los conteos de borde/solapamiento pueden ser cero; se reportan como no observados, no como prueba de equivalencia.

Verificación: 67 tests pasan (49 anteriores + 18 nuevos), log test_operator_support_full_002.log. Alcance nuevo: intervalos, spline polinómica/tensorial, límites y corrupción de descriptores, caps IO, integridad/procedencia de checkpoints, bloqueo de red, núcleo C con constantes/impulso/NaN/clipping y comparación sintética con kernel analítico, soporte desconocido, acumulación/orden, WCS identidad y deduplicación/cobertura conjunta. Los umbrales de tests sintéticos no son criterios científicos de aceptación. La advertencia de truncación del fixture inválido es deliberada.

Se conservaron logs de dos defectos de implementación hallados y corregidos: el guard del fragmento C contaba solo una aparición de un símbolo que también figura en la macro, y un fixture sintético de soporte no incluía ZNAXIS2 tras añadir esa metadata a la salida. Ninguno corresponde a un fallo científico del servicio. No se ajustó ningún parámetro para reducir residuales.

Smoke rank 1/g: C0_OPERATOR_SUPPORT_SMOKE_OK. 62500 píxeles comunes; L2 relativo analítico 2.2561545325609458e-06; float_coords 1.3141739130253662e-07; direct_lut 8.71431065662648e-08; spline_lut 8.687565247294774e-08. No se compararon los otros objetos/bandas. En este único caso el soporte comprimido requerido está ya cacheado: cero bytes adicionales condicionados al modelo; no se generaliza a los doce objetos.

La reanudación fue probada haciendo que run_job lanzara error si se invocaba: se reutilizó el checkpoint correctamente, sin recalcularlo (test_operator_support_resume_001.log). Los smoke de versiones intermedias y la fuente previa se conservaron por hash; las salidas de batch no existen todavía.

## DOCUMENTED

Fuentes fijadas y criterios: C0_NORMAL_CODE_SOURCES.json, C0_OPERATOR_SUPPORT_PLAN.md, C0_NORMAL_CUTOUT_PROTOCOL.md, CODEX_PHASE_C0_SPEC.md y C0_EXECUTION_DECISION_001.md. Se mantiene la distinción entre resampling del coadd y operador del viewer. Se compiló únicamente el fragmento local auditado descrito en el plan, no el módulo viewer ni fuentes nuevas. No se instaló SciPy.

## INFERRED

En el smoke, las variantes prefijadas reducen reproduciblemente el residual de la referencia analítica. La razón de energías y el cambio predicho se registran sin convertir la reducción en una atribución causal única ni equivalencia con el despliegue. El coste futuro es condicional a la ruta local y bricks conocidos; no es una cota universal para toda implementación del servicio.

## UNRESOLVED

Pendiente el lote humano 12×3, atribución de discrepancias remanentes, soporte completo y coste agregado. La spline not-a-knot local no está certificada como FITPACK, y Astropy TAN no está certificado como la implementación WCS de astrometry.net desplegada. Tampoco están certificados el commit/configuración/orden de bricks del despliegue, exhaustividad del soporte remoto ni unidades del cutout normal. Igualdad numérica local, si apareciera, no resolvería por sí sola esos puntos.

C0-C permanece PENDING. El objetivo de este handoff es diagnóstico, no obtener PASS. Tras la ejecución se decidirá, según criterios existentes, si hay evidencia suficiente, necesidad justificada de adquisición o INCONCLUSIVE/STOP.

Contadores offline intactos: 465348528 bytes; 383 solicitudes de datos; 936 HTTP totales. No adquisición ni SDSS/Tractor/nexp/máscaras/PSF.

Comando y condiciones: C0_OPERATOR_SUPPORT_HANDOFF.md.
