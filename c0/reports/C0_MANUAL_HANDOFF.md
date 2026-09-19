# Entrega manual 1 — ingesta Zenodo, no probe

Motivo: AGENTS.md exige ejecución humana de toda operación bulk sobre catálogos. El agente no ejecutó esta ingesta.

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
/home/jzsalinas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m c0_pipeline.manual_ingest --max-additional-mib 100
```

Previsualización opcional: añadir `--dry-run` al comando. No realiza red ni instalaciones.

- Descarga declarada: 90.631.376 bytes (86,43 MiB): rueda PyArrow 50.102.437 bytes y catálogo GZD-5 Parquet 40.528.939 bytes. Máximo adicional 100 MiB; también se aplica el contador acumulado de 2 GiB. No se descargan imágenes.
- Tiempo estimado: 2–10 minutos, condicionado por red, instalación y disco; no es una medición.
- Espacio: reservar 1 GiB libre para rueda, entorno local, original, proyecciones y archivos temporales. Estimación conservadora, pendiente de medición.
- Entradas: `c0/provenance/PYARROW_DEPENDENCY_LOCK.json`, metadatos versionados Zenodo, diccionario ya verificado y código local.
- Dependencia: PyArrow 25.0.1 se instala en `c0/.venv` desde rueda con SHA-256 fijado. Pip usa `--no-index --no-deps`; no resuelve dependencias por red. La rueda se descarga mediante el mismo contador que los datos.
- Salidas: RAW protegido; SUBJECT_INDEX.parquet; CONFOUND_AUDIT_C0.parquet; INTERPRETATION_LOCKBOX; esquema permitido; C0_ZENODO_INGEST_SUMMARY.json; C0_INGEST_ENVIRONMENT.json; manifiesto actualizado.
- Log: `c0/logs/C0_MANUAL_INGEST.log`. No imprimir catálogos ni contenido del lockbox.
- Éxito: mensaje exacto `C0_MANUAL_INGEST_OK`, código 0 y `c0/reports/C0_MANUAL_STATUS.json` con ese estado.
- Fallo: mensaje `C0_MANUAL_INGEST_FAILED`, código 2; conservar archivos y log para revisión. No repetir indefinidamente ni cambiar fuentes.
- Reanudación: mismo comando; recursos completos con SHA-256 verificado usan caché. Una transferencia interrumpida puede reiniciarse desde cero y consume otro intento; no se implementa HTTP Range. El contador persiste; máximo cuatro intentos totales por URL. Las proyecciones se reemplazan atómicamente por archivo; el marcador de éxito se escribe después de todas las comprobaciones.

Smoke tests realizados: transporte simulado (cache, redirect, truncación, tamaños), límites y fallback de identidad. La ingesta real con PyArrow aún no ha sido ejecutada: la dependencia se instalará en este paso manual. El script no declara C0.2 completo: faltan reconciliación CDS, campos adicionales y revisión de las proyecciones. No selecciona el probe ni evalúa Gates finales.

Después del comando, confirmar finalización y mensaje de salida. El agente inspeccionará los artefactos sin repetir la operación ni abrir respuestas morfológicas.
