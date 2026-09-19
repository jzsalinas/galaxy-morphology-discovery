---
title: "Galaxy Morphology Discovery — Research Seed"
version: "0.1"
date: "2026-09-16"
status: "Diseño científico previo a implementación"
language: "es"
methodological_framework: "Análisis de Arquitectura de Continuidad (AAC)"
---

# GALAXY_RESEARCH_SEED.md v0.1

## 0. Estatus, alcance y regla de lectura

Este documento congela la primera especificación científica del proyecto **Galaxy Morphology Discovery**. No contiene resultados experimentales y no autoriza todavía una implementación grande. Su función es convertir la pregunta general en decisiones contrastables, separar descubrimiento de interpretación y definir qué tendría que ocurrir para aceptar, revisar o abandonar cada afirmación.

La pregunta rectora es:

> **¿Podemos descubrir estructura morfológica de galaxias sin etiquetas y justificar operacionalmente por qué determinadas galaxias pueden tratarse como pertenecientes a una misma clase, secuencia o estructura latente?**

AAC se utiliza como disciplina metodológica, no como teoría a confirmar. No se propone de entrada un algoritmo nuevo. La hipótesis de trabajo es que una combinación rigurosa de formalismos existentes —representación auto-supervisada, clustering, análisis de manifolds, estabilidad, pruebas de perturbación, adaptación de dominio y detección de anomalías— puede ser suficiente. Si lo es, se utilizará esa combinación y no se reclamará novedad algorítmica.

Este documento distingue siempre:

- **observación:** píxeles, metadatos y catálogos efectivamente disponibles;
- **preprocesamiento:** transformaciones aplicadas por el pipeline;
- **supuesto astronómico:** decisión sobre qué se considera morfología;
- **invariancia impuesta:** información que el entrenamiento es incentivado a ignorar;
- **representación aprendida:** geometría producida por un encoder;
- **estructura candidata:** clusters, coordenadas, jerarquías, densidades o anomalías;
- **interpretación posterior:** relación con etiquetas humanas o variables físicas;
- **evidencia:** resultado de una prueba preespecificada;
- **inferencia:** explicación compatible, pero no directamente observada.

Un embedding visualmente atractivo no constituye evidencia de estructura astronómica.

---

## 1. Decisiones ejecutivas de v0.1

1. **Unidad estadística:** una galaxia astrofísica, representada por un *bundle observacional* multibanda. Las distintas vistas, augmentations u observaciones de la misma galaxia nunca cuentan como objetos estadísticos independientes y permanecen en el mismo split.
2. **Pregunta primaria:** descubrir estructura de la **distribución bidimensional resuelta de luz en el óptico**, con énfasis en rasgos estructurales (disco, bulbo, barra, brazos, asimetría, perturbaciones y rasgos de marea), no en luminosidad total, posición en el cielo ni orientación en el detector.
3. **No se presupone discreción:** clases, continuo, manifold, jerarquía, mezcla, regiones ambiguas y ausencia de estructura son resultados admisibles.
4. **Dataset inicial:** cohorte GZD-5 de Galaxy Zoo DECaLS, seleccionada en la intersección DECaLS–SDSS y observada en DECaLS DR5. Se usarán datos FITS DR5 y una réplica de la vista mostrada a voluntarios. Las etiquetas Galaxy Zoo quedan en cuarentena hasta la validación post hoc.
5. **Prueba instrumental fuerte:** pares de imágenes DECaLS–SDSS de la misma galaxia. Esto prueba robustez del observador sin confundir cambio de instrumento con cambio de objeto.
6. **Representación primaria:** imagen estructural monocromática en banda `r`; la rama `g,r,z` será una ablación para medir cuánto de la estructura proviene de color o de morfología cromática.
7. **Escala no será una invariancia automática:** se compararán un marco angular fijo y un marco normalizado por tamaño. Si sus conclusiones no coinciden, la clasificación no podrá llamarse independiente de escala.
8. **PSF, ruido y profundidad:** se tratan primero como perturbaciones observacionales controladas, no como augmentations agresivas. La pérdida de información por seeing no se puede “desaprender” legítimamente.
9. **Galaxy Zoo:** votos humanos continuos y su incertidumbre se utilizarán después del aprendizaje. Las predicciones de Zoobot son un comparador supervisado, nunca evidencia independiente ni baseline no supervisado.
10. **Anomalía:** será un perfil multiaxial, no una sola distancia al centro de un cluster.
11. **UMAP/t-SNE:** solo visualización exploratoria. No se aceptarán islas bidimensionales como prueba de clases.
12. **Resultado negativo permitido:** si solo sobrevive estructura del proceso de observación, se registrará como resultado principal.

---

## 2. Traducción de AAC al problema

La especificación AAC mínima queda fijada como:

\[
\Gamma=(S,E,B,\tau,\mathcal Q,O,g,\sim_M).
\]

| Elemento | Definición en este proyecto |
|---|---|
| \(S\) | Una galaxia astrofísica candidata. |
| \(E\) | Campo circundante, fuentes vecinas, foreground, background, atmósfera, detector, survey y pipeline. |
| \(B\) | Segmentación/cutout y regla para decidir qué emisión pertenece al objeto. Es operacional y falible. |
| \(\tau\) | Una época observacional; no se estudia evolución temporal de una galaxia individual en v0.1. |
| \(\mathcal Q\) | Equivalencia de morfología óptica resuelta bajo las exclusiones declaradas. |
| \(O\) | Survey, bandas, PSF, ruido, profundidad, pixelización y preprocessing. |
| \(g\) | Representación clásica o aprendida. |
| \(\sim_M\) | Relación candidata de equivalencia morfológica, definida por estabilidad de geometría local y no por una etiqueta previa. |

### 2.1 Definición operacional provisional de equivalencia

Dos observaciones \(x_i\) y \(x_j\) son **candidatas a equivalencia morfológica para \(\mathcal Q\)** cuando:

1. su relación de vecindad o pertenencia permanece consistente a través de una familia predeclarada de representaciones y preprocesamientos admisibles;
2. esa relación sobrevive a transformaciones que deberían preservar \(\mathcal Q\);
3. la representación reacciona a controles que destruyen rasgos estructurales relevantes;
4. la relación no se explica suficientemente por PSF, ruido, redshift, tamaño aparente, brillo, background, survey o artefactos;
5. generaliza a objetos y campos no usados para elegir criterios.

Formalmente, para una familia de observadores \(\mathcal A_Q\), se construirá una frecuencia de co-vecindad:

\[
C_{ij}=\frac{1}{|\mathcal A_Q|}\sum_{a\in\mathcal A_Q}
\mathbf 1\{j\in N_k^{(a)}(i)\ \lor\ i\in N_k^{(a)}(j)\}.
\]

`C_ij` no es todavía una clase ni una verdad física. Es una medida de consenso entre observadores. Los valores de \(k\) se explorarán en `{15, 30, 50, 100}`; ninguna conclusión podrá depender exclusivamente de uno de ellos.

