# OC-3 — especificación prospectiva de la sonda acotada del contrato físico del proveedor

**Fecha:** 2026-09-18  
**Estado documental:** especificación prospectiva; no implementada, no autorizada y no ejecutada.  
**Ámbito de autorización futuro:** `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Estado científico:** `OC-3 REMAINS NOT STARTED.`

## 1. Autoridad, integridad y precedencia

Antes de crear esta especificación se verificaron localmente los bytes de las autoridades y evidencias exigidas:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md` | `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b` |
| `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md` | `d02815a66f27df67e60f0cb1dc4d38a977e70c492417d3397946911159bf31c9` |
| `OC3_AMENDMENT_003_IMPLEMENTATION_REPORT.md` | `a1a02a2cdbb0daa697854c74d9c57cc44697a4486ff3547523271fe7cf90b2eb` |

También se verificaron:

- agregado de implementación actual, recalculado mediante la regla vigente sobre los 14 archivos Python bajo `oc3`, excluyendo `.venv`: `e374e482cc97c66399025c2bbe0776749dcbd8451998edd441bab165c03fd683`;
- fingerprint ambiental, recalculado sobre la serialización canónica del objeto `state` de `oc3/environment_setup/ENVIRONMENT.json`: `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`;
- SHA-256 de `oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json`: `09c9676e9f7f3b2ce8f063aa63b34fcc7d40fe3299cb898ecfdb76b95522a38e`.

Una discrepancia en cualquiera de estos bindings habría impedido crear este documento. El SHA-256 de esta especificación se calcula sobre sus bytes finales y se informa fuera de ella para evitar autorreferencia.

Esta especificación añade una compuerta de instrumentación y procedencia anterior al bootstrap. No modifica la pregunta científica, los criterios de selección, los límites de ejecución científica ni ninguna regla de Amendments 001–003. Si una evidencia futura exige corregir una expectativa documental del esquema físico, esa corrección requerirá una enmienda prospectiva separada antes de habilitar `ProviderSchemaAdapter` en producción.

## 2. Pregunta exclusiva y exclusiones

La sonda responde solamente:

> ¿Pueden establecerse los contratos físicos FITS exactos que necesita `ProviderSchemaAdapter` usando metadata estructural del proveedor, sin observar, decodificar ni utilizar ningún valor de fila o celda del proveedor?

Es una pregunta de instrumentación y procedencia. La sonda no es una etapa de selección de bricks, análisis de cobertura, exploración astronómica, selección de metadata para bootstrap ni ejecución científica OC-3. No puede producir candidatos, escoger bricks, evaluar cobertura, materializar una tabla proveedor ni iniciar el bootstrap.

## 3. Frontera estricta de observación

### 3.1 Observación permitida

Se permite observar exclusivamente:

1. metadata de transporte HTTP fijada en §7; y
2. metadata estructural de cabeceras FITS necesaria para describir el contrato físico.

Las tarjetas FITS permitidas son:

- `SIMPLE`, `XTENSION`, `BITPIX`, `NAXIS`, `NAXIS1`, `NAXIS2`, `PCOUNT`, `GCOUNT`, `TFIELDS`;
- `TTYPEn`, `TFORMn`, `TUNITn`, `TNULLn`, `TSCALn`, `TZEROn`;
- `EXTNAME`, `CHECKSUM`, `DATASUM`;
- las tarjetas mínimas que el estándar FITS requiera para delimitar inequívocamente una cabecera y calcular sus límites estructurales, sin interpretar datos;
- offsets y límites exactos de tarjetas, bloques de 2880 bytes, cabeceras y HDUs.

`NAXIS2` se registra únicamente como cardinalidad estructural declarada por la cabecera. No autoriza iteración, estadística ni observación de filas. Las tarjetas `CHECKSUM` y `DATASUM`, si existen, se registran como valores estructurales declarados; sin el payload completo no se consideran verificadas.

### 3.2 Observación prohibida

Queda prohibido:

- interpretar, decodificar, deserializar o materializar una fila o celda;
- examinar filas iniciales, finales, de ejemplo o elegidas por cualquier criterio;
- calcular estadísticas sobre valores, incluidos conteos derivados de iterar filas, mínimos, máximos, unicidad, distribuciones o membresía;
- imprimir, registrar, hashear como registro lógico o persistir valores de tabla;
- inferir candidatos o seleccionar bricks;
- usar valores astronómicos, geométricos, de cobertura o procedencia contenidos en filas.

## 4. Allowlist exacta de recursos

### 4.1 Recursos FITS

| Rol | URL exacta | Representación esperada |
|---|---|---|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | FITS comprimido con gzip |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | FITS comprimido con gzip |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | FITS comprimido con gzip |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | FITS sin compresión de archivo |

### 4.2 Manifiestos de checksums

| Rol | URL exacta |
|---|---|
| `ROOT_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/legacysurvey_dr9.sha256sum` |
| `NORTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/legacysurvey_dr9_north.sha256sum` |
| `SOUTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/legacysurvey_dr9_south.sha256sum` |

La allowlist es cerrada. Se prohíben crawling de directorios, búsquedas, índices no listados, mirrors, DR9sv, coadds, Tractor, catálogos de fuentes, parámetros de consulta y descubrimiento dinámico de URLs. Una URL de redirección no incluida prospectivamente en una autorización válida no puede seguirse.

## 5. Autorización separada y binding del comando

Se define el alcance humano `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`, separado de `METADATA_BOOTSTRAP_ONLY`. Autorizar uno no autoriza el otro.

Antes de una futura ejecución real deberá existir un registro de autorización revisable que ligue, como mínimo:

1. SHA-256 de los bytes finales de esta especificación;
2. agregado de implementación que vaya a ejecutarse;
3. fingerprint ambiental aplicable;
4. las siete URLs exactas y sus roles;
5. hosts, métodos y cabeceras permitidos;
6. rangos exactos y límites de bytes, solicitudes, reintentos, concurrencia y recursos;
7. directorio de ejecución aislado;
8. regla de cero observación de filas;
9. bytes exactos y SHA-256 del comando autorizado;
10. identidad de la implementación sintéticamente verificada;
11. reglas de fallo cerrado, reanudación y resultados terminales.

La mera existencia de esta especificación, de una implementación o de una opción de CLI no constituye autorización. El registro futuro no será un manifiesto de bootstrap, un registro de derechos de producción ni el ledger científico OC-3.

## 6. Métodos y conducta HTTP

Para los cuatro recursos FITS solo se permiten `HEAD` y `GET` con `Range` acotado. Para los tres manifiestos textuales se permite `HEAD` y un `GET` completo sujeto al límite agregado de §17. No se permite un `GET` FITS sin `Range`.

Cada petición deberá usar la URL literal autorizada, sin cookies, autenticación ni parámetros de consulta. Para conservar la identidad binaria de los rangos se solicitará `Accept-Encoding: identity`. Una codificación de contenido de transporte que cambie la representación direccionada por bytes provoca `PROBE_TRANSPORT_INTEGRITY_FAILURE`.

Las respuestas de cuerpo se consumirán mediante streaming y se abortarán al alcanzar el menor de los límites aplicables. Los bytes efectivamente recibidos se contabilizan incluso si luego se rechaza la respuesta. Ninguna respuesta puede ampliar la allowlist.

## 7. Etapa HEAD

Por recurso, `HEAD` puede registrar únicamente:

- URL solicitada y URL final;
- estado HTTP;
- `Content-Length`;
- `Content-Type`;
- `ETag`;
- `Last-Modified`;
- `Accept-Ranges`;
- timestamp UTC de transporte;
- identidad TLS y del host, cuando la biblioteca la exponga sin otra solicitud.

`HEAD` no establece estructura FITS, validez de checksum ni identidad del contenido. `Accept-Ranges: none` demuestra indisponibilidad para esta sonda. La ausencia de `Accept-Ranges` queda como desconocida y solo una respuesta `206` válida a uno de los rangos exactos autorizados puede demostrar soporte.

