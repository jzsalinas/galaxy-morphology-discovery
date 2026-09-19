# Handoff — único diagnóstico offline A/B

Directorio: `/home/jzsalinas/Documents/galaxy-morphology-discovery`.

Comando de ejecución humana:

```bash
c0/.venv/bin/python -m c0_pipeline.operator_support --run --max-read-mib 512 --max-write-mib 192
```

Previsualización opcional sin FITS científico ni compilación:

```bash
c0/.venv/bin/python -m c0_pipeline.operator_support --dry-run
```

## Alcance y coste

Doce objetos congelados × g/r/z; orden 1,2,4,6,7,8,9,10,11,12 y finalmente 3,5. Cuatro variantes previamente declaradas, sin ajuste a residuales. Un proceso local; duración estimada 1–5 minutos según CPU/disco. Aproximadamente hasta 512 MiB RAM; reservar 200 MiB de disco. Límites explícitos de payload IO por invocación: 512 MiB leídos y 192 MiB escritos. Incluyen archivos FITS, fragmentos y checkpoints; overhead de compilador, metadatos y log separado (<8 MiB esperado). Los límites no cambian parámetros científicos. El smoke actual leyó aproximadamente 5.3 MiB y escribió 1.3 MiB.

CERO adquisición: 0 bytes descargados, 0 solicitudes HTTP. No se instala SciPy ni se consulta ningún endpoint. El CLI bloquea eventos de conexión/DNS/urllib en su proceso y no tiene código de adquisición; únicamente puede invocar `cc --version` y compilar el fragmento C local auditado. El ledger se abre readonly y se verifica que sus contadores/intentos no cambien. No toca SDSS, Tractor, nexp, máscaras o PSF.

## Entradas

- C0_PROBE_FITS_REPORT.parquet y C0_SUBIMAGE_REPORT.parquet; FITS normales y subimágenes existentes, con hashes comprobados al usarlos.
- C0_RANGE_SUBSET_RESULTS.json; prefijos y fragmentos de tiles oficiales ya validados. Se verifica integridad, sin nueva descompresión de regiones para ampliar el smoke.
- C0_NORMAL_CODE_SOURCES.json y fuentes locales fijadas. Núcleo de ASTROMETRY_lanczos.i hasta antes del wrapper PyObject, compilado con `cc -O2 -fPIC -shared -ffp-contract=off ... -lm`; no ejecuta el viewer ni módulos Python externos.
- Protocolos congelados, addendum, manifiestos de dependencias y ledger persistente.

## Salidas

- `c0/reports/C0_OPERATOR_SUPPORT_BATCH_RESULTS.json`: métricas por objeto/banda/variante, signo, distribución, cuadrantes, borde/interior, solapamiento, intensidad observada y referencia de intensidad, diferencias de coordenadas/orden.
- `c0/reports/C0_OPERATOR_SUPPORT_BATCH_INVENTORY.json`: bricks candidatos, recortes, tiles/descriptores, rangos presentes/faltantes, deduplicación, cobertura marginal y costes condicionados; intentos y presupuesto restantes. No es autorización de adquisición.
- `c0/reports/C0_OPERATOR_SUPPORT_BATCH_STATUS.json`: estado operativo y código de salida.
- `c0/reports/operator_support/batch/NNN_B/`: checkpoint por objeto/banda con JSON y arrays NPZ ligados por SHA-256. Arrays numéricos para auditoría, sin galerías.
- `c0/reports/operator_support/batch/provenance.json`, `implementation.py`: versiones y copia del código ejecutado.
- `c0/provenance/operator_build/<hash>/`: fuente C extraída, binario y registro de compilador/flags/entorno/hashes.

Log append-only: `c0/logs/C0_OPERATOR_SUPPORT_BATCH.log`.

## Éxito, fallos y reanudación

Éxito: **C0_OPERATOR_SUPPORT_OK**, código 0. Significa únicamente que los 36 diagnósticos A/B terminaron y el ledger no cambió. **NO significa C0-C PASS**.

Fallo: **C0_OPERATOR_SUPPORT_FAILED**, código 2, con razón compacta en status/log. No hay reintentos ni fallback de red. Un límite de IO, hash incompatible, layout no soportado o archivo corrupto detiene la ejecución. Informar el fallo antes de reintentar.

Después de interrupción, es seguro reanudar con el mismo comando tras revisar el estado: los checkpoints completos se validan por procedencia y hashes, y se reutilizan sin repetir cálculos. También se verifican sus entradas locales; esta lectura no es una nueva adquisición. Los ficheros `.part` y payloads anteriores se preservan. Un checkpoint de otra versión se rechaza; no borrarlo para forzar continuidad. No ejecutar simultáneamente otra etapa C0.

El orden primario/ secundario se preserva incluso al reanudar. Los resultados de los diez primeros objetos quedan en sus checkpoints antes de procesar ranks 3 y 5; no se usa su resultado para modificar variantes posteriores.

## Interpretación pendiente

Los mínimos de bytes corresponden a payloads comprimidos necesarios bajo las coordenadas y bricks candidatos conocidos, reutilizando también píxeles de subimágenes nativas. El mínimo de peticiones de rango simple para esos bytes no es un mínimo universal de solicitudes: multipart no está validado y reducir peticiones podría requerir bytes extra. Se reporta esa distinción y si el plan mínimo viola intentos por URL. Ninguna envolvente ni nuevo umbral se convierte en obligación de adquirir.

Después de la ejecución humana se revisarán resultados contra el protocolo. No se decide de antemano adquisición, PASS, FAIL ni INCONCLUSIVE. C0-C sigue PENDING.

Delegación obligatoria: AGENTS.md exige ejecución humana para «operación bulk sobre catálogos, bricks, frames o imágenes». El agente ejecutó solo pruebas y rank 1/g, nunca el lote de 36.
