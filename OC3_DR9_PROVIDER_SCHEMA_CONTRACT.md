# OC-3 — contrato de esquema proveedor para el bootstrap DR9

**Fecha:** 2026-09-18  
**Naturaleza:** contrato prospectivo derivado de evidencia documental suministrada por revisión humana y auditoría local de la implementación Amendment 002.  
**Resultado de auditoría:** **IMPLEMENTATION_SCHEMA_ADAPTER_REQUIRED**

## 1. Propósito y límite probatorio

Este contrato separa dos operaciones que no son equivalentes:

1. **validación del esquema proveedor:** comprobar el layout completo conocido de un archivo antes de leer filas para selección;
2. **proyección científica/técnica:** exponer al selector solamente valores aprobados.

Una tabla puede contener campos `KNOWN_BUT_FORBIDDEN` y seguir siendo un producto proveedor válido. Sus valores nunca pueden entrar al selector, desempate, ranking, logs de selección ni decisiones de conveniencia. Un campo no reconocido debe detener el proceso antes de iterar sobre valores o seleccionar.

Los nombres y tipos documentados abajo no son observaciones FITS locales. Ninguna tabla DR9 fue adquirida. La cabecera real debe compararse en una ejecución futura autorizada.

## 2. Clases normativas

| Clase | Regla |
|---|---|
| `TECHNICAL_ALLOWED` | Nombre, tipo, shape y semántica deben coincidir con el contrato; sus valores pueden alimentar únicamente transformaciones técnicas congeladas. |
| `KNOWN_BUT_FORBIDDEN` | El esquema puede reconocer nombre/tipo/shape, pero el adaptador no lee, copia, serializa, registra ni expone sus valores. Su presencia no rechaza por sí sola el archivo. |
| `UNKNOWN_PROVIDER_FIELD` | Cualquier columna fuera del contrato exacto aplicable; falla cerrado antes de selección y sin imprimir nombre o valores en logs de selección. |

Una columna documentada con tipo o shape distinto del contrato se trata como discrepancia de esquema y falla cerrado. Un alias de nombre, cambio de case, coerción de tipo o flattening de arrays no se acepta por conveniencia.

## 3. `survey-bricks.fits.gz`: esquema geométrico documentado

La revisión humana suministró una lista completa de columnas para la tabla geométrica root. Todas se clasifican como `TECHNICAL_ALLOWED`.

| Orden documental | Columna proveedor | Tipo documentado | Clase | Uso permitido |
|---:|---|---|---|---|
| 1 | `BRICKNAME` | `char[8]` | `TECHNICAL_ALLOWED` | clave ASCII del brick |
| 2 | `BRICKID` | `int32` | `TECHNICAL_ALLOWED` | identidad técnica, no ranking |
| 3 | `BRICKQ` | `int16` | `TECHNICAL_ALLOWED` | geometría de retícula, no ranking |
| 4 | `BRICKROW` | `int32` | `TECHNICAL_ALLOWED` | geometría de retícula, no ranking |
| 5 | `BRICKCOL` | `int32` | `TECHNICAL_ALLOWED` | geometría de retícula, no ranking |
| 6 | `RA` | `float64` | `TECHNICAL_ALLOWED` | centro geométrico |
| 7 | `DEC` | `float64` | `TECHNICAL_ALLOWED` | centro geométrico |
| 8 | `RA1` | `float64` | `TECHNICAL_ALLOWED` | límite geométrico |
| 9 | `RA2` | `float64` | `TECHNICAL_ALLOWED` | límite geométrico |
| 10 | `DEC1` | `float64` | `TECHNICAL_ALLOWED` | límite geométrico |
| 11 | `DEC2` | `float64` | `TECHNICAL_ALLOWED` | límite geométrico |

La tabla cubre todos los bricks geométricos, no solamente los que tienen datos DR9. Por ello no puede establecer por sí sola elegibilidad ni cobertura.

### Condiciones todavía no documentadas para aceptación binaria

- índice exacto del HDU binario;
- correspondencia exacta de `char[8]`, signedness/endian y TFORM FITS;
- null sentinels/TNULL, escalas TZERO/TSCAL y unidades TUNIT;
- número esperado de filas y cualquier metadato estructural obligatorio.

Hasta resolverlos, el checksum puede probar identidad de bytes futuros, pero el adaptador no debe inventar una traducción de layout.

## 4. Resúmenes regionales north/south: proyección técnica documentada

Los siguientes campos constituyen la proyección técnica mínima suministrada. Sus nombres se congelan en minúscula lógica; la futura validación deberá fijar además el case exacto observado/documentado en FITS sin aplicar case folding silencioso.

