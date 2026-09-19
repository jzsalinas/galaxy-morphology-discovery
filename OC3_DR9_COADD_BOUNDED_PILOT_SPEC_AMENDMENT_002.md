# OC-3 — enmienda prospectiva 002

**Fecha:** 2026-09-18.  
**Estado:** corrección autorizada de especificación/contrato de ejecución; sin implementación ni ejecución.  
**OC-3 REMAINS NOT STARTED.**  
**Preflight actual: PREFLIGHT_BLOCKED_ENVIRONMENT, con bloqueos adicionales de integración.**

## 1. Autoridad, integridad y naturaleza de la corrección

Se verificaron antes de redactar esta enmienda los siete archivos exigidos; todos coinciden con los SHA-256 esperados:

| Autoridad / evidencia congelada | SHA-256 verificado |
|---|---|
| MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| OC3_IMPLEMENTATION_REPORT.md | `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864` |
| OC3_EXECUTION_PREFLIGHT_SPEC.md | `6d5617ad5cc2b552d4a036a340077f4a727d06be4217e10d0f5b7408c9f6c28e` |
| OC3_ENVIRONMENT_SETUP.md | `fc39dba8f0d757ef0b342af01ff5710e21b56c1e6093c7969f910e02ad27c43d` |

AGENTS.md fue leído: SHA-256 `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222`. La implementación OC-3 se examinó en modo de solo lectura. Su hash agregado previo sigue siendo `cf01a2774237ca98bf83dab01dda39a728f803e72e93c6796f214d20dcc6d57f`. Los documentos de intención científica y gobierno C0 conservan su autoridad histórica; no se reabre C0 ni E-OC1.

La instrucción prospectiva del usuario autoriza exclusivamente este nuevo Markdown. Un hash discrepante hubiera exigido detenerse, sin actualizar expectativas. El SHA-256 de Amendment 002 se calcula después de escribirla y se comunicará externamente: un futuro manifiesto debe incluirlo; no se introduce una autorreferencia imposible dentro de estos bytes.

### Defecto 1 — circularidad de bootstrap

**OBSERVED, código local:** `workflow.read_inputs` requiere el manifiesto final y la allowlist; `build_plan` llama a `choose_bricks` antes de adquirir metadata. Sin embargo, la metadata debe determinar los dos candidatos y permitir crear esos archivos. Usar candidatos ficticios, allowlists provisionales o URLs adivinadas no resuelve el defecto metodológicamente.

### Defecto 2 — límites de etapa confundidos con globales

**OBSERVED, código local:** `Ledger.__init__` conserva reducciones de caps mediante min, y los argumentos actuales `--max-*` alimentan esos caps globales. Aplicar allí 48 MiB/48 requests dejaría reducido permanentemente el presupuesto global; no sería legítimo devolverlo después a 1.5 GiB/200 requests.

Ambos son **DESIGN / EXECUTION-CONTRACT defects**, detectados antes de ejecución científica. **No son observaciones DR9 ni fallos experimentales de OC-3.** La evidencia histórica de 100 pruebas sintéticas no probaba este arranque causal ni una promoción con subpresupuestos. No se reescribe esa evidencia ni se la presenta como validación de la corrección aún no implementada.

## 2. Orden causal previo a la selección

Se sustituye prospectivamente solo el orden de bootstrap del contrato de ejecución:

```text
FROZEN AUTHORITIES
  → INDEPENDENT VERIFIED ENVIRONMENT
  → OC3_METADATA_BOOTSTRAP_MANIFEST.json
  → METADATA-ONLY ACQUISITION
  → DETERMINISTIC NORTH/SOUTH BRICK RESOLUTION
  → PERMANENT INSTRUMENTAL_DEVELOPMENT MARKING
  → OC3_DEVELOPMENT_BRICKS.csv
  → OC3_INPUT_MANIFEST.json
  → FINAL RESOURCE PLAN
  → SEPARATE HUMAN AUTHORIZATION
  → ACQUIRE-AUX
```

La metadata-only acquisition incluye las dependencias acotadas que solo pueden resolverse tras identificar los dos bricks: sus índices técnicos y HEAD condicionales, conforme a §4. No permite abrir mapas. La resolución de bricks no es la selección de las seis ubicaciones S1–N3; esta última sigue requiriendo auxiliares y pertenece a una etapa posterior.

El bootstrap forma parte de la contabilidad OC-3 desde su primera solicitud, pero **no es una observación científica de píxeles**. Ningún GET de mapa o PSF se admite antes de la promoción final y de las autorizaciones posteriores correspondientes. El bootstrap no requiere que existan los dos archivos finales, ni los crea vacíos para satisfacer una validación prematura.

## 3. Nuevo input de bootstrap y sellado

Se añade al inventario prospectivo un único nuevo input de producción:

`oc3/INPUTS/OC3_METADATA_BOOTSTRAP_MANIFEST.json`

