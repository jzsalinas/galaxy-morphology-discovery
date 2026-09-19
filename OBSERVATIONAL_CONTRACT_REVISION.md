# OBSERVATIONAL_CONTRACT_REVISION

## 1. Status and scope

**PROPOSED — revisión metodológica v0.1, 2026-09-18; para revisión humana.** Documento de diseño posterior a C0 cerrado. No es continuación experimental de C0, contrato aprobado, PASS, autorización de datos ni implementación. Se comparan rutas antes de recomendar una. No se crean PREPROCESSING_BRANCH_SPEC.md ni MIP_GATE_PROTOCOL.md.

**DOCUMENTED — autoridad nueva:** MIPS v0.1 aceptada y congelada autoriza exclusivamente esta revisión. El hash exigido se verificó antes de continuar. Las decisiones históricas de C0 no se reevalúan bajo MIPS.

Convención vinculante para este documento:

- **OBSERVED:** contenido/resultado local efectivamente registrado; cuando procede de C0 se identifica como histórico, no como medición nueva.
- **DOCUMENTED:** afirmación de autoridad metodológica o documentación oficial preservada; no implica comprobación por objeto.
- **INFERRED:** consecuencia razonada con condiciones explícitas; no certificación.
- **PROPOSED:** requisito o alternativa futura aún no adoptada.
- **UNRESOLVED:** evidencia ausente, insuficiente o sin interpretación contractual; nunca equivale a cero, falso o producto inexistente.

## 2. Authorities and integrity

**OBSERVED — integridad:** SHA-256 MIPS observado y esperado: `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24`. Coinciden. No se modificó MIPS. Los hashes completos de autoridades/evidencias figuran al final de esta sección; son hashes de las copias leídas, no certificados de inmutabilidad del servidor.

| Autoridad | Rol y precedencia en esta tarea |
|---|---|
| Instrucción del usuario de esta revisión | DOCUMENTED: diseño offline, un solo documento, sin reapertura, sin datos ni implementación |
| MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md v0.1 | DOCUMENTED: autoridad metodológica nueva; preservación, niveles A/B/C y límites de diseño |
| AGENTS.md | DOCUMENTED: no fuga, conservación de artefactos y delegación humana futura; no se interpreta como prohibición de esta revisión expresamente autorizada |
| AAC Working Paper v1.0 | DOCUMENTED: pregunta, observador admisible, equivalencias predeclaradas y límites de identificabilidad; localizado en `/home/jzsalinas/Documents/indice/analisis_arquitectura_continuidad.md`, fuera de este repositorio, sin copiarlo ni alterarlo |
| GALAXY_RESEARCH_SEED.md v0.1 | DOCUMENTED: intención histórica, muestra candidata y disciplina de no-fuga; sus decisiones experimentales no se ejecutan ahora |
| CODEX_PHASE_C0_SPEC.md y C0_EXECUTION_DECISION_001.md | DOCUMENTED: alcance/criterios y precedencia del cierre histórico, no autorización de nueva adquisición |
| C0_ACCESS_POLICY.yaml | DOCUMENTED: presupuesto y contadores históricos; no es presupuesto reutilizable del nuevo experimento |
| C0_GATE_LEDGER.md, C0_FINAL_REPORT.md, C0_BOUNDED_AUDIT_REPORT.md | OBSERVED: cierre formal y alcance de resultados; prevalecen sobre entradas históricas PENDING preservadas |
| Caracterización normal, semántica FITS, Range/subimage, registros de fuentes/manifiestos | OBSERVED / DOCUMENTED: evidencia limitada; no nuevas autoridades científicas ni derechos de generalización |

**DOCUMENTED — cambios prospectivos explícitos:** MIPS establece multibanda lineal conservadora como primaria y monobanda como baseline, frente a la prioridad histórica de r del seed. Rotación/reflexión, escalas y normalización quedan experimentales o prohibidas en primaria según MIPS, no se heredan automáticamente las decisiones del seed. No se corrige el seed ni se aplica este cambio retrospectivamente. AAC no exige identidad forense si la propiedad relevante se verifica independientemente; MIPS tampoco permite reemplazar evidencia por semejanza numérica.

### Hashes de las copias leídas

| Archivo / ubicación | SHA-256 |
|---|---|
| `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md` | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| `AGENTS.md` | `3ac4d102494633036ed91e93c334a5cec702c877ba9daa1a67dd9803e778d222` |
| `GALAXY_RESEARCH_SEED.md` | `6f1fa8e895b6921f02f2298ed17c8808f9fdec92a9f340c3042031b908a38995` |
| `CODEX_PHASE_C0_SPEC.md` | `1dfde2998fec1c03ac9f496d3bf813a9c12f3c9ce5ba8cc9f1f5cf3e21c290cb` |
| `C0_EXECUTION_DECISION_001.md` | `dffa854fd8df0df5063eebd9452b113423c6e3555aaf0c484844849be9621959` |
| `c0/provenance/C0_ACCESS_POLICY.yaml` | `cef738e7287dc1b777dc7b12260a1eb8751ac77829ddbb67c1048d53c71349d9` |
| `c0/reports/C0_GATE_LEDGER.md` | `959d61a5cb83956c71431b168c7ac4bf62a7879a4ee80befe6f5cfe36479ce4a` |
| `c0/reports/C0_FINAL_REPORT.md` | `5a22bdbcd2543bf6cc1e1bf7401e2510a58887f451e52d49ccfd840774665fc0` |
| `c0/reports/C0_BOUNDED_AUDIT_REPORT.md` | `7d5f58cfedfee2a1c62cc8b9b4d68e915dda2d253acb40ea07c83f164590c9f6` |
| `c0/reports/C0_NORMAL_CUTOUT_CHARACTERIZATION.md` | `4d99cb34b94c25a55fc627d41d0f5268ba69dee2361b3443187c7ed95bed5df3` |
| `c0/reports/C0_FITS_SEMANTICS_REPORT.md` | `131624307d563c1fce28124e86340263435a92d09928b58f8b80731a5cd9ffc3` |
| `c0/reports/C0_RANGE_SUBSET_RESULTS.json` | `8e59033039b0da5d851e74404b821e318b09f0316848bfc6a98b2ebcdf3fb6d7` |
| `c0/reports/C0_RANGE_SUBSET_ACCEPTANCE.json` | `c4eaa0ebeaab1029e2860676f23715dc628c758a851c79ce4eaf3c1d69f8031b` |
| `c0/reports/C0_SUBIMAGE_SUMMARY.json` | `e4acd2a367fea189aafc033ddb3926bcb5345c5eaf831b0e4c9a55a0f11e6670` |
| `c0/reports/C0_DR5_RESOURCE_INVENTORY_SUMMARY.json` | `7ba2793e44dba0994b59171c231202702e59b26b22cc3ff626b848d692020768` |
| `c0/provenance/C0_SOURCE_REGISTER.yaml` | `2cdaba1bf7df99f60519fc7dffe3988647e78c2815f2fc165d4f61fe4fe8b03a` |
| `c0/provenance/C0_REMOTE_FILE_MANIFEST.csv` | `f1d554ff44ad7e12f2ec5e24d730993edf634078cfc1466977d94478d7258fd4` |
| `c0/provenance/C0_NORMAL_CODE_SOURCES.json` | `6f3e769d3bda24f5c0d2dc98ebaf971d53c13aad539f10ed415e8c3748fd017e` |
| `c0/provenance/raw_metadata/S5.raw` | `7dd4e5ca9ae476508c09b35104a4846eeef10a72b076a1382d4a7a35c3fd1575` |
| `c0/provenance/raw_metadata/S6.raw` | `b7818d98910f16b81e235994926f888e47bd4f2c6b58283d1ec7383c6d585e9e` |
| `c0/provenance/raw_metadata/S7.raw` | `c93fd47e9764b1096e873fadf989d4d8078a373e123f11929a1a014adaf4e1af` |
| `c0/provenance/raw_metadata/DR5_BRICK_1853p160_DIRECTORY.raw` | `5bdf2cd554fc94a480ec4174887a61ad4f99e52e83a05b6024cd29f5643048f5` |
| `c0/provenance/resource_ledger.sqlite` | `e59f9ba0c2b08eb25bd27eeb2bd1f8d6b0749779cc318b77c78bf7930275fcf9` |
| `/home/jzsalinas/Documents/indice/analisis_arquitectura_continuidad.md` | `00bca4d85e1cb942d9156d827af62288dfa35241ee41a303d240a07c5c864b2d` |

