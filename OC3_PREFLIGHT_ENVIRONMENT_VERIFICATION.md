# OC-3 — verificación local del entorno y transición prospectiva de preflight

Fecha de verificación: 2026-09-18. Alcance: revisión documental/local de artefactos ya producidos. No se repitieron provisioning, instalación, replay sintético ni dry-run. No hubo acceso de red, consulta a proveedores de survey, adquisición DR9, selección de bricks, creación de manifiestos de producción, ledger ni promoción.

## 1. Resultado de integridad

### OBSERVED

Los archivos congelados y de gobierno conservan los siguientes SHA-256:

| Archivo | SHA-256 verificado |
|---|---|
| `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md` | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| `OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md` | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_IMPLEMENTATION_REPORT.md` | `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864` |
| `OC3_AMENDMENT_002_IMPLEMENTATION_REPORT.md` | `8ca240b5855c5196a78b8cfa2a1860a179b1d1f360a3f4aa95893f74f16da0f0` |
| `OC3_EXECUTION_PREFLIGHT_SPEC.md` | `6d5617ad5cc2b552d4a036a340077f4a727d06be4217e10d0f5b7408c9f6c28e` |
| `OC3_ENVIRONMENT_SETUP.md` | `fc39dba8f0d757ef0b342af01ff5710e21b56c1e6093c7969f910e02ad27c43d` |
| `AGENTS.md` | `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222` |

También se verificaron los antecedentes de gobierno del repositorio: `GALAXY_RESEARCH_SEED.md` = `6f1fa8e895b6921f02f2298ed17c8808f9fdec92a9f340c3042031b908a38995`, `CODEX_PHASE_C0_SPEC.md` = `1dfde2998fec1c03ac9f496d3bf813a9c12f3c9ce5ba8cc9f1f5cf3e21c290cb` y `C0_EXECUTION_DECISION_001.md` = `dffa854fd8df0df5063eebd9452b113423c6e3555aaf0c484844849be9621959`.

El agregado de implementación recalculado sobre los archivos Python actuales es `37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`. Coincide con `implementation_aggregate_expected` de `ENVIRONMENT.json`, con `implementation_aggregate` del recibo y con el valor autorizado.

### DOCUMENTED

Amendment 002 exige que cualquier bootstrap de producción ligue las autoridades, la implementación exacta, el entorno independiente y su replay. Una discrepancia en cualquiera de esos bindings asignaría `PREFLIGHT_INTEGRITY_FAILURE_STOP` antes de red.

### INFERRED

No se encontró una discrepancia de autoridad, implementación o evidencia ambiental. No corresponde `PREFLIGHT_INTEGRITY_FAILURE_STOP`.

## 2. Fingerprint y contenido del entorno

### OBSERVED

Se leyó `oc3/environment_setup/ENVIRONMENT.json`, SHA-256 de archivo `c8197a08121b72441382d8188c1d548a96b150aab296280d3361c42f757f5906`. Su `environment_sha256` embebido es:

`b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`

La serialización canónica del objeto `state` fue recalculada localmente y produjo exactamente el mismo fingerprint. La verificación completa del inventario instalado arrojó:

- 3.668 entradas esperadas y 3.668 observadas bajo la regla documentada que excluye `__pycache__` y `.pyc`;
- 0 archivos faltantes;
- 0 tamaños o SHA-256 discordantes;
- 0 entradas adicionales;
- hash del ejecutable, `requirements.lock` e `install-report.json` coincidentes con el estado sellado.

El entorno ocupa aproximadamente 403 MiB. `include-system-site-packages = false`. El prefijo efectivo es `/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv`; el `base_prefix` es `/home/jzsalinas/.local/share/uv/python/cpython-3.12.14-linux-x86_64-gnu`. Ni `base_prefix`, `sys.path`, los módulos importados ni los destinos inspeccionados pertenecen a `c0/.venv`.

La comprobación local de importación registró:

| Componente | Versión efectiva | Ubicación |
|---|---:|---|
| Python | 3.12.14 | `oc3/.venv/bin/python` |
| NumPy | 2.5.3 | dentro de `oc3/.venv/lib/python3.12/site-packages` |
| Astropy | 8.0.1 | dentro de `oc3/.venv/lib/python3.12/site-packages` |
| PyArrow | 25.0.1 | dentro de `oc3/.venv/lib/python3.12/site-packages` |

`install-report.json`, SHA-256 `0a241408a819878270031b15e58148ba0df749f80867b48b93924627af0ac23f`, registra siete wheels con versiones y hashes SHA-256: NumPy 2.5.3, Astropy 8.0.1, PyArrow 25.0.1, astropy-iers-data 0.2026.9.14.0.56.43, packaging 26.3, pyerfa 2.0.1.5 y PyYAML 6.0.3. Todos los archivos de distribución registrados proceden de `files.pythonhosted.org`. Esta es procedencia del provisioning de software, no procedencia de datos astronómicos.

`pip-check.log`, SHA-256 `9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09`, contiene exactamente el resultado satisfactorio `No broken requirements found.` El log de instalación termina en instalación exitosa de los siete paquetes; no se repitió ese proceso.

### DOCUMENTED

El preflight exige Python 3.12.x independiente de C0, las tres versiones fijadas, paquetes efectivamente importados, ausencia de site-packages heredados, procedencia/hash de instalación, fingerprint y replay ligado a la implementación Amendment 002.

### INFERRED

La evidencia observada satisface el prerrequisito ambiental congelado. El entorno no depende de `c0/.venv` y el bloqueo `PREFLIGHT_BLOCKED_ENVIRONMENT` queda **RESOLVED** para el agregado de implementación exacto verificado arriba. Esta conclusión no autoriza cambios de paquetes; cualquier cambio posterior invalida el binding y requiere nueva revisión/replay.

## 3. Recibo de preparación

### OBSERVED

`oc3/environment_setup/PREPARATION_RECEIPT.json` tiene SHA-256 exacto:

`0bce87d275ca71f6d6bef39f597fb354a3c1813c150830b395a1628d3b638654`

Los siete hashes de archivos enlazados por el recibo fueron recalculados y todos coinciden:

| Artefacto | SHA-256 |
|---|---|
| `ENVIRONMENT.json` | `c8197a08121b72441382d8188c1d548a96b150aab296280d3361c42f757f5906` |
| `install-report.json` | `0a241408a819878270031b15e58148ba0df749f80867b48b93924627af0ac23f` |
| `install.log` | `9ebabefc4d540826fe5cf02859a5f5b1f04985f9e693b0a24611a6ebc37497aa` |
| `pip-check.log` | `9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09` |
| `synthetic-tests.log` | `f68ccf3daa1ddc36fcf2a7c26be9a46199b4723d92d13c496bdd996388e4d033` |
| `synthetic-tests.json` | `667aa91a0a1b2fe8a4519d386f8e7240f4dcf15858babd2862efe28a8cd1cc41` |
| `dry-run.json` | `aff848e9de808c6011ca076d3fcc126d8e3eec01543803e6286f52318d419dd0` |

El recibo liga además Amendment 002, el informe de implementación Amendment 002, `requirements.lock`, el fingerprint, la implementación y las versiones esperadas. Declara `scope=OC3_ENVIRONMENT_PREPARATION_ONLY`, `oc3_scientific_execution=NOT_STARTED` y `preflight_ready_assigned=false`.

### DOCUMENTED

El recibo de preparación prueba el estado local preparado y sus dependencias; no sustituye manifiesto, derechos, procedencia de recursos ni autorización humana para red survey.

### INFERRED

El recibo es íntegro y compatible con la implementación actual. No asigna READY y no inicia OC-3.

## 4. Replay sintético y dry-run preservados

### OBSERVED

No se reejecutaron. Se verificaron los bytes ya preservados.

El replay almacenado informa:

- tests: 142;
- passed: 142;
- failed: 0;
- skipped: 0;
- real_network_requests: 0;
- synthetic_only: true.

El final del log confirma `Ran 142 tests`, `OK` y el mismo resumen. El dry-run preservado informa:

- `authorities_verified=true`;
- `network=false`;
- `evidence_mutation=false`;
- `fits_decoding=false`;
- `promotion=false`;
- `selection_persisted=false`;
- `scientific_execution=NOT_STARTED`;
- `status=OC3_DRY_RUN_OK`.

También conserva como faltante `oc3/INPUTS/OC3_INPUT_MANIFEST.json`, coherente con que no existe un input final de producción.

### DOCUMENTED

Amendment 002 requiere replay completo de la versión corregida, no reutilización del resultado histórico 100/0/0. Dry-run y replay son condiciones de software/entorno y no observaciones de DR9.

### INFERRED

El replay 142/0/0 y el dry-run satisfacen la evidencia ambiental y de software requerida. No satisfacen los prerrequisitos de manifiesto, derechos o autorización.

## 5. Transición prospectiva de estado

### DOCUMENTED

El orden terminal del preflight es integridad, entorno, manifiesto/derechos/requisitos restantes y finalmente READY. Con entorno verificado, pero sin manifiesto literal, procedencia/esquema, derechos locales o autorización concreta, el estado congelado aplicable es `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.