Si aparece una partición, la equivalencia discreta requerirá además co-asignación estable. Si solo aparece geometría local estable sin valles de densidad reproducibles, la salida será continua. Si ninguna geometría sobrevive, la salida será “sin estructura robusta identificable bajo este protocolo”.

### 2.2 Qué significa “morfología” en v0.1

La pregunta primaria se limita a **morfología estructural óptica aparente a baja/moderada redshift**, no a identidad evolutiva ni a equivalencia física total. Incluye:

- concentración y perfil relativo de luz;
- prominencia relativa de bulbo y disco;
- barras;
- brazos, multiplicidad y estructura no axisimétrica cuando estén resueltos;
- elongación e inclinación proyectada;
- asimetría, clumps y perturbaciones;
- colas, puentes y rasgos de interacción cuando superen el límite observacional.

No incluye por definición primaria:

- coordenadas celestes;
- orientación absoluta en el detector;
- luminosidad total;
- tamaño angular como criterio de clase;
- firma del survey;
- redshift como característica deseada;
- color global como sustituto de forma.

La proyección e inclinación sí afectan la apariencia morfológica. No se borrarán automáticamente: se reportará una estructura “aparente” y, por separado, se estudiará cuánto cambia al condicionar por `axis ratio`.

---

## 3. Estado del arte y lectura crítica

### 3.1 Taxonomías no supervisadas

La literatura ya contiene pipelines que producen agrupamientos útiles sin etiquetas. Hocking et al. desarrollaron una taxonomía automática mediante descriptores locales, Growing Neural Gas y clustering jerárquico, aplicada a HST Frontier Fields/CANDELS, y mostraron concordancia parcial con clasificaciones humanas y capacidad de recuperar objetos raros [Hocking et al. 2018]. Cheng et al. combinaron VQ-VAE y clustering jerárquico, obteniendo 27 grupos correlacionados con Sérsic, concentración, asimetría, Gini, color, masa y tamaño [Cheng et al. 2021]. Ese trabajo es especialmente instructivo para AAC: introduce explícitamente separabilidad en la pérdida y usa orientación para elegir cortes del árbol, de modo que parte de la discreción es una decisión metodológica, no una propiedad independiente demostrada.

Conclusión: **la viabilidad de agrupar galaxias está establecida; la unicidad, robustez cross-observer y naturaleza discreta de la estructura no lo están**.

### 3.2 Self-supervised learning y representation learning

Hayat et al. mostraron que contrastive learning sobre imágenes multibanda SDSS produce representaciones transferibles a morfología y redshift usando menos etiquetas que modelos supervisados [Hayat et al. 2021]. Stein et al. escalaron SSL y búsqueda por similitud a 42 millones de imágenes de DESI Legacy Surveys, demostrando recuperación de objetos raros a partir de ejemplos [Stein et al. 2021]. Mohale y Lochner aplicaron BYOL a Galaxy Zoo DECaLS, luego BGMM y Astronomaly; hallaron grupos morfológicamente coherentes, pero también clusters afectados por zoom, compañeros y artefactos [Mohale & Lochner 2024].

Estos resultados justifican SSL como familia de encoders, pero no justifican cualquier augmentation. En contrastive/non-contrastive learning, definir dos vistas como “el mismo objeto” equivale a imponer una relación de equivalencia. Esa decisión es científica, no solo ingenieril.

### 3.3 Representaciones fundacionales y multimodales

AstroCLIP alinea imágenes Legacy Survey y espectros DESI en un espacio común y logra resultados fuertes en similitud, redshift y propiedades físicas [Parker et al. 2024]. Es un baseline moderno valioso, pero no un árbitro de morfología pura: sus autores muestran que el alineamiento organiza fuertemente el espacio de imágenes por redshift. Para este proyecto, eso lo convierte simultáneamente en comparador potente y control positivo de un posible confusor.

La frontera 2025–2026 incluye modelos fundacionales multimodales, representaciones de Euclid y análisis mediante masked/sparse autoencoders. Son relevantes para fases posteriores, pero no eliminan el problema epistemológico: un modelo grande puede aprender una representación útil y al mismo tiempo comprimir morfología, redshift, color, selección e instrumento en la misma geometría. La escala del modelo no convierte proximidad latente en equivalencia morfológica.

### 3.4 Clusters, manifolds y continuos

Los trabajos existentes usan k-means, mezclas gaussianas, clustering jerárquico, density-based clustering y UMAP/LLE. La literatura demuestra que esos instrumentos revelan organización, pero una proyección 2D puede crear o exagerar separaciones. En este proyecto:

- PCA, diffusion maps y estimación de dimensión intrínseca servirán para evaluar estructura continua;
- k-means, GMM/BGMM, HDBSCAN y clustering jerárquico servirán como vistas discretas alternativas;
- UMAP se limitará a inspección y comunicación;
- la hipótesis discreta competirá contra la hipótesis continua y contra nulls sin clusters.

### 3.5 Galaxy Zoo y el problema de la “verdad”

Galaxy Zoo aporta distribuciones de votos, rutas por un árbol de decisión y desacuerdo humano, no una ontología. Galaxy Zoo DECaLS reunió millones de clasificaciones para 314 000 galaxias; Galaxy Zoo DESI publica mediciones automatizadas para 8.67 millones y votos humanos para una fracción [Walmsley et al. 2022; Walmsley et al. 2023]. La documentación oficial indica que GZ DESI reemplaza a GZ DECaLS para nuevos catálogos, pero el archivo GZ DECaLS y su intersección con SDSS siguen siendo particularmente útiles para este piloto reproducible y para construir pares cross-survey.

Las etiquetas se usarán como:

- distribuciones continuas de votos y entropía de desacuerdo;
- variables de interpretación post hoc;
- benchmark externo frente a preguntas específicas (smooth/features, edge-on, bar, spiral, merger);
- nunca como criterio para elegir encoder, augmentations, número de clusters o hiperparámetros.

Las predicciones Zoobot dependen de votos Galaxy Zoo y se declararán **supervisadas**. No son validación independiente.

### 3.6 Anomalías morfológicas

Astronomaly formaliza detección activa y personalizada de anomalías; mostró que la interacción experta puede aproximadamente duplicar el rendimiento inicial de hallazgo en sus pruebas [Lochner & Bassett 2021]. Storey-Fisher et al. combinaron WGAN, residuales, autoencoder y UMAP en casi un millón de galaxias HSC, encontrando mergers, rasgos de marea y sistemas extremos [Storey-Fisher et al. 2021]. Mohale y Lochner demostraron reutilización de features SSL para buscar mergers. AnomalyMatch representa una línea reciente semi-supervisada/activa y escalable, pero ya no es descubrimiento estrictamente no supervisado [Gómez & O'Ryan 2025; O'Ryan & Gómez 2025].

