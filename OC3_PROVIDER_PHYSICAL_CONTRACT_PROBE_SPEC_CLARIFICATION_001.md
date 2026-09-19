# OC-3 — aclaración prospectiva 001 de la sonda del contrato físico del proveedor

**Materia:** respuestas HTTP byte-range que alcanzan el final de la representación.  
**Fecha:** 2026-09-18.  
**Estado:** aclaración prospectiva; no implementada, no autorizada y no ejecutada.  
**Preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**Estado científico:** `OC-3 REMAINS NOT STARTED.`

## 1. Autoridad e integridad

Antes de crear esta aclaración se verificaron localmente los bindings vigentes:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_SPEC.md` | `9f86e8c685576a8207b4d5befe922f17a7a0bab428b306a8ec8af393ee37c174` |
| `OC3_PROVIDER_PHYSICAL_CONTRACT_PROBE_IMPLEMENTATION_REPORT.md` | `f96341567b35d32336640a371fc041f46401c7d4798b985d11366cd12ae68115` |
| agregado de implementación actual | `df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7` |
| fingerprint ambiental actual | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| `oc3/environment_setup/PHYSICAL_CONTRACT_PROBE_REPLAY_RECEIPT.json` | `51374b000ca3322cf3de07294d68d224b63f9b0678513775ec69d0a0264b1131` |

No se encontró discrepancia. Una discrepancia habría impedido crear este documento. El SHA-256 de esta aclaración se calcula sobre sus bytes finales y se informa fuera del documento para evitar autorreferencia.

## 2. Motivo y alcance exclusivo

La especificación y el informe de implementación vigentes requieren que toda respuesta satisfactoria a uno de los rangos de 64 KiB tenga `Content-Length=65536`. Esa regla resulta demasiado restrictiva cuando la representación vigente termina dentro del rango solicitado.

La premisa normativa suministrada y revisada externamente por el humano es RFC 9110 §14.1.2: si `last-pos` solicitado es mayor o igual que la longitud vigente, el rango se interpreta como el resto de la representación y su extremo efectivo pasa a ser la longitud vigente menos uno. No se realizó consulta de red para esta aclaración.

Este documento congela prospectivamente esa conducta antes de cualquier solicitud real. Solo aclara la validación de longitud de una respuesta `206` que alcanza EOF. No cambia las peticiones que el cliente puede emitir.

## 3. Rangos de petición inmutables

El cliente puede solicitar únicamente, en este orden causal:

1. `bytes=0-65535`;
2. `bytes=65536-131071`;
3. `bytes=131072-196607`;
4. `bytes=196608-262143`.

Aunque `HEAD` revele una representación corta, el cliente no puede generar un rango abreviado, ajustar dinámicamente `last-pos`, solicitar un sufijo, emitir un quinto rango ni reemplazar Range por un GET irrestricto.

Antes de cada petición se aplica §6: un rango cuyo inicio esté fuera de la representación conocida no se emite.

## 4. Regla normativa para una respuesta `206`

Sean:

- `S`: `requested_start`, inclusive;
- `E`: `requested_end`, inclusive;
- `L`: longitud completa actual de la representación declarada por `Content-Range`.

Una respuesta `206` es válida únicamente si se cumplen simultáneamente estas condiciones:

1. `L` es un entero decimal conocido y positivo;
2. `S < L`;
3. `actual_start = S`;
4. `actual_end = min(E, L - 1)`;
5. `Content-Range` es exactamente `bytes actual_start-actual_end/L`;
6. `Content-Length` existe, es decimal y equivale a `actual_end - actual_start + 1`;
7. la cantidad de bytes de cuerpo recibida equivale exactamente a `Content-Length`;
8. la URL, el rol, la representación y las demás comprobaciones de integridad vigentes coinciden.

No se aceptan espacios, unidades, extremos, totales ni sintaxis alternativos fuera del parser estricto ya congelado.

### 4.1 Ejemplo válido en EOF

Para:

```text
Range: bytes=0-65535
L = 40000
```

la única respuesta de longitud válida es:

```text
206
Content-Range: bytes 0-39999/40000
Content-Length: 40000
```

Es la respuesta definida para la petición Range exacta autorizada. No constituye un GET irrestricto ni una petición adaptada.

### 4.2 EOF en un rango posterior

Para el segundo rango, por ejemplo, si `L=90000`:

```text
Range: bytes=65536-131071
Content-Range: bytes 65536-89999/90000
Content-Length: 24464
```

es válido si todas las demás identidades coinciden. El tercer rango no se solicita porque su inicio, `131072`, no satisface `S < L`.

## 5. Respuesta que no alcanza EOF

Si `L > E`, el rango no alcanza EOF. En ese caso se conserva la exigencia original:

```text
actual_start = S
actual_end = E
Content-Length = E - S + 1 = 65536
```

Una respuesta más corta cuando `L > E`, un EOF del stream anterior a `Content-Length` o un cuerpo con otra longitud produce `PROBE_TRANSPORT_INTEGRITY_FAILURE`. No puede reinterpretarse como una respuesta EOF válida.

## 6. Coherencia con `HEAD` e identidad de representación

Si un `HEAD` exitoso suministró un `Content-Length` decimal confiable `H` para la misma representación, todo `Content-Range` posterior debe declarar `L=H`.

La igualdad se evalúa junto con los identificadores disponibles de la representación. Un cambio de `ETag`, `Last-Modified` u otra identidad ligada no habilita a aceptar una longitud nueva: detiene la sonda según el contrato de integridad vigente. No se continúa silenciosamente con otra generación y no se mezcla evidencia entre representaciones.

Antes de emitir cada rango autorizado:

- si la cabecera requerida ya terminó, no se emite;
- si se conoce `L` y `S >= L`, no se emite;
- solamente si la cabecera sigue incompleta y `S < L`, puede emitirse el siguiente rango literal.

Si `HEAD` ya demuestra que el inicio del primer rango está fuera de la representación, no se emite Range. Si EOF se alcanza sin completar la cabecera FITS requerida, no se solicita otro recurso o representación. La evidencia estructural queda sin resolver y el intento no puede terminar como `PROBE_PHYSICAL_CONTRACTS_RESOLVED`; bajo el modelo terminal vigente contribuye a `PROBE_PHYSICAL_CONTRACTS_PARTIALLY_RESOLVED`, salvo que exista además un fallo de mayor precedencia.

Una contradicción entre `H` y `L`, o entre identificadores de representación, produce `PROBE_TRANSPORT_INTEGRITY_FAILURE`.

## 7. Longitud completa desconocida

`Content-Range: bytes S-E/*` no permite demostrar que un cuerpo corto termina naturalmente en EOF. En esta sonda, cualquier total `*`, ausente, no decimal, cero, negativo, desbordado o ambiguo produce:

`PROBE_TRANSPORT_INTEGRITY_FAILURE`

No se infiere `L` a partir de `Content-Length`, tamaño del cuerpo, `HEAD` por sí solo ni otra respuesta.

## 8. Estados `200` y `416`

La conducta no cambia:

- `200` en respuesta a Range produce `PROBE_RANGE_UNAVAILABLE_STOP`; el cuerpo no se consume como representación completa;
- `416` produce `PROBE_RANGE_UNAVAILABLE_STOP`, sujeto a las comprobaciones de identidad e integridad ya congeladas.

No existe fallback a GET completo, mirror o recurso alternativo.

## 9. Firewall de filas

Una respuesta `206` corta por EOF puede contener bytes posteriores al límite de la cabecera BINTABLE requerida. La validez de transporte no autoriza su observación.

Para FITS sin compresión:

- solo se entregan al parser los bytes necesarios hasta el límite exacto del bloque de cabecera requerido;
- el resto recibido se mantiene opaco y se descarta sin interpretación;
- no aparece en contratos, evidencia interpretada, logs ni errores.

Para FITS gzip:

- se conserva el firewall de salida incremental;
- el descompresor emite únicamente los bytes estructurales aún necesarios;
- al alcanzar el límite de la cabecera no vuelve a invocarse;
- ningún byte no comprimido de fila puede emitirse.

Se mantienen `PROBE_ROW_OBSERVATION_FORBIDDEN` y `PROBE_ROW_OBSERVATION_INTEGRITY_FAILURE` sin cambios.

## 10. Contabilidad y reservas

En una respuesta EOF corta completada correctamente, los contadores de consumo registran exactamente los bytes de cuerpo recibidos. No registran 65536 por una respuesta legítima menor.

Una reserva preventiva anterior al transporte puede conservar el máximo de 65536 bytes para demostrar que la petición cabe en presupuesto. Esa reserva no se presenta como consumo real tras una respuesta exitosa. La regla conservadora existente para un crash antes de conocer o persistir de forma segura el consumo sigue vigente.

Los máximos originales permanecen:

- 256 KiB por recurso FITS;
- 1 MiB FITS agregado;
- 9 MiB de cuerpos HTTP agregados;
- 32 solicitudes;
- un reintento adicional por identidad exacta.

Ahorrar bytes por EOF no incrementa ningún máximo, no crea crédito transferible, no autoriza rangos adicionales y no reinicia contadores.

## 11. Corrección de implementación requerida

El agregado `df8fe72deb876b567e076e05fbd7108bd4734ead4b3b467bc2c7d1f306b836f7` y el recibo `51374b000ca3322cf3de07294d68d224b63f9b0678513775ec69d0a0264b1131` pasan a ser evidencia histórica pre-aclaración. No certifican esta nueva regla.

Una corrección posterior deberá, antes de red real, añadir como mínimo estos casos sintéticos:

1. primer rango con `L>65536`: acepta exactamente 65536 bytes;
2. primer rango con `L<65536`: acepta una respuesta `206` EOF corta válida;
3. segundo o posterior rango que termina en EOF: acepta el span corto exacto;
4. respuesta `206` corta cuando `L>E`: rechaza por integridad;
5. `Content-Length` distinto del span declarado: rechaza;
6. cuerpo distinto de `Content-Length`: rechaza y contabiliza lo recibido;
7. `Content-Length` de HEAD distinto del total de `Content-Range`: rechaza;
8. longitud HEAD inferior o igual al inicio siguiente: demuestra que ese rango no se emite;
9. EOF anterior a la cabecera FITS requerida: cierra sin contrato resuelto y sin otra adquisición;
10. bytes opacos posteriores a la cabecera en una patch list corta: demuestra ausencia en parser, contrato, logs, evidencia y errores;
11. regresión completa previa de 276 pruebas: 276/276 retenidas antes de sumar los casos nuevos.

También deberán cubrirse total `*`, deriva de identidad de representación y EOF exactamente en el extremo solicitado. El resultado final deberá tener 0 fallos, 0 omisiones y `real_network_requests=0`.

No se pueden cambiar golden values científicos o estadísticos para acomodar la corrección.

## 12. Precedencia limitada

Esta aclaración prevalece sobre la exigencia previa `Content-Length=65536` únicamente cuando el rango autorizado llega naturalmente al final de una representación cuya longitud completa `L` está demostrada.

No modifica:

- los cuatro valores literales de Range ni su orden;
- máximos de bytes, solicitudes, concurrencia o retries;
- allowlist, hosts, métodos o redirects;
- firewall de filas o política gzip;
- parser estructural FITS;
- outcomes terminales y su precedencia;
- criterios científicos;
- Amendments 001–003;
- separación de metadata bootstrap;
- necesidad de autorización humana futura.

## 13. Estado y autorización

Crear esta aclaración no modifica código, no ejecuta tests, no autoriza red y no crea evidencia de un intento real. El estado permanece:

`PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`

No debe crearse autorización humana contra la implementación pre-aclaración actual. Primero debe implementarse esta regla, ejecutarse offline la suite completa, calcularse un nuevo agregado y emitirse un nuevo recibo revisable. Solo después de revisión humana podrá considerarse una autorización `PROVIDER_PHYSICAL_CONTRACT_PROBE_ONLY` ligada al nuevo estado.

**OC-3 REMAINS NOT STARTED.**
