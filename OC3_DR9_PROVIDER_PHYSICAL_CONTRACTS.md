# OC-3 — contratos físicos congelados del proveedor DR9

**Fecha de congelación documental:** 2026-09-19  
**Naturaleza:** especificación prospectiva de contratos físicos FITS, sin cambio de código.  
**Fuente empírica:** evidencia estructural ya auditada de Probe 001, limitada a cabeceras.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades y verificación de integridad

Esta especificación se creó solo después de verificar localmente los siguientes bindings:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_EXECUTION_AUDIT.md` | `3cc152d5a05d3dcb5d348d22d0ec271c416c3a824518a35b067edf34d368654c` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md` | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json` | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |
| `PROBE_PHYSICAL_CONTRACT_CANDIDATES.json` | `eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1` |
| `PROBE_TERMINAL.json` | `27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3` |

También se verificaron los siguientes valores ligados:

| Binding | Valor verificado |
|---|---|
| Resultado terminal de Probe 001 | `PROBE_PHYSICAL_CONTRACTS_RESOLVED` |
| Veredicto de auditoría | `PROSPECTIVE_CORRECTION_REQUIRED_BEFORE_FREEZE` |
| Agregado de implementación actual | `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea` |
| Fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |

Una divergencia en cualquiera de estos bindings habría producido `PHYSICAL_CONTRACT_FREEZE_INTEGRITY_FAILURE` y habría impedido crear este documento. No se observó ninguna divergencia.

## 2. Propósito, causalidad y límite probatorio

Este documento congela las estructuras físicas FITS exactas que una futura ruta productiva de `ProviderSchemaAdapter` deberá validar antes de considerar cualquier decodificación. La secuencia causal preservada es:

```text
EXPECTATIVA PRE-PROBE CONGELADA
→ OBSERVACIÓN REAL ACOTADA SOLO A CABECERAS
→ AUDITORÍA DE EJECUCIÓN READ-ONLY
→ CORRECCIONES PROSPECTIVAS DE AMENDMENT 004
→ CONTRATOS FÍSICOS CONGELADOS EN ESTE DOCUMENTO
```

Las expectativas anteriores a Probe 001 permanecen registradas en Amendment 003. La observación acotada estableció representación física, no semántica de celdas. La auditoría clasificó las discrepancias. Amendment 004 corrigió prospectivamente 15 expectativas regionales y promovió solo una clave estructural candidata para la patch list. Este documento incorpora esas correcciones sin reescribir la historia.

La congelación:

- no autoriza decodificar filas o celdas;
- no demuestra semántica de filas;
- no habilita el bootstrap de metadata;
- no crea un manifiesto de bootstrap ni un registro de derechos;
- no habilita selección de bricks;
- no habilita el parser de membership de la patch list;
- no inicia OC-3.

## 3. Estados independientes del contrato

Los siguientes estados son independientes y no se pueden colapsar:

| Estado | Significado normativo |
|---|---|
| `PHYSICAL_SCHEMA_FROZEN` | La representación de cabecera definida aquí es normativa para la identidad exacta del recurso. |
| `FULL_FILE_INTEGRITY_BOUND` | Los bytes completos adquiridos localmente fueron verificados contra una identidad íntegra autorizada. |
| `ROW_SEMANTICS_VALIDATED` | Una tarea autorizada, prospectiva y separada validó el significado y las reglas de los valores de fila. |
| `PRODUCTION_DECODE_ENABLED` | Una autorización posterior permite que valores admitidos crucen la frontera productiva del adaptador. |

Para `ROOT_SUMMARY`, `NORTH_SUMMARY` y `SOUTH_SUMMARY`, `PHYSICAL_SCHEMA_FROZEN=true`. Sus checksums publicados se congelan como identidades completas **esperadas**, pero `FULL_FILE_INTEGRITY_BOUND=false` mientras los archivos completos no se adquieran y verifiquen localmente en una operación futura autorizada. Para esos tres roles, `ROW_SEMANTICS_VALIDATED=false` y `PRODUCTION_DECODE_ENABLED=false`.

Para `SOUTH_PATCH_LIST`, `PHYSICAL_SCHEMA_FROZEN=true`, `FULL_FILE_INTEGRITY_BOUND=false`, `ROW_SEMANTICS_VALIDATED=false` y `PRODUCTION_DECODE_ENABLED=false`. Se conserva exactamente `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`.

## 4. Reglas estructurales comunes y política fail-closed

Los cuatro contratos exigen:

| Propiedad | Valor normativo |
|---|---|
| `target_hdu_index` | `1` |
| `XTENSION` | `BINTABLE` |
| `BITPIX` | `8` |
| `NAXIS` | `2` |
| `PCOUNT` | `0` |
| `GCOUNT` | `1` |
| `EXTNAME` | `ABSENT` |
| `CHECKSUM` | `ABSENT` |
| `DATASUM` | `ABSENT` |

Para cada columna enumerada, `TUNIT`, `TNULL`, `TSCAL` y `TZERO` deben estar ausentes. El orden de columnas, el case exacto de cada `TTYPE` y cada `TFORM` son normativos.

La política congelada es estricta:

- columna extra, faltante o reordenada: fallo cerrado;
- cambio de case de `TTYPE`: fallo cerrado;
- `TFORM` diferente: fallo cerrado;
- `TUNIT`, `TNULL`, `TSCAL` o `TZERO` inesperado: fallo cerrado;
- `EXTNAME`, `CHECKSUM` o `DATASUM` inesperado: fallo cerrado;
- valor estructural común diferente: fallo cerrado.

La presencia futura de una tarjeta actualmente ausente se clasifica como divergencia del esquema físico, aunque pudiera ser aditiva según FITS. El consumidor no debe ignorarla, reinterpretarla ni actualizar automáticamente este contrato. El fallo debe ocurrir antes de acceder a datos de tabla.

La ausencia de estas tarjetas no permite inferir comportamiento de nulls, escalado, unidades ni valores de fila. Este contrato tampoco infiere endianess lógico fuera de lo que define el `TFORM`, conversión de strings ni reglas de aplicación.

## 5. Contrato `ROOT_SUMMARY`

### 5.1 Identidad y estructura

| Propiedad | Valor congelado |
|---|---|
| Rol | `ROOT_SUMMARY` |
| Recurso | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` |
| Compresión de transporte | `gzip` |
| HDU | `1` |
| `XTENSION` | `BINTABLE` |
| `BITPIX` | `8` |
| `NAXIS` | `2` |
| `NAXIS1` | `70` |
| `NAXIS2` | `662174` |
| `PCOUNT` | `0` |
| `GCOUNT` | `1` |
| `TFIELDS` | `11` |

