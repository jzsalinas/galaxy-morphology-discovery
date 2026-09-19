# Cutout normal DR5 — caracterización parcial, sin decisión de C0-C

## Evidencia observada

La equivalencia nativa Range–subimage permanece limitada a 42 archivos, los doce objetos congelados y los layouts soportados. No se extrapola al cutout normal. Los 96 cutouts normales ya recuperados tienen DR5 explícito, tres bandas y WCS/centro válidos; carecen de BUNIT y de commit del servicio en sus cabeceras examinadas.

El smoke nuevo usa únicamente rank 1, banda g, y archivos locales verificados. De 65536 píxeles, compara 62500 con soporte 7×7 completo; excluye 3036 por soporte desconocido, no por una selección astronómica. No hay NaN nativos en esta entrada. Frente a la referencia analítica prefijada: RMS residual 3.3285044654656886e-08; máximo absoluto 8.928213053871481e-07; L2 relativo 2.2561545325609458e-06; cero píxeles exactamente iguales. Las unidades de estos residuales absolutos son las de los valores numéricos de entrada; no asignan por sí solos BUNIT al servicio.

Artefactos: C0_NORMAL_SMOKE_RESULTS.json; C0_NORMAL_SMOKE_STATUS.json; normal_cutout/smoke_001_g.json. No hubo ajuste de ganancia, offset, centro, escala o kernel. No hubo descargas de imágenes. Las 49 pruebas locales pasan (test_normal_cutout_002.log), incluidos soporte, constantes, impulso sintético, propagación de NaN y distinción entre soporte desconocido y contribución no finita. Los tests sintéticos verifican la referencia, no el despliegue remoto.

## Documentación y código externos utilizados

