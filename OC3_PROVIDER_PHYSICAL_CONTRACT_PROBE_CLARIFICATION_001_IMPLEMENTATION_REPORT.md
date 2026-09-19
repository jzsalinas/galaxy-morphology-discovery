# OC-3 — informe de implementación de Provider Physical Contract Probe Clarification 001

**Fecha:** 2026-09-19  
**Alcance ejecutado:** corrección de implementación y verificación sintética/offline completa.  
**Ejecución real de la sonda:** `NOT_STARTED`.  
**Estado científico:** `OC-3 REMAINS NOT STARTED.`  
**Preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

## 1. Autoridades e identidad histórica verificadas

La integridad se verificó antes de modificar código. No se modificó ninguna de estas autoridades o evidencias históricas.

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
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md` | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_IMPLEMENTATION_REPORT.md` | `f96341567b35d32336640a371fc041f46401c7d4798b985d11366cd12ae68115` |
| `oc3/environment_setup/AMENDMENT_003_REPLAY_RECEIPT.json` | `09c9676e9f7f3b2ce8f063aa63b34fcc7d40fe3299cb898ecfdb76b95522a38e` |
| `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_REPLAY_RECEIPT.json` | `51374b000ca3322cf3de07294d68d224b63f9b0678513775ec69d0a0264b1131` |

El agregado histórico pre-aclaración se preserva como `PRE_CLARIFICATION_001_IMPLEMENTATION = df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7`.

## 2. Archivos modificados y creados

Se modificaron:

- `oc3/oc3lib/physical_contract_probe.py`;
- `oc3/tests/test_physical_contract_probe.py`.

Se crearon:

- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_SYNTHETIC_TESTS.log`;
- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_SYNTHETIC_TESTS.json`;
- `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_REPLAY_RECEIPT.json`;
- este informe.

No se sobrescribieron el informe, log, resultado o recibo de replay históricos de la implementación original.

## 3. Corrección de transporte Range

Las cuatro solicitudes autorizadas conservan literalmente sus rangos inclusivos de 65536 bytes y su orden causal. El motor sigue reservando hasta 65536 bytes antes del transporte, pero ahora valida cada `206` contra la longitud decimal positiva `L` de la representación:

- exige `S < L`;
- calcula `actual_end = min(E, L - 1)`;
- exige `Content-Range: bytes S-actual_end/L` sin wildcard ni sintaxis permisiva;
- exige `Content-Length = actual_end - S + 1`;
- exige que el cuerpo recibido tenga exactamente esa longitud.

Un span corto solo se acepta cuando el rango solicitado alcanza EOF (`L <= E`). Cuando `L > E`, siguen siendo obligatorios el span y cuerpo completos de 65536 bytes. El caso `L = E + 1` se acepta como respuesta completa que termina exactamente en EOF.

La longitud total se restringe a un entero decimal entre 1 y `2^63-1`. Se rechazan total ausente, wildcard, cero, negativo, no decimal, ambiguo u overflow. `L` nunca se infiere de `Content-Length`, del tamaño del cuerpo ni de HEAD por sí solo.

Los estados `200` y `416` para Range siguen produciendo `PROBE_RANGE_UNAVAILABLE_STOP`, sin consumir el cuerpo y sin fallback a GET completo.

## 4. Consistencia de representación y EOF

Cuando HEAD aporta `Content-Length=H`, cada `Content-Range` posterior debe declarar exactamente `L=H`. Los valores `ETag` y `Last-Modified` presentes en HEAD deben reaparecer sin cambios. Una contradicción termina en `PROBE_TRANSPORT_INTEGRITY_FAILURE` y no se mezcla evidencia entre representaciones.

Antes de solicitar un rango, el motor comprueba la cabecera ya completada y la longitud conocida. Si `S >= L`, no crea reserva ni emite la solicitud y registra `PROBE_REPRESENTATION_EOF_BEFORE_HEADER_COMPLETE`. Este evento contribuye a `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`; la precedencia terminal histórica no cambió. Si `S < L`, la siguiente solicitud continúa usando el rango literal completo preautorizado, aunque la respuesta válida pueda terminar antes en EOF.

El extractor gzip permite que un stream gzip válido llegue a EOF sin una cabecera BINTABLE completa para que el motor produzca la misma clasificación estructural no resuelta. Esto no relaja la validación gzip ni permite interpretar payload.

## 5. Longitud corporal y accounting

Se validan de forma independiente el span de `Content-Range`, el header `Content-Length` y los bytes realmente recibidos. Un cuerpo truncado o con al menos un byte adicional produce `PROBE_TRANSPORT_INTEGRITY_FAILURE`. Todos los bytes efectivamente recibidos, incluido el byte extra detectado, se cargan conservadoramente al ledger.

Después de un EOF corto exitoso, el consumo comprometido coincide con los bytes recibidos. La parte no utilizada de la reserva no aumenta caps, no crea crédito transferible y no autoriza otra solicitud. Si el proceso cae después de confirmar la reserva y antes de establecer un consumo seguro, la recuperación sigue cargando la reserva máxima completa.

## 6. Firewalls de filas y gzip

