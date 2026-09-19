# CODEX_PHASE_C0_SPEC.md

**Proyecto:** descubrimiento morfológico no supervisado de galaxias inspirado en AAC  
**Versión:** 0.1  
**Fecha de congelación:** 2026-09-17  
**Fase:** C0 — inventario reproducible, sin entrenamiento  
**Documento rector:** `GALAXY_RESEARCH_SEED.md v0.1`  
**Estado:** listo para implementación posterior; este documento no implementa código ni autoriza una descarga masiva

---

## 0. Decisión ejecutiva

C0 no construirá todavía el dataset científico completo. Su función es demostrar que ese dataset **puede construirse sin ambigüedad, fuga de etiquetas ni sustituciones silenciosas de release**.

La cohorte candidata sigue siendo GZD-5 sobre DECaLS DR5, pero queda condicionada a seis verificaciones adversariales:

1. resolver de forma inequívoca qué filas pertenecen a GZD-5;
2. reconciliar los distintos conteos publicados sin forzarlos a coincidir;
3. separar el índice de sujetos de las respuestas morfológicas;
4. comprobar qué contienen realmente los FITS DR5 y qué productos de ruido, máscara y PSF están disponibles;
5. demostrar que una muestra estratificada puede parearse con imágenes científicas SDSS DR8;
6. estimar el coste completo antes de descargar imágenes a escala de cohorte.

La salida de C0 será una decisión `GO`, `GO_WITH_REVISION` o `STOP`. Un resultado `STOP` es una conclusión válida: impide construir sobre un contrato de datos ficticio.

---

## 1. Autoridad y precedencia

En caso de conflicto, se aplica este orden:

1. `GALAXY_RESEARCH_SEED.md v0.1` para la intención científica;
2. este documento para el alcance operativo de C0;
3. publicaciones primarias para la semántica científica de la muestra;
4. documentación oficial versionada para esquemas y productos;
5. cabeceras y contenido de los archivos efectivamente recuperados;
6. implementaciones históricas, tutoriales o mirrors solo como evidencia secundaria.

Una discrepancia entre los niveles 3–5 no se resuelve eligiendo el dato conveniente. Se registra en `C0_DISCREPANCY_REGISTER.md` y se eleva al Gate correspondiente.

---

## 2. Objetivo y no-objetivos

### 2.1 Objetivo

Producir un inventario reproducible y auditable de las fuentes necesarias para materializar la cohorte inicial, junto con un borrador de contrato lógico que permita iniciar C1 sin interpretar intenciones vagas.

C0 debe responder con evidencia:

- cuál es el universo exacto de sujetos candidato;
- qué identificador estable une catálogos, PNG de presentación, FITS DECaLS y observaciones SDSS;
- qué release y producto originó cada dato;
- qué campos existen realmente, con unidad, tipo, nullabilidad y procedencia;
- qué información queda visible, auditada o bloqueada;
- qué productos faltan y cuánto costaría obtenerlos;
- qué fracción de objetos admite un par cross-survey reproducible.

### 2.2 No-objetivos

C0 no debe:

- entrenar encoders, clasificadores, autoencoders ni modelos fundacionales;
- calcular embeddings, UMAP, clusters o scores de anomalía;
- optimizar augmentations o preprocessing;
- consultar votos Galaxy Zoo para elegir filas, filtros o hiperparámetros;
- descargar los archivos completos de imágenes de ~100 GB;
- descargar todos los coadds DR5 o todos los frames SDSS;
- convertir las predicciones Zoobot en verdad de referencia;
- modificar la pregunta científica ni inventar un algoritmo AAC.

---

## 3. Hechos de partida y tensiones que C0 debe resolver

### 3.1 Hechos documentados

- Galaxy Zoo DECaLS usó galaxias del NASA–Sloan Atlas v1.0.0 dentro de la intersección DECaLS–SDSS DR8, con `z <= 0.15` y radio Petrosiano de al menos 3 arcsec.
- GZD-5 corresponde a la campaña basada en DR5 y empleó un árbol de decisión revisado.
- El artículo informa 262 000 galaxias GZD-5, mientras que el catálogo de clasificaciones voluntarias preservado por CDS contiene 253 286 registros.
- Para la construcción de imágenes GZD-5 se descargaron FITS a 0.262 arcsec/píxel, hasta 512 píxeles por lado, y luego se redimensionaron para producir la vista de 424×424 mostrada a voluntarios.
- La publicación informa 216 106 imágenes completas entre 247 746 galaxias GZD-5 que no estaban en DR1/DR2; esos números no describen necesariamente el mismo universo que el catálogo final de voluntarios.
- El archivo público de Galaxy Zoo incluye catálogos, predicciones supervisadas e imágenes de presentación; la documentación de consumo identifica cuatro archivos `gz_decals_dr5_png_part*.zip`.
- El servicio y los coadds oficiales de DR5 son la fuente candidata para imágenes FITS calibradas. Los stacks tienen 0.262 arcsec/píxel, y existen productos separados de imagen, inverse variance, número de exposiciones y modelo.
- Los sweeps DR5 proporcionan metadatos por fuente como `BRICKID`, `OBJID`, `NOBS_*`, `ANYMASK_*`, `ALLMASK_*`, `PSFSIZE_*`, `PSFDEPTH_*`, `GALDEPTH_*` y `FRACFLUX_*`.

