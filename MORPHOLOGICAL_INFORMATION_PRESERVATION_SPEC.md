# MORPHOLOGICAL INFORMATION PRESERVATION SPECIFICATION

**Documento:** `MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md`  
**Versión:** 0.1  
**Fecha:** 2026-09-18  
**Proyecto:** Galaxy Morphology Discovery  
**Estatus:** aceptada y congelada como autoridad metodológica para diseñar la revisión del contrato observacional; no autoriza adquisición, implementación, entrenamiento ni reapertura de C0  
**Autor de la investigación:** José Salinas  
**Asistencia analítica y de redacción:** ChatGPT (OpenAI)

---

## 1. Propósito

Esta especificación define qué información debe llegar desde el producto astronómico hasta la representación entregada al encoder para que sea científicamente legítimo investigar estructura morfológica no supervisada.

Su función no es prescribir un único pipeline de preprocessing. Su función es:

1. declarar qué diferencias se pretende conservar, comprimir o someter a prueba;
2. impedir que una operación de conveniencia decida silenciosamente qué cuenta como morfología;
3. vincular la exigencia de trazabilidad del instrumento con la afirmación científica que se desea realizar;
4. convertir las decisiones de preprocessing en hipótesis auditables;
5. definir las condiciones mínimas para diseñar un nuevo contrato observacional.

Principio rector:

> **Preprocesar no es limpiar los datos: es decidir qué mundo puede ver el algoritmo. Toda pérdida de información debe estar justificada por la pregunta científica, no por costumbre computacional.**

---

## 2. Relación con C0 y AAC

### 2.1 C0 permanece cerrado

Esta especificación no modifica el resultado histórico de C0:

- C0-A: `PASS`;
- C0-B: `PASS`;
- C0-C: `INCONCLUSIVE`;
- decisión global: `STOP`;
- C0-D, C0-E y C0-F: `INCONCLUSIVE` por cierre anticipado, no por fracaso experimental.

La ruta del *normal cutout* DR5 no queda rehabilitada. C0 no demostró que ese producto fuera incorrecto; demostró que la evidencia preservada no permitía certificar suficientemente la procedencia funcional y la semántica de unidades exigidas por el contrato entonces vigente.

Una ruta basada en productos nativos oficiales sería un nuevo contrato experimental, no una reparación silenciosa ni una continuación de C0.

### 2.2 AAC-Core no se modifica

Se preservan las reglas de AAC:

- la equivalencia depende de la pregunta \(\mathcal Q\);
- el observador \(O\) y la representación \(g\) deben ser admisibles para esa pregunta;
- las equivalencias no se eligen después de observar la estructura deseada;
- estabilidad representacional no implica significado físico;
- debe declararse lo observado, definido, inferido y no identificable;
- una estructura puede ser discreta, continua, jerárquica, ambigua o inexistente.

Esta especificación refina la operacionalización de AAC en imágenes galácticas mediante una regla de proporcionalidad:

> **La fuerza de caracterización exigida al observador debe corresponder a las propiedades que la afirmación científica pretende preservar.**

No es necesario reconstruir cada detalle histórico del instrumento si ese detalle no puede alterar una propiedad relevante. Sí es necesario conocer o acotar todo mecanismo capaz de modificar la evidencia morfológica o producir una estructura alternativa plausible.

---

## 3. Pregunta científica protegida

La pregunta provisional que gobierna esta especificación es:

> **¿Existe estructura no supervisada, reproducible y científicamente interpretable en la morfología visual de galaxias que sobreviva a representaciones razonables y que no pueda explicarse principalmente por el proceso de observación o preprocessing?**

La palabra *estructura* no presupone clusters. Incluye:

- clases discretas;
- continuos y secuencias;
- manifolds;
- jerarquías;
- mixtures y regiones ambiguas;
- anomalías;
- ausencia de discretización robusta.

La unidad de análisis aún no queda congelada por este documento. El futuro contrato deberá decidir si corresponde a una galaxia catalogada, una observación por banda, un conjunto multibanda co-registrado u otra entidad explícita.

---

## 4. El instrumento completo

Para este proyecto, el observador no es solamente el telescopio o survey. La cadena relevante es:

