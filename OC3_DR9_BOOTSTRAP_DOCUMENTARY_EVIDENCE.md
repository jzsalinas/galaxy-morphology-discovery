# OC-3 — evidencia documental para el bootstrap de metadata DR9

**Fecha de congelación:** 2026-09-18  
**Alcance:** revisión documental y local, sin acceso a red ni adquisición de datos DR9.  
**Estado de evidencia:** hechos revisados externamente por el humano contra documentación oficial vigente y suministrados para esta tarea. No son observaciones obtenidas de archivos survey descargados localmente.

## 1. Límites de esta congelación

Este documento conserva identidades, checksums esperados, esquemas documentados, semántica de productos y evidencia de acceso/derechos para una futura revisión de producción. No certifica disponibilidad HTTP actual, respuesta final después de redirects, tamaño real, cabecera FITS, HDU, esquema FITS observado, checksum local, pertenencia de ningún brick ni contenido de ningún producto.

En esta tarea no se creó un manifiesto bootstrap, ledger, rights record, allowlist ni selección de bricks. No se inició OC-3.

Las categorías usadas aquí son:

- **OBSERVED_LOCAL:** bytes o estado comprobados en el repositorio local.
- **DOCUMENTED_HUMAN_REVIEW:** evidencia oficial revisada externamente y suministrada por el humano el 2026-09-18.
- **INFERRED_PROJECT_GATE:** interpretación operacional estrecha para este proyecto; no equivale a una licencia jurídica universal.
- **UNRESOLVED:** afirmación que necesita evidencia adicional antes de producción.

## 2. Autoridades y entorno verificados localmente

Los siguientes hashes SHA-256 se recalcularon sobre los archivos presentes. No se modificó ninguna autoridad.