### OBSERVED

No existen archivos en los directorios de evidencia de producción `oc3/INPUTS`, `oc3/provenance`, `oc3/RAW_IMMUTABLE`, `oc3/TECHNICAL_INDEX` ni `oc3/reports`. En particular, no existen `OC3_METADATA_BOOTSTRAP_MANIFEST.json`, `OC3_INPUT_MANIFEST.json` ni `OC3_DEVELOPMENT_BRICKS.csv`. No existe ledger de ejecución OC-3, registro de promoción ni brick DR9 seleccionado.

### INFERRED

La transición prospectiva es:

`PREFLIGHT_BLOCKED_ENVIRONMENT` → **`PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`**

El bloqueo ambiental queda resuelto. **No** se asigna `PREFLIGHT_READY_FOR_METADATA_RESOLUTION`.

## 6. Inventario exacto de entradas para la siguiente etapa

### A. Entradas ya satisfechas

1. Hashes íntegros de las autoridades, Amendments 001/002, AGENTS y documentos de preflight/setup.
2. Implementación Amendment 002 y agregado exacto `37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`.
3. Entorno Python 3.12.14 independiente, paquetes fijados, inventario/fingerprint y procedencia de instalación.
4. Recibo de preparación y replay sintético 142/0/0 con cero red real.
5. Dry-run sin red, mutación, FITS, promoción ni selección persistida.
6. Familia congelada DR9 completo: south=DECaLS, north=BASS/MzLS, bandas g/r/z.
7. Reglas implementadas de selección técnica determinista, 9012 solo para south, no replacement, desarrollo instrumental permanente y exclusión confirmatoria prospectiva.
8. Esquema bootstrap v2, canonicalización, roles cerrados, firewall, promoción única y caps globales/METADATA_BOOTSTRAP implementados y probados sintéticamente.