### 5.2 Columnas ordenadas

| # | `TTYPE` | `TFORM` |
|---:|---|---|
| 1 | `BRICKNAME` | `8A` |
| 2 | `BRICKID` | `J` |
| 3 | `BRICKQ` | `I` |
| 4 | `BRICKROW` | `J` |
| 5 | `BRICKCOL` | `J` |
| 6 | `RA` | `D` |
| 7 | `DEC` | `D` |
| 8 | `RA1` | `D` |
| 9 | `RA2` | `D` |
| 10 | `DEC1` | `D` |
| 11 | `DEC2` | `D` |

### 5.3 Evidencia e integridad

| Identidad | SHA-256 o estado |
|---|---|
| Cabecera observada | `1b339ae87a09ec943d1b3a5bf7ddd89b0d018176a3dbfde5b67aabb65e90f1c1` |
| Candidato físico observado | `84ba119a591bcb89732eb533913782fdaff353a33052375f1366f7807d2d6c9e` |
| `EXPECTED_PROVIDER_FULL_FILE_SHA256` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| `LOCALLY_VERIFIED_FULL_FILE_SHA256` | `ABSENT_UNRESOLVED` |

El checksum esperado procede de un manifiesto autorizado. No representa una verificación local del archivo completo.

## 6. Contrato regional común de 51 columnas

`NORTH_SUMMARY` y `SOUTH_SUMMARY` comparten exactamente el siguiente inventario físico ordenado. La identidad de esquema no implica igualdad de filas, valores, cobertura ni población.

