# OC-3 — especificación prospectiva `PATCH_METADATA_DECODE_ONLY`

**Naturaleza:** especificación offline prospectiva; no implementa ni autoriza ejecución.

**Stage ID futuro:** `OC3-PATCH-METADATA-DECODE-001`.

**Terminal exitoso único:** `PATCH_METADATA_DECODE_VALIDATED`.

**Estado:** `NOT_STARTED`.

## 1. Pregunta y alcance

Esta etapa responde únicamente si el `SOUTH_PATCH_LIST` ya adquirido satisface las restricciones semánticas y relacionales congeladas antes de observar sus filas. Cruza la frontera desde `HEADER_OBSERVED / ROWS_NOT_OBSERVED` hasta la observación de exactamente tres campos PATCH, sólo si todos los gates pasan.

Es estrictamente offline. No autoriza red, readquisición, selección técnica, persistencia de membership, materialización de cohorte, imágenes, análisis morfológico, redistribución ni inicio científico de OC-3.

## 2. Evidencia e inputs cerrados

Raíz inmutable del intento:

`/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/`

| Evidencia | Identidad requerida |
|---|---|
| Terminal del intento | `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`; SHA-256 `6ca38830d7b8f364dbfb722f4c56de4697f80f9be705004d0897b3a13bdccef0` |
| Ledger | identity `c2fea670f7d4594cbe4b9a889f7b95f0f06a7fe81d218198cfef817e62dafc07`; SHA-256 `ff6957e3c74001356edd104d13e4e213f9aba29d04578ea4d680dd390cf8f270` |
| Patch acquisition evidence | SHA-256 `2dfad6faf65c48488d14f8aaacfb5e4a3638f5ac61161aa829e90f59ade04f37` |
| Patch RAW | `RAW_IMMUTABLE/SOUTH_PATCH_LIST/dr9-south-patched-bricks.fits`; 31,680 bytes; SHA-256 `f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6` |
| ROOT RAW para join | `RAW_IMMUTABLE/ROOT_SUMMARY/survey-bricks.fits.gz`; SHA-256 `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| SOUTH RAW para join | `RAW_IMMUTABLE/SOUTH_SUMMARY/survey-bricks-dr9-south.fits.gz`; SHA-256 `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

Antes de decodificar, deben coincidir paths, tamaños, hashes, binding del intento, autorización `214d361fe163da1417e14d61efa203b3bdb97f15c4d7b6481aa50c2643345b56`, agregado `432bcd449673786075938d3a290ad0ea139cc88bf1c2aae758c59d09179ef276`, entorno `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` y contrato físico PATCH `5be4df46180c0ec4964b53e3ad095bf75bf80a4c142dc7a8d22ba60efafbbd14`.

La identidad PATCH se clasifica exclusivamente como:

```text
ACQUISITION_BOUND_LOCAL_SHA256 = f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6
ACQUISITION_BOUND_LOCAL_SHA256_KNOWN = true
PROVIDER_PUBLISHED_CHECKSUM_KNOWN = false
PATCH_DECODE_INPUT_BOUND = true para estos bytes y este intento
```

`PATCH_DECODE_INPUT_BOUND` admite los bytes como entrada local completa del experimento; no los convierte en checksum publicado ni en evidencia independiente del proveedor.

## 3. Boundary de observación

Los únicos valores de celdas PATCH autorizados son:

```text
RELEASE
BRICKID
BRICKNAME
```

Para construir las referencias de join pueden volver a decodificarse, desde los RAW del mismo intento, sólo `BRICKNAME` y `BRICKID` de ROOT y SOUTH. Ningún otro valor ROOT/SOUTH necesita cruzar esta etapa.

Todo otro valor PATCH permanece prohibido: no puede decodificarse, materializarse, compararse, contarse, registrarse, serializarse ni aparecer en errores. Se conserva `OPAQUE_BYTE_TRANSIT != CELL_VALUE_OBSERVATION`. Quedan prohibidas tablas completas, `hdu.data`, `Table.read`, `FITS_rec`, Pandas y record arrays con campos adicionales.

## 4. Gates semánticos prospectivos

La validación completa y fail-closed exige simultáneamente:

- `row_count=1691` y `valid_row_count=1691`;
- cada `RELEASE` es el entero exacto `9012`;
- cada `BRICKNAME` cumple `OC3_BRICKNAME_SEMANTICS_V1`, sin trim, normalización, case folding ni replacement decode;
- cada `BRICKID` es un FITS `J` válido con semántica signed int32;
- 1.691 valores únicos de `BRICKNAME`;
- 1.691 valores únicos de `BRICKID`;
- 1.691 pares únicos `(BRICKNAME, BRICKID)`.

