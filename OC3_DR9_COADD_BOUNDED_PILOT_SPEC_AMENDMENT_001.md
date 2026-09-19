# OC-3 — enmienda prospectiva 001

**Fecha:** 2026-09-18.  
**Estado:** corrección de diseño autorizada; sin implementación ni adquisición.  
**OC-3 permanece NOT STARTED. No existe resultado OC-3.**

## 1. Autoridad, integridad y precedencia limitada

Se leyeron y verificaron las tres autoridades antes de redactar esta enmienda. Los SHA-256 observados coinciden exactamente con los esperados:

| Archivo congelado | SHA-256 verificado |
|---|---|
| MORPHOLOGICAL_INFORMATION_PRESERVATION_SPEC.md | `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24` |
| OBSERVATIONAL_CANDIDATE_TRIAGE_OC2.md | `9cbdc77943188717b1c92cf3fef64eaf03c968ce28e115df4171065e25362b93` |
| OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |

La autoridad de esta corrección es la instrucción prospectiva del usuario. No se reescribe ninguno de esos archivos. La enmienda prevalece sobre la especificación OC-3 únicamente en estos puntos:

1. Sustituye la parte inferencial de T10 (§7, remisión a §9; control de permutación, familia de Holm y lenguaje inferencial de §9) por §§3–5 de esta enmienda. Preserva íntegros los cálculos descriptivos originales.
2. Añade la interpretación vinculante de las guardas PSF de §§8 y 10 mediante §6 de esta enmienda, sin cambiar números, mediciones o condiciones de dominio.
3. Acota la interpretación de los dos bricks y del desenlace A de §§3 y 10 mediante §7 de esta enmienda, sin cambiar criterios ni nombres terminales.

Todo lo demás continúa vigente. C0 permanece CLOSED con STOP; E-OC1 permanece CLOSED con `NO_CURRENTLY_ADMISSIBLE_ROUTE_WITH_AVAILABLE_EVIDENCE`; OC-2 conserva `ONE_CANDIDATE_ADVANCES_TO_BOUNDED_PIXEL_PILOT`. Esta enmienda no es reapertura, contrato observacional, aprobación MIP ni autorización de ejecución.

## 2. Defecto corregido: resolución estadística

El diseño original prescribe 199 permutaciones y `p=(1+k)/200`, por lo que el mínimo alcanzable es 0,005. Para una familia de m pruebas, el primer umbral de Holm es 0,05/m. Cuando m>10 ese umbral es menor que el mínimo alcanzable y el procedimiento no puede rechazar siquiera la primera hipótesis, independientemente de la magnitud observada. La combinación bloque×lag×slot×banda puede producir muchas más de diez pruebas.

Esto es un **DESIGN BUG**, identificado algebraicamente antes de implementar. No es una no-detección observada, ni evidencia de independencia, ni fallo experimental de DR9. La corrección reduce la familia inferencial y mejora su resolución, sin prometer potencia suficiente para cualquier dependencia.

## 3. T10: descriptores preservados y un único omnibus

### 3.1 Conservar todos los registros originales

Por slot, banda, bloque, lag y estrato de estado/flags se conservan conteo de pares, medias muestrales de ambos extremos, varianzas, covarianza, correlación de Pearson y estado/motivo de estimabilidad. Se preservan los descriptores de todos los píxeles finitos y de los pares con NEXP>0 e IVAR>0, así como el desglose por flags. No se eliminan, reemplazan ni promedian esas filas para guardar solo el omnibus.

Permanecen los 16 bloques originales 32×32 del área 128×128, sin reemplazar bloques incompletos, y los diez lags originales, en este orden:

`(1,0), (0,1), (1,1), (1,-1), (2,0), (0,2), (4,0), (0,4), (8,0), (0,8)`.

Permanece la regla original: menos de 128 pares o varianza nula implica correlación no estimable; un resultado no finito tampoco es una correlación válida. No hay nuevo recorte, normalización, selección de cielo o sustracción de fondo.

### 3.2 Estadístico congelado

Hay **exactamente un omnibus por slot×banda**, como máximo seis slots por tres bandas = 18 pruebas. No se crean omnibus adicionales por estado, flag, bloque o lag.

Para eliminar ambigüedad entre las series descriptivas originales, la serie inferencial `r_jl` es la correlación T10 del conjunto de **todos los pares con ambos valores image finitos** del bloque j y lag l. Los subconjuntos de soporte/peso y flags permanecen descriptivos, sin significancia propia. Esto no declara limpios los píxeles de la serie inferencial. La permutación condicionará por sus clases de estado (§4).

Para cada bloque con al menos un lag estimable:

\[
R_j=\max_{\ell\ \mathrm{estimable}}|r_{j\ell}|.
\]

Para cada slot×banda:

\[
T=\operatorname{median}_{j\ \mathrm{estimable}} R_j.
\]

La mediana de un número par de valores es el promedio de los dos centrales. Un bloque sin lags estimables no aporta R_j y se conserva como no estimable, no como cero. Con menos de cuatro bloques estimables, el omnibus de esa unidad es **NOT_AUDITABLE**, con p crudo y ajustado no disponibles. No sustituir bloques, slots ni bandas.