| Archivo | SHA-256 verificado |
|---|---|
| `GALAXY_RESEARCH_SEED.md` | `6f1fa8e895b6921f02f2298ed17c8808f9fdec92a9f340c3042031b908a38995` |
| `CODEX_PHASE_C0_SPEC.md` | `1dfde2998fec1c03ac9f496d3bf813a9c12f3c9ce5ba8cc9f1f5cf3e21c290cb` |
| `C0_EXECUTION_DECISION_001.md` | `dffa854fd8df0df5063eebd9452b113423c6e3555aaf0c484844849be9621959` |
| `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md` | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| `OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md` | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_IMPLEMENTATION_REPORT.md` | `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864` |
| `OC3_AMENDMENT_002_IMPLEMENTATION_REPORT.md` | `8ca240b5855c5196a78b8cfa2a1860a179b1d1f360a3f4aa95893f74f16da0f0` |
| `OC3_EXECUTION_PREFLIGHT_SPEC.md` | `6d5617ad5cc2b552d4a036a340077f4a727d06be4217e10d0f5b7408c9f6c28e` |
| `OC3_ENVIRONMENT_SETUP.md` | `fc39dba8f0d757ef0b342af01ff5710e21b56c1e6093c7969f910e02ad27c43d` |
| `OC3_PREFLIGHT_ENVIRONMENT_VERIFICATION.md` | `ae131bbfe69efaae983cc353518c1a8cafde97893cb935fc8ec86a7079b71ded` |
| `AGENTS.md` | `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222` |

El agregado de los 12 archivos Python de implementación OC-3, calculado mediante la regla de `implementation_hash`, es:

`37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`

Coincide con el valor autorizado, con `implementation_aggregate_expected` de `ENVIRONMENT.json` y con `implementation_aggregate` del recibo.

| Artefacto ambiental | SHA-256 o fingerprint verificado |
|---|---|
| `oc3/environment_setup/PREPARATION_RECEIPT.json` | `0bce87d275ca71f6d6bef39f597fb354a3c1813c150830b395a1628d3b638654` |
| `oc3/environment_setup/ENVIRONMENT.json` | archivo `c8197a08121b72441382d8188c1d548a96b150aab296280d3361c42f757f5906` |
| fingerprint ambiental embebido | `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf` |
| `install-report.json` | `0a241408a819878270031b15e58148ba0df749f80867b48b93924627af0ac23f` |
| `synthetic-tests.json` | `667aa91a0a1b2fe8a4519d386f8e7240f4dcf15858babd2862efe28a8cd1cc41` |
| `synthetic-tests.log` | `f68ccf3daa1ddc36fcf2a7c26be9a46199b4723d92d13c496bdd996388e4d033` |
| `dry-run.json` | `aff848e9de808c6011ca076d3fcc126d8e3eec01543803e6286f52318d419dd0` |
| `pip-check.log` | `9261363b733079a641c2e4cc9bc46ffa1d8336945a87f807b6cf68847dbc9b09` |
| `install.log` | `9ebabefc4d540826fe5cf02859a5f5b1f04985f9e693b0a24611a6ebc37497aa` |

El recibo conserva replay sintético 142/142, cero fallos, cero omitidas y cero solicitudes reales. No se repitieron provisioning, tests ni dry-run en esta tarea.

## 3. Repositorio oficial y manifiestos de checksum

### DOCUMENTED_HUMAN_REVIEW

El distribuidor oficial documentado es:

- host: `portal.nersc.gov`;
- base DR9: `/cfs/cosmo/data/legacysurvey/dr9/`;
- rama north: `/cfs/cosmo/data/legacysurvey/dr9/north/`;
- rama south: `/cfs/cosmo/data/legacysurvey/dr9/south/`.

Los índices oficiales root, north y south exponen directamente los archivos resumen y manifiestos de checksum.

| Ámbito | Identidad documental del manifiesto |
|---|---|
| root | host `portal.nersc.gov`, path `/cfs/cosmo/data/legacysurvey/dr9/legacysurvey_dr9.sha256sum` |
| north | host `portal.nersc.gov`, path `/cfs/cosmo/data/legacysurvey/dr9/north/legacysurvey_dr9_north.sha256sum` |
| south | host `portal.nersc.gov`, path `/cfs/cosmo/data/legacysurvey/dr9/south/legacysurvey_dr9_south.sha256sum` |

Estos tres manifiestos son fuentes oficiales prospectivas de checksums de proveedor. No se descargaron ni se verificaron sus bytes localmente. Sus propios tamaños, hashes locales, respuestas HTTP y cobertura exacta por entrada siguen sin observarse.

## 4. Identidades oficiales de tablas resumen

### DOCUMENTED_HUMAN_REVIEW

| Rol | Host y path documental | SHA-256 esperado del proveedor |
|---|---|---|
| geometría global | `portal.nersc.gov` + `/cfs/cosmo/data/legacysurvey/dr9/survey-bricks.fits.gz` | `dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f` |
| cobertura north | `portal.nersc.gov` + `/cfs/cosmo/data/legacysurvey/dr9/north/survey-bricks-dr9-north.fits.gz` | `2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb` |
| cobertura south | `portal.nersc.gov` + `/cfs/cosmo/data/legacysurvey/dr9/south/survey-bricks-dr9-south.fits.gz` | `7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f` |

Los hashes fueron suministrados como valores extraídos de los manifiestos oficiales NERSC DR9. Son expectativas de integridad para una adquisición futura. No prueban que esos archivos existan localmente, que hayan sido descargados o que sus bytes se hayan validado.

`survey-bricks.fits.gz` describe la retícula geométrica completa de bricks y no solamente bricks con cobertura DR9. Su esquema documentado se congela en `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md`.

Los resúmenes regionales contienen metadata técnica y campos científicos o de conveniencia que no pueden influir en la selección. La separación entre validación del esquema proveedor y proyección científica también se congela en ese contrato.

## 5. Semántica documentada de cobertura

### DOCUMENTED_HUMAN_REVIEW

- `nexp_g`, `nexp_r` y `nexp_z` son la mediana del número de exposiciones contribuyentes dentro del área única `BRICK_PRIMARY`, por banda.
- `nexphist_g`, `nexphist_r` y `nexphist_z` son histogramas del número de píxeles por conteo de exposiciones dentro del área única del brick.
- Píxeles enmascarados por el Community Pipeline por condiciones como rayos cósmicos o saturación no contribuyen a esos histogramas.

Para el bootstrap OC-3, estos campos solamente pueden alimentar un predicado técnico g/r/z congelado prospectivamente. No pueden utilizarse para elegir por recuento de fuentes, tipo morfológico, profundidad, calidad PSF, cielo, extinción o pertenencia DESI.

### UNRESOLVED

Las autoridades existentes exigen cobertura g/r/z demostrada, pero los hechos suministrados no fijan una fórmula booleana completa que transforme `nexp_*`/`nexphist_*` en `grz`. No se adopta aquí un umbral después de ver datos. La fórmula y su tratamiento de nulos, ceros y bins deben quedar prospectivamente congelados antes de cualquier selección.

## 6. Lista oficial de bricks south corregidos 9012

### DOCUMENTED_HUMAN_REVIEW

La documentación oficial de issues DR9 declara:

- 1.691 bricks del sur afectados por corrupción asociada al procesamiento Burst Buffer;
- cambios en algunos productos coadd `image`, `invvar` o `nexp`;
- reprocesamiento de todas las reducciones afectadas;
- `RELEASE=9012` para las reducciones corregidas, frente a `9010`;
- enlace oficial a la lista de bricks afectados.

Identidad documental suministrada:

- filename: `dr9-south-patched-bricks.fits`;
- host: `www.legacysurvey.org`;
- path: `/files/dr9-south-patched-bricks.fits`;
- link suministrado: `http://www.legacysurvey.org/files/dr9-south-patched-bricks.fits`.

