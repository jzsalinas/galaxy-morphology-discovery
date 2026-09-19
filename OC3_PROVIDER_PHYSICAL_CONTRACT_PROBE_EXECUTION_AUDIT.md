# OC-3 Provider Physical Contract Probe — auditoría local posterior a ejecución

**Intento auditado:** `OC3-PHYSICAL-CONTRACT-PROBE-001`  
**Alcance de esta tarea:** auditoría local y read-only de evidencia persistida.  
**Red durante la auditoría:** 0 solicitudes.  
**Veredicto:** **PROSPECTIVE_CORRECTION_REQUIRED_BEFORE_FREEZE**.  
**Preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades, autorización y binding

| Binding | SHA-256 o valor verificado |
|---|---|
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC_CLARIFICATION_001.md` | `bf26b25d7b979e70d433edd42f12a69a36d59a43705f840bc3d9f1f1e4f7e39a` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_CLARIFICATION_001_IMPLEMENTATION_REPORT.md` | `52d9bb24ab94d602f32afd13989fdd9fb36563ac1014fa2db7e70b02e3390c32` |
| agregado de implementación | `696ba10c110fdd07b78752248910c61febbf5ab1ef2ea6e76c1ac384f92989ea` |
| fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| replay receipt de Clarification 001 | `86cd7453087f0a1c90eaa6fd2b9e9d0afad7f872d3988c6bf85b36c3182f3b65` |
| autorización final | `e9ebef8bae1c78689ae6ca5ffc0eb0dc94d3901f6a785df758a414712fa55757` |

La autorización canónica contiene `authorized=true`, scope `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY`, `attempt_id=OC3-PHYSICAL-CONTRACT-PROBE-001`, `zero_row_observation=true`, el agregado y fingerprint anteriores, y `command_sha256=335d808271d055ffe1e0ea41d8a72185c7ee15fcf3334f29e907a7b9fee8f34f`.

El binding del ledger coincide exactamente con specification, Clarification 001, implementación, entorno, attempt ID y SHA-256 de la autorización. El SQLite pasó `PRAGMA integrity_check=ok` en apertura `mode=ro&immutable=1`.

Los 11 registros de solicitud tienen `retry_of=NULL`, estado `COMPLETE` e identidades distintas. Existe un solo directorio de intento y no hay evidencia persistida de resume, retry ni segunda ejecución. Esta conclusión se limita a la evidencia auditable; no pretende probar eventos externos que no dejen rastro local.

## 2. Inventario inmutable del intento

Se descubrieron 13 archivos. Tamaños y hashes se calcularon sobre los bytes existentes sin modificar el intento.

| Ruta relativa al intento | Bytes | SHA-256 |
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

Los seis JSON del nivel principal y los cuatro JSON HEAD son serializaciones canónicas con un LF final. Los tres prefijos gzip coinciden en tamaño y SHA-256 con la tabla `chunks` del ledger. El chunk de patch list consta en el ledger como 31,680 bytes, SHA-256 `f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6`, pero sus bytes no se persistieron, de acuerdo con el firewall para el producto sin compresión.

## 3. Terminal y eventos

`PROBE_TERMINAL.json` registra:

- `outcome=PROBE_PHYSICAL_CONTRACTS_RESOLVED`;
- `probe_execution=COMPLETE`;
- `scientific_execution=NOT_STARTED`.

Su lista de eventos coincide byte-lógicamente con `PROBE_EVENTS.json`:

1. `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`;
2. `BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`;
3. `PROBE_PHYSICAL_CONTRACTS_RESOLVED`.

El ledger contiene 11 solicitudes completas, los cuatro chunks FITS verificados y contadores coherentes con esos cuerpos. Su tabla `events` está vacía porque la implementación persiste la historia terminal en los JSON anteriores; no existe una contradicción entre eventos JSON, requests, chunks y terminal.

`RESOLVED` significa que se recuperaron cuatro contratos estructurales y tres entradas documentales de checksum dentro del scope de la sonda. No elimina el evento secundario de conflicto documental de `brickid` ni habilita producción.

## 4. Contabilidad real observada