No se modificó el parser FITS ni se añadió ninguna API de filas. En la patch list sin compresión, el transporte puede recibir bytes posteriores al final exacto de la cabecera, pero `UncompressedHeaderExtractor` solo entrega bloques hasta completar la cabecera. Los canarios sintéticos inmediatamente posteriores permanecen fuera de contratos, evidencia estructural, errores y hashes lógicos.

El firewall de salida gzip permanece sin cambios: el descompresor emite como máximo el siguiente bloque estructural requerido, se detiene al completar la cabecera BINTABLE y una llamada posterior sigue generando `PROBE_ROW_OBSERVATION_FORBIDDEN`. Un EOF corto puede contener el stream comprimido completo, pero ningún byte de fila se emite después del límite de cabecera.

## 7. Binding de la aclaración

`RequestIdentity`, `ProbeBinding`, la autorización futura y el plan ligan el SHA-256 de Clarification 001. La verificación de autoridades exige la aclaración exacta. No se creó autorización humana; el cambio únicamente impide que una futura ejecución use una identidad de implementación pre-aclaración.

## 8. Pruebas sintéticas y regresión

Se añadieron 31 pruebas sintéticas. Cubren:

- primer rango completo y EOF corto;
- EOF corto en segundo, tercer y cuarto rango;
- EOF exacto con cuerpo completo;
- rechazo de span corto antes de EOF;
- divergencias entre span, `Content-Length` y cuerpo real;
- consistencia de `Content-Length` de HEAD, `ETag` y `Last-Modified`, incluidos cambios de identidad entre respuestas Range;
- supresión de una solicitud cuyo inicio ya está en EOF;
- conservación del rango literal cuando el inicio está antes de EOF;
- rechazo de wildcard, cero, negativo, no decimal, sintaxis ambigua y overflow;
- EOF antes de completar cabecera, tanto sin compresión como gzip;
- opacidad del canario de patch list y firewall de salida gzip;
- accounting de bytes reales, reserva no reutilizable y recuperación conservadora;
- comportamiento `200`/`416` y precedencia terminal sin cambios;
- binding de la aclaración y agregado histórico.

Comando ejecutado con el firewall de socket/DNS instalado antes de discovery/import:

```bash
oc3/.venv/bin/python -I -B oc3/tests/run_tests.py
```

Resultado final:

- total: 307;
- passed: 307;
- failed: 0;
- skipped: 0;
- regresión previa retenida: 276/276;
- pruebas nuevas: 31/31;
- `real_network_requests=0`;
- `synthetic_only=true`.

| Evidencia nueva | SHA-256 |
|---|---|
| `PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_SYNTHETIC_TESTS.log` | `b5bc73b5b26efada102aeb58811eab0118bb713d66513192037c6248d78ae78f` |
| `PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_SYNTHETIC_TESTS.json` | `083b9bfff68fdffd5c31138e623396dc85920bc6c612066f6b644dae1ed253b2` |

## 9. Identidad de implementación y entorno

La regla existente `implementation_hash` se aplicó a todos los archivos `*.py` bajo `oc3`, excluyendo `.venv`.

- agregado pre-aclaración histórico: `df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7`;
- agregado corregido: `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea`.

Se usó exclusivamente `oc3/.venv/bin/python`:

- Python 3.12.14;
- NumPy 2.5.3;
- Astropy 8.0.1;
- PyArrow 25.0.1.

El fingerprint permanece `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`. No se reinstaló ni modificó ningún paquete.

## 10. Recibo de replay

`oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_REPLAY_RECEIPT.json` usa JSON canónico, claves ordenadas, separadores compactos, UTF-8, `allow_nan=false` y un LF final.

SHA-256 del archivo completo:

`86cd7453087f0a1c90eaa6fd2b9e9d0afad7f872d3988c6bf85b36c3182f3b65`

El recibo liga la especificación, Clarification 001, el agregado corregido e histórico, el fingerprint, versiones, resultado 307/307, regresión 276/276, hashes de log/resultado y el recibo histórico de la sonda. Registra `scientific_execution=NOT_STARTED` y `probe_execution=NOT_STARTED`.

## 11. Ausencia de ejecución real

Esta tarea produjo:

- 0 DNS reales;
- 0 HEAD reales;
- 0 GET reales;
- 0 Range reales;
- 0 bytes DR9;
- 0 FITS reales;
- 0 bytes de manifiestos reales;
- 0 valores de filas del proveedor;
- 0 intentos reales de la sonda;
- 0 autorizaciones humanas;
- 0 manifiestos de bootstrap productivos;
- 0 registros de derechos productivos;
- 0 ledgers productivos OC-3;
- 0 bricks reales seleccionados.

Los directorios productivos permanecen vacíos y `oc3/provider_contract_probe/` permanece ausente.

## 12. Bloqueo siguiente

El estado permanece `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`. El próximo paso es la revisión humana de la implementación corregida, este informe y el recibo. Solo después de esa revisión puede crearse una autorización concreta y separada `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`; esa autorización todavía no existe.

**OC-3 REMAINS NOT STARTED.**
