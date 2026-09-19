# OC-2 — triage de candidatas observacionales

## 1. Estado, autoridad y alcance

**DOCUMENTED:** v0.1, 2026-09-18. La instrucción adjunta del usuario congela los tres desenlaces de ruta y el desenlace global de esta triage. OC-2 es una etapa metodológica posterior a E-OC1; no es una clasificación por puntuaciones, un contrato observacional aprobado ni una ejecución de OC-3.

**OBSERVED:** MIPS se leyó íntegramente y su SHA-256 coincide con el esperado: `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24`. Se consultaron AGENTS, seed, especificación/addendum C0, revisión contractual y los dos entregables E-OC1, además de cierre/ledger C0 como antecedentes de solo lectura. No existía un documento OC-2 previo en el directorio al iniciar esta tarea: se congela aquí la triage comunicada por el usuario, con contraste documental, sin atribuirle experimentos anteriores inexistentes.

**OBSERVED:** C0 permanece CLOSED, global STOP (A/B PASS; C INCONCLUSIVE; D/E/F INCONCLUSIVE por cierre anticipado). E-OC1 permanece CLOSED, `NO_CURRENTLY_ADMISSIBLE_ROUTE_WITH_AVAILABLE_EVIDENCE`. Ningún contenido DR9 se importa retrospectivamente a DR5.

**DOCUMENTED:** MIPS gobierna la preservación; los IDs A10/A11/B2/B3/B4/O1 se usan con las definiciones de §6 de la revisión contractual. La autorización nueva permite comparar estas tres rutas y diseñar el piloto, no modificar autoridades ni implementar sus decisiones. La mención de DR9 es un cambio prospectivo explícito de observador, no una sustitución de release dentro de C0.

**DOCUMENTED — vocabulario:** OBSERVED identifica evidencia local realmente examinada; DOCUMENTED, una afirmación atribuida a una fuente; INFERRED, una consecuencia razonada; PROPOSED, diseño sin ejecución; UNRESOLVED, evidencia insuficiente. Una propiedad documentada no es una propiedad comprobada en archivos del futuro piloto.

## 2. Expediente documental y límites

**OBSERVED:** Revisión de documentación oficial el 2026-09-18 mediante navegación textual, sin descargar imágenes, catálogos, PSFs ni ejecutar endpoints de datos. No se guardan nuevos snapshots porque esta entrega está limitada a dos Markdown. Las páginas vivas no se presentan como expediente de ejecución sellado. Una dirección HSC inicialmente probada no era accesible; se resolvió su página oficial PDR3 correcta. No se deriva una conclusión científica de ese error.

