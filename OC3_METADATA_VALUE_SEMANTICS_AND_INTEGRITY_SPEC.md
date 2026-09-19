# OC-3 — especificación prospectiva de semántica de valores e integridad de metadata

**Fecha:** 2026-09-19  
**Naturaleza:** especificación documental prospectiva anterior a toda observación de filas reales.  
**Estado de preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Metadata bootstrap:** `NOT_STARTED`.  
**Production decode:** `false`.  
**Ejecución científica:** `NOT_STARTED`.

## 1. Autoridades y estado verificados

Esta especificación se creó después de verificar localmente:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_PROVIDER_SCHEMA_CORRECTION_AMENDMENT_004.md` | `842d7b62e3a5408c88d534b3e531a6e2d85a4eb66593f2b0c9bf91bb7fe3fe48` |
| `OC3_DR9_PROVIDER_PHYSICAL_CONTRACTS.md` | `bdf38d98866de8a7a9ee1c4e495dafea9492e8fc2980edf307b5fb6951040e6b` |
| `OC3_POST_PROBE_001_REGRESSION_STATE_CLARIFICATION_001.md` | `930909ebdfffff58bc0c88cbbab9c619128cb4ab7adb8df9ec6a88e82324e155` |
| `OC3_AMENDMENT_004_PHYSICAL_CONTRACTS_IMPLEMENTATION_REPORT.md` | `63268d6e9637083d76eaf5ddf47faa8790f96a507d4f84b3ee8373055408bdad` |
| `oc3/environment_setup/AMENDMENT_004_PHYSICAL_CONTRACTS_REPLAY_RECEIPT.json` | `4b05cef13e0e6af785784c2c6e7da1e1d88887f4f29d42dcb95dc6ca49c75e5b` |

También se verificaron:

| Binding | Valor |
|---|---|
| Agregado de implementación | `034f2a9dc39960e4b89f0abc01ea3c2c91a913f9631fe4f3eb8e3b955d652880` |
| Fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| Regresión canónica | 330 total, 330 passed, 0 failed, 0 skipped |
| Red real durante replay | 0 solicitudes |
| Evidencia Probe 001 | 13/13 paths, tamaños y SHA-256 exactos |

Una divergencia habría producido `VALUE_SEMANTICS_INTEGRITY_SPEC_AUTHORITY_FAILURE` e impedido crear este documento. No se observó ninguna.

## 2. Propósito y separaciones normativas

Esta especificación congela, antes de observar una celda real:

1. semántica exacta de decodificación de identificadores técnicos;
2. igualdad exacta para joins y membership;
3. requisitos semánticos completos de `SOUTH_PATCH_LIST`;
4. requisitos de integridad completa para root, north y south;
5. un modelo de integridad separado y ligado a una adquisición futura para la patch list, cuyo proveedor no publica un SHA-256 conocido.

Se preservan cuatro conceptos independientes:

```text
representación física
!= semántica de valores
!= integridad del archivo
!= elegibilidad para selección
```

Que un archivo cumpla el contrato físico no prueba que sus valores cumplan esta especificación. Que sus bytes pasen integridad no valida su semántica. Que sus filas pasen semántica y joins tampoco autoriza selección hasta superar todos los gates y bindings restantes.

## 3. Hechos externos suministrados y referencias

Los siguientes hechos fueron revisados previamente por la persona responsable y se registran aquí de forma prospectiva. Esta tarea no consultó fuentes externas.

| ID | Hecho documental suministrado | Referencia humana registrada |
|---|---|---|
| `EXT-FITS-A` | En una tabla binaria FITS, `TFORM=A` representa caracteres del conjunto de texto ASCII restringido; un NUL ASCII puede terminar el texto antes del repeat count y los bytes posteriores al primer NUL quedan indefinidos. | NASA/IAU FITS Standard, sección de binary tables y campos character `A`. |
| `EXT-LS-BRICKNAME` | Los nombres de bricks de Legacy Surveys tienen exactamente ocho caracteres, con forma como `1126p222`: cuatro dígitos, `p` o `m` minúscula y tres dígitos. | Legacy Surveys brick-name documentation. |
| `EXT-LS-DR9-9012` | En DR9, 1691 bricks south afectados fueron rerun y recibieron `RELEASE=9012`, en lugar del release south ordinario `9010`. | Legacy Surveys DR9 Known Issues, sección Burst Buffer. |

Estos hechos documentales no sustituyen verificación de bytes, contrato físico, integridad, cardinalidad ni joins. Una futura contradicción observada debe fallar cerrado y registrarse; no permite adaptar retrospectivamente estas reglas.

## 4. `OC3_BRICKNAME_SEMANTICS_V1`

### 4.1 Entrada exacta

La entrada es una secuencia de exactamente 8 bytes procedente de un campo cuya representación física ya fue validada como `TFORM=8A`. La producción no puede delegar la aceptación a strip, normalización o replacement decoding genéricos de una biblioteca.

### 4.2 Predicado de validez

Una entrada es válida únicamente si cumple todas estas condiciones:

1. hay exactamente 8 bytes disponibles;
2. cada byte pertenece a ASCII;
3. ningún byte es NUL (`0x00`);
4. ningún byte es espacio (`0x20`);
5. no se admite padding inicial ni final;
6. bytes 0–3 son dígitos ASCII `0`–`9`;
7. byte 4 es exactamente `p` (`0x70`) o `m` (`0x6d`) minúscula;
8. bytes 5–7 son dígitos ASCII `0`–`9`.

Patrón estructural equivalente sobre los ocho bytes:

```text
^[0-9]{4}[pm][0-9]{3}$
```

Se rechazan NUL-terminated strings cortos, padding por espacios, `P` o `M` mayúscula, non-ASCII, replacement characters, input previamente trimmed y toda longitud diferente de 8.

Prohibiciones explícitas:

- ningún `strip()`;
- ningún `rstrip()`;
- ningún case folding;
- ninguna normalización Unicode;
- ninguna decodificación con reemplazo o pérdida.

Después de validar los ocho bytes, el valor lógico canónico es el string ASCII exacto de ocho caracteres. La decodificación ocurre después de validar bytes y debe ser estricta.

## 5. Igualdad de joins y membership

Dos brick names son iguales si y solo si sus ocho bytes canónicos validados son exactamente iguales byte por byte.

No se permite comparación fuzzy, normalización de case, normalización de whitespace, fallback derivado de coordenadas, fallback por `BRICKID`, alias ni coerción. Root, north, south y patch list usan la misma `OC3_BRICKNAME_SEMANTICS_V1`.

## 6. Reglas de valores root y regionales

Antes de toda adquisición real se congelan estas reglas mínimas:

| Campo | Semántica congelada |
|---|---|
| `brickname` | `OC3_BRICKNAME_SEMANTICS_V1` |
| `brickid` | decode signed FITS `J` / `int32`; futuros rangos semánticos requieren especificación separada |
| `ra`, `dec`, primary bounds | valores finitos donde Amendment 003 ya los exige |
| `nexp_g`, `nexp_r`, `nexp_z` | `GRZ_MEDIAN_PRESENT_V1` sin cambio |
| `survey_primary` | semántica lógica exacta ya congelada |

No se añade ningún criterio de morfología, conveniencia, profundidad, calidad visual o elegibilidad. Esta especificación no modifica el selector.

## 7. Semántica de cada fila `SOUTH_PATCH_LIST`

Toda fila futura debe cumplir conjuntamente:

| Campo | Regla |
|---|---|
| `RELEASE` | integer exacto `9012` |
| `BRICKID` | decode válido `J` / `int32` signed |
| `BRICKNAME` | `OC3_BRICKNAME_SEMANTICS_V1` |

Una sola fila inválida hace fallar cerrada la validación semántica de la patch list completa. No se elimina, limpia o convierte una fila inválida en “no miembro”. Ningún subconjunto de filas puede adquirir autoridad de membership mientras falle el conjunto.

## 8. Cardinalidad de patch list

El contrato físico exige `NAXIS2=1691`. La validación semántica futura debe requerir además exactamente 1691 filas decodificadas y 1691 filas semánticamente válidas.

No se infiere la cardinalidad de membership desde prefijos, muestras o subsets. Valores 1690 o 1692 fallan cerrados.

## 9. Unicidad de patch list

Sobre las 1691 filas completas se requieren simultáneamente:

- `BRICKNAME` único;
- `BRICKID` único;
- par `(BRICKID, BRICKNAME)` único.

Cualquier duplicado invalida el producto completo. No se deduplica, elige first/last ni combina automáticamente.

## 10. Consistencia cruzada y joins exactos

No se afirma que `BRICKID` y `BRICKNAME` sean mutuamente derivables. El metadata bootstrap futuro debe verificar:

1. cada patch `BRICKNAME` une exactamente una fila root;
2. el patch `BRICKID` es exactamente igual al `BRICKID` de esa fila root;
3. el mismo `BRICKNAME` une exactamente una fila `SOUTH_SUMMARY`;
4. el `brickid` south es exactamente igual al `BRICKID` root/patch.

Un join con cero matches, múltiples matches o identidad discrepante falla cerrado. No hay fuzzy joins, reemplazo, fallback ni búsqueda por proximidad.

## 11. Integridad completa root, north y south

Se congelan estos SHA-256 esperados publicados por el proveedor:

| Rol | `EXPECTED_PROVIDER_FULL_FILE_SHA256` |
|---|---|
| `ROOT_SUMMARY` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| `NORTH_SUMMARY` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| `SOUTH_SUMMARY` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

Una adquisición futura autorizada debe, en este orden:

1. adquirir el recurso exacto completo;
2. calcular localmente SHA-256 sobre todos los bytes exactos adquiridos;
3. comparar con el digest esperado del proveedor;
4. fallar cerrado antes del decode de filas ante cualquier diferencia.

Solo la igualdad completa para la identidad inmutable adquirida puede hacer elegible una consideración posterior de `FULL_FILE_INTEGRITY_BOUND=true`. Un hash de prefijo, Range parcial, cabecera descomprimida, candidato físico, `ETag` o `Content-Length` no satisface esta condición.

## 12. Modelo de integridad de `SOUTH_PATCH_LIST`

Se preservan permanentemente:

```text
PROVIDER_PUBLISHED_SHA256 = ABSENT
PATCH_LIST_PROVIDER_CHECKSUM_NOT_FOUND
```

Un hash local nunca puede etiquetarse como provider-published. Se define una clase separada:

```text
ACQUISITION_BOUND_LOCAL_SHA256
```

Solo una adquisición futura, completa y autorizada por separado de la URL oficial exacta puede crear ese valor. Antes de transferir se deben ligar:

- URL HTTPS literal exacta;
- política de no redirects;
- rol exacto `SOUTH_PATCH_LIST`;
- hash del contrato físico congelado;
- metadata de representación esperada de Probe 001;
- hash de la autorización;
- agregado de implementación;
- fingerprint ambiental;
- límites máximos de bytes y solicitudes.

## 13. Continuidad de representación de patch list

La adquisición completa futura solo puede continuar si la representación live coincide con la identidad previamente auditada, salvo revisión prospectiva anterior a la transferencia:

| Propiedad | Valor esperado de Probe 001 |
|---|---|
| `Content-Length` | `31680` |
| `ETag` | `"5ffdf047-7bc0"` |
| `Last-Modified` | `Tue, 12 Jan 2021 18:53:59 GMT` |
| URL final | igual byte-lógicamente a la URL oficial solicitada |

La URL oficial exacta es:

`https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits`

Una diferencia produce `PATCH_LIST_REPRESENTATION_DRIFT_STOP`. No se adquiere ni usa automáticamente una representación cambiada y no se actualizan estos valores después de observar el drift.

## 14. Hash completo futuro de patch list

Después de una transferencia completa autorizada se calcula SHA-256 sobre los 31680 bytes exactos. Se registra como `ACQUISITION_BOUND_LOCAL_SHA256`, nunca como `PROVIDER_PUBLISHED_SHA256`.

El digest solo se convierte en identidad inmutable de los bytes admitidos para este experimento después de revisar conjuntamente el receipt de adquisición y los bindings de transporte. Una segunda implementación local de SHA-256 puede comprobar la implementación, pero no añade procedencia independiente del proveedor.

## 15. Estados de integridad de patch list

Estado inicial normativo:

| Estado | Valor |
|---|---:|
| `PROVIDER_PUBLISHED_CHECKSUM_KNOWN` | false |
| `ACQUISITION_BOUND_LOCAL_SHA256_KNOWN` | false |
| `FULL_FILE_INTEGRITY_BOUND` | false |

Después de una adquisición completa autorizada y revisión humana, una decisión prospectiva posterior puede permitir `ACQUISITION_BOUND_LOCAL_SHA256_KNOWN=true` y decidir si esa evidencia basta para `FULL_FILE_INTEGRITY_BOUND=true`. Esta especificación no realiza ni automatiza ninguna promoción.

## 16. Congelación previa a observación

No se inspeccionó ningún valor real para comprobar que las reglas propuestas encajaran con las filas. Una incompatibilidad futura es un resultado negativo científicamente válido.

No se pueden relajar regex, padding, `RELEASE=9012`, cardinalidad, unicidad o joins después de observar filas sin una nueva enmienda prospectiva. Los errores no autorizan data cleaning adaptativo.

## 17. Orden causal del metadata bootstrap futuro

El orden obligatorio es:

```text
autorización verificada
→ adquisición completa exacta
→ integridad de archivo completo
→ validación del contrato físico
→ decode bajo semántica congelada
→ validación semántica completa
→ joins exactos
→ validación de membership patch
→ DTOs candidatos técnicos
→ selección determinista de bricks
```

La selección no puede influir en decodificación de strings, aceptación de integridad, tratamiento de duplicados, validación de membership ni joins.

## 18. Boundary de derechos y redistribución

Los derechos productivos permanecen separados. Esta especificación se limita a futura adquisición científica local y validación técnica; no autoriza redistribución de FITS del proveedor, bytes de patch list ni catálogos derivados a nivel de fila.

Se preserva `redistribution=false` hasta revisión separada.

## 19. Pruebas sintéticas futuras obligatorias

Una implementación posterior debe cubrir, como mínimo:

1. brickname válido de 8 bytes;
2. rechazo de `P`/`M` mayúscula;
3. rechazo de space padding;
4. rechazo de NUL inicial;
5. rechazo de NUL interno;
6. rechazo de non-ASCII;
7. rechazo de 7 bytes;
8. rechazo de 9 bytes;
9. ausencia demostrada de trimming;
10. igualdad exacta byte a byte;
11. aceptación de `RELEASE=9012`;
12. rechazo de `RELEASE!=9012`;
13. invalidación total por una sola fila malformed;
14. rechazo de `BRICKNAME` duplicado;
15. rechazo de `BRICKID` duplicado;
16. rechazo de join root con cero matches;
17. rechazo de join root duplicado;
18. rechazo de mismatch patch/root `BRICKID`;
19. rechazo de join south con cero o múltiples matches;
20. rechazo de mismatch south `brickid`;
21. aceptación de cardinalidad 1691;
22. rechazo de 1690;
23. rechazo de 1692;
24. igualdad con digest conocido del proveedor;
25. rechazo de digest proveedor diferente;
26. incapacidad de un hash parcial para ligar integridad;
27. ausencia persistente de digest proveedor para patch;
28. detección de representation drift de patch;
29. separación entre digest local de adquisición y digest proveedor;
30. ausencia de promoción automática de estados de integridad;
31. indisponibilidad de selección antes de todos los gates.

Estas pruebas usarán únicamente valores sintéticos. No necesitan filas reales del proveedor.

## 20. Estado actual

Crear esta especificación no activa decode ni adquisición. Permanecen:

```text
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
metadata_bootstrap = NOT_STARTED
production_decode_enabled = false
redistribution = false
```

Probe 001 permanece inmutable. No se creó manifiesto, autorización, selección ni registro de derechos.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
