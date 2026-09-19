# Ejecución manual — experimento Range, doce objetos congelados

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.range_experiment --run --max-additional-mib 128 --max-data-requests 84
```

Previsualización offline:

```bash
c0/.venv/bin/python -m c0_pipeline.range_experiment --dry-run
```

Alcance: ranks 1–12 ya fijados, bandas g/r/z y todos sus bricks intersectados; 42 archivos oficiales. No modifica muestra ni parámetros científicos. Usa HTTP Range con ETag y Content-Range exactos. Cada archivo usa un prefijo de hasta 256 KiB y un intervalo de tiles comprimidos de hasta 8 MiB. No descarga archivos completos como fallback. No adquiere Tractor, nexp ni SDSS.

Entradas: C0_DR5_RESOURCE_INVENTORY.json, C0_SUBIMAGE_REPORT.parquet, subimágenes ya verificadas y ledger persistente. Dependencias existentes y fijadas por ASTROPY_DEPENDENCY_LOCK.json. Los dos fragmentos originales del smoke se reutilizan por SHA-256, URL, rango, tamaño total y ETag.

Transferencia nueva estimada: aproximadamente 54 MiB por extrapolación de un único archivo; no es una medición de los otros 41. Límite duro por ejecución: 128 MiB adicionales y 84 solicitudes de datos (se esperan como máximo 82 nuevas con la caché actual). También se aplican los 2 GiB, 1000 solicitudes de datos y contadores de intentos globales existentes. No hay reintentos automáticos. Los cuatro intentos totales por URL del código existente siguen siendo un límite conservador, incluyendo el HEAD y las distintas peticiones Range: no se reinician ni se amplían.

Tiempo estimado: 5–25 minutos, según el servicio. Reservar 160 MiB de disco y hasta 512 MiB de RAM. Si un layout requiere exceder un cap, el script se detiene antes de transferir ese intervalo, sin relajar el límite.

Salidas: fragmentos binarios en c0/probe/range_c0/; C0_RANGE_SUBSET_RESULTS.json con URLs, ETags, límites de bytes, hashes, regiones y comparaciones; C0_RANGE_SUBSET_STATUS.json; manifiesto y resumen de recursos actualizados. Las comparaciones requieren igualdad exacta (NaN equivalentes) y consistencia WCS; no hay normalización, resize, galería ni inspección morfológica.

Log: c0/logs/C0_RANGE_SUBSET.log. Éxito: C0_RANGE_SUBSET_OK y código 0. Fallo: C0_RANGE_EXPERIMENT_FAILED, código 2; detenerse e informar, sin volver a ejecutar por cuenta propia. El éxito del experimento no equivale a aprobar C0-C: el contraste del cutout remuestreado sigue pendiente.

Reanudación después de revisión: mismo comando; reutiliza fragmentos íntegros con procedencia compatible, conserva límites acumulados y reconstruye resultados desde ellos. Los prefijos/tiles ya descargados no se vuelven a pedir. Un fragmento existente con procedencia incompatible causa parada, no se sobrescribe silenciosamente. Los fragmentos fallidos .part y el ledger se conservan para diagnóstico.

AGENTS.md exige delegar «operación bulk sobre catálogos, bricks, frames o imágenes». Por eso el agente ejecutó solo tests y reproducción offline; no ejecutó esta ampliación.