Se reportan siempre, descriptivamente y sin pruebas adicionales:

- todos los `r_jl` y todos los R_j disponibles;
- T, máximo de R_j e IQR de R_j;
- cantidad e identidad de bloques/lags estimables y faltantes;
- heterogeneidad entre bloques, conteos de pares y desgloses originales de estado/flags.

IQR = Q0.75−Q0.25, con cuantiles por interpolación lineal sobre posición `(n−1)q` en los R_j ordenados. Con datos insuficientes se preservan los descriptores calculables sin conferirles un p-value. No se cambia la definición max-lag/median-block indicada por el usuario: no se encontró contradicción matemática en ella.

## 4. Nulo de permutación y reproducibilidad

### 4.1 Subflujos deterministas

Se utilizan **999 permutaciones por slot×banda estimable**, PCG64 y seed maestra **301**. Regla exacta hash-to-seed, de especificación solamente:

1. Formar la cadena ASCII/UTF-8 `OC3-v1|<slot>|<band>`, sin espacios, BOM ni salto final. Slot usa exactamente S1, S2, S3, N1, N2 o N3; banda exactamente g, r o z.
2. Calcular SHA-256 de esos bytes. Dividir los 32 bytes del digest en ocho palabras consecutivas de cuatro bytes, interpretadas como enteros unsigned de 32 bits big-endian.
3. Inicializar una SeedSequence con `entropy=301` y `spawn_key` igual a esas ocho palabras en orden; usarla para inicializar PCG64 (no PCG64DXSM).
4. Cada unidad usa su propio subflujo pseudoaleatorio; no consume el estado de otra unidad. El orden de ejecución o una reanudación no cambia su secuencia. Esta separación por hash no es una demostración matemática de independencia entre generadores.

Fijar y registrar la versión de la biblioteca de RNG/permutación en el entorno futuro. Dentro de cada unidad: permutaciones 1…999, bloques en orden fila y luego columna, clases ordenadas canónicamente, coordenadas dentro de clase en orden `(y,x)`. Reanudación debe reproducir el mismo estado o regenerar la misma secuencia desde esa clave; nunca sortear otra seed.

### 4.2 Qué se permuta y qué permanece fijo

En cada permutación se parte de los valores originales, no del resultado de la permutación previa. Se permutan solo valores finitos dentro del **mismo bloque original y la misma clase de estado del píxel**; se conservan las coordenadas, soporte, mapas auxiliares, número de píxeles de cada clase y posiciones no finitas/ausentes.

La clase se determina una vez a partir de los ejes originales de OC-3 §6: presencia, finitud, condición de cero, finitud/signo del peso, valor NEXP, entero MASKBITS óptico, flags conocidos/desconocidos, pertenencia geométrica, evidencia de soporte/calidad y estado de validez. Se mantiene UNKNOWN distinto de false. No incluir amplitud continua de image o de IVAR como clave adicional ni agrupar clases después de observar correlaciones. Orden canónico = representación JSON del vector de esos campos en ese orden, UTF-8, sin espacios; escalares enteros/booleanos y etiquetas textuales, nulidad explícita. Clases de un solo miembro permanecen sin intercambio. Si la partición deja poca libertad, se informa esa limitación; no se fusionan clases para obtener significancia.

En cada permutación se recalculan los Pearson originales y su estimabilidad, los R_j y el mismo T. Se conserva el número de bloques/lags estimables por permutación. Si una permutación no permite construir T con al menos cuatro bloques, la unidad queda NOT_AUDITABLE para inferencia: no se descarta ese sorteo para reducir el denominador, no se sustituye por otro y no se inventa una correlación cero. Los descriptores observados se mantienen. Una distribución degenerada pero definida no se reintenta; se reporta como limitación de sensibilidad.

El nulo es la intercambiabilidad condicional de valores dentro de bloque y clase fija. El control no transforma una mezcla de señal astronómica, gradientes, ruido y pesos variables en ruido puro. Las permutaciones no se guardan como observaciones científicas preprocesadas ni se entregan a un encoder.

### 4.3 p-value y Holm

Con T observado y las 999 realizaciones definidas:

