# Recuperación de sesión y factibilidad HTTP Range

## Estado recuperado antes de modificar archivos

Los seis checkpoints humanos tienen estado de éxito en disco y no se repitieron. Los documentos autoritativos y AGENTS.md conservan los SHA-256 del snapshot inicial. Git sigue sin reconocer un repositorio; no hay diff fiable y no se modificó .git.

El experimento Range estaba implementado como prototipo y había sido ejecutado mediante comandos ad hoc. Existían:

- c0_pipeline/ranges.py: fetch_range y RangeView.
- c0/probe/range_smoke/prefix.bin: 262144 bytes.
- c0/probe/range_smoke/tiles.bin: 1119953 bytes.
- c0/probe/range_smoke/plan.json: región x0=1762, y0=2985, 256×256; dieciséis tiles de 100×100; banda g, brick 1853p160.
- c0/reports/C0_RANGE_SMOKE_COMPARISON.json: igualdad exacta declarada frente a subimage; no comparación con un archivo oficial completo descargado.
- Dos eventos VERIFIED_RANGE / HTTP 206 con URL, ETag, Content-Range, timestamps UTC y SHA-256 concordantes con los archivos.

No había archivos .part del experimento, pruebas específicas de Range ni CLI de reproducción. No se encontró log separado de los comandos ad hoc: el registro persistente era el ledger SQLite y el JSON de comparación. Los resúmenes exportados estaban atrasados en dos solicitudes y 1382097 bytes.

Se preservaron copias del prototipo, plan, comparación y exportaciones antiguas, junto con un snapshot de hashes y eventos, en c0/provenance/recovery_range_001/. Los dos fragmentos originales no fueron modificados.

## Comprobaciones nuevas, exclusivamente locales

Se implementó range_plan.py y range_experiment.py con modo offline. Se reprodujo la planificación desde el prefijo oficial recuperado y se exigió igualdad con el plan previo. La región extraída de esos bytes coincide exactamente con la subimagen guardada; sus WCS coinciden en las cuatro esquinas dentro de 1e-5 píxeles, tolerancia numérica explícita. Ver C0_RANGE_OFFLINE_VERIFICATION.json.

44 pruebas pasan: HTTP 200 rechazado sin leer cuerpos, ETags/rangos/tamaños/codificación incompatibles, truncación, caché que no mezcla versiones, huecos de bytes rechazados, conflictos de solapamiento, WCS desplazada y equivalencia parcial/completa para tres regiones de un FITS sintético comprimido (incluyendo bordes y NaN). La comparación sintética usa la imagen leída del archivo completo, no los píxeles anteriores a comprimir. Log final: c0/logs/test_range_recovery_003.log. Se conservan logs de las iteraciones previas, incluida una prueba inicialmente fallida por el alias RICE_1 frente a RICE_ONE, corregida con soporte explícito para ambos identificadores.

Se fortaleció el cache para exigir tamaño total y ETag compatibles. El lector virtual nunca rellena bytes ausentes con ceros. El plan admite solo layouts RICE bidimensionales verificados y descriptores de heap de bytes reconocidos; cualquier otro caso se detiene sin improvisar. El intervalo incluye bytes intermedios entre tiles para reducir solicitudes: no se afirma que sea el mínimo teórico.

Las exportaciones ahora incluyen range_start/range_end/resource_total_bytes/content_range y un contador separado VERIFIED_RANGE. Se regeneraron desde el ledger sin adquirir datos. Ninguna etapa manual exitosa fue reejecutada.

## Conclusión limitada

Factibilidad técnica demostrada para la representación HTTP y región probadas: 1382097 bytes recuperados frente a 13236480 del archivo completo (aproximadamente 89.6% menos). La cabecera oficial contiene BUNIT=nanomaggy. No se cambia producto, release, calibración ni resolución.

La prueba de lectura completa frente a parcial es sintética; para el archivo oficial se verifican los bytes declarados por HTTP 206, su ETag común, SHA-256 por fragmento, extracción sin lectura de huecos e igualdad con el subarray del servicio. No se ha comprobado el SHA-256 del coadd completo contra el proveedor. El ETag es un validador HTTP, no un checksum criptográfico del archivo. No se ha establecido todavía equivalencia con el cutout normal remuestreado ni aprobado C0-C/C0-D.

Siguiente paso: experimento manual sobre los mismos doce objetos fijados, 42 archivos oficiales; máximo 128 MiB adicionales y 84 solicitudes de datos por ejecución. Si falla acceso Range, layout o equivalencia, detener y registrar; no descargar el archivo completo como fallback ni sustituir productos.

## Recursos

Ledger recuperado y conservado: 411215853 bytes, 301 solicitudes no metadata, 845 solicitudes totales y 96 objetos. Esta recuperación no realizó solicitudes de red. Los límites originales permanecen sin cambios.