Conclusión: la rareza geométrica es un filtro de candidatos. El interés científico requiere estabilidad, descarte de artefactos y revisión experta.

### 3.7 Domain shift y robustez cross-survey

DeepAstroUDA y trabajos relacionados muestran que modelos de morfología pueden degradarse fuertemente entre SDSS, DECaLS, distinta profundidad o distintos años simulados de LSST, y que domain adaptation puede recuperar rendimiento [Ćiprijanović et al. 2022, 2023]. Esos resultados provienen principalmente de clasificación supervisada o semi-supervisada; demuestran la severidad del problema, no garantizan que una estructura no supervisada sea survey-invariant.

El vacío específico que aborda este proyecto no es “hacer clustering de galaxias”, sino **auditar si una estructura morfológica no supervisada sobrevive al observador y si merece llamarse clase, continuo o anomalía**.

---

## 4. Dataset inicial recomendado

### 4.1 Cohorte A — núcleo controlado

**Parent sample:** campaña GZD-5 de Galaxy Zoo DECaLS dentro de la huella SDSS DR8, usando sus coordenadas e identificadores, pero sin exponer etiquetas al pipeline de descubrimiento. GZD-5 contiene la cohorte más grande y usa DECaLS DR5 y el árbol de decisión mejorado.

**Imágenes primarias:** cutouts FITS de **DECaLS DR5** en `g,r,z`. Las imágenes históricas de GZ DECaLS proceden de DR1/DR2/DR5; al restringir el núcleo a GZD-5 se fija DR5 y se evita mezclar releases. DR10 no sustituirá silenciosamente DR5; podrá añadirse como cambio de observador.

**Ventaja científica:** la selección permite obtener imágenes SDSS del mismo objeto. El par `(DECaLS_i, SDSS_i)` funciona como perturbación del operador de observación manteniendo fija la galaxia.

**Ventaja práctica:** existe un catálogo público estable, identificadores, clasificaciones humanas posteriores, imágenes publicadas y abundante literatura comparable. La selección original ya restringe el parent sample a `z <= 0.15` en el NASA-Sloan Atlas y a radio Petrosiano `>= 3 arcsec`; estas condiciones se registran como selección heredada, no como hallazgo.

**Limitación:** la muestra es seleccionada, de bajo/moderado redshift, y no representa automáticamente la población de Euclid/JWST/Rubin.

### 4.2 Unidad observacional

Cada fila lógica corresponde a un `galaxy_id` y contiene:

- coordenadas y procedencia;
- cubo de imagen FITS `g,r,z`;
- inverse variance o mapas de peso disponibles;
- máscara de píxeles/flags;
- PSF por banda o resumen de seeing;
- estimación de background y ruido;
- segmentación del target y vecinos;
- cutout SDSS pareado, cuando exista;
- vistas derivadas, ligadas al mismo `galaxy_id`;
- metadatos de confusión;
- tablas de evaluación bloqueadas.

Una imagen JPEG RGB puede utilizarse solo como baseline de compatibilidad con trabajos previos, no como dato científico primario.

### 4.3 Criterios de elegibilidad congelados

Se incluirán objetos que cumplan todos estos criterios, calculados sin Galaxy Zoo:

1. cobertura finita en `g,r,z` en el cutout;
2. centro no afectado por un bit de máscara fatal (saturación, bleed severo o ausencia de datos);
3. al menos 90% de píxeles válidos dentro de la región central de análisis;
4. señal integrada positiva y `S/N >= 20` en `r` dentro de la segmentación;
5. diámetro aparente estimado del target de al menos 12 píxeles y contenido dentro del cutout fijo;
6. no duplicación: detecciones que correspondan a la misma galaxia se consolidan bajo un solo `galaxy_id`;
7. vecinos no se eliminan por principio; se registra `contamination_fraction` y se crea un estrato limpio, porque interacción/compañeros pueden ser señal física.

Los nombres concretos de columnas y bits se congelarán en `DATA_CONTRACT.md` después de verificar los esquemas oficiales. No se reemplazará un criterio lógico por una etiqueta morfológica.

### 4.4 Vistas de imagen

**O0 — marco observacional fijo (primario):**

- 256×256 píxeles;
- escala nativa de DECaLS, 0.262 arcsec/píxel;
- 67.1 arcsec de campo;
- centro en la posición catalogada, con corrección de centrado registrada;
- banda `r` para la pista estructural primaria.

**O1 — marco normalizado por tamaño (auditoría):**

- misma galaxia reescalada para que el radio de media luz ocupe 32 píxeles;
- campo final 256×256;
- la transformación y su factor se guardan;
- no reemplaza O0 y no se utiliza para declarar clases si O0 y O1 discrepan.

**O2 — multibanda (ablación):**

- canales calibrados `g,r,z`, no JPEG;
- mismo WCS, campo y máscaras que O0;
- se compara contra `r` para distinguir estructura aportada por color.

**O3 — cross-survey:**

- imagen SDSS de la misma galaxia;
- versión nativa y versión armonizada a PSF/pixelización común;
- se usa solo para robustez del observador.

**O_GZ — réplica de presentación (auditoría):**

- imagen 424×424 con el escalado dependiente de radios Petrosianos utilizado por GZ DECaLS;
- conserva el encuadre sobre el que se emitieron los votos humanos;
- se usa para medir cuánto cambia la estructura por el framing adaptativo, no como observación científica primaria.

### 4.5 Preprocesamiento primario

1. conservar unidades y calibración originales en el artefacto inmutable;
2. sustraer background con estimador robusto en región externa, enmascarando fuentes;
3. propagar máscara e inverse variance;
4. recentrar sin rotar ni reescalar;
5. producir dos normalizaciones:
   - `P_flux`: transformación `asinh` con escala global fijada en train, preservando diferencias de brillo;
   - `P_shape`: dividir por flujo positivo total del target y aplicar `asinh`, reduciendo luminosidad total pero preservando perfil relativo;
6. no igualar histogramas por imagen;
7. no aplicar deblending nuevo en v0.1; auditar el deblending del survey como parte del observador.

### 4.6 Splits y cuarentena

El split se realizará por regiones HEALPix, no por filas aleatorias, para reducir leakage espacial y condiciones observacionales compartidas.

- `train_discovery`: 70% de tiles;
- `dev_calibration`: 15% de tiles;
- `holdout_confirmatory`: 15% de tiles, inaccesible hasta congelar métricas y Gates;
- asignación determinista por hash de `HEALPix nside=16` y semilla de proyecto;
- todos los duplicados, vistas y pares de una galaxia pertenecen al mismo split.

Tablas separadas:

- `TRAIN_VISIBLE`: imágenes y metadatos necesarios para preprocessing;
- `CONFOUND_AUDIT`: redshift, PSF, S/N, tamaño aparente, background, profundidad, máscara, survey y campo;
- `INTERPRETATION_LOCKBOX`: votos Galaxy Zoo, Zoobot y variables físicas no necesarias para auditoría;
- `HOLDOUT_LOCKBOX`: imágenes/filas confirmatorias.