Estado congelado exacto:

- `IDENTITY_DOCUMENTED`
- `PURPOSE_DOCUMENTED`
- `FORMAT_SUFFIX_DOCUMENTED`
- `INTERNAL_SCHEMA_UNRESOLVED`
- `PROVIDER_CHECKSUM_UNRESOLVED`

No se supone una columna `BRICKNAME`, un HDU, una cardinalidad de filas ni ningún tipo FITS. El link suministrado usa `http`; el validador actual exige `https`. Sin una resolución documental del esquema/canonical URL no se puede convertir esta identidad en un recurso de producción.

## 7. Semántica de releases

### DOCUMENTED_HUMAN_REVIEW

| Región/survey | Release/generación permitida |
|---|---|
| south, DECaLS DR9 | `9010` o `9012`; `9012` solamente para los 1.691 bricks reprocesados |
| north, BASS/MzLS DR9 | `9011` |

La selección south de OC-3 requiere pertenencia documental al conjunto corregido 9012. North nunca hereda el predicado 9012. DR9sv permanece prohibido como sustituto.

## 8. Contrato documental de productos coadd futuros

### DOCUMENTED_HUMAN_REVIEW

La documentación oficial de archivos define patrones relativos al brick para `image`, `invvar`, `maskbits`, `nexp` y `psfsize`, con estas semánticas:

| Producto | Semántica documentada |
|---|---|
| `image` | coadd ponderado por inverse variance; unidades ópticas nanomaggies/pixel; inputs remuestreados upstream con Lanczos-3 |
| `invvar` | inverse variance del coadd, basada en la suma de inverse variances de entrada |
| `maskbits` | plano óptico `MASKBITS` en HDU 1 |
| `nexp` | número de exposiciones que contribuyen a cada píxel apilado |
| `psfsize` | promedio ponderado del FWHM de la PSF en arcsec en cada píxel apilado |

Los stacks g/r/z comparten una grilla TAN de 3600 × 3600 píxeles, con escala nominal de 0.262 arcsec/pixel.

Esta evidencia no materializa URLs por brick, prefixes, checksums, tamaños ni HDU adicionales. Ningún producto fue adquirido en esta tarea.

## 9. Evidencia de acceso y derechos

### DOCUMENTED_HUMAN_REVIEW

1. NERSC Cosmology Data Repository describe sus datasets cosmológicos como públicamente disponibles, incluye explícitamente DESI Imaging Legacy Surveys, co-localiza datos y recursos de cómputo para análisis y ofrece mecanismos de descarga individual y bulk.
2. Legacy Surveys publica un acknowledgment para trabajos científicos que usan sus datos.
3. Legacy Surveys documenta separadamente CC BY 4.0 para capas renderizadas especificadas.

### INFERRED_PROJECT_GATE

Para el alcance estrecho de análisis científico privado/local y el cache estrictamente necesario para realizarlo, la combinación documental sostiene prospectivamente:

```text
scientific_local_analysis = true
local_preservation = true
redistribution = false
FITS_OR_DERIVED_REDISTRIBUTION = DISABLED_UNRESOLVED
```

