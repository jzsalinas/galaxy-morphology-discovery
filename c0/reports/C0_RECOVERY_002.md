# Recuperación 002 — HTTP 504 y diagnóstico acotado

La segunda ejecución humana recibió HTTP 504 en el endpoint API del catálogo, aproximadamente 31 segundos después de solicitarlo. No fue el timeout local de 120 segundos. La respuesta declaró 92 bytes; su cuerpo no se leyó. Cero bytes del catálogo, ninguna proyección creada. La rueda PyArrow permaneció en caché y no volvió a descargarse.

Diagnóstico posterior: una consulta GET documental a la página oficial del record agotó el timeout sin bytes; una consulta HEAD a la ruta pública candidata del mismo record y nombre también agotó el timeout. No se descargaron datos ni se validó una ruta alternativa. No se cambió el endpoint de ingesta. Estos resultados no identifican si la causa está en Zenodo o en un intermediario de red.

Se conserva el evento original HTTP 504. Se amplió el resumen de futuros fallos para incluir HTTP, tipo de error, etapa y bytes, sin contenido del catálogo. Dieciocho pruebas offline siguen pasando; compilación válida. No se ejecutó ingesta real ni otra descarga del catálogo.

Estado operativo: adquisición pausada tras diagnóstico acotado; no se pide otro intento sin evidencia de recuperación del servicio. Dos intentos de datos del catálogo consumidos, sin reiniciar contadores. Ningún Gate científico se ha evaluado formalmente ni se emite una decisión global de C0 en este informe de incidencia. No iniciar fases dependientes.

Para continuar será necesario demostrar de nuevo acceso al recurso versionado con una comprobación ligera y, solo después, delegar la adquisición bajo los límites restantes. Una respuesta HTTP no bastará para validar el catálogo: se exigirán tamaño y MD5 ya fijados. El fallo temporal de transporte no prueba ausencia del producto.