### 4.7 Cohortes futuras, no iniciales

- GZ DESI DR8 fuera de la intersección SDSS: generalización geográfica/instrumental y réplica exacta mediante el servicio DR8;
- SDSS Stripe 82: profundidad repetida;
- HSC: mayor profundidad y resolución;
- Galaxy Zoo Euclid Q1: dominio espacial y mayor redshift;
- UKIDSS: cambio de longitud de onda, tratado como **no-invariancia potencial** por morphological k-correction;
- JWST/CANDELS: nueva fase científica, no simple test del mismo problema.

---

## 5. Transformaciones: invariancias, pruebas y prohibiciones

### 5.1 Invariancias primarias impuestas

Estas transformaciones forman `T_preserve_core` para la pregunta de v0.1:

| Transformación | Rango | Justificación | Riesgo |
|---|---:|---|---|
| Rotación en el plano | uniforme `[0°,360°)` | orientación del detector no define tipo | interpolación/aliasing |
| Traslación pequeña | hasta 5% del ancho | error de centrado no define morfología | bordes/crop |
| Reflexión | horizontal o vertical, pista sin quiralidad | la pregunta primaria excluye handedness | borra una posible señal de paridad; se conserva pista sin reflexión |
| Escala fotométrica global | factor `[0.9,1.1]` común | tolerancia a calibración absoluta | no equivale a contraste arbitrario |
| Offset de background | dentro de `±0.5 sigma_sky` | tolerancia a error residual leve | puede ocultar rasgos débiles |

Se entrenarán dos variantes idénticas salvo reflexión. Una discrepancia material obliga a declarar que el resultado depende de quiralidad/reflexión.

### 5.2 Robustez deseada, pero no invariancia irrestricta

| Factor | Política |
|---|---|
| PSF/seeing | degradar observaciones buenas a PSF objetivo dentro del soporte de datos y medir estabilidad; no exigir recuperar rasgos irresolubles |
| Ruido/profundidad | inyectar ruido compatible con inverse variance y estudiar curvas de degradación; permitir abstención |
| Tamaño aparente | comparar O0 y O1; no usar zoom/crop agresivo como positive pair primario |
| Brillo superficial | preservar en `P_flux` y contrastar con `P_shape`; no borrarlo por normalización local automática |
| Contaminación | registrar y estratificar; no eliminar todos los compañeros, porque interacción puede ser morfología real |

### 5.3 No-invariancias o transformaciones científicamente peligrosas

No se impondrán como augmentations positivas en el experimento primario:

- cambio de banda o permutación `g,r,z`;
- jitter independiente de color;
- ecualización de histograma o contraste fuerte;
- blur arbitrario;
- redimensionamiento que normalice tamaño sin pista paralela;
- crop que elimine colas, compañeros o disco externo;
- random erasing/cutout;
- mezcla entre galaxias;
- eliminación automática de asimetrías;
- transformación a JPEG RGB como única observación.

### 5.4 Controles que deben destruir información

`T_destroy` verificará que el encoder no sea indiferente a todo:

- **radialización:** sustituir la imagen por su perfil azimutal, preservando perfil radial y destruyendo barra, brazos y asimetría;
- **randomización de fase:** preservar aproximadamente el espectro de potencias y destruir organización espacial;
- **permutación de cuadrantes:** conservar histograma y energía local, destruir coherencia global;
- **enmascarado central/extenso controlado:** probar sensibilidad diferencial a bulbo y disco.

Una representación que trata `T_destroy` como equivalente no es admisible para la pregunta primaria aunque produzca clusters estables.

---

## 6. Hipótesis y alternativas

### H1 — equivalencia representacional

Existe al menos una familia de representaciones que comprime `T_preserve_core`, responde a `T_destroy` y conserva geometría local fuera de muestra.

**Alternativa:** ninguna representación logra simultáneamente invariancia y sensibilidad; la equivalencia propuesta es demasiado amplia, demasiado estrecha o no identificable con estas imágenes.

### H2 — estructura morfológica reproducible

Después de controlar el observador, existe geometría local reproducible en la población.

H2 no exige clusters. Puede manifestarse como continuo, manifold, jerarquía o mixtures.

**Alternativa:** la geometría cambia más entre observadores razonables de lo que se conserva.

### H3 — discreción (hipótesis subordinada)

La distribución contiene valles de densidad y particiones reproducibles que justifican al menos una descripción discreta en una escala declarada.

**Alternativa:** la descripción continua/jerárquica explica igual o mejor los datos. En ese caso se rechaza H3 sin rechazar H2.

### H4 — relevancia astronómica posterior

La estructura robusta aporta información fuera de muestra sobre variables físicas no usadas en el aprendizaje, más allá de un baseline de confusores y fotometría simple.

**Alternativa:** la estructura es morfológicamente interpretable pero no añade información física detectable, o solo recapitula color/redshift/masa.

### H5 — utilidad residual de AAC

La auditoría AAC cambia justificadamente al menos una conclusión que habría producido `encoder → embedding → clustering`: rechaza una partición, identifica un confusor, prefiere un continuo, delimita la escala válida o recupera anomalías más estables.

**Alternativa:** el mejor pipeline convencional produce las mismas conclusiones, robustez y limitaciones con menor complejidad. En ese caso AAC no aporta utilidad científica residual.

---

## 7. Baselines obligatorios

### 7.1 Representaciones

| ID | Representación | Función |
|---|---|---|
| R0 | vector clásico: concentración, asimetría, smoothness, Gini, M20, ellipticidad y tamaño relativo | baseline interpretable |
| R1 | píxeles `P_shape` + Incremental PCA (32, 64, 128 componentes) | baseline mínimo |
| R2 | convolutional autoencoder, latentes 32/128 | reconstrucción no supervisada |
| R3 | BYOL + ResNet-18, imagen `r`, 5 seeds | SSL principal reproducible y comparable con Mohale & Lochner |
| R4 | encoder contrastivo MoCo-v2 o pesos públicos equivalentes, cuando la licencia/datos lo permitan | alternativa SSL |
| R5 | AstroCLIP image encoder congelado | baseline fundacional moderno y control de redshift |
| R6 | ImageNet ResNet-18 congelado | control de transferencia no astronómica |
| R7 | Zoobot congelado | techo/comparador supervisado; excluido de selección y de la categoría “no supervisado” |

R4 podrá posponerse si no hay artefacto reproducible. No se sustituirá por una implementación aproximada sin registrarlo.

### 7.2 Métodos de estructura

