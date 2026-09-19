# OC-3 — especificación congelada del primer metadata bootstrap real

**Fecha de congelación:** 2026-09-19  
**Naturaleza:** especificación documental prospectiva; no es implementación, manifiesto ni autorización.  
**Scope futuro:** `METADATA_BOOTSTRAP_ONLY`.  
**Attempt ID futuro:** `OC3-METADATA-BOOTSTRAP-001`.  
**Modelo de patch congelado:** `MODEL_B_TWO_STAGE`.  
**Estado actual:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Metadata bootstrap:** `NOT_STARTED`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades verificadas

Antes de crear este documento se recalcularon y verificaron:

| Autoridad o evidencia | SHA-256 |
|---|---|
| `OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md` | `c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348` |
| `OC3_METADATA_VALUE_SEMANTICS_IMPLEMENTATION_REPORT.md` | `bb84fd3992d9f2a52572bea1676234d188553078cade1229be9fedeada5d07e3` |
| `oc3/environment_setup/METADATA_VALUE_SEMANTICS_REPLAY_RECEIPT.json` | `1c692e67c179ece429fc492e72adeb680b5522ecf98458de60d37b247cf78467` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md` | `930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155` |

También coincidieron:

| Binding | Valor verificado |
|---|---|
| agregado de implementación | `f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581` |
| fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| regresión canónica | 413 total, 413 passed, 0 failed, 0 skipped |
| red real durante replay | 0 solicitudes |
| Probe 001 | 13/13 paths, tamaños y SHA-256 exactos |

Una divergencia produce `METADATA_BOOTSTRAP_SPEC_AUTHORITY_FAILURE` y prohíbe implementar o preparar autorización desde esta especificación.

## 2. Pregunta y límite científico

El primer bootstrap pregunta únicamente si los cuatro recursos exactos de metadata DR9 pueden adquirirse completamente, ligarse a integridad, cumplir sus contratos físicos y, dentro del alcance permitido por el modelo de patch, decodificarse bajo reglas semánticas congeladas sin que campos prohibidos o feedback de selección influyan en el resultado.

No pregunta qué bricks deben integrar la cohorte, qué región conviene, qué galaxias son interesantes ni qué morfología existe. No contiene selección, imágenes, coadds, PSF, Tractor, Galaxy Zoo, labels, visualización ni análisis científico.

## 3. Scope futuro y capacidad negativa

Una futura autorización debe declarar exactamente:

```text
scope = METADATA_BOOTSTRAP_ONLY
attempt_id = OC3-METADATA-BOOTSTRAP-001
patch_model = MODEL_B_TWO_STAGE
```

Puede autorizar, solo para los cuatro recursos literales de §4:

- HEAD y GET completo bajo el orden de §7;
- escritura raw inmutable dentro del attempt;
- SHA-256 completo y validación de integridad;
- validación del contrato físico congelado;
- decode de valores `TECHNICAL_ALLOWED` de root, north y south;
- semántica congelada y joins root↔regional exactos;
- resúmenes técnicos agregados y evidencia de ejecución;
- para patch, adquisición completa, hash local ligado y validación **solo de cabecera**.

No autoriza:

- lectura de filas o celdas de `SOUTH_PATCH_LIST`;
- `RELEASE`, `BRICKNAME`, `BRICKID`, membership, unicidad o joins de patch;
- `OC3_TECHNICAL_CANDIDATE_V1`, DTOs reales o selección de bricks;
- coadds, imágenes, mapas, PSF, Tractor, catálogos de fuentes o Galaxy Zoo;
- criterios morfológicos, inspección visual o estadísticas para cambiar gates;
- mirrors, descubrimiento de URLs, query strings, redirects o fallback;
- redistribución de FITS o productos a nivel de fila.

Una autorización genérica, otra scope o una autorización que omita cualquiera de estas capacidades negativas falla antes de abrir red.

## 4. Allowlist cerrada de cuatro recursos

| Orden | Rol | URL HTTPS literal | Representación |
|---:|---|---|---|
| 1 | `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | gzip opaco |
| 2 | `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | gzip opaco |
| 3 | `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | gzip opaco |
| 4 | `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | bytes FITS sin compresión HTTP |

La allowlist contiene exactamente estos cuatro pares rol/URL. No se permite resolver enlaces, listar directorios, consultar manifiestos, probar otro host, cambiar esquema, añadir parámetros ni seguir redirects.

## 5. Identidad de representación previa a transferencia

Probe 001 congeló estas longitudes esperadas:

| Rol | `Content-Length` exacto esperado |
|---|---:|
| `ROOT_SUMMARY` | 13.147.987 bytes |
| `NORTH_SUMMARY` | 20.882.100 bytes |
| `SOUTH_SUMMARY` | 55.399.879 bytes |
| `SOUTH_PATCH_LIST` | 31.680 bytes |
| **Agregado** | **89.461.646 bytes** |

El binding machine-readable futuro debe usar el entero exacto `expected_aggregate_bytes = 89461646`.

Son identidades de representación, no hechos científicos.

Para root, north y south se adopta prospectivamente la política conservadora: un `Content-Length` ausente, no decimal o diferente detiene antes del primer GET con `METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP`. El checksum publicado no arbitra una representación cuyo tamaño ya cambió. Cualquier cambio requiere revisión prospectiva nueva; no se decide después de descargar.

Para patch deben coincidir simultáneamente:

```text
Content-Length = 31680
ETag = "5ffdf047-7bc0"
Last-Modified = Tue, 12 Jan 2021 18:53:59 GMT
final_url = https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits
redirected = false
```

Cualquier diferencia produce `PATCH_LIST_REPRESENTATION_DRIFT_STOP` antes del GET.

Para los cuatro HEAD se exige status 200, URL solicitada y final idénticas, cero historial de redirect y `Content-Encoding` ausente o exactamente `identity`. Las respuestas GET deben conservar la misma identidad validada, devolver status 200, carecer de `Content-Range`, no aplicar decompression de transporte y entregar exactamente la longitud declarada. Un GET 206, 3xx, chunk truncado, cuerpo excedente, encoding distinto o identidad cambiante falla cerrado.

## 6. Métodos y headers

Para cada recurso solo se permiten:

```text
HEAD
GET de la representación completa
```

No se permiten Range, POST, OPTIONS ni discovery. Cada request envía `Accept-Encoding: identity`. Para los tres `.fits.gz`, el objeto de integridad es el stream gzip exacto recibido; la capa HTTP no puede descomprimirlo transparentemente.

## 7. Orden causal y secuencial

Concurrencia y número de transfers activos: uno. El orden es:

1. verificar autoridades, spec, implementación, entorno, rights binding, autorización y comando;
2. verificar que el attempt ID/directorio no entra en conflicto y abrir el único ledger;
3. `HEAD ROOT_SUMMARY`;
4. `HEAD NORTH_SUMMARY`;
5. `HEAD SOUTH_SUMMARY`;
6. `HEAD SOUTH_PATCH_LIST`;
7. validar conjuntamente las cuatro identidades pre-transferencia;
8. GET completo root → raw inmutable → SHA-256 local → comparación proveedor → contrato físico;
9. GET completo north → raw inmutable → SHA-256 local → comparación proveedor → contrato físico;
10. GET completo south → raw inmutable → SHA-256 local → comparación proveedor → contrato físico;
11. GET completo patch → raw inmutable → SHA-256 local ligado → contrato físico header-only;
12. solo si 1–11 pasaron, decodificar root/north/south bajo el firewall de §§14–17;
13. validar semántica completa y joins root↔north/root↔south;
14. emitir evidencias y terminar `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`.

No sale ningún GET si cualquiera de los cuatro HEAD o la validación conjunta falla. Un fallo de cuerpo, hash o contrato detiene los GET posteriores. Ninguna fila se decodifica hasta que los cuatro recursos estén adquiridos, ligados y físicamente validados dentro del alcance de MODEL B.

## 8. Límites duros

| Recurso | Máximo congelado |
|---|---:|
| requests HTTP totales | 12 |
| concurrencia por servicio y global | 1 |
| intento adicional | 1 por identidad exacta, sujeto además al cap global |
| cuerpos HTTP acumulados, incluidos fallos | 134.217.728 bytes (128 MiB) |
| cuerpo de un solo recurso/intento | 67.108.864 bytes (64 MiB) |
| disco del attempt | 268.435.456 bytes (256 MiB) |
| I/O local acumulado | 536.870.912 bytes (512 MiB) |
| RAM | 1.073.741.824 bytes (1 GiB) |
| cómputo activo | 300 s |
| wall time | 900 s |
| threads | 1 |
| GPU | 0 |

Los límites de requests, concurrencia, retries, disco, I/O, cómputo y wall conservan valores iguales o más estrictos que los máximos históricos cuando son compatibles con los cuatro archivos exactos. El agregado esperado de 89.461.646 bytes no cabe en los allowances históricos de metadata de 48/64 MiB. Por eso el futuro implementation preflight debe incorporar prospectivamente este cap específico de 128 MiB para `METADATA_BOOTSTRAP_ONLY`; mientras el código conserve el cap incompatible, la ejecución permanece bloqueada. No se permite elevarlo en CLI ni reinterpretarlo durante la corrida.

Cada byte recibido cuenta, incluidos cuerpos de error, parciales y abandonados. Cada HEAD, GET, fallo y retry cuenta. Un recurso puede tener como máximo dos intentos con el mismo método, URL, headers e identidad. El total de 12 prevalece aunque queden retries nominales. Un retry usa la misma representación y no habilita fallback. Timeout de conexión/lectura inactiva: 30 s; backoff: 2 s para el único intento adicional; `Retry-After > 60 s` detiene. Crédito no usado no se transfiere ni aumenta otro cap.

## 9. Attempt, raw inmutable y staging

El directorio futuro exacto es:

`oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/`

Los destinos raw finales son:

```text
RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz
RAW_IMMUTABLE/NORTH_SUMMARY/survey-bricks-dr9-north.fits.gz
RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz
RAW_IMMUTABLE/SOUTH_PATCH_LIST/dr9-south-patched-bricks.fits
```

Cada GET escribe primero un archivo exclusivo en `STAGING/`, con identidad de request e intento. Al completar longitud y transporte, se hace fsync y publicación atómica con creación exclusiva en el path raw. Nunca se sobrescribe raw ni se modifica un byte del proveedor. Un parser solo abre raw read-only.

Un staging parcial se conserva y se carga al ledger, pero no es raw válido ni puede hashearse como archivo completo. Como Range está prohibido, un retry usa un staging nuevo y vuelve a solicitar la representación completa. Conflictos, tamaños inciertos o un raw preexistente no ligado al mismo ledger/autorización detienen; no se “repara” ni se reemplaza.

No se persisten copias descomprimidas. La inspección FITS y el decode consumen la representación raw read-only mediante una ruta revisada que respete RAM, disco e I/O.

## 10. Procedencia obligatoria del digest local

Un string SHA-256 suministrado por caller, manifiesto o CLI no puede establecer integridad. La implementación futura debe calcularlo por streaming sobre el archivo raw final que ella misma publicó desde el transfer autorizado.

Cada `LOCALLY_COMPUTED_FULL_FILE_SHA256` debe ligar como un solo objeto canónico:

- rol y URL literal;
- SHA-256 de autorización y `attempt_id`;
- path raw relativo exacto;
- número exacto de bytes leídos del raw;
- SHA-256 calculado sobre todos esos bytes;
- agregado de implementación y fingerprint ambiental;
- identidad y hash del receipt de transporte;
- identidad de request/attempt y watermark del ledger;
- UTC de finalización del cálculo.

El cálculo reabre el raw read-only desde el path ligado. El digest de staging, cabecera, Range, decompressed payload, ETag, contrato físico o string externo no satisface esta clase.

## 11. Integridad de root, north y south

| Rol | `EXPECTED_PROVIDER_FULL_FILE_SHA256` |
|---|---|
| `ROOT_SUMMARY` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| `NORTH_SUMMARY` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| `SOUTH_SUMMARY` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

El orden por recurso es: transferencia completa → raw inmutable → SHA-256 local derivado → comparación exacta con digest proveedor → contrato físico. Una diferencia produce `METADATA_FULL_FILE_INTEGRITY_FAILURE`, impide todo decode de filas y detiene recursos posteriores.

La igualdad crea evidencia de validación para el attempt; no muta automáticamente constantes ni autoridades. El estado productivo solo puede ligarse a la identidad completa de ese raw y receipt.

## 12. Patch: MODEL B de dos etapas

Se preservan permanentemente:

```text
PROVIDER_PUBLISHED_SHA256 = ABSENT
PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND
```

Tras el GET completo de 31.680 bytes, la implementación calcula un `ACQUISITION_BOUND_LOCAL_SHA256` conforme a §10 y emite `PATCH_ACQUISITION_BOUND_EVIDENCE.json`. Nunca lo etiqueta como digest publicado por el proveedor.

El estado resultante del primer attempt es:

```text
PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW
provider_published_checksum_known = false
acquisition_bound_local_sha256_known = true para ese receipt/attempt
full_file_integrity_bound = false
patch_row_semantics = NOT_OBSERVED
patch_membership = NOT_OBSERVED
```

Este estado provisional permite exclusivamente validar la cabecera contra el contrato físico congelado. Inspeccionar `NAXIS2=1691` en la cabecera no establece que existan 1691 filas decodificables ni su validez semántica.

En `OC3-METADATA-BOOTSTRAP-001` queda prohibido acceder a `hdu.data`, iterar filas/celdas, leer `RELEASE`, `BRICKID` o `BRICKNAME`, validar cardinalidad semántica, unicidad, joins o membership patch. Una revisión humana posterior del receipt y bindings deberá preceder otra especificación/autorización limitada, por ejemplo `PATCH_METADATA_DECODE_ONLY`. No existe promoción automática a `FULL_FILE_INTEGRITY_BOUND=true`.

Por diseño, `METADATA_BOOTSTRAP_RESOLVED` es inalcanzable en este primer attempt aun cuando todos los pasos permitidos pasen.

## 13. Contratos físicos

Después de integridad completa, root/north/south deben cumplir exactamente los hashes de contrato congelados:

| Rol | Hash de contrato físico |
|---|---|
| `ROOT_SUMMARY` | `6e50b8b0c258f10752bf2d7d2d88c64ec16899fbb02711fd0621e4d642ea53` |
| `NORTH_SUMMARY` | `59fb8668165d14f201df1f269009ca0b47b41fa431b0bb0d55212c19c77f2677` |
| `SOUTH_SUMMARY` | `2faad729eac8e1912f63e4da8373acdc7cd5e9101601ea51e8ec9fb145dc25fa` |
| `SOUTH_PATCH_LIST` | `5be4df46180c0ec4964b53e3ad095bf75bf80a4c142dc7a8d22ba60efafbbd14` |

Se validan HDU, BINTABLE, NAXIS, NAXIS1/2, orden/nombre/TFORM de columnas y metadata restringida antes de celdas. Para patch solo se valida cabecera. Cualquier drift produce `METADATA_PHYSICAL_CONTRACT_FAILURE`; no se prueba otra HDU ni se actualiza el contrato en runtime.

## 14. Firewall de observación de campos

El schema completo se valida por metadata antes de la primera fila. Una columna desconocida produce `METADATA_PHYSICAL_CONTRACT_FAILURE`. De las columnas conocidas, solo estas celdas pueden cruzar el boundary:

**Root — 11 `TECHNICAL_ALLOWED`:**

`BRICKNAME`, `BRICKID`, `BRICKQ`, `BRICKROW`, `BRICKCOL`, `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, `DEC2`.