### B. Evidencia documental disponible localmente

1. `OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md` registra referencias oficiales D1–D5 para archivos, descripción, bitmasks, issues y PSF de DR9, y conserva las limitaciones científicas/derechos.
2. `OC3_EXECUTION_PREFLIGHT_SPEC.md` documenta el inventario lógico máximo, cotas, productos prohibidos, nombres conceptuales de tablas resumen, política 9012 y referencias oficiales. Declara explícitamente que las URLs finales, tamaños, checksums, disponibilidad y esquemas concretos todavía no fueron comprobados.
3. `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` fija los roles permitidos, bindings, métodos, caps y requisitos de resolución dependiente.
4. `E_OC1_EVIDENCE_REGISTER.json` y `e_oc1/evidence/RIGHTS-DR5.html`, este último SHA-256 `adb1c5b41ad8aee7544a23d1b499b317d97c82222b4f69f65efa3ad13f6a9a1c`, preservan un snapshot oficial de acknowledgment/uso de imágenes. Su alcance es general/parcial y no constituye por sí solo una licencia completa para análisis/cache/redistribución de todos los FITS DR9.
5. Los artefactos ambientales verificados en las secciones 2–4 están disponibles para enlazarse por hash en el futuro padre.

Estas fuentes locales permiten formular el trabajo de revisión. No sustituyen la evidencia literal faltante que sigue.

