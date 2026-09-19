# OC-3 — informe de implementación de semántica de valores e integridad de metadata

**Fecha:** 2026-09-19  
**Alcance ejecutado:** implementación y verificación sintética/offline.  
**Estado de regresión:** `POST_PROBE_001`.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Metadata bootstrap:** `NOT_STARTED`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades verificadas antes de modificar

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md` | `c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348` |
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| `OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md` | `930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155` |
| `OC3_AMENDMENT_004_PHYSICAL_CONTRACTS_IMPLEMENTATION_REPORT.md` | `63268d6e9637083d76eaf5ddf47faa8790f96a507d4f84b3ee8373055408bdad` |
| `oc3/environment_setup/AMENDMENT_004_PHYSICAL_CONTRACTS_REPLAY_RECEIPT.json` | `4b05cef13e0e6af785784c2c6e7da1e1d88887f4f29d42dcb95dc6ca49c75e5b` |

El agregado previo se reprodujo exactamente como `034f2a9dc39960e4b89f0abc01ea3c2c91a913f9631fe4f3eb8e3b955d652880`. El fingerprint ambiental se reprodujo como `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`. La regresión basal pasó 330/330, con 0 fallos, 0 skips y 0 solicitudes reales de red. La evidencia inmutable de Probe 001 pasó 13/13.

## 2. Archivos creados

- `oc3/oc3lib/metadata_value_semantics.py`;
- `oc3/tests/test_metadata_value_semantics.py`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_SYNTHETIC_TESTS.log`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_SYNTHETIC_TESTS.json`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_REPLAY_RECEIPT.json`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_SYNTHETIC_TESTS_PRELIMINARY.log`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_SYNTHETIC_TESTS_PRELIMINARY.json`;
- `oc3/environment_setup/METADATA_VALUE_SEMANTICS_REPLAY_RECEIPT_PRELIMINARY.json`;
- este informe.

No se modificó ningún documento autoritativo, artifact histórico, adapter productivo, selector, manifiesto, autorización, registro de derechos ni archivo de Probe 001.

El primer replay completo pasó 410/410. Una revisión posterior al replay detectó que la igualdad nativa de Python permitía equivalencias de tipos como `0 == False` y `31680.0 == 31680` en objetos construidos manualmente. Antes de congelar el resultado se endurecieron los tipos exactos de la identidad de representación y del conteo adquirido, además de las invariantes de construcción de tipos validados. Los tres artefactos de ese replay se conservaron con sufijo `PRELIMINARY`; no son la evidencia final.

## 3. `OC3_BRICKNAME_SEMANTICS_V1`

El validador normativo recibe únicamente `bytes` exactos. Exige longitud ocho, dígitos ASCII en posiciones 0–3 y 5–7, y `p` o `m` ASCII minúscula en posición 4. Como consecuencia del predicado cerrado, rechaza NUL, espacios, non-ASCII, mayúsculas y cualquier byte malformado. Solo después de validar bytes ejecuta decode ASCII estricto.

La ruta no usa trimming, case folding, normalización Unicode ni decodificación con reemplazo o pérdida. El resultado `ValidatedBrickname` conserva simultáneamente los ocho bytes originales, el string canónico y la versión semántica. La igualdad productiva solo acepta dos instancias validadas y compara los ocho bytes exactamente; un operando sin validar falla cerrado.

## 4. Semántica completa de patch

`PatchRowInput` y `ValidatedPatchRow` implementan una frontera pura para fixtures suministrados por el llamador:

- `RELEASE` debe ser el entero exacto `9012`;
- `BRICKID` debe ser un entero Python no booleano dentro del dominio signed int32;
- `BRICKNAME` debe pasar `OC3_BRICKNAME_SEMANTICS_V1`.

`validate_complete_patch_rows` materializa el conjunto completo de entrada sin limpiar ni descartar filas. Requiere exactamente 1691 filas y unicidad global de `BRICKNAME`, `BRICKID` y `(BRICKID, BRICKNAME)`. Una sola fila inválida o cualquier duplicado invalida el resultado completo. Los tests generan 1691 identidades sintéticas y deterministas; no usan valores de filas reales ni dependen del orden del proveedor.

## 5. Joins exactos

`validate_patch_joins` exige, para cada una de las 1691 filas validadas:

1. exactamente una coincidencia root por los ocho bytes de `BRICKNAME`;
2. igualdad exacta de `BRICKID` patch/root;
3. exactamente una coincidencia south por el mismo `BRICKNAME`;
4. igualdad exacta de `brickid` south con root/patch.

Cero coincidencias, múltiples coincidencias o un ID discrepante fallan cerrado. No existe argumento north, unión fuzzy, proximidad, alias ni fallback por `BRICKID`. Una prueba permuta independientemente root y south y confirma que el resultado no depende del orden.

## 6. Integridad root, north y south