**North y south — 16 `TECHNICAL_ALLOWED`:**

`brickname`, `ra`, `dec`, `nexp_g`, `nexp_r`, `nexp_z`, `nexphist_g`, `nexphist_r`, `nexphist_z`, `brickid`, `ra1`, `ra2`, `dec1`, `dec2`, `area`, `survey_primary`.

De los 35 campos regionales `KNOWN_BUT_FORBIDDEN` solo puede inspeccionarse metadata física de esquema. Sus valores nunca se materializan, cuentan, registran, serializan ni pasan a errores, joins, elegibilidad, orden o debug. El adapter debe usar lectura column-selective. Si la biblioteca no puede garantizarlo, produce `METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE` antes de observar una celda.

Patch tiene cero campos autorizados para lectura de celdas en MODEL B.

## 15. Semántica de valores autorizada

Root, north y south usan exactamente:

- `OC3_BRICKNAME_SEMANTICS_V1`, sobre ocho bytes antes de decode ASCII estricto;
- signed int32 para `brickid` y tipos exactos del contrato;
- reglas finitas ya congeladas para geometría;
- `GRZ_MEDIAN_PRESENT_V1` sin optimización ni umbral nuevo;
- boolean FITS exacto para `survey_primary`;
- transformaciones/clasificaciones de Amendment 003/004.