Es distinto de `oc3/INPUTS/OC3_INPUT_MANIFEST.json`. **No se crea en esta entrega.** Su esquema versionado debe rechazar campos extra, rutas prohibidas y contenido de sujetos; no debe aceptar como alias el esquema final anterior.

### Contenido obligatorio del padre

| Grupo | Binding mínimo exigido |
|---|---|
| Autoridades | Hashes de los siete documentos de §1, AGENTS, Amendment 001 y esta Amendment 002; referencias de gobierno aplicables, sin omitir una enmienda al ejecutar |
| Implementación | Versión identificable cuando exista y hash exacto de código/tests revisados para implementar 002; el hash histórico no acredita una versión futura distinta |
| Entorno | Python exacto/build, paquetes requeridos y versiones efectivas, fingerprint independiente, hash de installation report, preparation receipt y replay sintético, incluido resultado de cero red real |
| Familia | Legacy Surveys release DR9 completo; regiones north/south; bandas g/r/z, sin sustitutos |
| Selección | Reglas congeladas de geometría/cobertura/generación y hash ordering; prohibición de reemplazo; ningún brick aún no derivado se escribe como elegido |
| Separación científica | Política permanente INSTRUMENTAL_DEVELOPMENT y exclusión confirmatoria prospectiva |
| Recursos | Identidades metadata enumeradas, método HTTP, roles/tipos, hosts exactos, URL y evidencia documental aplicable, release/generación, referencia de checksum proveedor cuando exista y hard body cap por recurso |
| Límites | Caps globales sellados y límites de METADATA_BOOTSTRAP separados, incluidos límites menores autorizados |
| Derechos | Alcance afirmativamente revisado de análisis/cache local y evidence_refs; reproducción de imágenes separada; redistribution=false con alcance FITS/derivados DISABLED/UNRESOLVED |
| Autorización | Referencia y hash del registro humano de alcance metadata-only, límites y versión revisada; no basta escribir execute-network en la CLI |

No contendrá identidades de galaxias, Galaxy Zoo, votos/predicciones, filas de fuentes Tractor, morfología, magnitud, color, propiedades físicas, selección derivada de imágenes ni URLs coadd adivinadas. Tampoco pares de bricks «provisionales». No se abre un holdout para construirlo.

### Canonicalización y dos hashes diferentes

Para todo manifiesto JSON sellado de este contrato:

1. Rechazar claves duplicadas, valores no finitos, esquemas desconocidos y tipos ambiguos. Las listas con significado de orden mantienen el orden congelado; los conjuntos técnicos se ordenan por una regla explícita antes de serializar, nunca por orden accidental del proveedor.
2. Definir C(obj) como UTF-8 de JSON con claves ordenadas, `separators=(',', ':')`, `ensure_ascii=False`, `allow_nan=False`, sin BOM. La implementación fijada controla la serialización; no se afirma equivalencia universal con otro canonicalizador.
3. `sealed = SHA256(C(obj sin únicamente el campo superior sealed))`, hex minúsculo de 64 caracteres.
4. Archivo final = `C(obj con sealed)` seguido por exactamente un LF. `file_sha256 = SHA256(bytes exactos del archivo final)`, incluyendo ese LF. El hash de archivo se registra en el ledger/binding posterior, no dentro del mismo archivo para evitar autorreferencia.
5. Fijar antes del sello los timestamps/identificadores que forman parte del contenido; reanudarlos desde evidencia almacenada, no regenerarlos al recalcular hashes.

El manifiesto padre se sella y registra antes de la primera solicitud metadata. Desde esa solicitud es inmutable; cualquier cambio constituye otro input incompatible, no un resume. Una revisión pre-ejecución requiere nueva revisión/autorización y sello antes de red, nunca reescribir un padre ya usado. Sellar no prueba por sí solo derechos, procedencia ni autorización.

## 4. Alcance metadata y referencias dependientes

Solo se permiten los roles ya fijados en OC3_EXECUTION_PREFLIGHT_SPEC.md:

| Rol | Operación permitida | Máximo por cuerpo heredado del preflight |
|---|---|---:|
| Manifiestos SHA-256 oficiales aplicables a raíz/north/south-9012 | GET; hasta tres identidades distintas, deduplicadas si corresponden al mismo archivo | 1 MiB cada uno |
| survey-bricks.fits.gz | GET de tabla técnica geométrica | 16 MiB |
| survey-bricks-dr9-north.fits.gz | GET de resumen técnico de cobertura | 8 MiB |
| survey-bricks-dr9-south.fits.gz | GET de resumen técnico de cobertura | 16 MiB |
| Lista oficial de los 1691 bricks sur corregidos/9012 | GET de lista técnica identificada documentalmente | 2 MiB |
| Índice técnico del único brick sur seleccionado | Un GET acotado, no recorrido recursivo | 512 KiB |
| Índice técnico del único brick norte seleccionado | Un GET acotado, no recorrido recursivo | 512 KiB |
| Recursos coadd futuros ya identificados, máximo 26 | HEAD condicional, solo si falta tamaño exacto en metadata previa | 64 KiB de eventual cuerpo de error por intento; cuerpo HEAD exitoso esperado cero |