\[
\text{galaxia}
\rightarrow O_{\rm survey}
\rightarrow O_{\rm producto}
\rightarrow O_{\rm cutout}
\rightarrow O_{\rm pre}
\rightarrow g_{\rm encoder}
\rightarrow \text{estructura candidata}.
\]

Donde:

- \(O_{\rm survey}\): óptica, detector, bandas, seeing, ruido y selección del survey;
- \(O_{\rm producto}\): calibración, coadd, astrometría, remuestreo y máscaras del producto científico;
- \(O_{\rm cutout}\): selección espacial y construcción del cutout a partir del producto científico, incluyendo bandas, coordenada de referencia, tamaño de recorte, cobertura y cualquier nuevo remuestreo;
- \(O_{\rm pre}\): background, normalización, enmascaramiento y transformaciones de entrada;
- \(g_{\rm encoder}\): extracción o aprendizaje de características y representación resultante.

En este documento, **construcción del cutout no significa extracción de características**. Consiste en seleccionar una región y construir los arrays observacionales que contienen la galaxia. Detectar o segmentar la galaxia, aislarla del fondo, rotarla, reescalarla, recentrar sus píxeles o normalizar intensidades pertenece a \(O_{\rm pre}\). Extraer descriptores, embeddings o componentes pertenece a \(g_{\rm encoder}\). Si la construcción del cutout exige remuestreo para formar una rejilla común, ese remuestreo continúa en \(O_{\rm cutout}\), pero debe auditarse como una transformación potencialmente morfológica.

Ninguna etapa posterior puede considerarse neutral por defecto. Un producto upstream perfectamente calibrado puede perder su valor si una operación propia destruye señal relevante. Del mismo modo, un encoder robusto no corrige una construcción de cutout de procedencia insuficiente.

---

## 5. Vocabulario normativo

Cada propiedad o transformación debe recibir una categoría antes de ejecutar el experimento que dependa de ella.

### 5.1 Información que debe preservarse (`PRESERVE`)

La información debe permanecer disponible en la representación primaria o en artefactos auxiliares enlazables por objeto. Puede existir una rama transformada, pero no puede destruirse la única copia auditable.

### 5.2 Invariancia deseada (`INVARIANT`)

La diferencia se considera irrelevante para la equivalencia provisional. Esto no autoriza a eliminarla con cualquier algoritmo. Debe demostrarse que la operación o representación reduce sensibilidad sin borrar otras propiedades relevantes.

### 5.3 Hipótesis experimental (`EXPERIMENTAL`)

No existe todavía derecho suficiente para conservarla como señal ni para comprimirla como nuisance. Deben compararse ramas preespecificadas y medir cuánto altera la estructura descubierta.

### 5.4 Transformación no admisible en la representación primaria (`PROHIBITED_PRIMARY`)

La operación elimina o mezcla información de manera incompatible con la pregunta amplia actual. Puede aparecer únicamente como baseline destructivo o prueba adversarial explícita, nunca como ruta canónica silenciosa.

### 5.5 Confusor auditable (`AUDIT_CONFOUNDER`)

La variable no se define como morfología, pero puede dominar la representación. Debe conservarse como metadata o medirse independientemente para evaluar explicaciones alternativas.

Una propiedad puede recibir más de una etiqueta. Por ejemplo, la PSF debe preservarse como metadata, tratarse como confusor y someterse a ramas experimentales.

---

## 6. Matriz provisional de preservación

Esta tabla es vinculante para el diseño de la siguiente propuesta, pero sus filas `EXPERIMENTAL` no quedan resueltas por declaración.