No se hace trimming, case folding, replacement decode, coerción, limpieza de filas ni adaptación a distribuciones observadas. Una violación whole-file fail-closed produce `METADATA_VALUE_SEMANTICS_FAILURE`.

## 16. Validación completa y joins permitidos

Para cada tabla se registran únicamente agregados:

- filas físicas declaradas;
- filas recorridas;
- filas técnicas válidas;
- filas inválidas por código congelado;
- duplicados de identidad por conteo;
- conteos de joins exactos, ausentes, múltiples o con `brickid` discrepante.

Los reason codes permitidos son cerrados: `BRICKNAME_INVALID`, `BRICKID_INVALID`, `FINITE_VALUE_INVALID`, `GRZ_INPUT_INVALID`, `SURVEY_PRIMARY_INVALID`, `DUPLICATE_BRICKNAME`, `DUPLICATE_BRICKID`, `ROOT_MATCH_ZERO`, `ROOT_MATCH_MULTIPLE` y `ROOT_BRICKID_MISMATCH`. No incluyen valores ni nombres desconocidos.

Root debe tener identidad técnica única. Cada fila north y cada fila south debe unir exactamente una fila root por `BRICKNAME` validado y tener el mismo `BRICKID`. No se exige que cada fila de la grilla root tenga cobertura regional. No hay fuzzy match, alias, proximidad, fallback por ID ni overwrite geométrico. Cualquier conteo inválido distinto de cero falla el conjunto completo.