Son cotas, no tamaños ni disponibilidad observados. Hasta 9 GET distintos y 26 HEAD condicionales sin reintentos; el tope agregado sigue siendo 48 requests. Duplicados exactos de identidad se recuperan una vez. No se añade un documento, tabla CCD ni manifiesto extra automáticamente porque falte evidencia: una fuente necesaria fuera del inventario exige revisión antes de red, dentro de autoridades y presupuesto.

**Prohibido durante bootstrap:** GET de image, invvar, nexp, maskbits o psfsize; cualquier coadd-PSF request; catálogos de fuentes Tractor; model, blobmodel, depth, galdepth, chi2, JPEG, exposiciones individuales, recursos Galaxy Zoo y crawling recursivo. **HEAD no autoriza GET.** No se usa FITS Range para leer headers de mapas científicos. Un tamaño HTTP no verifica HDU, WCS, unidades o contenido.

### Resolver dependencias sin volver a introducir la circularidad

Las identidades de los primeros resúmenes/checksums deben tener URL literal y procedencia exactas antes del primer request. No se puede enumerar honestamente la URL de un brick todavía desconocido como si ya estuviese seleccionado. Por ello los únicos recursos dependientes se representan en el padre mediante **roles finitos enumerados y reglas de resolución documentadas**, no mediante libertad de búsqueda:

- exactamente un rol de índice por región, ligado al resultado sellado de la regla de §5;
- hasta 26 roles HEAD, ligados a los cinco tipos autorizados, brick/región/generación/banda y a enlaces exactos obtenidos de esos dos índices o metadata oficial ya autorizada;
- cada rol fija método, host, fuente documental de la relación de URL, dependencias, cardinalidad y body cap. Ningún patrón admite un brick alternativo, un método distinto o un sufijo adivinado.

Antes de enviar cada solicitud dependiente se debe materializar su **URL literal e identidad exacta** en un registro inmutable de resolución, con hash del rol padre, hash de la evidencia recuperada, hash de selección y método/cota. Ese registro es evidencia append-only subordinada al padre, no una edición del manifiesto ni una segunda promoción. La función de resolución debe reproducir exactamente la misma identidad offline. Un enlace sin cadena documental verificable, una URL no enumerada ni derivable por esos roles cerrados o cualquier redirección no autorizada se rechaza antes de transferir; no hay descubrimiento abierto.

Si no se puede expresar/revisar esa relación de forma suficientemente cerrada, se conserva el bloqueo de manifiesto; no se soluciona permitiendo URLs arbitrarias en runtime. Esta precisión distingue la identidad declarada del rol antes de selección de la identidad concreta obligatoria antes de su request. No habilita URLs coadd construidas por intuición. El inventario finalmente adquirido, sus identidades exactas y todos los registros de resolución se incluyen en el recibo metadata hasheado.

## 5. Resolución determinista y territorio de desarrollo

Tras validar metadata y su proyección técnica permitida:

1. Construir candidatos exclusivamente con geometría, cobertura DR9 g/r/z y generación documentalmente verificadas. Mantener el inventario proyectado/ordenado y sus hashes; columnas inesperadas se rechazan sin imprimir contenido prohibido. No leer valores de fuentes para «completar» cobertura.
2. Sur: intersección con el subconjunto oficial corregido **RELEASE=9012**, no una suposición basada en el nombre de archivo. Norte: DR9 completo BASS/MzLS con su generación documentada; no imponerle la regla 9012 sur.
3. Para cada región ordenar por SHA-256 UTF-8 de `OC3-v1|brick|<region>|<brickname>` ascendente, sin espacios ni newline. Desempate por brickname ASCII. Elegir el primero: exactamente un sur DECaLS y un norte BASS/MzLS si ambas clases son resolubles.
4. Registrar inmediatamente la pareja, sus identidades de generación y evidencia de selección en el ledger. Marcar ambos bricks **INSTRUMENTAL_DEVELOPMENT** permanentemente, incluyendo todas sus ventanas OC-3 y productos observacionales directos. Este registro precede a cualquier interpretación de conveniencia posterior y sobrevive aunque no se complete la promoción o el piloto.

No se permite inspección visual, recuento de fuentes, selección por brillo/color/morfología, quality shopping ni umbral de seeing/profundidad no congelado. No hay reemplazo por un brick «más fácil» si después falta un producto, un estrato, un tamaño favorable o un permiso. Resume usa la misma pareja y el mismo registro; comprobar reproducibilidad no autoriza efectuar otra elección.

Si no existe candidato elegible en cualquiera de las dos regiones, el bootstrap termina por insuficiencia conservando recibos/consumo; no promueve un hijo incompleto ni busca otra release, DR9sv o survey. Eso no crea un quinto desenlace científico: una eventual clausura formal OC-3 seguirá las reglas existentes de insuficiencia, sin ejecutar ahora finalize ni atribuir observaciones que no existen.