- k-means para `k ∈ {2,3,4,5,6,8,10,15,20,30}`;
- GMM con covarianza diagonal y completa donde sea computacionalmente viable;
- BGMM con truncación superior 30;
- HDBSCAN con barrido predeclarado de `min_cluster_size ∈ {50,100,250,500}` y `min_samples ∈ {10,30,50}`;
- aglomerativo Ward/average sobre subconjuntos reproducibles;
- diffusion maps y grafo kNN para hipótesis continua;
- PCA y estimación de dimensión intrínseca TwoNN/MLE;
- spectral clustering solo en subconjuntos, como sensibilidad.

No se seleccionará un método por apariencia del gráfico. Silhouette, Calinski–Harabasz y Davies–Bouldin son diagnósticos secundarios, no criterios únicos.

### 7.3 Nulls

Cada afirmación de estructura se comparará con:

1. Gaussian null con media/covarianza de la representación;
2. null unimodal generado preservando espectro de covarianza;
3. embeddings con píxeles espacialmente destruidos pero histograma preservado;
4. agrupamiento inducido solo por confusores observacionales;
5. asignaciones aleatorias preservando tamaños de cluster.

---

## 8. Arquitectura experimental

### Fase E0 — contrato y auditoría de datos

- resolver esquemas, licencias, checksums y conteos;
- crear manifiesto por objeto;
- estimar exclusiones y sesgo de selección;
- producir splits sin cargar etiquetas Galaxy Zoo;
- verificar duplicados y pares cross-survey.

### Fase E1 — baselines simples

- ejecutar R0 y R1 en O0/P_shape;
- medir dimensión, clustering tendency, estructura continua y particiones;
- ejecutar nulls;
- registrar si ya explican cualquier hallazgo posterior.

### Fase E2 — representación no supervisada

- entrenar R2 y R3 con seeds `{11, 23, 47, 89, 131}`;
- latente `{32,128}`;
- augmentations `T_preserve_core` y variante sin reflexión;
- no acceder a `INTERPRETATION_LOCKBOX`;
- guardar checkpoints, features pre-reducción y logs.

### Fase E3 — equivalencia y controles

- medir órbitas bajo `T_preserve_core`;
- medir respuesta a `T_destroy`;
- comparar P_flux/P_shape y O0/O1/O2;
- descartar representaciones colapsadas o insensibles.

### Fase E4 — forma de la estructura

- comparar hipótesis discreta, continua, jerárquica y nula;
- construir matriz de co-vecindad/co-asignación entre representaciones;
- marcar regiones estables, ambiguas y sin soporte;
- no asignar nombres astronómicos todavía.

### Fase E5 — confusores y observador

- probes y asociaciones con PSF, S/N, redshift, tamaño, superficie, background, contaminación y campo;
- matching/estratificación;
- degradación contrafactual del mismo objeto;
- comparación DECaLS–SDSS nativa y armonizada.

### Fase E6 — congelación confirmatoria

Antes de abrir holdout se congelan:

- representación(es) candidata(s);
- métricas;
- estructura hipotetizada;
- reglas de matching;
- umbrales;
- gráficos permitidos;
- análisis estadístico;
- criterios de aprobación/rechazo.

### Fase E7 — holdout e interpretación

- ejecutar una sola evaluación confirmatoria principal;
- abrir votos humanos y variables físicas únicamente después;
- reportar todos los resultados, no solo los favorables;
- cualquier ajuste posterior se etiqueta exploratorio y requiere nuevo holdout.

### Fase E8 — anomalías

- construir perfiles multiaxiales;
- separar artefacto, rareza observacional, ambigüedad y rareza morfológica;
- revisión experta ciega a score específico;
- no reutilizar feedback experto para afirmar rendimiento no supervisado original.

---

## 9. Métricas

### 9.1 Fidelidad a invariancias

Para transformación `t`:

- `orbit_ratio = median d(g(x),g(t(x))) / median d(g(x),g(x_random))`;
- Jaccard de vecinos top-k antes/después;
- rank correlation de distancias;
- tasa de cambio de cluster, separando puntos de alta y baja pertenencia;
- curva de estabilidad frente a PSF, ruido y background.

### 9.2 Sensibilidad morfológica

- razón `d_destroy / d_preserve` por objeto;
- pérdida de vecinos bajo radialización y randomización de fase;
- respuesta diferencial a máscara central vs. externa;
- no-colapso: effective rank, varianza por dimensión y uniformidad de vecinos.

### 9.3 Robustez entre observadores

- overlap de vecinos ajustado por azar;
- Spearman de distancias por pares;
- CKA como diagnóstico auxiliar, no como equivalencia;
- ARI, AMI y Variation of Information para particiones;
- Jaccard de clusters emparejados;
- matriz de co-asignación y entropía de consenso.

### 9.4 Evidencia de estructura

- estabilidad bootstrap;
- prediction strength en holdout;
- DBCV para density clustering;
- held-out likelihood/BIC para mixtures, interpretados con cautela;
- persistencia de comunidades al variar escala `k`;
- dimensión intrínseca con intervalos bootstrap;
- trustworthiness/continuity para proyecciones;
- comparación contra nulls.

### 9.5 Confusores

Para cada confusor:

- capacidad de predicción desde embedding (`R²`, MAE o AUC);
- mutual information estimada;
- standardized mean differences entre grupos;
- persistencia de vecindades/particiones después de matching;
- incremento explicativo del embedding sobre un modelo nuisance-only.

Que el redshift sea predecible es una alarma, no prueba automática de contaminación: puede correlacionar con población y resolución. La evidencia adversa fuerte será que la estructura desaparezca dentro de estratos o bajo observaciones pareadas/controladas.

### 9.6 Validación post hoc

**Galaxy Zoo:** distribuciones de votos, entropía, mutual information, Cramér's V, calibración de un probe simple y análisis de objetos de desacuerdo.

**Variables físicas:** `ΔR²`, `ΔMAE` o `Δlog-likelihood` en holdout al añadir embedding/coordenadas/cluster a un baseline de redshift + fotometría simple.

**Variables prioritarias:**

- espectroscópicas: sSFR/SFR, D4000, Hα equivalente, metalicidad, dispersión de velocidad, clase BPT;
- derivadas: masa estelar, edad y metalicidad de población;
- environment: densidad local, pertenencia a grupo/halo cuando exista;
- estructurales externas: Sérsic, concentración, axis ratio, tamaño, Gini-M20, declaradas como no plenamente independientes porque provienen de las mismas imágenes;
- color: útil para interpretación, pero no independiente de O2.

Redshift se usa principalmente como confusor y estratificador, no como evidencia física favorable.

---

## 10. Cómo decidir entre clases, continuo, jerarquía o ausencia

### Salida D — estructura discreta aceptable

Requiere simultáneamente:

- valles/densidades reproducibles más allá de nulls;
- `median ARI >= 0.70` entre seeds del mismo método;
- `median ARI >= 0.50` entre al menos tres familias de representación admisibles;
- `prediction strength >= 0.80` en holdout para al menos una escala;
- estabilidad de objetos de alta confianza frente a perturbaciones;
- ninguna variable observacional explica por sí sola las particiones.