| Propiedad o transformación | Categoría provisional | Razón científica | Consecuencia para el diseño |
|---|---|---|---|
| Estructura espacial relativa dentro de cada banda | `PRESERVE` | Es parte central de la evidencia morfológica | No binarizar, colapsar ni suavizar de forma irreversible en la rama primaria |
| Registro espacial entre bandas | `PRESERVE` | Desalineaciones pueden crear o borrar estructura cromática | Verificar WCS/co-registro y propagar su incertidumbre |
| Identidad de banda (`g/r/z` u otras) | `PRESERVE` | El color espacial puede contener bulbo, brazos, polvo y formación estelar | Mantener canales separados; monocromo solo como baseline |
| Traslación limitada en el cuadro | `INVARIANT` + `EXPERIMENTAL` | La posición accidental del objeto no define su morfología, pero el recentrado puede introducir sesgo | Usar regla de centro congelada y probar perturbaciones de centrado |
| Rotación global en el plano de la imagen | `EXPERIMENTAL` con expectativa de invariancia | La orientación celeste absoluta suele ser incidental; canonizarla exige estimar un eje ambiguo | No alinear horizontalmente por defecto; evaluar augmentations y sensibilidad |
| Reflexión global | `EXPERIMENTAL` | Puede preservar forma gruesa, pero elimina handedness/chirality y puede ocultar asimetrías sistemáticas | No imponer invariancia hasta evaluar su costo informativo |
| Inclinación física / axis ratio proyectado | `PRESERVE` + `AUDIT_CONFOUNDER` | No equivale a una simple rotación 2D y altera la apariencia morfológica | No “desproyectar” por defecto; medir y analizar su influencia |
| Escala angular y pixel scale | `PRESERVE` + `AUDIT_CONFOUNDER` | Cambian detalle resoluble y tamaño aparente | Conservar WCS; comparar escala angular fija con alternativas preespecificadas |
| Escala física | `EXPERIMENTAL` | Requiere distancia/redshift y responde a otra noción de equivalencia | Rama separada; no sustituir silenciosamente la escala angular |
| Campo de visión y tamaño de recorte | `EXPERIMENTAL` | Puede truncar halos, colas, vecinos o contexto | Congelar varias escalas razonables antes del holdout y medir estabilidad |
| PSF/seeing | `PRESERVE` + `AUDIT_CONFOUNDER` + `EXPERIMENTAL` | Puede simular concentración o borrar barras/brazos | Conservar modelo/metadata; comparar original, degradación controlada y homogeneización |
| Ruido e inverse variance | `PRESERVE` + `AUDIT_CONFOUNDER` | La detectabilidad de estructura depende del ruido | Retener mapas de incertidumbre; no usar denoising opaco en la rama primaria |
| Background y su estimación | `PRESERVE` + `EXPERIMENTAL` | Un error de fondo afecta halos y bajo brillo superficial | Guardar estimación, residuo y regla; comparar variantes congeladas |
| Máscaras, saturación y píxeles inválidos | `PRESERVE` | Imputación silenciosa puede fabricar estructura | Conservar máscaras separadas; registrar toda imputación o exclusión |
| Contaminantes y fuentes vecinas | `EXPERIMENTAL` + `AUDIT_CONFOUNDER` | Pueden ser contaminación, ambiente relevante o señal de interacción | Comparar ramas con contexto y tratamiento explícito; no borrarlos sin registro |
| Brillo/calibración absoluta | `PRESERVE` + `AUDIT_CONFOUNDER` | Puede no definir forma, pero permite detectar estructura dominada por fotometría o selección | Utilizar productos con unidades trazables; una rama normalizada no elimina el dato original |
| Ganancia global positiva por objeto | `EXPERIMENTAL` con posible invariancia | Puede ser nuisance, pero su normalización borra brillo superficial global | Comparar representación fotométrica y normalizada; no declarar equivalencia por intuición |
| Offset aditivo global | `EXPERIMENTAL` | Puede representar background o error de calibración | Tratar mediante modelo de fondo explícito, no como invariancia automática |
| Contraste no lineal, `asinh`, clipping o histogram equalization | `PROHIBITED_PRIMARY` | Cambia relaciones de intensidad y detectabilidad espacial | Solo visualización o baseline documentado; nunca fuente primaria sin rama lineal |
| RGB → escala de grises | `PROHIBITED_PRIMARY` | Colapsa información multibanda | Permitido únicamente como baseline monocromático preespecificado |
| Binarización por threshold | `PROHIBITED_PRIMARY` | Impone frontera objeto/fondo y borra señal tenue | Solo prueba adversarial; no entrada canónica |
| Apertura/cierre morfológico | `PROHIBITED_PRIMARY` | Puede eliminar clumps, regiones HII, brazos o compañeros | Solo baseline destructivo con parámetros congelados |
| Rotación a eje mayor horizontal | `PROHIBITED_PRIMARY` por defecto | Introduce un estimador morfológico previo y falla en objetos ambiguos | Solo rama experimental con ambigüedad y error del eje registrados |
| Redshift | `AUDIT_CONFOUNDER` | Mezcla evolución, resolución, dimming y selección | Excluir del aprendizaje principal inicial, conservar para auditoría/holdout |
| Masa, SFR, color integrado, Sérsic, concentración y entorno | `AUDIT_CONFOUNDER` / validación externa | Ayudan a interpretar sin definir la representación no supervisada primaria | No usarlos para entrenamiento o selección salvo experimento declarado |
| Etiquetas Galaxy Zoo/Hubble | evaluación externa | No constituyen verdad ontológica y podrían filtrar la solución | Mantener en lockbox hasta las etapas preespecificadas de evaluación |