Una petición Range requiere estado `206` y un `Content-Range` sintáctica y numéricamente congruente con la URL y el rango solicitado. Una respuesta `200` a Range se rechaza, su cuerpo no se acepta como FITS completo y el proceso termina como `PROBE_RANGE_UNAVAILABLE_STOP`. `416`, soporte explícitamente ausente o imposibilidad equivalente también producen `PROBE_RANGE_UNAVAILABLE_STOP`. Estado, rango, longitud o identidad de representación contradictorios producen `PROBE_TRANSPORT_INTEGRITY_FAILURE`.

No existe fallback a descarga completa.

## 8. Modelo de prefijos FITS

El máximo de bytes de cuerpo FITS recibidos por recurso es 262144 bytes, equivalentes a 256 KiB. El tamaño máximo de cada fragmento es 65536 bytes, equivalentes a 64 KiB. Solo se permiten, en este orden, hasta cuatro rangos contiguos:

1. `bytes=0-65535`;
2. `bytes=65536-131071`;
3. `bytes=131072-196607`;
4. `bytes=196608-262143`.

La ejecución deja de solicitar fragmentos en cuanto se conoce el límite completo de la cabecera BINTABLE requerida. No se puede saltar un rango, ampliar uno, solicitar sufijos, hacer rangos múltiples ni adaptar el máximo después de observar un resultado parcial.

Si la cabecera requerida no se recupera dentro del cuarto fragmento, se registra el evento `PHYSICAL_CONTRACT_HEADER_CAP_INSUFFICIENT` y el resultado terminal `PROBE_HEADER_CAP_INSUFFICIENT`. No se ensaya un quinto rango ni otra fuente.

## 9. Parser FITS estructural

El parser futuro será específico para cabeceras. Consumirá tarjetas de 80 bytes y reconocerá el cierre de cada cabecera por una tarjeta `END` válida más el padding hasta el siguiente límite de 2880 bytes. Rechazará cabeceras truncadas, tarjetas obligatorias contradictorias, longitudes imposibles, overflow de aritmética estructural y duplicados ambiguos de campos normativos.

El parser no podrá exponer una API de filas. Su salida contendrá solo las tarjetas permitidas, su orden, los offsets de cabecera y el contrato de columnas. No entregará el buffer posterior a una biblioteca de tablas.

Para una BINTABLE, el orden de columnas se deriva exclusivamente de `TFIELDS` y de los pares `TTYPEn`/`TFORMn`, con presencia y valor estructural de `TUNITn`, `TNULLn`, `TSCALn` y `TZEROn`. Las formas vectoriales o arrays se conservan literalmente en `TFORMn`; no se materializa un elemento.

## 10. Regla para los tres archivos `.fits.gz`

Los bytes conservados son el prefijo comprimido exacto autorizado. Se usa un descompresor gzip incremental único y secuencial. Los fragmentos 2–4 continúan el estado de los anteriores; nunca se intenta iniciar descompresión en medio del stream. En una reanudación, los fragmentos ya verificados pueden releerse localmente desde byte cero para reconstruir el estado sin nueva red.

El descompresor deberá recibir entrada de manera incremental y usar un límite explícito de salida. Solo puede emitir los bytes no comprimidos todavía necesarios para completar:

1. la cabecera primaria;
2. la comprobación de seguridad entre HDUs de §12; y
3. la cabecera BINTABLE objetivo hasta su límite de bloque de 2880 bytes.

En cuanto el parser conoce y alcanza ese límite, no se permite otra llamada que pueda emitir salida. Un fragmento comprimido puede contener información que representaría bytes posteriores, pero esos bytes permanecen opacos y comprimidos. No pueden convertirse en bytes de registros de tabla, aunque sea de forma transitoria en memoria.

Se registran por separado y de forma monótona:

- `wire_bytes_received`: bytes de cuerpo HTTP recibidos para el recurso;
- `compressed_bytes_consumed`: bytes entregados efectivamente al estado gzip;
- `uncompressed_header_bytes_emitted`: bytes de cabeceras FITS emitidos al parser.