Los digests completos esperados del proveedor se representan como `ExpectedProviderFullFileSha256`; un digest calculado localmente sobre archivo completo usa `LocallyComputedFullFileSha256`. `PartialFileSha256` es un tipo separado y no puede entrar al validador de integridad completa.

El resultado de igualdad es `ProviderIntegrityValidation`. Contiene `production_state_mutated=false` y no modifica `ACTIVATION_STATES`. Los tres digests esperados permanecen:

| Rol | SHA-256 completo esperado del proveedor |
|---|---|
| `ROOT_SUMMARY` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| `NORTH_SUMMARY` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| `SOUTH_SUMMARY` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

## 7. Integridad y continuidad de patch

`ProviderPublishedSha256` y `AcquisitionBoundLocalSha256` son tipos distintos. Para `SOUTH_PATCH_LIST`, el primero solo admite `value=None` y el estado `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`; un digest local no puede convertirse en checksum publicado por el proveedor.

El validador puro de continuidad exige simultáneamente:

| Propiedad | Identidad congelada |
|---|---|
| `Content-Length` | `31680` |
| `ETag` | `"5ffdf047-7bc0"` |
| `Last-Modified` | `Tue, 12 Jan 2021 18:53:59 GMT` |
| URL final | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` |
| redirect | `false` |

Cualquier diferencia produce `PATCH_LIST_REPRESENTATION_DRIFT_STOP`. La validación es de un objeto suministrado; no contiene HTTP.

El objeto futuro `AcquisitionBoundLocalSha256` liga rol, URL, hash del contrato físico, autorización, agregado de implementación, fingerprint ambiental, identidad de representación, 31680 bytes y SHA-256 local. En esta tarea solo se construyeron instancias sintéticas. `PATCH_INTEGRITY_STATE` permanece congelado en `false/false/false`; ninguna validación promueve integridad completa automáticamente.

## 8. Gates y límites preservados

El orden futuro expuesto es:

```text
authorization
→ complete_acquisition
→ full_file_integrity
→ physical_contract_validation
→ value_decode
→ semantic_validation
→ joins
→ membership
→ dtos
→ selection
```

El módulo no expone selector ni acceso a filesystem, red, FITS, tablas, bootstrap o DTOs. Los cuatro estados productivos conservan `production_decode_enabled=false`; `PRODUCTION_PROVIDER_DECODE_NOT_ENABLED` no se modificó. `GRZ_MEDIAN_PRESENT_V1`, el contrato lógico V2, los cuatro hashes de contratos físicos y el firewall de campos prohibidos permanecen iguales. `redistribution=false`.

## 9. Verificación sintética final

El runner instaló el bloqueo de socket/DNS antes de discovery/import y ejecutó:

```bash
oc3/.venv/bin/python -I -B oc3/tests/run_tests.py
```

| Métrica | Resultado |
|---|---:|
| Total | 413 |
| Passed | 413 |
| Failed | 0 |
| Skipped | 0 |
| Pruebas previas retenidas | 330/330 |
| `real_network_requests` | 0 |

La suite nueva aporta 83 pruebas, incluidas las 70 comprobaciones mínimas solicitadas. Los hashes de evidencia final son:

| Artefacto | SHA-256 |
|---|---|
| Log | `b1b4a414b3f8a8f0533a215ee0373c1053e82d9c23f21d7ab413530ea146a197` |
| Resultado JSON | `06f6cd026920548a63d1d9fea05dcf709c8d31b1257626683c832ec184bfb913` |
| Replay receipt | `1c692e67c179ece429fc492e72adeb680b5522ecf98458de60d37b247cf78467` |

El nuevo agregado de implementación es `f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581`.

El entorno permaneció en Python 3.12.14, NumPy 2.5.3, Astropy 8.0.1 y PyArrow 25.0.1, con fingerprint `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`. No se reinstaló ningún paquete.

## 10. Probe 001 y contabilidad cero

Antes de modificar y después del replay se verificaron exactamente los 13 paths, tamaños y SHA-256 congelados de Probe 001. El resultado fue 13/13 en ambos controles. No se reanudó, repitió ni creó otro intento.

Esta implementación produjo:

- 0 solicitudes reales de red;
- 0 bytes nuevos de DR9;
- 0 filas o celdas reales observadas;
- 0 decode productivo;
- 0 membership real;
- 0 DTOs o selección real;
- 0 metadata bootstrap;
- 0 manifiestos o autorizaciones productivas;
- 0 registros de derechos.

## 11. Bloqueos restantes y estado terminal

La infraestructura valida reglas prospectivas, pero no prueba valores de proveedor. Permanecen pendientes una futura autorización separada, adquisición completa, bindings de integridad, validación física, decode productivo revisado, semántica real, joins reales, membership, derechos y manifiesto de bootstrap.

```text
metadata_bootstrap=NOT_STARTED
production_decode_enabled=false
redistribution=false
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
```

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