La exclusión del territorio de desarrollo de toda evaluación morfológica confirmatoria futura es vinculante incluso si OC-3 falla. Se implementa prospectivamente, no inspeccionando el holdout. Un conflicto posterior con una partición previamente congelada exige detener/revisar; no reemplazar la pareja para esconderlo.

## 6. Binding padre → hijo y promoción única

El manifiesto bootstrap es el **PARENT execution binding**. Su sello/hash y autoridades fijan el origen de la corrida y del ledger único. Una vez resuelta la metadata, existe como máximo **un CHILD execution binding**, inmutable, con:

- file hash y sello canónico del padre;
- hash del recibo metadata, incluidos URLs/métodos, respuestas/fragmentos, checksums, fallos/reintentos y resoluciones dependientes;
- identidad del mismo ledger y watermark de eventos/counters;
- bytes y requests consumidos, más los restantes contadores globales/de etapa pertinentes;
- pareja exacta elegida y hash/evidencia de selección determinista;
- registro permanente de exclusión de desarrollo;
- SHA-256 del CSV de desarrollo;
- sello y file hash del input final;
- identidades exactas de recursos futuros y su alcance;
- caps efectivos sellados y saldo global al watermark indicado;
- todos los bindings de autoridades, entorno, derechos aplicables e implementación, sin cambios respecto del padre.

**El hijo refina al padre; no reemplaza historia.** No se hace UPDATE del binding padre ni edición manual de SQLite para conseguir compatibilidad. Los artefactos metadata siguen ligados al padre; los posteriores enlazan al hijo y, transitivamente, al padre. Una discrepancia de entorno/código/autoridades entre ambos detiene por integridad, no crea una nueva pareja.

### Atomicidad semántica y ausencia de ciclos de hash

La futura implementación debe cumplir, independientemente de su formato físico concreto:

1. Padre y ledger se registran antes de red. El recibo metadata se fija cuando no hay HTTP pendiente; snapshot de counters + watermark reproducible. La identidad del ledger es persistente y verificable, no el hash permanente de un SQLite que seguirá cambiando.
2. Preparar deterministicamente CSV → input final → registro hijo, en ese orden de hashes. El input final contiene enlaces hacia padre/metadata/CSV, **no el hash de un hijo que a su vez contiene su propio file hash**. El registro hijo se hashea fuera de sí mismo. Así no existe ciclo de autorreferencias.
3. Preservar bytes preparados y hashes. Un registro de preparación append-only puede fijar el hijo propuesto sin autorizar todavía uso de píxeles. No existe una segunda variante válida bajo el mismo padre.
4. Publicar una sola relación padre→hijo mediante commit atómico con unicidad por padre e identidad de ledger. Su significado es append-only aunque existan tablas auxiliares de contadores derivados. Rechazar un segundo intento explícito de promoción, incluso si pretende sustituir por otra pareja «equivalente».
5. Archivos finales preparados pero sin commit no son inputs activos. Lectores exigen la promoción comprometida y sus hashes antes de usarlos. Si un crash separa publicación de archivos y commit, la recuperación solo puede completar exactamente los mismos bytes/binding o parar para revisión de integridad.
6. Tras commit, resume valida y utiliza el hijo existente: esto **no es otro intento de promoción**. No se reejecuta selección ni se vuelve a adquirir metadata ya validada. Una petición explícita de promover de nuevo se rechaza; una reanudación normal después del commit solo reproduce el estado hijo.

Antes del commit, resume reproduce el estado padre y, si existe preparación, exactamente esa preparación. Después del commit, reproduce el hijo comprometido. Un crash en la frontera no puede hacer desaparecer el registro de desarrollo, crear otro ledger, reiniciar contadores o elegir otro brick.

Los saldos del hijo son snapshots identificados por watermark, no una nueva bolsa de recursos. IO/cómputo de preparación, publicación y recuperación también se contabilizan; gastos posteriores al snapshot permanecen como eventos adicionales. Toda reserva usa los counters vivos y sus reservas pendientes, nunca un saldo viejo del JSON.

Para evitar sobrescribir registros inmutables, la futura implementación puede conservar recibos y bindings canónicos como registros append-only en **el mismo ledger**, referidos por hash. El padre ya es verificable mediante su propio input/registro. El registro agregado `OC3_AUTHORITIES.json` se publicará una vez como snapshot de la cadena validada, sin reescribir una versión padre anterior; el plan final se produce después de la promoción. Esta corrección de orden de publicación pertenece al cambio de binding, no autoriza reescrituras de evidencia previa. No se añaden archivos de ejecución en esta entrega.

## 7. Manifiestos finales

Solo después de la resolución determinista se crean prospectivamente:

- `oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv`;
- `oc3/INPUTS/OC3_INPUT_MANIFEST.json`.