| # | `TTYPE` | `TFORM` | # | `TTYPE` | `TFORM` | # | `TTYPE` | `TFORM` |
|---:|---|---|---:|---|---|---:|---|---|
| 1 | `brickname` | `8A` | 18 | `ndup` | `J` | 35 | `ext_g` | `E` |
| 2 | `ra` | `D` | 19 | `psfsize_g` | `E` | 36 | `ext_r` | `E` |
| 3 | `dec` | `D` | 20 | `psfsize_r` | `E` | 37 | `ext_z` | `E` |
| 4 | `nexp_g` | `I` | 21 | `psfsize_z` | `E` | 38 | `wise_nobs` | `4I` |
| 5 | `nexp_r` | `I` | 22 | `psfdepth_g` | `E` | 39 | `trans_wise` | `4E` |
| 6 | `nexp_z` | `I` | 23 | `psfdepth_r` | `E` | 40 | `ext_w1` | `E` |
| 7 | `nexphist_g` | `6J` | 24 | `psfdepth_z` | `E` | 41 | `ext_w2` | `E` |
| 8 | `nexphist_r` | `6J` | 25 | `galdepth_g` | `E` | 42 | `ext_w3` | `E` |
| 9 | `nexphist_z` | `6J` | 26 | `galdepth_r` | `E` | 43 | `ext_w4` | `E` |
| 10 | `nobjs` | `J` | 27 | `galdepth_z` | `E` | 44 | `brickid` | `J` |
| 11 | `npsf` | `J` | 28 | `ebv` | `E` | 45 | `ra1` | `D` |
| 12 | `nsimp` | `J` | 29 | `trans_g` | `E` | 46 | `ra2` | `D` |
| 13 | `nrex` | `J` | 30 | `trans_r` | `E` | 47 | `dec1` | `D` |
| 14 | `nexp` | `J` | 31 | `trans_z` | `E` | 48 | `dec2` | `D` |
| 15 | `ndev` | `J` | 32 | `cosky_g` | `E` | 49 | `area` | `D` |
| 16 | `ncomp` | `J` | 33 | `cosky_r` | `E` | 50 | `survey_primary` | `L` |
| 17 | `nser` | `J` | 34 | `cosky_z` | `E` | 51 | `in_desi` | `L` |

Este inventario incorpora las 15 correcciones prospectivas de Amendment 004. Las clasificaciones de campos de Amendment 003 se conservan independientemente de los tipos físicos.

## 7. Contrato `NORTH_SUMMARY`

| Propiedad | Valor congelado |
|---|---|
| Rol | `NORTH_SUMMARY` |
| Recurso | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` |
| Compresión de transporte | `gzip` |
| HDU | `1` |
| `XTENSION` | `BINTABLE` |
| `BITPIX` | `8` |
| `NAXIS` | `2` |
| `NAXIS1` | `300` |
| `NAXIS2` | `93548` |
| `PCOUNT` | `0` |
| `GCOUNT` | `1` |
| `TFIELDS` | `51` |
| Esquema | Las 51 columnas exactas de la sección 6 |

| Identidad | SHA-256 o estado |
|---|---|
| Cabecera observada | `4ed9da1bdc60563447731a4ba43611e079cd27def2734774809841b08b959749` |
| Candidato físico observado | `8dc23b47dc995a9aceef5a42794abd3f6b25345f674e36ba856dbddec1f7c597` |
| `EXPECTED_PROVIDER_FULL_FILE_SHA256` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| `LOCALLY_VERIFIED_FULL_FILE_SHA256` | `ABSENT_UNRESOLVED` |

## 8. Contrato `SOUTH_SUMMARY`

| Propiedad | Valor congelado |
|---|---|
| Rol | `SOUTH_SUMMARY` |
| Recurso | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` |
| Compresión de transporte | `gzip` |
| HDU | `1` |
| `XTENSION` | `BINTABLE` |
| `BITPIX` | `8` |
| `NAXIS` | `2` |
| `NAXIS1` | `300` |
| `NAXIS2` | `253658` |
| `PCOUNT` | `0` |
| `GCOUNT` | `1` |
| `TFIELDS` | `51` |
| Esquema | Las 51 columnas exactas de la sección 6 |