## 3. Preserved C0 state

**OBSERVED — histórico inalterado:** C0-A=PASS; C0-B=PASS; C0-C=INCONCLUSIVE; decisión global C0=STOP. C0-D/E/F=INCONCLUSIVE por cierre anticipado, no fracaso experimental. 253286 identidades reconciliadas; 96 objetos del probe; no cohorte completa materializada. La ruta normal no fue demostrada incorrecta: no se verificaron suficientemente procedencia funcional y unidades bajo aquel contrato.

**OBSERVED:** contadores archivados 465348528 bytes, 383 solicitudes de datos, 936 HTTP totales. Ningún saldo histórico se convierte en permiso para esta tarea. Las menciones PENDING en informes intermedios son estados históricos superados por el cierre; se conservan literalmente sin editar.

**OBSERVED — igualdad limitada:** C0_RANGE_SUBSET_RESULTS.json y su aceptación registran 42 archivos oficiales de imagen, 42 comparaciones de regiones para ranks1–12 en g/r/z, 14 bricks y 84 fragmentos con hashes. Igualdad de valores decodificados con NaN equivalentes, error WCS máximo reportado 4.460665883222895e-10 píxeles. Esto no es igualdad binaria entre archivos FITS completos: headers, contenedores y compresión pueden diferir. El checksum de cada archivo oficial completo no se verificó; hay URL, ETag, tamaño total, rangos y hashes locales de fragmentos.

**UNRESOLVED — no extrapolar:** otras regiones, objetos, layouts, condiciones de borde, productos invvar/máscaras/nexp/PSF, otro tamaño/escala o el normal viewer. g/r/z están presentes en las comparaciones históricas, sin validación universal de cada banda en todo DR5. La correspondencia de WCS y shapes de image/invvar en 96 respuestas subimage no demuestra identidad/calibración de invvar nativa.

## 4. Protected scientific question

**DOCUMENTED — MIPS §§3,6–8:** buscar estructura morfológica visual reproducible, discreta o no, que no se explique principalmente por observación/preprocessing. Se preservan distribución espacial, canales separados, registro, resolución y ruta hacia fotometría calibrada; se auditan brillo, ruido, redshift, selección y entorno.

**PROPOSED:** una futura unidad podría ser una galaxia catalogada candidata con bundle multibanda y auxiliares ligados por identidad; vistas/bandas/bricks no serían sujetos estadísticos nuevos. Un ID nominal único no prueba una galaxia física única: duplicados espaciales y ambigüedad seguirían requiriendo resolución independiente de votos. No se congela todavía una cohorte admisible ni una selección por calidad.

**PROPOSED:** la pregunta amplia no autoriza asumir irrelevantes color espacial, luz tenue, handedness, vecinos o inclinación. El contrato debe permitir investigar esas alternativas conservando la observación previa a normalización. No se elige encoder ni representación final.

## 5. Boundary of O_product, O_cutout and O_pre

| Etapa | Contenido y frontera |
|---|---|
| O_survey | DOCUMENTED: adquisición óptica/instrumental, bandas, seeing, detector y selección; no se rehace en esta propuesta |
| O_product | DOCUMENTED: calibración, astrometría, sky upstream, resampling/coadd y productos de calidad del proveedor. “Nativo” aquí significa píxeles del coadd publicado, no píxeles crudos sin remuestreo |
| O_cutout | PROPOSED: selección de producto y región por coordenada catalogada, bandas, ventana/footprint, traslado exacto del WCS al crop, conservación de auxiliares y linaje. Remapping necesario para un grid común sería transformación explícita de esta etapa, no operación neutral |
| O_pre | DOCUMENTED: estimación/sustracción propia de fondo, segmentación, aplicación científica de máscaras, imputación, recentrado subpíxel, rotación, escala física, homogenización PSF y normalización. No se diseñan algoritmos aquí |
| g_encoder | DOCUMENTED: features/representación aprendida; construcción del cutout no es extracción de características |

**PROPOSED:** leer/copiar flags y crear un mapa de procedencia/soporte durante O_cutout no equivale a aplicar una máscara sobre intensidades. Los arrays se preservan con valores originales, incluidos negativos y ceros. Se registra sky ya sustraído por O_product; no se “resta otra vez” ni se reconstruye un fondo no disponible. El recorte elige una ventana alrededor de la coordenada, sin estimar un centro morfológico ni trasladar sus píxeles.

## 6. Frozen comparison criteria

**PROPOSED — fijados en este documento antes de valorar rutas (§§8–12):** comparación por requisitos, sin puntuación ponderada ni compensación de un bloqueo con ahorro de recursos. A=BLOQUEANTE espacial; B=obligatorio para auditoría; C=condicional a un efecto material. “Aceptable” significa incertidumbre documentada con dominio/cota defendible y criterio futuro congelado, no una tolerancia elegida de los residuales C0. Ningún residual de C0 se usa como umbral de adopción.