---

## 7. Niveles de exigencia del contrato observacional

El aprendizaje de C0 exige descomponer la antigua noción agregada de “semántica científica del cutout”.

### Nivel A — Semántica geométrica y espacial (`BLOCKING`)

Antes de entrenar debe verificarse, dentro de tolerancias congeladas:

- procedencia del producto científico;
- WCS y pixel scale;
- coordenada de referencia y regla de construcción del cutout;
- bandas y registro entre ellas;
- tamaño y cobertura del recorte;
- remuestreo introducido durante la construcción del cutout, si existe;
- píxeles inválidos, máscaras y límites de soporte;
- relación relevante entre PSF, resolución y muestreo.

Una incertidumbre capaz de deformar o inventar estructura espacial bloquea el experimento dependiente.

### Nivel B — Semántica fotométrica, ruido y selección (`REQUIRED_FOR_AUDIT`)

Debe existir evidencia suficiente para:

- interpretar unidades y calibración de las imágenes de origen;
- rastrear transformaciones de intensidad propias;
- conservar mapas de inverse variance o incertidumbre disponibles;
- estudiar brillo superficial, S/N, background y redshift como explicaciones alternativas;
- saber cuándo una normalización destruye fotometría absoluta.

No toda representación entregada al encoder debe preservar escala absoluta. Sin embargo, el proyecto sí debe preservar una ruta auditable hasta valores calibrados para poder distinguir morfología de selección o fotometría. La normalización no puede utilizarse para declarar irrelevante aquello que acaba de eliminar.

### Nivel C — Identidad operacional detallada (`CONDITIONAL`)

Commit, compilador, biblioteca o configuración exactos son bloqueantes solo si:

- modifican propiedades de Nivel A o B;
- impiden reproducir/acotar una transformación relevante;
- o dejan una explicación alternativa material para la estructura descubierta.

Una implementación públicamente plausible no equivale a la ruta desplegada. A la vez, AAC no exige identidad forense completa cuando la propiedad relevante puede verificarse independientemente.

---

## 8. Requisitos para una representación primaria conservadora

La próxima especificación de contrato deberá proponer una representación primaria que, como mínimo:

1. parta de productos científicos oficiales y versionados con semántica documentada;
2. realice la selección espacial y construcción del cutout mediante una ruta controlada, reproducible y registrada;
3. conserve por separado las bandas originales seleccionadas;
4. preserve arrays antes de normalización y toda metadata necesaria para reinterpretarlos;
5. conserve WCS, pixel scale, unidades, máscaras, incertidumbre y PSF disponibles;
6. use un centrado reproducible con incertidumbre o fallos explícitos;
7. evite binarización, morfología matemática, alineación por eje mayor y transformaciones no lineales en la ruta primaria;
8. diferencie píxel sin soporte, píxel inválido, píxel enmascarado y píxel válido de valor cero;
9. registre cada operación, parámetros, versión, hash y orden de ejecución;
10. permita regenerar exactamente la entrada del encoder desde los artefactos preservados.

La evidencia obtenida en C0 favorece investigar una ruta desde productos DR5 nativos oficiales. Esto no la aprueba todavía. El nuevo contrato debe demostrar que la construcción local del cutout satisface esta especificación antes de adoptar esa ruta.

