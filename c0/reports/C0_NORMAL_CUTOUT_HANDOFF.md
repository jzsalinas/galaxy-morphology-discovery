# Handoff humano — diagnóstico offline del cutout normal

Directorio: `/home/jzsalinas/Documents/galaxy-morphology-discovery`.

```bash
c0/.venv/bin/python -m c0_pipeline.normal_cutout --run
```

Opcional, sin procesamiento: `c0/.venv/bin/python -m c0_pipeline.normal_cutout --dry-run`.

Alcance fijo: ranks 1–12 y g/r/z; 36 comparaciones contra referencia analítica Lanczos-3. No constituye réplica exacta del servicio ni evaluación automática de C0-C. Protocolo previo: C0_NORMAL_CUTOUT_PROTOCOL.md. Smoke rank 1/g ya realizado; no repetir etapas de adquisición.

Coste: cero red, cero solicitudes de datos y cero descargas. Aproximadamente 10–120 segundos, hasta 512 MiB RAM y menos de 2 MiB de nuevas salidas. FITS de entrada únicos: 30,378,240 bytes; el script rechaza entradas que sumen más de 128 MiB. Lecturas repetidas de hashes/bandas estimadas inferiores a 200 MiB. Se mantiene el probe original de 96 objetos y todos los contadores acumulados.

Entradas: C0_PROBE_FITS_REPORT.parquet, C0_SUBIMAGE_REPORT.parquet, C0_RANGE_SUBSET_RESULTS.json, cutouts/subimágenes locales verificados, C0_NORMAL_CODE_SOURCES.json y snapshots documentales. No lee catálogos raw ni lockbox, no modifica los FITS.

Salidas: `c0/reports/normal_cutout/batch_NNN_B.json` (checkpoint por objeto/banda), `c0/reports/C0_NORMAL_BATCH_RESULTS.json`, `c0/reports/C0_NORMAL_BATCH_STATUS.json`. Log append-only: `c0/logs/C0_NORMAL_BATCH.log`. El resumen contiene residuales, píxeles excluidos por soporte faltante y limitaciones. Sin galerías ni transformaciones para entrenamiento.

Éxito operativo inequívoco: `C0_NORMAL_BATCH_OK`, código 0. Solo significa que terminaron las 36 caracterizaciones; NO significa PASS de C0-C. Fracaso: `C0_NORMAL_CHARACTERIZATION_FAILED`, código 2; informar y no reintentar automáticamente.

Reanudación tras interrupción/revisión: el mismo comando reutiliza checkpoints cuya procedencia coincide. Si cambian código/protocolo/entradas, se detiene conservando resultados; no borrar ni sobrescribirlos para forzar reanudación. No ejecutar concurrentemente con otra etapa C0. Un residual grande no se oculta ni provoca una descarga de fallback.

Delegación obligatoria por AGENTS.md: «operación bulk sobre catálogos, bricks, frames o imágenes». Aunque es pequeño y offline, el agente solo ejecutó el smoke y pruebas sintéticas; el lote queda para ejecución humana. Tras entregar el comando, espera su finalización.
