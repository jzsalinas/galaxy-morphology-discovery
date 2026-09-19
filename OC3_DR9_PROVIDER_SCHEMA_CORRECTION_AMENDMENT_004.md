# OC-3 — Amendment 004: corrección prospectiva del esquema proveedor DR9

**Fecha:** 2026-09-19  
**Naturaleza:** corrección documental prospectiva basada exclusivamente en evidencia auditada de cabeceras.  
**Cambio de código:** ninguno.  
**Estado:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridad e integridad de la evidencia

Antes de crear esta enmienda se verificaron los siguientes bindings:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md` | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_IMPLEMENTATION_REPORT.md` | `52d9bb24ab94d602f32afd13989fdd9fb36563ac1014fa2db7e70b02e3390c32` |
| `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json` | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_EXECUTION_AUDIT.md` | `3cc152d5a05d3dcb5d348d22d0ec271c416c3a824518a35b067edf34d368654c` |
| `PROBE_PHYSICAL_CONTRACT_CANDIDATES.json` | `eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1` |
| `PROBE_TERMINAL.json` | `27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3` |
| `PROBE_EVENTS.json` | `d130134b7bb46a612c8213aba80b0d5d613303d04d1870063b5d0a5677e75fd0` |

También se verificaron:

- terminal real: `PROBE_PHYSICAL_CONTRACTS_RESOLVED`;
- veredicto de auditoría: `PROSPECTIVE_CORRECTION_REQUIRED_BEFORE_FREEZE`;
- agregado de implementación: `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea`;
- fingerprint ambiental: `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`.

No se modificó evidencia del intento real. Una discrepancia en cualquiera de estos bindings habría producido `AMENDMENT_004_EVIDENCE_INTEGRITY_FAILURE` y detenido la creación de esta enmienda.

## 2. Propósito y causalidad

Amendment 004 corrige exclusivamente expectativas documentales del esquema proveedor que Amendment 003 congeló antes de observar una cabecera real. La secuencia causal es:

```text
PRE-PROBE DOCUMENTATION
→ PROSPECTIVELY FROZEN EXPECTATION
→ BOUNDED HEADER-ONLY OBSERVATION
→ READ-ONLY EXECUTION AUDIT
→ PROSPECTIVE DOCUMENTARY CORRECTION
```

La corrección no usa valores científicos ni adapta criterios después de observar una población. Probe 001 no leyó filas o celdas, no observó bricks candidatos, morfología, coverage, membresías ni valores de `brickid`. La evidencia aplicable se limita a representación estructural FITS y entradas textuales acotadas de manifiestos.

Esta enmienda no reescribe la historia. Amendment 003 permanece como registro de las expectativas originales incompatibles y del método fail-closed que permitió detectarlas.

## 3. Estados probatorios

Este documento utiliza cuatro estados explícitos:

| Estado | Significado |
|---|---|
| `PRE_PROBE_DOCUMENTED` | expectativa congelada antes de Probe 001; puede ser correcta o incompatible con el header observado |
| `OBSERVED_HEADER_ONLY` | hecho estructural recuperado de cabecera, sin lectura de valores de tabla |
| `CORRECTED_PROSPECTIVE_EXPECTATION` | expectativa normativa para una futura congelación de contratos, corregida después de auditoría y antes de decode productivo |
| `STILL_UNRESOLVED` | semántica o integridad que la evidencia de header no puede resolver |

Un `OBSERVED_HEADER_ONLY` no constituye observación de semántica de filas. Un `CORRECTED_PROSPECTIVE_EXPECTATION` tampoco habilita por sí mismo un parser o una adquisición.

## 4. `ROOT_SUMMARY`

### 4.1 Estructura observada

Probe 001 observó exclusivamente por cabecera:

| Propiedad | `OBSERVED_HEADER_ONLY` |
|---|---|
| HDU index | `1` |
| XTENSION | `BINTABLE` |
| BITPIX | `8` |
| NAXIS | `2` |
| NAXIS1 | `70` |
| NAXIS2 | `662174` |
| PCOUNT | `0` |
| GCOUNT | `1` |
| TFIELDS | `11` |
| EXTNAME | ausente |
| CHECKSUM | ausente |
| DATASUM | ausente |

`TUNIT`, `TNULL`, `TSCAL` y `TZERO` están ausentes para las 11 columnas.

### 4.2 Esquema ordenado

| Índice | TTYPE | TFORM |
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

Los nombres, el case, el orden y los tipos lógicos corresponden a la expectativa root previa. No se corrige ningún tipo lógico root. `8A` demuestra representación estructural `char[8]`; no demuestra padding, trimming o decodificación de valores de celda.

## 5. Identidad estructural de `NORTH_SUMMARY` y `SOUTH_SUMMARY`

North y south observaron independientemente:

| Propiedad | North | South |
|---|---:|---:|
| HDU index | 1 | 1 |
| XTENSION | `BINTABLE` | `BINTABLE` |
| BITPIX | 8 | 8 |
| NAXIS | 2 | 2 |
| NAXIS1 | 300 | 300 |
| NAXIS2 | 93,548 | 253,658 |
| PCOUNT | 0 | 0 |
| GCOUNT | 1 | 1 |
| TFIELDS | 51 | 51 |
| EXTNAME | ausente | ausente |
| CHECKSUM | ausente | ausente |
| DATASUM | ausente | ausente |

En ambas cabeceras, `TUNIT`, `TNULL`, `TSCAL` y `TZERO` están ausentes para las 51 columnas. `NAXIS2` se congela únicamente como metadata estructural de esas representaciones; no demuestra igualdad de poblaciones, contenidos o valores entre regiones.

El inventario ordenado de nombres, case y TFORM es idéntico entre north y south:

| # | TTYPE | TFORM | # | TTYPE | TFORM | # | TTYPE | TFORM |
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

Esta simetría es evidencia estructural. No autoriza inferir igualdad de filas, valores, cobertura o población.

## 6. Corrección prospectiva de 15 tipos regionales

Amendment 003 congeló 15 tipos lógicos incompatibles con ambas cabeceras regionales. Se corrigen de forma idéntica para north y south:

| Campo | Clase conservada | `PRE_PROBE_DOCUMENTED` | `OBSERVED_HEADER_ONLY` | `CORRECTED_PROSPECTIVE_EXPECTATION` |
|---|---|---|---|---|
| `brickid` | `TECHNICAL_ALLOWED` | `int16` | `J` / `int32` | `int32` |
| `nobjs` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `npsf` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `nsimp` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `nrex` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `nexp` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `ndev` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `ncomp` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `nser` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `ndup` | `KNOWN_BUT_FORBIDDEN` | `int16` | `J` / `int32` | `int32` |
| `ra1` | `TECHNICAL_ALLOWED` | `float32` | `D` / `float64` | `float64` |
| `ra2` | `TECHNICAL_ALLOWED` | `float32` | `D` / `float64` | `float64` |
| `dec1` | `TECHNICAL_ALLOWED` | `float32` | `D` / `float64` | `float64` |
| `dec2` | `TECHNICAL_ALLOWED` | `float32` | `D` / `float64` | `float64` |
| `area` | `TECHNICAL_ALLOWED` | `float32` | `D` / `float64` | `float64` |

Son exactamente 15 campos. La causa de las discrepancias documentales permanece `STILL_UNRESOLVED`; no se atribuye a versión, error editorial, serialización o implementación.

## 7. Tipos regionales preservados

La corrección anterior no cambia clasificaciones ni tipos que ya coincidían.

### 7.1 `TECHNICAL_ALLOWED`

| Campo | Expectativa preservada | TFORM observado |
|---|---|---|
| `brickname` | `char[8]` | `8A` |
| `ra`, `dec` | `float64` | `D` |
| `nexp_g`, `nexp_r`, `nexp_z` | `int16` | `I` |
| `nexphist_g`, `nexphist_r`, `nexphist_z` | `int32[6]` | `6J` |
| `survey_primary` | `boolean` | `L` |

### 7.2 `KNOWN_BUT_FORBIDDEN`

| Campos | Expectativa preservada | TFORM observado |
|---|---|---|
| `psfsize_g/r/z` | `float32` | `E` |
| `psfdepth_g/r/z` | `float32` | `E` |
| `galdepth_g/r/z` | `float32` | `E` |
| `ebv` | `float32` | `E` |
| `trans_g/r/z` | `float32` | `E` |
| `cosky_g/r/z` | `float32` | `E` |
| `ext_g/r/z` | `float32` | `E` |
| `wise_nobs` | `int16[4]` | `4I` |
| `trans_wise` | `float32[4]` | `4E` |
| `ext_w1`, `ext_w2`, `ext_w3`, `ext_w4` | `float32` | `E` |
| `in_desi` | `boolean` | `L` |

`KNOWN_BUT_FORBIDDEN` continúa prohibido. Observar su metadata física no permite leer, copiar, registrar, proyectar, seleccionar o ordenar por sus valores.

## 8. Resolución física prospectiva de `brickid`

El evento histórico se preserva exactamente:

`BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`

La representación física prospectivamente corregida es:

| Rol | Nombre exacto | Representación corregida |
|---|---|---|
| ROOT | `BRICKID` | `J` / `int32` |
| NORTH | `brickid` | `J` / `int32` |
| SOUTH | `brickid` | `J` / `int32` |

El tipo físico deja de estar pendiente para una futura congelación de contratos: root, north y south exigen `J/int32`. La causa por la que la documentación regional indicaba `int16` permanece `STILL_UNRESOLVED`.

El rango documental contextual `[1, 662174]` es compatible conceptualmente con `int32`, pero no fue usado para derivar el TFORM: la corrección deriva de las cabeceras auditadas. No se observó ningún valor de celda `BRICKID/brickid`.

## 9. Evidencia estructural de `SOUTH_PATCH_LIST`

URL observada y final:

`https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits`

| Propiedad | `OBSERVED_HEADER_ONLY` |
|---|---|
| HDU index | `1` |
| XTENSION | `BINTABLE` |
| BITPIX | `8` |
| NAXIS | `2` |
| NAXIS1 | `14` |
| NAXIS2 | `1691` |
| PCOUNT | `0` |
| GCOUNT | `1` |
| TFIELDS | `3` |
| EXTNAME | ausente |
| CHECKSUM | ausente |
| DATASUM | ausente |

`TUNIT`, `TNULL`, `TSCAL` y `TZERO` están ausentes en las tres columnas.

| Índice | TTYPE | TFORM |
|---:|---|---|
| 1 | `RELEASE` | `I` |
| 2 | `BRICKID` | `J` |
| 3 | `BRICKNAME` | `8A` |

`NAXIS2=1691` coincide con la cardinalidad documental únicamente como header. No demuestra que todas las filas tengan el contenido semántico esperado ni que constituyan membresías válidas.

## 10. Estado de la clave de membership de patch list

Amendment 004 promueve exclusivamente:

```text
BRICKNAME / 8A
INTERNAL_SCHEMA_UNRESOLVED
→ STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE
```

La promoción se justifica porque el campo existe en el header, su nombre exacto es `BRICKNAME`, su TFORM es `8A` y Amendment 003 ya exige joins exactos por `brickname`.

Esto no habilita un parser de membership. Permanecen `STILL_UNRESOLVED`:

- padding, trimming y decodificación exacta de strings;
- unicidad y filas duplicadas;
- nulls, blanks y valores inválidos;
- consistencia con `BRICKID`;
- valores efectivos de `RELEASE`;
- contenido de membership;
- validez semántica de todas las filas.

No se observó ningún valor de membership.

## 11. Checksum de patch list

El estado se conserva exactamente:

`PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`

No se sustituye un checksum de proveedor/full-file por ETag, Content-Length, SHA-256 de prefijo, header SHA-256 o hash del candidato de contrato. La estrategia de integridad productiva de patch list continúa `STILL_UNRESOLVED`.

## 12. Checksums de manifiestos root/regionales

Probe 001 observó entradas textuales que coinciden con las expectativas documentales:

| Rol | SHA-256 del proveedor observado |
|---|---|
| ROOT | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| NORTH | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| SOUTH | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

La distinción normativa permanece:

```text
provider-manifest checksum observed
!=
full local FITS checksum verified
```

La sonda obtuvo prefijos acotados. No adquirió ni verificó localmente los FITS resumen completos contra esos hashes.

## 13. Alcance no resuelto

Esta enmienda corrige expectativas; no crea objetos o archivos `PhysicalContract` de producción. Antes de cualquier decode productivo permanecen pendientes, como mínimo:

- política exacta de padding y decodificación de strings fundada en una adquisición futura autorizada con filas;
- verificación full-file root/north/south contra checksums de manifiesto durante una adquisición autorizada;
- estrategia de integridad full-file para patch list sin checksum proveedor conocido;
- validación de valores de membership de patch list;
- semántica de `RELEASE` al nivel de filas;
- unicidad, nulls y joins exactos al nivel de valores;
- rights binding de producción;
- manifiesto bootstrap de producción;
- autorización humana `METADATA_BOOTSTRAP_ONLY` para artefactos y comando exactos.

La evidencia estructural de cabeceras no se presenta como semántica de filas.

## 14. Precedencia

Amendment 004 tiene precedencia sobre Amendment 003 solamente para:

1. los 15 tipos regionales corregidos en §6;
2. la representación física prospectiva de `brickid` en §8;
3. las expectativas de cabecera estructural observadas por Probe 001;
4. el esquema estructural de patch list en §9;
5. `BRICKNAME/8A` como `STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE` en §10.

Amendment 003 conserva autoridad para:

- clasificación `TECHNICAL_ALLOWED` / `KNOWN_BUT_FORBIDDEN` / `UNKNOWN_PROVIDER_FIELD`;
- `GRZ_MEDIAN_PRESENT_V1`;
- boundary de no observación de valores prohibidos;
- DTO candidato;
- generación north 9011;
- requisito de membership south 9012;
- fail-closed y aislamiento de campos;
- prohibición de decode/selección antes de contrato e integridad válidos.

Amendments 001 y 002 no cambian.

## 15. Separación de implementación

Esta tarea no modifica `provider_schema.py`, `bootstrap.py`, `physical_contract_probe.py`, tests, manifiestos ni recibos ambientales. El agregado de implementación actual permanece como evidencia histórica anterior a la adopción futura de Amendment 004.

Ninguna ruta de producción puede asumir que el código vigente ya aplica esta enmienda. Su adopción requiere una tarea de implementación prospectiva separada, con fixtures locales, revisión y replay.

## 16. Gate siguiente

Después de congelar y revisar Amendment 004, una tarea posterior puede crear, por separado:

`OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md`

Ese documento futuro podrá usar la evidencia estructural auditada de Probe 001, estas expectativas corregidas y las identidades de checksum de los manifiestos. No se crea en esta tarea.

## 17. Estado

El estado permanece:

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

No se asigna metadata-bootstrap READY. No se habilita decode de producción mediante `ProviderSchemaAdapter`. No se habilita el parser de membership de patch list. No se autoriza bootstrap, selección ni otra adquisición.

**DO NOT RE-RUN OR RESUME THE PROBE.**

**OC-3 REMAINS NOT STARTED.**