---

## 9. Familia mínima de ramas experimentales

No se buscará un pipeline único después de ver qué variante produce clusters más atractivos. Antes de la evaluación confirmatoria se congelará una familia pequeña de representaciones con preguntas distintas.

| Rama provisional | Pregunta que responde | Restricción |
|---|---|---|
| Multibanda lineal conservadora | ¿Qué estructura aparece con la mayor información observacional admisible? | Ruta primaria; valores y metadata trazables |
| Monobanda `r` | ¿La estructura depende principalmente del color? | Misma geometría y muestreo que la primaria |
| Intensidad normalizada | ¿Sobrevive la estructura al comprimir escala fotométrica global? | Conservar entrada calibrada; fórmula congelada |
| PSF homogeneizada | ¿La variación de seeing domina la estructura? | Target PSF fijada sin mirar clusters; registrar pérdida de resolución |
| Resolución degradada | ¿Qué estructuras sobreviven a menor información espacial? | Degradación física y niveles preespecificados |
| Perturbación de centrado | ¿La asignación depende de errores plausibles de centro? | Distribución de desplazamientos congelada |
| Rotaciones controladas | ¿La representación es estable ante orientación global? | Sin canonización por eje; mismos ángulos para todos los modelos comparables |
| Escalas de recorte vecinas | ¿La estructura depende del campo de visión? | Tamaños congelados antes del holdout |
| Contexto/máscara de vecinos | ¿Vecinos e interacciones explican la estructura? | Ambas ramas conservadas; tratamiento explícito |

Esta lista es un mínimo conceptual, no una orden de ejecutar todas las ramas a cualquier costo. El diseño posterior deberá justificar cuáles son necesarias, estimar recursos y usar fases exploratorias separadas del holdout.

---

## 10. Pruebas de pérdida de información

Antes de considerar admisible una transformación, deberán definirse pruebas acordes con la propiedad que pretende preservar.

### 10.1 Pruebas directas

- reversibilidad cuando se afirme transformación sin pérdida;
- conservación de coordenadas y registro;
- propagación de máscaras y soporte;
- respuesta a fuentes sintéticas, perfiles, barras, brazos tenues, clumps y colas inyectadas;
- sensibilidad a background, ruido y PSF dentro de rangos observados;
- cuantificación de flux/forma cuando corresponda;
- inspección de fallos por objeto, no solo métricas agregadas.

Las inyecciones sintéticas verifican propiedades del pipeline, no realismo completo de las galaxias.

### 10.2 Pruebas de representación

Para una transformación \(T\) que se espera preserve equivalencia, evaluar al menos:

\[
d\bigl(g(x),g(Tx)\bigr)
\]

y el efecto de \(T\) sobre:

- vecinos en el embedding;
- posición en el manifold;
- pertenencia o probabilidad de cluster, si existen clusters;
- puntaje de anomalía;
- incertidumbre o inconsistencia entre representaciones.

La distancia pequeña no prueba por sí sola equivalencia física. La distancia grande ante una transformación declarada irrelevante cuenta contra la admisibilidad de la representación.

### 10.3 Controles discriminantes

Cada perturbación relevante debe compararse, cuando sea posible, con:

- una perturbación de magnitud comparable que debería ser irrelevante;
- una perturbación que deliberadamente destruya información morfológica;
- un baseline simple;
- más de un encoder o semilla.

Esto evita interpretar robustez general, saturación o colapso de la representación como invariancia científicamente selectiva.

---

## 11. Gates de preservación antes y durante el experimento

### MIP-0 — Contrato trazable

**Pregunta:** ¿la ruta desde producto científico hasta array previo al encoder posee suficiente procedencia y semántica para los Niveles A y B?

**PASS:** propiedades bloqueantes verificadas y propiedades de auditoría preservadas.  
**FAIL:** evidencia directa de transformación incompatible con la especificación.  
**INCONCLUSIVE:** evidencia insuficiente para distinguir una ruta admisible de una explicación alternativa material.  
**Efecto:** no se entrena un experimento dependiente tras `FAIL` o `INCONCLUSIVE` bloqueante.

### MIP-1 — Pérdida controlada