No se ejecutan joins regional↔patch ni se valida generación 9012. Tampoco se crean DTOs o candidatos north: este attempt termina antes de toda elegibilidad y selección.

## 17. Política de outputs row-bearing

La decisión prospectiva para el primer attempt es **cero persistencia a nivel de fila**. Los valores técnicos autorizados pueden existir transitoriamente dentro del boundary para validar semántica y joins, pero se descartan antes de escribir artifacts. No se crea Parquet, CSV, SQLite row table, DTO, membership set ni índice por brick.

`BOOTSTRAP_SEMANTIC_SUMMARY.json` contiene únicamente:

- versión de schema, attempt, modelo patch y bindings;
- por rol: total, válidas, inválidas por reason code y versiones semánticas;
- para root↔north y root↔south: conteos agregados de matches exactos y fallos;
- `row_values_persisted=false`;
- `forbidden_values_observed=false`;
- `patch_row_semantics=NOT_OBSERVED` y `patch_membership=NOT_OBSERVED`.

Esta decisión evita crear una proyección que pudiera convertirse prematuramente en input del selector. Una fase posterior deberá especificar y autorizar prospectivamente cualquier persistencia técnica mínima.

## 18. Artefactos exactos del attempt

Además de los cuatro raw de §9, el attempt puede contener exactamente:

```text
BOOTSTRAP_AUTHORIZATION_BINDING.json
BOOTSTRAP_TRANSPORT_EVIDENCE.json
BOOTSTRAP_RAW_FILE_MANIFEST.json
BOOTSTRAP_INTEGRITY_EVIDENCE.json
BOOTSTRAP_PHYSICAL_CONTRACT_EVIDENCE.json
BOOTSTRAP_SEMANTIC_SUMMARY.json
PATCH_ACQUISITION_BOUND_EVIDENCE.json
BOOTSTRAP_EVENTS.json
BOOTSTRAP_TERMINAL.json
BOOTSTRAP_LEDGER.sqlite
BOOTSTRAP_RUN.log
```

Los JSON usan UTF-8, keys ordenadas, separadores compactos, `ensure_ascii=false`, números finitos y un LF final. Rechazan claves desconocidas. Cada artifact final liga attempt, autorización, spec, implementación, entorno, ledger identity y hashes de sus inputs. El log y events contienen códigos, contadores, URLs allowlisted, tamaños, digests y timestamps; nunca celdas o filas.

El ledger es la única base mutable durante ejecución. Reserva caps antes del request, carga bytes aun ante fallo y conserva retries, request identities, bindings y watermark. Al terminar se fsync, se cierra y se liga desde terminal. No se crea un segundo ledger para resume.

