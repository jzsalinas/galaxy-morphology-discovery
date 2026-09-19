# OC-3 — informe de implementación de la sonda del contrato físico del proveedor

**Fecha:** 2026-09-18  
**Alcance ejecutado:** implementación y verificación sintética/offline.  
**Ejecución real de la sonda:** `NOT_STARTED`.  
**Estado científico:** `OC-3 REMAINS NOT STARTED.`  
**Preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

## 1. Autoridades verificadas antes de modificar código

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_DR9_PROVIDER_SCHEMA_ADAPTER_AMENDMENT_003.md` | `ca8d2884995a2f3411bc24bb7a2003752153e99ca06cca7c5ba9f2163b47aa8c` |
| `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md` | `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b` |
| `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md` | `d02815a66f27df67e60f0cb1dc4d38a977e70c492417d3397946911159bf31c9` |
| `OC3_AMENDMENT_003_IMPLEMENTATION_REPORT.md` | `a1a02a2cdbb0daa697854c74d9c57cc44697a4486ff3547523271fe7cf90b2eb` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json` | `09c9676e9f7f3b2ce8f063aa63b34fcc7d40fe3299cb898ecfdb76b95522a38e` |

El agregado pre-sonda se recalculó antes de la implementación y coincidió con `e374e482cc97c66399025c2bbe0776749dcbd8451998edd441bab165c03fd683`. El fingerprint ambiental se reprodujo como `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`.

## 2. Archivos creados y modificado

### Código creado

- `oc3/oc3lib/physical_contract_probe.py`: implementación aislada de autoridades, allowlist, transporte, ledger, parser FITS, extractores gzip/sin compresión, contratos, checksums, outcomes, autorización y ejecución futura.
- `oc3/oc3_probe.py`: CLI `plan`/`run`, offline por defecto.

### Pruebas creadas

- `oc3/tests/test_physical_contract_probe.py`: 94 pruebas sintéticas nuevas.

### Código de prueba modificado

- `oc3/tests/run_tests.py`: el firewall previo a discovery sigue bloqueando `socket.socket`, `create_connection` y `getaddrinfo`; además bloquea `gethostbyname`, `gethostbyname_ex`, `gethostbyaddr`, `getnameinfo` y `getfqdn`, y fija también `VECLIB_MAXIMUM_THREADS=1`.

### Evidencia nueva

- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_SYNTHETIC_TESTS.log`.
- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_SYNTHETIC_TESTS.json`.
- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_REPLAY_RECEIPT.json`.
- este informe.

No se modificaron documentos autoritativos, especificaciones, informes o recibos históricos. No se creó `oc3/provider_contract_probe/`: ese nombre permanece reservado para un futuro intento real autorizado.

## 3. Identidad de implementación

La regla existente `implementation_hash` se aplicó a todos los archivos `*.py` bajo `oc3`, excluyendo `.venv`.

- `PRE_PROBE_IMPLEMENTATION`: `e374e482cc97c66399025c2bbe0776749dcbd8451998edd441bab165c03fd683`
- agregado nuevo: `df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7`

El agregado histórico no fue sobrescrito.

## 4. Arquitectura y separación

La sonda vive en `oc3lib.physical_contract_probe` y no importa `bootstrap`, `provider_schema` ni `selection`. Su flujo futuro es:

```text
autorización PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY validada
→ ledger exclusivo de la sonda
→ transporte inyectable
→ HEAD / Range o GET textual exactos
→ parser de cabeceras FITS sin API de filas
→ evidencia de transporte
→ contrato físico estructural candidato
→ resultado terminal único
```

La evidencia de transporte y el contrato interpretado son dataclasses inmutables distintas. Los tests sintéticos usan únicamente directorios temporales.

## 5. CLI y autorización

`oc3/oc3_probe.py` ofrece `plan` y `run`, con `--offline`, `--dry-run`, `--execute-network`, `--authorization` y `--resume`.

`plan`, `run --offline` y `run --dry-run` verifican autoridades, informan las siete URLs, métodos, cuatro rangos, caps y estados `NOT_STARTED`, sin crear ledger o evidencia. `run` sin capacidad explícita o sin autorización termina en `PROBE_HUMAN_AUTHORIZATION_REQUIRED`.

Una ejecución futura exige un JSON canónico cuyo scope sea `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY` y que ligue la especificación, el agregado nuevo, el fingerprint, recursos, métodos, rangos, caps, directorio/attempt ID, firewall de filas y SHA-256 de la serialización canónica de los argumentos exactos. No se creó ese registro en esta tarea.

## 6. Allowlist y transporte

La allowlist contiene exactamente cuatro FITS y tres manifiestos, con rol y URL literal. Se rechazan esquema HTTP, host/path alternativo, query, fragment, credenciales, puerto no estándar, rango arbitrario y rol no listado. `http.client` no sigue redirects; cualquier estado HEAD distinto de 200 o `final_url` diferente falla.

El transporte se inyecta mediante una interfaz mínima. `OfflineTransport` carece de capacidad de red, `MemoryTransport` sustenta las pruebas y `HTTPProbeTransport` solo puede construirse después de validar autorización. Todas las peticiones usan `Accept-Encoding: identity`.

## 7. Enforcement Range

El motor acepta causalmente solo:

1. `bytes=0-65535`;
2. `bytes=65536-131071`;
3. `bytes=131072-196607`;
4. `bytes=196608-262143`.

Exige `206`, `Content-Range` exacto, total estable, `Content-Length=65536`, representación identity y coherencia con HEAD. `200` o `416` producen `PROBE_RANGE_UNAVAILABLE_STOP` sin leer el cuerpo. Las contradicciones producen `PROBE_TRANSPORT_INTEGRITY_FAILURE`. Se detiene al completar la cabecera o, tras el cuarto fragmento, con `PHYSICAL_CONTRACT_HEADER_CAP_INSUFFICIENT`.

## 8. Parser FITS estructural

El parser propio procesa tarjetas ASCII de 80 bytes, `END` y padding de 2880 bytes. Valida cabecera primaria, `BITPIX`, `NAXISn`, aritmética con overflow cerrado, tamaño estructural del payload, identidad BINTABLE, `NAXIS1/2`, `PCOUNT`, `GCOUNT`, `TFIELDS`, columnas ordenadas, `TFORM` escalares/vectoriales y metadata `TUNIT/TNULL/TSCAL/TZERO`.

`CHECKSUM` y `DATASUM` se registran con `verified=false`. El parser no usa Astropy, no expone método de filas y no contiene una ruta para `FITS_rec`, `hdu.data`, `Table.read`, iteración de filas o celdas.

Si el HDU anterior tiene payload no nulo, se detiene con `INTERVENING_DATA_PAYLOAD_STOP`. No atraviesa ese payload.

## 9. Fronteras gzip y patch list

`GzipHeaderExtractor` comienza en byte comprimido cero, conserva estado incremental y limita cada emisión al siguiente bloque estructural requerido. Cuando termina la cabecera BINTABLE no vuelve a llamar al descompresor. Registra `wire_bytes_received`, `compressed_bytes_consumed` y `uncompressed_header_bytes_emitted`. Una llamada posterior dispara `PROBE_ROW_OBSERVATION_FORBIDDEN`.

Los fragmentos gzip verificados pueden persistirse como bytes comprimidos opacos y reconstruir el estado desde el fragmento cero. Los tests usan canarios inmediatamente después de la cabecera y prueban que no aparecen en la salida no comprimida.

`UncompressedHeaderExtractor` copia solo los bloques necesarios y deja opaco el resto del cuerpo Range. No persiste fragmentos completos de patch list. Los canarios sintéticos no aparecen en parser, contrato, logs, errores o evidencia textual.

## 10. Firewall de filas

`RowObservationTripwire` falla explícitamente para:

- acceso `hdu.data`;
- `Table.read`;
- decode candidato de `ProviderSchemaAdapter`;
- `resolve_bootstrap_bricks`;
- decoder de fila o celda;
- helpers de selección.

Además, el módulo no importa los módulos que implementan bootstrap, adapter o selección. Una emisión gzip posterior a la cabecera se clasifica como violación de observación.

## 11. Manifiestos y checksums

El parser textual acotado exige líneas SHA-256 válidas y una única coincidencia de path exacto. Rechaza ausencia, duplicado, basename ambiguo, formato inválido y discrepancia con los tres hashes documentales mediante `PROVIDER_CHECKSUM_DOCUMENTATION_CONFLICT_STOP`.

La patch list conserva explícitamente `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`; no se sintetiza un checksum de proveedor.

## 12. Contrato físico y `brickid`

`PhysicalContractCandidate` contiene solo identidad de rol/recurso, metadata de transporte seleccionada, cabecera estructural, columnas, estado no verificado de tarjetas checksum, checksum documental y hashes de evidencia. Usa JSON canónico y SHA-256 determinista.

El outcome secundario de `brickid` usa únicamente `TTYPE`/`TFORM`:

- root `J` y regionales `I` → `BRICKID_PHYSICAL_LAYOUT_SUPPORTS_DOCUMENTATION`;
- regional `J` contra expectativa `I` → `BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`;
- campo ausente o ambiguo → `BRICKID_PHYSICAL_LAYOUT_UNRESOLVED`.

No se modifica Amendment 003 ante un conflicto sintético u observado.

## 13. Ledger, límites y reanudación

`ProbeLedger` es SQLite y queda separado del ledger Amendment 002. Su binding incluye specification hash, agregado, fingerprint, authorization hash y attempt ID. Reserva identidad antes del transporte; registra solicitudes, cuerpos FITS/manifiestos, bytes totales, disco/IO, retries y fragmentos.

Los máximos implementados son 1 MiB FITS agregado, 256 KiB/FITS, 8 MiB textual, 9 MiB HTTP, 32 solicitudes, concurrencia 1, un retry adicional, RAM 512 MiB, disco 64 MiB, IO 256 MiB, compute 300 s, wall 900 s, un thread y ninguna GPU. Solo se permiten overrides menores y explícitamente scoped.

Un crash posterior al commit conserva la solicitud y carga conservadoramente todo el cuerpo reservado aún no contabilizado. Un retry exige la misma identidad URL/método/rango/rol/spec. La reanudación gzip relee fragmentos contiguos cuyo tamaño y SHA-256 coinciden; no inicia en un offset comprimido inventado.

## 14. Outcome terminal

Se implementó la precedencia exacta:

1. `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`;
2. `PROBE_TRANSPORT_INTEGRITY_FAILURE`;
3. `PROBE_PROVIDER_DOCUMENTATION_CONFLICT`;
4. `PROBE_RANGE_UNAVAILABLE_STOP`;
5. `PROBE_HEADER_CAP_INSUFFICIENT`;
6. `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`;
7. `PROBE_PHYSICAL_CONTRACTS_RESOLVED`.

Los eventos secundarios se conservan. La integración sintética ejercitó un recorrido resuelto y otro con fallo de transporte, ambos con un terminal único.

## 15. Verificación sintética y regresión

Comando ejecutado localmente:

```bash
oc3/.venv/bin/python -I -B oc3/tests/run_tests.py
```

Resultado final:

- total: 276;
- passed: 276;
- failed: 0;
- skipped: 0;
- pruebas nuevas de sonda: 94;
- regresión previa retenida: 182/182;
- `real_network_requests=0`;
- `synthetic_only=true`.

SHA-256 de evidencia:

| Artefacto | SHA-256 |
|---|---|
| `PHYSICAL_CONTRACT_PROBE_SYNTHETIC_TESTS.log` | `9656523c486a152bf2c33d0f9d6a9b59a32d857afe701af1bd7df646b4fa14af` |
| `PHYSICAL_CONTRACT_PROBE_SYNTHETIC_TESTS.json` | `fe4b85e5a1f6bbbf070ae86455963ef3eb64a7702ddad77a2d8cb17710c8e72c` |

El firewall bloqueó creación de sockets, conexión y las entradas DNS indicadas en §2 antes de importar las pruebas.

## 16. Entorno

Se usó exclusivamente `oc3/.venv/bin/python`:

- Python 3.12.14;
- NumPy 2.5.3;
- Astropy 8.0.1;
- PyArrow 25.0.1.

El fingerprint recalculado permanece `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`. Se verificaron 3668 entradas esperadas y 3668 observadas en el entorno, con 0 faltantes, 0 extras y 0 discrepancias. No se reinstaló ni modificó ningún paquete.

## 17. Recibo de replay

`oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_REPLAY_RECEIPT.json` es JSON canónico, ordenado, compacto, UTF-8, `allow_nan=false` y un LF final.

SHA-256:

`51374b000ca3322cf3de07294d68d224b63f9b0678513775ec69d0a0264b1131`

Liga specification hash, agregado nuevo/anterior, fingerprint, versiones, inventario, 276/276/0/0, hashes de log/resultado, recibo Amendment 003, cero red/DR9/filas/bricks y ambos estados `NOT_STARTED`.

## 18. Ausencia de ejecución real

Esta tarea produjo:

- 0 HEAD reales;
- 0 GET reales;
- 0 Range reales;
- 0 DNS al proveedor;
- 0 bytes DR9;
- 0 FITS reales;
- 0 bytes de manifiestos reales;
- 0 valores de filas proveedor;
- 0 intentos reales de la sonda;
- 0 autorizaciones humanas creadas;
- 0 manifiestos de bootstrap productivos;
- 0 registros de derechos productivos;
- 0 ledgers productivos OC-3;
- 0 bricks reales seleccionados.

Los directorios productivos permanecen vacíos y `oc3/provider_contract_probe/` no existe.

## 19. Bloqueo siguiente

El paso siguiente no es ejecutar red. Se requiere revisión humana de este informe y de la implementación. Solo después puede redactarse una autorización separada `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`, ligada al comando exacto, specification hash `9f86…`, agregado `df8fe7…`, fingerprint `b49e…`, allowlist y caps. Esa autorización no existe todavía.

El estado permanece `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

**OC-3 REMAINS NOT STARTED.**
