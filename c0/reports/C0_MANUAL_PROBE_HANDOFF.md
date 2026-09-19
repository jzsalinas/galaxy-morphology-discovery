# Entrega manual 3 — fijar la muestra, sin red

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.manual_probe
```

Entradas: SUBJECT_INDEX.parquet y las columnas galaxy_id, petro_theta y active_learning_on de CONFOUND_AUDIT_C0.parquet. No se abre RAW ni lockbox.

Salida: c0/probe/C0_PROBE_MANIFEST.parquet, c0/reports/C0_PROBE_SELECTION_SUMMARY.json y C0_MANUAL_PROBE_STATUS.json. La selección registra los 96 IDs en el contador persistente de objetos; no recupera productos.

Algoritmo congelado antes de ejecutarlo: semilla 11; cuartiles de RA por rango ordenado, empates por galaxy_id; cuartiles de radio Petrosiano dentro de cada cuartil RA, empates por galaxy_id; seis por celda (24 por RA). En cada celda se eligen por SHA-256 hasta dos objetos por estado de selección activa; se completan las cuotas globales de al menos 24 por estado y luego los cupos restantes por hash. Si las cuotas no pueden satisfacerse por este procedimiento, se detiene sin relajar silenciosamente. No se optimiza después de observar resultados. Radios ausentes o no finitos detienen la ejecución y requieren revisión, no imputación. Se comprueba que barajar las filas no modifica ningún registro del probe.

Tiempo estimado: menos de 2 minutos; red: cero bytes; espacio nuevo inferior a 10 MiB; reservar hasta 1 GiB RAM para las tablas y la prueba de reordenamiento. Son estimaciones. Log: c0/logs/C0_MANUAL_PROBE.log; salida extensa solo al log.

Éxito: C0_MANUAL_PROBE_OK y código 0. Fallo: C0_MANUAL_PROBE_FAILED, código 2; detenerse e informar. Reanudación con el mismo comando: selección determinista, registro de IDs idempotente y sin reiniciar límites. --help y --dry-run disponibles. 26 tests offline pasan, incluidos rechazo de campos bloqueados, cuotas imposibles, radios ausentes e invariancia ante reordenamiento.

Se delega porque AGENTS.md exige ejecución humana para «operación bulk sobre catálogos, bricks, frames o imágenes», aunque aquí el proceso sea local y breve. Después de ejecutar, confirmar resultado; el agente inspeccionará el manifiesto sin volver a seleccionar. La comparación de sesgo de disponibilidad por selección activa queda pendiente hasta recuperar los productos.