El CSV tiene **exactamente** estas columnas y este orden:

```text
region,brickname,development,holdout_disjoint,evidence_ref
```

Dos filas, orden fijo south y north; strings booleanos `true`; UTF-8 sin BOM, separador coma, quoting CSV determinista y LF. SHA-256 sobre todos los bytes, incluido LF final. `evidence_ref` liga la selección/exclusión prospectiva. `development=true` para ambos. `holdout_disjoint=true` significa exclusión confirmatoria por política aplicada, **no una comparación empírica contra un holdout abierto**. Si esa exclusión no puede hacerse vinculante, no escribir true ni promover.

El input final conserva las restricciones/esquemas de campos técnicos, rights y resources del preflight, con extensión **explícita y versionada** para los enlaces de esta enmienda: padre bootstrap, metadata receipt, CSV, autoridades, implementación, entorno, release issues, alcance de derechos, recursos finales exactos y saldo con watermark. Estos enlaces son obligatorios, no campos extra tolerados silenciosamente por el esquema viejo. La versión concreta debe fijarse y probarse antes de uso; el código actual no la implementa.

El input final sigue el sello canónico y whole-file SHA-256 de §3, coherente con el preflight. No contiene Galaxy Zoo ni variables de validación física. El plan final reproduce esas identidades sin volver a elegir los bricks. Recursos PSF permanecen diferidos al manifiesto ligado a ubicaciones selladas, con la reserva y reglas científicas ya congeladas; aquí no se inventan coordenadas, URLs ni respuestas PSF.

## 8. Dos niveles de contabilidad

Se mantienen los máximos globales originales y se anida METADATA_BOOTSTRAP:

| Dimensión | GLOBAL OC-3 | METADATA_BOOTSTRAP |
|---|---:|---:|
| Body bytes | 1,610,612,736 (1.5 GiB) | 50,331,648 (48 MiB) |
| HTTP requests totales | 200 | 48 |
| Allowance metadata/documentos, dentro de bytes globales | 64 MiB | Todo byte de bootstrap debita este allowance y su cap de 48 MiB |
| Allowance PSF, dentro de bytes globales | 54 MiB; máximo 1 MiB por posición/banda lógica | Ninguna solicitud PSF |
| Bricks / ubicaciones | 2 / 6 | Resolver 2 bricks; no adquirir/seleccionar las 6 ventanas |
| Disco | 4 GiB incremental global | 256 MiB atribuibles al bootstrap, además del tope global |
| IO local acumulado | 8 GiB | 512 MiB atribuibles al bootstrap |
| Cómputo activo acumulado | 1800 s | 300 s |
| Wall/invocación | 3600 s | 900 s |
| Reintentos por recurso | 2 adicionales | Los mismos; no un cupo adicional |
| Concurrencia | 1 | 1 |
| RAM / threads / GPU | 2 GiB / 1 / ninguna | Sin ampliar estos límites |

Para toda dimensión x con cap aplicable se deben cumplir simultáneamente:

```text
used_stage(x) <= cap_stage(x)
used_global(x) <= cap_global(x)
```

Bytes, requests, IO y cómputo son acumulados a través de reanudaciones. Wall-clock conserva su ámbito explícito por invocación; disco/RAM/concurrencia se controlan como ocupación/capacidad en su ámbito, no como una falsa suma de muestras. Toda operación atribuible al bootstrap consume también el global correspondiente. Costes compartidos se cargan conservadoramente una vez, sin esconderlos al pasar de etapa.

Los caps de etapa **no redefinen los globales**. Terminar la etapa no devuelve bytes/requests realmente gastados ni resta su IO/cómputo. Saldo no usado de metadata no crea un presupuesto adicional. Los 64 MiB metadata y 54 MiB PSF están incluidos en el global, no sumados a 1.5 GiB. C0 no aporta saldo.

La CLI futura distinguirá `--max-global-...` de `--max-stage-...`, o un mecanismo tipado de claridad equivalente. Para esta especificación se adoptan esos prefijos, sin conflicto observado con la arquitectura argparse. Un argumento podrá bajar un límite de su ámbito, nunca subir un global previamente sellado. Restricciones adicionales posteriores se registrarán de forma monotónica, sin editar el padre ni recuperar un cap menor ya aceptado.

Ejemplo normativo, no ejecución: stage bytes=48 MiB y global bytes=1.5 GiB desde el inicio. Gastar 40 MiB en bootstrap deja como máximo 1496 MiB globales, no 1536 MiB nuevos. Pasar a otra etapa con el global que siempre fue 1.5 GiB **no es restaurar/aumentar** un global de 48 MiB: nunca se lo redujo a ese valor. Si el usuario sí bajó explícitamente el global, ese global menor persiste. Reabrir el bootstrap mantiene su stage_id, consumo y restricciones; no se obtiene otro cupo de 48 MiB.