### 3.2 Tensiones abiertas

Los siguientes puntos **no se consideran resueltos** hasta ejecutar C0:

1. los conteos 262 000, 253 286, 247 746 y 216 106 tienen denominadores distintos;
2. el archivo PNG de Galaxy Zoo no es sustituto de un FITS científico;
3. el endpoint FITS de DR5 puede entregar solo el cubo de imagen, sin inverse variance ni máscara por píxel;
4. `ANYMASK_*` y `ALLMASK_*` de Tractor describen el píxel central, no una máscara completa del cutout;
5. la versión NSA usada en selección fue v1.0.0, no publicada; la publicación afirma que los valores utilizados coinciden con v1.0.1 aunque cambien nombres de columnas;
6. estar dentro de la huella SDSS DR8 no garantiza que el mecanismo de recuperación de frames esté resuelto para cada coordenada;
7. la selección activa de GZD-5 hace que `active_learning_on`, `upload_group` y número de votos sean variables de selección potencialmente morfológicas, no metadatos inocuos.

---

## 4. Fuentes candidatas que deben fijarse

El ejecutor debe resolver la versión concreta, fecha de acceso, URL final, tamaño y checksum de cada archivo utilizado. Un DOI conceptual sin versión no basta para una corrida reproducible.

| ID | Fuente | Uso permitido en C0 | Evidencia esperada |
|---|---|---|---|
| S1 | [Galaxy Zoo Data](https://data.galaxyzoo.org/) | Punto oficial de descubrimiento | Enlace al depósito y descripción del contenido |
| S2 | [Zenodo DOI 10.5281/zenodo.4196266](https://doi.org/10.5281/zenodo.4196266) | Manifiesto oficial de catálogos e imágenes | Record versionado, archivos, tamaños, checksums y licencia |
| S3 | [CDS J/MNRAS/509/3966](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/MNRAS/509/3966?format=html&tex=true) | Esquema independiente y control de cardinalidad | `gzdv5.dat`, 253 286 filas y diccionario byte a byte |
| S4 | [Walmsley et al. 2022](https://arxiv.org/html/2102.08414v2) | Semántica de campaña, selección y construcción de vistas | Secciones 2–3 y conteos publicados |
| S5 | [DECaLS DR5 description](https://www.legacysurvey.org/dr5/description/) | Release, escala, cutouts y limitaciones | `layer=decals-dr5`, 0.262 arcsec/píxel, máximo de servicio y versiones |
| S6 | [DECaLS DR5 files](https://www.legacysurvey.org/dr5/files/) | Coadds, sweeps y campos de observación | Rutas y semántica de image/invvar/nexp/PSF/catálogos |
| S7 | [Legacy Survey viewer URL documentation](https://www.legacysurvey.org/viewer/urls) | Verificación de endpoints | Patrones de FITS, PSF, exposición y SDSS; no se asume que todos preserven DR5 |
| S8 | NSA v1.0.1 data model oficial de SDSS | Documentación de campos heredados | URL final versionada y correspondencia con nombres GZD |
| S9 | [SDSS DR8](https://www.sdss3.org/dr8/) y SAS/CAS asociado | Imágenes O3 y resolución de campos | release, rutas `frame`, metadatos astrométricos y productos de máscara/PSF |

### 4.1 Regla de versionado

Para depósitos con versionado:

- registrar el DOI conceptual;
- resolver el DOI/record de la versión concreta;
- guardar el JSON de metadatos original;
- registrar `record_id`, fecha de publicación, fecha de acceso y licencia;
- no sustituir automáticamente por una versión posterior.

Para servicios vivos:

- guardar URL, parámetros, fecha UTC, estado HTTP y cabeceras relevantes;
- conservar una muestra de respuesta y su checksum;
- registrar si el resultado incluye identificador de release en cabecera FITS;
- tratar una respuesta sin release verificable como no reproducible.

---

## 5. Política de acceso y presupuesto de C0

### 5.1 Operaciones permitidas

- solicitudes `HEAD` y consultas de metadatos a las fuentes S1–S9;
- descarga de catálogos y diccionarios necesarios para inspeccionar esquemas;
- descarga de hasta 96 objetos de prueba por survey;
- descarga de los sweeps o bricks mínimos necesarios para esos objetos;
- lectura de cabeceras y tablas FITS;
- cómputo de checksums `SHA-256` y verificación de checksums del proveedor;
- cruces por identificador y por coordenadas con radio predefinido;
- estimación de volumen mediante tamaños observados, no por intuición.

### 5.2 Operaciones prohibidas

- descargar los cuatro ZIP PNG completos;
- materializar la cohorte completa;
- descargar un brick, sweep o frame sin que aparezca en el manifiesto de la muestra de prueba;
- reintentar indefinidamente endpoints fallidos;
- usar credenciales privadas o mirrors no declarados;
- abrir columnas morfológicas para inspección humana, gráficos o selección;
- generar thumbnails para juzgar morfología durante C0;
- ejecutar cualquier entrenamiento.

### 5.3 Límites duros

- descarga total C0: **2 GiB**;
- objetos astronómicos de prueba: **96**;
- solicitudes de datos no metadata: **1 000**;
- reintentos por recurso: **3** con backoff;
- concurrencia a cada servicio público: **máximo 4**;
- si una ruta requiere exceder un límite, C0 se detiene y solicita revisión.

Estos límites no son el presupuesto del proyecto; son un fusible para impedir que un inventario se transforme accidentalmente en materialización masiva.

---

## 6. Arquitectura de cuarentena

### 6.1 Zonas lógicas

| Zona | Contenido | Acceso durante C0 | Acceso futuro |
|---|---|---|---|
| `RAW_IMMUTABLE` | Archivos originales y metadatos del proveedor | Solo ingesta/verificación | Solo lectura |
| `SUBJECT_INDEX` | Identidad, campaña, coordenadas y rutas técnicas | Permitido | Permitido |
| `DISCOVERY_VISIBLE` | Imágenes y metadatos estrictamente necesarios para materialización | Solo muestra de prueba | C1–C4 |
| `CONFOUND_AUDIT` | Seeing, profundidad, máscaras, S/N, redshift, tamaño, selección activa | Permitido para auditoría, no para elegir morfología | Gates de confusión |
| `INTERPRETATION_LOCKBOX` | Votos, fracciones, respuestas del árbol y Zoobot | Ingesta automática y sellado; sin análisis | Solo C5 autorizado |
| `HOLDOUT_LOCKBOX` | Filas e imágenes confirmatorias futuras | No se construye aún | Solo C5 autorizado |

### 6.2 Desensamblado obligatorio del catálogo GZD-5

El archivo completo se ingiere una vez en `RAW_IMMUTABLE`. En la misma operación se generan tres proyecciones y luego se bloquea el original:

**`SUBJECT_INDEX`:**

- identificador estable de fuente;
- `iauname` o equivalente;
- `ra`, `dec`;
- indicador inequívoco de pertenencia a GZD-5;
- ruta/nombre técnico del PNG;
- índice de fila original;
- versión y checksum de origen.

**`CONFOUND_AUDIT`:**

- redshift;
- radios Petrosianos y fotometría heredada;
- `upload_group`;
- `active_learning_on`;
- pertenencia previa a GZD-1/2;
- warnings puramente técnicos;
- conteo de votos, marcado como variable de selección y no como señal morfológica.

**`INTERPRETATION_LOCKBOX`:**

- todas las respuestas, fracciones y conteos por rama del árbol;
- cualquier etiqueta agregada;
- predicciones automáticas y sus incertidumbres;
- cualquier campo cuyo nombre o semántica describa morfología.

El programa de C0 no debe imprimir estadísticas descriptivas de columnas del lockbox, salvo número de columnas, checksum y prueba de que el archivo puede releerse sin corrupción.

### 6.3 Regla de no-fuga

Los logs no pueden contener nombres o valores de respuestas morfológicas. El informe solo podrá afirmar que se detectaron y aislaron columnas mediante un mapeo versionado. La lista completa de esas columnas se conserva dentro del lockbox, no en resultados de uso diario.

---

## 7. Identidad y cardinalidad

### 7.1 Identificador canónico provisional

`galaxy_id` se define provisionalmente como:

`GZD5:<normalized_iauname>`

Si `iauname` no es único o falta, se utiliza un UUIDv5 determinista derivado de:

- namespace fijo del proyecto;
- DOI/record versionado;
- índice de fila original;
- coordenadas normalizadas.

No se construye un identificador redondeando solo RA/Dec.

### 7.2 Cruce espacial

Para asociar GZD-5 con catálogos DECaLS o SDSS:

- radio primario: 1.0 arcsec;
- guardar todas las candidatas dentro de 3.0 arcsec;
- aceptar automáticamente solo una candidata dentro de 1.0 arcsec;
- si hay más de una, no elegir por brillo, tipo Tractor ni morfología: marcar `AMBIGUOUS`;
- guardar separación, densidad local y método de desempate si una revisión posterior lo autoriza.

### 7.3 Tabla de flujo obligatoria

`C0_CARDINALITY_FLOW.csv` tendrá al menos:

| Etapa | N filas | N identificadores únicos | N coordenadas únicas | N duplicados | N nulos | Definición del denominador |
|---|---:|---:|---:|---:|---:|---|
| Campaña reportada en artículo | | | | | | GZD-5 clasificada |
| Catálogo Zenodo GZD-5 | | | | | | filas publicadas |
| Catálogo CDS `gzdv5.dat` | 253286 esperado | | | | | mirror publicado |
| Índice tras proyección | | | | | | identidad utilizable |
| Imágenes PNG referenciadas | | | | | | presentación disponible |
| Match único DR5 | | | | | | fuente Tractor candidata |
| Probe FITS válido | | | | | | muestra, no extrapolación directa |
| Match SDSS DR8 | | | | | | par O3 candidato |

Los valores publicados son checks de plausibilidad, no aserciones que deban satisfacerse mediante descarte ad hoc.

---

## 8. Matriz mínima de campos

`C0_FIELD_AVAILABILITY_MATRIX.csv` debe contener una fila por campo lógico y estas columnas:

- `logical_field`;
- `source_id`;
- `physical_column_or_hdu`;
- `type`;
- `shape`;
- `unit`;
- `nullable`;
- `role` (`identity`, `preprocess`, `confound`, `interpretation`, `provenance`);
- `availability` (`all`, `some`, `derived`, `absent`, `unknown`);
- `semantic_evidence_url`;
- `allowed_phase`;
- `notes`.

### 8.1 Campos lógicos obligatorios

**Identidad y procedencia**

- `galaxy_id`, `iauname`, `ra_deg`, `dec_deg`;
- `gzd_campaign`, `source_record_version`, `source_row`;
- `decals_release`, `brickname`, `brickid`, `objid`, `release`;
- checksum del recurso y timestamp de adquisición.

**Imagen DECaLS**

- arreglo de flujo por banda `g,r,z`;
- unidad por píxel;
- WCS;
- escala de píxel;
- máscara por píxel o prueba explícita de ausencia;
- inverse variance por píxel o prueba explícita de ausencia;
- número de exposiciones por píxel o prueba explícita de ausencia;
- PSF por banda: modelo, FWHM local o aproximación catalogal claramente rotulada;
- background/sky y semántica de su sustracción.

**Catálogo de observación**

- `NOBS_G/R/Z`;
- `ANYMASK_G/R/Z` y `ALLMASK_G/R/Z`;
- `PSFSIZE_G/R/Z`;
- `PSFDEPTH_G/R/Z` y `GALDEPTH_G/R/Z`;
- `FLUX_G/R/Z` y `FLUX_IVAR_G/R/Z`;
- `FRACFLUX_G/R/Z`;
- modelo `TYPE`, solo como metadato del pipeline observador, nunca como etiqueta morfológica.

**SDSS DR8**

- identificador de campo (`run`, `rerun`, `camcol`, `field` o equivalente);
- imagen calibrada por banda;
- WCS, escala y unidad;
- máscara y producto PSF disponibles;
- relación exacta entre coordenada NSA y frame elegido.

**Selección/interpretación**

- redshift y radios Petrosianos en `CONFOUND_AUDIT`;
- selección activa y número de votos en `CONFOUND_AUDIT`;
- votos y predicciones automáticas en `INTERPRETATION_LOCKBOX`.

### 8.2 Prohibición de equivalencias falsas

No se permite registrar:

- `ANYMASK_*` como “máscara del cutout”;
- `PSFSIZE_*` como “PSF image”;
- `FLUX_IVAR_*` como “inverse variance por píxel”;
- PNG como “FITS calibrado”;
- una imagen SDSS del viewer sin release verificable como “SDSS DR8”;
- NSA v1.0.1 como si fuera literalmente el archivo v1.0.0 usado históricamente.

---

## 9. Muestra de prueba C0

### 9.1 Construcción

Se seleccionan 96 objetos mediante hash determinista sobre `galaxy_id`, sin consultar ninguna columna morfológica:

- 24 por cuartil de RA para cubrir rutas/servidores diferentes;
- dentro de cada cuartil, balance aproximado por cuartiles de radio Petrosiano;
- al menos 24 con `active_learning_on=true` y 24 con `false`, si el campo existe, únicamente para auditar sesgo de disponibilidad;
- los restantes se seleccionan por hash;
- semilla maestra: `11`.

Si balancear por `active_learning_on` modifica la distribución de disponibilidad, se informa; no se interpreta morfológicamente.

### 9.2 Datos autorizados por objeto

- una referencia PNG, sin descargar el archivo masivo si no existe acceso individual;
- FITS DECaLS DR5 `g,r,z` a 256×256 y 0.262 arcsec/píxel;
- registro Tractor/sweep correspondiente;
- productos auxiliares mínimos de inverse variance, máscara, nexp y PSF cuando existan;
- frame/cutout SDSS DR8 necesario para validar el par.

### 9.3 Inspecciones automáticas

Por recurso FITS:

- firma y checksum;
- lista de HDUs, dimensiones, `BITPIX`, dtype y endianess;
- WCS válida y centro recuperado;
- bandas y orden de ejes;
- unidad y calibración documentadas;
- fracción finita y fracción con cobertura;
- estadísticos de píxel robustos sin generar una galería morfológica;
- presencia y forma compatible de ivar/máscara/nexp;
- release y versión de pipeline en cabeceras, cuando existan.

No se aplican `asinh`, normalización, recentrado, segmentación ni resize durante C0.

---

## 10. Fases de ejecución

### C0.0 — Preflight de entorno

**Acciones**

1. crear directorios lógicos y permisos de lockbox;
2. registrar sistema, hora UTC, cliente HTTP, librería FITS y algoritmo de hash;
3. verificar espacio disponible y límites C0;
4. inicializar el registro de decisiones y el ledger de Gates.

**Salida:** `C0_ENVIRONMENT_SNAPSHOT.txt` y `C0_ACCESS_POLICY.yaml`.

### C0.1 — Manifiesto remoto

**Acciones**

1. resolver versiones concretas de S1–S9;
2. capturar metadatos sin descargar archivos grandes;
3. registrar tamaños y checksums declarados;
4. distinguir DOI conceptual de record versionado;
5. comprobar licencias y requisitos de citación.

**Salida:** `C0_SOURCE_REGISTER.yaml`, `C0_REMOTE_FILE_MANIFEST.csv` y metadatos crudos.

### C0.2 — Esquema y cuarentena de GZD-5

**Acciones**

1. descargar solo los catálogos/diccionarios;
2. verificar checksum;
3. inspeccionar nombres, tipos, unidades y cardinalidad;
4. generar las tres proyecciones de la sección 6;
5. sellar el lockbox;
6. comparar Zenodo y CDS por identificador, coordenadas y conteo, sin comparar votos.

**Salida:** `SUBJECT_INDEX.parquet`, `CONFOUND_AUDIT_C0.parquet`, lockbox cifrado o protegido, `C0_SCHEMA_SNAPSHOT/` y `C0_CARDINALITY_FLOW.csv`.

### C0.3 — Resolución DECaLS DR5

**Acciones**

1. asociar la muestra de 96 con fuentes DR5 dentro de 1 arcsec;
2. registrar todas las ambigüedades;
3. recuperar FITS de prueba usando explícitamente `layer=decals-dr5`;
4. inspeccionar si el endpoint entrega solo imagen o también productos auxiliares;
5. para un subconjunto de 12 objetos, contrastar el cutout de servicio con el subarray del coadd/brick oficial;
6. medir si la ruta por brick permite obtener ivar, nexp y PSF a coste razonable;
7. no asumir una máscara fatal hasta documentar bits y semántica.

**Salida:** `C0_DECALS_MATCHES.parquet`, `C0_FITS_SEMANTICS_REPORT.md` y `C0_AUXILIARY_PRODUCT_MATRIX.csv`.

### C0.4 — Factibilidad SDSS DR8

**Acciones**

1. resolver la coordenada de cada objeto de prueba a un frame científico DR8;
2. recuperar al menos banda `r` para los 96 y `g,r,i` para 12;
3. registrar escala nativa esperada, WCS, unidad, PSF y máscara;
4. comprobar que el identificador/ruta fija DR8 y no una release posterior;
5. verificar centro, cobertura y multiplicidad;
6. estimar el coste de O3 completo y armonizado, sin armonizar aún.

**Salida:** `C0_SDSS_PAIR_MANIFEST.parquet` y `C0_PAIRING_FEASIBILITY_REPORT.md`.

### C0.5 — Presupuesto de materialización

**Acciones**

1. medir bytes por objeto y por tipo de producto;
2. estimar número de recursos únicos, bricks y frames;
3. separar almacenamiento bruto, cache y derivados;
4. estimar solicitudes, transferencia y tiempo con intervalos conservadores;
5. proponer materialización por etapas y cache compartido;
6. identificar términos/licencias y carga responsable sobre servicios públicos.

**Salida:** `C0_RESOURCE_BUDGET.md` con escenarios mínimo, recomendado y completo.

### C0.6 — Decisión

**Acciones**

1. ejecutar los Gates C0-A a C0-F;
2. clasificar cada uno `PASS`, `REVISE`, `FAIL` o `INCONCLUSIVE`;
3. emitir una sola decisión global;
4. redactar `DATA_CONTRACT_DRAFT.md v0.1` solo si la decisión no es `STOP`;
5. enumerar cambios exigidos al seed para v0.2.

**Salida:** `C0_GATE_LEDGER.md`, `C0_FINAL_REPORT.md` y, condicionalmente, `DATA_CONTRACT_DRAFT.md`.

---

## 11. Gates adversariales de C0

### Gate C0-A — fuente inmutable y auditable

**Hipótesis:** los catálogos que fijan la cohorte pueden recuperarse desde fuentes versionadas y verificarse criptográficamente.

**Apoya:** record concreto resuelto; archivos, tamaños, checksums y licencia registrados; re-descarga de un archivo pequeño reproduce el hash.

**Obliga a revisar:** el DOI resuelve una versión viva pero los archivos tienen checksums oficiales; se crea snapshot local inmutable y se documenta la limitación.

**Falla/STOP:** no puede fijarse una versión concreta o el contenido cambia entre recuperaciones sin historial.

### Gate C0-B — identidad GZD-5 sin semántica morfológica

**Hipótesis:** es posible construir `SUBJECT_INDEX` usando solo identidad, campaña, coordenadas y rutas técnicas.

**Apoya:** identificadores únicos >= 99.5%; coordenadas válidas >= 99.9%; diferencias Zenodo–CDS explicadas; lockbox sellado.

**Obliga a revisar:** duplicados o ausencias entre 0.5% y 2%; se preservan como estrato y se formula regla no morfológica.

**Falla/STOP:** pertenencia a campaña o identidad solo puede inferirse a partir de respuestas morfológicas, o >2% de filas quedan ambiguas.

### Gate C0-C — semántica de imagen científica

**Hipótesis:** el recurso DR5 recuperado contiene flujo calibrado, WCS y release verificable; no es un producto de visualización disfrazado.

**Apoya:** 95 de 96 objetos recuperables; las 3 bandas están presentes; centro dentro de 1 píxel; unidad y WCS documentadas; contraste cutout–coadd compatible salvo remuestreo documentado.

**Obliga a revisar:** 90–94 de 96 recuperables, cabeceras incompletas o discrepancias explicables por servicio; se migra a extracción desde bricks.

**Falla/STOP:** menos de 90 recuperables, release no verificable, unidades opacas o valores incompatibles con el coadd oficial.

### Gate C0-D — pesos, máscara y PSF honestos

**Hipótesis:** los productos requeridos por el seed pueden obtenerse o aproximarse con semántica explícita y coste viable.

**Apoya:** ivar por píxel y nexp disponibles para >=95% del probe; máscara por píxel o regla de cobertura documentada; PSF local o FWHM por fuente disponible por banda.

**Obliga a revisar:** solo existen `ANYMASK/ALLMASK`, PSF FWHM catalogal o ivar por brick; C1 deberá redefinir el contrato y separar `available`, `approximate` y `absent`.

**Falla/STOP del contrato actual:** no hay forma viable de distinguir ausencia de datos, saturación y ruido a nivel requerido. No se puede continuar fingiendo una máscara o un ivar.

### Gate C0-E — par cross-survey identificable

**Hipótesis:** la selección heredada permite recuperar un par científico SDSS DR8 para la mayoría de GZD-5.

**Apoya:** >=90 de 96 pares únicos y válidos; rutas DR8 inmutables; centro dentro de 1 píxel; metadatos de PSF/máscara identificados.

**Obliga a revisar:** 77–89 pares; O3 se limita a un subconjunto con análisis explícito de missingness.

**Falla/abandona O3 en v0.1:** <=76 pares o el servicio disponible no fija DR8. El proyecto puede continuar sin claim cross-survey, pero el seed debe versionarse.

### Gate C0-F — factibilidad operacional y responsabilidad

**Hipótesis:** la cohorte puede materializarse sin depender de millones de solicitudes frágiles ni almacenamiento desproporcionado.

**Apoya:** plan por lotes y cache; volumen bruto estimado <=1 TiB; número de recursos únicos y tiempo aceptables; preferencia por archivos públicos/bulk frente a golpear endpoints.

**Obliga a revisar:** 1–3 TiB o dependencia alta de extracción por brick; reducir cohorte piloto mediante hash/HEALPix sin mirar morfología.

**Falla/STOP de materialización completa:** >3 TiB, servicio sin canal bulk sostenible, licencia incompatible o coste no justificable para los primeros Gates.

### Regla de decisión global

- `GO`: C0-A/B/C pasan; C0-D/E/F pasan o solo requieren ajustes nominales ya especificados.
- `GO_WITH_REVISION`: no hay `FAIL`, pero al menos un Gate requiere cambiar el contrato, tamaño de cohorte u O3; primero se publica seed v0.2.
- `STOP`: falla C0-A, C0-B o C0-C; o C0-D demuestra que los criterios de elegibilidad no pueden evaluarse honestamente; o la materialización viola límites/licencias.

---

## 12. Métricas y reportes

### 12.1 Integridad

- tasa de archivos con checksum verificado;
- tasa de lectura FITS válida;
- tasa de WCS válida;
- coincidencia de dimensiones/HDU con documentación;
- tasa de recursos con release verificable.

### 12.2 Identidad

- unicidad de `galaxy_id`;
- duplicados por `iauname` y por radio de 1 arcsec;
- separación angular al match primario y segundo candidato;
- fracción `MATCHED`, `AMBIGUOUS`, `MISSING` por fuente.

### 12.3 Cobertura de campos

- disponibilidad por campo lógico;
- nullabilidad observada;
- fracción con productos auxiliares compatibles;
- contradicciones entre documentación y archivo.

### 12.4 Recursos

- bytes medidos por producto y objeto;
- bytes proyectados con intervalo P10/P50/P90;
- número de bricks/frames únicos;
- solicitudes y fallos por host;
- cache hit estimado por agrupación espacial.

No se calcula ninguna métrica morfológica durante C0.

---

## 13. Estructura de artefactos

La implementación posterior deberá producir exactamente esta estructura lógica:

```text
c0/
  provenance/
    C0_ENVIRONMENT_SNAPSHOT.txt
    C0_SOURCE_REGISTER.yaml
    C0_REMOTE_FILE_MANIFEST.csv
    raw_metadata/
  schemas/
    C0_SCHEMA_SNAPSHOT/
    C0_FIELD_AVAILABILITY_MATRIX.csv
    C0_DISCREPANCY_REGISTER.md
  quarantine/
    SUBJECT_INDEX.parquet
    CONFOUND_AUDIT_C0.parquet
    INTERPRETATION_LOCKBOX/
  probe/
    C0_PROBE_MANIFEST.parquet
    C0_DECALS_MATCHES.parquet
    C0_PROBE_FITS_REPORT.parquet
    C0_AUXILIARY_PRODUCT_MATRIX.csv
    C0_SDSS_PAIR_MANIFEST.parquet
  reports/
    C0_CARDINALITY_FLOW.csv
    C0_FITS_SEMANTICS_REPORT.md
    C0_PAIRING_FEASIBILITY_REPORT.md
    C0_RESOURCE_BUDGET.md
    C0_GATE_LEDGER.md
    C0_FINAL_REPORT.md
    DATA_CONTRACT_DRAFT.md
```

Los nombres podrán mapearse a almacenamiento de objetos, pero su semántica y separación no cambian.

---

## 14. Esquemas mínimos de manifiesto

### 14.1 `C0_REMOTE_FILE_MANIFEST.csv`

- `source_id`
- `provider`
- `concept_doi`
- `version_doi_or_record`
- `url`
- `retrieved_at_utc`
- `http_status`
- `etag`
- `last_modified`
- `declared_bytes`
- `observed_bytes`
- `provider_checksum_algorithm`
- `provider_checksum`
- `sha256`
- `license`
- `local_logical_path`
- `access_result`
- `notes`

### 14.2 `C0_PROBE_MANIFEST.parquet`

- `galaxy_id`
- `probe_rank`
- `stratum_ra`
- `stratum_size`
- `active_learning_stratum`
- `selection_hash`
- `gzd_source_row`
- `decals_match_status`
- `sdss_match_status`
- `all_resources_checked`
- `exclusion_reason`

### 14.3 `C0_GATE_LEDGER.md`

Por Gate:

- hipótesis;
- evidencia esperada;
- artefactos consultados;
- resultado cuantitativo;
- estado;
- desviaciones;
- decisión y responsable;
- cambio requerido al seed;
- timestamp y checksum del informe.

---

## 15. Pruebas de aceptación para la implementación futura

La fase C0 no se considera completada si falta cualquiera de estas pruebas:

1. repetir la ingesta de un catálogo produce el mismo SHA-256 y la misma proyección `SUBJECT_INDEX`;
2. cambiar el orden de filas no cambia `galaxy_id` ni la selección del probe;
3. el selector del probe falla si recibe una columna de `INTERPRETATION_LOCKBOX`;
4. los logs no contienen valores de columnas bloqueadas;
5. una coordenada con dos matches dentro de 1 arcsec queda `AMBIGUOUS`;
6. un FITS sin WCS, unidad o release se rechaza o queda explícitamente `INCONCLUSIVE`;
7. una forma de ivar incompatible con la imagen causa error;
8. `ANYMASK_*` no puede registrarse mediante el tipo lógico `pixel_mask`;
9. una URL SDSS sin DR8 explícito no satisface O3;
10. superar 2 GiB, 96 objetos o 1 000 solicitudes detiene la ejecución;
11. reanudar una ejecución no vuelve a descargar un recurso cuyo checksum ya fue verificado;
12. el informe final puede regenerarse solo desde manifiestos y resultados tabulares.

---

## 16. Cambios que C0 puede exigir al seed v0.2

C0 está autorizado a proponer, no a aplicar silenciosamente:

- reemplazar “máscara por píxel” por una jerarquía de disponibilidad si DR5 no la ofrece de forma viable;
- limitar O3 a un subconjunto documentado;
- reducir la cohorte piloto por hash espacial;
- separar “GZD-5 catalogada”, “GZD-5 con imagen de presentación” y “GZD-5 materializable en FITS”;
- cambiar el criterio de S/N si no existe segmentación/ivar consistente;
- abandonar la réplica exacta O_GZ si el framing histórico no puede reproducirse desde campos disponibles;
- usar extracción por coadd en lugar del cutout service;
- declarar que PSF catalogal es una aproximación y no un modelo de PSF.

No está autorizado a:

- relajar filtros después de mirar morfología;
- usar votos para decidir qué objetos conservar;
- reemplazar DR5 por DR9/DR10 por conveniencia;
- cambiar SDSS DR8 por un composite del viewer sin versionarlo;
- afirmar que una variable ausente fue reconstruida.

---

## 17. Criterios de éxito y fracaso de C0

### Éxito

C0 tiene éxito si, incluso con decisión `GO_WITH_REVISION`, entrega:

- fuentes y versiones fijadas;
- cardinalidades reconciliadas semánticamente;
- índice GZD-5 libre de etiquetas visibles;
- matriz honesta de campos presentes/ausentes;
- evidencia de semántica FITS DR5;
- estimación empírica del pareo SDSS DR8;
- presupuesto medido;
- ledger de Gates y modificaciones necesarias.

### Fracaso operativo

C0 fracasa si:

- produce un dataset sin poder explicar su denominador;
- mezcla productos DR5 con releases posteriores;
- permite acceso a etiquetas durante selección;
- confunde PNG con datos científicos;
- promete ivar, máscara o PSF que no comprobó;
- calcula conteos tras filtros sin preservar la tabla de flujo;
- continúa después de un Gate `FAIL`.

### Fracaso científico evitado por C0

Detenerse porque no existen productos adecuados no es un fracaso del proyecto. El fracaso sería entrenar un modelo y llamar “morfología” a una estructura cuyo observador nunca se documentó.

---

## 18. Entrega exacta a Codex

Cuando se autorice implementación, Codex recibirá:

1. este documento sin cambios no versionados;
2. `GALAXY_RESEARCH_SEED.md v0.1`;
3. un directorio de trabajo vacío con permisos separados para lockbox;
4. límites de red, disco y tiempo;
5. la instrucción de implementar **solo C0.0–C0.6**;
6. prohibición explícita de entrenamiento y visualización morfológica;
7. obligación de detenerse ante Gates o límites duros;
8. obligación de entregar artefactos y pruebas, no solo un notebook exitoso.

La aceptación humana de C0 ocurrirá antes de iniciar C1. `DATA_CONTRACT_DRAFT.md` no se convierte en contrato congelado por el mero hecho de haber sido generado.

---

## 19. Registro inicial de decisiones

| ID | Decisión v0.1 | Razón | Estado |
|---|---|---|---|
| C0-D001 | Tratar GZD-5 como cohorte candidata, no confirmada | Los conteos publicados describen universos diferentes | Congelada para C0 |
| C0-D002 | Usar el catálogo GZD-5 solo para identidad y cuarentena | Evita fuga de morfología | Congelada |
| C0-D003 | No usar PNG como dato científico primario | Es producto de presentación RGB | Congelada |
| C0-D004 | Exigir DR5 explícito en imágenes primarias | Evita cambio de observador/release | Congelada |
| C0-D005 | Probar cutout contra coadd | Audita semántica y remuestreo | Congelada |
| C0-D006 | Considerar `ANYMASK/ALLMASK` insuficientes como máscara de imagen | Solo resumen catalogal/central | Congelada |
| C0-D007 | Exigir SDSS DR8 en O3 | Mantiene el observador histórico fijado | Congelada |
| C0-D008 | Limitar C0 a 96 objetos y 2 GiB | Inventario antes de escala | Congelada |
| C0-D009 | No reconciliar conteos mediante exclusiones retrospectivas | Preserva honestidad del denominador | Congelada |

---

## 20. Referencias primarias y oficiales de C0

1. Walmsley, M. et al. (2022), “Galaxy Zoo DECaLS: Detailed Visual Morphology Measurements from Volunteers and Deep Learning for 314,000 Galaxies”. [arXiv:2102.08414v2](https://arxiv.org/html/2102.08414v2); [MNRAS 509, 3966](https://doi.org/10.1093/mnras/stab2093).
2. Galaxy Zoo, catálogo y documentación oficial. [Galaxy Zoo Data](https://data.galaxyzoo.org/).
3. Galaxy Zoo DECaLS data release. [Zenodo DOI 10.5281/zenodo.4196266](https://doi.org/10.5281/zenodo.4196266).
4. CDS/VizieR, catálogo asociado a Walmsley et al. [J/MNRAS/509/3966](https://cdsarc.cds.unistra.fr/viz-bin/ReadMe/J/MNRAS/509/3966?format=html&tex=true).
5. DESI Legacy Imaging Surveys. [DECaLS DR5 description](https://www.legacysurvey.org/dr5/description/).
6. DESI Legacy Imaging Surveys. [DR5 file products and schemas](https://www.legacysurvey.org/dr5/files/).
7. DESI Legacy Imaging Surveys. [Viewer URL patterns](https://www.legacysurvey.org/viewer/urls).
8. Sloan Digital Sky Survey. [SDSS Data Release 8](https://www.sdss3.org/dr8/).

---

## 21. Condición de cierre

C0 termina cuando existe una decisión global firmada por evidencia y cada campo del futuro contrato está marcado como `verified`, `approximate`, `absent` o `deferred`.

No termina cuando “ya pudimos descargar algunas imágenes”.

**Regla final:** ninguna disponibilidad técnica convierte por sí sola un producto en observación morfológica válida; ninguna ausencia se rellena con una suposición silenciosa.
