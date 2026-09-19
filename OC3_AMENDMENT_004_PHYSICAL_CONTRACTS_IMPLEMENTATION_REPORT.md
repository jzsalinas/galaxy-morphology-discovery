# OC-3 — informe de implementación de Amendment 004 y contratos físicos DR9

**Fecha:** 2026-09-19  
**Alcance ejecutado:** implementación y verificación sintética/offline completa.  
**Estado de regresión:** `POST_PROBE_001`.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades verificadas

Antes de modificar código se verificaron los siguientes bindings:

| Autoridad o evidencia | SHA-256 |
|---|---|
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| `OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md` | `930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_EXECUTION_AUDIT.md` | `3cc152d5a05d3dcb5d348d22d0ec271c416c3a824518a35b067edf34d368654c` |
| `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json` | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |

El agregado previo coincidió con `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea` y se conserva como `PRE_AMENDMENT_004_PHYSICAL_CONTRACT_ADOPTION`. El fingerprint ambiental coincidió con `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`.

## 2. Transición de regresión `POST_PROBE_001`

La regresión histórica pre-Probe tenía 307 pruebas, con 306 passing y una única falla esperada por la presencia legítima de la evidencia real. Se reemplazó únicamente el significado de `test_89_no_real_probe_attempt_directory` por `test_89_single_audited_probe_attempt_is_preserved_immutably`.

La prueba revisada verifica read-only:

- un solo directorio `OC3-PHYSICAL-CONTRACT-PROBE-001`;
- exactamente 13 archivos auditados;
- tamaños y SHA-256 exactos;
- terminal `PROBE_PHYSICAL_CONTRACTS_RESOLVED`;
- `scientific_execution=NOT_STARTED`;
- binding de la autorización humana;
- cero retries/resume y ningún segundo intento;
- apertura SQLite con `mode=ro&immutable=1`.

Después de este cambio, los 307 tests heredados pasaron antes de implementar Amendment 004. Los 306 tests que ya pasaban permanecen passing y la prueba post-Probe revisada también pasa.

## 3. Archivos cambiados y creados

Modificados:

- `oc3/oc3lib/provider_schema.py`;
- `oc3/tests/test_amendment003.py`;
- `oc3/tests/test_physical_contract_probe.py`.

Creados:

- `oc3/oc3lib/provider_physical_contracts.py`;
- `oc3/tests/test_amendment004_physical_contracts.py`;
- `oc3/environment_setup/AMENDMENT_004_PHYSICAL_CONTRACTS_SYNTHETIC_TESTS.log`;
- `oc3/environment_setup/AMENDMENT_004_PHYSICAL_CONTRACTS_SYNTHETIC_TESTS.json`;
- `oc3/environment_setup/AMENDMENT_004_PHYSICAL_CONTRACTS_REPLAY_RECEIPT.json`;
- este informe.

No se modificaron autoridades, receipts históricos, `.venv` ni evidencia de Probe 001.

## 4. Revisión del contrato lógico

El contrato lógico activo es `OC3_DR9_PROVIDER_LOGICAL_V2_AMENDMENT_004`, SHA-256 `f396ba8dfb933043cf75a3a15a60f6019e77adeeaf2dd8c721d132bc41090a40`.

La identidad histórica `OC3_DR9_PROVIDER_LOGICAL_V1` permanece reproducible con SHA-256 `301ef8bf8d30da2f9bc0410146a7faa6537e4badb5100ae57128d3f4ff5b4373` y no se usa para decode actual.

Se corrigieron exactamente 15 tipos regionales:

- `brickid`: `int32`;
- `nobjs`, `npsf`, `nsimp`, `nrex`, `nexp`, `ndev`, `ncomp`, `nser`, `ndup`: `int32`;
- `ra1`, `ra2`, `dec1`, `dec2`, `area`: `float64`.

Las clases no cambiaron: `brickid` y los cinco campos geométricos siguen `TECHNICAL_ALLOWED`; los nueve contadores siguen `KNOWN_BUT_FORBIDDEN`. Todos los demás tipos permanecen iguales.

## 5. Contratos físicos productivos congelados

Los contratos son constantes inmutables; no se derivan de archivos o manifiestos. Cada hash cubre rol, URL literal, compresión, HDU, estructura FITS, esquema ordenado, metadata ausente, checksum esperado/status y versión.

| Rol | SHA-256 del contrato |
|---|---|
| `ROOT_SUMMARY` | `6e50b8b0c258f10752bf2d7d7d2d88c64ec16899fbb02711fd0621e4d642ea53` |
| `NORTH_SUMMARY` | `59fb8668165d14f201df1f269009ca0b47b41fa431b0bb0d55212c19c77f2677` |
| `SOUTH_SUMMARY` | `2faad729eac8e1912f63e4da8373acdc7cd5e9101601ea51e8ec9fb145dc25fa` |
| `SOUTH_PATCH_LIST` | `5be4df46180c0ec4964b53e3ad095bf75bf80a4c142dc7a8d22ba60efafbbd14` |