Se elimina para esta planificación la ambigüedad de los antiguos `--max-bytes`/`--max-requests`: no se interpretan silenciosamente como stage ni como global. Una interfaz de compatibilidad deberá rechazarlos cuando el ámbito sea ambiguo y explicar el prefijo requerido. No se modifican los caps numéricos ni se permite un aumento mediante un alias.

## 9. Reservas, identidad del ledger y cache

Todas las solicitudes metadata usan reserva-antes-de-request. La reserva es atómica en **ambos niveles**: comprobar cap de recurso, etapa, global, allowance metadata, request/retries/concurrencia antes de cualquier envío. Si falla cualquiera, no sale HTTP ni queda una reserva unilateral. Desconocer Content-Length no habilita lectura ilimitada.

El único ledger debe exponer al menos:

- identidad persistente de corrida/ledger y vínculo a su raíz de ejecución;
- binding padre inmutable y binding hijo solo si hubo promoción;
- counters/caps globales, counters/caps por stage_id y reservas pendientes;
- intentos de recurso con método, identidad estable, secuencia y etapa;
- cuerpos completos, parciales y fallidos, bytes leídos y consumo de retries;
- identidades inmutables de cache/fragmentos y checksums;
- registros de selección, desarrollo, preparación y promoción única, con watermark/hash verificables.

Cada byte recibido cuenta globalmente y en su etapa activa; también cuerpos de error y fragmentos abandonados. Cada request cuenta, incluidos HEAD, fallos y reintentos; no se permite seguir redirects no enumerados. La categoría de HEAD no puede transformarse en GET para eludir la lista autorizada. La identidad de intentos no puede cambiar al reanudar/promover para reiniciar retries. Continúan timeout 30 s, backoff 2/5 s y terminación si Retry-After supera 60 s; sin polling ni loops ilimitados.

Liberar una reserva no utilizada es distinto de reembolsar consumo real. Si un crash deja bytes inciertos, mantener la carga conservadora de la reserva según la regla previa; no ponerla a cero. Un recurso completo verificado se reutiliza sin HEAD/GET de recreación. Fragmentos y conflictos se preservan; un archivo completo no se afirma validado solo por hash de fragmentos.

La promoción conserva **la misma identidad y el mismo ledger**; no abre otro, no copia contadores manualmente, no borra intentos/HTTP ni migra saldo a cero. Abrir una nueva base junto a artefactos de esa corrida o presentar un hijo con otra identidad debe fallar cerrado. Reabrir la misma base con su identidad/bindings íntegros para continuar no constituye un segundo ledger. Un hash del archivo SQLite mutable no sustituye estas verificaciones de identidad e historia.

## 10. Derechos y entorno como prerrequisitos reales

Los manifiestos solo pueden autorizar el alcance local científicamente revisado:

| Categoría | Regla conservada |
|---|---|
| SCIENTIFIC_USE | Documentado/revisado, con acknowledgment aplicable si se publica |
| PUBLIC_ACCESS | Documentado/revisado; acceso público no implica licencia ilimitada |
| IMAGE_REPRODUCTION | Alcance separado de capas/renderizados y su atribución |
| FITS_OR_DERIVED_REDISTRIBUTION | DISABLED / UNRESOLVED; redistribution=false |

Si la evidencia revisada no sostiene afirmativamente análisis/preservación local necesarios, **no se inicia metadata acquisition**. No se escribe un flag true para satisfacer software. Redistribución deshabilitada no bloquea por sí misma un uso local que sí esté documentado, pero tampoco suple un permiso local desconocido. No se amplía el alcance jurídico mediante esta enmienda.

No hay metadata request hasta que el entorno independiente de OC3_ENVIRONMENT_SETUP.md haya sido **realmente** preparado/verificado. El padre liga Python exacto/build, versiones requeridas/importadas, fingerprint, installation-report hash, preparation-receipt hash, replay sintético independiente y su evidencia de cero red real. Se mantienen Python 3.12.x, NumPy 2.5.3, Astropy 8.0.1, PyArrow 25.0.1 mientras no exista otra modificación prospectiva autorizada. Python 3.14 del sistema no sustituye 3.12.x; `c0/.venv` histórico no vale como entorno de producción.

La implementación de 002 cambiará el hash de código. Por ello un replay anterior de solo la versión histórica no puede autenticar la versión corregida: se exige replay de la suite revisada completa, con regresión de la cobertura previa y los casos de §12, ligado a su hash exacto. El número de pruebas resultante se declarará prospectivamente en la futura entrega de implementación; no se altera retrospectivamente el 100/0/0 histórico, ni se fuerza un recibo de 100 para omitir pruebas nuevas. La evidencia de preparación del entorno se conserva, y el recibo de replay nuevo identifica expresamente la versión corregida. No se ejecuta ninguno ahora.

## 11. Contrato CLI prospectivo

Se mantienen los siete subcomandos principales: `plan`, `acquire-aux`, `select`, `acquire-fixed`, `analyze`, `verify`, `finalize`.

