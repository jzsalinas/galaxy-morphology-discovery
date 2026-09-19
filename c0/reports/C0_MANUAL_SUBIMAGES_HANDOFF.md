# Entrega manual 5 — subimágenes y rutas de bricks DR5

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.manual_subimages --max-additional-mib 250
```

Entradas: C0_PROBE_FITS_REPORT.parquet, SUBJECT_INDEX.parquet con consulta de las 96 identidades fijadas y los dos recursos smoke ya verificados. No se lee el lockbox.

Operaciones: hasta 95 nuevas extracciones subimage y 95 consultas de bricks; secuenciales, sin reintentos automáticos. Mismos 96 objetos, sin sustituciones. El primer objeto reutiliza caché SHA-256. No se descargan bricks completos ni tablas Tractor en este paso.

Transferencia estimada: aproximadamente 146 MiB si las respuestas tienen tamaños similares al smoke de 1609920 bytes; máximo adicional 250 MiB y contador global de 2 GiB. Tiempo estimado 10–40 minutos, dependiente del servicio. Reservar 300 MiB de disco; menos de 1 GiB RAM. Son estimaciones, no mediciones.

Salidas: c0/probe/subimages/*.fits; c0/probe/bricks/*.json; C0_SUBIMAGE_REPORT.parquet; C0_BRICK_ROUTES.parquet; C0_SUBIMAGE_SUMMARY.json y C0_MANUAL_SUBIMAGES_STATUS.json. Las rutas Tractor son candidatas, no matches de fuente. Los ranks 1–12 quedan identificados para el contraste independiente posterior.

Log: c0/logs/C0_MANUAL_SUBIMAGES.log. Éxito: C0_MANUAL_SUBIMAGES_OK, código 0. Fallo: C0_MANUAL_SUBIMAGES_FAILED, código 2; detenerse e informar. Reanudación, solo después de revisión: mismo comando; cache de recursos completos verificados, contadores persistentes y tablas parciales atómicas. No reinicia selección ni límites. --help y --dry-run disponibles.

31 tests offline pasan. Smoke real de un objeto: DR5 explícito, 3 imágenes y 3 invvar con forma/WCS compatibles; unidades aún pendientes. No se asigna PASS a C0-C/D por estos HDUs. Máscara, nexp y PSF ausentes de esta respuesta, no declarados ausentes de todo DR5.

Se delega según AGENTS.md por operación bulk sobre imágenes y duración estimada superior a cinco minutos. El agente no ejecutó el lote y esperará confirmación antes de inspeccionar los artefactos.