| ID / clase MIPS | Propiedad y relevancia | Evidencia suficiente requerida | Incertidumbre aceptable | Impide adopción |
|---|---|---|---|---|
| A1 BLOCKING | Procedencia oficial/versionada; evita cambio de observador | Release, tipo de producto, autoridad/URI, headers y contenido fijado con hashes/linaje | Empaquetado distinto si identidad del contenido científico está demostrada | Ruta no identificable o mezcla de releases |
| A2 BLOCKING | WCS/escala; forma, tamaño y localización | WCS completo, convención de píxeles, footprint, escala local y verificación geométrica | Error acotado frente a resolución, con futura tolerancia previa | WCS ambiguo o transformación espacial sin cota |
| A3 BLOCKING | Identidad de bandas; estructura cromática | Filtro por plano, producto y orden inequívocos | Metadata no espacial ausente rotulada | Banda sustituida, mezclada o inferida de color |
| A4 BLOCKING | Co-registro multibanda; evita falsas estructuras de color | Mismo grid demostrado o mapeo y error relativo documentados | Residuo de astrometría acotado por método independiente | Misma shape usada como prueba de alineación |
| A5 BLOCKING | Coordenada/centro; evita selección morfológica implícita | Fuente, frame/época cuando relevante, incertidumbre, regla de ventana/offset | Descentrado catalogal registrado y evaluable posteriormente | Recentraje oculto o identidad ambigua |
| A6 BLOCKING | Dimensiones/FOV; evita truncamiento | Ventana exacta, footprint y criterio previo de escala | Recorte finito con límites y sensibilidad futura declarada | Tamaño adaptado por inspección o truncamiento no auditable |
| A7 BLOCKING | Cobertura/soporte; evita señal fabricada | Mapa de muestras disponibles y validez, por banda, con significado | Missingness conservada; no apto hasta regla científica predeclarada | Ausencia representada como cero válido |
| A8 BLOCKING | Brick/tile boundaries; evita costuras | Descriptores, regiones y regla de pertenencia/solapamiento explícita | Restricción geométrica de dominio con sesgo cuantificable | Promedio, stitching, padding o clipping silenciosos |
| A9 BLOCKING | Remuestreo O_cutout; cambia señal/covarianza | Ausencia de resampling por extracción exacta, o operador/control de error y soporte auditados | Aproximación probada dentro de futuros criterios | Kernel, normalización, bordes o propagación desconocidos |
| A10 BLOCKING | Máscaras/inválidos; artefactos imitan forma | Flags por píxel o evidencia alternativa suficiente sobre su efecto; relación al producto y diccionario versionados | Causa específica desconocida solo si validez espacial queda independientemente acotada | Ivar positiva/valor finito declarado limpio sin evidencia; bits ajenos a DR5 |
| A11 BLOCKING | PSF/resolución respecto del muestreo | Información espacial relevante o aproximación cuya suficiencia se demuestre | FWHM como proxy declarado si limita el claim y las pruebas prueban suficiencia | Confundir escalar PSF con modelo; resolución indeterminada material |
| B1 REQUIRED_FOR_AUDIT | Unidades/calibración; auditar brillo y selección | Semántica oficial del producto, headers y linaje de escala | Error sistemático documentado con alcance | Inferir calibración de mera semejanza numérica |
| B2 REQUIRED_FOR_AUDIT | Relación image/ivar/mask; soporte y ruido | Producto/HDU, grid, unidades, significado de ceros/negativos/no finitos y flags | Ivar diagonal aproximada con límites explícitos sobre correlaciones | FLUX_IVAR catalogal como mapa o peso como covarianza completa |
| B3 REQUIRED_FOR_AUDIT | Background; luz tenue y halos | Sustracción upstream documentada; modelo/metadata disponibles y límites | Modelo original ausente si impacto puede auditarse sin inventarlo | Tratar coadd como cielo sin sustraer o pérdida de luz tenue inidentificable para el claim |
| B4 REQUIRED_FOR_AUDIT | PSF disponible; confusión instrumental | Metadatos/productos con unidad, posición, banda, dominio y calidad | Aproximación separada del dato/modelo completo | Campos ausentes rellenados con PSF ideal o promedio no justificado |
| B5 REQUIRED_FOR_AUDIT | S/N, brillo superficial, redshift, selección | Entradas de ruido/área/calibración y catálogo de auditoría trazable, missingness | Valores desconocidos explícitos y restricciones de inferencia | Normalización destruye única ruta a fotometría o redshift se usa como etiqueta |
| B6 REQUIRED_FOR_AUDIT | Pre-normalización/metadata; reversibilidad de decisiones | Arrays/headers inmutables y transformaciones enlazadas | Formato sin pérdida con representación semántica canónica | Solo JPEG, normalizados o arrays sin linaje |
| B7 REQUIRED_FOR_AUDIT | Estados del píxel; selección | Soporte, finitud, calidad y peso como ejes separados | Estado UNKNOWN bloquea el claim correspondiente | Unsupported/invalid/masked/valid-zero colapsados |
| C1 CONDITIONAL | Commit/dependencias/runtime; relevancia A/B | Versión local fijada o verificación independiente del resultado relevante | Compilador upstream desconocido si no deja efecto material sin acotar | Diferencias de decoder/resampling/calibración capaces de alterar A/B |
| C2 CONDITIONAL | Identidad de compresión/decoder | Layout/quantización, escalado FITS y endian documentados; hash de fragmentos/contenido | Recompresión conocida preservando valores científicos | Confundir bytes comprimidos con valores o caché parcial con archivo íntegro |
| O1 requisito operativo | Licencias y redistribución | Términos del producto y servicio, atribución, alcance de derivados | Redistribución deshabilitada si uso permitido está explícito | Derechos indeterminados para la operación propuesta |
| O2 requisito operativo | Recursos y sostenibilidad | Inventario de recursos únicos, IO/cache/derivados y presupuesto autorizado | Estimaciones con supuestos e incertidumbre | Plan depende de transferencias sin límite o caché no reproducible |

**DOCUMENTED / PROPOSED:** la importancia científica de C1/C2 deriva de A/B. Para crop exacto no se exige reconstruir el compilador del survey si producto/semántica están fijados y la extracción se verifica independientemente. Si se introducen resampling o decodificación con pérdida, sí debe identificarse o acotarse el efecto relevante. A/B no se flexibilizan para evitar pedir versión, ni se exige versión por mero formalismo.

## 7. Existing evidence register

| ID | Estado y evidencia local | Alcance / no extrapolar |
|---|---|---|
| E1 | OBSERVED: ledger/final/bounded audit C0 | Estados históricos cerrados; no revisión del Gate |
| E2 | OBSERVED: C0_RANGE_SUBSET_RESULTS.json, aceptación, manifiesto HTTP y fragmentos | 42 regiones de imagen/ranks1–12; igualdad de valores, no todo FITS, ivar o normal |
| E3 | OBSERVED: C0_SUBIMAGE_SUMMARY.json y C0_FITS_SEMANTICS_REPORT.md | 96 respuestas,118bricks, pares image/ivar compatibles geométricamente; sin máscara/nexp/PSF suministrados en esa respuesta; no prueba de ausencia global |
| E4 | DOCUMENTED: S5.raw, secciones bricks/Image Stacks/PSF/Sky Level/Photometry | TAN, grz con proyecciones idénticas por brick,3600²,0.262″; sky upstream; PSF por exposición; calibración natural DECam AB; advertencia coadds no para trabajo de precisión |
| E5 | DOCUMENTED: S6.raw, coadd image/invvar/nexp y tablas | Image en nanomaggies/píxel; invvar suma de inverse variances,1/(nanomaggies)² por píxel; nexp contribuciones. No prueba de mapa de covarianza ni píxel limpio |
| E6 | OBSERVED: BUNIT=nanomaggy en headers oficiales examinados, WCS comparado | Refuerza E4/E5 para imagen; semántica nativa invvar todavía no validada por Range |
| E7 | DOCUMENTED: S6.raw ANYMASK/ALLMASK/PSFSIZE/FLUX_IVAR | Flags centrales catalogales, FWHM promedio ponderado, incertidumbre de flujo de fuente; no mapas sustitutos |
| E8 | OBSERVED: inventario HEAD 514 recursos, C0_DR5_RESOURCE_INVENTORY_SUMMARY.json | Tamaños históricos, no contenido adquirido ni extrapolación de cohorte |
| E9 | DOCUMENTED CANDIDATE: C0_NORMAL_CODE_SOURCES.json y fuentes preservadas | Código público íntegro, no despliegue certificado; no recuperar normal como ruta primaria |
| E10 | DOCUMENTED: C0_SOURCE_REGISTER.yaml y C0_REMOTE_FILE_MANIFEST.csv | Términos Zenodo CC-BY-4.0 no transfieren licencia a coadds; otros derechos todavía bajo revisión |
| E11 | OBSERVED: DR5_BRICK_1853p160_DIRECTORY.raw y descriptores Range | .fits.fz observados frente a .fits documentado; solo layouts validados, no universalidad de HTTP Range |
| E12 | UNRESOLVED: evidencia conjunta de máscara completa, PSF efectiva del coadd, limitación de precisión y derechos de uso/redistribución | No se sustituye por mapa de finitud, FWHM central o permiso implícito de acceso público |

**DOCUMENTED — cautela determinante:** S5.raw, sección Image Stacks, advierte contra trabajo de precisión con esos stacks y aclara que Tractor usa exposiciones individuales. Esa advertencia no prueba que todo uso morfológico sea inválido, pero tampoco permite asumir que preserva barras tenues, colas o fotometría superficial con precisión suficiente. En §19 se delimita qué evidencia falta. El dato ya ha sufrido sky subtraction y Lanczos-3 en O_product: crop local no revierte esas operaciones.

**UNRESOLVED:** no se encontró en la evidencia examinada una nueva acreditación independiente local de la ruta normal tras el cierre. El menú moderno del sitio y enlaces a otras releases en S5/S6 no acreditan productos DR5 ni autorizan sustitución.

## 8. Candidate Route A — DR5 normal viewer cutout

**OBSERVED:** referencia histórica descartada bajo el contrato C0 cerrado; no se demostró incorrecta. Cabeceras DR5/grz/WCS observadas, pero unidades del normal y procedencia funcional no suficientemente verificadas. El diagnóstico candidato tampoco acreditó selección exhaustiva de bricks, resolución/PSF efectiva, máscara o covarianza del normal. **DOCUMENTED CANDIDATE:** fuentes públicas describen la ruta, sin certificar despliegue.

**UNRESOLVED:** A1/A7–A11 y B1/B2/B4 no quedan resueltos por las semejanzas numéricas. MIPS C1 admite evidencia independiente de propiedades en vez de commit exacto, pero no se dispone aquí de esa nueva evidencia y no se reinterpreta C0. No habrá nuevos contrastes, retuning ni los seis rangos de rank5.