Debe cumplirse que la salida no comprimida termina exactamente en el límite del bloque de la cabecera BINTABLE requerida. Cualquier emisión posterior constituye `PROBE_ROW_OBSERVATION_FORBIDDEN`, incluso si ningún valor llegó a decodificarse, y termina como `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`.

## 11. Regla para la patch list sin compresión

`dr9-south-patched-bricks.fits` usa los mismos cuatro rangos de prefijo y los mismos límites. El consumidor entrega al parser solo cabeceras completas y corta exactamente en el límite de la cabecera BINTABLE objetivo. No lee ni conserva como evidencia bytes posteriores a ese límite; cualquier exceso de transporte inevitable dentro de la respuesta se contabiliza y descarta sin interpretarlo.

La sonda puede establecer `HDU index`, `XTENSION`, `EXTNAME`, `NAXIS1`, `NAXIS2`, `PCOUNT`, `GCOUNT`, `TFIELDS`, los metadatos estructurales de columnas y las tarjetas estructurales de checksum. Puede comparar el `NAXIS2` declarado con la afirmación documental `1691` solo como comprobación de cardinalidad estructural. No enumera ni observa membresía.

## 12. Seguridad del HDU primario y HDUs intermedios

La sonda puede avanzar secuencialmente desde la cabecera primaria a la cabecera siguiente solo si las tarjetas estructurales demuestran que el payload del HDU precedente tiene longitud cero. La longitud se calcula con aritmética FITS estructural validada y sin leer datos.

Si un HDU inesperado con payload no nulo precede a la tabla requerida, o si alcanzar otra cabecera exige descargar, descomprimir, saltar o inspeccionar payload, se registra `INTERVENING_DATA_PAYLOAD_STOP`. No se atraviesa el payload. El recurso queda sin contrato completo y solo puede contribuir a `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`, salvo que otro fallo de mayor precedencia determine el resultado terminal.

## 13. Manifiestos de checksum

Los tres manifiestos NERSC se adquieren como texto bajo el límite agregado de §17. El parser extrae únicamente una entrada exacta, no ambigua y vinculada al nombre esperado por manifiesto:

| Rol | Nombre exacto | SHA-256 documental esperado |
|---|---|---|
| root | `survey-bricks.fits.gz` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| north | `survey-bricks-dr9-north.fits.gz` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| south | `survey-bricks-dr9-south.fits.gz` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

Una entrada ausente, duplicada, malformada, asociada a otro path o con hash diferente produce `PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP` y el resultado `PROBE_PROVIDER_DOCUMENTATION_CONFLICT`. El checksum publicado se registra como identidad documental esperada; el prefijo FITS no permite verificar el checksum del archivo completo y no se afirma lo contrario.

No hay una fuente de checksum autorizada para la patch list. Si el recurso autorizado no aporta uno en sus cabeceras y ninguna autoridad ya congelada lo documenta, se registra `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`. Este resultado negativo no permite inventar, extrapolar ni sustituir un checksum de proveedor. Un hash del prefijo o de la evidencia local no se presenta como checksum del archivo completo.

## 14. Pregunta física de `brickid`

El estado documental previo es:

- `BRICKID` root documentado como `int32`;
- `brickid` regional documentado como `int16`;
- otros productos DR9 documentan Brick IDs en el intervalo `[1, 662174]`.

La sonda observa exclusivamente el `TTYPE` y `TFORM` estructural correspondiente. No observa un valor `brickid`, no verifica rangos empíricos y no deriva membresía.

El resultado secundario será exactamente uno de:

- `BRICKID_PHYSICAL_LAYOUT_SUPPORTS_DOCUMENTATION`: todos los layouts requeridos se recuperaron y sus `TFORM` coinciden con la expectativa documental aplicable;
- `BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`: al menos un `TFORM` recuperado contradice inequívocamente la expectativa;
- `BRICKID_PHYSICAL_LAYOUT_UNRESOLVED`: falta la cabecera, el campo es ambiguo/ausente o el contrato no puede establecerse dentro de las reglas.

