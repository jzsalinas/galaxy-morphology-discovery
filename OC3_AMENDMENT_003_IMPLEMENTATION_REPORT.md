# OC-3 Amendment 003 — informe de implementación y verificación sintética

**Fecha:** 2026-09-18  
**Alcance:** implementación del boundary de esquema proveedor definido por Amendment 003 y replay exclusivamente sintético/local.  
**Estado:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**OC-3 REMAINS NOT STARTED.**

## 1. Autoridades verificadas

Los bindings exigidos se verificaron antes de modificar código:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_AMENDMENT_002_IMPLEMENTATION_REPORT.md` | `8ca240b5855c5196a78b8cfa2a1860a179b1d1f360a3f4aa95893f74f16da0f0` |
| `OC3_PREFLIGHT_ENVIRONMENT_VERIFICATION.md` | `ae131bbfe69efaae983cc353518c1a8cafde97893cb935fc8ec86a7079b71ded` |
| `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md` | `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b` |
| `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md` | `d02815a66f27df67e60f0cb1dc4d38a977e70c492417d3397946911159bf31c9` |

El agregado histórico anterior a Amendment 003 permanece registrado como:

`PRE_AMENDMENT_003 = 37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`

## 2. Archivos de implementación y evidencia

### Código creado

- `oc3/oc3lib/provider_schema.py`: contratos lógicos/físicos, field IDs, lectura selectiva FITS, DTOs, joins, predicado g/r/z y firewall de patch list.

### Código modificado

- `oc3/oc3lib/core.py`: Amendment 003 incorporado al binding de autoridades.
- `oc3/oc3lib/bootstrap.py`: binding de esquema proveedor, bloqueo de proyecciones libres en producción, selector tipado por DTO y enforcement north 9011.

### Pruebas

- `oc3/tests/test_amendment003.py`: 40 casos nuevos con FITS sintéticos locales.
- `oc3/tests/test_amendment002.py`: el puente histórico se marca explícitamente `synthetic_legacy`; north se mantiene fuera de 9012 y ahora exige 9011 según la precedencia de Amendment 003.
- `oc3/tests/test_infrastructure.py`: inventario de autoridades actualizado de seis a siete. No se modificaron golden values estadísticos.

### Evidencia nueva

- `oc3/environment_setup/AMENDMENT_003_SYNTHETIC_TESTS.log`.
- `oc3/environment_setup/AMENDMENT_003_SYNTHETIC_TESTS.json`.
- `oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json`.
- `OC3_AMENDMENT_003_IMPLEMENTATION_REPORT.md`.

Las verificaciones de sintaxis generaron/actualizaron caches CPython bajo `__pycache__`. Son derivados no autoritativos, no contienen evidencia de ejecución y están excluidos por la regla de agregado, que solo incluye archivos `*.py` fuera de `.venv`.

No se modificaron `oc3/environment_setup/ENVIRONMENT.json`, `PREPARATION_RECEIPT.json`, el entorno `.venv`, especificaciones anteriores ni informes históricos.

## 3. Identidad de implementación

La regla histórica `implementation_hash` se aplicó a los 14 archivos Python actuales bajo `oc3`, excluyendo `.venv`.

Nuevo agregado:

`e374e482cc97c66399025c2bbe0776749dcbd8451998edd441bab165c03fd683`

El agregado anterior no fue sobrescrito ni presentado como certificación del código nuevo.

## 4. Arquitectura `ProviderSchemaAdapter`

La ruta implementada es:

```text
recurso local sintético inmutable
→ identidad de rol tipada
→ SHA-256 completo
→ inspección estructural FITS
→ comparación de todas las columnas
→ clasificación completa
→ lectura selectiva TECHNICAL_ALLOWED
→ transformaciones/constantes congeladas
→ OC3_TECHNICAL_CANDIDATE_V1
→ selector tipado
→ orden SHA-256 OC3-v1
```

`ProviderIdentity`, `ProviderRole`, `PhysicalContract` y `ProviderSchemaAdapter` son boundaries explícitos. El selector rechaza diccionarios/tablas crudos con `RAW_PROVIDER_TABLE_FORBIDDEN`. El único puente para las pruebas Amendment 002 exige `synthetic_legacy=True`, construye un DTO validado y nunca está disponible para una ruta de producción.

## 5. Contratos de esquema

Se implementaron contratos lógicos inmutables/versionados:

- `LOGICAL_CONTRACT_VERSION=OC3_DR9_PROVIDER_LOGICAL_V1`;
- inventario root exacto de 11 campos `TECHNICAL_ALLOWED`;
- inventario regional exacto de 16 campos `TECHNICAL_ALLOWED` y 35 `KNOWN_BUT_FORBIDDEN`;
- hash canónico del contrato lógico;
- `FIELD_ID_NAMESPACE=OC3_PROVIDER_FIELD_ID_V1`.

Se implementaron contratos físicos solamente sintéticos:

- `SYNTHETIC_ROOT_FITS_V1`;
- `SYNTHETIC_REGIONAL_FITS_V1` y variante sintética south ligada al mismo layout de fixture.

Estos fijan HDU, orden, TTYPE, TFORM y ausencia/presencia esperada de TUNIT/TNULL/TSCAL/TZERO para los fixtures. La política de strings sintéticos explicita trim de padding space/NUL observado en los bytes generados.

`PRODUCTION_PHYSICAL_CONTRACTS` permanece vacío. Cualquier decode de producción termina antes de abrir un FITS con `PRODUCTION_PROVIDER_PHYSICAL_CONTRACT_UNAVAILABLE`. No se codificó un HDU, TFORM, scaling, null o unidad real por conjetura.

## 6. Stable field IDs y manifiesto futuro

Cada `FieldId` liga rol lógico, nombre proveedor exacto, clase, tipo lógico y transformación autorizada. Las lecturas usan esos IDs enumerados; no existe un source-column string suministrable por manifiesto.

El bootstrap puede ligar prospectivamente:

- adapter version;
- candidate DTO version;
- field-ID namespace;
- logical-contract version/hash;
- physical-contract ID cuando exista.

Una ruta production exige ese binding y rechaza `JSON_ROWS_V1`/`FITS_BINTABLE_ROWS_V1` con proyección libre mediante `LEGACY_PROVIDER_PROJECTION_FORBIDDEN`. `PROVIDER_FITS_ADAPTER_V1` no admite `projection`. No se creó un manifiesto de producción.

## 7. Boundary de valores prohibidos

El adaptador abre el FITS con Astropy en modo lazy solo para leer headers, tipo de HDU y offsets. No accede a `hdu.data` ni utiliza `Table.read`.

Después de validar **todas** las columnas, cierra el HDU y lee directamente del archivo únicamente los segmentos de bytes de columnas `TECHNICAL_ALLOWED`, calculados a partir del row length y los TFORM ya validados. Las columnas prohibidas no se decodifican ni se materializan como arrays/celdas.

`CellAccessProbe` instrumenta cada acceso en fixtures. Un intento de acceso prohibido produciría `FORBIDDEN_PROVIDER_CELL_ACCESS`. Los tests incluyen sentinels distintivos y verifican cero accesos prohibidos y ausencia de esos valores en DTOs, objetos audit y errores.

Ningún raw HDU, FITS record, nombre desconocido ni valor prohibido sale del boundary.

## 8. Campos desconocidos y discrepancias

Antes de iterar filas se comprueban:

- HDU `BINTABLE` exacta del contrato sintético;
- cardinalidad y nombres exactos de columnas;
- TFORM/dtype y shapes;
- TUNIT/TNULL/TSCAL/TZERO;
- NAXIS1, NAXIS2, PCOUNT y GCOUNT;
- identidad rol↔contrato.

Campo extra, faltante, dtype/shape/HDU/scaling/null/unit incompatible terminan con `PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP`. El error no incluye el nombre desconocido. Checksums se validan antes de inspección FITS.

La discrepancia documental de `brickid` permanece `DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY`. Los contratos sintéticos ejercitan root `J/int32` y regional `I/int16`, pero eso no decide el layout real. Un conflicto fixture↔contrato termina explícitamente sin cast, truncation o wraparound.

## 9. `GRZ_MEDIAN_PRESENT_V1`

Se implementó exactamente:

```text
finite_integer(nexp_g) AND nexp_g >= 1
AND finite_integer(nexp_r) AND nexp_r >= 1
AND finite_integer(nexp_z) AND nexp_z >= 1
```

El decoder selectivo produce enteros Python desde el TFORM físico validado. Nulls, booleanos, floats, arrays, scalars NumPy no autorizados u otros valores no enteros fallan cerrado. Cero en cada banda se probó por separado.

El DTO solo conserva `grz`. Magnitudes de `nexp` por encima de uno no modifican el DTO, orden ni selección. `nexphist` existe solamente en `OC3_GRZ_TECHNICAL_AUDIT_V1` y sus cambios no alteran elegibilidad u orden.

## 10. DTO y objeto audit

`OC3_TECHNICAL_CANDIDATE_V1` es un dataclass inmutable con exactamente:

`region, survey, release_family, generation, brickname, brickid, ra, dec, primary_bounds, grz, corrected_9012, survey_primary, evidence_refs`.

Valida procedencia north/south, generación, ASCII, rango documental de brick ID, geometría finita, booleanos y referencias ordenadas únicas. Su serialización es JSON canónico UTF-8 con versión y un LF; su SHA-256 es determinista.

`OC3_GRZ_TECHNICAL_AUDIT_V1` está separado. Puede contener `nexp_*` y `nexphist_*`, pero nunca se pasa al selector. No contiene campos prohibidos.

## 11. Procedencia y joins

Las constantes de rol producen:

- north: `north`, `BASS_MzLS`, `DR9`, `9011`, `corrected_9012=false`;
- south: `south`, `DECaLS`, `DR9`, `9012`, `corrected_9012=true` solo por membership sintética exacta.

North no consulta ningún proveedor de patch membership. South sin membership habilitada termina con `PATCH_LIST_ADAPTER_DISABLED`. El helper de membership south está marcado `synthetic_only`; no puede confundirse con evidencia real.

Los joins root↔regional son exactos y uno-a-uno. Duplicados, root ausente, diferencias de case, conflicto de brick ID o geometría fallan. No hay fuzzy matching, aliases ni coerción numérica. Los fixtures definen explícitamente su padding y comparación exacta.

La permutación de filas conserva candidatos y selección. Variar arbitrariamente valores prohibidos conserva bytes del DTO y resultados de selección; el hash completo del recurso permanece en el recibo de adquisición, fuera del input del ordering.

## 12. Selector y regresiones

`resolve_bootstrap_bricks` recibe solamente `TechnicalCandidate`, salvo el puente sintético explícito descrito arriba. North exige 9011. South exige membership 9012. El orden permanece:

`SHA256(UTF-8("OC3-v1|brick|<region>|<brickname>"))`, ascendente, con brickname ASCII como desempate.

No se modificaron Amendment 001 T10, PCG64/SeedSequence ni sus golden values. La prueba golden raw RNG pasó. Las pruebas Amendment 002 de promoción única, ledger, subpresupuestos, recuperación de crashes, firewall y causalidad bootstrap/final pasaron dentro del replay completo.

## 13. Patch-list firewall

`PatchListSchemaAdapter.decode_production` termina siempre con:

`PATCH_LIST_ADAPTER_DISABLED`

No existe parser real, columna `BRICKNAME` supuesta, HDU elegida, fallback ni acceso a `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits`.

## 14. Replay sintético final

El replay final se ejecutó exclusivamente con:

`oc3/.venv/bin/python oc3/tests/run_tests.py`

El runner sustituyó `socket.socket`, `socket.create_connection` y `socket.getaddrinfo` por una función que falla ante cualquier intento de red.

| Métrica | Resultado |
|---|---:|
| tests totales | 182 |
| passed | 182 |
| failed | 0 |
| skipped | 0 |
| red real | 0 |
| synthetic_only | true |

Los 142 casos anteriores permanecen en la misma suite y todos pasaron. Se añadieron 40 casos Amendment 003. No se cambiaron golden values para obtener el resultado.

| Evidencia | SHA-256 |
|---|---|
| `AMENDMENT_003_SYNTHETIC_TESTS.log` | `e3a4e916c3deb4d6b2457561ace6220955bcc6e8fe09120c755bde420e4b2d6b` |
| `AMENDMENT_003_SYNTHETIC_TESTS.json` | `8de7c0e756ca8510a580671ee4939bc9719f1a0e9a517795dea79e777b2ae219` |

## 15. Entorno independiente y nuevo recibo

Se verificaron 3.668 entradas esperadas y 3.668 observadas en `oc3/.venv`, con cero faltantes, discrepancias o extras bajo la regla congelada que excluye `__pycache__`/`.pyc`.

El fingerprint reproducido permanece:

`b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`

Versiones efectivas:

- Python 3.12.14;
- NumPy 2.5.3;
- Astropy 8.0.1;
- PyArrow 25.0.1.

No se instalaron paquetes ni se modificó `.venv`. El recibo histórico `PREPARATION_RECEIPT.json`, SHA-256 `0bce87d275ca71f6d6bef39f597fb354a3c1813c150830b395a1628d3b638654`, se conserva como evidencia histórica del entorno anterior; no certifica el código nuevo.

El nuevo recibo canónico es `oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json`, SHA-256:

`09c9676e9f7f3b2ce8f063aa63b34fcc7d40fe3299cb898ecfdb76b95522a38e`

Liga Amendment 003, ambos agregados de implementación, fingerprint, inventario, versiones, resultados 182/182, hashes del log/resultado, cero red, el recibo histórico y `scientific_execution=NOT_STARTED`.

## 16. Ausencia de ejecución de producción

- solicitudes survey: 0;
- DNS survey: 0;
- bytes DR9: 0;
- FITS reales: 0;
- manifiestos bootstrap de producción: 0;
- rights records de producción: 0;
- ledgers de producción: 0;
- promociones: 0;
- bricks reales seleccionados: 0.

Los FITS usados por tests se crearon dentro de directorios temporales y fueron eliminados al terminar cada caso. No contienen nombres de bricks DR9 reales.

Los directorios `oc3/INPUTS`, `oc3/provenance`, `oc3/RAW_IMMUTABLE`, `oc3/TECHNICAL_INDEX` y `oc3/reports` permanecen sin archivos de producción.

## 17. Bloqueos de producción

Permanecen abiertos:

1. contratos binarios reales root/regionales: HDU, TFORM, endian, scaling, nulls, unidades, strings y comparación geométrica;
2. resolución prospectiva de `DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY` para `brickid` con evidencia de bytes;
3. checksum, esquema, HDU, membership key, cardinalidad y null/scaling de la lista real 9012;
4. habilitación prospectiva del adapter real de patch list;
5. bytes, checksums y tamaños reales de los recursos proveedor;
6. production rights binding;
7. manifiesto bootstrap de producción;
8. autorización humana concreta `METADATA_BOOTSTRAP_ONLY`.

El siguiente blocker causal es obtener y revisar los contratos binarios/checksums de proveedor, en especial la lista 9012, mediante una tarea documental/metadata separada autorizada. Esta implementación no asigna READY.

## 18. Estado terminal

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

**OC-3 REMAINS NOT STARTED.**