| Contador | Observado | Máximo congelado | Resultado |
|---|---:|---:|---|
| solicitudes HTTP | 11 | 32 | dentro del cap |
| HEAD | 4 | incluido en 32 | dentro del cap |
| GET Range | 4 | incluido en 32 | dentro del cap |
| GET de manifiesto | 3 | incluido en 32 | dentro del cap |
| retries | 0 | 1 adicional por identidad | dentro del cap |
| cuerpos HTTP | 230,130 bytes | 9,437,184 | dentro del cap |
| cuerpos FITS | 228,288 bytes | 1,048,576 | dentro del cap |
| cuerpos de manifiesto | 1,842 bytes | 8,388,608 | dentro del cap |
| disco registrado | 217,918 bytes | 67,108,864 | dentro del cap |
| IO local registrado | 217,918 bytes | 268,435,456 | dentro del cap |

### Cuerpos por recurso

| Rol | HEAD bytes | GET bytes | Total corporal | Cap aplicable |
|---|---:|---:|---:|---:|
| `ROOT_SUMMARY` | 0 | 65,536 | 65,536 | 262,144 FITS/recurso |
| `NORTH_SUMMARY` | 0 | 65,536 | 65,536 | 262,144 FITS/recurso |
| `SOUTH_SUMMARY` | 0 | 65,536 | 65,536 | 262,144 FITS/recurso |
| `SOUTH_PATCH_LIST` | 0 | 31,680 | 31,680 | 262,144 FITS/recurso |
| `ROOT_CHECKSUM_MANIFEST` | no solicitado | 1,270 | 1,270 | 8,388,608 documental agregado |
| `NORTH_CHECKSUM_MANIFEST` | no solicitado | 286 | 286 | 8,388,608 documental agregado |
| `SOUTH_CHECKSUM_MANIFEST` | no solicitado | 286 | 286 | 8,388,608 documental agregado |

Todos los contadores efectivamente persistidos están dentro de sus caps. El ledger no conserva mediciones de compute, wall, RAM, concurrencia máxima observada, threads o GPU; no se infieren valores para esos campos.

## 5. Revisión de transporte por recurso

### FITS

| Rol | Resultado persistido | Content-Length | Content-Type | Accept-Ranges | ETag | Last-Modified | Range y wire bytes | Redirect |
|---|---|---:|---|---|---|---|---|---|
| `ROOT_SUMMARY` | HEAD `COMPLETE`; Range `206` | 13,147,987 | `application/x-gzip` | `bytes` | `"c89f53-5ac51d5ccaf1f"` | `Fri, 07 Aug 2020 23:19:22 GMT` | `bytes=0-65535`; 65,536 | ninguno; URL final exacta |
| `NORTH_SUMMARY` | HEAD `COMPLETE`; Range `206` | 20,882,100 | `application/x-gzip` | `bytes` | `"13ea2b4-5b6277bef4180"` | `Fri, 11 Dec 2020 02:59:42 GMT` | `bytes=0-65535`; 65,536 | ninguno; URL final exacta |
| `SOUTH_SUMMARY` | HEAD `COMPLETE`; Range `206` | 55,399,879 | `application/x-gzip` | `bytes` | `"34d55c7-5b887f52cc140"` | `Sun, 10 Jan 2021 08:55:57 GMT` | `bytes=0-65535`; 65,536 | ninguno; URL final exacta |
| `SOUTH_PATCH_LIST` | HEAD `COMPLETE`; Range `206` EOF corto válido | 31,680 | `application/octet-stream` | `bytes` | `"5ffdf047-7bc0"` | `Tue, 12 Jan 2021 18:53:59 GMT` | petición `bytes=0-65535`; respuesta 31,680 | ninguno; URL final exacta |

Las URLs solicitadas y finales FITS coinciden literalmente con la allowlist. El estado HEAD numérico no fue persistido, aunque el estado de request es `COMPLETE`; el `206` de Range sí está preservado en evidencia de transporte.

### Manifiestos

| Rol | URL preservada | Request | Bytes | Metadata HTTP adicional |
|---|---|---|---:|---|
| `ROOT_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/legacysurvey_dr9.sha256sum` | GET `COMPLETE`, sin Range | 1,270 | no persistida |
| `NORTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/north/legacysurvey_dr9_north.sha256sum` | GET `COMPLETE`, sin Range | 286 | no persistida |
| `SOUTH_CHECKSUM_MANIFEST` | `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/south/legacysurvey_dr9_south.sha256sum` | GET `COMPLETE`, sin Range | 286 | no persistida |

