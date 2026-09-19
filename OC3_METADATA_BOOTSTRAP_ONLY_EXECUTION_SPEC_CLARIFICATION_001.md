# OC-3 — Clarification 001 de la especificación `METADATA_BOOTSTRAP_ONLY`

**Fecha:** 2026-09-19  
**Naturaleza:** aclaración documental prospectiva; no es implementación ni autorización.  
**Documento aclarado:** `OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md`.  
**Precedencia limitada:** boundary de observación de campos prohibidos, autorización de resume y clasificación de STAGING.  
**Estado actual:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

## 1. Autoridades verificadas

Antes de crear esta aclaración se verificaron:

| Autoridad o evidencia | SHA-256 |
|---|---|
| `OC3_METADATA_BOOTSTRAP_ONLY_EXECUTION_SPEC.md` | `e42ecef50f2a4dd01dbd2d1c8acbcb24e48f30d4692d3bae19c73011fa265dbd` |
| `OC3_METADATA_VALUE_SEMANTICS_AND_INTEGRITY_SPEC.md` | `c72f2ff7d3032b1ed38a22cc7f002781e3e1266c8b9aa45c2af08822164d6348` |
| `OC3_METADATA_VALUE_SEMANTICS_IMPLEMENTATION_REPORT.md` | `bb84fd3992d9f2a52572bea1676234d188553078cade1229be9fedeada5d07e3` |

También coincidieron:

| Binding | Valor |
|---|---|
| agregado de implementación | `f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581` |
| fingerprint ambiental | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| regresión canónica | 413/413 passed, 0 failed, 0 skipped, 0 red real |
| Probe 001 | 13/13 paths, tamaños y SHA-256 exactos |

Una discrepancia produce `METADATA_BOOTSTRAP_CLARIFICATION_AUTHORITY_FAILURE` y prohíbe usar esta aclaración.

## 2. Propósito y precedencia limitada

Esta Clarification 001 resuelve exclusivamente:

1. la diferencia entre tránsito opaco de bytes e interpretación de una celda;
2. la autoridad requerida por un resume con capacidad de red;
3. la diferencia entre archivos de ejecución `STAGING/` y artifacts finales de evidencia.

No cambia `MODEL_B_TWO_STAGE`, attempt ID, allowlist, URLs, orden de red, métodos, headers, caps, retries dentro de una invocación, contratos físicos, value semantics, campos `TECHNICAL_ALLOWED`, prohibición de filas patch, policy de outputs row-bearing, outcomes o su precedencia, derechos, redistribución, estado científico ni agregado de implementación.

Ante conflicto sobre uno de los tres puntos aclarados, este documento prevalece sobre el texto base. Fuera de ellos, la especificación base conserva autoridad íntegra.

## 3. Boundary de observación

Se congela la distinción:

```text
OPAQUE_BYTE_TRANSIT != CELL_VALUE_OBSERVATION
```

En root, north y south, descomprimir completamente la representación gzip autorizada e íntegra hace que bytes de registros FITS atraviesen memoria. Ese tránsito es permitido únicamente como transporte estructural opaco. No autoriza interpretar todas las columnas.

Para los spans correspondientes a campos `KNOWN_BUT_FORBIDDEN` se permite solamente:

- presencia dentro de un buffer de decompression opaco;
- contabilización de bytes del buffer o stream;
- avance por el stride físico de una fila;
- cálculo y salto de offsets derivados del contrato congelado;
- descarte inmediato del span sin interpretación.

Un campo/celda se considera observado desde el primer acto que atribuya significado de valor a sus bytes. Queda prohibido:

- ejecutar decode escalar o vectorial FITS del span;
- construir un scalar, array, masked value, columna u objeto lógico;
- convertir el span a Python, NumPy, Astropy, Pandas o record array;
- aplicar cast, coerción, null handling o scaling para obtener su valor;
- comparar el valor o calcular count/distinct/min/max/distribución/estadística;
- incluirlo en logs, errores, debug dumps, serialización, DTOs o artifacts;
- usarlo para joins, elegibilidad, orden o selección.

La mera existencia de bytes descomprimidos en memoria no cuenta como observación si permanecen opacos, se saltan por offset y nunca adquieren representación de valor.

## 4. Arquitectura selectiva obligatoria

Para tablas reales root, north y south quedan prohibidas las rutas que puedan materializar la tabla completa o columnas prohibidas, incluidas:

```text
hdu.data
Table.read
FITS_rec de filas completas
np.asarray(full_table)
record arrays que contengan campos prohibidos
conversión a Pandas
conversión a Astropy Table con columnas prohibidas materializadas
```

No basta con materializar todo y descartar después. La implementación debe usar un decoder selectivo revisado cuyos únicos outputs de valor sean las columnas `TECHNICAL_ALLOWED` congeladas.

La arquitectura admisible sigue este orden:

1. validar el schema físico completo exclusivamente desde metadata de cabecera;
2. obtener y descomprimir bytes de row records como stream/buffer opaco;
3. calcular offsets deterministas desde `NAXIS1`, orden y `TFORM` congelados;
4. extraer y decodificar únicamente slices pertenecientes a campos `TECHNICAL_ALLOWED`;
5. avanzar sobre spans `KNOWN_BUT_FORBIDDEN` sin invocar decoder de valor;
6. descartar esos spans sin representación a nivel de celda.

La validación de metadata física puede conocer nombre, TFORM, shape, offset, longitud y restricciones estructurales de una columna prohibida. No puede conocer el valor de ninguna celda de esa columna.

Si una biblioteca o ruta de ejecución no permite demostrar esta separación, el bootstrap falla cerrado con `METADATA_FORBIDDEN_FIELD_BOUNDARY_FAILURE` antes del primer valor prohibido.

## 5. Prueba instrumental y canarios

Los fixtures sintéticos futuros deben colocar valores canario distintivos en todos los campos `KNOWN_BUT_FORBIDDEN`, incluidos scalars y vectores. La instrumentación separa explícitamente:

```text
opaque_bytes_transited
cell_values_decoded
```

`opaque_bytes_transited` puede ser mayor que cero debido a decompression/stride. Eso no implica observación. Para una ejecución válida deben permanecer exactamente:

```text
forbidden_cell_decode_count = 0
forbidden_value_materialization_count = 0
forbidden_value_log_count = 0
forbidden_value_serialization_count = 0
```

La prueba debe tripwirear la llamada al decoder antes de producir un objeto de valor. Buscar después el canario en un artifact no sustituye el contador de materialización: ambos controles son necesarios.

Las columnas permitidas ubicadas antes, entre y después de spans prohibidos deben decodificarse correctamente, demostrando offsets y stride sin interpretar el contenido omitido.

## 6. Patch permanece más estricto

La licencia de tránsito opaco de §§3–4 se limita a root, north y south. No se extiende a `SOUTH_PATCH_LIST` en `OC3-METADATA-BOOTSTRAP-001`.

Bajo MODEL B, patch permite solamente parsing de cabeceras. Como su representación está sin compresión, no existe necesidad de hacer transitar el payload BINTABLE por un decoder de filas. Ningún slice perteneciente a row records patch puede suministrarse a una función de decode o iteración.

Permanecen:

```text
RELEASE = NOT_OBSERVED
BRICKID = NOT_OBSERVED
BRICKNAME = NOT_OBSERVED
patch_row_semantics = NOT_OBSERVED
patch_membership = NOT_OBSERVED
```

Que los bytes raw completos se hayan adquirido y hasheado no autoriza a leer su payload como tabla.

## 7. Autorización de primera ejecución

Se congela:

```text
FIRST_RUN_NETWORK_AUTHORIZATION != RESUME_NETWORK_AUTHORIZATION
```

La autorización humana final de la primera ejecución liga únicamente el argv literal sin `--resume`, el attempt ID, spec/clarification, implementación, entorno, allowlist, caps y command hash exactos. Añadir `--resume`, cambiar argv o reinterpretar la autorización original invalida el binding antes de construir transporte.

El retry automático único de una identidad exacta, dentro de la misma invocación autorizada, permanece incluido en la autorización first-run. No es un resume ni una nueva intención humana si conserva método, URL, headers, caps, attempt, ledger y proceso invocado.

## 8. Autorización separada de resume con red

Una ejecución posterior iniciada por una persona con `--resume` constituye otra intención y otro argv. Si puede construir transporte de red, requiere un candidato y aprobación separados.

El candidato de resume debe ligar como mínimo:

- `scope=METADATA_BOOTSTRAP_ONLY` y `execution_mode=NETWORK_RESUME`;
- attempt ID y directorio existentes exactos;
- SHA-256 de la autorización first-run, spec y esta clarification;
- ledger identity, watermark y resumen de counters/caps consumidos;
- raw completos ya ligados y sus receipts;
- staging parciales presentes con tamaños/counters;
- recursos pendientes exactos y operaciones restantes;
- caps globales restantes sin reinicio ni aumento;
- agregado de implementación, fingerprint ambiental y replay aplicable;
- argv literal de resume, command hash y `authorized=false` hasta aprobación humana.

La autorización first-run no satisface este objeto. La persona debe aprobar explícitamente el candidato de resume; no se deriva aprobación por presencia del attempt.

Un comando puramente offline puede inspeccionar, verificar o producir un diagnóstico desde evidencia existente sin autorización de red nueva únicamente si su construcción no posee transport capability y no puede cambiar estado de adquisición. `--offline` no puede caer a red por error o fallback.

## 9. Resume, retries y contabilidad

La distinción normativa es:

```text
automatic bounded retry inside one authorized invocation
!=
later human-invoked --resume execution
```