La cantidad de clusters se reportará como rango/escala si varias resoluciones son defendibles.

### Salida C — estructura continua/manifold

Se prefiere cuando:

- particiones no alcanzan criterios D;
- los vecinos y principales coordenadas de difusión son reproducibles;
- `Spearman >= 0.80` entre coordenadas alineadas o distancias geodésicas;
- `kNN overlap >= 0.60` entre observadores admisibles;
- variables post hoc cambian gradualmente sin valles robustos.

### Salida H — jerarquía

Se acepta si existen ramas anidadas persistentes en bootstrap y entre representaciones, pero no un único corte privilegiado. Se reporta dendrograma/árbol de consenso con rangos de persistencia, no una lista única de clases.

### Salida M — mixture/ambigüedad

Se utiliza cuando hay regiones densas reconocibles conectadas por transiciones o gran pertenencia suave. Se conservan probabilidades y entropía; no se fuerza hard assignment.

### Salida N — ausencia de estructura robusta

Se declara cuando la estabilidad no supera nulls, las representaciones razonables son incompatibles o la geometría está dominada por confusores. Esta es una conclusión científica válida.

---

## 11. Anomalías: definición operacional

Cada objeto recibe un **perfil**, no un único score:

1. `density_outlier`: baja densidad local (LOF/HDBSCAN);
2. `compression_outlier`: alto residual de reconstrucción normalizado por S/N;
3. `observer_instability`: vecinos o pertenencia inconsistentes entre encoders/surveys;
4. `transformation_sensitivity`: respuesta anormal a `T_preserve_core`;
5. `off_manifold`: residual respecto de la geometría dominante;
6. `bridge_score`: posición persistente entre regiones densas;
7. `artifact_risk`: máscara, background, saturación, vecino/deblend, borde.

Se reportarán listas Pareto y consenso por rangos. No se sumarán los ejes con pesos aprendidos después de ver objetos interesantes.

Categorías de salida:

- artefacto/instrumental;
- objeto mal segmentado o contaminado;
- raro por condición observacional;
- extremo de un continuo conocido;
- transición/puente;
- morfología rara estable;
- inconsistencia no explicada, candidata a follow-up.

---

## 12. Gates adversariales

### Gate 0 — procedencia, leakage y congelación

**Prueba:** el pipeline de descubrimiento no puede acceder a Galaxy Zoo, Zoobot ni variables físicas de interpretación; splits, seeds y criterios están versionados.

**Apoya:** auditoría de columnas, hashes y dependencias sin rutas de leakage.

**Revisar/abandonar:** cualquier etiqueta o modelo entrenado con Galaxy Zoo influye en selección del encoder, augmentations, hiperparámetros, `k` o elección del resultado. Se invalida la corrida completa.

### Gate 1 — validez de la unidad y del dataset

**Hipótesis:** cada fila representa una galaxia y no un crop/duplicado/artefacto; la exclusión no construye inadvertidamente una taxonomía.

**Apoya:** duplicados consolidados, vistas ligadas, menos de 1% de fallos no explicados y reporte de selección por S/N, tamaño, redshift y campo.

**Revisar:** más de 5% de exclusiones técnicas o fuerte dependencia de exclusión con redshift/brillo/tamaño. Redefinir muestra y reiniciar splits.

**Abandonar cohorte:** no puede recuperarse una correspondencia fiable entre objeto, cutout y metadatos.

### Gate 2 — equivalencia no trivial

**Hipótesis:** la representación comprime transformaciones permitidas sin borrar morfología.

**Apoya:** para rotación/traslación, `median top-50 neighbor Jaccard >= 0.70`, percentil 10 `>= 0.40` y `median orbit_ratio <= 0.20`; además `median d_destroy/d_preserve >= 2`.

**Revisar:** falla una sola familia de transformaciones o la sensibilidad depende de normalización; ajustar la relación de equivalencia, no el resultado deseado.

**Abandonar representación:** colapso, indiferencia a radialización/randomización o imposibilidad de equilibrar invariancia y sensibilidad.

### Gate 3 — ¿galaxias o proceso de observación?

**Hipótesis:** la geometría candidata no se explica principalmente por PSF, ruido, redshift, tamaño, superficie, background, campo o contaminación.

**Apoya:** al armonizar/degradar y hacer matching, sobreviven al menos 70% de las relaciones top-50 de consenso y ninguna partición principal coincide casi completamente con un único confusor.

**Revisar:** pérdida de 30–50% de vecinos o asociación fuerte localizada; restringir dominio de validez, estratificar o modelar incertidumbre.

**Abandonar afirmación morfológica:** más de 50% de la geometría estable desaparece bajo control razonable, o un clasificador nuisance-only reproduce las particiones con `ARI >= 0.80`.

### Gate 4 — forma de la estructura

**Hipótesis:** los datos favorecen una de D/C/H/M sobre N.

**Apoya discreción:** criterios de la sección 10 para D.

**Apoya continuo:** criterios C con particiones inestables.

**Revisar:** evidencia dependiente de UMAP, de un único `k`, de un único encoder o de un corte posterior al gráfico.

**Abandonar estructura:** desempeño no superior a nulls y baja reproducibilidad geométrica.

### Gate 5 — robustez del observador

**Hipótesis:** la estructura se conserva al cambiar seed, encoder, preprocessing y survey.

**Apoya:** al menos tres representaciones admisibles sostienen la geometría; en pares DECaLS–SDSS armonizados, la distancia del par real cae en el decil inferior frente a controles emparejados y la asignación de alta confianza coincide `>= 0.70`.

**Revisar:** robustez solo dentro de un encoder o survey; degradar la afirmación a “estructura específica del observador”.

**Abandonar universalidad:** un clasificador de survey sobre pares armonizados logra `AUC > 0.65` y la estructura se alinea con survey, o la co-asignación cross-survey es `< 0.50`.

### Gate 6 — generalización confirmatoria

**Hipótesis:** reglas congeladas generalizan a tiles nunca vistos.

**Apoya:** todos los umbrales principales mantienen su categoría en `holdout_confirmatory`, con intervalos bootstrap compatibles con dev.

**Revisar:** caída de 10–20 puntos porcentuales en estabilidad o cobertura.

**Abandonar conclusión:** cambio de salida D/C/H/M a N, o necesidad de cambiar hiperparámetros después de abrir holdout.

### Gate 7 — interpretación humana y física

**Hipótesis:** la estructura robusta posee interpretación externa sin haber sido moldeada por ella.

**Apoya:** asociación reproducible con votos humanos continuos y/o incremento físico fuera de muestra. Umbral físico principal: `ΔR² >= 0.02` con límite inferior bootstrap 95% `> 0` para al menos dos variables espectroscópicas, frente al baseline nuisance + fotometría.