`plan` tendrá dos modos explícitos y mutuamente excluyentes. Sus selectores de input no pueden quedar simultáneamente activos por defaults de argparse. No se detectó conflicto arquitectónico que obligue a cambiar los nombres propuestos; la implementación futura debe resolver explícitamente el default actual de --inputs y rechazar ambigüedad.

### A. Bootstrap metadata mode

Interfaz conceptual **NO IMPLEMENTADA / NO EJECUTAR**:

```text
python3 oc3/oc3_pilot.py plan
  --bootstrap-inputs oc3/INPUTS/OC3_METADATA_BOOTSTRAP_MANIFEST.json
  --resolve-metadata
  --execute-network
  --max-global-bytes 1610612736
  --max-global-requests 200
  --max-stage-bytes 50331648
  --max-stage-requests 48
  --resume
```

No requiere input final ni CSV de desarrollo. Valida padre, entorno/replay, derechos y autorización; solo puede recuperar los roles metadata permitidos. Aplica simultáneamente caps globales y de etapa. Puede resolver la pareja y registrar desarrollo, preparar las evidencias y completar la promoción única validada. No descarga mapas, no selecciona S1–N3 y no obtiene PSF.

El modo debe soportar --dry-run/--offline: cero red y cero mutación de evidencia; ausencia de inputs se informa sin fabricarlos. Offline jamás activa un fallback online. Un resume offline no puede resolver una dependencia faltante mediante red. Si ya hubo promoción, resume valida el hijo existente y termina/reproduce el estado sin otro commit de promoción ni nueva selección.

### B. Final plan mode

Interfaz conceptual **NO IMPLEMENTADA / NO EJECUTAR**:

```text
python3 oc3/oc3_pilot.py plan
  --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json
  --offline
```

Requiere input final, CSV y promoción padre→hijo completada y compatible con el mismo ledger. Reproduce el binding promovido y prepara/valida el plan de etapas posteriores. No llama de nuevo a choose_bricks, no muta manifiestos y no recupera metadata. --resolve-metadata pertenece solo al modo bootstrap y se rechaza en modo final.

La promoción no autoriza acquire-aux. Se presenta al humano el plan final, hashes, consumo/saldo y recursos exactos; solo una **autorización humana separada** habilita esa adquisición. No se implementa ni se entrega ahora un comando científico ejecutable. La corrección futura necesitará CLI help/dry-run/sentinels/exit codes y pruebas revisadas antes de autorizar red.

## 12. Pruebas sintéticas futuras obligatorias

La implementación de 002 debe añadir cobertura verificable para todos los casos siguientes, **sin red real y solo con fixtures sintéticos/locales**. Los recibos identificarán test, versión, resultado y evidencia; cero fallos/omitidas en la cobertura obligatoria antes de cualquier autorización metadata. No se ejecutan aquí.

| Nº | Caso mínimo y resultado exigido |
|---:|---|
| 1 | Bootstrap funciona sin manifiesto final; no lo fabrica para pasar |
| 2 | Bootstrap funciona sin CSV final de desarrollo; no usa allowlist provisional |
| 3 | Modo final exige ambos archivos y promoción compatible |
| 4 | Bootstrap rechaza GET de todos los tipos de mapa científico, incluso bajo etiqueta metadata |
| 5 | Bootstrap rechaza solicitudes PSF |
| 6 | URL no enumerada ni resoluble por un rol cerrado autorizado es rechazada; identidad literal se fija antes del request |
| 7 | Rechazo de descubrimiento recursivo/seguimiento fuera de los dos índices |
| 8 | Sur se elige solo del conjunto sintético elegible y corregido 9012 |
| 9 | Norte no hereda regla 9012 ni acepta DR9sv |
| 10 | Permutar orden de filas conserva la selección y sus hashes |
| 11 | Campos image/fuentes/morfología se rechazan y no influyen en selección |
| 12 | Fallo/inconveniencia posterior no reemplaza bricks |
| 13 | Registro permanente de desarrollo se crea al seleccionar y sobrevive a fallo posterior |
| 14 | Hijo liga hash/sello exactos del padre |
| 15 | Solo una promoción; segundo intento explícito falla cerrado |
| 16 | Promoción conserva una identidad de ledger |
| 17 | Promoción conserva counters globales y reservas/consumo pertinentes |
| 18 | Promoción conserva counters y stage_id metadata |
| 19 | Crash inmediatamente antes del commit permite reproducir/completar la misma preparación o parar; nunca otra pareja |
| 20 | Crash inmediatamente después del commit recupera el mismo hijo sin segunda promoción |
| 21 | Binding hijo incompatible produce parada por integridad |
| 22 | Intento de otro ledger para la misma promoción/corrida es rechazado |
| 23 | Caps globales y de etapa se imponen simultáneamente, con reserva atómica |
| 24 | Agotar stage cap no altera el global sellado |
| 25 | Completar etapa no reembolsa bytes/requests consumidos globalmente |
| 26 | Etapa posterior no reinicia consumo bootstrap ni retries |
| 27 | Flags stage-local no elevan ni redefinen caps globales; flags ambiguos se rechazan |
| 28 | Sello canónico y whole-file SHA-256 final deterministas y sin autorreferencias |
| 29 | CSV de desarrollo determinista, dos filas y columnas exactas |
| 30 | Semántica holdout_disjoint se prueba con política prospectiva; cualquier intento de abrir holdout falla |
| 31 | Falta/cambio de fingerprint, preparación o replay aplicable bloquea network mode |
| 32 | Falta evidencia de derechos de análisis/cache local bloquea bootstrap antes de red |
| 33 | Redistribution permanece false; eso no bloquea local use afirmativamente permitido ni inventa su permiso |
| 34 | Offline/dry-run bootstrap produce cero DNS/socket/HTTP, cero evidencia nueva y cero decodificación científica |
| 35 | Conducta Amendment 001 T10 preservada: 999, PCG64/SeedSequence y golden output, omnibus, Holm, estados, lenguaje y guardas/generalización sin cambios |

