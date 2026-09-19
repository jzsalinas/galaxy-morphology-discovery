# C0 — semántica FITS, evidencia parcial de un objeto

Muestra: probe_rank=1; selección fijada antes de adquirir imágenes. Fuente exacta y coordenadas en C0_DR5_SMOKE_REQUEST.json; auditoría en C0_DR5_SMOKE_AUDIT.json.

Observado: HTTP 200, 792000 bytes, un HDU PrimaryHDU; BITPIX=-32, arreglo 3×256×256, big endian float32; SURVEY=DECaLS, VERSION=DR5, BANDS=grz. WCS celeste TAN en ejes 1–2; escala 0.262 arcsec/píxel; error de centro 4.42e-9 píxeles. El tercer eje enumera bandas y no se interpreta como coordenada espacial. Sin transformación de datos ni modificación del RAW.

BUNIT ausente: estado INCONCLUSIVE_MISSING_BUNIT a nivel de campo. La documentación DR5 S6 declara nanomaggies/píxel para coadds, pero no se ha contrastado este cutout con un coadd. No se transfiere automáticamente esa unidad al recurso. No es todavía una evaluación formal de C0-C.

No contiene HDUs separados de inverse variance, máscara o número de exposiciones. Fracción finita 100% en las tres bandas; eso no prueba cobertura, ausencia de saturación ni calidad de ruido. Productos auxiliares y PSF pendientes. ANYMASK/ALLMASK y FLUX_IVAR catalogales no se usan como mapas por píxel.

Pendientes: los otros cutouts, asociación Tractor dentro de 1 arcsec conservando candidatas hasta 3 arcsec, comparación con coadd para 12 objetos predefinidos por rank, semántica/calibración y matriz de auxiliares. No se generaron imágenes de visualización ni se evaluó morfología.

## Actualización — lote de cutouts

C0_DR5_CUTOUT_SUMMARY.json registra 96/96 recuperados, cero fallos. C0_PROBE_FITS_REPORT.parquet tiene 96 auditorías de geometría verificadas; error máximo de centro 7.05e-9 píxeles. Todas carecen de BUNIT y tienen un HDU de imagen. No se interpreta finitud como cobertura.

## Actualización — un smoke subimage

`&subimage` para probe_rank=1 devuelve siete HDUs: primario vacío y pares image/invvar para g,r,z. Brick 1853p160, offsets X0=1762/Y0=2985; formas y WCS compatibles entre cada imagen e invvar. No es el mismo grid centrado del cutout remuestreado; no se comparan directamente píxeles por índice entre ambos recursos. Auditoría: C0_SUBIMAGE_SMOKE_AUDIT.json. BUNIT sigue ausente.

La ruta oficial del brick, documentada en S6 y consultada por listado, contiene productos `.fits.fz` y un archivo SHA-256 del proveedor. Esto difiere de los nombres `.fits` de la documentación. Se preserva el listado como DR5_BRICK_1853p160_DIRECTORY.raw; aún no se recuperó ningún coadd completo ni se validó equivalencia pixel a pixel contra el archivo oficial.

## Actualización — lote subimage completo

C0_SUBIMAGE_SUMMARY.json registra 96/96 objetos y 118 bricks únicos. Las auditorías estructurales pasaron: 75 respuestas de siete HDUs, 20 de trece HDUs y una de diecinueve HDUs. Esto refleja solapamiento entre bricks, no objetos adicionales. El mínimo de fracción con peso positivo de una subimagen es aproximadamente 0.73167; no se puede afirmar cobertura válida total basándose en finitud de los cutouts.

Esta evidencia confirma disponibilidad de arrays image/invvar compatibles en las respuestas examinadas, pero no certifica aún unidades ni saturación ni equivalencia exacta con archivos oficiales. Máscara/nexp/PSF permanecen pendientes fuera de este endpoint. Las rutas de bricks no son matches Tractor de fuentes.

## Actualización — subconjunto oficial mediante HTTP Range

La ejecución humana C0_RANGE_SUBSET_OK recuperó fragmentos de 42 archivos oficiales para los doce objetos congelados (ranks 1–12), incluidas las tres bandas y los bricks intersectados. Las 42 comparaciones de regiones nativas contra las subimágenes del servicio presentan igualdad exacta, con NaN equivalentes. Error WCS máximo: 4.460665883222895e-10 píxeles. Las cabeceras oficiales declaran BUNIT=nanomaggy; S6 documenta nanomaggies por píxel. Esta evidencia corresponde a las imágenes, no certifica las unidades de inverse variance.

Verificación local posterior: 84 hashes de fragmentos y todos los hashes registrados de código/entradas coinciden. Evidencia: C0_RANGE_SUBSET_RESULTS.json y C0_RANGE_SUBSET_ACCEPTANCE.json. Transferencia adicional: 53,049,810 bytes, 82 solicitudes de datos. Acumulado: 464,265,663 bytes y 383 solicitudes de datos. No se repitieron adquisiciones.

La procedencia fija URL, ETag, tamaño total y rangos de bytes; no se verificó un checksum del archivo oficial completo. La equivalencia de lectura parcial se probó además sobre FITS comprimidos sintéticos completos. No extrapolar a layouts no soportados.

C0-C sigue pendiente: falta contrastar el cutout normal remuestreado, documentando el algoritmo del servicio sin confundirlo con el remuestreo usado para construir los coadds. No se transfieren automáticamente las unidades al cutout normal ni se aprueba C0-D. Asociación Tractor, nexp, máscara y PSF continúan pendientes; SDSS no se inició.

## Actualización — caracterización inicial del cutout normal

C0_NORMAL_CUTOUT_CHARACTERIZATION.md separa datos observados, documentación/código público fijado, inferencias y supuestos abiertos. Protocolo previo: C0_NORMAL_CUTOUT_PROTOCOL.md. Smoke offline rank 1/g: 62500/65536 píxeles con soporte disponible, residual L2 relativo 2.2561545325609458e-06 frente a una referencia analítica Lanczos-3; no equivalencia certificada. No se identifica el commit desplegado ni se transfiere automáticamente BUNIT. C0-C permanece pendiente. El lote offline de doce objetos queda delegado mediante C0_NORMAL_CUTOUT_HANDOFF.md.

## Actualización — lote normal offline verificado

C0_NORMAL_BATCH_ACCEPTANCE.json confirma 36/36 checkpoints y hashes de entradas/procedencia. Residual L2 relativo frente a referencia analítica: 7.20e-7–5.97e-6. La comparación es parcial, especialmente ranks 3 y 5 (40750 y 17750 píxeles por banda de 65536); no constituye equivalencia completa. Ver actualización en C0_NORMAL_CUTOUT_CHARACTERIZATION.md y auditoría geométrica mínima C0_NORMAL_RANK5_SUPPORT_AUDIT.json. No cambian unidades ni Gate C0-C ni presupuesto; no hubo nuevas adquisiciones.

## Actualización — revisión A/B completa, sin adquisición

C0_OPERATOR_SUPPORT_BATCH_REVIEW.md verifica los 36 checkpoints humanos. La variante prefijada LUT/spline local tiene residual L2 relativo 4.61e-8–8.69e-8 sobre soporte común parcial, sin equivalencia exacta global. El inventario identifica soporte local completo para 33/36 combinaciones; rank 5 conserva 768 píxeles por banda con muestras faltantes. Coste condicionado de cierre: 172146 bytes en seis intervalos/peticiones, no ejecutados. Primero procede aprovechar el soporte cacheado; no se certifican despliegue ni unidades ni se decide C0-C.