Final URL, status, Content-Length/Type, Accept-Ranges, ETag y Last-Modified de los manifiestos no se conservaron y se marcan como no registrados. La implementación ligada no sigue redirects y solo completa un manifiesto con estado 200 y URL final igual a la literal. No aparece en la evidencia ninguna URL, host, query, mirror, target alternativo o redirect no autorizado.

## 6. Contratos físicos observados

Para las cuatro tablas: HDU objetivo 1, `XTENSION=BINTABLE`, `EXTNAME` ausente, `BITPIX=8`, `NAXIS=2`, `PCOUNT=0`, `GCOUNT=1`, `CHECKSUM` ausente y `DATASUM` ausente. Ninguna tarjeta checksum ausente se presenta como verificada.

En todas las columnas de los cuatro contratos, `TUNIT`, `TNULL`, `TSCAL` y `TZERO` están ausentes. Las listas siguientes conservan orden, case y TFORM exactos.

### `ROOT_SUMMARY`

- compresión: gzip;
- `NAXIS1=70`, `NAXIS2=662174`, `TFIELDS=11`;
- cabecera objetivo: `[2880, 8640)`;
- header SHA-256: `1b339ae87a09ec943d1b3a5bf7ddd89b0d018176a3dbfde5b67aabb65e90f1c1`;
- candidate SHA-256: `84ba119a591bcb89732eb533913782fdaff353a33052375f1366f7807d2d6c9e`;
- evidence refs: transport `5ecbb55ee8f6a6350bfd425afdca4f6b23eb556dd731d23286dec7747b660cb4`, header `1b339ae87a09ec943d1b3a5bf7ddd89b0d018176a3dbfde5b67aabb65e90f1c1`, manifiesto `ff242c611c0f61a09613d93a1215923075ffb84768d74ebd5f78eb3bc366981c`;
- columnas: `1 BRICKNAME/8A`, `2 BRICKID/J`, `3 BRICKQ/I`, `4 BRICKROW/J`, `5 BRICKCOL/J`, `6 RA/D`, `7 DEC/D`, `8 RA1/D`, `9 RA2/D`, `10 DEC1/D`, `11 DEC2/D`.

La reconstrucción local del prefijo gzip produjo exactamente el mismo header hash, 8,640 bytes de cabeceras emitidos y ningún byte posterior a la frontera requerida.

### `NORTH_SUMMARY`

- compresión: gzip;
- `NAXIS1=300`, `NAXIS2=93548`, `TFIELDS=51`;
- cabecera objetivo: `[2880, 14400)`;
- header SHA-256: `4ed9da1bdc60563447731a4ba43611e079cd27def2734774809841b08b959749`;
- candidate SHA-256: `8dc23b47dc995a9aceef5a42794abd3f6b25345f674e36ba856dbddec1f7c597`;
- evidence refs: transport `471f5d83f048ab00c25eb99b9fb5c5ca40cc6e707e251cc9b043b4d4750adf7a`, header `4ed9da1bdc60563447731a4ba43611e079cd27def2734774809841b08b959749`, manifiesto `3638b39c5393f804888467c4c34ff21e2e894d0629c56275f2697dd2ee67febf`;
- columnas: `1 brickname/8A`, `2 ra/D`, `3 dec/D`, `4 nexp_g/I`, `5 nexp_r/I`, `6 nexp_z/I`, `7 nexphist_g/6J`, `8 nexphist_r/6J`, `9 nexphist_z/6J`, `10 nobjs/J`, `11 npsf/J`, `12 nsimp/J`, `13 nrex/J`, `14 nexp/J`, `15 ndev/J`, `16 ncomp/J`, `17 nser/J`, `18 ndup/J`, `19 psfsize_g/E`, `20 psfsize_r/E`, `21 psfsize_z/E`, `22 psfdepth_g/E`, `23 psfdepth_r/E`, `24 psfdepth_z/E`, `25 galdepth_g/E`, `26 galdepth_r/E`, `27 galdepth_z/E`, `28 ebv/E`, `29 trans_g/E`, `30 trans_r/E`, `31 trans_z/E`, `32 cosky_g/E`, `33 cosky_r/E`, `34 cosky_z/E`, `35 ext_g/E`, `36 ext_r/E`, `37 ext_z/E`, `38 wise_nobs/4I`, `39 trans_wise/4E`, `40 ext_w1/E`, `41 ext_w2/E`, `42 ext_w3/E`, `43 ext_w4/E`, `44 brickid/J`, `45 ra1/D`, `46 ra2/D`, `47 dec1/D`, `48 dec2/D`, `49 area/D`, `50 survey_primary/L`, `51 in_desi/L`.