| Campo lógico documentado | Tipo documentado | Clase | Uso permitido |
|---|---|---|---|
| `brickname` | `char[8]` | `TECHNICAL_ALLOWED` | join técnico por identidad |
| `ra` | `float64` | `TECHNICAL_ALLOWED` | centro documentado; validación geométrica |
| `dec` | `float64` | `TECHNICAL_ALLOWED` | centro documentado; validación geométrica |
| `nexp_g` | `int16` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura g |
| `nexp_r` | `int16` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura r |
| `nexp_z` | `int16` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura z |
| `nexphist_g` | `int32[6]` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura g |
| `nexphist_r` | `int32[6]` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura r |
| `nexphist_z` | `int32[6]` | `TECHNICAL_ALLOWED` | solamente predicado congelado de cobertura z |
| `brickid` | `int16` según documentación proveedor | `TECHNICAL_ALLOWED` | identidad técnica; validar sin coerción |
| `ra1` | `float32` | `TECHNICAL_ALLOWED` | límite geométrico |
| `ra2` | `float32` | `TECHNICAL_ALLOWED` | límite geométrico |
| `dec1` | `float32` | `TECHNICAL_ALLOWED` | límite geométrico |
| `dec2` | `float32` | `TECHNICAL_ALLOWED` | límite geométrico |
| `area` | `float32` | `TECHNICAL_ALLOWED` | validación técnica; no ranking |
| `survey_primary` | `boolean` | `TECHNICAL_ALLOWED` | pertenencia técnica documentada; no quality shopping |

La diferencia documentada `BRICKID int32` en root frente a `brickid int16` regional se conserva como una diferencia entre productos. No se hace cast implícito ni se declara conflicto sin observar los archivos. Un join debe comprobar consistencia de valores representables y conservar procedencia de ambos tipos.

### Semántica de cobertura permitida

`nexp_g/r/z` son medianas de exposiciones contribuyentes en el área única `BRICK_PRIMARY`. `nexphist_g/r/z` son histogramas de píxeles por número de exposiciones en esa área; píxeles rechazados upstream por condiciones como rayos cósmicos o saturación no contribuyen.

Solo pueden derivar un booleano `grz` mediante una regla prospectiva congelada. No pueden usarse como proxy de seeing, profundidad, apariencia o calidad general. El umbral/regla exacto no aparece en la evidencia suministrada y permanece `UNRESOLVED`; no se define en esta revisión posterior a la evidencia.

## 5. Inventario conocido de campos regionales prohibidos

La revisión humana los presentó como “known examples”. Se expanden aquí los shorthands exactamente, pero no se afirma que constituyan el esquema regional completo.

| Grupo | Columnas lógicas clasificadas `KNOWN_BUT_FORBIDDEN` |
|---|---|
| conteos/modelos de fuentes | `nobjs`, `npsf`, `nsimp`, `nrex`, `nexp`, `ndev`, `ncomp`, `nser`, `ndup` |
| PSF | `psfsize_g`, `psfsize_r`, `psfsize_z` |
| profundidad PSF | `psfdepth_g`, `psfdepth_r`, `psfdepth_z` |
| profundidad de galaxias | `galdepth_g`, `galdepth_r`, `galdepth_z` |
| extinción/reddening | `ebv`, `ext_g`, `ext_r`, `ext_z`, `ext_w1`, `ext_w2`, `ext_w3`, `ext_w4` |
| transmisiones | `trans_g`, `trans_r`, `trans_z`, `trans_wise` |
| cielo | `cosky_g`, `cosky_r`, `cosky_z` |
| WISE | `wise_nobs` |
| footprint externo | `in_desi` |

Para estos campos no se suministraron tipos, shapes, unidades ni null conventions. Por tanto:

- sus nombres conocidos quedan clasificados y bloqueados para proyección;
- sus valores no se pueden leer para selección;
- su presencia no autoriza aceptar todavía el esquema completo;
- la validación exacta de tipos/shapes permanece `UNRESOLVED`;
- cualquier otra columna es `UNKNOWN_PROVIDER_FIELD` hasta una revisión prospectiva.

La exigencia de congelar el esquema oficial exacto no puede satisfacerse fingiendo que “at minimum” y “known examples” son listas exhaustivas. Antes de producción se necesita una fuente oficial exhaustiva o la cabecera FITS observada, revisada contra una enmienda prospectiva. La primera observación de una columna adicional no permite incorporarla automáticamente.

## 6. Lista de patches 9012: contrato deliberadamente no definido

Para `dr9-south-patched-bricks.fits` solo están documentados filename, host/path, propósito, sufijo FITS y cardinalidad conceptual de 1.691 bricks afectados.

Estado obligatorio:

```text
IDENTITY_DOCUMENTED
PURPOSE_DOCUMENTED
FORMAT_SUFFIX_DOCUMENTED
INTERNAL_SCHEMA_UNRESOLVED
PROVIDER_CHECKSUM_UNRESOLVED
```

No existe contrato de columnas para este archivo. No se supone `BRICKNAME`. No se puede construir `corrected_9012` hasta resolver esquema, checksum y regla exacta de pertenencia. Su parser debe permanecer deshabilitado.

## 7. Transformación técnica necesaria antes del selector

Una futura implementación debe separar un DTO proveedor de un DTO candidato. La transformación cerrada mínima sería:

| Campo candidato | Fuente permitida | Estado |
|---|---|---|
| `brickname` | columna técnica homónima y join con root | documentada; case/layout FITS pendiente |
| `brickid` | root/regional, verificando consistencia sin coerción | el pipeline actual no lo admite en `CANDIDATE_FIELDS` |
| `region` | identidad inmutable del recurso north/south | constante de procedencia, no columna científica |
| `survey` | identidad documental de rama: DECaLS south o BASS/MzLS north | constante de procedencia |
| `release` | familia sellada `DR9` | constante de procedencia |
| `generation` | south 9012 solo por pertenencia al patch list; north 9011 por documentación/procedencia | patch parser pendiente; north 9011 no se impone actualmente |
| `grz` | predicado técnico prospectivo sobre `nexp_*`/`nexphist_*` | fórmula pendiente |
| `corrected_9012` | pertenencia exacta a la lista oficial 9012; siempre false/no aplicable en north | esquema/checksum de lista pendiente |
| `primary_bounds` | estructura canónica derivada de `ra1`, `ra2`, `dec1`, `dec2` tras validación | constructor pendiente |
| `evidence_refs` | hashes/IDs inmutables de los recursos y checksums usados | síntesis de procedencia pendiente |

La selección determinista posterior puede usar solamente `region`, `brickname`, `survey`, `release`, `generation`, `grz`, `corrected_9012` y geometría/evidencia técnica aprobada. `brickid` puede conservarse para identidad/auditoría, pero no altera el hash ordering. Ningún campo prohibido participa en joins de elegibilidad, desempate o registros de selección.

## 8. Algoritmo normativo de validación futura

Antes de leer valores de filas o invocar selección:

1. verificar identidad del recurso, límite, hash local completo y checksum proveedor aplicable;
2. abrir solamente el HDU exacto previamente congelado;
3. extraer metadata de esquema: nombres, orden si es normativo, TFORM/dtype, shapes, null/scaling y unidades requeridas;
4. comparar contra un contrato versionado exhaustivo;
5. clasificar cada columna como `TECHNICAL_ALLOWED` o `KNOWN_BUT_FORBIDDEN`;
6. ante una columna desconocida o discrepancia de tipo/shape, fallar cerrado antes de iterar filas;
7. construir una vista nueva que contenga únicamente columnas `TECHNICAL_ALLOWED`;
8. ejecutar transformaciones técnicas predeterminadas, sin ganancia, thresholds, aliases ni parámetros adaptados a los datos;
9. comprobar joins uno-a-uno o cardinalidades congeladas y conflictos de identidad;
10. construir el DTO candidato y solo entonces llamar al selector determinista.

La inspección del esquema puede reconocer nombres prohibidos. No debe leer ni serializar sus arrays. Los errores de producción deben usar códigos generales, sin nombres ni valores prohibidos en logs destinados a selección. Una evidencia de auditoría separada puede registrar el hash del contrato y el resultado PASS/FAIL del esquema, nunca valores prohibidos.

## 9. Auditoría de la implementación Amendment 002

### Capacidades presentes

1. `validate_literal_resource` exige un diccionario `projection` para JSON/FITS y rechaza targets fuera de `CANDIDATE_FIELDS`.
2. `merge_candidate_rows` exige que el DTO fusionado tenga exactamente los campos candidatos y rechaza conflictos.
3. `resolve_bootstrap_bricks` aplica orden SHA-256 determinista e independiente del orden de filas.
4. South exige DECaLS, DR9, `generation=9012`, `corrected_9012=true` y `grz=true`; north exige BASS/MzLS, DR9 y `grz=true`.
5. Los errores actuales de proyección no incluyen valores de celdas en el mensaje.

### Defectos del boundary proveedor