**PROPOSED:** papel futuro legítimo limitado a antecedente de límites epistemológicos y, si una futura especificación lo autoriza, comparador técnico explícitamente no calibrador ni árbitro de verdad. No fuente primaria, teacher, selector de objetos ni evidencia de aprobación de otra ruta.

## 9. Candidate Route B — construcción local desde productos nativos oficiales DR5

**DOCUMENTED:** familia candidata `dr5/coadd/<AAA>/<brick>/legacysurvey-<brick>-image-<band>` y correspondientes `invvar`/`nexp`; sufijos reales se fijarían por manifiesto, no se adivinan desde una plantilla. E4–E6 sostienen geometría/unidades de imagen y semántica documental de productos. **OBSERVED:** se han leído regiones de image `.fits.fz`; no se han certificado de igual forma todos los auxiliares. `model`, `chi2`, `depth` y `galdepth` no sustituyen image, máscara o ivar por píxel. Se conservarían canales g/r/z; no observación RGB ni monobanda impuesta como primaria.

### B1 — crop directo, sin nuevo remuestreo

**PROPOSED, no contrato adoptado:** elegir una región rectangular de un único brick por regla geométrica congelada, común a las bandas después de verificar sus WCS, y copiar muestras/auxiliares sin interpolación, reescalado ni mezcla. Transformar WCS mediante el desplazamiento entero de la ventana y preservar el WCS original. Conservar offset subpíxel entre coordenada catalogada y centro de la ventana; no forzar el centro mediante interpolación. Copiar valores decodificados no prueba igualdad binaria del archivo comprimido ni vuelve “cruda” una imagen coadded.

**UNRESOLVED:** regla de propiedad entre bricks solapados, disponibilidad de ventana completa/auxiliares y suficiencia de PSF/calidad. Un catálogo de bricks por centro y la pertenencia nominal no prueban cobertura de toda la ventana. Si ningún brick contiene la región admisible en todas las bandas, registrar fallo de soporte; no rellenar bordes ni mosaicar automáticamente. Excluir sistemáticamente objetos próximos a límites podría inducir selección por campo, tamaño o ambiente y requiere auditoría antes de aceptar ese dominio. No se elige el brick de mejor aspecto o menor residual.

**INFERRED:** B1 permite separar una transformación local de selección exacta de los efectos upstream. Su ventaja científica es poder demostrar qué muestras y metadatos fueron conservados. No depende de que esas muestras estén hoy cacheadas. No soluciona por sí sola la advertencia de precisión, máscara, PSF, licencias o faltantes.

### B2 — remapping o mosaico

**PROPOSED:** alternativa separada, no fallback de B1. WCS de distintos bricks puede diferir aunque comparta escala nominal; concatenar por índices no es un mosaico astronómico. Un grid común exigiría definir soporte de kernel, normalización fotométrica/área, fronteras, contribuciones compartidas, rechazo y propagación de flags/pesos. El solapamiento puede reutilizar exposiciones: no tratar bricks como mediciones independientes ni sumar sus ivar como si lo fueran.

**UNRESOLVED:** operador, covarianza, PSF combinada, precisión de astrometría y footprint. Sin esas definiciones B2 no es admisible; no se propone kernel, tolerancia ni blending. Se registrarían para cada píxel fuentes, pesos y transformaciones si esta alternativa llegara a autorizarse. No se construye mosaico ahora.

### B3 — auxiliares y regeneración

**PROPOSED:** conservar image, invvar correspondiente, nexp si ofrece semántica necesaria de soporte y todo producto real de máscara/calidad disponible, sin inventar archivos. Un manifiesto debe distinguir present/absent/not_examined/unknown con evidencia. PSFSIZE por fuente puede ser proxy de seeing; no se ofrecerá como kernel de la PSF del coadd. El modelo de exposición no es automáticamente el efectivo del stack.

**DOCUMENTED:** S5 describe sky espacial sustraído upstream; conservar esa declaración y cualquier metadata realmente disponible. **PROPOSED:** ningún background propio, segmentación, recentrado, rotación, conversión a escala física o normalización en O_cutout.

**PROPOSED:** regenerar valores, dtype, geometría, auxiliares y linaje desde producto/fragmentos preservados; distinguir checksum del contenedor, checksum de valores canónicos y representación de NaN. Datos parciales requieren todos los headers/descriptores y bytes necesarios, ETag/tamaño compatibles, layout y decoder fijados. No se convierte ETag en checksum criptográfico del archivo completo. Exactitud de regeneración propia se prueba en un Gate futuro, no se presume por haber escrito una regla.

**UNRESOLVED:** derechos y coste completo por objeto/cohorte. Las hipótesis de B1 son más simples que B2, pero simplicidad no compensa un bloqueo MIPS. B queda como candidata prioritaria de evidencia, no ganadora aprobada.

## 10. Candidate Route C — subimage como vista nativa

**OBSERVED:** las regiones de imagen E2 igualan valores nativos en la muestra validada. No igualan los bytes completos de dos FITS ni certifican invvar/mask/PSF, cada objeto/banda/layout o borde. E3 muestra un servicio capaz de devolver arrays por brick con offsets; no una garantía contractual universal.

**PROPOSED — cuatro papeles separados:**

1. Vista exacta de valores: solo puede afirmarse por recurso/región comprobada contra el producto versionado y sus headers. “Byte-exact” se reservaría a una identidad explícita de bytes, no a valores numéricos equivalentes.
2. Ayuda de extracción acotada: posible futuro transporte si la respuesta queda ligada independientemente a producto, región, versión, estado de soporte y auxiliares. No importa cómo se implementó el servidor si A/B pueden verificarse sin esa identidad, pero esa verificación no está generalizada aquí.
3. Oráculo de verificación: usar respuestas históricas como ejemplos/regresiones limitados; el ancla es el producto oficial. No prueba universal ni verificación circular entre dos outputs del mismo servicio.
4. Ruta primaria: actualmente no suficientemente sustentada; faltan contrato de cobertura/selección y auxiliares, fijación de versión y términos del servicio.

**UNRESOLVED:** evidencia nueva necesaria antes de contractualizar C: especificación oficial que enlace producto/release y offsets, manejo de fragmentación/missingness/bordes, igualdad en dominio futuro definido previamente, semántica independiente de auxiliares, regenerabilidad y derechos. No se pide ni ejecuta esa ampliación en esta tarea. Si verificar cada respuesta requiriera el producto nativo completo, el supuesto ahorro podría desaparecer; tampoco eso decide la validez científica.

## 11. Candidate Route D — otra release/familia/survey, diferida

**DOCUMENTED:** el seed cita DR8/GZ DESI, HSC, Stripe82 y otros dominios como posibilidades posteriores. S5/S6 mencionan exposiciones individuales utilizadas por Tractor. **UNRESOLVED:** ninguna evidencia local aquí demuestra que una de esas alternativas resuelva conjuntamente máscaras, ruido/PSF, geometría, muestra, licencias y coste mejor que las candidatas evaluadas. Existencia, novedad o mayor profundidad no bastan.

**PROPOSED — diferimiento justificado:** no se abre búsqueda entre surveys ni SDSS. Una evaluación futura de D requeriría un candidato concreto con documento oficial de release/producto y mejora material identificada sobre el bloqueo de A/B (p. ej., calidad/PSF con semántica auditable), además de nueva justificación de selección/longitud de onda/resolución y presupuesto. Las exposiciones individuales DR5 son una familia distinta posible, no sustituto autorizado: podrían evitar algunas ambigüedades del coadd, pero introducirían elección de exposición, PSF y registro múltiples. No se desarrolla esa ruta sin evidencia discriminante.

## 12. Comparative decision matrix

**PROPOSED — aplicación de §6, sin score ni ganador por conveniencia.** B1/B2 se separan porque no comparten operador. En esta tabla O=OBSERVED, D=DOCUMENTED, I=INFERRED, P=PROPOSED, U=UNRESOLVED; cada celda lleva su estatus. Evidencias E1–E12 en §7. “Diferida” no equivale a inferior.

