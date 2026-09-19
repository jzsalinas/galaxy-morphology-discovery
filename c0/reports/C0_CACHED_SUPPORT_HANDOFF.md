# Handoff humano — soporte cacheado C0-C

Estado recuperado el 2026-09-18: implementación y protocolo presentes; 71 pruebas OK en c0/logs/test_cached_support_002.log. Smoke actual rank1/g y reanudación verificados: COMMITTED seguido de REUSED, sin repetir comparación. Hashes de código/protocolo/entradas de procedencia y checkpoint JSON/NPZ comprobados. El primer smoke de una revisión anterior está preservado en un namespace distinto. No existe lote cached_support/batch ni se ejecutó el lote completo. Código operator_support anterior sin cambios respecto a su procedencia congelada. Git sigue no operativo; no se reparó.

## Comando

Desde /home/jzsalinas/Documents/galaxy-morphology-discovery:

```bash
c0/.venv/bin/python -m c0_pipeline.cached_support --run --max-read-mib 768 --max-write-mib 256
```

Previsualización opcional: sustituir --run por --dry-run. Ayuda: --help.

## Alcance y recursos

Nuevo diagnóstico offline de los 12 objetos × grz y cuatro variantes prefijadas. No repite el lote A/B ni adquisición alguna. Entradas: informes Parquet de probe/subimage, FITS normales y subimages locales, 42 pares de fragmentos Range referenciados por C0_RANGE_SUBSET_RESULTS.json, checkpoints/procedencia A/B, fuentes C auditadas y protocolos. No se leen catálogos morfológicos.

Red: cero solicitudes, cero bytes nuevos; audit hook bloquea conexiones/resolución DNS/urllib. No subprocess de adquisición. Contadores acumulados de ledger se comparan antes/después: 465348528 bytes, 383 solicitudes de datos, 936 HTTP totales. No seis rangos rank5 ni SDSS/Tractor/nexp/máscaras/PSF.

Estimación CPU: 2–15 minutos, dependiente del equipo; ejecución secuencial, sin paralelismo de jobs. RAM estimada <=768 MiB (estimación, no límite OS). Payload IO limitado por ejecución a 768 MiB leídos y 256 MiB escritos; reservar 300 MiB libres para resultados/logs. El compilador, si hiciera falta reconstruir el kernel auditado, y metadatos pequeños no forman parte del contador de payload; el kernel ya existe. No se reinician contadores de red. La reanudación requiere releer/verificar entradas y checkpoints, pero no recalcula comparaciones confirmadas.

## Artefactos

- c0/reports/C0_CACHED_SUPPORT_BATCH_RESULTS.json: métricas por objeto/banda/variante y dominios, procedencia, contadores.
- c0/reports/C0_CACHED_SUPPORT_BATCH_STATUS.json: estado, motivo, IO y código de salida.
- c0/reports/cached_support/batch/provenance.json.
- c0/reports/cached_support/batch/NNN_b/checkpoint.json y payloads result-<sha>.json, arrays-<sha>.npz: predicciones, residuales y máscaras explícitas.
- Log acumulativo: c0/logs/C0_CACHED_SUPPORT_BATCH.log.

Éxito inequívoco: C0_CACHED_SUPPORT_OK y exit code 0. Significa diagnóstico completado, NO PASS de C0-C. Fallo: C0_CACHED_SUPPORT_FAILED y exit code 2; revisar reason/log, no aumentar límites ni borrar archivos para forzar éxito.

Interrupción: repetir exactamente el comando. Checkpoints confirmados se verifican y reutilizan; una combinación interrumpida sin checkpoint puede recalcularse. Archivos .part y payloads no referenciados se preservan. Un cambio de procedencia/hash, soporte discrepante con el inventario, límites agotados o conflicto de ejecución detiene el proceso; informar el error antes de modificar entradas o parámetros. No ejecutar simultáneamente otros procesos C0.

## Interpretación pendiente

C0-C permanece PENDING. El protocolo previo C0_CACHED_SUPPORT_PROTOCOL.md fija máscaras, borde3, solapamiento candidato, variantes y métricas sin nueva tolerancia. La spline local no certifica FITPACK/despliegue. Soporte completo se distingue de evaluación y de finitud; rank5 mantiene soporte ausente explícito. Tras ejecución humana se revisarán resultados y solo entonces se decidirá si seis intervalos son necesarios, útiles o incapaces de resolver el bloqueo semántico. No se autoriza adquisición automáticamente.

Delegación por AGENTS.md: «operación bulk sobre catálogos, bricks, frames o imágenes» y «Después de entregar el comando, detente y espera a que el usuario confirme su finalización».