La reconstrucción local produjo el mismo header hash, 14,400 bytes de cabeceras emitidos y ningún byte posterior.

### `SOUTH_SUMMARY`

- compresión: gzip;
- `NAXIS1=300`, `NAXIS2=253658`, `TFIELDS=51`;
- cabecera objetivo: `[2880, 14400)`;
- header SHA-256: `8fe8ecf7191f7b6eeebcb613e34b56776b27d4c14193669eb1fbc205ae1e8d7f`;
- candidate SHA-256: `a18f93063fd73529860c6d4e8acb27a3e792e0f059c07a42eed51b9acc52bd7c`;
- evidence refs: transport `80bc51efd72c970cf9cb9d1ab1651ab3dc22f61f1d2bb8db0cd337686976599f`, header `8fe8ecf7191f7b6eeebcb613e34b56776b27d4c14193669eb1fbc205ae1e8d7f`, manifiesto `3fbf38cc8562aab2451e59d95d6b2840e0142509288ce2d393f2b696a757d8a3`;
- columnas: idénticas en orden, case, TFORM y metadata ausente a las 51 columnas enumeradas para `NORTH_SUMMARY`.

La reconstrucción local produjo el mismo header hash, 14,400 bytes de cabeceras emitidos y ningún byte posterior.

### `SOUTH_PATCH_LIST`

- compresión: identity;
- `NAXIS1=14`, `NAXIS2=1691`, `TFIELDS=3`;
- cabecera objetivo: `[2880, 5760)`;
- header SHA-256: `f1e338aa4e2c8211f7a01d05e7ede15d91628c291bba1e35d30931a0ceb0b112`;
- candidate SHA-256: `8216278b05e16134f6853f3dfbf3a5c77c347420b9b62eb9aac2abbe68cbb821`;
- evidence refs: transport `11bb4fec9953ba3c11c52b58087aaa737ed0f8f9f5854a036f3c44986e1a3720`, header `f1e338aa4e2c8211f7a01d05e7ede15d91628c291bba1e35d30931a0ceb0b112`;
- columnas: `1 RELEASE/I`, `2 BRICKID/J`, `3 BRICKNAME/8A`.

`NAXIS2=1691` coincide con la cardinalidad documental únicamente como comprobación de header; no se inspeccionó ninguna membresía. El layout hace prospectivamente especificable una clave candidata de membership: `BRICKNAME`, TFORM `8A`, columna 3, porque el header demuestra esa identidad estructural y Amendment 003 usa `brickname` como join exacto root↔regional. Esto no valida padding de valores, unicidad, nulls, contenido, relación con `BRICKID` ni membresía real.

El parser permanece deshabilitado. No hay checksum de proveedor aplicable a la patch list y el estado exacto se conserva como `PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND`; el hash del prefijo no lo sustituye.

## 7. Comparación documental

### Root