| Requisito auditado | Resultado | Evidencia en comportamiento actual |
|---|---|---|
| validación completa del esquema proveedor | **NO** | `Table.read(path).as_array()` no compara nombres/tipos/shapes/HDU contra un contrato exhaustivo |
| proyección explícita solo desde `TECHNICAL_ALLOWED` | **NO** | se valida el target, pero cualquier string puede ser columna source |
| reconocer `KNOWN_BUT_FORBIDDEN` sin exponer valores | **NO** | no existe clasificación proveedor; una columna prohibida puede mapearse a un target permitido |
| fail-closed ante `UNKNOWN_PROVIDER_FIELD` | **NO** | columnas no proyectadas se ignoran silenciosamente |
| impedir logging/artefactos de valores prohibidos | **NO GARANTIZADO** | no hay logging directo del decoder, pero una proyección maliciosa/errónea puede introducir el valor prohibido en candidato/selección |
| selección determinista solo con campos aprobados | **PARCIAL** | el algoritmo es determinista una vez recibido el DTO, pero no autentica el origen permitido de sus valores |
| construir campos derivados/procedencia | **NO** | la proyección solo copia `row[source]`; no crea constantes, bounds, predicado grz, membership 9012 ni evidence refs |
| conservar la proyección técnica mínima regional | **NO** | `brickid`, `nexp_*`, `nexphist_*`, `ra/dec`, `area` y `survey_primary` no son targets válidos de `CANDIDATE_FIELDS` |
| imponer north generation 9011 | **NO** | el selector north no verifica `generation == 9011` |

La suite sintética actual usa filas ya preconstruidas con una proyección identidad hacia `CANDIDATE_FIELDS`. Prueba el selector y el pipeline de bootstrap sintético, pero no prueba este boundary de un FITS proveedor real.

## 10. Resultado obligatorio de auditoría

**IMPLEMENTATION_SCHEMA_ADAPTER_REQUIRED**

La implementación actual no puede satisfacer la separación `provider schema validation != scientific projection` sin una modificación prospectiva revisada.

## 11. Cambio prospectivo mínimo

No se implementa en esta tarea. El cambio mínimo revisable debe:

1. añadir contratos versionados por rol proveedor con HDU, inventario exhaustivo, dtype/TFORM, shape, null/scaling y clase de cada columna;
2. insertar un `ProviderSchemaAdapter` antes de `decode_candidate_rows`/`merge_candidate_rows`;
3. validar el esquema entero antes de leer filas y rechazar cualquier `UNKNOWN_PROVIDER_FIELD` o discrepancia;
4. impedir que `projection` nombre como source una columna no `TECHNICAL_ALLOWED`;
5. crear una tabla/vista nueva solo con campos permitidos, sin leer valores prohibidos;
6. soportar constantes de procedencia y transformaciones técnicas cerradas para región, survey, release, 9011/9012, `primary_bounds`, `grz`, `corrected_9012` y `evidence_refs`;
7. conservar `brickid` y la proyección técnica requerida en un artefacto auditado, actualizando el DTO/final manifest solo donde la especificación lo requiera;
8. bloquear el adaptador de patch list hasta congelar su esquema/checksum;
9. aplicar `generation=9011` a north y 9012 exclusivamente al subconjunto south documentado;
10. emitir códigos de error generales y resultados de esquema hasheados, sin valores prohibidos.

No es suficiente añadir los nombres prohibidos a un filtro posterior: para cuando existe un DTO contaminado, el boundary ya falló.

## 12. Pruebas sintéticas prospectivas mínimas

Una enmienda de implementación deberá añadir, sin red real:

1. tabla con esquema documentado completo y columnas prohibidas: se acepta el esquema y ningún valor prohibido es accesible al selector;
2. source prohibido mapeado a target permitido: rechazo antes de selección;
3. columna proveedor desconocida: rechazo antes de iterar filas;
4. campo conocido con dtype/shape/HDU incorrecto: rechazo;
5. ausencia de campo técnico requerido: rechazo;
6. logs y recibos sin nombres/valores prohibidos según política congelada;
7. derivación determinista del predicado g/r/z con casos cero, nulo y bins, después de congelar la regla;
8. join geométrico/regional conflictivo o duplicado: rechazo;
9. south fuera de patch list no adquiere 9012; north jamás adquiere 9012 y exige 9011;
10. permutación de filas conserva candidatos, selección y hashes;
11. esquema real del patch list sintético solo después de su congelación;
12. regresión completa de las 142 pruebas actuales sin adaptar golden values para acomodar discrepancias.

## 13. Estado terminal

El contrato documental no autoriza una ejecución. Permanecen pendientes el esquema regional exhaustivo, el HDU/layout real, el predicado g/r/z, el patch list, el adaptador, el rights binding, el manifiesto y la autorización humana.

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

- Solicitudes reales de red: **0**.
- Bytes DR9 adquiridos: **0**.
- Código modificado: **0 archivos**.

**OC-3 REMAINS NOT STARTED.**