La cobertura también debe incluir recursos dependientes reproducibles, límites de cuerpos HEAD/error, metadata cap global compartido, intentos fallidos/parciales y recuperación de reservas. Ninguna prueba es una observación DR9. No adaptar golden values, selección, umbrales ni ciencia para pasar pruebas de integración.

## 13. Semántica terminal y estado actual

Se conservan los cuatro desenlaces científicos, sin seleccionar ninguno ahora:

- `DR9_COADD_SUPPORTS_OBSERVATIONAL_CONTRACT_DRAFT`;
- `DR9_COADD_REQUIRES_NARROWER_SCIENTIFIC_DOMAIN`;
- `DR9_COADD_NOT_CURRENTLY_ADMISSIBLE`;
- `PILOT_INTEGRITY_FAILURE_STOP`.

También se conservan exactamente los cuatro estados de preflight, con la prioridad/reglas del preflight existente:

- `PREFLIGHT_READY_FOR_METADATA_RESOLUTION`;
- `PREFLIGHT_BLOCKED_ENVIRONMENT`;
- `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`;
- `PREFLIGHT_INTEGRITY_FAILURE_STOP`.

**Estado actual: PREFLIGHT_BLOCKED_ENVIRONMENT, con bloqueos de integración adicionales.** No existe aquí un entorno nuevo ni implementación corregida/replay. Escribir esta enmienda, o implementarla posteriormente, no asigna READY. Una revisión separada después de implementar/probar y preparar el entorno verificará todos los requisitos y la autorización concreta. No hay PENDING ni un nuevo terminal científico «bootstrap aprobado» que permita avanzar automáticamente.

## 14. Precedencia limitada

Amendment 002 prevalece sobre el contrato original únicamente para:

1. orden de bootstrap metadata anterior al manifiesto final;
2. separación de bindings bootstrap/final;
3. promoción inmutable padre→hijo, su publicación y recuperación;
4. límites metadata anidados en el mismo ledger global;
5. modos explícitos de planificación CLI necesarios para eliminar circularidad.

Los enlaces de entorno/replay, recursos dependientes y pruebas de integración de esta enmienda instrumentan esos cinco cambios; no reescriben el experimento. El inventario prospectivo incorpora OC3_METADATA_BOOTSTRAP_MANIFEST.json y las relaciones de binding descritas; los recibos internos no autorizan una proliferación libre de productos científicos.

Amendment 001 sigue siendo autoridad para inferencia T10, interpretación de guardas PSF y generalización de dos bricks. Permanecen todos los slots S1–N3 y su selección, productos, no-preprocessing/no-fuga, lógica PSF, semántica T01–T12 y condiciones de los cuatro desenlaces científicos. Dos bricks no establecen representatividad DR9; ninguna promoción es un PASS de preservación morfológica.

No se amplían límites globales, releases, regiones, bandas, permisos de uso o autorización humana. C0/E-OC1 permanecen cerrados con sus resultados previos. Los documentos congelados se conservan como tales; cualquier incompatibilidad fuera de esta precedencia requiere revisión prospectiva, no una modificación tácita del código para acomodarla.

## 15. Entrega y conservación

Esta tarea crea **exactamente un archivo**: `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md`. No modifica código, tests, lock, README, informes, preflight, setup ni ninguna autoridad previa. Solo se hicieron lecturas/revisión local y comprobaciones de integridad; no se ejecutaron OC-3 ni pruebas nuevas, ni se creó entorno o instaló paquete alguno.

Cero solicitudes reales de red, cero adquisición de metadata/FITS/píxeles/PSF/catálogos/datos astronómicos. Ningún manifiesto de producción creado, ningún brick DR9 elegido, ningún resultado observacional A/B/C/D asignado. No se reparó ni inicializó Git.

**OC-3 REMAINS NOT STARTED.**