**Pregunta:** ¿cada operación de preprocessing tiene propósito, dominio, parámetros, información eliminada y pruebas congeladas?

**PASS:** no existe pérdida silenciosa y los tests preespecificados cumplen sus criterios.  
**FAIL:** una operación destruye información marcada `PRESERVE` o fabrica estructura.  
**REVISE:** una operación sustituible falla sin invalidar el contrato upstream.

### MIP-2 — Robustez a transformaciones de equivalencia

**Pregunta:** ¿la representación conserva estabilidad selectiva bajo transformaciones declaradas invariantes sin volverse insensible a cambios morfológicos relevantes?

No se acepta un umbral elegido a partir del holdout. Deben reportarse heterogeneidad por objeto, banda, S/N, tamaño, redshift y morfología aparente cuando estén disponibles.

### MIP-3 — Dependencia del preprocessing

**Pregunta:** ¿la estructura candidata persiste entre ramas razonables o es producto de una decisión particular?

Una estructura que cambia radicalmente entre preprocessings igualmente admisibles no queda validada como taxonomía robusta. Puede reinterpretarse como incertidumbre, familia de observadores o resultado negativo.

### MIP-4 — Dominio por confusores

**Pregunta:** ¿seeing, redshift, tamaño aparente, brillo superficial, background, cobertura, S/N, survey o artefactos explican la estructura mejor que una interpretación morfológica?

Las correlaciones no prueban causalidad, pero una dependencia fuerte y reproducible constituye una explicación alternativa que debe confrontarse antes de atribuir significado físico.

### MIP-5 — Evaluación externa sin fuga

**Pregunta:** ¿la estructura preserva información astronómica independiente y cómo se relaciona con etiquetas humanas no utilizadas para construirla?

Galaxy Zoo/Hubble y variables físicas se abren solo en la etapa preespecificada. Su concordancia ayuda a interpretar; su desacuerdo no es automáticamente error y su concordancia no demuestra ontología.

---

## 12. Criterios de fracaso y resultados válidos

Esta especificación debe detener o degradar una afirmación cuando:

- la geometría o soporte de la entrada no es identificable en el grado requerido;
- una transformación primaria destruye señal marcada `PRESERVE`;
- la estructura depende principalmente de una rama arbitraria de preprocessing;
- las asignaciones son inestables frente a perturbaciones que debían preservar equivalencia;
- la aparente robustez proviene de colapso o insensibilidad general del encoder;
- los confusores observacionales explican la estructura de forma suficiente;
- los criterios se modifican después de observar el holdout;
- solo se obtienen clusters atractivos sin ventaja sobre baselines ni evidencia de robustez;
- no puede decidirse entre representaciones razonables incompatibles.

Son resultados científicamente válidos:

- ausencia de clases discretas;
- estructura continua o jerárquica;
- regiones de ambigüedad;
- anomalías definidas por inestabilidad;
- dependencia demostrada del observador;
- imposibilidad de sostener una equivalencia propuesta;
- `INCONCLUSIVE` por límite de identificabilidad predeclarado.

---

## 13. Artefactos obligatorios para la siguiente fase

Antes de implementar una nueva ruta deberán producirse y congelarse:

1. `OBSERVATIONAL_CONTRACT_REVISION.md` — fuente, productos, selección espacial/construcción del cutout, unidad observacional, licencia y trazabilidad;
2. `PREPROCESSING_BRANCH_SPEC.md` — operaciones exactas, orden, parámetros, pérdidas y ramas;
3. `MIP_GATE_PROTOCOL.md` — tests, métricas, tolerancias, seeds, holdout y decisiones;
4. inventario de metadata y mapas auxiliares por objeto;
5. registro de confusores permitidos para auditoría y variables encerradas en lockbox;
6. presupuesto de red, CPU, RAM, disco y tiempo;
7. comandos determinísticos para todo proceso pesado que deba ejecutar el operador humano;
8. criterios explícitos de `PASS`, `REVISE`, `FAIL`, `INCONCLUSIVE` y `STOP`.

Ningún proceso pesado deberá ejecutarse automáticamente si puede entregarse como CLI reproducible al operador. Un sentinel técnico solo certificará terminación e integridad del trabajo, nunca aprobación científica del Gate.

