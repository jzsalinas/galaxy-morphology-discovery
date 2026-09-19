# Entrega manual 2 — reconciliación CDS

La ingesta Zenodo concluyó; sus hashes, tamaños, permisos y conteos de footer se verificaron sin repetirla. Ver C0_INGEST_VERIFICATION.json. CDS respondió HEAD 200; recurso enlazado en el directorio oficial preservado S3_directory.raw.

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.manual_cds --max-additional-mib 40 --http-timeout-seconds 120
```

- Entrada local: SUBJECT_INDEX.parquet y C0_CDS_RESOURCE_LOCK.json; esquema byte-a-byte S3.raw. Fuente: gzdv5.dat.gz de CDS, catálogo J/MNRAS/509/3966.
- Transferencia esperada: 32.863.685 bytes (31,34 MiB); máximo adicional 40 MiB, siempre dentro del contador acumulado C0. Una solicitud de datos prevista, sin reintentos automáticos.
- Tiempo estimado: 1–5 minutos, condicionado por red y CPU. Reservar 500 MiB libres y aproximadamente 500 MiB de RAM. Son estimaciones, no mediciones.
- No escribe el catálogo descomprimido completo: lee gzip secuencialmente, con límite de 300 MiB expandidos y 300000 filas. Solo interpreta los primeros 66 bytes de identidad/coordenadas.
- Salidas: RAW_IMMUTABLE/gzdv5.dat.gz protegido, CDS_IDENTITY_RECONCILIATION.parquet, C0_CDS_RECONCILIATION_SUMMARY.json y C0_MANUAL_CDS_STATUS.json. Las diferencias quedan registradas; completar la ejecución no equivale a aprobar un Gate.
- Log: c0/logs/C0_MANUAL_CDS.log.
- Éxito: C0_MANUAL_CDS_OK y código 0. Fallo: C0_MANUAL_CDS_FAILED y código 2; detenerse e informar.
- Reanudación: mismo comando; caché SHA-256 evita redescargar un recurso íntegro. Las transferencias interrumpidas reinician desde cero; contadores e intentos persisten.
- Previsualización: añadir --dry-run, sin red. --help disponible.

Pruebas: 21 tests pasan con PyArrow instalado; incluyen casos sintéticos de duplicados, ausentes y diferencias de coordenadas. No se ejecutó la reconciliación real. No se seleccionaron objetos ni se descargaron imágenes.

Delegación obligatoria por AGENTS.md: «operación bulk sobre catálogos, bricks, frames o imágenes». Después del comando, confirmar resultado para inspección de artefactos; no repetir ante un fallo.