| Identidad | SHA-256 o estado |
|---|---|
| Cabecera observada | `8fe8ecf7191f7b6eeebcb613e34b56776b27d4c14193669eb1fbc205ae1e8d7f` |
| Candidato físico observado | `a18f93063fd73529860c6d4e8acb27a3e792e0f059c07a42eed51b9acc52bd7c` |
| `EXPECTED_PROVIDER_FULL_FILE_SHA256` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |
| `LOCALLY_VERIFIED_FULL_FILE_SHA256` | `ABSENT_UNRESOLVED` |

La igualdad física con el contrato north termina en la estructura. No se infiere identidad de poblaciones ni igualdad de valores.

## 9. Contrato `SOUTH_PATCH_LIST`

### 9.1 Identidad y estructura

| Propiedad | Valor congelado |
|---|---|
| Rol | `SOUTH_PATCH_LIST` |
| Recurso | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` |
| Compresión de transporte | `identity` |
| HDU | `1` |
| `XTENSION` | `BINTABLE` |
| `BITPIX` | `8` |
| `NAXIS` | `2` |
| `NAXIS1` | `14` |
| `NAXIS2` | `1691` |
| `PCOUNT` | `0` |
| `GCOUNT` | `1` |
| `TFIELDS` | `3` |

### 9.2 Columnas ordenadas

| # | `TTYPE` | `TFORM` |
|---:|---|---|
| 1 | `RELEASE` | `I` |
| 2 | `BRICKID` | `J` |
| 3 | `BRICKNAME` | `8A` |

### 9.3 Evidencia e integridad

| Identidad | SHA-256 o estado |
|---|---|
| Cabecera observada | `f1e338aa4e2c8211f7a01d05e7ede15d91628c291bba1e35d30931a0ceb0b112` |
| Candidato físico observado | `8216278b05e16134f6853f3dfbf3a5c77c347420b9b62eb9aac2abbe68cbb821` |
| Checksum completo del proveedor | `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND` |
| `EXPECTED_PROVIDER_FULL_FILE_SHA256` | `ABSENT_UNRESOLVED` |
| `LOCALLY_VERIFIED_FULL_FILE_SHA256` | `ABSENT_UNRESOLVED` |

No se puede sustituir el checksum ausente con `ETag`, `Content-Length`, hash de prefijo, hash de cabecera ni hash de candidato físico.

## 10. Clave candidata de membership de la patch list

Se congela la presencia estructural:

```text
BRICKNAME / 8A
classification = STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE
```

No se clasifica como `MEMBERSHIP_KEY_ENABLED`. El parser futuro permanece deshabilitado. Antes de cualquier promoción se requieren reglas prospectivas y pruebas para:

- decodificación ASCII/string;
- semántica exacta de los 8 bytes;
- padding por espacios o NUL;
- valores blank o null;
- unicidad;
- duplicados;
- consistencia con `BRICKID`;
- semántica de `RELEASE`;
- integridad del archivo completo;
- matching exacto con `brickname` de root y regional.

Este documento no congela semántica de filas ni valida membresía real.

## 11. Representación física de `BRICKID`

| Rol | Nombre exacto | Representación congelada |
|---|---|---|
| `ROOT_SUMMARY` | `BRICKID` | `J` / `int32` |
| `NORTH_SUMMARY` | `brickid` | `J` / `int32` |
| `SOUTH_SUMMARY` | `brickid` | `J` / `int32` |
| `SOUTH_PATCH_LIST` | `BRICKID` | `J` / `int32` |

Se conserva el evento histórico `BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`. Amendment 004 corrigió prospectivamente la expectativa documental north/south de `int16` a `int32`. La causa de la discrepancia original permanece sin resolver. La coincidencia de representación no demuestra igualdad de valores entre tablas.

## 12. Frontera de clasificación de campos

Este contrato físico no modifica las clasificaciones de Amendment 003:

- `TECHNICAL_ALLOWED` permanece `TECHNICAL_ALLOWED`;
- `KNOWN_BUT_FORBIDDEN` permanece `KNOWN_BUT_FORBIDDEN`;
- cualquier `UNKNOWN_PROVIDER_FIELD` permanece fail-closed.

La presencia de una columna en un contrato físico solo permite validar estructura. No autoriza que sus valores crucen la frontera de `ProviderSchemaAdapter`, ni que sean leídos, registrados, proyectados, ordenados o usados para selección. Esta regla incluye campos conocidos pero prohibidos.

## 13. Política de `NAXIS2`

Cada `NAXIS2` se congela como `EXPECTED_REPRESENTATION_NAXIS2` de la identidad exacta del recurso observado:

| Rol | `EXPECTED_REPRESENTATION_NAXIS2` |
|---|---:|
| `ROOT_SUMMARY` | 662174 |
| `NORTH_SUMMARY` | 93548 |
| `SOUTH_SUMMARY` | 253658 |
| `SOUTH_PATCH_LIST` | 1691 |

Estos valores forman parte de la identidad de representación; no prueban contenido, membresía ni semántica de filas. Si una adquisición futura autorizada de la misma identidad inmutable presenta otro `NAXIS2`, el consumidor debe fallar cerrado por representation drift. No debe reescribir automáticamente este contrato.

## 14. Semántica pendiente de strings

Solo se congela `BRICKNAME TFORM=8A` donde corresponda. No se congela todavía normalización de celdas. Permanecen sin resolver:

- presencia de espacios finales;
- presencia de NUL;
- política de decode;
- política de trim;
- rechazo de contenido malformed o non-ASCII.

Una operación futura con filas debe congelar la política de decodificación antes de que valores de join o membership influyan en una selección. No se puede diseñar esa política después de mirar resultados candidatos.

## 15. Integridad de archivo completo

Para root, north y south existen valores `EXPECTED_PROVIDER_FULL_FILE_SHA256` recuperados de manifiestos autorizados. Una futura adquisición productiva debe verificar localmente todos los bytes del archivo completo contra el valor esperado antes de decodificar. Evidencia HEAD, prefijos Range y hashes de cabecera son insuficientes.

Para la patch list no existe un checksum completo autorizado del proveedor. Su integridad productiva queda bloqueada hasta que una estrategia separada sea especificada, revisada y autorizada. Este documento no decide esa estrategia.

## 16. Matriz normativa de activación

| Rol | Physical schema frozen | Expected provider checksum known | Full-file locally verified | Row semantics validated | Production decode enabled |
|---|---:|---:|---:|---:|---:|
| `ROOT_SUMMARY` | `true` | `true` | `false` | `false` | `false` |
| `NORTH_SUMMARY` | `true` | `true` | `false` | `false` | `false` |
| `SOUTH_SUMMARY` | `true` | `true` | `false` | `false` | `false` |
| `SOUTH_PATCH_LIST` | `true` | `false` | `false` | `false` | `false` |

Esta matriz es normativa. Un estado `true` en una columna no promueve ninguna otra columna.

## 17. Implementación futura requerida

El código actual no implementa todavía Amendment 004 ni estos `PhysicalContracts` productivos. Una tarea posterior y separada deberá:

1. actualizar los tipos lógicos regionales;
2. añadir contratos físicos productivos para los cuatro roles;
3. ligar hashes exactos de cada contrato de esquema;
4. conservar el firewall de campos prohibidos;
5. conservar deshabilitado el parser de la patch list;
6. añadir fixtures sintéticos que reproduzcan los cuatro esquemas físicos observados;
7. retener todas las regresiones existentes;
8. producir un nuevo agregado de implementación y un nuevo replay receipt.

Esta congelación documental no realiza ni autoriza esa implementación.

## 18. Bloqueos abiertos

Después de esta congelación permanecen abiertos, como mínimo:

1. adopción en código de Amendment 004 y estos contratos;
2. verificación de integridad completa de root, north y south durante una adquisición de metadata autorizada;
3. estrategia de integridad completa para la patch list;
4. política prospectiva de decodificación y padding de strings;
5. validación de valores de membership de la patch list;
6. semántica de filas de `RELEASE`;
7. validación de unicidad, duplicados y nulls;
8. binding de derechos productivos;
9. manifiesto productivo de metadata bootstrap;
10. autorización humana `METADATA_BOOTSTRAP_ONLY`.

No se asigna estado READY.

## 19. Estado congelado

El estado actual permanece `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

`ProviderSchemaAdapter` productivo permanece deshabilitado. El parser de patch list permanece deshabilitado. No se creó manifiesto de bootstrap, registro de derechos, selección de bricks ni ejecución científica. Esta tarea usó cero red y cero valores de filas.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
