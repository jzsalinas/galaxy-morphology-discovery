# OC-3 — informe de implementación de selección técnica

**Stage:** `OC3-TECHNICAL-SELECTION-001`
**Estado al cerrar este informe:** implementación validada offline; selección real no ejecutada.

## Cambio implementado

- `oc3/oc3_technical_selection.py`: CLI cerrado a `--execute-offline` o `--dry-run`, sin argumentos URL ni objetos de transporte.
- `oc3/oc3lib/technical_selection.py`: revalidación de bindings locales, lectura FITS column-selective, joins exactos, elegibilidad congelada, orden SHA-256 determinista, firewall de auditoría y publicación única.
- `oc3/tests/test_technical_selection.py`: 23 pruebas sintéticas enfocadas para límites de campos y paths, ausencia de red, elegibilidad, PATCH, joins, determinismo, materialización canónica y terminales.
- `.gitignore`: excluye únicamente el CSV row-level y el directorio runtime que producirá la ejecución humana.

El agregado de implementación Python OC-3 es:

`1795c519238de667c7358520fe75b953fc47589399b4758dd0ab96969f5a906c`

La ejecución queda ligada al spec SHA-256 `781784819b6e9b8254d664d0d4d85478837c82de616a96e7ef590924f37882a8`, a los cuatro RAW inmutables ya adquiridos y a los cuatro artifacts validados de `OC3-PATCH-METADATA-DECODE-001`.

## Comportamiento verificado

La implementación observa exclusivamente los campos congelados, deriva `grz` con `GRZ_MEDIAN_PRESENT_V1`, aplica PATCH sólo a south y detiene el stage completo ante discrepancias de schema, identidad, joins o geometría. El orden usa exactamente `SHA256(UTF-8("OC3-v1|brick|<region>|<brickname>"))`, con desempate ASCII, sin RNG ni dependencia del orden proveedor.

En éxito sólo puede publicar `oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv`, con dos filas south/north y el schema canónico congelado. Los cuatro artifacts de auditoría contienen únicamente bindings, conteos y hashes agregados; las pruebas comprueban que no persisten candidatos, rankings, brick IDs, geometría, NEXP, membership PATCH ni bricknames seleccionados.

Las rutas productivas de input y output están cerradas a los paths absolutos congelados. Un path alternativo, symlink, hash incorrecto, output preexistente o artifact PATCH faltante falla cerrado antes de materializar filas productivas.

## Validación offline

- Pruebas enfocadas: **23/23 PASS**, 0 fallos, 0 skips. Log `/tmp/oc3_technical_selection_focused.log`, SHA-256 `ab324093b54d44622bb6648a1ea689248352c30b5994313b2ec83f8f46a254b4`.
- Regresión completa: **667/667 PASS**, 0 fallos, 0 skips, `real_network_requests=0`. Log `/tmp/oc3_technical_selection_full_regression.log`, SHA-256 `95089ac993dbbdb873c431b12a4faf535127cabaae24d50c79d880a8b135ea13`.
- `py_compile` y `git diff --check` pasan.
- El CSV productivo y `oc3/technical_selection/OC3-TECHNICAL-SELECTION-001/` permanecen ausentes.

No se realizó ninguna solicitud de red, descarga, inspección de píxeles o imágenes, selección de galaxias, validación física, preprocessing ni modificación de evidencia previa.

## Frontera de ejecución

La ejecución real no se realizó durante la implementación. Recorre los catálogos ROOT, NORTH y SOUTH completos y la lista PATCH; por ello `AGENTS.md` exige ejecución humana aunque permanezca bajo los caps técnicos. El costo esperado es aproximadamente 256 MiB de lectura local contabilizada, con límite fail-closed de 512 MiB, menos de 2 GiB de RAM, un thread, cero red y menos de 1 MiB de outputs. No existe reanudación ni sobrescritura: tras cualquier output final, la invocación no debe repetirse y los artifacts deben preservarse para revisión.