Debe reutilizarse `validate_complete_patch_rows()` y las funciones de semántica ya congeladas. No se ajustan reglas después de observar resultados.

## 5. Gates relacionales

La clave de join es el `BRICKNAME` validado, comparado por sus ocho bytes canónicos exactos. Para cada fila PATCH debe existir exactamente una fila ROOT y una fila SOUTH con ese `BRICKNAME`; los tres `BRICKID` deben ser idénticos. Debe reutilizarse `validate_patch_joins()`.

El éxito exige:

```text
missing_from_ROOT = 0
missing_from_SOUTH = 0
multiplicity_failures = 0
brickid_mismatches = 0
brickname_mismatches = 0
ambiguous_joins = 0
exact_ROOT_matches = 1691
exact_SOUTH_matches = 1691
```

No se permiten joins fuzzy, proximidad, aliases, normalización, fallback por ID ni reparación heurística.

## 6. Fallo y no adaptación

Cualquier discrepancia de binding/integridad, campo observado inesperado, cardinalidad, `RELEASE`, semántica, unicidad o join termina como `PATCH_METADATA_DECODE_FAILED` con un código técnico cerrado. No se limpia, filtra, deduplica, repara ni descarta ninguna fila. La evidencia de fallo puede conservar únicamente bindings, contadores agregados y el primer código; nunca el valor, identidad o índice de la fila infractora.

## 7. Outputs cerrados

Directorio futuro exacto:

`/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/patch_metadata_decode/OC3-PATCH-METADATA-DECODE-001/`

Únicos artifacts permitidos:

```text
PATCH_DECODE_INPUT_BINDING.json
PATCH_DECODE_AGGREGATE_EVIDENCE.json
PATCH_DECODE_TERMINAL.json
PATCH_DECODE_RUN.log
```

Pueden contener hashes/bindings, conteos de filas y `RELEASE`, conteos de unicidad y joins, contadores de observación del decoder, primer error y terminal. No pueden contener filas, nombres o IDs individuales, membership lists, tablas unidas, DTOs, índices de cohorte ni selecciones. El RAW FITS sigue siendo el único artifact row-bearing.

`PATCH_METADATA_DECODE_VALIDATED` significa solamente que el contrato semántico y relacional PATCH pasó. No significa checksum del proveedor, selección autorizada, cohorte materializada, redistribución permitida ni OC-3 iniciado.

## 8. CLI y límites de implementación

Entrada CLI futura exacta:

```bash
/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/oc3_patch_metadata_decode.py --execute-offline --attempt-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001 --output-directory /home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/patch_metadata_decode/OC3-PATCH-METADATA-DECODE-001
```

El entry point debe ser incapaz de construir transporte, resolver DNS o aceptar URLs. Los paths y hashes anteriores son cerrados; no admite otro attempt, input o output. Límites máximos: 0 solicitudes, 0 bytes de red, concurrencia 1, un thread, GPU 0, RAM 1 GiB, I/O local 512 MiB, output 1 MiB, compute 300 s y wall 900 s.

La implementación debe extender la arquitectura manual row-stride de `SelectiveFitsDecoder` con un modo PATCH cerrado a tres campos, conservando tripwires por campo, y reutilizar `validate_complete_patch_rows()` y `validate_patch_joins()`. No debe crear un lector PATCH genérico ni habilitar `PatchListSchemaAdapter.decode_production()` fuera de este stage.

Pruebas sintéticas enfocadas mínimas: paths/hashes cerrados; cero red; tres campos y tripwire para cualquier cuarto; tránsito opaco; 1691/1690/1692 filas; `RELEASE`; brickname/int32; tres unicidades; faltantes, multiplicidad y mismatch en ambos joins; ausencia de valores por fila en outputs; terminales y límites. Después de implementar y revisar, se permite una sola invocación real offline; si supera los umbrales de `AGENTS.md`, se entrega como CLI para ejecución humana.

## 9. Estado y frontera siguiente

```text
Metadata Bootstrap Attempt 001 = METADATA_BOOTSTRAP_PARTIALLY_RESOLVED
PATCH = PATCH_ACQUISITION_BOUND_PENDING_HUMAN_REVIEW
PATCH_METADATA_DECODE_ONLY = NOT_STARTED
OC-3 scientific phase = NOT_STARTED
new_network_acquisition_required = false
```

Sólo después de `PATCH_METADATA_DECODE_VALIDATED` puede diseñarse prospectivamente una etapa separada `TECHNICAL_SELECTION / COHORT_MATERIALIZATION`, con sus outputs row-level y selección determinista propios. Esta especificación no la define ni la autoriza.
