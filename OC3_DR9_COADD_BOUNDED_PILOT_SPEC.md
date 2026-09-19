# OC-3 — especificación de piloto técnico acotado DR9

## 1. Estado y límites de autoridad

**PROPOSED:** v0.1, 2026-09-18. DISEÑO SOLAMENTE; OC-3 NO INICIADO. Este documento congela preguntas, selección, pruebas, presupuestos propuestos y reglas de decisión antes de adquirir píxeles. No contiene resultados. No autoriza implementación ni red de datos; requerirá autorización humana posterior y un manifiesto de ejecución sellado conforme a estas reglas.

**OBSERVED:** MIPS verificado: SHA-256 `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24`. Autoridades leídas: MIPS, revisión contractual, registro/revisión E-OC1 y AGENTS; C0 solo como antecedente. OC-2 congela `ONE_CANDIDATE_ADVANCES_TO_BOUNDED_PIXEL_PILOT`. C0 permanece CLOSED/STOP y E-OC1 CLOSED/`NO_CURRENTLY_ADMISSIBLE_ROUTE_WITH_AVAILABLE_EVIDENCE`.

**DOCUMENTED:** La autorización de diseño OC-3 es explícita y posterior; no ejecuta las fases del seed ni evade MIPS §13. No implementa una nueva ruta primaria: las especificaciones de preprocessing y Gates MIP requeridas antes de esa implementación continúan fuera de alcance. Tampoco declara MIP-0 PASS.

**DOCUMENTED — categorías:** OBSERVED = artefacto local examinado; DOCUMENTED = fuente atribuida; INFERRED = consecuencia con límites; PROPOSED = requisito del piloto no ejecutado; UNRESOLVED = evidencia aún no disponible. Todas las instrucciones operativas siguientes son PROPOSED, congeladas para una futura implementación, no hallazgos.

## 2. Pregunta e hipótesis falsable

**PROPOSED — pregunta:** ¿Puede un crop directo por índices enteros de productos oficiales DR9, acompañado de su información nativa de calidad, ruido y PSF, hacer medibles y auditables las limitaciones observacionales del coadd lo suficiente para justificar la redacción de un contrato restringido?

**PROPOSED — H-OC3:** Un recorte local sin nuevo remuestreo de image DR9, junto con invvar, nexp, maskbits, psfsize e información coadd-PSF, puede caracterizar O_product dentro de un dominio morfológico explícitamente acotado.

**PROPOSED — adversario:** intentar romper la coherencia de ese bundle con bordes, flags, poco soporte y variación PSF; identificar estados no distinguibles y modelos sin linaje. Una igualdad de arrays propia no salva semántica desconocida. El piloto no mide recuperación de barras/brazos, ni demuestra fidelidad morfológica universal. Sus restricciones impedirán que la eventual redacción prometa eso.