| Criterio | A normal | B1 crop nativo | B2 remapping/mosaico | C subimage | D alternativa |
|---|---|---|---|---|---|
| Procedencia | O:release en headers; U:ruta efectiva | D:productos oficiales; O:fragmentos image; P:linaje propio | D:entrada oficial; U:operador propio no definido | O:igualdad limitada; U:contrato global | U:no candidata evaluable |
| Unidades | U:no verificadas suficientemente | D:coadd nanomaggies/píxel; O:BUNIT nativo | D:entrada; U:semántica salida/área | O:valores imagen de subset; U:metadata general | U |
| Geometría | O:WCS/centro; U:semántica del muestreo | D:TAN/escala; P:crop+WCS exactos a validar | U:mapeo/astrometría a definir | O:offsets/WCS en subset; U:extrapolación | U |
| Resampling | D:candidato; U:efectivo | P:ninguno nuevo; D:coadd ya Lanczos-3 | U:nuevo operador y covarianza | O:nativo en regiones testadas; U:todo dominio | U |
| Máscaras | U:sin mapa demostrado | U:mapa/diccionario suficientes no establecidos | U:además propagación | O:no suministradas en respuestas; U:alternativa | U |
| Ivar | O:normal sin planos; U:relación | D:producto correspondiente; U:validación específica | U:propagación/correlación entre bricks | O:shape/WCS compatibles; U:unidad/equivalencia nativa | U |
| PSF | U:efectiva | D:FWHM catalogal/exposición; U:suficiencia coadd | U:mezcla/resolución espacial | U:no producto suministrado | U |
| Co-registro | O:WCS cubo; U:cadena | D:misma proyección por brick; P:comprobación y error | U:registro interbrick | O:subsets; U:garantía general | U |
| Bordes/soporte | U:selección efectiva | P:no padding/blending; U:regla y cobertura final | U:seams/duplicación/weights | O:múltiples HDUs; U:selección completa | U |
| Reproducibilidad | O:respuestas preservadas; U:servicio futuro | P:regeneración desde bytes/versiones; O:viabilidad limitada | U:operador no congelado | O:respuesta cacheada; U:regeneración del servicio | U |
| Auditabilidad | O:diagnóstico; U:A/B incompletos | I:transformación propia aislable; U:auxiliares | I:más transformaciones por justificar | I:ayuda limitada; U:linaje contractual | U |
| Licencias | U:producto y servicio | U:coadd/auxiliares/derivados | U:mismos derechos+derivados | U:servicio/producto | U |
| Adquisición | O:96 normales existentes; U:coste contractual completo | O:HEAD históricos E8; U:cohorte/auxiliares | I:más bricks/soporte que B1, sin medida global | O:168871911 bytes etapa96; U:coste completo | U |
| Almacenamiento | O:normal float32; U:completo | P:preservar inputs+arrays+auxiliares; I:fórmula §17 | I:inputs múltiples+weights/covarianza | P:respuestas+pruebas nativas; U:total | U |
| Complejidad | O:históricamente endpoint simple; U:certificación difícil | I:crop simple, semántica auxiliar no resuelta | I:mayor, afecta A/B | I:transporte simple, validación no trivial | U |
| Bloqueos | O:C0 cerrado; U:semántica | U:máscaras,PSF/calidad/precisión,licencias y verificaciones | U:los de B1 más operador/soporte | U:dominio/versionado/auxiliares/semántica | U:evidencia comparativa inexistente |
| Riesgo de morfología inducida | I:remuestreo/bordes no controlados | I:upstream, selección de ventana/campo, PSF y calidad | I:costuras, ruido correlacionado, PSF mezclada | I:selección oculta/metadata insuficiente | U:riesgos no caracterizados |

**INFERRED — resultado comparativo:** B1 tiene una ventaja metodológica concreta sobre A y B2: la transformación nueva puede limitarse a selección espacial exacta y hacerse auditable sin un servicio de resampling. C solo tiene igualdad limitada útil como evidencia auxiliar. Esa ventaja de B1 no resuelve E12 y no basta para ofrecer un contrato listo para aprobación. No hay ganador adoptable; se recomienda priorizar una sola decisión documental sobre B1 antes de elaborar un contrato concreto.

## 13. Proposed observational contract, if supported

**UNRESOLVED — no se presenta todavía un contrato concreto para aprobación.** La evidencia sustenta la familia B1 como candidata, pero no identifica todos los medios necesarios para A10/A11 y B2–B4/O1. Llamarla ya “contrato propuesto suficiente” trasladaría los bloqueos al futuro bajo una etiqueta optimista. La siguiente tabla es un mapa de requisitos para una eventual propuesta, no un contrato ejecutable ni selección de parámetros.

| Elemento requerido | Definición candidata / condición pendiente |
|---|---|
| 1. Pregunta protegida | DOCUMENTED:MIPS§3; preservación espacial/cromática con confusores auditables |
| 2. Unidad observacional | PROPOSED:galaxia catalogada candidata+bundle grz; identidad física/duplicados no se presumen |
| 3. Survey/release | PROPOSED:DECaLS DR5 para B1, sin sustitución; decisión definitiva después de evidencia |
| 4. Familia autoritativa | DOCUMENTED:coadds oficiales image/invvar y auxiliares; no model/JPEG |
| 5. Bandas | PROPOSED:g,r,z separadas, todas requeridas para una futura primaria multibanda; falta no imputada |
| 6. Arrays/auxiliares | PROPOSED:image,invvar,soporte/calidad y metadata PSF; nexp según significado; UNRESOLVED:producto efectivo de máscara |
| 7. Identidad/versionado | PROPOSED:release+brick+banda+producto+hash+headers, offsets/HDU y snapshot documental |
| 8. Coordenadas | PROPOSED:índice GZD5 autorizado y checksum/row estable, RA/Dec y frame/época documentados; incertidumbre/match explícitos |
| 9. O_cutout | PROPOSED:crop entero desde único brick; sin reciente/reescalar intensidades; propiedad de brick por geometría a congelar |
| 10. Geometría | UNRESOLVED:dimensiones/familia FOV y regla de ventana. 256×256 a escala nominal ≈67.072″ es antecedente C0, no decisión óptima ni garantía de contener morfología |
| 11. Grid | PROPOSED:nativo de brick, WCS preservado; no asumir grid idéntico entre bricks |
| 12. Resampling | PROPOSED:ninguno nuevo B1. B2 exige otra especificación y evidencia, no fallback |
| 13. Cobertura | PROPOSED:footprint y soporte por plano; fallo explícito si región no está respaldada; umbral científico futuro no elegido aquí |
| 14. Máscara/inválidos | PROPOSED:planos/flags de origen conservados+estados separados; UNRESOLVED:regla demostrable de calidad espacial |
| 15. Unidades/calibración | DOCUMENTED:coadd nanomaggies/píxel, calibración natural DECam AB; PROPOSED:no conversión propia ni renormalización |
| 16. Ruido | DOCUMENTED:semántica suma de inverse variances; PROPOSED:conservar originales, no suponer covarianza diagonal exacta ni S/N de apertura sin auditoría |
| 17. PSF | UNRESOLVED:producto/metadata suficiente por banda/posición; PROPOSED:proxy con alcance explícito solo si suficiente |
| 18. Vecinos | PROPOSED:conservar luz/contexto y metadatos disponibles; no segmentar, borrar ni elegir aislados ahora |
| 19. Metadata | PROPOSED:esquema §14 con desconocidos explícitos y procedencia de confusores |
| 20. Linaje/hashes | PROPOSED:producto/fragmentos, scripts futuros, parámetros, orden, UTC y outputs; sin escribir en archivo C0 |
| 21. O_pre | DOCUMENTED:fuera del crop; ninguna decisión de normalización/fondo/segmentación/rotación/reflexión |
| 22. Regenerabilidad | PROPOSED:valores,flags,WCS y metadata reproducibles desde entradas fijadas; bytes canónicos separados de contenedor |
| 23. Licencias | UNRESOLVED:uso científico, archivo local y redistribución de producto/derivados por proveedor |
| 24. Fallos | PROPOSED:NOT_AVAILABLE,PROVENANCE_CONFLICT,GEOMETRY_UNVERIFIED,SUPPORT_MISSING,QUALITY_UNKNOWN,UNIT_UNKNOWN,PSF_INSUFFICIENT,LICENSE_UNRESOLVED,RESOURCE_LIMIT; no imputar un éxito |
| 25. Decisiones aplazadas | DOCUMENTED:PREPROCESSING_BRANCH_SPEC futura definiría únicamente operaciones O_pre. Survey/grid/FOV/centro/soporte/licencias deben resolverse en contrato, no esconderse en preprocessing |
| 26. Pruebas futuras | PROPOSED:MIP-0 procedencia/geometría/auxiliares; MIP-1 pérdida; MIP-2/3 robustez; MIP-4 confusores; MIP-5 no-fuga, sin protocolo ni tolerancias creados ahora |