**Revisar:** solo color, Sérsic o axis ratio muestran asociación; declarar posible recapitulación de proxies visuales.

**No implica abandono automático:** falta de correlación física no borra una estructura morfológica robusta, pero hace fallar H4.

**Abandonar significado físico:** toda asociación desaparece al condicionar por redshift/fotometría o solo existe con etiquetas Zoobot no independientes.

### Gate 8 — anomalías estables y útiles

**Hipótesis:** los perfiles multiaxiales priorizan objetos interesantes mejor que scores simples.

**Apoya:** candidatos presentes en al menos 3 representaciones, artefactos `< 50%` del top revisado y tasa de interés experto al menos 3 veces la muestra aleatoria estratificada.

**Revisar:** una familia de score domina o el resultado depende del revisor; conservar perfiles y personalización.

**Abandonar claim de descubrimiento:** lista dominada por saturación, bordes, deblending o baja S/N, o no mejora a LOF/reconstruction error simples.

### Gate 9 — utilidad residual de AAC

**Hipótesis:** la disciplina AAC produce una decisión científicamente mejor que el mejor pipeline convencional.

**Apoya:** al menos una conclusión cambia por evidencia adversarial y el resultado retenido generaliza mejor o declara correctamente incertidumbre/continuidad/null.

**Revisar:** AAC añade documentación pero no modifica resultados ni errores.

**Abandonar AAC como contribución separada:** el mejor baseline alcanza igual robustez, detección de confusores, interpretación y honestidad de salida con menor complejidad. Conservar AAC solo como checklist pedagógico.

---

## 13. Criterios globales de éxito y fracaso

### Éxito científico mínimo

El proyecto es exitoso si produce de forma reproducible una de estas conclusiones:

- una estructura discreta delimitada y robusta;
- un continuo/manifold reproducible sin clases privilegiadas;
- una jerarquía con escalas explícitas;
- regiones ambiguas y anomalías estables;
- o una demostración convincente de que, bajo estos datos, no hay estructura morfológica separable de los confusores.

### Éxito fuerte

Además del éxito mínimo:

- la estructura sobrevive cross-survey;
- aporta información física independiente en holdout;
- y el protocolo supera o corrige una conclusión de baselines simples/modernos.

### Fracaso de la hipótesis morfológica

Se declara si:

- ninguna representación supera Gate 2;
- la geometría se explica principalmente por observación (Gate 3/5);
- la estructura no supera nulls;
- el holdout revierte la conclusión;
- o solo puede obtenerse modificando retrospectivamente equivalencia, filtros o número de clusters.

### Fracaso de AAC como aporte

Incluso si se descubre estructura, AAC no aporta utilidad residual si:

- R0/R1 o un SSL convencional producen la misma conclusión con la misma robustez;
- los Gates no eliminan falsos hallazgos ni cambian el dominio de validez;
- las métricas AAC son solo renombres de estabilidad/clustering/domain adaptation existentes;
- o el costo metodológico no produce información adicional accionable.

No se reclamará un “algoritmo AAC” salvo que una necesidad no cubierta por métodos existentes aparezca y sobreviva comparación directa.

---

## 14. Reproducibilidad y gobernanza

### 14.1 Seeds

Seeds maestras: `{11, 23, 47, 89, 131}`. Todo submuestreo, inicialización y bootstrap deriva de una de ellas y registra su linaje.

### 14.2 Artefactos obligatorios

- `DATA_MANIFEST.parquet`: un registro por galaxia/vista;
- `DATA_CONTRACT.md`: columnas, unidades, máscaras, licencias, consultas y checksums;
- `SPLIT_MANIFEST.parquet`: tile, split y razón;
- `PREPROCESSING_SPEC.yaml`;
- `EXPERIMENT_SPEC.yaml` por corrida;
- environment lock/container digest;
- checkpoints y embeddings sin reducción;
- métricas crudas por objeto;
- índices de vecinos y matrices de co-asignación;
- figuras generadas desde datos, nunca editadas manualmente;
- `GATE_LEDGER.md`: aprobado/fallido/inconcluso, evidencia y decisión;
- `NEGATIVE_RESULTS.md`;
- model/data cards;
- log de acceso al holdout.

### 14.3 Registro de decisiones

Cada cambio posterior a v0.1 debe indicar:

- motivo anterior a resultados o motivo posterior a resultados;
- evidencia que lo exigió;
- análisis afectados;
- si convierte una prueba confirmatoria en exploratoria;
- nuevo número de versión.

### 14.4 Incertidumbre y multiplicidad

- intervalos bootstrap agrupados por tile, no por imagen independiente;
- corrección FDR para familias amplias de asociaciones post hoc;
- reportar tamaños de efecto e intervalos, no solo p-values;
- separar cobertura (qué fracción recibe asignación) de pureza/estabilidad;
- conservar objetos no asignados.

---

## 15. Paquete posterior para Codex

Codex no recibirá “aplicar AAC”. Recibirá, en este orden:

### C0 — inventario reproducible, sin entrenamiento

1. `CODEX_PHASE_C0_SPEC.md` con fuentes exactas, comandos permitidos, checksums y outputs;
2. implementación de descarga/materialización y manifiesto;
3. informe de disponibilidad real de campos y conteos tras cada filtro;
4. ninguna optimización de modelos.

### C1 — contrato de datos y preprocessing

1. `DATA_CONTRACT.md` congelado;
2. funciones deterministas para O0–O3 y P_flux/P_shape;
3. pruebas unitarias de centrado, escala, máscaras, PSF y duplicados;
4. galería QA estratificada, sin etiquetas morfológicas.

### C2 — baselines

1. R0/R1;
2. nulls;
3. métricas de E1;
4. artefactos y criterios de aceptación exactos.

### C3 — representación

1. arquitectura R2/R3 exacta;
2. augmentations y probabilidades;
3. seeds, epochs, optimizer, scheduler, batches y hardware budget;
4. early stopping sin etiquetas;
5. outputs de Gate 2.

### C4 — estructura y robustez

1. matriz completa de clustering/manifold;
2. barridos cerrados;
3. matching de clusters;
4. controles de confusores y pares DECaLS–SDSS;
5. `GATE_LEDGER.md` generado desde métricas.

### C5 — confirmación e interpretación

Solo después de autorización explícita:

1. desbloqueo de holdout;
2. evaluación única pre-registrada;
3. join con Galaxy Zoo y catálogos físicos;
4. informe confirmatorio inmutable;
5. análisis posteriores separados como exploratorios.

Cada especificación para Codex incluirá objetivo, inputs, outputs, criterios de error, pruebas, límites de recursos y acciones prohibidas. Ninguna fase inferirá decisiones científicas ausentes de este seed o de una revisión versionada.

---

## 16. Riesgos abiertos que v0.1 no resuelve