- [DR5 files](https://www.legacysurvey.org/dr5/files/), snapshot S6.raw, líneas 1995–2013: coadds ponderados por inverse variance, nanomaggies/píxel, remuestreo Lanczos-3 en su construcción. Es el operador anterior al viewer; no se deduce de aquí el algoritmo del cutout.
- [Página oficial del viewer](https://www.legacysurvey.org/viewer/), VIEWER_HOME.raw, línea 2002: enlaza el repositorio legacysurvey/imagine. La página no certifica un commit desplegado.
- [Implementación pública fijada](https://github.com/legacysurvey/imagine/blob/d1b54504be1a8d9037989af14f0befacf96bf4b6/map/views.py): dispatcher en map/cutouts.py y map/urls.py; rama DR5 genérica ReDecalsLayer; escala 0 a 0.262 arcsec/píxel; WCS TAN centrada en (width+1)/2, (height+1)/2. write_cutout llama render_rgb con get_images_only=True y retorna antes de la transformación RGB. Esta ruta candidata no aplica stretch/asinh ni JPEG a los valores FITS.
- En ese código, render_into_wcs recorta una región del brick con margen 10, remuestrea por WCS, elimina contribuciones no finitas y acumula imágenes float32. get_pixel_weights retorna 1; RenderAccumulatorImage divide por suma de pesos, con cero donde no hubo contribución. No se observa factor de área de píxel en esa ruta a escala 0. La disponibilidad y selección geométrica de bricks pueden afectar qué contribuciones entran; no equivalen a concatenar todas las subimágenes.
- [Dependencia pública fijada](https://github.com/dstndstn/astrometry.net/blob/d20a0503739e74b02418cde2e7d65013dadac579/util/resample.py): defaults L=3, spline=True, splineStep=25, splineMargin=12, cinterp=True; coordenadas spline convertidas a float32; fallback a WCS directa si el solapamiento no permite spline.
- [Kernel C fijado](https://github.com/dstndstn/astrometry.net/blob/d20a0503739e74b02418cde2e7d65013dadac579/util/lanczos.i): LUT de 1024 intervalos por unidad, interpolación lineal de tabla, soporte 7×7, normalización por suma de coeficientes; índices recortados al borde del array suministrado. No hay reemplazo de NaN dentro del kernel. El caller elimina posteriormente valores no finitos.

Los dos commits son snapshots públicos independientes, NO un par de versiones desplegadas certificado. URLs finales, timestamps UTC, estados HTTP, tamaños y SHA-256 están en C0_NORMAL_CODE_SOURCES.json y C0_REMOTE_FILE_MANIFEST.csv. No se ejecutó código externo descargado. La referencia local es una implementación analítica distinta, declarada en el protocolo.

## Inferencias

El smoke es compatible con un operador próximo a Lanczos-3 sobre los valores nativos, pero no demuestra cuál versión/camino lo produjo. Las diferencias conocidas de LUT, spline, WCS y aritmética podrían explicar residuales; aún no se ha calculado una cota que lo demuestre. No se atribuye causalmente el residual a redondeo sin esa prueba.

La ruta pública candidata mantiene la escala numérica de las muestras mediante kernel normalizado y media entre bricks. Esto no demuestra conservación de flujo integrado, integrales sobre píxeles de salida ni propagación de ruido. Tampoco fija unidades del servicio desplegado sin cerrar la cadena de evidencia.

## Supuestos no resueltos

Commit/dependencias/configuración desplegados; tabla efectiva de disponibilidad de bricks, selección y orden; reglas efectivamente ejecutadas en NaN y bordes; efecto numérico de spline/LUT/float32; equivalencia del cutout completo, incluyendo los píxeles sin soporte local; calibración formal del producto remuestreado. No se generaliza a otra escala, rotación, release o tamaño.

## Alcance de equivalencias

Equivalencia exacta demostrada: solamente regiones nativas Range–subimage del subconjunto anterior. Nueva referencia: ninguna equivalencia certificada. Comparación numérica de 62500 píxeles interiores de una banda de un objeto; no implica equivalencia de todo el cutout ni de los otros once objetos. La conservación de un campo constante en tests sintéticos no equivale a conservación de flujo de una fuente.

## Estado y siguiente paso

C0-C continúa PENDIENTE DE EVALUACIÓN, no PASS ni una decisión formal INCONCLUSIVE. Criterios previos en C0_NORMAL_CUTOUT_PROTOCOL.md. Si al cierre persiste falta de semántica verificable, el addendum exige INCONCLUSIVE y STOP; no se elude esta regla con el diagnóstico.

Se entrega CLI offline para 12 objetos × 3 bandas. Produce residuales y fracciones explícitas sin tolerancia ajustable ni decisión automática. Después de revisar sus artefactos se decidirá si hace falta reproducir fielmente el operador y resolver bordes/procedencia; no se fija un umbral retrospectivo para aprobar. No se inició SDSS, Tractor, nexp, máscaras ni PSF.

Contabilidad actual: 465348528 bytes (~443.79 MiB), 383 solicitudes no metadata; nueve consultas documentales nuevas sumaron 1082865 bytes. El total HTTP es 936, distinto del contador limitado de solicitudes de datos. Todos los límites acumulados se preservan.

## Verificación del lote humano — 2026-09-17

C0_NORMAL_BATCH_OK confirmado mediante los 36 checkpoints, coincidencia exacta con el resumen, hashes actuales de entradas FITS y procedencia. No se repitió el procesamiento ni ninguna adquisición. Registro reproducible: C0_NORMAL_BATCH_ACCEPTANCE.json, ligado al SHA-256 del resultado.

Los 36 residuales L2 relativos abarcan 7.204108629270602e-07 a 5.965528323041554e-06 (mediana 2.1340413573073152e-06). Se compararon 2050500 de 2359296 píxeles. Por banda: diez objetos tienen 62500/65536 píxeles comparados; rank 3 tiene 40750/65536 y rank 5 solo 17750/65536. Por lo tanto la caracterización no demuestra equivalencia de los cutouts completos. Los campos observado no finito son cero; no se interpreta como cobertura válida. No se adoptó una tolerancia retrospectiva.

Una comprobación geométrica mínima de rank 5/g, usando solo cabeceras y tablas de tiles existentes, muestra dos bricks: uno contiene geométricamente los centros de 20224 píxeles de salida y otro los 65536. La intersección conservadora de soportes del diagnóstico explica por qué su fracción comparada es pequeña; no prueba ausencia de datos en el resto. Las envolventes de tiles calculadas para incluir el soporte ampliado no están enteras en caché para ninguno de esos dos archivos. No se descargó nada. Evidencia: C0_NORMAL_RANK5_SUPPORT_AUDIT.json. Ese cálculo no certifica la selección desplegada de bricks ni propone transferir toda la envolvente como mínimo necesario.

Siguiente requisito científico: resolver por separado (1) la precisión y procedencia del operador candidato y (2) el soporte completo y la pertenencia geométrica por brick. Antes de cualquier adquisición adicional se debe inventariar qué tiles exactos faltan y su coste, reutilizando los ya presentes y respetando intentos acumulados. Un cálculo de envolvente no autoriza redescargar fragmentos. No ampliar muestra ni ajustar el operador buscando menor residual.

C0-C permanece pendiente de evaluación. Este lote no autoriza PASS, ni demuestra por sí solo FAIL del servicio. Si al cierre no puede verificarse la semántica, debe emitirse INCONCLUSIVE/STOP conforme al addendum. Contadores sin cambios: 465348528 bytes y 383 solicitudes de datos. SDSS y los demás productos continúan sin iniciarse en esta etapa.
