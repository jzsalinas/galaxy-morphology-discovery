# C0 — Registro de discrepancias

Estado: pre-ingesta. No es una decisión global de C0.

| ID | Evidencia | Tratamiento |
|---|---|---|
| D001 | C0-E/§17 y regla global originales son incompatibles | Resuelto por C0_EXECUTION_DECISION_001.md; criticidad por dependencia. |
| D002 | UUIDv5 utiliza índice original y aceptación exige invariancia al orden | Procedencia inmutable conservada; prueba sintética pasa. |
| D003 | .git vacío; Git no reconoce repositorio | Registrado en snapshot; no reparado. |
| D004 | DOI 4196266 es conceptual; API conduce a record 4573248 | Se conserva respuesta original y se consulta record concreto; versión 0.0.2. |
| D005 | CDS declara 253286 filas, artículo usa otros denominadores | Conteo observado pendiente; no se fuerzan coincidencias. |
| D006 | Python del sistema y runtime carecen de PyArrow/Astropy | PyArrow 25.0.1 fijado mediante PyPI para Python 3.12; instalación manual y offline desde rueda verificada. Astropy pendiente para C0.3. |
| D007 | Tres intentos iniciales sin conectividad en sandbox | Registrados como URLError sin contenido; consultas posteriores autorizadas funcionaron. No atribuido a ausencia de datos. |
| D008 | NSA oficial es v1.0.1; selección histórica usa v1.0.0 | No se declara equivalencia literal. Correspondencias pendientes de validación. |
| D009 | Diccionario Zenodo describe petro_th90 con texto de radio 50% | No interpretar ni corregir silenciosamente; contraste con modelo NSA pendiente. |
| D010 | Registro Zenodo license cc-by-4.0; otras fuentes requieren revisión específica de términos | Ningún PASS de licencia global ni Gate F emitido. |
| D011 | Permisos 0700/0400 bajo mismo usuario | Protección de acceso rutinario y separación del código; no constituye aislamiento de seguridad frente al propietario. No mostrar ni analizar valores bloqueados. |

El MD5 del diccionario Zenodo coincide con el declarado; dos recuperaciones independientes tienen igual SHA-256. `VERIFIED` en el manifiesto HTTP indica integridad local de la respuesta; la comprobación del checksum del proveedor se registra aparte.

## D012 — ejecución manual 1

TimeoutError en la solicitud del catálogo antes de obtener cabeceras, cero bytes recibidos. PyArrow instalado correctamente. No hubo ingesta ni acceso a etiquetas. Recuperación de transporte documentada en `c0/reports/C0_RECOVERY_001.md`; no representa un Gate científico FAIL. Timeout manual ajustado de 25 a 120 segundos, sin reintentos automáticos ni cambio de fuente.

## D013 — ejecución manual 2

HTTP 504 del endpoint API, antes de transferir el catálogo; el timeout local de 120 segundos no fue la causa registrada. Dos comprobaciones documentales/HEAD posteriores terminaron en timeout. No se autoriza técnicamente una ruta alternativa ni se recomienda repetir la ingesta sin nueva evidencia. Ver `c0/reports/C0_RECOVERY_002.md`.

## D014 — smoke FITS DR5

El endpoint entrega cubo con VERSION=DR5 y WCS verificable, pero sin BUNIT y sin HDUs de ivar/máscara/nexp. No se interpreta finitud como cobertura. Calibración pendiente de evidencia cutout/coadd; campo unit_status=INCONCLUSIVE_MISSING_BUNIT. Ver C0_FITS_SEMANTICS_REPORT.md. No sustituir por otra release.

## D015 — extensión de productos DR5

S6 documenta image/invvar como `.fits`; el listado oficial de 1853p160 los publica como `.fits.fz`, y nexp también como `.fits.fz`. Usar solo nombres realmente listados y registrar compresión. No inferir tamaños de productos no descargados ni afirmar equivalencia de extracción sin contraste. Archivo documental: DR5_BRICK_1853p160_DIRECTORY.raw.

## D016 — acceso de catálogo por NOIRLab

Se consultó TAP_SCHEMA.tables en el TAP público sugerido por la documentación de acceso a catálogos. `ls_dr5.tractor` no figura; la búsqueda de nombres DR5 devolvió VHS y cruces asociados, no DECaLS. No se sustituyó dataset. Se conserva la ruta oficial NERSC y los metadatos de ambas consultas. No se concluye que todo servicio NOIRLab carezca de DR5; solo que no fue identificado en este esquema consultado.

## D017 — recuperación después de interrupción

Había dos respuestas HTTP Range verificadas y fragmentos íntegros, pero las exportaciones seguían mostrando el checkpoint previo: 299 solicitudes de datos en lugar de 301. No se perdió contabilidad en SQLite; se preservaron las exportaciones antiguas y se regeneraron incluyendo campos específicos de rangos. El experimento original carecía de CLI y pruebas propias; ahora tiene reproducción offline y 44 pruebas totales. Ver C0_RANGE_RECOVERY_001.md. No se repitieron las etapas humanas ni solicitudes de red.

## D018 — procedencia del remuestreo normal aún incompleta

El viewer oficial enlaza código público; se fijaron commits de imagine y astrometry.net y sus hashes. No se observó una certificación de esos commits/dependencias como despliegue productor de los FITS guardados. El código candidato describe Lanczos-3/spline/LUT/media entre bricks, mientras que el smoke local usa una referencia analítica explícitamente distinta. Su residual pequeño no certifica equivalencia ni unidades y excluye píxeles sin soporte completo. C0-C no se decide con este diagnóstico. Ver C0_NORMAL_CUTOUT_PROTOCOL.md y C0_NORMAL_CUTOUT_CHARACTERIZATION.md. No confundir el Lanczos de construcción del coadd (S6) con el operador posterior del viewer.
