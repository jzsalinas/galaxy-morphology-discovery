# Entrega manual 4 — cutouts DR5

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.manual_dr5 --max-additional-mib 200
```

Entradas: C0_PROBE_MANIFEST.parquet, identidad permitida en SUBJECT_INDEX.parquet, smoke request/FITS y ledger persistente. Astropy 8.0.1 y cinco dependencias se instalaron desde ruedas fijadas por SHA-256 con transporte contabilizado; lock en ASTROPY_DEPENDENCY_LOCK.json. No usa RAW de Galaxy Zoo ni lockbox.

Descarga estimada: unos 72 MiB nuevos si los otros 95 objetos tienen tamaño similar al primero; límite adicional de 200 MiB, 2 MiB por respuesta y 2 GiB acumulados. Solicitudes secuenciales, sin reintentos automáticos. Tiempo estimado: 5–30 minutos según servicio. Reservar 250 MiB de disco. El primer objeto se reutiliza con comprobación SHA-256.

Salida: c0/probe/dr5/*.fits, C0_PROBE_FITS_REPORT.parquet con auditorías por objeto, C0_DR5_CUTOUT_SUMMARY.json y C0_MANUAL_DR5_STATUS.json. Log: c0/logs/C0_MANUAL_DR5.log. No se generan galerías ni imágenes derivadas.

Éxito del paso: C0_MANUAL_DR5_OK y código 0. NO significa C0-C aprobado: los campos sin semántica, como BUNIT ausente, permanecen inconclusos hasta contraste documental y coadd. Fallo: C0_MANUAL_DR5_FAILED y código 2; detenerse e informar. Detención inmediata ante límites duros o fallo técnico de release/WCS/bandas/centrado; siete fallos de recuperación detienen el lote sin sustituir objetos.

Reanudación: mismo comando solo después de revisión; caché SHA-256 evita transferencias repetidas; cada informe parcial se guarda por archivo de forma atómica. Los contadores y las 96 identidades persisten. Los archivos verificados pueden volver a auditarse localmente; no se reinicia selección. --help y --dry-run disponibles.

Este paso cubre la recuperación y auditoría de cutouts, no todo C0.3. Quedan matches Tractor, doce comparaciones cutout/coadd y productos auxiliares. Las doce comparaciones usarán probe_rank 1–12, sin selección por contenido ni por éxito del servicio.

Delegación conforme a AGENTS.md por operación bulk sobre imágenes y posible duración superior a cinco minutos. El agente realizó solo un smoke test y 29 pruebas locales; no ejecutó el lote. Tras la ejecución, confirmar resultado para inspección de artefactos.