### C. Identidades literales de proveedor todavía faltantes

Antes de sellar el padre se deben suministrar y verificar, sin red en esta tarea:

1. Hasta tres identidades exactas de manifiestos SHA-256 oficiales aplicables a raíz, north y south/9012: URL literal, host, método GET, release/generación cubierta, evidencia documental, cota ≤1 MiB y semántica de cobertura del checksum.
2. Identidad exacta de `survey-bricks.fits.gz`: URL literal oficial, host, método GET, release, evidencia, checksum o referencia aplicable, cota ≤16 MiB, decoder y proyección técnica revisada.
3. Identidad exacta de `survey-bricks-dr9-north.fits.gz`: los mismos bindings, cota ≤8 MiB y evidencia de cobertura north g/r/z.
4. Identidad exacta de `survey-bricks-dr9-south.fits.gz`: los mismos bindings, cota ≤16 MiB y evidencia de cobertura south g/r/z.
5. Nombre e identidad exactos de la lista oficial de los 1.691 bricks sur corregidos: URL, host, método GET, release/generación 9012, evidencia, checksum aplicable, cota ≤2 MiB, decoder/proyección.
6. Esquema completo de proveedor para cada tabla anterior: formato, HDU o estructura JSON aplicable, nombres/tipos/unidades/cardinalidad de columnas, reglas de valores faltantes y mapeo cerrado hacia los campos técnicos permitidos. Debe probarse que no es un catálogo de fuentes.
7. Especificación cerrada de un rol de índice técnico por región, con host/método/producto, evidencia documental de la relación, resolver permitido, plantilla o mapa de enlaces exactos, cota ≤512 KiB y regla que solo acepta el brick ya seleccionado.
8. Hasta 26 roles HEAD finitos para los futuros productos autorizados, ligados a región/brick/generación/producto/banda; cada uno necesita evidencia del enlace, host, método HEAD, cota de eventual cuerpo de error ≤64 KiB, futuro `max_bytes` e HDU. Solo se materializan después de la selección; no se escriben ahora URLs de bricks desconocidos.
9. Lista exacta de hosts aprobados y evidencia de que cada URL pertenece al proveedor oficial. Redirects no enumerados permanecen prohibidos.
10. Tamaños exactos cuando estén disponibles, o hard body caps dentro de los máximos congelados; aplicabilidad precisa de cada checksum proveedor. Una etiqueta aproximada de directorio no es un tamaño exacto.

### D. Bindings de derechos/evidencia todavía faltantes

1. Evidencia afirmativa y revisada, aplicable a los recursos DR9 concretos, para `scientific_local_analysis=true`.
2. Evidencia afirmativa y revisada para `local_preservation=true`, limitada a cache local/privado necesario para esta ejecución.
3. Evidencia de acceso público/documental con su alcance preciso; acceso público no se convertirá en licencia ilimitada.
4. Evidence refs inmutables —archivo local preservado, URL oficial, fecha/versión y SHA-256— que sostengan cada booleano anterior.
5. Separación explícita de derechos de reproducción de imágenes/renderizados y de FITS/derivados.
6. `redistribution=false` y alcance `FITS_OR_DERIVED_REDISTRIBUTION=DISABLED/UNRESOLVED`. Esto no bloquea por sí solo un uso local afirmativamente documentado, pero tampoco lo autoriza.
7. Revisión de que acknowledgment/atribución aplicables serán cumplidos si existe publicación futura.