## 14. Required per-object provenance schema

**PROPOSED — esquema lógico de diseño, no tabla materializada:** cada campo tendrá valor, unidad/tipo, estado `verified/documented/approximate/unknown/absent/not_examined`, referencia de evidencia y motivo de nulidad. `absent` exige búsqueda/afirmación acotada; `not_examined` no significa ausente. Separar registro por objeto, observación, producto y región mediante IDs; no duplicar galaxias por vista.

| Grupo | Campos necesarios / relación |
|---|---|
| Identidad | galaxy_id, campaign, catálogo/record/version/SHA, source_row inmutable, coordinate_source, RA/Dec/frame/época/uncertainty, estado de match/duplicados |
| Observación/producto | survey,release,band,product_type,brick_id/name, footprint, pipeline metadata original disponible, exposición/contexto si existe |
| Recurso | authority,original_url,final_url,UTC,statusHTTP,ETag,total_size,provider_checksum,local_sha; distinción archivo completo/fragmento; licencia_id |
| FITS/decoder | HDU/header íntegro o hash+referencia, dtype,endian,BITPIX,BSCALE/BZERO,BLANK/NaN,compresión/quantización/layout,versión decoder |
| Región/bytes | rangos inclusivos de archivo, mapa de fragmentos; ventana espacial semia­bierta e índices 0/1-based inequívocos; ningún rango de bytes confundido con ROI |
| Geometría | WCS original y salida, transformación, escala local/nominal,huella,shape por banda,centro esperado/offset,registro/error y soporte |
| Estado por píxel | source_available,finite,quality_state,weight_state,flags originales; mask provenance y causas UNKNOWN. Si valor=0 con soporte/finitud/calidad válidos, valid_zero; si falta un eje no presumir validez |
| Fotometría/ruido | BUNIT original,unidad interpretada+fuente,calibración,sky upstream,ivar product/HDU/unit/grid,estado covarianza,coverage/nexp significado |
| PSF | tipo modelo/proxy,posición/banda,unidad,método/footprint,versión/calidad/error,campos no disponibles; sin kernel inventado |
| Confusores | redshift/selección/fotometría de auditoría con origen e incertidumbre; futuros S/N,área,seeing,background/vecinos con método y estado, sin calcular ahora |
| Transformaciones | stage=O_product/O_cutout/O_pre,grafo de padres,software/parameters/order,ventana,hashes de arrays/headers,identificador de contrato y Gate |
| Acceso | RAW_IMMUTABLE,SUBJECT_INDEX,CONFOUND_AUDIT,INTERPRETATION_LOCKBOX y futura partición/holdout; ninguna etiqueta accesible al constructor/selector |
| Resultado | status/reason por objeto y campo,fuentes faltantes,dominio de claims,hash de salida,licencia/atribución/redistribución permitida |

**PROPOSED:** máscaras originales y metadata no se pierden al producir flags derivados. Un píxel puede estar respaldado por datos y ser inválido o estar enmascarado; los estados no se reducen a una clase numérica excluyente. Ivar≤0, no finitud, nexp=0 y flags deben conservar sus significados distintos; las reglas de invalidación dependen de documentación, no de intuición. No se usa ANYMASK/ALLMASK catalogal para poblar una imagen.

## 15. Adversarial review

**PROPOSED — intentar invalidar B1, sin darlo por elegido.** Referencias MIP indican el Gate conceptual de MIPS que debería recibir la prueba en el futuro; no constituyen el protocolo de ese Gate.

| Riesgo que sobrevive | Consecuencia científica | ¿Bloquea adopción? | Evidencia necesaria / futuro Gate |
|---|---|---|---|
| Brick/tile boundary altera datos | Costuras, réplica de borde o selección espacial pueden parecer estructura | Sí si no se verifica soporte/selección | Descriptores+footprints, propietario único, casos frontera y pérdidas; MIP-0/1 |
| Misregistro de bandas | Falsas estructuras cromáticas y asimetrías | Sí | WCS y verificación astrométrica relativa con incertidumbre; MIP-0 |
| Ausencia convertida a cero | Huecos parecen zonas oscuras o estructura | Sí | Separación de estados y trazabilidad de máscara, controles valid-zero; MIP-0/1 |
| Máscaras/pesos mal interpretados | Saturación o ruido alteran forma y selección | Sí | Diccionario DR5 y vínculo a coadd, no sustitutos catalogales; MIP-0/4 |
| PSF domina la apariencia | Seeing simula concentración o elimina rasgos | Sí si efecto espacial material no acotable | Metadata/modelo/proxy suficientemente local y pruebas de suficiencia; MIP-0/4, luego MIP-2 |
| Grid común introduce correlación | Estructura de interpolación confundida con luz | Sí en B2 hasta justificación; B1 no la añade | Operador/ruido/PSF propagados e inyecciones predeclaradas; MIP-0/1 |
| Coadd ya correlacionado | Ivar diagonal infravalora incertidumbre de estructuras extensas | Sí para claims de S/N/tenuidad no auditables | Semántica de pesos, límites de covariance y uso admisible; MIP-0/4 |
| FOV trunca señal | Halos, colas y compañeros desaparecen | Sí si la afirmación presupone señal fuera del dominio | Regla/familia de ventanas congelada y sensibilidad; MIP-0/3 |
| Vecinos dominan el cutout | Ambiente o contaminación se confunden con morfología del target | No obliga a borrar vecinos; sí bloquea atribución no auditada | Contexto conservado y ramas posteriores con tratamiento explícito; MIP-3/4 |
| Píxeles preservados, metadata perdida | No se puede auditar observador ni regenerar | Sí | Esquema completo, hashes y linaje probado; MIP-0 |
| Crop “nativo” pasa por servicio oculto | Reaparece ambigüedad de O_cutout | Sí | URI de producto oficial, bytes/header/decoder y offsets locales; MIP-0 |
| Advertencia de precisión ignorada | Supuesta fidelidad morfológica excede producto | Sí para pregunta amplia hasta delimitar efecto | Evidencia oficial de mecanismos/limitaciones, alcance y posterior Gate de preservación; MIP-0/1/4 |
| Background upstream borra tenue | No recuperable por guardar crop | Sí si el claim requiere señal no identificable | Semántica sky y evaluación de límites sin prometer reversión; MIP-0/4 |
| Selección de un brick sesga muestra | Disponibilidad por posición/tamaño determina población | Sí si queda oculta; puede justificar dominio menor explícito | Flujo de cardinalidad y missingness técnica sin votos; MIP-0/4 |
| Preservación por compresión aparente | Igualdad de ROI es confundida con fidelidad a exposición original | Sí para esa afirmación | Separar coadd cuantizado/decodificado de detector; no afirmar más; MIP-0 |
| Recursos crecen a escala | Cache incompleta o degradación selectiva por conveniencia | Sí operacionalmente | Inventario único y presupuestos/reanudación previos; MIP-0 |
| Derechos no resueltos | Ruta no utilizable/redistribuible como se promete | Sí para operación afectada | Términos exactos por producto/derivado; MIP-0 |
| A/B sustentados solo en parecido | Certificación circular | Sí | Documentación nativa y transformaciones propias verificables independientemente; MIP-0 |