Esta es una interpretación operacional del proyecto. No afirma una licencia universal. La licencia de capas renderizadas no se extiende a FITS ni a datasets derivados de píxeles.

### Evidencia mínima para el futuro rights binding de producción

El registro futuro debe ligar, mediante referencias inmutables y revisables:

1. snapshots o documentos oficiales exactos sobre acceso público NERSC, con URL solicitada/final, fecha UTC, HTTP, tamaño y SHA-256 local;
2. documento oficial de acknowledgment, con el mismo linaje;
3. documento que delimite CC BY 4.0 a las capas renderizadas indicadas;
4. declaración humana explícita de que el uso autorizado es análisis científico local/privado y cache necesario;
5. `redistribution=false` y `FITS_OR_DERIVED_REDISTRIBUTION=DISABLED_UNRESOLVED`;
6. hashes de autoridades, implementación, entorno, recibo y manifiesto bootstrap concreto;
7. alcance `METADATA_BOOTSTRAP_ONLY` y autorización humana separada para el comando exacto.

No se creó ese rights record en esta tarea.

## 10. Estrategia prospectiva de checksums e índices

Los manifiestos root/north/south son las fuentes oficiales documentadas para checksums de proveedor. Una adquisición futura debe validar el hash local de cada tabla contra la entrada exacta del manifiesto aplicable y preservar bytes, URL solicitada/final, headers, HTTP, timestamp UTC y evidencia de cobertura.

Después de seleccionar un brick, las identidades per-brick solo pueden materializarse mediante reglas cerradas documentadas o evidencia exacta de índices/checksums del proveedor. Este documento no inventa brick, prefix AAA, patrón concreto, URL de producto, checksum per-brick ni tamaño.

## 11. Estado local y bloqueos

### OBSERVED_LOCAL

Los directorios de evidencia de producción contienen cero archivos. No existen un manifiesto bootstrap de producción, ledger, manifiesto final, CSV de desarrollo ni brick seleccionado.

El estado permanece exactamente:

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

### Bloqueos exactos vigentes

1. Esquema interno, HDU, campos/tipos y checksum proveedor de `dr9-south-patched-bricks.fits`.
2. URL canónica HTTPS o regla de redirect aprobada para la lista 9012; el link documental suministrado usa HTTP y la implementación actual solo admite HTTPS.
3. Adaptador de esquema proveedor exigido por la auditoría de `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md`.
4. Esquema regional oficial completo y exacto: los hechos suministrados dicen “at minimum” y “known examples” y no aportan tipos/shapes de todos los campos prohibidos.
5. HDU/estructura FITS exacta de las tres tablas resumen y comparación futura contra las cabeceras reales.
6. Predicado booleano g/r/z completo y prospectivo para derivar `grz` de `nexp_*`/`nexphist_*`, incluidos nulos, ceros y bins.
7. Regla de síntesis y procedencia para región, survey, release, generación, bounds, evidence refs y pertenencia 9012.
8. Verificación de `9011` para north dentro del adaptador/selector; el selector actual no impone esa generación.
9. Aplicabilidad exacta observada de los manifiestos checksum, sus bytes/tamaños y los tamaños reales de tablas dentro de los caps congelados.
10. Regla cerrada o evidencia exacta del índice por brick y de las identidades futuras per-brick, sin seleccionar todavía un brick.
11. Production rights binding con las referencias inmutables descritas arriba.
12. Manifiesto bootstrap de producción sellado y revisado.
13. Autorización humana concreta `METADATA_BOOTSTRAP_ONLY`, ligada al manifiesto y comando exactos.

La evidencia documental de derechos estrecha el bloqueo, pero no cambia el estado porque los requisitos de esquema, manifiesto y autorización siguen abiertos.

## 12. Contabilidad de esta tarea

- Solicitudes reales de red: **0**.
- Solicitudes a Legacy Surveys/NERSC: **0**.
- Bytes DR9 adquiridos: **0**.
- FITS adquiridos: **0**.
- Manifiestos de producción creados: **0**.
- Ledgers creados: **0**.
- Bricks reales seleccionados: **0**.
- Código modificado: **0 archivos**.

**OC-3 REMAINS NOT STARTED.**