\[
p=\frac{1+\#\{T_{\mathrm{perm}}\geq T_{\mathrm{observado}}\}}{1000}.
\]

Se incluyen los empates, el denominador es 1000 y **p_min=0,001**. No detener permutaciones temprano por el p provisional.

Holm se aplica con α=0,05 **solo a los omnibus slot×banda auditables**, m≤18. Reportar m, las unidades incluidas y cada exclusión por no auditabilidad; ninguna inclusión se elige por significancia o magnitud de T. Las unidades no auditables conservan p=null, no p=1 presentado como medición. No hay corrección o claim inferencial por bloque, lag, estado o flag.

Ordenar p crudos crecientes, con desempate por orden S1,S2,S3,N1,N2,N3 y g,r,z. Para el rango i, de 1 a m:

\[
p^{\mathrm{Holm}}_{(i)}=
\min\left(1,\max_{1\leq k\leq i}\{(m-k+1)p_{(k)}\}\right).
\]

Reportar p crudo, p ajustado y rango. Detección omnibus si p ajustado≤0,05. Con m=0 no se aplica Holm ni se fabrica detección/no-detección. Con m=18 el primer umbral es 0,05/18≈0,002778, mayor que 0,001: ya no hay imposibilidad de rechazo por la granularidad anterior. Eso no demuestra potencia, validez del nulo en cada campo ni detección futura.

## 5. Interpretación: tamaño de efecto antes que decisión binaria

El propósito de T10 sigue siendo auditabilidad observacional, no una afirmación poblacional. El informe preservará toda la dependencia por lag, T, máximo e IQR de R_j, heterogeneidad, conteos y estado/flags. El p-value no sustituye esa evidencia ni define un nuevo umbral de aprobación de OC-3.

Lenguaje permitido para la unidad:

- «dependencia espacial empírica detectada a la sensibilidad de este piloto»;
- «no detectada a la sensibilidad de este piloto»;
- «no auditable».

No se permite concluir «los píxeles vecinos son independientes», «la covarianza es cero», «Lanczos causó la correlación» ni «se reconstruyó la covarianza completa». Una detección no identifica causa física; una no-detección no establece independencia. Si la intercambiabilidad o la separación señal/cielo/ruido no permite el claim requerido, se registra el límite de auditabilidad conforme a OC-3, no se cambia el nulo o los datos.

El aumento a 999 permutaciones no aumenta ningún presupuesto. Una implementación futura deberá satisfacer los límites de tiempo, RAM, IO y demás recursos ya congelados. Si no puede completar la inferencia prescrita, no vuelve a 199 ni reduce selectivamente unidades/lags: aplica las reglas existentes de cierre por insuficiencia/límites. No se ejecuta benchmark en esta enmienda.

Los nuevos resultados inferenciales se incorporarán a los artefactos ya previstos —OC3_CORRELATION.csv y ledger/informe— diferenciando registros descriptivos y omnibus; sin crear aquí tablas, código o un nuevo inventario de archivos de ejecución. El futuro registro de autoridades deberá vincular también el hash de esta enmienda para impedir la ejecución inadvertida del T10 supersedido.

## 6. Guardas PSF: interpretación vinculante

Se mantienen sin alteración:

- variación PSFSIZE≤10%;
- FWHM mínima≥2 píxeles nativos;
- masa absoluta del borde del stamp PSF≤1%.

Son **PILOT ENGINEERING GUARDS ONLY**. Pasarlas no demuestra preservación de barras, brazos, colas de marea, halos, asimetrías ni ningún otro rasgo morfológico. Pueden delimitar un subdominio instrumental candidato; no pueden convertirse en umbrales finales de preservación morfológica de un contrato sin justificación independiente en una etapa MIP posterior y congelada.

Fallar una guarda puede restringir el dominio instrumental según las reglas ya existentes. Pasarlas no constituye MIP-0 ni MIP-1 PASS, ni valida por sí solo la fidelidad del modelo PSF. No se modifican sus estimadores, T07–T09 o la selección de slots.

## 7. Dos bricks: generalización no demostrada

OC-3 utiliza como máximo un brick norte y uno sur para caracterización técnica adversarial. Ningún desenlace, incluido `DR9_COADD_SUPPORTS_OBSERVATIONAL_CONTRACT_DRAFT`, demuestra representatividad de toda la huella DR9, distribución de condiciones observacionales, población de fuentes o conjunto de regímenes de procesamiento.

El desenlace A significa únicamente que la arquitectura de productos y la semántica **ensayadas** fueron suficientemente coherentes para justificar redactar un contrato observacional candidato. Sus requisitos de generalización permanecerán explícitamente UNRESOLVED y deberán probarse prospectivamente antes de materializar una cohorte. El desenlace B mantiene un alcance todavía más estrecho. Esta aclaración no selecciona nuevos campos, no añade bricks ni autoriza una campaña de generalización.

## 8. Elementos inalterados y cierre de esta entrega

Se mantienen exactamente los cuatro desenlaces terminales OC-3:

- A — `DR9_COADD_SUPPORTS_OBSERVATIONAL_CONTRACT_DRAFT`.
- B — `DR9_COADD_REQUIRES_NARROWER_SCIENTIFIC_DOMAIN`.
- C — `DR9_COADD_NOT_CURRENTLY_ADMISSIBLE`.
- D — `PILOT_INTEGRITY_FAILURE_STOP`.

No se elige ninguno ahora: no hay ejecución ni resultado OC-3. Sus condiciones originales siguen vigentes, con la corrección inferencial y los límites interpretativos explícitos anteriores. No cambia selección de slots, cantidad de bricks, productos, presupuestos, prohibiciones de preprocessing, no-fuga ni delegación humana. No se añade un desenlace PENDING.

Esta entrega crea exclusivamente `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md`. No crea implementación, scripts, tests, snapshots ni datos. No se realizan solicitudes de red ni adquisición astronómica. Los archivos congelados permanecen intactos. **OC-3 remains NOT STARTED.**
