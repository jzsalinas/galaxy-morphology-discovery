# OC-3 — Clarification 001 del estado de regresión posterior a Probe 001

**Fecha:** 2026-09-19  
**Naturaleza:** aclaración documental prospectiva del estado persistente esperado.  
**Cambio de código o pruebas:** ninguno.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades y estado verificados

Antes de crear esta aclaración se verificaron localmente los siguientes bindings:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md` | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_IMPLEMENTATION_REPORT.md` | `52d9bb24ab94d602f32afd13989fdd9fb36563ac1014fa2db7e70b02e3390c32` |
| `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json` | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_EXECUTION_AUDIT.md` | `3cc152d5a05d3dcb5d348d22d0ec271c416c3a824518a35b067edf34d368654c` |
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |

También se verificaron:

| Binding | Valor |
|---|---|
| Agregado de implementación actual | `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea` |
| Fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Intento real permitido | `OC3-PHYSICAL-CONTRACT-PROBE-001` |
| Resultado terminal persistido | `PROBE_PHYSICAL_CONTRACTS_RESOLVED` |
| Ejecución científica persistida | `NOT_STARTED` |

El runner sintético oficial, con su firewall instalado antes del discovery/import, produjo:

| Métrica | Resultado observado |
|---|---:|
| Total | 307 |
| Passed | 306 |
| Failed | 1 |
| Skipped | 0 |
| `real_network_requests` | 0 |

La única falla fue `test_89_no_real_probe_attempt_directory`. Su única causa fue la aserción `assertFalse((PROJECT / "oc3/provider_contract_probe").exists())`: el directorio ahora existe legítimamente porque Probe 001 fue autorizado, ejecutado, completado y auditado. No falló ninguna otra prueba ni se observó otra causa. Una divergencia de estos hechos habría producido `POST_PROBE_REGRESSION_CLARIFICATION_INTEGRITY_FAILURE` e impedido esta aclaración.

## 2. Propósito y alcance

Esta aclaración cambia únicamente el estado persistente que debe esperar la regresión después de la ejecución legítima de Probe 001. No debilita la invariante histórica anterior a la ejecución.

La invariante histórica fue correcta:

```text
ANTES de existir una sonda real autorizada:
oc3/provider_contract_probe/ no debe contener ningún intento real.
```

La invariante posterior es ahora:

```text
DESPUÉS de Probe 001 autorizado, completado y auditado:
la evidencia exacta e inmutable de ese único intento debe permanecer presente.
```

Por ello, la ausencia del directorio de intento ya no es una condición válida de regresión para este workspace canónico. La nueva condición es la presencia, singularidad e integridad exacta de la evidencia autorizada.

Esta aclaración no implementa Amendment 004, no modifica código o pruebas, no crea un replay receipt y no autoriza ninguna ejecución.

## 3. Transición explícita del estado de regresión

La transición se congela así:

| Estado | Invariante |
|---|---|
| `PRE_PROBE_001` | `NO_REAL_PROBE_ATTEMPT_EXPECTED` |
| `POST_PROBE_001` | `ONE_AUDITED_REAL_PROBE_ATTEMPT_EXPECTED` |

La autoridad de transición es la autorización humana completada para Probe 001, junto con el resultado terminal persistido y su auditoría read-only.

`test_89_no_real_probe_attempt_directory` no era incorrecta cuando se creó. Expresaba correctamente el estado `PRE_PROBE_001`. La ejecución autorizada cambió el estado del workspace; no corrompió retroactivamente la prueba ni sus replay receipts históricos.

## 4. Único intento real permitido

| Propiedad | Valor congelado |
|---|---|
| `attempt_id` | `OC3-PHYSICAL-CONTRACT-PROBE-001` |
| Directorio | `oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001` |
| SHA-256 de autorización | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |
| Terminal | `PROBE_PHYSICAL_CONTRACTS_RESOLVED` |
| `scientific_execution` | `NOT_STARTED` |

No se permite un segundo intento real, un resume, otro directorio hermano ni evidencia adicional de ejecución. La presencia de cualquier intento distinto debe fallar cerrado.

## 5. Inventario inmutable auditado

El inventario normativo contiene exactamente 13 archivos. Las rutas son relativas a `oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001`.

| Ruta relativa | Bytes | SHA-256 |
|---|---:|---|
| `PROBE_CHECKSUM_EVIDENCE.json` | 1,109 | `f464983d87ef4ab2776b699a54490874667c7f4a7ca138269180d8467defee3f` |
| `PROBE_EVENTS.json` | 145 | `d130134b7bb46a612c8213aba80b0d5d613303d04d1870063b5d0a5677e75fd0` |
| `PROBE_LEDGER.sqlite` | 40,960 | `8bd834e3a1fa28d820d7ac81f8fe049749761f518b569cc2d915beb32191b441` |
| `PROBE_PHYSICAL_CONTRACT_CANDIDATES.json` | 15,421 | `eaa8287fab7c4de44dc265239dcf3b9e9e56f5c2adce4334711634cb9e9b7eb1` |
| `PROBE_TERMINAL.json` | 257 | `27b944d654045c314505e548242eee85416cf9391ffc337d5f4a834fbb3c84e3` |
| `PROBE_TRANSPORT_EVIDENCE.json` | 2,462 | `cd0248193669bb2d303ca55fb24e3ab46f9b0ac2aefc59086c3df2dd49f4975a` |
| `compressed_prefix/NORTH_SUMMARY/0.part` | 65,536 | `7b0cb006d16f193cdcef2120169d039300aa56d9aca863decc3d654c20be4cd6` |
| `compressed_prefix/ROOT_SUMMARY/0.part` | 65,536 | `28c7b004fbbcf9cd02999c6345b6b5f428c901bf8b76fc10d6612aa29d5ded5e` |
| `compressed_prefix/SOUTH_SUMMARY/0.part` | 65,536 | `383aa7a812405560e418efff4109268979c3ad45118e9d00ffbb0ad3c666748b` |
| `transport/NORTH_SUMMARY.head.json` | 508 | `833b31cdccb786069e07c2bbf0e286ca8a84c410399ab3b9ad1fa28e321e0a9c` |
| `transport/ROOT_SUMMARY.head.json` | 490 | `bf79a2189fd3ae09863059f4c5bcd5ae6531a4d242d75cd813603f3b8ddc972a` |
| `transport/SOUTH_PATCH_LIST.head.json` | 410 | `9d8ce43f7bc76529045a80c495d47787c1d7d539cbbd142d2d0889919edc6c3c` |
| `transport/SOUTH_SUMMARY.head.json` | 508 | `71636341463e738a601cf8aa8c24131e900762bb802ac5d17b12751bf24cb166` |

Una regresión posterior deberá comparar estas 13 rutas, sus tamaños y sus SHA-256 exactos. No debe regenerar valores esperados a partir de evidencia alterada. Un archivo faltante, adicional, cambiado o reubicado debe producir una falla.

## 6. Invariante de regresión `POST_PROBE_001`

La implementación posterior debe reemplazar el significado conductual de `test_89_no_real_probe_attempt_directory` por una prueba cuyo propósito sea aproximadamente `test_89_single_audited_probe_attempt_is_preserved_immutably`. El nombre Python exacto puede elegirse durante esa implementación; su semántica queda fijada aquí.

La prueba debe verificar conjuntamente:

1. que `oc3/provider_contract_probe` existe;
2. que contiene exactamente un directorio de intento real, `OC3-PHYSICAL-CONTRACT-PROBE-001`;
3. que no existe otro directorio de intento hermano;
4. que el inventario auditado contiene exactamente las 13 rutas de la sección 5;
5. que el tamaño y SHA-256 de cada archivo coinciden exactamente;
6. que `PROBE_TERMINAL.json` conserva `PROBE_PHYSICAL_CONTRACTS_RESOLVED`;
7. que `scientific_execution` permanece `NOT_STARTED`;
8. que el binding de autorización permanece ligado al SHA-256 de Probe 001 indicado aquí;
9. que no existe evidencia de resume;
10. que no existe evidencia de un segundo intento.

El test debe fallar ante cualquier discrepancia. No puede reparar, completar, normalizar o eliminar evidencia.

## 7. Regresión estrictamente read-only

La regresión revisada inspeccionará la evidencia de Probe 001 solo en modo lectura. Debe evitar cualquier operación que pueda modificar los bytes o metadata persistente. En particular, no debe:

- tocar mtimes;
- reescribir JSON canónico;
- abrir SQLite en modo read-write;
- ejecutar `VACUUM` ni ninguna sentencia mutante;
- normalizar finales de línea;
- recrear evidencia faltante;
- reparar hashes discrepantes;
- borrar archivos desconocidos;
- modificar el directorio del intento.

Si se requiere inspeccionar el ledger, debe abrirse con URI SQLite explícitamente read-only e immutable, por ejemplo con semántica equivalente a `mode=ro&immutable=1`. La comprobación primaria de integridad sigue siendo el tamaño y SHA-256 exactos del archivo.

## 8. Evidencia real y fixtures sintéticos

El directorio de Probe 001 contiene evidencia real preservada. No es un fixture sintético, output desechable, directorio temporal ni un recurso que setup/teardown pueda regenerar o limpiar.

Los tests sintéticos de la sonda deben continuar usando directorios temporales separados. Ningún helper de aislamiento puede borrar, mover, reescribir o sustituir el intento real.

La regresión posterior puede leer bytes para calcular hashes y leer los JSON estructurales requeridos por esta invariante. No puede decodificar los prefijos FITS preservados como datos de tabla ni observar filas o celdas del proveedor.

## 9. Workspace canónico y clean checkout

Se distinguen dos modos de validación cuando una copia intencional del repositorio excluya evidencia runtime:

| Modo | Estado esperado |
|---|---|
| Regresión sintética histórica/preflight | puede operar en un checkout sin evidencia runtime, conservando la invariante `PRE_PROBE_001` de su contexto |
| Auditoría del estado local post-Probe | exige la evidencia exacta de `POST_PROBE_001` |

En el workspace canónico actual, el estado normativo es `POST_PROBE_001`: el único intento auditado debe existir y su integridad debe comprobarse. La implementación futura puede separar arquitectura o entry points para preservar ambos casos, pero no puede omitir silenciosamente el control de integridad en el workspace canónico. En el replay canónico no se acepta un test skipped.

## 10. Comportamiento de red

La revisión de la expectativa de regresión no autoriza red. El replay posterior debe conservar `real_network_requests=0`, instalar el firewall antes de discovery/import y no:

- llamar la ruta de red del CLI de la sonda;
- revalidar URLs remotas;
- reanudar el intento;
- descargar bytes;
- consultar documentación externa.

## 11. Estado científico y productivo

La presencia de evidencia preservada no significa que haya comenzado otro proceso. Permanecen:

| Estado | Valor |
|---|---|
| Metadata bootstrap | `NOT_STARTED` |
| `ProviderSchemaAdapter` production decode | `false` |
| Patch-list membership | `disabled` |
| Ejecución científica | `NOT_STARTED` |
| Selección real de bricks | `NOT_STARTED` |

No existe una transición implícita desde evidencia presente hacia activación productiva.

## 12. Replay receipts históricos

Los replay receipts anteriores con resultado 307/307 permanecen históricamente válidos para el estado `PRE_PROBE_001` en el que fueron producidos. No deben invalidarse, sobrescribirse ni reinterpretarse.

Después de ejecutar legítimamente Probe 001, la vieja aserción de ausencia ya no puede pasar en el mismo filesystem. Esto es una transición del estado persistente, no corrupción retroactiva de la prueba. Un replay posterior deberá producir un recibo nuevo que identifique explícitamente `POST_PROBE_001`.

## 13. Precedencia limitada

Esta aclaración tiene precedencia únicamente sobre tests o aserciones que requieran la ausencia de `oc3/provider_contract_probe/` o de su único intento real auditado.

Permanecen sin cambios todas las demás invariantes, incluidas:

- ningún intento real no aprobado;
- ningún resume automático;
- ninguna segunda ejecución;
- cero red durante replay sintético;
- firewall de observación de filas;
- límites de recursos;
- inmutabilidad de la evidencia real;
- estado OC-3 `NOT_STARTED`.

## 14. Próxima tarea de implementación

Después de congelar y revisar esta aclaración, una tarea separada de adopción de Amendment 004 y los contratos físicos podrá:

1. actualizar la regresión obsoleta de estado del filesystem;
2. demostrar la inmutabilidad exacta de Probe 001;
3. implementar Amendment 004;
4. implementar los contratos físicos congelados;
5. ejecutar la regresión completa post-Probe;
6. producir un agregado de implementación y replay receipt nuevos.

Ninguno de esos pasos se ejecuta mediante esta aclaración.

## 15. Estado actual

Crear este documento no altera código, pruebas, evidencia ni entorno. El agregado de implementación permanece:

`696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea`

El estado permanece `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
