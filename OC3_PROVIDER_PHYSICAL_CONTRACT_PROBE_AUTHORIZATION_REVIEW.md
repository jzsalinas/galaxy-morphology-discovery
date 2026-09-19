# OC-3 Provider Physical Contract Probe — revisión del candidato de autorización 001

**THE CANDIDATE IS NOT AN AUTHORIZATION.**

**DO NOT RUN THE NETWORK COMMAND YET.**

El archivo [candidato](oc3/provider_contract_probe_authorization_candidate.json) contiene `authorized=false`, `status="HUMAN_REVIEW_REQUIRED"` y campos de aprobación humana nulos. La ruta real de ejecución lo rechaza con `PROBE_HUMAN_AUTHORIZATION_REQUIRED`. Este documento tampoco autoriza la ejecución: presenta exactamente el alcance, el comando y los límites que el humano debe revisar antes de una decisión separada.

## 1. Identidad congelada

| Binding | Valor verificado |
|---|---|
| Probe specification | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| Clarification 001 | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| Informe de implementación de Clarification 001 | `52d9bb24ab94d602f32afd13989fdd9fb36563ac1014fa2db7e70b02e3390c32` |
| Agregado de implementación | `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea` |
| Fingerprint del entorno | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Recibo de replay de Clarification 001 | `86cd7453087f0a1c90eaa6fd2b9e9d0afad7f872d3988c6bf85b36c3182f3b65` |
| Candidato de autorización | `0deea6953200c51caf70e4a2962b82bb5f79f1bae3f232b11d7299d41a9d382b` |

La verificación sintética vigente es 307 passed, 0 failed y 0 skipped, con `real_network_requests=0`.

El intento propuesto queda fijado como:

- `attempt_id`: `OC3-PHYSICAL-CONTRACT-PROBE-001`;
- directorio futuro: `oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001`;
- scope: `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`;
- archivo futuro de autorización final: `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json`.

El directorio de intento y el archivo final de autorización no existen todavía.

## 2. Actividad de red que se propone autorizar

La autorización futura permitiría exclusivamente una sonda física acotada de siete recursos literales. Para los cuatro FITS permitiría `HEAD` y `GET` con uno de cuatro rangos fijos, emitidos en orden causal. Para los tres manifiestos permitiría `HEAD` y un GET textual acotado por el presupuesto documental. Cada solicitud usa `Accept-Encoding: identity`.

No se permiten cookies, autenticación, query strings, headers arbitrarios, redirects, targets alternativos, mirrors, descubrimiento de URLs ni fallback de proveedor. La URL final debe coincidir con la URL literal autorizada.

### Recursos exactos

| Rol | Recurso literal | Operación permitida |
|---|---|---|
| `ROOT_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | HEAD; GET Range FITS |
| `NORTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | HEAD; GET Range FITS |
| `SOUTH_SUMMARY` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | HEAD; GET Range FITS |
| `SOUTH_PATCH_LIST` | `https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits` | HEAD; GET Range FITS |
| `ROOT_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/legacysurvey_dr9.sha256sum` | HEAD; GET textual acotado |
| `NORTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/legacysurvey_dr9_north.sha256sum` | HEAD; GET textual acotado |
| `SOUTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/legacysurvey_dr9_south.sha256sum` | HEAD; GET textual acotado |

Los únicos hosts permitidos serían `portal.nersc.gov` y `www.legacysurvey.org` mediante las URLs literales anteriores.

### Rangos FITS exactos

1. `bytes=0-65535`
2. `bytes=65536-131071`
3. `bytes=131072-196607`
4. `bytes=196608-262143`

No se autoriza GET FITS irrestricto. El motor deja de emitir rangos cuando completa la cabecera BINTABLE requerida o cuando la longitud conocida hace que el inicio `S` del siguiente rango satisfaga `S >= L`.

Clarification 001 permite que la respuesta al rango literal sea más corta únicamente cuando el rango alcanza el EOF demostrado de la representación. La petición no se acorta. `Content-Range`, `Content-Length`, longitud corporal, longitud total e identidad de representación deben concordar. El ahorro por EOF no se convierte en crédito reutilizable.

## 3. Actividad expresamente fuera de alcance

La autorización propuesta no cubriría:

- `METADATA_BOOTSTRAP_ONLY`;
- ejecución científica OC-3;
- selección de bricks;
- observación o iteración de filas o celdas;
- descarga FITS completa;
- imágenes coadd o productos PSF;
- catálogos o Tractor;
- Galaxy Zoo o DR9sv;
- mirrors, descubrimiento de URL o fallback de proveedor.

No autoriza bootstrap, manifiesto productivo, registro de derechos, ledger científico Amendment 002, construcción de candidatos científicos ni selección de cobertura.

## 4. Exposición máxima