**DOCUMENTED:** Las fuentes D1–D6/H1–H4 están identificadas en OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md. [DR9 files](https://www.legacysurvey.org/dr9/files/) documenta los auxiliares; [DR9 description](https://www.legacysurvey.org/dr9/description/) documenta Lanczos-3 upstream y la limitación de precisión. **INFERRED:** ningún crop puede eliminar esa historia. Los píxeles del coadd son nativos de ese producto, no del detector.

## 3. Unidad, dominio y exclusiones

**PROPOSED:** Seis ubicaciones técnicas distintas, en exactamente dos bricks como máximo: uno sur DECaLS y uno norte BASS/MzLS. Tres bandas g/r/z por ubicación: hasta 18 combinaciones. No son seis sujetos galácticos, no estiman completitud poblacional y no se convierten en train/dev/holdout de ciencia.

**PROPOSED:** Cada ventana solicitada es 129×129 píxeles nativos (radio 64), fijada por conveniencia metrológica: tamaño impar, centro entero, espacio para bloques de autocorrelación y tres puntos PSF. No se afirma que contenga una galaxia o luz extendida. A escala nominal corresponde a 33.798 arcsec por lado; la escala efectiva se verificará en WCS. No cambiar dimensiones tras ver datos.

**PROPOSED:** El claim máximo es auditabilidad del bundle en esas regiones y regímenes concretos para preparar un contrato. No precisión de fotometría extendida, inventario exhaustivo de artefactos, astrometría absoluta validada, covarianza completa ni generalización a toda DR9. La referencia de futura población GZ-DESI no autoriza acceder a su catálogo. GZD-5 histórico sigue siendo otra población.

**PROPOSED — prohibiciones:** cero votos/predicciones Galaxy Zoo/Zoobot, Tractor TYPE, variables físicas, catálogos morfológicos, selección visual o final science holdout. Ningún entrenamiento, embedding, modelo nuevo, clustering, PCA, UMAP, anomalías o segmentación. No normalización, nueva sustracción de cielo, rotación, reflexión, resize, homogenización PSF, recentrado morfológico, imputación, mosaico, RGB ni aplicación de máscara modificando intensidades. Leer el modelo PSF del proveedor y calcular descriptores no es entrenar un modelo.

## 4. Selección determinista antes de abrir intensidades

### 4.1 Inputs técnicos y exclusión del holdout

**PROPOSED:** El futuro manifiesto de entradas usará únicamente: región, brickname/brickid, límites geométricos, WCS técnico, cobertura grz, RELEASE/generación y pertenencia al listado oficial de bricks reprocesados. Datos de referencia: resúmenes de bricks DR9 por región, listado de issues y metadatos oficiales de productos. No leer columnas de tipos, número de galaxias, color, magnitud o ajuste de fuente aunque estén presentes en esos resúmenes.

**PROPOSED:** Un custodio suministrará allowlist geométrica de bricks de desarrollo disjuntos del holdout científico. El proceso no abre el holdout para fabricar esa allowlist. Si aún no existe holdout, los dos bricks completos, todas sus ventanas y exposiciones compartidas conocidas quedan marcados como desarrollo instrumental y excluidos de la futura evaluación confirmatoria. Si no puede certificarse esta separación, no se adquieren mapas. No se reutiliza la muestra C0 como autorización de acceso.

**PROPOSED:** Elegir un brick por región entre aquellos con cobertura grz documentada y autorizados. En sur usar el subconjunto del listado oficial corregido 9012, para ejercitar procedencia de reprocesado; norte conserva su generación DR9 documentada. Orden ascendente del SHA-256 UTF-8 de `OC3-v1|brick|<region>|<brickname>`; empate por brickname ASCII. Tomar el primero, sin inspeccionar calidad ni intensidad y sin sustituirlo si faltan auxiliares. Si el subconjunto sur/cobertura/allowlist no puede resolverse, registrar imposibilidad y cerrar con C (§10); no buscar otro régimen, release o tercer brick.

**UNRESOLVED:** Los nombres, coordenadas, URLs definitivas, HDUs, tamaños y hashes de estos dos bricks no se han resuelto en esta tarea. La regla está fijada, no sus resultados. El manifiesto concreto se sellará en la futura fase de planificación; no inventar coordenadas para simular que existe.

### 4.2 Seis slots fijos

**PROPOSED:** Seleccionar primero desde geometría y mapas auxiliares nativos; el selector carece de acceso al producto image. Esto requiere una futura lectura de NEXP/MASKBITS/PSFSIZE: cuenta como adquisición de datos del piloto y NO se realiza ahora. El propio algoritmo de selección se congela aquí; no se adapta a los arrays que encuentre.

**PROPOSED:** Candidatos = retícula técnica fija 0-based: x en {0,64,128,…} menores que NAXIS1 más NAXIS1−1, y análogamente para y; deduplicar extremos. No se exploran todos los centros ni se refina alrededor de resultados. WCS transforma cada centro a RA/Dec, sin recentrado. Ventana `[x-64,x+65) × [y-64,y+65)`. Para estadísticas auxiliares se usa únicamente la intersección real con el array; su fracción se registra. Orden fijo S1,S2,S3,N1,N2,N3; prohibir centro ya elegido. Desempate mediante SHA-256 de `OC3-v1|slot|region|brickname|x|y`, con enteros decimales sin padding y desempate final `(y,x)` ascendente.

| Slot | Región | Predicado / regla técnica congelada |
|---|---|---|
| S1 | sur | Interior: ventana completa y todos sus centros a ≥64 píxeles del límite geométrico de región única BRICK_PRIMARY. Elegir mínimo hash; no condicionar por flags o brillo. |
| S2 | sur | Frontera: minimizar distancia del centro al límite geométrico BRICK_PRIMARY; desempate hash. La ventana debe intersectar ambos lados de ese límite dentro del mismo brick. Si no hay candidato, slot ausente. |
| S3 | sur | Mask: ventana completa con algún bit óptico 1–7,10–13 no nulo; elegir mínimo hash, sin maximizar número de flags. No seleccionar por bit NPRIMARY ni bits WISE. |
| N1 | norte | Mismo predicado de interior que S1, hash propio. |
| N2 | norte | Soporte: prioridad 1, ventana que intersecta tanto NEXP=0 como NEXP>0 en alguna banda; prioridad 2 si no existe ninguna de prioridad 1, ventana con NEXP=1 en alguna banda. Elegir mínimo hash dentro de la primera clase disponible. Sin ninguna clase: slot ausente. |
| N3 | norte | Ventana completa; PSFSIZE positivo/finito en todos los píxeles de las tres bandas. Maximizar V definido abajo, luego hash. No usar image ni ivar para optimizar el estrato. |

**PROPOSED:** En N3, `V = max(max_b[(max(P_b)-min(P_b))/median(P_b)], max_b median(P_b)/min_b median(P_b)-1)` usando PSFSIZE de la ventana. Esto selecciona contraste relativo de un metadato instrumental, no morfología. Se llama estrato de variación fuerte solo si V≥0.10; si su máximo es menor, guardar el candidato y la anotación `STRATUM_NOT_EXERCISED`, sin alterar el umbral ni buscar otro brick.

**PROPOSED:** Distancias de límites geométricos se evalúan en el plano de píxeles nativo usando WCS y límites publicados, incluyendo wrap RA. NPRIMARY sirve de contraste, no de reemplazo de geometría. S2 cruza región única, no necesariamente borde del array: se reportan ambos por separado. Para borde físico se evaluará además una ventana de soporte virtual a partir de la misma ubicación, solo aritmética de índices; no es una séptima adquisición ni prueba de píxeles inexistentes.

**PROPOSED:** Seis slots, sin reposición. Un slot ausente reduce la evidencia, nunca se rellena por apariencia o un séptimo lugar. Si las seis ubicaciones no son distintas o un estrato no se ejercita, A queda vedado; B solo bajo la subfamilia predeclarada en §10. Todas las fallas se conservan en el flujo de selección. Las ubicaciones y ventanas se sellan antes de adquirir/abrir image o PSF; no se recalculan tras métricas de imagen.

## 5. Bundle, extracción y procedencia

**PROPOSED:** Por brick, g/r/z: image, invvar, nexp, psfsize (12 recursos); maskbits óptico (1 recurso compartido por bandas). Máximo 26 recursos nativos. Añadir hasta dos tablas CCD de procedencia, sin columnas de catálogo de fuentes. La familia documental está bajo `https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/<region>/coadd/<AAA>/<brick>/`; sufijos/HDU efectivos deben confirmarse y sellarse, no adivinarse a partir de nombre. No adquirir model, blobmodel, chi2, depth, JPEG, exposiciones ni catálogos Tractor como sustitutos.

**PROPOSED:** Por ubicación, obtener PSF en tres puntos enteros: centro, offset (-32,-32), offset (+32,+32), por cada banda disponible. Hasta 54 combinaciones posición/banda, deduplicadas por identidad de respuesta. Si un punto está fuera de soporte, conservar NOT_AVAILABLE sin moverlo. El servicio candidato `viewer/coadd-psf/` con capa DR9 solo se usará si el preflight determina parámetros y vínculo independiente al mismo brick/región/generación/banda. No invocarlo aquí. Un nombre ls-dr9 por sí solo no acredita ese vínculo. No sustituir por PSF exposición, Gaussian inventada ni mapa FWHM. No evaluar código remoto.

**PROPOSED:** Registrar URL solicitada/final, UTC, estado HTTP, bytes, ETag/Last-Modified, checksum proveedor cuando exista y SHA-256 local; release semántica DR9, RELEASE técnico, región/cámara, brick/banda/producto, versiones de proceso observables y fuente que las vincula. RELEASE puede venir de metadatos oficiales externos al header: no inventar una keyword obligatoria ni inferir versión del título del servidor. Falta de linaje es C; contradicción de identidad o hash en entrada sellada es D.

**PROPOSED:** Conservar FITS originales/fragmentos, headers completos, HDU, BITPIX, dimensiones, BSCALE/BZERO, BLANK, endian, compresión/cuantización y versión del decoder. Leer HDUs reales (no confundir HDU físico comprimido con imagen lógica). MASKBITS óptico se identifica documentalmente y por header; no mezclar planos WISE. Las unidades quedan ligadas a cada producto. ETag no es checksum y hash de fragmento no acredita archivo completo.

**PROPOSED:** Crop = slice exacto de valores decodificados; dtype original, sin conversión float32 añadida. Para window parcial, guardar solo la intersección y su offset más un descriptor de dominio solicitado/obtenido; no padding con ceros ni NaN. WCS de crop conserva la proyección y cambia CRPIX por offset entero; distorsiones/tablas anexas se preservan o se rechaza layout no soportado. Comparar cada valor/bit con el slice independiente del mismo input; conservar payload NaN si el decoder lo permite y registrar lo contrario, sin atribuir igualdad binaria al contenedor.

**PROPOSED:** Lectura completa de solo esos dos bricks es fallback permitido únicamente si el inventario demuestra presupuesto; Range es opcional, nunca supuesto equivalente por C0. Range exige 206/Content-Range, identidad constante, layout soportado y todos los bytes necesarios. Si el servidor ignora Range, no aceptar un cuerpo completo no presupuestado. Cualquier ruta de decodificación parcial debe validar la extracción contra lectura independiente del input fijado o quedar sin prueba; no descargar un archivo adicional grande solo para probar ahorro. La extracción local exacta no demuestra exactitud respecto de exposiciones originales.

## 6. Estados separados y no-fuga

**PROPOSED:** Por píxel conservar ejes independientes: `array_present`, `finite_image`, `image_zero`, `weight_finite`, `weight_sign` (negativo/cero/positivo), `nexp_value`, `raw_optical_maskbits`, `known_flags`, `unknown_bits`, `geometric_primary`, `support_evidence`, `quality_evidence`, `validity_state`. UNKNOWN no se codifica como false. No sustituir ausencia, saturación, invalidación y cero válido por un único valor de máscara.

**PROPOSED:** Una combinación finita+ivar positiva+nexp positivo+bits cero se llamará `supported_unflagged_candidate`, no científicamente limpia. `valid_zero` exige evidencia de validez independiente aplicable, además de valor cero; si no existe, mantener `zero_with_unresolved_validity`. Saturación de alguna exposición no implica automáticamente inutilidad del coadd; GALAXY tampoco es clase ni flag fatal. Diccionario de bits exacto DR9, sin incorporar semántica DR10+ que aparezca en menús modernos.

**PROPOSED:** Aislar RAW_IMMUTABLE, TECHNICAL_INDEX y CONFOUND_AUDIT. No abrir ni copiar INTERPRETATION_LOCKBOX o HOLDOUT_LOCKBOX; el nuevo manifiesto no tendrá filas de sujetos Galaxy Zoo. Allowlist de columnas y rutas con rechazo de todo campo extra; no imprimir nombres/valores bloqueados. Hashes y procedencia técnica pueden salir a logs. Se conservan todas las ubicaciones fallidas, no solo las utilizables.

## 7. Pruebas y criterios antes de resultados

**PROPOSED:** Cada prueba produce evidencia por ubicación/banda/producto, estado `VERIFIED`, `CONTRADICTED`, `NOT_AUDITABLE` o `NOT_EXERCISED`, causa y referencias a hashes. Estos estados de prueba no son desenlaces terminales alternativos. Valores numéricos se reportan completos; no ajustar umbrales, ganancias, offsets, centros, kernels, selección o ruido tras inspección.

| Test | Método / observación falsadora | Propiedad |
|---|---|---|
| T01 — identidad | Verificar release, región, generación, diccionario y linaje de todos los recursos. URL sin vínculo independiente no basta. Conflicto en input sellado → D; metadata insuficiente → C. | A1/O1 |
| T02 — grid | Comparar shape y transformaciones WCS de todos los productos/bandas en todos los centros de la región y esquinas. Error máximo de composición ≤1e-6 píxel; rechazar WCS no invertible o relación desconocida. Esta tolerancia es de bookkeeping numérico, no precisión astrométrica celeste. | A2–A4 |
| T03 — crop | Dos rutas locales independientes: slice de array decodificado y lectura de ventana. Igualdad exacta de valores/flags/dtype y posiciones; hash canónico repetible, NaN documentado. Prohibido realinear para pasar. | A5–A9 |
| T04 — fronteras | Separar límite de array, región única, NPRIMARY y soporte real por banda. Contabilizar intersección y faltantes. Ningún pixel sintetizado. Ventana virtual fuera del array comprueba solo regla de índices. | A7/A8 |
| T05 — relación de mapas | Tabla conjunta exhaustiva NEXP, signo/finitud IVAR, cero/finitud image y cada bit; mapas de discrepancias por coordenada. NEXP no se fuerza a NOBS. Todo conflicto se explica por fuente o queda NOT_AUDITABLE. | A10/B2 |
| T06 — estados | Verificar que original y derivado preservan cada eje de §6; cero no equivale a missing. Estado válido no demostrado queda UNKNOWN. Ausencia de ceros verdaderamente válidos es NOT_EXERCISED, no prueba positiva. | A10/B7 |
| T07 — resolución | Min/max/mediana y cuantiles 0.05/0.95 PSFSIZE; variación por banda y espacial; perfiles por x/y y fracciones sin descriptor. No suavizar mapa. | A11/B4 |
| T08 — mapa frente a PSF | Descriptores del modelo en los tres puntos de §5 y comparación definida en §8. Diferencia no implica fallo por sí misma: primero comprobar misma definición. Sin relación defendible → NOT_AUDITABLE. | A11/B4 |
| T09 — linaje PSF | Posición, banda, grid, escala, región, generación, método de combinación y dominio deben ser enlazables al coadd concreto. Repetibilidad de bytes cacheados no demuestra correspondencia. No exigir commit forense si propiedades relevantes quedan verificadas independientemente. | A11/B4/C1 |
| T10 — correlación | Estadísticos de §9 sobre todos los slots, sin seleccionar cielo por apariencia; detectar dependencia vecina, separar intensidad/cielo/ruido como identificabilidad. | B2/B3 |
| T11 — issues | Manifestar pertenencia a reprocessing y aplicabilidad norte/Mosaic, máscara incompleta y bleed; no descargar objetos del SGA para seleccionar casos. No considerar no-detección como descarte de issue. | A10/B3 |
| T12 — reproducción | Segunda ejecución offline desde cache, mismos inputs/offsets/código/entorno: hashes canónicos y decisiones iguales; comparar métricas serializadas float64 a 17 dígitos bajo entorno fijado. Cero nueva red. | C1/C2 |

**PROPOSED:** T02 prueba coherencia de grids, no registro astrométrico real entre bandas. No detectar fuentes ni hacer cross-correlation de galaxias para ajustar desplazamientos; esa limitación debe figurar en cualquier borrador. T03 no evalúa conservación de flujo del coadd upstream: solo prueba no introducir cambios propios.

**PROPOSED:** Integridad, límites y no-fuga preceden toda adquisición. Los futuros tests de software serán sintéticos mínimos, sin inventar resultados de survey: bytes alterados, mezcla de releases, replay sin red, presupuesto agotado, coordenada fuera de array, ceros versus missing, y campo/ruta prohibidos. Se diseñan aquí; no se implementan ni ejecutan.

## 8. PSF: compatibilidad de definiciones y dominio

**PROPOSED:** Conservar modelo PSF sin renormalizar sus píxeles. Calcular suma S, fracción de masa absoluta en borde externo de dos píxeles, mínimo/máximo, peso negativo, centroide de momentos y matriz de segundos momentos con sumas float64. Si S≤0, no finitud, matriz no positiva o falta escala/centro documental: declarar descriptor no interpretable; no recortar valores negativos ni ajustar modelo Gaussian para ocultarlo.

**PROPOSED:** Medir anchuras sobre los cortes x/y por el centro de modelo declarado: primer cruce de media altura a ambos lados, con interpolación lineal solo del escalar cruce, no de imagen científica. Si máximo no central, múltiples cruces o media altura no alcanzada, registrar ambigüedad, no elegir el cruce más favorable. Reportar además `F_mom=2*sqrt(2*ln(2))*sqrt(trace(M)/2)*pixel_scale` como anchura Gaussian equivalente de momentos, no FWHM física universal. Es un descriptor, no ajuste ni sustitución de PSF.

**PROPOSED:** Comparar PSFSIZE en el píxel nativo exacto con esas anchuras, dando diferencias absolutas/relativas, bandas, posición y definiciones. Un promedio de FWHMs y la FWHM de una mezcla no tienen que coincidir. Solo rotular «acuerdo» si una definición común y una cota de error independiente, selladas antes de abrir las respuestas PSF, hacen evaluable la igualdad; si no existe esa cota, informar diferencia sin inventar tolerancia retrospectiva. La existencia de un kernel enlazado y con dominio caracterizado puede sostener B4 aunque PSFSIZE sea solo proxy.

**PROPOSED:** Guardas técnicas prospectivas para la subfamilia restringida: variación de PSFSIZE por banda en la ventana ≤10%; FWHM mínima ≥2 píxeles en las tres bandas; masa absoluta del borde de cada stamp PSF ≤1% de la masa absoluta total. Son filtros conservadores del piloto para evitar extrapolación submuestreada/truncada, no garantías de recuperación de rasgos. No son tolerancias para forzar acuerdo PSFSIZE–PSF. Si una definición queda sin justificar, la guarda no salva el test.

**UNRESOLVED:** No hay medición de estrellas ni comparación con exposición en este piloto; un modelo coherente no queda empíricamente validado frente al cielo. El borrador eventual deberá mantener esa limitación, sin prometer PSF exacta ni reconstrucción de morfología bajo el seeing.

## 9. Ruido, fondo y autocorrelación sin preprocessing

**PROPOSED:** Sobre cada crop completo dividir el bloque 128×128 con esquina inferior de índices (0,0) en 16 cuadrados fijos de 32×32; última fila/columna de la ventana 129 se conserva pero no entra al estimador. En ventana parcial, bloques incompletos se marcan no disponibles, no se rellenan. Reportar conteos para todos los píxeles finitos y para pares con NEXP>0 e IVAR>0, estratificados por flags ópticos relevantes; ese subconjunto no se llama cielo limpio.

**PROPOSED:** Para desplazamientos `(1,0),(0,1),(1,1),(1,-1),(2,0),(0,2),(4,0),(0,4),(8,0),(0,8)`, calcular covarianza empírica de pares usando sus medias muestrales, varianzas y correlación de Pearson. Esta resta algebraica en un estadístico NO produce ni guarda una imagen con nuevo fondo sustraído. No clipping, source masking, selección por amplitud ni normalización de las intensidades originales. Guardar medias/varianzas, número de pares y estados indeterminados. Menos de 128 pares o varianza nula ⇒ no estimable.

**PROPOSED:** Control limitado: 199 permutaciones de coordenadas de valores finitos dentro de cada bloque y clase de estado, PCG64 seed 301; conservar soporte y marginales. Comparar |correlación| observada con control de independencia a lags definidos, p=(1+#permutaciones ≥ observado)/200; Holm a α=0.05 sobre todas las pruebas estimables del piloto (familia única, sin seleccionar bandas). Reportar también tamaños de efecto y heterogeneidad por bloque. Son estadísticas instrumentales, no perturbaciones de entrada a un encoder ni bootstrap de galaxias.

**INFERRED:** Este control detecta estructura incompatible con la independencia bajo su hipótesis de intercambiabilidad; variación de pesos, fuentes reales o gradientes pueden romperla. No atribuir automáticamente significancia a ruido de Lanczos. Ausencia de significancia no demuestra independencia. No usar `1/sqrt(ivar)` para normalizar arrays ni para afirmar ruido blanco.

**PROPOSED:** La salida distingue «dependencia espacial empírica detectada», «no detectada a esta sensibilidad» y «no identificable». Comparar varianza empírica con valores de inverse variance solo descriptivamente, por unidades y estados, sin imponer igualdad. No se recupera covarianza completa ni SNR de galaxia. Si el contrato necesita separar ruido/cielo/fuentes a una precisión que estos datos no permiten, T10 queda NOT_AUDITABLE y se aplica C, no una sustracción adicional o nuevas exposiciones. El dominio restringido excluye claims de ruido independiente y detección de estructuras LSB a significancia calibrada.

## 10. Desenlaces terminales y regla no retrospectiva

**PROPOSED:** Se emite exactamente uno, con prioridad D, luego C si hay bloqueo universal, luego A o B según dominios. No PENDING. Un cierre por evidencia insuficiente es un resultado completo.

| Código terminal | Condición congelada y alcance |
|---|---|
| D — `PILOT_INTEGRITY_FAILURE_STOP` | Hash/autoridad/input sellado inconsistente, fuga, modificación no autorizada de selección/protocolo, mezcla oculta de release, límite duro vulnerado o ledger no fiable. Parada inmediata sin interpretación científica dependiente. |
| A — `DR9_COADD_SUPPORTS_OBSERVATIONAL_CONTRACT_DRAFT` | Seis slots/estratos ejercitados, bundle íntegro en grz, T01–T12 auditables en su dominio aplicable, ninguna discrepancia material sin explicación/cota previa, linaje PSF suficiente, estados/missingness conservados y derechos de uso necesarios documentados. Se permite únicamente redactar un contrato limitado a lo medido, no adoptar DR9. |
| B — `DR9_COADD_REQUIRES_NARROWER_SCIENTIFIC_DOMAIN` | El dominio completo no satisface A, pero al menos S1 y N1, las tres bandas y PSFs, satisfacen todos los requisitos relevantes dentro de D_restricted definido abajo. Las fallas externas quedan localizadas por reglas previas, nunca ocultas. Permite proponer ese dominio menor para revisión, no cambiar umbrales por morfología. |
| C — `DR9_COADD_NOT_CURRENTLY_ADMISSIBLE` | Falta linaje/semántica/derecho necesario, incompatibilidad no acotable, evidencia insuficiente incluso para D_restricted, estratos básicos ausentes, o imposibilidad de completar dentro del presupuesto sin violarlo. No más búsquedas, datos o fallback automático. |

**PROPOSED — D_restricted previo:** solo ventanas completas interiores a región única, grz presente, NEXP≥2 e IVAR finita positiva en todo el crop, sin bits 1–7,10–13 ni bits desconocidos, PSF enlazada en los tres puntos y guardas de §8 satisfechas. Se conserva el estado `supported_unflagged_candidate`; las guardas no prueban limpieza. Se requiere además que T05/T06 permitan declarar las limitaciones de calidad sin una incertidumbre espacial material no acotada para el claim restringido. Si no, C. No excluir silenciosamente GALAXY del estudio futuro: el sesgo de esta restricción debe quedar explícito y no define una cohorte científica.

**PROPOSED:** D_restricted no admite fotometría de halos, colas tenues, ruido diagonal exacto, máscaras exhaustivas ni recuperación de rasgos de tamaño ≤PSF. El piloto no autoriza fijar un corte de SNR de galaxia: no lo mide. Si solo un corte SNR desconocido pudiera salvar la ruta, corresponde C; no buscar el umbral después. Las guardas instrumentales son condiciones previas para formular un dominio posible, no umbrales de aceptación morfológica.

**PROPOSED:** A/B requieren una tabla de claims explícitamente permitidos/excluidos y evidencia por test. NOT_AUDITABLE material en A10/A11 bloquea ambos. NOT_EXERCISED de un estado raro, como cero válido, impide declararlo verificado; solo puede quedar fuera de un dominio prospectivo aplicable sin fingir que no existe. Si excluirlo requiere una regla que no puede implementarse con semántica independiente, C. Derechos de redistribución pueden quedar fuera del borrador al deshabilitarla; análisis/archivo necesarios no pueden quedar indeterminados.

**DOCUMENTED:** Éxito nunca significa imágenes atractivas, acuerdo con Galaxy Zoo, galaxias visualmente limpias, clusters o precisión de modelos. Un sentinel técnico no es A/B ni PASS MIP.

## 11. Presupuesto independiente y adquisición futura escalonada

**PROPOSED — límites acumulados OC-3, no autorizados aún:**

| Recurso | Límite duro |
|---|---:|
| Ubicaciones / bricks | 6 / 2, sin reposición |
| Bytes de cuerpos descargados, incluyendo metadatos, PSFs, errores y reintentos | 1610612736 (1.5 GiB) |
| Solicitudes HTTP totales, incluyendo HEAD, redirects y reintentos | 200 |
| Reintentos por recurso | 2 adicionales, nunca ilimitados |
| Concurrencia por servicio / global | 1 / 1 |
| Metadatos/documentos incluidos en total | 64 MiB |
| Respuestas PSF incluidas en total | 54 MiB; máximo 1 MiB por posición/banda lógica |
| RAM / threads / GPU | 2 GiB / 1 / ninguna |
| Disco incremental, incluidos cache, parciales y outputs | 4 GiB |
| IO local acumulado | 8 GiB |
| Cómputo activo total / wall-clock por invocación | 30 min / 60 min |

**INFERRED — estimación, no medida:** hasta 26 mapas de 3600² a 4 bytes son ~1.26 GiB sin compresión, antes de otros HDUs, headers y PSF. Compresión/dtypes pueden variar; no se asume que quepa. Reservar 2–4 GiB de disco y aproximadamente 10–60 minutos según transporte. Todo proceso real será CLI humano según AGENTS, incluso una lectura de mapas para elegir posiciones. Si tamaño/layout no permite una cota segura dentro del máximo, C sin transferir. No ampliar presupuesto ni usar saldo C0.

**PROPOSED — orden:**

1. Preflight local sin datos: verificar autoridades, código futuro revisado, aislamiento, derechos, allowlist, entorno y presupuesto. Sellar documentos de semántica/issue y reglas necesarias; sin evidencia suficiente cerrar C.
2. Planificación metadata: recuperar únicamente resúmenes técnicos y listar los dos bricks; resolver tamaños/procedencia de recursos exactos, sin recorrer colecciones. Emitir plan de bytes/peticiones y ledger. Toda fuente extra debe estar en input manifest; nada de búsqueda abierta automatizada.
3. Adquisición auxiliar de esos bricks: NEXP/MASKBITS/PSFSIZE y headers, dentro de presupuesto; seleccionar y sellar seis slots por §4. Esta fase nunca abre image. No elegir otro brick si faltan estratos.
4. Adquirir image/invvar y PSF para la lista fija; contrastar linaje antes de métricas. No cambiar selección. Fallos se conservan y reducen alcance según §10.
5. Análisis/reproducción offline; informe con exactamente un desenlace. Sin nueva red para resolver incertidumbres descubiertas.

**PROPOSED:** Reservar bytes máximos por recurso/solicitud antes de enviar y contabilizar lo realmente leído incluidos cuerpos parciales. Tamaño desconocido exige cota conservadora verificable y streaming limitado; no leer ilimitadamente hasta Content-Length. Abort before-next-request cuando la reserva exceda presupuesto. Si hay limitación de plan sin superar tope, C; si se vulnera tope por bug/incidente, D. Retry-After mayor que 60 s termina la invocación, sin polling; timeout por solicitud 30 s, backoff 2 y 5 s. El ledger persiste y no se reinicia.

**PROPOSED:** Cache por recurso/generación/hash; archivos completos verificados se reutilizan sin HEAD/GET de recreación. Parciales inmutables con bitmap de fragmentos, hashes y cota pendiente; reanudar solo bytes faltantes si identidad sigue verificable. No mezclar generaciones ni sobrescribir evidencia discrepante. Si el servidor cambió, conservar ambos registros y D para corrida sellada. No `nohup`, background ni descarga masiva de colecciones.

## 12. Inventario local exacto para la futura implementación

**PROPOSED:** Todo bajo `oc3/`, creado solo tras autorización futura. En esta entrega no se crea ese directorio. La cardinalidad variable permitida se define por claves del manifiesto, no por descubrimiento libre:

```text
oc3/
  INPUTS/OC3_INPUT_MANIFEST.json
  INPUTS/OC3_DEVELOPMENT_BRICKS.csv
  provenance/OC3_AUTHORITIES.json
  provenance/OC3_ENVIRONMENT.json
  provenance/OC3_RIGHTS_AND_SEMANTICS.json
  provenance/OC3_RESOURCE_PLAN.json
  provenance/OC3_RESOURCE_LEDGER.sqlite
  provenance/OC3_HTTP_EVENTS.jsonl
  provenance/OC3_RELEASE_ISSUES.json
  provenance/OC3_HEADERS.jsonl
  RAW_IMMUTABLE/metadata/<sha256>.body
  RAW_IMMUTABLE/products/<resource_id>/<sha256>.body
  RAW_IMMUTABLE/psf/<response_id>/<sha256>.body
  RAW_IMMUTABLE/partials/<resource_id>/<start>-<end>.<sha256>.part
  TECHNICAL_INDEX/OC3_BRICKS.csv
  TECHNICAL_INDEX/OC3_LOCATIONS.json
  TECHNICAL_INDEX/OC3_SELECTION_FLOW.csv
  TECHNICAL_INDEX/OC3_PRODUCT_LINKS.json
  TECHNICAL_INDEX/OC3_PSF_LINKS.json
  crops/<slot>/<band>/<product>.fits
  crops/<slot>/optical_maskbits.fits
  crops/<slot>/OC3_WINDOW.json
  CONFOUND_AUDIT/OC3_PIXEL_STATES.parquet
  CONFOUND_AUDIT/OC3_MAP_RELATIONSHIPS.csv
  CONFOUND_AUDIT/OC3_PSF_DIAGNOSTICS.csv
  CONFOUND_AUDIT/OC3_CORRELATION.csv
  reports/OC3_TEST_LEDGER.json
  reports/OC3_REPRODUCIBILITY.json
  reports/OC3_RESOURCE_SUMMARY.json
  reports/OC3_FINAL_REPORT.md
  reports/OC3_TERMINAL.json
  logs/OC3_RUN.log
```

**PROPOSED:** `<product>` solo image/invvar/nexp/psfsize; maskbits se deduplica por slot. IDs de recursos derivan de URL canónica+generación+tipo; response_id de parámetros PSF sellados. Ningún archivo representa producto ausente: manifests registran NOT_AVAILABLE/UNKNOWN. Crops son observaciones sin preprocessing. El informe no contiene galerías; tablas/perfiles técnicos bastan. Logs extensos al archivo, terminal solo etapa/coste/sentinel/código. Fuentes, headers y offsets permiten reconstrucción sin servicio vivo.

## 13. Contrato CLI futuro — no implementado, no ejecutar

**PROPOSED:** La futura interfaz será `oc3/oc3_pilot.py`, Python 3 con dependencias/decoder fijados y ambiente independiente de C0. Ese archivo NO existe por este diseño y no se afirma haber probado estos comandos. Son la especificación exacta que deberá satisfacer una implementación autorizada posteriormente. No son un handoff de ejecución vigente.

**PROPOSED:** Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`, secuencia humana futura:

```bash
python3 oc3/oc3_pilot.py --help
python3 oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --dry-run --offline
python3 oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --resolve-metadata --max-bytes 1610612736 --max-requests 200 --max-bricks 2 --max-locations 6 --resume
python3 oc3/oc3_pilot.py acquire-aux --plan oc3/provenance/OC3_RESOURCE_PLAN.json --max-bytes 1610612736 --max-requests 200 --resume
python3 oc3/oc3_pilot.py select --plan oc3/provenance/OC3_RESOURCE_PLAN.json --offline --seal --resume
python3 oc3/oc3_pilot.py acquire-fixed --plan oc3/provenance/OC3_RESOURCE_PLAN.json --locations oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json --max-bytes 1610612736 --max-requests 200 --resume
python3 oc3/oc3_pilot.py analyze --locations oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json --offline --resume
python3 oc3/oc3_pilot.py verify --offline
python3 oc3/oc3_pilot.py finalize --offline
```

**PROPOSED:** `--help` no red/escritura. Todo subcomando admite `--dry-run`: no red ni mutación ni decodificación de imágenes; informa dependencias faltantes, cotas y acciones previstas. `--offline` debe bloquear físicamente cliente de red. Parámetros CLI nunca pueden ampliar topes de la spec; las tres órdenes con acceso de red (planificación, auxiliares y bundle fijo) comparten el mismo ledger, no tres presupuestos. Plan exige hashes de spec/autoridades/allowlist y bindings de fuentes; no genera URLs científicas a partir de intuición. `select --seal` fija coordenadas y offsets antes de image/PSF; reanudar selección solo reproduce el mismo hash.

**PROPOSED:** Sentinel por etapa `OC3_<STAGE>_OK` solo certifica terminación técnica. Final `OC3_TECHNICAL_RUN_COMPLETE; outcome=<uno de §10>`, exit 0 para A/B/C completos con evidencia; D imprime `OC3_INTEGRITY_FAILURE_STOP`, exit 20. Interrupción de transporte preserva checkpoint y sale 75 sin éxito; permite al humano repetir el mismo comando `--resume` dentro de reintentos/topes. Si decide cerrar sin completar, `finalize --offline` produce C por evidencia insuficiente. Ningún informe final puede quedar PENDING; no cerrar ni interpretar D como fallo científico del survey.

**PROPOSED:** La implementación futura deberá demostrar con smoke tests sintéticos no-fuga, límites y reanudación, documentar tamaños de inputs reales, entorno, cotas de tiempo/espacio, outputs y log antes de entregar esta secuencia como ejecutable. Se detendrá tras el handoff y esperará confirmación humana, conforme AGENTS. En la presente tarea no se crea código, entorno, manifiesto de ejecución ni script de adquisición.

## 14. Control de cambios y cierre de diseño

**PROPOSED:** Tras sellar manifiesto, cambiar strata, tamaños, definición de métricas o guardas requiere nueva versión prospectiva y autorización, nunca rescatar una corrida mirando morphology/residuales. Los resultados de este piloto no serán holdout confirmatorio. No se abre R2/HSC si R1 falla y no se redacta automáticamente un contrato final.

**OBSERVED — entrega de diseño:** únicamente dos Markdown nuevos, este y OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md. Cero adquisición de datos astronómicos, cero pruebas de píxeles, cero implementación. Las consultas externas fueron documentales. Autoridades y archivos previos se conservan; no se inicializa ni repara Git. La verificación de preservación es documental y de inventario, no un rerun C0/E-OC1.