La validación de estructura es header-only y rechaza HDU, NAXIS1/2, columnas extra/faltantes/reordenadas, case, TFORM y metadata inesperada. Nunca accede a `hdu.data`.

## 6. Estado de activación y gate de decode

| Rol | Schema frozen | Expected checksum known | Full file bound | Row semantics | Production decode |
|---|---:|---:|---:|---:|---:|
| `ROOT_SUMMARY` | true | true | false | false | false |
| `NORTH_SUMMARY` | true | true | false | false | false |
| `SOUTH_SUMMARY` | true | true | false | false | false |
| `SOUTH_PATCH_LIST` | true | false | false | false | false |

Los estados son dataclasses inmutables e independientes. `physical_schema_frozen=true` no promueve ningún otro estado. Todo intento de decode productivo falla antes de abrir el path con `PRODUCTION_PROVIDER_DECODE_NOT_ENABLED`.

## 7. Integridad completa, patch list y strings

Root, north y south almacenan únicamente sus SHA-256 completos esperados del proveedor. La interfaz futura compara un digest proporcionado, pero no cambia el estado de activación. Una coincidencia sintética probada no establece `full_file_integrity_bound`.

La patch list conserva `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`, no tiene digest esperado y su comparación falla con `PATCH_LIST_FULL_FILE_INTEGRITY_UNRESOLVED`. `BRICKNAME/8A` permanece `STRUCTURAL_MEMBERSHIP_KEY_CANDIDATE`; `PatchListSchemaAdapter` continúa deshabilitado.

No se añadió política productiva de strip/rstrip, padding, NUL, case folding o replacement decoding. Toda operación dependiente de semántica de strings queda bloqueada por `row_semantics_validated=false`.

## 8. Firewall de campos prohibidos y fixtures

Los fixtures sintéticos cubren las cuatro estructuras congeladas. Los regionales contienen 51 columnas con `J` y `D` corregidos. Canarios `int32` fuera del rango `int16` en los nueve contadores prohibidos confirmaron:

- cero accesos prohibidos instrumentados;
- cero campos prohibidos en la tabla permitida;
- cero valores canario en la serialización permitida;
- conservación de las regresiones de DTO, ordering, selector y manifest.

También permanecen las regresiones `GRZ_MEDIAN_PRESENT_V1`, north 9011, patch real deshabilitada, selector sin tablas crudas y RNG dorado de Amendment 001.

## 9. Resultado sintético final

Comando ejecutado con el firewall de socket/DNS instalado antes de discovery/import:

```bash
oc3/.venv/bin/python -I -B oc3/tests/run_tests.py
```

| Métrica | Resultado |
|---|---:|
| Total | 330 |
| Passed | 330 |
| Failed | 0 |
| Skipped | 0 |
| `real_network_requests` | 0 |

| Evidencia | SHA-256 |
|---|---|
| Log final | `3c38aa30ddbb46111a8f2483d613d4892467049839d4778ef455b62be6274dae` |
| Resultado JSON | `eec42a9b795668a09e9dddd1c648e7116fffc93e00d135db13265743b12986bf` |
| Replay receipt | `4b05cef13e0e6af785784c2c6e7da1e1d88887f4f29d42dcb95dc6ca49c75e5b` |

El nuevo agregado de implementación es `034f2a9dc39960e4b89f0abc01ea3c2c91a913f9631fe4f3eb8e3b955d652880`.

El entorno permaneció:

- Python 3.12.14;
- NumPy 2.5.3;
- Astropy 8.0.1;
- PyArrow 25.0.1;
- fingerprint `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`.

## 10. Evidencia real y contabilidad cero

Después del replay se recalcularon los 13 paths, tamaños y SHA-256 congelados de Probe 001: 13/13 coincidieron. No existe un sibling attempt, resume ni segundo intento.

Esta tarea produjo:

- 0 solicitudes reales de red;
- 0 bytes DR9 nuevos;
- 0 filas o celdas reales del proveedor;
- 0 DTO reales;
- 0 valores reales de membership;
- 0 selección real;
- 0 metadata bootstrap;
- 0 manifiestos de bootstrap;
- 0 registros de derechos;
- 0 intentos o resumes de Probe 001.

## 11. Bloqueos restantes

Permanecen pendientes la adquisición autorizada y verificación completa root/north/south, una estrategia de integridad para patch, la política prospectiva de strings y semántica de filas, validación de membership, derechos productivos, manifiesto de metadata bootstrap y autorización humana `METADATA_BOOTSTRAP_ONLY`.

El estado permanece `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`. Production decode es false en los cuatro roles.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