| Recurso | Máximo |
|---|---:|
| Cuerpos FITS totales | 1,048,576 bytes |
| FITS por recurso | 262,144 bytes |
| Cuerpos documentales/manifiestos | 8,388,608 bytes |
| Cuerpos HTTP totales | 9,437,184 bytes |
| Solicitudes HTTP | 32 |
| Concurrencia | 1 |
| Retry | 1 intento adicional por identidad exacta |
| RAM | 536,870,912 bytes |
| Disco | 67,108,864 bytes |
| IO local | 268,435,456 bytes |
| Compute activo | 300 segundos |
| Wall | 900 segundos |
| Threads | 1 |
| GPU | ninguna (`0`) |

La ejecución puede detenerse por debajo de estos máximos y nunca puede aumentarlos.

## 5. Firewall de observación de filas

El binding exige `ZERO_PROVIDER_ROW_OBSERVATION=true`. Quedan prohibidos `hdu.data`, `Table.read`, `FITS_rec`, iteración de filas o celdas, decode candidato de `ProviderSchemaAdapter`, `resolve_bootstrap_bricks`, helpers de selección, construcción de candidatos, selección de cobertura, logging de filas y cualquier salida descomprimida posterior a la cabecera BINTABLE.

Cualquier violación produce `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`. Un intento comprometido no se reanuda automáticamente.

## 6. Aislamiento de salida

Una ejecución futura solo podría escribir bajo:

`oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001`

No puede escribir en `oc3/INPUTS`, `oc3/provenance`, `oc3/RAW_IMMUTABLE`, `oc3/TECHNICAL_INDEX` u `oc3/reports`, ni crear o actualizar el ledger científico OC-3 de Amendment 002.

## 7. Comando futuro exacto

El directorio de trabajo requerido es:

`/home/jzsalinas/Documents/galaxy-morphology-discovery`

El array argv completo y autoritativo es:

```json
["oc3/.venv/bin/python","oc3/oc3_probe.py","run","--project","/home/jzsalinas/Documents/galaxy-morphology-discovery","--execute-network","--authorization","oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json"]
```

Su `command_argv_sha256` es:

`16222b83e046f0a1d82065a8dc627e3c09f204cac83006bd7825aaf5584a93a2`

La regla es SHA-256 de la serialización JSON canónica UTF-8 del array, con separadores compactos, `ensure_ascii=false`, `allow_nan=false` y sin LF final. El orden del array es significativo.

Render POSIX para revisión visual:

```bash
oc3/.venv/bin/python oc3/oc3_probe.py run --project /home/jzsalinas/Documents/galaxy-morphology-discovery --execute-network --authorization oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json
```

**DO NOT RUN THE NETWORK COMMAND YET.**

La CLI liga internamente los argumentos posteriores al script mediante el hash `335d808271d055ffe1e0ea41d8a72185c7ee15fcf3334f29e907a7b9fee8f34f`. Ese hash se calcula sobre JSON canónico de `{"argv": runtime_cli_argv}` más un LF y figura como `command_sha256` en la proyección runtime del candidato. El `attempt_id` y el directorio se toman del futuro archivo final, pues la CLI no ofrece argumentos separados para ellos.

## 8. Outcomes terminales

La precedencia congelada es:

1. `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`;
2. `PROBE_TRANSPORT_INTEGRITY_FAILURE`;
3. `PROBE_PROVIDER_DOCUMENTATION_CONFLICT`;
4. `PROBE_RANGE_UNAVAILABLE_STOP`;
5. `PROBE_HEADER_CAP_INSUFFICIENT`;
6. `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`;
7. `PROBE_PHYSICAL_CONTRACTS_RESOLVED`.

Una salida negativa o parcial es un resultado válido de la sonda y no autoriza ampliar alcance, usar otro proveedor o iniciar OC-3.

## 9. Validación local del candidato

La forma canónica, los bindings, las siete URLs, los cuatro rangos, caps, hashes de comando y estado no autorizado se validaron localmente. También se invocó la ruta `run` con `--execute-network` y el candidato mientras sockets, DNS y el constructor del transporte real estaban bloqueados. El resultado fue:

```text
PROBE_HUMAN_AUTHORIZATION_REQUIRED
real_transport_constructed=false
real_network_requests=0
```

No se creó el directorio de intento, un ledger, la autorización final ni ningún artefacto productivo.

## 10. Cómo aprobar en un paso posterior

El humano debe revisar el candidato completo, este documento, las siete URLs, los caps, ambos hashes de comando y el agregado de implementación. Si decide autorizar, debe enviar en un mensaje posterior la declaración exacta incluida abajo. Ese paso separado permitirá preparar el archivo final con el conjunto exacto de campos aceptado por `load_authorization`, `authorized=true` y sin campos del envoltorio de revisión.

La declaración propuesta para el paso posterior es:

> I authorize OC3-PHYSICAL-CONTRACT-PROBE-001 under scope PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY exactly as bound by candidate file SHA-256 0deea6953200c51caf70e4a2962b82bb5f79f1bae3f232b11d7299d41a9d382b and command argv SHA-256 16222b83e046f0a1d82065a8dc627e3c09f204cac83006bd7825aaf5584a93a2.

La presencia de ese texto aquí es únicamente material de revisión y no constituye aprobación.

**AWAITING HUMAN AUTHORIZATION**

**OC-3 REMAINS NOT STARTED.**