**INFERRED:** B1 elimina un resampling propio, no todos los mecanismos capaces de producir morfología instrumental. El expediente no debe promover “sin resampling adicional” a “sin pérdida de información”. Tampoco un mapa de nexp basta para distinguir saturación, interpolación upstream y falta de observación.

## 16. Unresolved questions

**UNRESOLVED — bloqueos de propuesta suficientemente sustentada:**

- Q1: ¿qué evidencia DR5 permite conservar o acotar la calidad espacial del coadd y distinguir inválido/enmascarado/ausente/valid-zero, incluyendo saturación y otros artefactos, más allá de finitud, ivar positiva y flags centrales?
- Q2: ¿qué describe suficientemente la PSF efectiva y el ruido correlacionado de ese producto en el dominio de interés, y qué límites concretos motivan la advertencia de precisión? FWHM catalogal y PSF de exposición son información útil, sin equivalencia automática al coadd.
- Q3: ¿qué términos autorizan uso científico, preservación local y eventual redistribución de recortes/metadata de DR5? Acceso público y CC-BY-4.0 del catálogo GZD no responden por imágenes.

**UNRESOLVED — decisiones del eventual contrato, no permiso para ejecutar:** dominio de objetos y tamaños/FOV, centro/window rounding, regla determinista de brick, condiciones de cobertura, tolerancias geométricas, suficiencia de PSF/ruido y política de derechos. Necesitan congelación antes de Gate/holdout; no se fijan mirando residuales anteriores. La evidencia solicitada debe hacer posible una elección defendible, no escogerla por nosotros.

**DOCUMENTED — decisiones excluidas de esta revisión:** normalización, algoritmo de background, segmentación, rotación/reflexión, target PSF de homogenización, encoder, clustering y tolerancias de holdout. Tampoco se decide abrir etiquetas.

## 17. Resource and licensing considerations

**OBSERVED — inventario histórico, no presupuesto nuevo:** 514 HEAD satisfactorios: 42 image para12objetos=584127360bytes (557.07MiB),354nexp de118bricks=44412480bytes (42.36MiB),118Tractor=806607360bytes (769.24MiB). Suma1435147200bytes. No incluye todos los image/ivar/máscaras/PSF para96 ni para253286 objetos. Los restantes saldos que aparecen en ese snapshot describen su fecha; no son el saldo final ni autorización vigente. Subimage96 registró168871911bytes adicionales en su etapa, sin costes completos de auxiliares/validación. No se usa ninguno para prometer un factor de ahorro universal.

**INFERRED — fórmulas de capacidad, no benchmarking:** para N objetos, B bandas, H×W y s bytes por muestra, arrays image+ivar ocupan N×B×H×W×2s antes de contenedores/compresión. Escenario ilustrativo float32,3bandas,256²:1.5MiB/objeto,144MiB para96,≈371.02GiB para253286 si todos produjeran un único bundle. No fija N,FOV,dtype ni tasa de admisión. Añadir máscaras/soporte (N×B×H×W×bytes_estado),nexp,headers,PSF,catálogos,originales/fragmentos,checkpoints y copias. Una imagen+ivar completa de3600²×3bandas,float32 suma311040000bytes por brick sin comprimir; no multiplicar automáticamente118bricks por toda la cohorte. Compresión/auxiliares cambian tamaños y RAM.

**PROPOSED:** presupuestar por recursos únicos compartidos y rangos necesarios, no objetos×archivo completo. Range puede limitar transferencia solo donde el layout/servidor/versionado permiten obtener y conservar todos los bytes requeridos. `gzip` de archivo, compresión en tiles y cuantización son casos distintos. No asumir que invvar/nexp/mask/PSF admiten la misma estrategia que42image históricos. Deduplicación no autoriza borrar inputs necesarios para regeneración.

**UNRESOLVED:** CPU/RAM/tiempo y transferencia de futura construcción a escala no medidos; no se realiza benchmark. El nuevo experimento necesitará un presupuesto separado y explícito. Los contadores C0 quedan archivados, no se reinician ni se amplían. Esta revisión consume cero red y solo produce este Markdown.

**UNRESOLVED — licencias:** el registro S2 acredita CC-BY-4.0 del catálogo/versionado correspondiente. Para coadds, auxiliares y respuestas del servicio, el registro conserva términos pendientes. La página de archivos enlazada o un copyright del sitio no bastan para autorizar redistribución. Un permiso de software tampoco licencia imágenes. No se afirma incompatibilidad legal; falta evidencia del permiso apropiado. El contrato futuro debe separar análisis local, archivo de originales, publicación de recortes y redistribución de metadata/catálogos.

**PROPOSED — ejecución futura pesada:** antes de autorizarla, la futura especificación deberá entregar script reproducible, comando exacto probado (`--help`/`--dry-run`, límites), política de red, inputs, CPU/RAM/disco/tiempo, outputs,log,checkpoints/restart y sentinel técnico conforme AGENTS. Aquí no se propone una operación pesada ni se inventa un comando para software inexistente. Ningún comando histórico de C0 es reutilizado como instrucción de ejecución.

## 18. Relationship to future preprocessing and MIP Gates

**DOCUMENTED:** MIPS exige contrato, PREPROCESSING_BRANCH_SPEC y MIP_GATE_PROTOCOL congelados antes de implementar. Esta tarea solo entrega la primera revisión comparativa; las otras dos especificaciones no se inician. La salida B tampoco autoriza redactarlas automáticamente.

**PROPOSED:** si llegara a aprobarse un contrato nuevo, MIP-0 tendría que probar fuente/headers/geometría, offsets y bandas, cobertura en boundaries, decodificación/extracción, relaciones de auxiliares, PSF/ruido, unidades, regenerabilidad y no-fuga dentro del dominio declarado. Las tolerancias deben derivarse de pregunta/resolución/error admisible y congelarse antes de pruebas confirmatorias, sin reutilizar los residuales C0 como tolerancia. Pruebas de rasgos sintéticos y errores conocidos de observador se definirían después, sin ejecutarlas ahora.

**PROPOSED:** MIP-1 evaluaría operaciones O_pre y pérdidas; MIP-2/3, estabilidad selectiva y dependencia de ramas; MIP-4, PSF/ruido/brillo/selección/vecinos; MIP-5, interpretación externa sin fuga. Un PASS hipotético futuro no cambia ningún estado C0. Un éxito técnico de extracción no decide MIP-0.

## 19. Exit analysis

**INFERRED — por qué no A ahora:** hay producto image oficial con semántica documentada y una opción O_cutout controlable, pero no un contrato completo suficientemente sustentado: Q1–Q3 afectan propiedades protegidas y uso viable. No se convierte un listado de condiciones pendientes en autorización de la ruta nativa.

**INFERRED — por qué no concluir C definitivo en esta revisión:** la evidencia no demuestra imposibilidad de DR5 nativo; identifica vacíos concretos documentales y de enlace de auxiliares que podrían tener respuesta independiente. La etapa siguiente debe discriminar eso y terminar, no extender indefinidamente la búsqueda. A permanece referencia histórica; C auxiliar limitada; D diferida. Se prioriza evaluar Q1–Q3 para B1 por control de O_cutout y documentación de O_product, no por coste o cache.

### Una única etapa de evidencia propuesta: E-OC1

**PROPOSED — naturaleza:** revisión documental acotada de suficiencia de DR5 coadd para B1, sin creación de imágenes, tests numéricos nuevos, consulta de etiquetas ni reapertura de C0. No está iniciada ni autorizada para adquisición por este documento. Pregunta exacta: **¿puede enlazarse el producto image/ivar DR5 a información de calidad y resolución/ruido con limitaciones explícitas suficientes para preservar A10/A11 y auditar B2–B4, y a términos de uso compatibles, sin suponer equivalencias nuevas?**

