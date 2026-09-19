# OC-3 — preflight de ejecución

Fecha: 2026-09-18. Alcance: preparación documental autorizada, sin ejecución del piloto. Este documento no modifica las autoridades congeladas ni autoriza red. Se acompaña de `OC3_ENVIRONMENT_SETUP.md`.

**Estado actual: PREFLIGHT_BLOCKED_ENVIRONMENT.** No existe `oc3/.venv` ni un replay de pruebas en un entorno independiente. Existen además bloqueos de manifiesto/integración descritos en C y F; resolver el entorno no los elimina. No se asigna READY ni un desenlace observacional A/B/C/D.

## A. Autoridad documental

Los cinco SHA-256 exigidos coinciden con los archivos locales:

| Archivo | SHA-256 verificado |
|---|---|
| MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| OC3_IMPLEMENTATION_REPORT.md | `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864` |

AGENTS leído, SHA-256 `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222`. Se revisaron README, lock, implementación y pruebas OC-3. El hash agregado de implementación sigue siendo `cf01a2774237ca98bf83dab01dda39a728f803e72e93c6796f214d20dcc6d57f`. Seed, especificación/addendum C0 y OC-2 se conservan como autoridades/antecedentes aplicables; C0 y E-OC1 no se reabren.

MIPS gobierna la intención de preservación. La especificación OC-3 gobierna el piloto; Amendment 001 prevalece solamente en inferencia T10, interpretación de guardas PSF y generalización de dos bricks. El informe de implementación es evidencia histórica de software, no prueba del survey. Una discrepancia de hashes detiene el preflight; no se actualizan hashes esperados para eludirla.

### Familia observacional fijada

Solo Legacy Surveys **DR9 completo**: `north = BASS/MzLS`, `south = DECaLS`, bandas g/r/z. Los únicos productos científicos coadd futuros son `image`, `invvar`, `nexp`, `maskbits` óptico y `psfsize`. Se admiten headers técnicos FITS y tablas técnicas de procedencia brick/CCD dentro del alcance ya autorizado por la especificación. PSF coadd únicamente después de seleccionar y sellar ubicaciones, con vínculo independiente al mismo brick/región/generación/banda.

No se añaden model, blobmodel, depth, galdepth, chi2, JPEG, catálogos de fuentes Tractor, exposiciones, DR9sv, DR5, DR10 ni otro survey como sustitutos. La primera etapa descrita aquí no recupera ningún mapa ni PSF, tampoco mediante un pequeño GET/Range de un FITS de píxeles. Un HEAD para tamaño de un recurso futuro no es una lectura de su header FITS y no valida su semántica.

### Hechos documentales y procedencia

**Límite de esta revisión:** cero consultas externas. Se usan el registro documental OC-2, el snapshot local de acknowledgment y los hechos oficiales aportados explícitamente en la solicitud de este preflight. Las referencias siguientes identifican la fuente oficial; no constituyen una consulta viva realizada ahora, ni un snapshot DR9 recién sellado. Los detalles adicionales aportados por la solicitud —estructura del repositorio, HDU1 y disponibilidad pública— quedan identificados como tales. Disponibilidad actual, URLs finales, tamaños, cabeceras y checksums de los recursos particulares todavía no están comprobados.