| ID | Fuente / sección | Alcance documental |
|---|---|---|
| D1 | [DR9 files](https://www.legacysurvey.org/dr9/files/), Image Stacks | DOCUMENTED: inventario y semántica de productos, no verificación de disponibilidad por ubicación |
| D2 | [DR9 description](https://www.legacysurvey.org/dr9/description/), PSF, Sky Level, Image Stacks | DOCUMENTED: construcción upstream y limitaciones |
| D3 | [DR9 bitmasks](https://www.legacysurvey.org/dr9/bitmasks/), MASKBITS | DOCUMENTED: diccionario de bits; la página actual menciona también bits posteriores, que no se incorporan a DR9 |
| D4 | [DR9 issues](https://www.legacysurvey.org/dr9/issues/) | DOCUMENTED: clases de fallos y diferencias de release |
| D5 | [DR9 PSF](https://www.legacysurvey.org/dr9/psf/) | DOCUMENTED: PSF por exposición y tratamiento de alas, no garantía del modelo efectivo del coadd |
| D6 | [Viewer URLs](https://www.legacysurvey.org/viewer/urls), snapshot histórico S7.raw | OBSERVED: snapshot local contiene enlace coadd-psf para ls-dr9; no se invoca |
| H1 | [HSC PDR3 processing](https://hsc-release.mtk.nao.ac.jp/doc/index.php/processing__pdr3/) | DOCUMENTED: máscaras/interpolación, warps, coadd y PSF; cadena upstream |
| H2 | [HSC PDR3 known problems](https://hsc-release.mtk.nao.ac.jp/doc/index.php/known-problems__pdr3/) | DOCUMENTED: limitaciones de artefactos y deblending |
| H3 | [HSC PDR3 FAQ](https://hsc-release.mtk.nao.ac.jp/doc/index.php/faq__pdr3/) | DOCUMENTED: modelos PSF en archivos/coadd y distinción de productos |
| H4 | [HSC PDR3 data access](https://hsc-release.mtk.nao.ac.jp/doc/index.php/data-access__pdr3/) | DOCUMENTED: acceso registrado y alcance de uso del archivo |
| L1 | E_OC1_EVIDENCE_REGISTER.json / E_OC1_SUFFICIENCY_REVIEW.md | OBSERVED: derechos Legacy parcialmente documentados; no cierre nuevo de ese asunto |

**OBSERVED:** D6 local: `c0/provenance/raw_metadata/S7.raw`, SHA-256 `c93fd47e9764b1096e873fadf989d4d8078a373e123f11929a1a014adaf4e1af`, sección «PSF model for coadd». Contiene `coadd-psf/` con `layer=ls-dr9`. El código público preservado se identifica en C0_NORMAL_CODE_SOURCES.json; no es certificación del despliegue. **UNRESOLVED:** respuesta actual, linaje al brick, pesos, región, banda y release concreta del modelo. Su disponibilidad documental motiva una prueba, no satisface A11/B4 por anticipado.

## 3. Matriz de requisitos, sin puntuaciones

**DOCUMENTED:** D1 describe maskbits ópticos espaciales, nexp por píxel y psfsize como FWHM promedio ponderado por píxel. La imagen y su invvar son productos separados. **INFERRED:** Estos auxiliares mejoran materialmente la auditabilidad potencial respecto del expediente DR5 de E-OC1, sin demostrar suficiencia. [D1](https://www.legacysurvey.org/dr9/files/).

**DOCUMENTED:** D2 conserva coaddition Lanczos-3 y la limitación de que los stacks no fueron diseñados para precisión. Describe modelos PSF espaciales por exposición y sustracción de cielo upstream; DR9 incorpora correcciones adicionales de patrones/fringing. **INFERRED:** Crop entero evita una transformación propia, no revierte las upstream. [D2](https://www.legacysurvey.org/dr9/description/).

| Requisito heredado | R1 — coadd DR9 nativo | R2 — exposiciones DR9 | R3 — HSC PDR3 |
|---|---|---|---|
| A10 calidad espacial | DOCUMENTED: D1/D3 ofrecen flags espaciales. UNRESOLVED: exhaustividad y causas no codificadas | DOCUMENTED: mapas DQ/weight y defectos en exposiciones. UNRESOLVED: propagación a observación canónica propia | DOCUMENTED: H1 describe máscaras y defectos interpolados. UNRESOLVED: equivalencia de estados con Legacy |
| A11 resolución | DOCUMENTED: mapa FWHM y servicio candidato. UNRESOLVED: PSF efectiva suficiente | DOCUMENTED: PSF espacial por CCD, D2/D5. INFERRED: combinarla exige decisiones nuevas | DOCUMENTED: H1/H3 ofrecen PSF coadd. UNRESOLVED: dominio comparativo y filtros distintos |
| B2 pesos/ruido | DOCUMENTED: invvar coadd. INFERRED: no representa covarianza completa | INFERRED: mayor acceso a entradas, pero registro/mezcla propios alteran ruido | DOCUMENTED: H1 remuestrea y combina. UNRESOLVED: covarianza efectiva para el experimento |
| B3 cielo/luz tenue | DOCUMENTED: cielo upstream D2. UNRESOLVED: pérdida relevante no recuperable por crop | INFERRED: controlar entradas no recupera señal ya sustraída; recalibración sería otra ruta | DOCUMENTED: H1 distingue cielo global y local. INFERRED: elegir producto cambia O_product |
| B4 auditoría PSF | PROPOSED: enlazar modelo, posición, banda, versión y mapa; sin asumir equivalencia | DOCUMENTED: modelos exposición. PROPOSED: posible oráculo, no PSF sintética adoptada | DOCUMENTED: modelos accesibles por posición. UNRESOLVED: validación cross-survey |
| O1 derechos | UNRESOLVED: distinguir análisis, archivo y redistribución científica; L1 no licencia todo DR9 | UNRESOLVED: verificar términos de proveedor/exposiciones, no heredarlos del viewer | DOCUMENTED: H4 restringe archivo a ciencia/educación no comercial. UNRESOLVED: redistribución científica y derivados |
| Continuidad observador | INFERRED: familia Legacy grz y bricks facilita vínculo, no identidad de producto ni población | INFERRED: mismas entradas instrumentales posibles, distinta unidad observacional | INFERRED: cambia telescopio, instrumento, muestreo, filtros, profundidad, PSF, footprint y procesamiento |
| Nuevo O_product propio | PROPOSED: limitar O_cutout a crop exacto; riesgo upstream conservado | INFERRED: alto si se construye observación única multiexposición | INFERRED: producto de otro observador; armonización posterior sería transformación adicional |

**DOCUMENTED:** D2 documenta acceso a pesos de exposiciones; el código público local preservado enlaza productos `oow`/`ood`. D5 describe PSF extendida y modificaciones de alas DECam. **UNRESOLVED:** no se comprobó ningún archivo exposición y el acceso más detallado no demuestra una observación canónica suficiente. [D2](https://www.legacysurvey.org/dr9/description/), [D5](https://www.legacysurvey.org/dr9/psf/).

## 4. Desenlaces de las tres rutas

### R1 — Legacy Surveys DR9 native coadd

**DOCUMENTED — decisión congelada por instrucción:** `CANDIDATE_REQUIRES_BOUNDED_PIXEL_PILOT`.

**INFERRED:** Hay una mejora concreta del bundle auxiliar y continuidad geométrica suficiente para formular una prueba discriminante. Persisten incertidumbres de calidad, PSF efectiva, correlación y derechos. No se presupone que maskbits sea exhaustivo, que psfsize sea un kernel ni que pesos diagonales describan toda la incertidumbre. La posibilidad de obtener una PSF no demuestra que corresponda al mismo coadd. No hay aprobación de contrato.

### R2 — Legacy Surveys DR9 individual exposures

**DOCUMENTED — decisión congelada por instrucción:** `CANDIDATE_NOT_CURRENTLY_ADMISSIBLE_AS_PRIMARY`.

**INFERRED:** El acceso a DQ, pesos y PSF espacial ofrece un posible control independiente. Pero convertir múltiples exposiciones en una vista única trasladaría a este proyecto registro, interpolación, ponderación, rechazo, combinación PSF y elección de exposiciones. Eso crea un O_product propio material que este diseño no justifica. **PROPOSED:** reservar como posible validación/oráculo futuro, sin adquirir, implementar ni usarlo como fallback automático de OC-3.

### R3 — HSC-SSP PDR3

**DOCUMENTED — decisión congelada por instrucción:** `CANDIDATE_SUITABLE_ONLY_AS_CROSS_SURVEY_OBSERVER`.

**DOCUMENTED:** H1 describe warps, rechazo de artefactos antes del coadd y combinación de modelos PSF; usa Lanczos de orden 5 en PDR3. H3 permite recuperar PSF por posición. **INFERRED:** Esta trazabilidad potencial no hace equivalentes los observadores. [H1](https://hsc-release.mtk.nao.ac.jp/doc/index.php/processing__pdr3/), [H3](https://hsc-release.mtk.nao.ac.jp/doc/index.php/faq__pdr3/).

**PROPOSED:** Solo un futuro experimento pareado de robustez, con identidades/coordenadas fijadas independientemente y missingness auditada. No redefine sujetos ni reemplaza silenciosamente población primaria. No se abre adquisición HSC.

## 5. Sentinels de problemas DR9

**DOCUMENTED — D4:** NOBS de Tractor cuenta solapamientos incluso enmascarados; NEXP del coadd cuenta contribuciones de peso positivo. Hubo 1691 bricks sur reprocesados por corrupción: RELEASE 9012 frente a 9010. También se documentan 52 galaxias omitidas del SGA utilizado, sin flag GALAXY; algunos bleed trails catalogados como fuentes en MzLS/BASS; y efectos de pattern-noise Mosaic-3 sobre fotometría z y posibles pérdidas de envolventes. [D4](https://www.legacysurvey.org/dr9/issues/).

| Clase | PROPOSED: control OC-3 | Límite de inferencia |
|---|---|---|
| NOBS ≠ NEXP | Usar NEXP nativo; no descargar catálogos ni imponer igualdad | INFERRED: una diferencia semántica no es corrupción |
| Bricks rehechos / RELEASE | Congelar manifiesto de generación; no mezclar archivos antiguos y corregidos | UNRESOLVED: pertenencia de los dos bricks hasta preflight |
| GALAXY incompleto | Registrar aplicabilidad de issue; nunca declarar limpio por bit ausente | INFERRED: no implica todas las máscaras incorrectas |
| Bleed trails | Conservar flags/estados desconocidos y riesgo por régimen | UNRESOLVED: no se promete detectar todos sin exposición |
| Mosaic-3 norte | Auditoría separada z/norte; no declarar precisión LSB universal | INFERRED: no condena todo norte ni todo grz |

**DOCUMENTED:** D3 asigna significados diferentes a saturación, ALLMASK y regiones de foreground; no todos los bits expresan invalidez física. **PROPOSED:** preservar entero completo y diccionario versionado, sin convertir todo bit no nulo en descarte. [D3](https://www.legacysurvey.org/dr9/bitmasks/).

## 6. Limitaciones propias de HSC

**DOCUMENTED:** H2 reconoce over-shredding/deblending de galaxias cercanas estructuradas y artefactos residuales, incluidos ghosts. H1 distingue imágenes con cielo global de las imágenes con sustracción local usadas para detección/mediciones. [H2](https://hsc-release.mtk.nao.ac.jp/doc/index.php/known-problems__pdr3/), [H1](https://hsc-release.mtk.nao.ac.jp/doc/index.php/processing__pdr3/).

**INFERRED:** Deblending afecta la atribución de flujo a fuentes; no implica que todos los píxeles del coadd hayan sido reemplazados por galaxias deblendadas. La decisión de cielo sí puede alterar luz extendida. Son efectos del observador que exigen comparación explícita, no pruebas de superioridad/inferioridad de HSC. Más profundidad no garantiza equivalencia morfológica.

## 7. Identidad, derechos y continuidad de población

**OBSERVED:** La población histórica reconciliada es GZD-5. **DOCUMENTED:** El pedido actual habla de población candidata GZ-DESI. **UNRESOLVED:** no existe aquí una reconciliación autorizada/materializada entre ambas. Se conserva esa distinción; no se renombra SUBJECT_INDEX ni se importa una nueva selección.

**PROPOSED:** OC-3 usará ubicaciones técnicas, no una muestra de galaxias. Un futuro vínculo GZ-DESI exigiría IDs/coordenadas/versiones y duplicados resueltos sin votos/predicciones, con todas las vistas del mismo sujeto en el mismo split. DR9 grz y la misma familia de bricks no prueban igualdad de filtro, calibración, población o presentación a voluntarios. HSC sería observación adicional del sujeto ya fijado.

**OBSERVED:** L1 documenta licencia de capas de imágenes y agradecimientos, dejando indeterminado el alcance FITS/derivados. **PROPOSED:** para OC-3 no redistribuir píxeles; exigir evidencia aplicable de análisis y preservación local antes de adquisición. Deshabilitar redistribución no suple un permiso de uso desconocido. Para HSC, H4 describe acceso registrado científico/educativo; no se interpreta como licencia ilimitada de derivados. [H4](https://hsc-release.mtk.nao.ac.jp/doc/index.php/data-access__pdr3/).

## 8. Resultado global y congelación

**DOCUMENTED — resultado único OC-2:** `ONE_CANDIDATE_ADVANCES_TO_BOUNDED_PIXEL_PILOT`.

**PROPOSED:** Solo R1 avanza a diseño de una prueba técnica acotada, definida en OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md. Esto no inicia OC-3, no aprueba DR9, no dicta un contrato final y no altera C0/E-OC1. Un resultado negativo del piloto será admisible.

**OBSERVED:** Esta entrega crea únicamente este documento y la especificación OC-3. No se adquirieron datos astronómicos, se abrieron etiquetas, se materializó una cohorte ni se ejecutaron pruebas de píxeles. Git no está inicializado; no se reparó. La comprobación local final encontró exactamente los dos Markdown nuevos, cero cambios de inventario/tamaño/mtime en 6584 archivos preexistentes y cero cambios en los 14 hashes controlados de autoridades/E-OC1. No se hizo rehash masivo de datos ni se accedió al lockbox.
