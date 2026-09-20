# OC-3 — informe de implementación `PATCH_METADATA_DECODE_ONLY`

**Stage:** `OC3-PATCH-METADATA-DECODE-001`
**Estado al cerrar este informe:** implementación validada offline; invocación real no ejecutada.

## Cambio implementado

- `oc3/oc3_patch_metadata_decode.py`: CLI cerrado a `--execute-offline` o `--dry-run`, sin argumentos URL ni construcción de transporte.
- `oc3/oc3lib/patch_metadata_decode.py`: binding exacto de Attempt 001, decoder FITS manual row-stride, validación semántica y relacional, tripwires, firewall de outputs y límites de recursos.
- `oc3/tests/test_patch_metadata_decode.py`: 21 pruebas sintéticas enfocadas.
- `.gitignore`: excluye exclusivamente el directorio runtime de esta etapa.
- `oc3/oc3lib/metadata_bootstrap.py` y sus dos suites: aíslan los intentos sintéticos del Attempt 001 real ya completado; el path de producción permanece canónico e inalterado.

El agregado de implementación OC-3 nuevo es:

`479feb485ac63399595f6bf0b69a281a784356ecb498842ea3f80c7d60826810`

El decoder verifica por separado que la evidencia fuente esté ligada al agregado bootstrap histórico `432bcd449673786075938d3a290ad0ea139cc88bf1c2aae758c59d09179ef276`; no exige que el código actual conserve ese agregado.

## Validación offline

- Pruebas enfocadas: **21/21 PASS**, 0 fallos, 0 skips. Log `/tmp/oc3_patch_focused.log`, SHA-256 `6132368efa006e50887e6a6c249d3a4668e84f32199ad617a4d36c686265324b`.
- Regresión completa: **644/644 PASS**, 0 fallos, 0 skips, `real_network_requests=0`. Log `/tmp/oc3_patch_full_regression.log`, SHA-256 `5682dc8c00c8f856b1846a6021db312cbf51765e6251fdb99baa9986e6dfa3a8`.
- La prueba de frontera rechaza un cuarto campo PATCH antes de observar su valor y registra únicamente el contador agregado del tripwire.
- Los outputs sintéticos contienen sólo bindings, contadores y terminales; no contienen valores de filas.
- Los límites de I/O, output, memoria, tiempo e hilos se comprueban de forma fail-closed durante lecturas y barridos. Los entornos numéricos quedan fijados a un thread.

No se abrió ninguna conexión ni se resolvió DNS. No hubo descarga, readquisición, selección técnica, materialización de cohorte ni modificación de `OC3-METADATA-BOOTSTRAP-001`.

## Frontera de ejecución

La invocación real PATCH no se ejecutó al crear este informe. Aunque el volumen estimado está dentro de 512 MiB de I/O y 5 minutos, recorre catálogos ROOT/SOUTH completos para construir las referencias de join. `AGENTS.md` clasifica toda operación bulk sobre catálogos como ejecución humana obligatoria. La implementación debe quedar comprometida antes de entregar ese comando.