El retry interno sigue sujeto a la identidad exacta, un solo intento adicional y todos los caps originales. Un resume autorizado reutiliza el mismo ledger, counters, attempt y saldos; no reinicia requests, bytes, retries, disco, I/O, compute o wall. Si el saldo restante no permite la operación completa, falla antes de red.

La revisión y aprobación de un resume no amplía caps ni autoriza nuevos recursos.

## 10. STAGING frente a artifacts finales

La lista `BOOTSTRAP_*` de §18 de la especificación base enumera **artifacts finales de evidencia**. Los archivos bajo `STAGING/` son estado interno de ejecución y no forman parte de esa lista final.

El único path permitido es:

`oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001/STAGING/`

No puede existir staging de este attempt fuera de ese directorio. Cada archivo liga request identity, ordinal de intento, ledger, bytes observados y estado. No es una representación completa por nombre, extensión o tamaño aparente.

## 11. Terminal exitoso

Para emitir `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED` deben cumplirse conjuntamente:

- no queda ningún payload incompleto u huérfano bajo `STAGING/`;
- los cuatro cuerpos completos fueron publicados atómicamente en los paths `RAW_IMMUTABLE` congelados;
- raw manifest, receipts, integridad, contratos, resumen y terminal ligan esos cuatro paths;
- la lista final del attempt contiene los cuatro raw más exactamente los artifacts finales autorizados por §18 base;
- no existe un artifact adicional de filas, selección o staging.

El proceso puede eliminar su propio staging transitorio únicamente después de publicación raw comprobada, antes del terminal exitoso, y dejando en ledger/events la identidad y contabilidad. No puede eliminar evidencia de un intento fallido para simular éxito.

## 12. Terminal fallido o detenido

Ante fallo/stop, uno o más archivos parciales pueden permanecer en `STAGING/` como evidencia forense. Cada uno debe:

- permanecer dentro del path exacto de §10;
- estar ligado al ledger y al intento/request exactos;
- registrar número exacto de bytes observados y consumo correspondiente;
- conservar estado explícito `PARTIAL`, `FAILED` o `UNCERTAIN`, nunca `COMPLETE`;
- no satisfacer raw manifest, integridad completa, contrato FITS o input de parser;
- no publicarse, sobrescribirse ni borrarse silenciosamente por auditoría.

Su presencia no contradice la lista cerrada de artifacts **finales**, porque STAGING es estado de ejecución fallida. `BOOTSTRAP_TERMINAL.json` y el inventario forense deben declarar los staging existentes sin incorporar su contenido como filas o FITS.

## 13. Resume y STAGING

Un resume con autorización separada puede inspeccionar offline raw, staging y ledger antes de considerar red. Un body parcial previo nunca se continúa con Range y nunca se abre como FITS.

Si se autoriza otro GET completo, escribe un staging nuevo con identidad/ordinal diferente. No se anexa, trunca, reemplaza ni sobrescribe un staging previo. Los bytes del intento anterior permanecen cargados al presupuesto. Solo el nuevo cuerpo completo puede seguir la publicación atómica raw de la especificación base.

## 14. Pruebas futuras obligatorias

La implementación posterior debe cubrir al menos:

1. tránsito de bytes prohibidos en un buffer sintético de decompression;
2. `forbidden_cell_decode_count=0`;
3. ausencia de objetos Python/NumPy para valores prohibidos;
4. ausencia de canarios prohibidos en logs, errores y artifacts;
5. decode correcto de columnas permitidas alrededor de spans omitidos;
6. rutas `hdu.data`, `Table.read` y tabla completa inalcanzables para proveedor real;
7. payload patch incapaz de entrar al decoder bajo MODEL B;
8. autorización first-run rechaza argv con `--resume`;
9. resume con red rechaza autorización first-run;
10. shape de autorización resume separada se valida completamente offline;
11. retry exacto dentro de una invocación sigue permitido y acotado;
12. terminal exitoso rechaza staging incompleto/huérfano;
13. terminal fallido preserva staging parcial ledger-bound;
14. staging parcial nunca satisface integridad completa ni parser FITS;
15. Probe 001 permanece 13/13 inmutable;
16. replay sintético registra `real_network_requests=0`.

Los tests deben instalar firewall de socket/DNS antes de discovery/import. Todas las filas, buffers y canarios son sintéticos; no leen datos del proveedor ni prefixes de Probe 001 como tabla.

## 15. Estado inalterado

Crear esta aclaración no modifica código, tests, outputs históricos, autorización, attempt, ledger, raw, staging ni estado productivo.

```text
PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS
metadata_bootstrap = NOT_STARTED
production_decode_enabled = false
redistribution = false
real_network_requests = 0
real_provider_row_values = 0
```

El agregado de implementación permanece:

`f3f64a05c581e2c74d2cb80c2a2e499ab7c76cbd8eba7ad7f9e5f40a49e48581`

Probe 001 permanece inmutable 13/13.

**DO NOT RE-RUN OR RESUME PROBE 001.**

**OC-3 REMAINS NOT STARTED.**