| Hecho que se registra | Fuente oficial y evidencia disponible |
|---|---|
| Grids coadd de plano tangente de 3600×3600; escala nominal 0.262 arcsec/píxel | [DR9 files, Image Stacks](https://www.legacysurvey.org/dr9/files/), [DR9 description, Image Stacks](https://www.legacysurvey.org/dr9/description/). OC-2 D1/D2 y hechos aportados en la solicitud |
| image es un coadd ponderado por inverse variance | DR9 files / description, referencias D1/D2 |
| Lanczos-3 se usa en el remuestreo upstream de construcción del coadd | [DR9 description](https://www.legacysurvey.org/dr9/description/), D2; no certifica un operador posterior de cutouts |
| invvar corresponde al coadd y se basa en la suma de inverse variances de entradas | [DR9 files](https://www.legacysurvey.org/dr9/files/), D1 y solicitud; no es la covarianza completa ni una prueba de independencia |
| maskbits es el bitmask óptico espacial de problemas por píxel, documentado en HDU1 | [DR9 files](https://www.legacysurvey.org/dr9/files/), [DR9 bitmasks](https://www.legacysurvey.org/dr9/bitmasks/), D1/D3; HDU1 aportado explícitamente en esta solicitud. Se deberá confirmar el HDU lógico/físico real, sin incorporar bits de releases posteriores |
| nexp cuenta exposiciones contribuyentes por píxel apilado | DR9 files y [DR9 issues](https://www.legacysurvey.org/dr9/issues/), D1/D4; no se sustituye por NOBS de Tractor |
| psfsize es el promedio ponderado de FWHM PSF, en arcsec por píxel apilado | DR9 files, D1; es un descriptor escalar, no un kernel PSF |
| Repositorio público DR9, ramas north/south, survey-bricks.fits.gz, survey-bricks-dr9-north.fits.gz, survey-bricks-dr9-south.fits.gz y manifiestos SHA-256 de release | [Repositorio oficial NERSC DR9](https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/), [DR9 files, Summary Files](https://www.legacysurvey.org/dr9/files/). Hechos aportados en esta solicitud; no se listó el servidor ni se descargó ninguno de esos FITS |
| 1691 bricks sur fueron reprocesados por corrupción; las reducciones corregidas tienen RELEASE=9012 en vez de 9010; existe lista oficial de afectados | [DR9 issues](https://www.legacysurvey.org/dr9/issues/), OC-2 D4 y solicitud. No se recuperó la lista FITS; pertenencia de un brick aún no determinada |
| DR9sv no sustituye al DR9 completo | Regla explícita de esta solicitud y alcance DR9 de la especificación; no se buscará una ruta alternativa DR9sv |

Antes de armar un manifiesto de red deben existir referencias documentales revisadas que identifiquen literalmente los enlaces oficiales y su alcance. No se inventan aquí el nombre del FITS de afectados ni los nombres de los manifiestos SHA-256. No se atribuyen hashes de snapshots inexistentes. Si las referencias locales/aportadas no bastan para resolver una URL, permanece bloqueada; una consulta documental futura requiere autorización explícita, contabilización y alcance propio, sin píxeles ni crawling.

## B. Entorno de ejecución

Requisitos previos: Python 3.12.x independiente de C0, NumPy 2.5.3, Astropy 8.0.1 y PyArrow 25.0.1, versiones efectivamente importadas verificadas, ausencia de site-packages heredados, registro de dependencias transitivas/plataforma/binarios y fingerprint del entorno. Python 3.12.14 es el patch histórico probado, no una justificación para usar el ejecutable de `c0/.venv`.

El replay humano debe completar **100/100, 0 fallos, 0 omitidas**, con red bloqueada por el runner y fixtures sintéticos, conservando un log nuevo separado del histórico. El dry-run debe informar authorities_verified=true, network=false, evidence_mutation=false y scientific_execution=NOT_STARTED; la ausencia de manifiesto puede seguir apareciendo. Ni un dry-run exitoso ni los 100 tests históricos equivalen a READY. Los comandos exactos, pins, hashes y límites de reproducibilidad están en `OC3_ENVIRONMENT_SETUP.md`.

## C. Manifiesto metadata-only y bloqueo de integración

**Hallazgo en código, no inferencia sobre DR9:** `workflow.read_inputs` exige allowlist y hash; `build_plan` llama a `choose_bricks` antes de adquirir metadata. `bind_authorities` incluye el manifiesto final/allowlist; `Ledger.__init__` rechaza otro binding; el plan y registro de autoridades se escriben inmutables. Por tanto, la implementación actual NO permite comenzar sin candidatos y sellar después el manifiesto final como solicita este preflight. Los tests de plan utilizan metadatos sintéticos ya resueltos y no prueban ese arranque desde cero. Tampoco existe un lector validado de las tablas proveedor para producir la proyección técnica ni soporte HEAD en HTTPTransport.

No se ejecutará el antiguo handoff `plan --resolve-metadata`, ni se crearán candidatos ficticios o una allowlist temporal para sortear el problema. El informe de implementación queda intacto como documento histórico; aquí se registra su límite operativo.

### Contrato de arranque requerido, todavía sin implementar

Antes de cualquier primer comando metadata-only, una tarea posterior expresamente autorizada deberá implementar y probar una entrada de planificación previa a la selección, distinta del manifiesto final de productos. Debe contener:

- hashes de autoridades, estos dos documentos, código revisado y fingerprint/replay del entorno;
- release/regiones/bandas fijas y reglas de selección, sin ningún sujeto científico;
- lista cerrada de recursos metadata: URL literal, host autorizado, origen documental del enlace, tipo, tamaño exacto si existe o cota estricta, checksum proveedor si existe y esquema técnico permitido;
- contratos de las únicas referencias dependientes permitidas para listar recursos de los dos bricks elegidos; cada URL concreta se revisa y registra antes de enviarla;
- límites de etapa además de los globales, permisos de uso local documentados y ámbito de autorización humana;
- política prospectiva INSTRUMENTAL_DEVELOPMENT y exclusión confirmatoria de D/G.

El nombre/path de esa entrada y las nuevas interfaces deberán fijarse en la tarea de integración, sin sobrecargar a escondidas el esquema del input final. Esta tarea no crea archivos JSON/CSV ni una CLI inexistente.

El ledger global se inicializará una sola vez bajo el binding de arranque. El sellado del input final será un **hijo inmutable con hash del padre, recibos metadata y contadores**, registrado por una transición validada; no una sustitución libre del binding. Todos los recursos ya obtenidos seguirán ligados al padre. Se requieren pruebas de autoridad incompatible, doble promoción, reanudación de cada lado de la transición y conservación exacta de bytes/requests/identidades. Prohibidos un ledger nuevo para borrar el coste inicial o un UPDATE manual de binding. La compatibilidad con los artefactos congelados se revisará antes de implementar; si exige cambiar una autoridad, se necesita una enmienda prospectiva explícita.

### Primera etapa acotada: diseño, no ejecución

Finalidad exclusiva: resolver un candidato norte y uno sur mediante geometría/cobertura, y calcular un plan acotado de recursos. Orden determinista de dependencias; ninguna selección de ventanas ni decodificación de imágenes. Inventario lógico máximo:

| Orden / recurso | Uso permitido | Cota máxima por cuerpo, no tamaño observado |
|---|---|---:|
| SHA-256 oficial de release aplicable a raíz | Integridad de summaries; solo enlaces explícitos verificados | 1 MiB |
| SHA-256 oficial aplicable a north | Integridad de cobertura/recursos norte | 1 MiB |
| SHA-256 oficial aplicable a south/9012 | Integridad de cobertura/corrección; no mezclar generaciones | 1 MiB |
| survey-bricks.fits.gz | Identidad y geometría de bricks | 16 MiB |
| survey-bricks-dr9-north.fits.gz | Cobertura técnica DR9 g/r/z norte | 8 MiB |
| survey-bricks-dr9-south.fits.gz | Cobertura técnica DR9 g/r/z sur | 16 MiB |
| Lista FITS oficial de los 1691 afectados/reprocesados | Pertenencia documentada al subconjunto corregido 9012 | 2 MiB |
| Índice técnico oficial del único brick sur seleccionado | Enumerar exactamente sus 13 productos permitidos, tamaños si exactos | 512 KiB |
| Índice técnico oficial del único brick norte seleccionado | Mismo alcance para norte | 512 KiB |
| HEAD de hasta 26 recursos coadd ya identificados | Solo tamaño HTTP si no está disponible exactamente en metadata anterior; nunca GET del mapa | 64 KiB por intento para un eventual cuerpo de error; cuerpo HEAD exitoso esperado cero |

Los siete primeros roles se deduplican por URL/generación idénticas; un mismo manifiesto puede cumplir varios roles y se descarga una sola vez. Si se necesitan más de tres manifiestos distintos, si un manifiesto no cubre lo declarado o si una cota no alcanza, bloquear y revisar antes de transferir; no dividir/cambiar el plan automáticamente. El SHA-256 local acredita bytes recuperados, no autenticación independiente del proveedor ni cobertura de un archivo que no figura en su manifiesto.

Los dos índices son consultas directas acotadas tras el hash ordering; no crawling recursivo. Se filtran enlaces a la familia exacta ya autorizada; no se siguen enlaces a fuentes/Tractor. Si el enlace/nombre/generación no se resuelve de manera verificable, no se construye por intuición. Los HEAD se hacen solo cuando falta tamaño exacto: una etiqueta redondeada de directorio no basta. Se requiere soporte HEAD revisado antes de autorizar esta ruta. No se lee el header FITS de un mapa mediante Range. La semántica/layout de sus bytes seguirá pendiente hasta una adquisición posterior autorizada.

Plan de requests sin reintentos: como máximo 9 GET distintos + 26 HEAD condicionales = 35; si los índices suministran tamaños exactos, se omiten los HEAD y bastan hasta 9. No se consultan snapshots documentales extra en esta etapa: deben quedar revisados entre los prerrequisitos. No se añade una tabla CCD global si no es necesaria para esta finalidad. Un checksum que no existe/no cubre un recurso se registra como tal, sin inventarlo; la evidencia restante debe permitir la integridad/identidad exigida o se bloquea.

El contenido de tablas técnicas puede contener columnas no usadas. El futuro adaptador debe validar el esquema completo contra una allowlist del formato oficial antes de leer valores, aceptar únicamente columnas técnicas aprobadas y rechazar nombres inesperados sin imprimirlos. No se permite usar recuentos de fuentes, magnitud, color, TYPE, valores físicos, etiquetas o inspección visual. No se puede proyectar silenciosamente una tabla de fuentes hacia la allowlist. Si no existe un recurso técnico pequeño que satisfaga estas restricciones, la etapa no está habilitada.

**No hay un comando de red ejecutable autorizado en este documento.** Faltan los enlaces literales aún no resueltos, el esquema de proveedor y la integración anterior. El diseño fija operaciones y cotas exactas, pero no finge que esas entradas pendientes ya forman un manifiesto sellado. Resolver ese bloqueo es condición de READY, no una acción de red implícita de este preflight.

## D. Allowlist instrumental y sellado posterior

Las ubicaciones OC-3 son desarrollo instrumental, no galaxias/sujetos. No se abrirá ninguna población Galaxy Zoo para construir elegibilidad. No se ha acreditado aquí la existencia de un holdout científico final; se adopta la siguiente regla prospectiva, vinculante antes de recuperar metadata:

**Todo brick elegido por OC-3, todas sus ventanas OC-3 y todos los productos observacionales directos de esos bricks serán permanentemente INSTRUMENTAL_DEVELOPMENT y se excluirán de evaluación morfológica confirmatoria futura.** Esto incluye vistas del mismo territorio y debe propagarse a futuras asignaciones de splits, sin consultar ahora el holdout. No se elimina esa exclusión porque un producto resulte inútil. Si apareciese un conflicto con un holdout previamente congelado, detener/revisar la partición; no abrir etiquetas ni reemplazar el brick para ocultarlo.

Secuencia después de la futura recuperación metadata-only, con sus bytes/hash/HTTP/UTC ya registrados:

1. Validar identidades y geometría; construir el conjunto técnico de candidatos con cobertura g/r/z demostrada por documentación y columnas permitidas. No imponer umbrales de recuento de fuentes, seeing, profundidad o conveniencia no congelados. Un NEXP resumen solo puede apoyar cobertura si su semántica oficial es conocida; no es un recuento de fuentes.
2. Sur: intersecar cobertura técnica, geometría y lista oficial corregida 9012; comprobar que la procedencia indica corrección y no solamente una cadena en el nombre. Norte: cobertura/geometría DR9 y generación documentada, sin heredar 9012 del sur.
3. Ordenar por SHA-256 de UTF-8 `OC3-v1|brick|<region>|<brickname>` ascendente; desempatar por brickname ASCII. Tomar el primero de cada región. Guardar el conjunto candidato proyectado y su hash/orden antes de reducirlo a dos. Si falta una clase elegible, registrar bloqueo; no buscar otra release o estrato.
4. Registrar permanentemente ambos bricks como INSTRUMENTAL_DEVELOPMENT. No reemplazarlos por problemas posteriores de datos, estratos, costes, máscaras o apariencia. No ejecutar el selector S1–N3: requiere auxiliares que esta etapa prohíbe adquirir.
5. Resolver y revisar identidades exactas de los 26 recursos nativos futuros: por brick image/invvar/nexp/psfsize en g/r/z y un maskbits óptico. URL solicitada/canónica, región, generación, release, banda, producto, HDU documentado y límites de tamaño deben tener evidencia; HDU real y contenido aún deberán verificarse. `resource_identity` liga URL/generación/tipo y claves técnicas; no certifica científicamente esa identidad. PSF permanece diferida hasta ubicaciones selladas, reservando su presupuesto sin inventar coordenadas.
6. Generar **solo entonces** OC3_DEVELOPMENT_BRICKS.csv, columnas exactas `region,brickname,development,holdout_disjoint,evidence_ref`. Las dos filas definitivas tendrán development=true. `holdout_disjoint=true` significa exclusión confirmatoria prospectiva aplicada por política, NO comparación empírica contra un holdout inexistente o abierto; evidence_ref debe enlazar esta política y el registro de selección/exclusión. Si esa exclusión no puede hacerse vinculante, no escribir true.
7. Sellar el CSV como bytes UTF-8 con orden fijo y newline registrado; calcular SHA-256. Generar OC3_INPUT_MANIFEST.json con el hash exacto del CSV, proyección técnica y linajes, derechos locales limitados, redistribución deshabilitada, issues, recursos/cotas y hashes de autoridades/código. Su sello es SHA-256 del JSON canónico UTF-8, claves ordenadas, separadores `(',', ':')`, ensure_ascii=False, allow_nan=False, excluyendo solo el campo superior `sealed`. Conservar además SHA-256 del archivo final, que es distinto conceptualmente del sello canónico.
8. Verificar offline la reproducción de orden/identidades/sellos, promover el hijo mediante el mecanismo revisado de C conservando el ledger, y presentar el plan/coste restante al humano. **Solo después puede solicitarse autorización separada para acquire-aux.**

No hay nombres de bricks elegidos en este documento ni se creó allowlist/input de producción. La exclusión de dos bricks no demuestra representatividad de DR9 ni valida un futuro contrato morfológico.

## E. Derechos y semántica de uso

Se mantienen tres afirmaciones documentales diferentes:

| Categoría | Evidencia y alcance | Lo que no permite inferir |
|---|---|---|
| SCIENTIFIC_USE | [Legacy Surveys acknowledgment](https://www.legacysurvey.org/acknowledgment/) prescribe agradecimientos para publicaciones científicas que usan sus datos | Una licencia universal sin condiciones para cualquier FITS o derivado |
| PUBLIC_ACCESS | El repositorio de datos cosmológicos NERSC describe los datasets Legacy como públicos y ofrece descarga de archivos individuales; hecho aportado en la solicitud, referencia [repositorio DR9](https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/) | Que acceso público equivale a redistribución ilimitada |
| IMAGE_REPRODUCTION | La página oficial de acknowledgment documenta CC BY 4.0 para las capas Legacy indicadas, con atribución requerida | Extender términos de capas/renderizados a todos los productos FITS científicos o datasets derivados |

Para acknowledgment existe evidencia local: `e_oc1/evidence/RIGHTS-DR5.html`, SHA-256 `adb1c5b41ad8aee7544a23d1b499b317d97c82222b4f69f65efa3ad13f6a9a1c`, URL solicitada/final oficial anterior, recuperación histórica UTC 2026-09-18T15:27:39.297632+00:00, HTTP 200, 21688 bytes, registrados en E_OC1_EVIDENCE_REGISTER.json. La declaración es general; el nombre histórico del snapshot no la convierte en licencia específica de todos los FITS DR9. No se alteró el resultado histórico de insuficiencia E-OC1.

Se puede proponer al humano adquisición científica local y cache privado como alcance operativo limitado, apoyado en uso científico/acceso público documentados; no se declara en esta tarea una licencia jurídica más amplia. Si se publica, cumplir el acknowledgment aplicable; para reproducir capas, cumplir además atribución de imagen. **Redistribución de FITS originales o datasets derivados de píxeles: DISABLED/UNRESOLVED**, sin activar automáticamente esa opción porque exista CC BY para imágenes.

`Run.acquire` exige actualmente `rights.analysis is True`, `rights.local_preservation is True` y evidence_refs; no exige redistribution=true. Esos booleanos deberán representar la revisión documentada del alcance de análisis/cache local efectivamente solicitado y su autorización, nunca la inferencia «público ⇒ licencia ilimitada». No rellenarlos para que pase el código. Si esa revisión no sostiene el uso local necesario, o si un componente exige derechos más fuertes, detener con PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS; no inferirlos ni instalar un bypass. No se necesita resolver redistribución para esta etapa si permanece deshabilitada.

## F. Presupuesto y contabilidad única

Límites prospectivos **de la etapa metadata**, incluidos errores/reintentos/cuerpos parciales:

| Recurso | Límite de etapa |
|---|---:|
| Bytes de cuerpos | 50,331,648 = 48 MiB |
| Solicitudes HTTP totales | 48; hasta 35 normalmente, menos si tamaños exactos evitan HEAD |
| Reintentos | Máximo 2 adicionales/recurso, siempre subordinados a los topes agregados |
| Concurrencia | 1 global |
| RAM objetivo | 2 GiB; no aumentar límite global |
| Disco incremental metadata/cache/partes/salidas | 256 MiB, además sujeto al espacio global disponible |
| IO local de la etapa | 512 MiB, además debitado al global |
| Cómputo activo de la etapa | 300 s, incluido en los 1800 s globales |
| Wall-clock de la etapa | 900 s por invocación, sin polling prolongado |
| Timeout / backoff | 30 s/request; 2 y 5 s para reintentos; Retry-After>60 s termina invocación |

Las cotas máximas iniciales de la tabla C suman 47.625 MiB si se necesitaran todos los HEAD; no son estimaciones de tamaños reales. La reserva se comprueba antes de cada solicitud, y los reintentos compiten por el saldo de 48 MiB: no se presupone que quepan. Un recurso cuyo tamaño excede su cota se rechaza antes de transferirlo. Un tamaño desconocido exige lectura acotada; nunca leer hasta agotar disco. URLs/final URL/UTC/status/bytes/ETag/checksum local/proveedor se preservan. No redirigir, no rehacer un GET completo ya validado, no fragmentar solicitudes para eludir topes.

Siguen intactos los límites OC-3 globales: 1.5 GiB, 200 requests, 64 MiB metadata/documentos, 54 MiB PSF, 2 bricks, 6 ubicaciones, 2 GiB RAM, un thread, cero GPU, 4 GiB disco incremental, 8 GiB IO, 30 min de cómputo y 60 min wall/invocación. Consumir los máximos de esta etapa dejaría como máximo 1488 MiB de cuerpos, 152 requests y 16 MiB del allowance metadata, no un presupuesto nuevo. Toda transferencia de esta etapa debita simultáneamente el mismo ledger global. No usar saldo C0.

**Bloqueo adicional observado:** los actuales `--max-bytes`/`--max-requests`/`--max-io-bytes` bajan caps persistentes globales por min, no límites temporales de etapa. No invocar esos flags con 48 MiB/48 requests para luego pretender ampliarlos. La integración pendiente debe imponer límites de etapa separados y acumulados sobre el mismo ledger, manteniendo intactos los globales. Debe probar que una promoción/reanudación no reinicia ni el consumo de etapa ni el global.

RuntimeGuard cuenta actualmente todo lo que está bajo `oc3`, incluido el entorno `.venv` y sus logs, al comprobar disco. La planificación posterior debe reservar ese espacio ya ocupado dentro del límite efectivo, no asumir que está excluido. La preparación de paquetes se registra separadamente como provisioning; no se presenta como tráfico del survey ni como ampliación de los límites OC-3.

## G. Lockbox y no-fuga

Aislar RAW_IMMUTABLE, TECHNICAL_INDEX y CONFOUND_AUDIT; no abrir/copiar/inventariar contenido de lockboxes para construir elegibilidad. Ningún sujeto Galaxy Zoo, predicción morfológica, variable física, magnitud/color, fuente Tractor o imagen visual puede influir en candidato, slot, parámetro o autorización. Rutas, symlinks, columnas y tipo de producto se validan antes de uso; campos inesperados se rechazan sin imprimir nombre/valor. Los tests históricos son evidencia de esa infraestructura, no validación del futuro adaptador de metadata.

La política de exclusión confirmatoria se aplica prospectivamente por geometría/identidad de brick y productos directos. Registrar evidencia de exclusión es necesario; afirmar que se «comprobó el holdout» sin hacerlo sería incorrecto y hacerlo aquí violaría el alcance. El lector metadata nuevo necesitará pruebas sintéticas de fuga y de rechazo de campos prohibidos antes de red real.

## H. Autorización y estados terminales del preflight

Se definen exactamente estos cuatro estados (no son los desenlaces científicos OC-3):

| Estado | Condición |
|---|---|
| PREFLIGHT_INTEGRITY_FAILURE_STOP | Autoridad/sello/identidad incompatible, evidencia alterada, fuga o contabilidad no fiable; prioridad absoluta, ninguna adquisición dependiente |
| PREFLIGHT_BLOCKED_ENVIRONMENT | Falta entorno independiente verificado, versiones/dependencias/fingerprint o replay sintético correcto. Registrar además cualquier bloqueo C–G sin ocultarlo |
| PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS | Entorno verificado, pero faltan manifiesto metadata literal/procedencia/esquema, integración de arranque/ledger/subpresupuestos, política de exclusión aplicable, alcance de uso local documentado o autorización humana concreta |
| PREFLIGHT_READY_FOR_METADATA_RESOLUTION | A–G satisfechos con evidencia real y H con autorización humana del comando concreto metadata-only, sus hashes, inventario y cotas. Habilita exclusivamente esa etapa; no auxiliares, ubicaciones, PSF ni análisis |

Orden de evaluación: integridad → entorno → manifiesto/derechos/restantes requisitos → READY. Se conservan todos los motivos aunque se comunique un único estado. No existe PENDING; faltar evidencia es un bloqueo explícito. Este documento asigna solamente PREFLIGHT_BLOCKED_ENVIRONMENT con bloqueos adicionales C/F; no ejecuta el motor científico ni cambia un Gate histórico.

La integración pendiente requiere una tarea de implementación autorizada y pruebas sintéticas específicas; no está autorizada por escribir estos documentos. Una vez cerrada, la etapa metadata será humana: procesa tablas técnicas y puede superar umbrales AGENTS. Antes de entregarle un comando real se requieren inventario literal, tamaños/cotas, log, outputs, sentinel, reinicio y exit codes implementados/revisados. No se publica aquí un comando ficticio. Autorización para preparar/instalar el entorno nunca equivale a autorización de red survey.

## Cierre de esta preparación

Se crean únicamente `OC3_EXECUTION_PREFLIGHT_SPEC.md` y `OC3_ENVIRONMENT_SETUP.md`. No se modifica código, README, lock, tests, informe de implementación ni autoridades. No se ejecutan tests nuevamente, paquetes, comandos de adquisición, plan --resolve-metadata, select, analyze, verify o finalize. Los 100 tests/0 fallos/0 omitidas y cero red del informe anterior siguen siendo evidencia histórica, no un replay nuevo.

**OC-3 remains NOT STARTED.** Cero adquisición astronómica, cero solicitudes reales al survey y cero descarga de píxeles. Ningún brick DR9 elegido; ningún input/allowlist de producción creado o sellado; ningún desenlace observacional A/B/C/D asignado.