No se permite ningún artifact científico, selection CSV, development-brick list, input manifest final, rights record o autorización dentro del attempt.

## 19. Reanudación y retry

Resume solo puede usar el mismo attempt ID, directorio, ledger, spec, autorización, implementación y entorno. Un raw completo cuya longitud, hash local, receipt y ledger binding se revaliden offline se reutiliza sin HEAD/GET.

Antes de adquirir recursos todavía incompletos, resume repite HEAD para cada recurso pendiente bajo la misma identidad y consume su único retry; vuelve a aplicar la validación conjunta para todos los pendientes. Un segundo resume que requiera otro HEAD o supere 12 requests detiene.

Un body parcial no se reanuda con Range. El único retry permitido solicita el cuerpo completo a staging nuevo; preserva y carga los bytes parciales anteriores. Raw final nunca se sobrescribe. Un crash con bytes inciertos conserva la carga conservadora de la reserva.

No hay auto-resume, background, polling ni reintentos prolongados. La persona ejecutora decide si invoca una vez el comando explícito de resume después de revisar el fallo.

## 20. Outcomes terminales y precedencia

Se emite exactamente un outcome terminal según esta precedencia, de mayor a menor:

1. `METADATA_ROW_OBSERVATION_INTEGRITY_FAILURE` — cualquier acceso patch o acceso no autorizado a celdas;
2. `METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE` — materialización o fuga de un valor prohibido;
3. `METADATA_BOOTSTRAP_AUTHORITY_FAILURE` — spec/autoridad/implementación/entorno incompatibles;
4. `METADATA_BOOTSTRAP_AUTHORIZATION_FAILURE` — scope, comando o binding humano inválido;
5. `METADATA_LOCAL_STATE_CONFLICT` — attempt/raw/ledger/output conflictivo;
6. `METADATA_RESOURCE_LIMIT_STOP` — cualquier cap o reserva falla;
7. `PATCH_LIST_REPRESENTATION_DRIFT_STOP` — identidad patch previa o durante transfer difiere;
8. `METADATA_PRETRANSFER_REPRESENTATION_DRIFT_STOP` — tamaño/identidad root, north o south difiere;
9. `METADATA_TRANSPORT_INTEGRITY_FAILURE` — método, status, headers, cuerpo o continuidad de transporte inválidos;
10. `METADATA_FULL_FILE_INTEGRITY_FAILURE` — root/north/south no coincide con digest proveedor;
11. `METADATA_PHYSICAL_CONTRACT_FAILURE` — contrato físico exacto no coincide;
12. `METADATA_VALUE_SEMANTICS_FAILURE` — valor permitido, unicidad o join exacto inválido;
13. `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` — todos los pasos autorizados pasaron y patch queda pendiente de revisión;
14. `METADATA_BOOTSTRAP_RESOLVED` — reservado para una fase futura; inalcanzable bajo MODEL B en attempt 001.