---

## 14. Decisiones abiertas que esta versión no resuelve

Estas decisiones deben resolverse en la revisión del contrato, no durante la ejecución:

1. unidad observacional exacta;
2. survey y release definitivos;
3. construcción local del cutout desde productos nativos frente a otro mecanismo oficialmente documentado;
4. bandas incluidas y tratamiento de datos faltantes;
5. escala angular fija, física fija o diseño multiescala;
6. tamaño o familia de tamaños de recorte;
7. definición y estimador de centro;
8. política de vecinos, estrellas y fuentes contaminantes;
9. tratamiento de PSF y target de homogeneización, si se usa;
10. normalización de intensidad y definición de background;
11. invariancia a rotación y reflexión;
12. tolerancias científicas para cada Gate;
13. composición del holdout y reglas de lockbox;
14. criterio para concluir que el preprocessing domina el resultado.

No resolver estas preguntas todavía no constituye una falla. Ocultarlas dentro del código sí lo sería.

---

## 15. Regla de congelamiento y control de cambios

La versión 0.1 fue aceptada explícitamente por José Salinas el 2026-09-18 y queda congelada. Desde este momento:

- no podrá modificarse para hacer pasar una ruta observacional concreta;
- cualquier cambio deberá registrar motivo, evidencia nueva, impacto y versión;
- C0 seguirá siendo un resultado histórico inalterado;
- una revisión podrá cambiar la pregunta o equivalencia futura, pero deberá declararse como nuevo experimento;
- los resultados exploratorios no podrán utilizarse para fijar retroactivamente tolerancias confirmatorias.

Toda excepción deberá responder:

1. ¿qué afirmación científica exige el cambio?;
2. ¿qué información se gana o pierde?;
3. ¿qué explicación alternativa introduce?;
4. ¿qué Gate detectará si la excepción fue perjudicial?;

---

## 16. Criterio de éxito de esta especificación

Esta especificación habrá cumplido su función si permite diseñar un instrumento donde:

- sepamos qué información observacional entra al encoder;
- sepamos qué información fue eliminada y por qué;
- ninguna invariancia relevante se imponga de forma silenciosa;
- una estructura candidata pueda desafiarse mediante observadores razonables;
- los confusores permanezcan auditables aunque no formen parte del aprendizaje;
- y el proyecto pueda concluir honestamente que una clasificación no se ha ganado.

No habrá cumplido su función si se convierte en una lista ceremonial, si exige trazabilidad irrelevante sin relación con \(\mathcal Q\), o si se utiliza para legitimar después de los hechos el pipeline que produzca el resultado más atractivo.

---

## 17. Procedencia interna

Esta versión deriva de:

- `analisis_arquitectura_continuidad.md`, especialmente su disciplina epistemológica, Gate III, protocolo operativo y aplicación a clasificación no supervisada;
- `C0_GATE_LEDGER.md`;
- `C0_FINAL_REPORT.md`;
- `C0_BOUNDED_AUDIT_REPORT.md`;
- `C0_NORMAL_CUTOUT_CHARACTERIZATION.md`;
- la discusión metodológica posterior al cierre de C0 sobre instrumento, equivalencia y preprocessing;
- el antecedente aportado por José Salinas de un pipeline clásico de visión —grayscale, threshold, apertura, intersección, centrado y alineación— utilizado aquí como contraste conceptual, no como propuesta para galaxias.

La contribución nueva de esta especificación es hacer explícito que existen dos instrumentos encadenados —el producto observacional y nuestro preprocessing— y que la trazabilidad exigible a cada uno debe derivarse de la información que la pregunta científica necesita preservar.

---

## 18. Estado de decisión

**Decisión:** v0.1 aceptada y congelada el 2026-09-18.  
**No autoriza:** reapertura de C0, adquisición, materialización de cohorte, SDSS, entrenamiento, selección de modelo ni evaluación con etiquetas humanas.  
**Sí autoriza:** diseñar, sin ejecutar, `OBSERVATIONAL_CONTRACT_REVISION.md` bajo esta autoridad.  
**Siguiente fase:** revisión explícita del contrato observacional y comparación previa de rutas candidatas.