**PROPOSED — entradas locales existentes exactas:** MIPS y hashes de §2; S5.raw secciones Image Stacks/PSF/Sky Level/Photometry, S6.raw tablas y coadd image/invvar/nexp, listado DR5_BRICK_1853p160_DIRECTORY.raw, C0_SOURCE_REGISTER.yaml, C0_REMOTE_FILE_MANIFEST.csv, C0_RANGE_SUBSET_RESULTS.json/ACCEPTANCE.json, C0_SUBIMAGE_SUMMARY.json, C0_FITS_SEMANTICS_REPORT.md, C0_DR5_RESOURCE_INVENTORY_SUMMARY.json y cierre C0. Solo reportes/metadatos, sin decodificar imágenes ni acceder a catálogos de interpretación. Releerlos por sí solo no constituye evidencia nueva que cierre Q1–Q3.

**UNRESOLVED — documentos oficiales que faltan para discriminar, sin presumir que existan:** un expediente con un máximo de tres piezas específicas, o una declaración oficial que cubra sus tres contenidos:

| Pieza requerida | Autoridad y documento/contenido exacto solicitado | Pregunta que debe contestar | Localización conocida / límite |
|---|---|---|---|
| DQ-DR5 | Especificación oficial DR5 de calidad/máscaras del coadd y propagación de flags desde exposiciones | Qué producto/plano o garantía documentada distingue soporte, saturación/artefactos e invalidez; significado de ivar/nexp=0; bits y vínculo geométrico | S6 de DR5 es punto de referencia local; no hay URL de documento suficiente verificada. Solicitar a responsables Legacy Surveys DR5; no usar bitmasks DR11 del menú |
| RES-DR5 | Nota oficial DR5 sobre límites de Image Stacks, PSF efectiva y semántica de incertidumbre del coadd | Qué pérdida/artefactos motivan advertencia de precisión; qué PSF/proxy es pertinente y qué ruido/covarianza puede auditarse | S5 secciones Image Stacks/PSF y S6 invvar identifican la cuestión, no su resolución; se requiere nota/clarificación vinculada a la release/productos |
| RIGHTS-DR5 | Términos oficiales aplicables a imágenes y auxiliares DR5, con alcance de derivados | Uso científico/archivo local/redistribución y atribución, incluyendo proveedor correspondiente | Responsables Legacy Surveys y archivo proveedor NERSC/NOIRLab según producto; URL suficiente no fijada localmente. No inferirla ni heredar licencia Zenodo |

**PROPOSED — adquisición futura de evidencia, no ejecución:** el usuario podrá aportar localmente esas piezas con URL/autoridad, release, fecha y original preservado, o autorizar por separado un plan documental limitado a ellas. No envío solicitudes a terceros ni realizo HTTP. Máximo tres documentos,10MiB combinados; sin adjuntos de imágenes/catálogos ni recorridos recursivos. Si se requiere red para localizarlos, la autorización posterior deberá fijar endpoints y límites de peticiones antes de ejecutarse; la falta actual de URL no se resuelve mediante una búsqueda abierta. Un documento genérico no aplicable a DR5 cuenta como insuficiente, no como permiso de ampliar el expediente. Una respuesta puede afirmar inexistencia/limitación: es un resultado informativo válido.

**PROPOSED — procedimiento de E-OC1:** una revisión del expediente sellado, verificando autenticidad/procedencia y aplicabilidad a los archivos/versiones; mapear afirmaciones a A10/A11/B2/B3/B4/O1 y registrar contradicciones. No proponer productos inexistentes para completar filas. Una licencia clara sin calidad, o una PSF clara sin máscara, no cierra conjuntamente la pregunta. No exige identidad forense si una garantía independiente suficiente verifica la propiedad relevante. Si se necesitan nuevos píxeles para siquiera formular un contrato, esta etapa no los ejecuta y debe declarar insuficiencia de su alcance.

**PROPOSED — presupuesto de revisión:** cero red durante la lectura del expediente local; sin FITS/image decode ni cálculo bulk. Lectura de metadata/documentos ≤64MiB incluyendo las tres piezas; outputs ≤2MiB. No cómputo intensivo ni necesidad de CLI pesado; la interpretación humana/agente puede requerir varias lecturas, sin proceso de espera/polling. No hay estimación ficticia de tiempo de respuesta de proveedores ni permiso para esperar indefinidamente.

**PROPOSED — outputs futuros, fuera de C0:** `E_OC1_EVIDENCE_REGISTER.json` con hashes/autoridad/versiones y ausencias; `E_OC1_SUFFICIENCY_REVIEW.md` con matriz de Q1–Q3, contradicciones y una conclusión única. Ninguno se crea ahora. Una eventual herramienta de inventario podría emitir un sentinel técnico de integridad, nunca aprobación científica; no se implementa ni necesita comando en esta fase documental.

**PROPOSED — todos los desenlaces y parada:**

1. Expediente íntegro con evidencia afirmativa suficiente para los tres contenidos y sin contradicción material: se permite **redactar para revisión humana** un contrato concreto B1 con dominio/limitaciones; aún no adopción, adquisición, ejecución o PASS. Tolerancias y pruebas futuras no se declaran satisfechas por documentación.
2. Evidencia directa de incompatibilidad con requisitos protegidos, licencia incompatible para uso necesario o ausencia de vía de calidad/resolución suficiente: **NO_CURRENTLY_ADMISSIBLE_ROUTE** para las rutas consideradas bajo esta evidencia. No reducir MIPS ni abrir D automáticamente.
3. Documento ausente, genérico/no versionado, dudosa autoridad, contradicción no resoluble con las tres piezas, o resultados que solo prometen información futura: **NO_CURRENTLY_ADMISSIBLE_ROUTE con evidencia disponible**, por insuficiencia, no demostración de inexistencia física. No encadenar otro E-OC1 ni terminar PENDING.
4. Fallo de integridad de MIPS o inputs: detener la revisión sin usar la pieza alterada; informar autoridad no verificada. No evaluación científica basada en ese expediente. Una reposición válida necesitaría autorización explícita, no sustitución silenciosa.

**PROPOSED — regla de cierre:** una sola pasada sobre el expediente recibido; si el usuario decide cerrarlo sin documentos faltantes, aplica desenlace3. La etapa no comienza mientras el expediente no esté fijado o se declare explícitamente incompleto para su cierre. No plazo indefinido de investigación ni ampliación de muestra/rangos. La salida presente es B, una decisión terminada de diseño, no PENDING de C0 ni una etapa E-OC1 corriendo.

**INFERRED — poder discriminante:** estas piezas podrían convertir vacíos de calidad/resolución/derechos en propiedades/limitaciones verificables o demostrar que no existe soporte suficiente para proponer B1. Más igualdad entre imágenes no identifica esos significados ni derechos. Por eso ni adquirir los seis rangos, ni reproducir mejor LUT, ni conseguir tres arrays completos adicionales discrimina Q1–Q3.

## 20. Explicit outcome A, B or C

**B — `ONE_BOUNDED_EVIDENCE_STAGE_REQUIRED`.**

**PROPOSED:** priorizar el expediente E-OC1 para la candidata B1 (crop nativo local de un brick), sin recomendar aún una ruta adoptable ni presentar contrato suficientemente sustentado. No ejecutar E-OC1 automáticamente. Bloqueos concretos: calidad/máscaras, PSF y ruido efectivos/límites de precisión del coadd, y derechos aplicables. Geometría propia, FOV, ventanas y pruebas deben congelarse después, si esa evidencia permite proponer un contrato.

**OBSERVED — alcance de esta entrega:** se creó únicamente OBSERVATIONAL_CONTRACT_REVISION.md. No se modifican C0, autoridades, código, contadores, resultados ni snapshots. No red, adquisición, normal/subimage nuevos, crop/mosaico, benchmark, entrenamiento, modelo ni materialización. No PREPROCESSING_BRANCH_SPEC.md ni MIP_GATE_PROTOCOL.md. C0 conserva A/B=PASS, C=INCONCLUSIVE y STOP global; D/E/F=INCONCLUSIVE por cierre anticipado. Esta salida B pertenece exclusivamente a la revisión metodológica nueva.