1. **Frontera del objeto:** deblending puede separar o fusionar estructuras físicamente relacionadas.
2. **Morfología aparente vs. intrínseca:** una sola proyección no identifica forma 3D.
3. **Morphological k-correction:** cambiar banda puede cambiar la morfología real observada.
4. **Resolución:** invariancia no puede recuperar información que no fue medida.
5. **Selección:** GZ DECaLS/SDSS no representa galaxias débiles, pequeñas o de alto redshift.
6. **Dependencia de catálogo:** R50, segmentación y centrado ya contienen decisiones de otro pipeline.
7. **Validación física:** muchas propiedades “independientes” se derivan de la misma fotometría; se prioriza espectroscopia.
8. **Causalidad:** correlación entre latente y SFR/masa/environment no implica que la morfología cause esas variables ni viceversa.
9. **Costo computacional:** el barrido completo puede requerir una fase piloto para estimar recursos; cualquier reducción conservará la estructura factorial del diseño.

---

## 17. Registro de afirmaciones permitidas

Si los Gates se aprueban, podrá afirmarse:

> “Bajo la pregunta, muestra, transformaciones y observadores declarados, encontramos una estructura morfológica [discreta/continua/jerárquica/mixta] reproducible, con estos límites y estas asociaciones externas.”

No podrá afirmarse sin evidencia adicional:

- que las clases son tipos naturales únicos;
- que el embedding recupera la historia evolutiva real;
- que estabilidad matemática prueba realidad física;
- que concordancia con Galaxy Zoo prueba verdad ontológica;
- que una correlación física identifica causalidad;
- que robustez en DECaLS–SDSS implica robustez universal;
- que AAC constituye un nuevo algoritmo o teoría.

---

## 18. Referencias primarias y documentación oficial seleccionada

1. Hocking, A. et al. (2018), “An automatic taxonomy of galaxy morphology using unsupervised machine learning”, *MNRAS* 473, 1108. [doi:10.1093/mnras/stx2351](https://doi.org/10.1093/mnras/stx2351).
2. Cheng, T.-Y. et al. (2021), “Beyond the Hubble sequence — exploring galaxy morphology with unsupervised machine learning”, *MNRAS* 503, 4446. [doi:10.1093/mnras/stab734](https://doi.org/10.1093/mnras/stab734).
3. Hayat, M. A. et al. (2021), “Self-Supervised Representation Learning for Astronomical Images”, *ApJL* 911, L33. [doi:10.3847/2041-8213/abf2c7](https://doi.org/10.3847/2041-8213/abf2c7).
4. Stein, G. et al. (2021), “Self-supervised similarity search for large scientific datasets”. [arXiv:2110.13151](https://arxiv.org/abs/2110.13151).
5. Mohale, K. & Lochner, M. (2024), “Enabling unsupervised discovery in astronomical images through self-supervised representations”, *MNRAS* 530, 1274. [doi:10.1093/mnras/stae926](https://doi.org/10.1093/mnras/stae926).
6. Parker, L. et al. (2024), “AstroCLIP: A Cross-Modal Foundation Model for Galaxies”, *MNRAS* 531, 4990. [arXiv:2310.03024](https://arxiv.org/abs/2310.03024).
7. Walmsley, M. et al. (2022), “Galaxy Zoo DECaLS: Detailed Visual Morphology Measurements from Volunteers and Deep Learning for 314,000 Galaxies”. [arXiv:2102.08414](https://arxiv.org/abs/2102.08414).
8. Walmsley, M. et al. (2023), “Galaxy Zoo DESI: Detailed Morphology Measurements for 8.7M Galaxies in the DESI Legacy Imaging Surveys”. [arXiv:2309.11425](https://arxiv.org/abs/2309.11425).
9. Galaxy Zoo, catálogo y documentación oficial. [Galaxy Zoo Data](https://data.galaxyzoo.org/).
10. DESI Legacy Imaging Surveys, descripciones oficiales y servicio de cutouts. [DECaLS DR5](https://www.legacysurvey.org/dr5/description/) y [Legacy Survey DR10](https://www.legacysurvey.org/dr10/description/).
11. Dey, A. et al. (2019), “Overview of the DESI Legacy Imaging Surveys”, *AJ* 157, 168. [doi:10.3847/1538-3881/ab089d](https://doi.org/10.3847/1538-3881/ab089d).
12. Ćiprijanović, A. et al. (2022), “DeepAdversaries: Examining the Robustness of Deep Learning Models for Galaxy Morphology Classification”. [arXiv:2112.14299](https://arxiv.org/abs/2112.14299).
13. Ćiprijanović, A. et al. (2023), “DeepAstroUDA: Semi-Supervised Universal Domain Adaptation for Cross-Survey Galaxy Morphology Classification and Anomaly Detection”. [arXiv:2302.02005](https://arxiv.org/abs/2302.02005).
14. Lochner, M. & Bassett, B. A. (2021), “Astronomaly: Personalised Active Anomaly Detection in Astronomical Data”, *Astronomy and Computing* 36, 100481. [doi:10.1016/j.ascom.2021.100481](https://doi.org/10.1016/j.ascom.2021.100481).
15. Storey-Fisher, K. et al. (2021), “Anomaly detection in Hyper Suprime-Cam galaxy images with generative adversarial networks”. [arXiv:2105.02434](https://arxiv.org/abs/2105.02434).
16. Gómez, P. & O'Ryan, D. (2025), “AnomalyMatch: Discovering Rare Objects of Interest with Semi-supervised and Active Learning”. [arXiv:2505.03509](https://arxiv.org/abs/2505.03509).
17. O'Ryan, D. & Gómez, P. (2025), “Identifying astrophysical anomalies in 99.6 million source cutouts from the Hubble Legacy Archive using AnomalyMatch”, *A&A* 704, A227. [ADS record](https://ui.adsabs.harvard.edu/abs/2025A%26A...704A.227O/abstract).
18. Wu, J. F. & Walmsley, M. (2025), “Re-envisioning Euclid Galaxy Morphology: Identifying and Interpreting Features with Sparse Autoencoders”. [arXiv:2510.23749](https://arxiv.org/abs/2510.23749). Trabajo emergente; no se toma como evidencia consolidada.

---

## 19. Estado de congelación

**Congelado en v0.1:** pregunta, unidad observacional, dataset inicial, separación de tablas, invariancias centrales, no-invariancias, familias de baseline, métricas principales, Gates, splits, seeds, criterios globales y orden de entrega a Codex.

**Pendiente para v0.2 antes de entrenar:** resolución exacta de nombres de columnas/bits oficiales, conteos tras filtros, disponibilidad de PSF/inverse variance por fuente, presupuesto de cómputo y arquitectura detallada de R2/R3. Estas decisiones deberán documentarse sin consultar etiquetas morfológicas ni el holdout.

**Regla final:** si un método existente explica el problema mejor, se usa; si una hipótesis falla, se registra; si los datos no justifican clases discretas, no se inventan.