El snapshot local de acknowledgment es evidencia parcial. No basta para activar análisis/cache por conveniencia de software.

### E. Campos de autorización humana todavía faltantes

El registro humano externo y su binding en el manifiesto deben contener, como mínimo:

1. `authorized=true` solo después de una autorización humana concreta.
2. `scope="METADATA_BOOTSTRAP_ONLY"`.
3. `evidence_ref` no vacío hacia el registro revisable.
4. `record_sha256` hex minúsculo de 64 caracteres sobre los bytes exactos del registro.
5. Vínculo del registro con el agregado de implementación, fingerprint/recibo ambiental, versión y sello del padre revisado, lista literal de recursos/roles/hosts/métodos, límites globales y de etapa, directorio de ejecución, reglas de reanudación y prohibiciones de mapas/PSF/catálogos.
6. Autorización del comando metadata-only concreto. Preparar el entorno o escribir `--execute-network` no constituye esa autorización.

### F. Valores que no se pueden adivinar

No se inferirán ni fabricarán:

- URLs solicitadas/finales, hosts, paths, filenames o sufijos de proveedor;
- nombres de manifiestos checksum ni qué archivos cubre cada uno;
- checksums, ETag, tamaños reales, disponibilidad o respuestas HEAD;
- nombre/ubicación de la lista de 1.691 corregidos;
- esquema, HDU, columnas, tipos, unidades, proyección o semántica de tablas proveedor;
- nombres de bricks, brick IDs, geometrías, bounds, generación north o pertenencia south a 9012;
- plantillas de índices de brick, enlaces coadd, bandas/productos disponibles o futuros resource IDs;
- booleanos de derechos, alcance de cache, licencia FITS/derivados o evidencia refs;
- autorización humana, su timestamp, referencia o hash;
- sellos/file hashes del padre antes de fijar todos sus bytes;
- recursos PSF, ubicaciones S1–N3, manifiesto final o CSV de desarrollo;
- equivalencias con DR9sv, DR5, DR10, Tractor, imágenes de otra release o cualquier fallback.

## 7. Bloqueos vigentes

### OBSERVED

Permanecen ausentes: manifiesto bootstrap de producción, URLs literales metadata, procedencia local sellada para esas URLs, esquema/proyección proveedor verificado, evidencia suficiente de análisis/cache local, registro humano metadata-only, tamaños/checksum applicability reales y cualquier selección DR9.

### DOCUMENTED

Cada elemento anterior es obligatorio antes de sellar `OC3_METADATA_BOOTSTRAP_MANIFEST.json`. Un recurso no resoluble queda bloqueado; no se habilita crawling, búsqueda de alternativas ni sustitución de release.

### INFERRED

El estado actual es **PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**. Llegar a READY requiere una revisión posterior de las entradas C–E y una autorización concreta; no ocurre automáticamente por esta verificación.

## 8. Contabilidad de esta verificación

### OBSERVED

- Solicitudes reales realizadas por esta tarea: 0.
- DNS a Legacy Surveys, NERSC, Galaxy Zoo u otro proveedor survey: 0.
- Solicitudes survey: 0.
- Bytes astronómicos adquiridos: 0.
- Bytes metadata DR9 adquiridos: 0.
- Bricks reales seleccionados: 0.
- Manifiestos de producción creados: 0.
- Ledgers creados: 0.
- Promociones ejecutadas: 0.

El `install.log` preserva descargas anteriores desde el índice de paquetes durante la preparación humana; esta tarea no las repitió. El replay preservado declara cero solicitudes de red reales.

### INFERRED

Esta revisión cambia únicamente el diagnóstico prospectivo del preflight mediante este documento. No crea evidencia observacional ni consume presupuesto survey OC-3.

## 9. Estado final

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

**OC-3 REMAINS NOT STARTED.**