Un outcome de mayor precedencia no se reemplaza por uno posterior. Fallar cerrado conserva evidencia ya escrita, prohíbe selección y no cambia la especificación.

## 21. Derechos, atribución y redistribución

Las referencias documentales locales son:

- `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md`, SHA-256 `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b`, especialmente §9;
- `OC3_EXECUTION_PREFLIGHT_SPEC.md`, referencias oficiales a [NERSC DR9](https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/) y [Legacy Surveys acknowledgment](https://www.legacysurvey.org/acknowledgment/);
- snapshot local `e_oc1/evidence/RIGHTS-DR5.html`, SHA-256 `adb1c5b41ad8aee7544a23d1b499b317d97c82222b4f69f65efa3ad13f6a9a1c`, con las limitaciones registradas en el preflight.

Se congela como regla del protocolo:

```text
local_scientific_acquisition = ALLOWED_FOR_THIS_PROTOCOL
local_preservation = ALLOWED_FOR_THIS_PROTOCOL
redistribution = false
FITS_OR_DERIVED_REDISTRIBUTION = DISABLED_UNRESOLVED
```

Es una decisión estrecha de gobernanza de investigación basada en acceso público y uso científico documentados; no es una determinación jurídica amplia. CC BY 4.0 de capas renderizadas no se extiende a FITS o derivados de filas. Una publicación futura debe cumplir el acknowledgment aplicable.

La evidencia externa permanece separada de la autoridad de ejecución. Antes de red debe existir en una tarea posterior un rights binding revisable que ligue referencias/snapshots exactos, hashes, alcance local, `redistribution=false`, spec, implementación, entorno, manifiesto y autorización. Este documento no crea ese registro, por lo que el preflight actual sigue bloqueado. Los raw no salen del workspace de investigación.

## 22. Firewall contra exploración y selección

El attempt termina antes de selección determinista de development bricks. No se inspeccionan listas por brick, extremos, mapas, distribuciones o estadísticas para cambiar semántica, integridad, membership, allowlist, tamaños o aceptación.

Los únicos resultados observables son integridad, estructura, contadores semánticos agregados y conteos agregados de joins. Un resultado negativo es válido y no habilita cleaning, relajación, sustitución de release ni selección alternativa. Solo una revisión humana posterior de la evidencia puede autorizar la fase siguiente precongelada.

## 23. Implementación, replay, plan y autorización futuros

El trabajo debe ocurrir en tareas separadas y en este orden:

1. implementación offline, idempotente y reanudable;
2. replay sintético completo con firewall previo a imports y regresión heredada;
3. plan exacto de ejecución y estimación medida;
4. candidato de autorización con `authorized=false` y argv/hash exactos;
5. revisión humana;
6. autorización humana final `METADATA_BOOTSTRAP_ONLY` ligada al candidato;
7. ejecución manual del CLI por la persona responsable;
8. auditoría post-ejecución sin repetir transfers.

La implementación deberá proporcionar `--help`, `--dry-run`, `--offline`, `--execute-network`, `--authorization` y `--resume`, con límites no elevables. El comando real, log, sentinel, outputs y reglas de fallo se congelarán después del replay. Codex no ejecutará la adquisición real: por política humana obligatoria, el transfer/parse completo se delega aunque su volumen nominal sea menor que 250 MiB.

## 24. Estado que este documento no cambia

Esta especificación crea cero directorios de attempt, raw, manifest, ledger, rights record o autorización. No modifica código ni activa rutas productivas.

```text
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
metadata_bootstrap = NOT_STARTED
production_decode_enabled = false
redistribution = false
real_network_requests = 0
real_provider_row_values = 0
```

Probe 001 permanece inmutable 13/13. El agregado de implementación permanece `f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581`.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