| Expectativa documental | Observación | Clasificación |
|---|---|---|
| 11 nombres, case y orden root | coincidencia exacta | `MATCH` |
| `char[8]` para `BRICKNAME` | `8A` | `MATCH` |
| `int32` para `BRICKID`, `BRICKROW`, `BRICKCOL` | `J` | `MATCH` |
| `int16` para `BRICKQ` | `I` | `MATCH` |
| `float64` para `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, `DEC2` | `D` | `MATCH` |
| HDU, NAXIS, TFORM exacto, unidades, null/scaling y filas | no estaban fijados como expectativa previa; ahora observados | `NOT_APPLICABLE` a comparación previa |
| padding/decodificación de valores string | no se leyeron celdas | `UNRESOLVED` |

### North y south

Ambas ramas exhiben el mismo inventario físico de 51 columnas. No hay nombres extra o ausentes respecto del inventario exhaustivo de Amendment 003 y el case observado coincide.

| Expectativa documental | Observación | Clasificación |
|---|---|---|
| inventario exhaustivo y case de 51 campos | coincidencia exacta | `MATCH` |
| `brickname char[8]` | `8A` | `MATCH` |
| `ra`, `dec` float64 | `D` | `MATCH` |
| `nexp_g/r/z` int16 | `I` | `MATCH` |
| `nexphist_g/r/z` int32[6] | `6J` | `MATCH` |
| `brickid` int16 | `J` = int32 | `DOCUMENTARY_CORRECTION_REQUIRED` |
| `nobjs`, `npsf`, `nsimp`, `nrex`, `nexp`, `ndev`, `ncomp`, `nser`, `ndup` int16 | todos `J` = int32 | `DOCUMENTARY_CORRECTION_REQUIRED` |
| `ra1`, `ra2`, `dec1`, `dec2`, `area` float32 | todos `D` = float64 | `DOCUMENTARY_CORRECTION_REQUIRED` |
| PSF/depth/extinction/transmission/sky escalares float32 | `E` | `MATCH` |
| `wise_nobs` int16[4] | `4I` | `MATCH` |
| `trans_wise` float32[4] | `4E` | `MATCH` |
| `survey_primary`, `in_desi` boolean | `L` | `MATCH` |
| TUNIT/TNULL/TSCAL/TZERO y orden físico | no estaban fijados como expectativas binarias; ahora se observa ausencia y orden | `NOT_APPLICABLE` a comparación previa |
| padding/decodificación de `brickname` | no se leyeron celdas | `UNRESOLVED` |

Las 15 discrepancias de tipo son simétricas en north y south. Los bytes observados no modifican Amendment 003: requieren una corrección prospectiva revisada antes de congelar contratos de producción.

### Patch list

| Expectativa documental | Observación | Clasificación |
|---|---|---|
| URL HTTPS congelada por Amendment 003 | solicitada/final exacta | `MATCH` |
| cardinalidad conceptual 1,691 | `NAXIS2=1691` | `MATCH` como header solamente |
| HDU/layout/columnas/clave | previamente no definidos; ahora observados | `NOT_APPLICABLE` a expectativa previa; aptos para especificación prospectiva |
| checksum proveedor | no encontrado | `UNRESOLVED` |
| membership y valores `RELEASE=9012` | no se leyeron filas | `UNRESOLVED` |

## 8. Resultado `brickid`

| Rol | TTYPE observado | TFORM observado |
|---|---|---|
| ROOT | `BRICKID` | `J` |
| NORTH | `brickid` | `J` |
| SOUTH | `brickid` | `J` |

El resultado secundario persistido exacto es:

`BRICKID_PHYSICAL_LAYOUT_CONFLICTS_WITH_DOCUMENTATION`

Root coincide con `int32`. North y south contradicen la expectativa regional congelada `int16`; ambos son físicamente `J`/int32. Esto también hace coherente, a nivel conceptual, la capacidad de representar el rango global documentado `[1, 662174]`, pero no explica por qué la documentación regional decía `int16`. La causa sigue sin resolverse y no se adivina. Tampoco se inspeccionó ningún valor `brickid`.

## 9. Manifiestos de checksum

| Rol | Entrada exacta | SHA-256 del proveedor observado | Expectativa documental | Resultado |
|---|---|---|---|---|
| ROOT | `survey-bricks.fits.gz` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` | mismo valor | `MATCH` |
| NORTH | `survey-bricks-dr9-north.fits.gz` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` | mismo valor | `MATCH` |
| SOUTH | `survey-bricks-dr9-south.fits.gz` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` | mismo valor | `MATCH` |

Los SHA-256 locales registrados para los cuerpos de manifiesto son, respectivamente, `ff242c611c0f61a09613d93a1215923075ffb84768d74ebd5f78eb3bc366981c`, `3638b39c5393f804888467c4c34ff21e2e894d0629c56275f2697dd2ee67febf` y `3fbf38cc8562aab2451e59d95d6b2840e0142509288ce2d393f2b696a757d8a3`. Los cuerpos crudos no quedaron persistidos, por lo que esos tres hashes se auditan como valores registrados, no se recalculan aquí.

Un checksum del proveedor observado en su manifiesto no equivale a un checksum FITS completo verificado localmente. La sonda solo adquirió prefijos acotados de las tres representaciones gzip; no verificó localmente los archivos completos contra esos hashes.

## 10. Auditoría del firewall de filas

La evidencia persistida ofrece comprobaciones independientes del terminal:

- cada extractor gzip registra exactamente 8,640 o 14,400 bytes de cabeceras emitidos, iguales a la frontera de header correspondiente;
- la reconstrucción local de los tres prefijos reproduce contratos y header hashes sin emitir bytes posteriores;
- patch list registra 5,760 bytes de cabecera emitidos aunque el transporte recibió 31,680 bytes; el resto no aparece en el contrato;
- `PROBE_EVENTS.json` no contiene `PROBE_ROW_OBSERVATION_FORBIDDEN` ni `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE`;
- los candidatos persistidos contienen metadata estructural y hashes, sin arrays de filas/celdas;
- no existen artefactos de DTO, `ProviderSchemaAdapter`, bootstrap, resolución de bricks o selección.

No hay un contador explícito llamado “rows observed”. Por ello la conclusión precisa es: **no existe evidencia persistida de observación de filas y las fronteras de emisión demuestran cero bytes descomprimidos post-header en las rutas gzip**. No se ejecutó Astropy, `Table.read`, `hdu.data`, `FITS_rec`, decode candidato, `resolve_bootstrap_bricks` ni selección durante esta auditoría.

Resultado del audit de filas: **PASS — no violation observed, header-boundary evidence consistent**.

`PROBE_PHYSICAL_CONTRACT_CANDIDATES.json` nombra candidatos de contrato físico; no contiene candidatos astronómicos derivados de filas.

## 11. Aislamiento de salidas

Los directorios `oc3/INPUTS`, `oc3/provenance`, `oc3/RAW_IMMUTABLE`, `oc3/TECHNICAL_INDEX` y `oc3/reports` contienen cero archivos. No se encontró ledger Amendment 002 ni otro SQLite fuera del área autorizada. Los únicos productos del intento están bajo `oc3/provider_contract_probe/OC3-PHYSICAL-CONTRACT-PROBE-001`; la autorización final preexistente permanece en `oc3/PROVIDER_PHYSICAL_CONTRACT_PROBE_AUTHORIZATION_001.json`.

No se creó manifiesto bootstrap, rights record, contrato físico de producción, DTO candidato ni selección real.

## 12. Alcance probatorio

### OBSERVED

- transporte real acotado de siete recursos autorizados;
- metadata HEAD preservada para cuatro FITS;
- cuatro respuestas Range y sus bytes contabilizados;
- cabeceras BINTABLE y contratos físicos de cuatro roles;
- tres entradas textuales exactas de manifiestos oficiales;
- evento de conflicto físico-documental para `brickid`;
- ausencia de evento de violación de filas y fronteras de emisión de cabecera.

### DOCUMENTED

- esquemas lógicos root/regionales de `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md` y Amendment 003;
- checksums esperados root/north/south;
- cardinalidad conceptual 1,691 y propósito 9012 de la patch list;
- semántica futura de joins, cobertura y generaciones.

### INFERRED

La evidencia basta para redactar prospectivamente contratos físicos revisables para los cuatro roles. Antes de congelarlos debe corregirse prospectivamente la documentación regional para las 15 diferencias de tipo observadas y decidir el contrato exacto que reemplaza las expectativas incompatibles. La patch list permite proponer `BRICKNAME/8A` como clave estructural futura, pero no permite habilitar el parser sin checksum/full-byte binding y reglas de valores, unicidad, nulls y padding.

No se observó contenido de filas, membresía, cobertura g/r/z, morfología, idoneidad científica, joins o bricks candidatos. `PROBE_PHYSICAL_CONTRACTS_RESOLVED` no afirma ninguno de esos hechos.

## 13. Veredicto y estado

El intento es válido e internamente consistente: autoridades, autorización, command binding, ledger, contadores, transporte, contratos y manifiestos concuerdan; no hay violación de filas ni salida fuera del área permitida. No corresponde `PROBE_POST_EXECUTION_INTEGRITY_FAILURE_STOP`.

No corresponde todavía `PHYSICAL_CONTRACT_EVIDENCE_READY_FOR_PROSPECTIVE_FREEZE`, porque Amendment 003 contiene expectativas regionales que contradicen de forma material los TFORM observados. Debe elaborarse y revisarse una corrección prospectiva antes de congelar contratos físicos de producción.

Veredicto único:

**PROSPECTIVE_CORRECTION_REQUIRED_BEFORE_FREEZE**

El estado permanece **PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**. No se asigna metadata-bootstrap READY, no se habilita `ProviderSchemaAdapter`, no se habilita el parser de patch list y no se crea un contrato físico de producción.

**DO NOT RE-RUN OR RESUME THE PROBE.**

**OC-3 REMAINS NOT STARTED.**