Una demostración de `int32` regional no reescribe Amendment 003. Se documenta como conflicto que exige corrección prospectiva separada.

## 15. Contrato físico candidato y evidencia

Para cada rol FITS, una futura ejecución puede producir un candidato de contrato con estos campos y ningún dato adicional:

- rol, URL solicitada y URL final;
- estado HTTP y metadata HEAD permitida;
- compresión y representación de transporte;
- índice de HDU, `XTENSION` y `EXTNAME`;
- `BITPIX`, `NAXIS`, `NAXIS1`, `NAXIS2`, `PCOUNT`, `GCOUNT`, `TFIELDS`;
- lista ordenada de columnas con `TTYPE`, `TFORM` y presencia/valor de `TUNIT`, `TNULL`, `TSCAL`, `TZERO`;
- offsets y límite exacto de la cabecera;
- `CHECKSUM`/`DATASUM` estructurales, marcados como no verificados cuando falte el payload;
- checksum del manifiesto proveedor cuando corresponda, marcado como documental y no verificado contra el archivo completo;
- hashes SHA-256 de fragmentos exactos, cabeceras emitidas y artefactos de evidencia;
- los tres contadores gzip cuando corresponda;
- estados, discrepancias y resultado secundario de `brickid`.

No contendrá valores de tabla. La evidencia de transporte y la interpretación contractual serán artefactos separados.

## 16. Firewall duro de filas

La implementación futura deberá impedir por construcción cualquier ruta que pueda materializar datos de filas. Cualquiera de estas acciones produce inmediatamente `PROBE_ROW_OBSERVATION_FORBIDDEN` y el resultado terminal `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`:

- acceder a `hdu.data`;
- llamar `astropy.table.Table.read` o una API equivalente de tablas;
- decodificar, deserializar o iterar un registro BINTABLE o una celda;
- registrar una fila o un valor;
- calcular estadísticas a partir de valores;
- invocar `ProviderSchemaAdapter` para decodificar filas candidatas;
- invocar `resolve_bootstrap_bricks`;
- invocar selección, cobertura o proyección técnica;
- emitir bytes no comprimidos posteriores al límite de cabecera BINTABLE requerido.

El proceso no debe importar código de selección salvo en tests sintéticos que demuestren que su invocación está bloqueada. El firewall tiene precedencia sobre cualquier resultado parcial útil y no admite reanudación automática del intento comprometido.

## 17. Límites independientes de recursos

| Recurso | Límite rígido |
|---|---:|
| Cuerpo FITS | 4 recursos × 256 KiB = 1 MiB máximo |
| Cuerpo de manifiestos textuales/documentales | 8 MiB agregados máximo |
| Cuerpo HTTP total | 9 MiB máximo |
| Solicitudes HTTP totales | 32 |
| Concurrencia | 1 |
| Reintentos | 1 intento adicional por identidad exacta recurso/método/rango |
| RAM | 512 MiB |
| Disco | 64 MiB |
| Lectura/escritura local | 256 MiB |
| Cómputo activo | 300 s |
| Tiempo de pared | 900 s |
| Threads | 1 |
| GPU | ninguna |

Los límites incluyen respuestas fallidas, rechazadas, parciales y recibidas antes de un crash. Alcanzar un límite detiene nuevas operaciones. Los 9 MiB son un máximo global de cuerpos, no dos presupuestos reutilizables.

Estos son límites de `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`. No redefinen ni consumen el ledger global científico de Amendment 002 porque la sonda es una caracterización de instrumento separada. Sus resultados solo podrán citarse por hash en un bootstrap de producción autorizado posteriormente.

## 18. Aislamiento de salidas

Toda futura salida residirá exclusivamente bajo:

`oc3/provider_contract_probe/`

La implementación deberá crear un directorio de intento inmutable y único dentro de esa raíz. Como mínimo distinguirá:

- autorización y binding del comando;
- ledger específico de la sonda;
- eventos HTTP y contabilidad;
- fragmentos comprimidos exactos;
- cabeceras estructurales emitidas;
- entradas de manifiestos;
- candidatos de contrato físico;
- discrepancias;
- resultado terminal y recibo de ejecución.

No escribirá en `oc3/INPUTS`, `oc3/provenance`, `oc3/RAW_IMMUTABLE`, `oc3/TECHNICAL_INDEX` ni `oc3/reports`. Tampoco creará o actualizará manifiestos de bootstrap, registros de derechos o el ledger de producción OC-3.

## 19. Identidad, crash, retry y reanudación

La identidad inmutable de cada operación incluirá:

- URL exacta;
- método;
- valor exacto de `Range`, o ausencia para `HEAD`/manifiesto;
- rol esperado;
- SHA-256 de esta especificación.

Antes de enviar una solicitud se reserva en el ledger de la sonda su identidad y presupuesto. Los bytes recibidos se contabilizan de forma conservadora aun si hay error, timeout, excepción o crash. Un reintento conserva exactamente URL, método, rango y rol; no puede solicitar otra porción ni usar otro proveedor.

La reanudación puede reutilizar fragmentos locales solo si su identidad, longitud, `Content-Range`, validaciones y SHA-256 están completos y coinciden con el ledger. Un fragmento incompleto no se concatena ni se trata como evidencia. Para gzip, la reanudación reconstruye el estado desde el primer fragmento local verificado. No se reanuda desde un offset no autorizado del stream comprimido.

El máximo de un reintento adicional se aplica individualmente a cada identidad exacta. No hay bucles de retry, backoff prolongado, fallback de host ni redescubrimiento.

## 20. Verificación sintética obligatoria anterior a red

Antes de solicitar autorización humana para una sonda real, la implementación deberá superar offline, con fixtures locales y red bloqueada, al menos:

1. contabilidad de `HEAD` sin cuerpo;
2. `Accept-Ranges` soportado, ausente y explícitamente no soportado;
3. enforcement literal de los cuatro rangos;
4. requisito de `206` y rechazo de `200` a Range;
5. validación completa de `Content-Range`;
6. tope de 256 KiB por FITS y máximo de cuatro fragmentos;
7. extracción de cabecera gzip en uno y varios fragmentos;
8. límites de salida que impidan emitir un solo byte de fila;
9. reconstrucción local del estado gzip al reanudar;
10. ruta de HDU primario con `NAXIS=0`;
11. `INTERVENING_DATA_PAYLOAD_STOP`;
12. extracción de cabecera de patch list sin compresión;
13. contrato BINTABLE, orden de columnas y arrays en `TFORM`;
14. presencia/valor de `TUNIT`, `TNULL`, `TSCAL` y `TZERO`;
15. prohibiciones de `hdu.data`, `Table.read`, decodificador de filas/celdas y `ProviderSchemaAdapter` candidato;
16. prohibición de invocar selección o `resolve_bootstrap_bricks`;
17. parsing exacto de entradas de manifiesto, duplicados, ausencias y conflictos;
18. ausencia de checksum de proveedor para patch list conservada como no resuelta;
19. contabilidad y límites tras crash/retry/resume;
20. dry-run/offline con cero red, cero escritura productiva y cero filas;
21. regresión completa previa: 182 tests pasan, 0 fallan y 0 se omiten.

Los tests usarán FITS y respuestas HTTP sintéticas construidas para incluir canarios después del límite de cabecera. Deberán demostrar que esos canarios no aparecen en memoria observable, logs ni artefactos. No se usará red real durante implementación o verificación sintética.

## 21. Resultados terminales y precedencia

Cada intento real deberá terminar con exactamente uno de estos resultados:

| Resultado | Condición |
|---|---|
| `PROBE_PHYSICAL_CONTRACTS_RESOLVED` | Los cuatro contratos estructurales requeridos quedan completos dentro de las reglas; los tres checksums publicados coinciden; no hubo violación ni conflicto. La ausencia documentada de checksum de patch list puede permanecer como `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`. |
| `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED` | Se obtuvo evidencia estructural válida para uno o más roles, pero al menos un contrato queda sin resolver por información insuficiente o `INTERVENING_DATA_PAYLOAD_STOP`, sin conflicto inequívoco ni fallo de integridad. |
| `PROBE_PROVIDER_DOCUMENTATION_CONFLICT` | Una cabecera estructural inequívoca o un manifiesto autorizado contradice la documentación congelada. Incluye `PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP`. |
| `PROBE_HEADER_CAP_INSUFFICIENT` | Alguna cabecera requerida no termina dentro del prefijo rígido de 256 KiB. |
| `PROBE_RANGE_UNAVAILABLE_STOP` | Un recurso FITS requerido no admite los rangos exactos necesarios y no existe fallback permitido. |
| `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE` | Se intentó o produjo cualquier observación/emisión prohibida por el firewall de filas. |
| `PROBE_TRANSPORT_INTEGRITY_FAILURE` | La identidad, estado, rango, longitud, representación, redirect o contabilidad de transporte no puede validarse de acuerdo con esta especificación. |

La precedencia para elegir el único terminal es:

1. `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`;
2. `PROBE_TRANSPORT_INTEGRITY_FAILURE`;
3. `PROBE_PROVIDER_DOCUMENTATION_CONFLICT`;
4. `PROBE_RANGE_UNAVAILABLE_STOP`;
5. `PROBE_HEADER_CAP_INSUFFICIENT`;
6. `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`;
7. `PROBE_PHYSICAL_CONTRACTS_RESOLVED`.

Los eventos secundarios `PHYSICAL_CONTRACT_HEADER_CAP_INSUFFICIENT`, `INTERVENING_DATA_PAYLOAD_STOP`, `PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP`, `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`, `PROBE_ROW_OBSERVATION_FORBIDDEN` y el resultado de `brickid` se conservan aunque el terminal sea determinado por una condición de mayor precedencia.

## 22. Criterio de éxito y resultados negativos válidos

La sonda tiene éxito solo si responde preguntas estructurales sin observar valores de fila. Una fila científicamente útil, una lista de miembros o una selección no son resultados válidos.

Para root, north y south, `PROBE_PHYSICAL_CONTRACTS_RESOLVED` exige metadata suficiente para redactar contratos físicos de producción revisables y vinculados por evidencia. Para la patch list exige metadata suficiente para definir la interfaz de un parser futuro; sus valores de membresía seguirán sin leerse hasta un bootstrap de metadata separado y autorizado.

Son resultados negativos metodológicamente válidos:

- Range no disponible;
- cabecera mayor que el cap;
- gzip incompatible con extracción acotada sin emitir filas;
- payload intermedio no nulo;
- conflicto entre documentación, cabecera o manifiesto;
- información estructural insuficiente;
- ausencia de checksum de proveedor para la patch list.

Ninguno permite ampliar red, rangos, bytes, métodos, hosts o recursos para rescatar la sonda.

## 23. Efecto sobre Amendment 003 y bootstrap

La sonda caracteriza el contrato físico observado; no lo promueve automáticamente a producción. Incluso `PROBE_PHYSICAL_CONTRACTS_RESOLVED` requiere revisión humana de los artefactos y, cuando corresponda, una corrección documental prospectiva antes de cambiar o habilitar `ProviderSchemaAdapter`.

No se ejecutará `ProviderSchemaAdapter.decode`, no se resolverán bricks y no se creará `OC3_TECHNICAL_CANDIDATE_V1`. Los valores de tabla permanecen reservados para un futuro `METADATA_BOOTSTRAP_ONLY` autorizado independientemente.

## 24. Estado tras esta especificación

Crear este documento no autoriza implementación, tests, red ni ejecución. No autoriza `HEAD`, Range, descarga de manifiestos, lectura de DR9, selección real, bootstrap, manifiesto, derechos ni ledger productivos.

El estado permanece:

`PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`

OC-3 permanece científicamente sin iniciar.

**OC-3 REMAINS NOT STARTED.**
