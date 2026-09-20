# OC-3 — especificación prospectiva del piloto acotado de auxiliares y píxeles

**Stage de desarrollo:** `BOUNDED_AUXILIARY_AND_PIXEL_PILOT`
**Naturaleza:** especificación solamente; cero red, cero selección de ubicaciones y cero inspección de imágenes.
**Estado al congelar:** los dos bricks `INSTRUMENTAL_DEVELOPMENT` están fijados; las seis ubicaciones y todos los productos coadd permanecen sin adquirir.

## 1. Autoridad, binding de entrada y precedencia

Esta especificación implementa el siguiente tramo del diseño ya fijado por `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` y sus Amendments 001/002. No modifica la pareja de bricks, el propósito observacional, el selector técnico congelado, los caps globales ni los cuatro desenlaces científicos OC-3.

El input row-level exclusivo es:

`oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv`

Debe verificarse byte a byte con SHA-256:

`147c0942a5340ed18eec23a610f8afd5721390fad09c1da7ed01593deb40fab6`

Su procedencia obligatoria es `OC3-TECHNICAL-SELECTION-001`, terminal `TECHNICAL_PILOT_COHORT_MATERIALIZED`. Contiene exactamente un brick south/DECaLS 9012 y uno north/BASS-MzLS 9011. Sus identidades no se reproducen en esta especificación. No se vuelve a ejecutar la selección de bricks ni se permite reemplazarlos.

Esta especificación tiene precedencia limitada sobre la anterior sólo para:

1. exigir soporte geométrico completo de 129×129 para los seis outputs de ubicación;
2. exigir seis ubicaciones distintas para emitir `LOCATION_SELECTION_VALIDATED`;
3. separar formalmente ese terminal de la adquisición posterior `BOUNDED_NATIVE_PRODUCTS_ACQUIRED`; y
4. cerrar el manifiesto mínimo y la auditoría de estas dos etapas.

Las ventanas parciales o virtuales de la especificación anterior pueden seguir usándose más tarde como diagnósticos de borde, pero no son outputs elegibles de esta selección de seis ubicaciones.

## 2. Pregunta, unidad y alcance negativo

La pregunta es si los productos nativos DR9 permiten caracterizar en un piloto acotado señal de imagen, inverse variance/ruido diagonal disponible, cobertura de exposiciones, máscaras/calidad y PSF/seeing, manteniendo visibles sus limitaciones observacionales.

La unidad de selección es un **centro entero de píxel del coadd nativo**, identificado por:

```text
(region, brickname, native_x, native_y)
```

`native_x` y `native_y` son enteros 0-based. La coordenada celeste es un valor derivado por el WCS del producto nativo con convención origin=0; se conserva como procedencia, nunca como ranking. La ventana exacta es:

```text
[native_x-64, native_x+65) × [native_y-64, native_y+65)
```

con shape 129×129 y centro en `[64,64]` del crop. No hay rescaling, nuevo remuestreo, padding, recentrado, rotación, normalización, segmentación, imputación, mosaico ni homogenización PSF.

S1–S3/N1–N3 son ubicaciones observacionales técnicas. No son galaxias, sujetos morfológicos, ejemplos de entrenamiento ni miembros de una población científica. No se abre Galaxy Zoo, Zoobot, Tractor, catálogos de fuentes, variables físicas, espectroscopia, imágenes renderizadas, holdout o lockbox para construirlas.

## 3. Suficiencia del estado local

Los datos locales actuales **no son suficientes para seleccionar las seis ubicaciones**.

Las tablas ya validadas contienen geometría de brick y resúmenes `nexp_g/r/z` usados para elegir la pareja. Esos valores son medianas sobre `BRICK_PRIMARY`; no sustituyen mapas NEXP por píxel. El stage no posee mapas nativos NEXP, MASKBITS o PSFSIZE de los dos bricks. Tampoco posee un manifiesto final sellado con las 26 identidades coadd, tamaños, HDU lógicos y hashes aplicables.

Por tanto, el próximo flujo requiere primero resolver y adquirir de forma autorizada los 14 auxiliares nativos de los dos bricks. No se puede ejecutar una selección offline honesta desde la metadata actual.

## 4. Información permitida para elegir ubicaciones

El selector acepta exclusivamente el CSV congelado, geometría/WCS técnica y este bundle por brick:

```text
nexp:    mapas nativos por banda g/r/z
psfsize: mapas nativos por banda g/r/z
maskbits: un mapa óptico entero compartido
```

`image` e `invvar` no son argumentos, dependencias ni fuentes indirectas de la selección. La validación previa puede observar headers técnicos necesarios para identidad, HDU, shape, dtype, unidades, compresión y WCS; no puede observar intensidades de image.

| Cantidad | Banda | Papel vinculante |
|---|---|---|
| shape, WCS, límites del array y bounds `BRICK_PRIMARY` | por producto; comparados en conjunto | gates de identidad, grid y geometría |
| NEXP | g/r/z por píxel | requisito de bundle; criterio estratificado sólo para N2 |
| MASKBITS óptico raw | sin banda | requisito de bundle; criterio de presencia de flags sólo para S3 |
| PSFSIZE | g/r/z por píxel, arcsec | requisito de bundle; validez y ranking de variación sólo para N3 |
| región, generación y brick | por recurso | gates de procedencia; nunca ranking de ubicación |

No se usa el valor mediano regional `nexp_g/r/z`, `nexphist`, `psfsize_g/r/z` del resumen, profundidad, seeing catalogal, número/tipo de fuentes, color, magnitud, masa, SFR, Sérsic, concentración, ambiente, redshift o apariencia.

## 5. Gates comunes de producto y geometría

Antes de construir candidatos deben pasar todos estos gates:

1. Los dos bricks y generaciones coinciden exactamente con el CSV y la evidencia de `OC3-TECHNICAL-SELECTION-001`.
2. Cada recurso tiene URL literal, release DR9, región, generación, producto, banda, tamaño/cota, HDU lógico y evidencia sellados antes del request.
3. Cada auxiliar decodifica como array 2D nativo; MASKBITS tiene dtype entero no negativo; NEXP conserva enteros no negativos; PSFSIZE conserva su dtype y unidades documentadas.
4. Los siete auxiliares de un brick comparten shape y WCS. La composición de grids debe respetar la tolerancia congelada de bookkeeping, máximo `1e-6` píxel; no se realinea para pasar.
5. El WCS soportado es la geometría TAN local ya congelada, sin descartar silenciosamente distorsiones o tablas anexas. Layout no soportado falla cerrado.
6. Para cada candidato, `64 <= native_x <= NAXIS1-65` y `64 <= native_y <= NAXIS2-65`. La ventana obtenida debe ser idéntica a la solicitada, sin padding ni píxeles sintetizados.
7. La relación con `BRICK_PRIMARY` se calcula desde WCS y bounds publicados, incluido wrap RA. El bit NPRIMARY no reemplaza esa geometría.

Una discrepancia de identidad, schema, HDU, shape, WCS, dtype o unidades falla el stage completo. No se convierte en exclusión conveniente de una ubicación.

## 6. Política MASKBITS prospectiva

No se exige `MASKBITS=0`. El piloto caracteriza variación del observador y debe conservar el entero completo.

### A. Inutilizable como input técnico

Ningún bit DR9 individual convierte por sí solo todo un centro en inutilizable para este selector. Son fallos del stage, no filtros por ubicación:

- producto que no sea el plano óptico MASKBITS;
- HDU o diccionario de release no verificable;
- dtype no entero, valores negativos, shape/grid incompatible;
- bits cuya procedencia se haya reinterpretado con semántica de otra release.

La saturación de alguna exposición no implica automáticamente que el coadd sea inutilizable, y GALAXY no es un flag fatal ni una clase morfológica.

### B. Variación observacional retenida

- Bits 1–7 y 10–13: se preservan y su presencia en una ventana completa define el estrato S3. S3 no maximiza cantidad, área ni tipo de flags.
- Bit 0/NPRIMARY: se preserva como contraste, pero no selecciona ni sustituye el límite geométrico `BRICK_PRIMARY`.
- Bits 8–9/WISE: se preservan, pero no participan en el predicado óptico S3.
- Valor cero: significa ausencia de flags registrados en ese mapa; no certifica un píxel limpio o válido.

### C. Semántica no resuelta

Bits fuera del diccionario DR9 congelado se registran como `unknown_bits` y nunca se convierten en false. La incompletitud documentada de GALAXY, bleed trails y otros issues permanece riesgo observacional. Ausencia de un bit no permite declarar ausencia del fenómeno. Ninguna de estas incertidumbres autoriza reemplazar una ubicación.

## 7. Cobertura NEXP y PSFSIZE

Los tres mapas NEXP g/r/z son obligatorios y deben ser compatibles con el grid. NEXP cuenta exposiciones contribuyentes por píxel del coadd; no se sustituye por NOBS de Tractor ni por la mediana regional.

El gate brick-level `grz=true` ya demostró `nexp_g>=1`, `nexp_r>=1` y `nexp_z>=1` bajo `GRZ_MEDIAN_PRESENT_V1`; aquí se exige además que los tres mapas por píxel sean válidos. Éste es el soporte g/r/z congelado. No se inventa después una fracción mínima positiva por ventana.

No existe un gate universal `NEXP>=k` para todos los píxeles de todos los slots. Imponerlo eliminaría precisamente el estrato de soporte N2. NEXP sólo influye en N2 mediante la regla congelada de §9. En los demás slots se conserva y audita después, sin ranking por máximo NEXP.

Los tres mapas PSFSIZE g/r/z también son obligatorios y describen FWHM promedio ponderado en arcsec; no son un kernel PSF. PSFSIZE sólo influye en N3. No se minimiza seeing ni se elige la PSF “mejor”. Los modelos coadd-PSF son productos posteriores, no inputs de selección.

## 8. Retícula y canonicalización determinista

Para un array de shape `(NAXIS2,NAXIS1)`, crear por eje:

```text
X = sorted(unique({0,64,128,... < NAXIS1} ∪ {NAXIS1-1}))
Y = sorted(unique({0,64,128,... < NAXIS2} ∪ {NAXIS2-1}))
```

Recorrer conceptualmente el producto cartesiano; el orden de lectura no decide el resultado. Aplicar primero los gates comunes y excluir centros ya elegidos en el mismo brick.

Para cada slot y candidato calcular exactamente:

```text
SHA256(UTF-8("OC3-v1|<slot>|<region>|<brickname>|<x>|<y>"))
```

`slot` es uno de `S1,S2,S3,N1,N2,N3`; región `south` o `north`; `x,y` son enteros decimales sin padding, espacios, signo positivo, BOM ni LF. El digest se representa en hex minúsculo. El desempate final es `(y,x)` entero ascendente.

No se usa RNG, seed, orden de filas proveedor ni selección manual.

## 9. Estrategia B: variación observacional deliberada

Se adopta la opción **B**, ya congelada por OC-3: seis tests técnicos complementarios, no tres réplicas equivalentes. Interior, frontera geométrica, flags, transición de soporte y variación PSF son condiciones del observador que deben hacerse visibles antes de morfología.

Los slots se resuelven en orden fijo `S1,S2,S3,N1,N2,N3`, sin reposición:

| Slot | Regla exacta después de gates comunes | Orden |
|---|---|---|
| S1 | ventana completa dentro de `BRICK_PRIMARY` y cada píxel/centro a ≥64 píxeles de su límite | `(hash,y,x)` ascendente |
| S2 | la ventana completa intersecta ambos lados del límite `BRICK_PRIMARY` dentro del mismo coadd | `(distancia_del_centro_al_límite,hash,y,x)` ascendente |
| S3 | ventana completa con al menos un bit 1–7 o 10–13 no nulo | `(hash,y,x)` ascendente |
| N1 | misma regla de interior que S1 | `(hash,y,x)` ascendente |
| N2 | clase 0 si alguna banda contiene NEXP=0 y NEXP>0; si no existe, clase 1 si alguna banda contiene NEXP=1 | `(clase,hash,y,x)` ascendente |
| N3 | ventana completa y PSFSIZE positivo/finito en todos sus píxeles y bandas | `(-V,hash,y,x)` ascendente |

Para N3:

```text
V = max(
  max_b((max(P_b)-min(P_b))/median(P_b)),
  max_b(median(P_b))/min_b(median(P_b))-1
)
```

Si el máximo `V < 0.10`, se conserva esa ubicación con `status=STRATUM_NOT_EXERCISED`. No se cambia el umbral, el brick o el ranking.

Si cualquier slot carece de candidato, si dos slots terminan en el mismo centro o si no pueden materializarse tres ubicaciones por brick, no se emite el terminal de éxito. Se preservan conteos agregados y se falla cerrado; no existe séptimo lugar, otro brick o sustitución por apariencia.

## 10. Manifiesto cerrado de seis ubicaciones

Único artifact row-level de esta selección:

`oc3/TECHNICAL_INDEX/OC3_LOCATIONS.json`

Top-level exacto:

```text
binding,locations,selection_sha256
```

`binding` es el binding inmutable del plan autorizado. `selection_sha256` es SHA-256 del JSON canónico de `locations`, con claves ordenadas, separadores compactos, UTF-8, `ensure_ascii=false`, `allow_nan=false` y sin LF dentro del hash.

`locations` contiene exactamente seis objetos, en orden S1,S2,S3,N1,N2,N3. Schema exacto de cada objeto:

```text
slot,region,brick,x,y,ra_dec,window,selection_hash,status,V
```

Reglas:

- `brick` debe ser el brick congelado de esa región;
- `x,y` son los centros 0-based;
- `ra_dec=[ra_deg,dec_deg]` deriva del WCS sin afectar selección;
- `window` contiene exactamente `requested`, `obtained`, `integer_offset`, `offset_in_requested`, `padding`, `resampling`;
- para esta etapa `requested==obtained`, `offset_in_requested=[0,0]`, `padding=false`, `resampling=false`;
- `selection_hash` sigue §8;
- `status` es `SELECTED` o, sólo para N3, `STRATUM_NOT_EXERCISED`;
- `V` es null salvo N3, donde es float64 finito serializado por el canonicalizador fijado.

No contiene image, invvar, NEXP arrays, MASKBITS arrays, PSFSIZE arrays, fuentes, objetos astronómicos ni propiedades físicas.

## 11. Evidencia agregada separada

La implementación futura debe producir, sin identidades adicionales de filas:

1. `OC3_SELECTION_FLOW.csv`: una fila por slot con conteo de retícula, gates geométricos, candidatos del estrato, centros ya usados, seleccionado 0/1 y estado del estrato.
2. `OC3_LOCATION_SELECTION_AGGREGATE.json`: hashes de inputs/arrays, counts de exclusión, histogramas técnicos agregados de NEXP y MASKBITS, PSFSIZE min/max/mediana y máximo V por banda/slot, selected count y leakage count. No incluye listas de candidatos ni coordenadas no seleccionadas.
3. `OC3_RESOURCE_PLAN.json`: recursos exactos, orden, métodos, caps, hashes/evidencia, ledger y saldo acumulado.
4. `OC3_RESOURCE_SUMMARY.json`: reservas/consumo de bytes, requests, retries, disco, I/O, CPU y wall por stage y global.
5. log y terminal de cada stage, compactos y sin apariencia/morfología.

RAW_IMMUTABLE, TECHNICAL_INDEX y CONFOUND_AUDIT permanecen separados. Los mapas completos/caches van en RAW_IMMUTABLE; ubicaciones en TECHNICAL_INDEX; estados y diagnósticos posteriores en CONFOUND_AUDIT.

## 12. Productos nativos requeridos

### 12.1 Para seleccionar ubicaciones

Por brick:

- `nexp-g`, `nexp-r`, `nexp-z`;
- `psfsize-g`, `psfsize-r`, `psfsize-z`;
- un `maskbits` óptico.

Total exacto: **14 recursos auxiliares nativos** para dos bricks.

### 12.2 Después de sellar ubicaciones

Por brick y banda: `image` e `invvar`, total **12 recursos nativos**. Junto con auxiliares, el inventario máximo es **26 mapas coadd**.

Por ubicación/banda se extraen slices directos 129×129 de `image`, `invvar`, `nexp` y `psfsize`; MASKBITS se extrae una vez por ubicación y se comparte entre bandas. Cada crop conserva dtype decodificado, header/WCS traducido por offset entero y procedencia del recurso. No se modifica la intensidad usando máscara o peso.

WCS y procedencia técnica se conservan desde headers completos. Pueden añadirse hasta dos tablas CCD de procedencia si su identidad, schema y necesidad quedan sellados sin columnas de fuentes. No son sustitutos de un mapa.

Después del sello de ubicaciones puede materializarse `OC3_PSF_LINKS.json`: centro, `(-32,-32)` y `(+32,+32)` respecto del centro, para cada banda y slot, hasta **54 respuestas coadd-PSF**. Cada punto/banda aparece exactamente una vez como recurso o `NOT_AVAILABLE`; nunca se mueve el punto. PSFSIZE no sustituye esa PSF y la PSF no participa retroactivamente en selección.

## 13. Contrato proveedor actualmente demostrable

La familia de directorio documentada es:

```text
https://portal.nersc.gov/cfs/cosmo/data/legacysurvey/dr9/<region>/coadd/<AAA>/<brick>/
```

Las autoridades locales documentan patrones relativos para `image`, `invvar`, `nexp`, `psfsize` y `maskbits`, grilla TAN 3600×3600 y escala nominal 0.262 arcsec/píxel. Sólo MASKBITS está documentalmente ligado al plano óptico lógico HDU 1.

El estado local **no fija todavía** de forma auditable:

- filenames/sufijos concretos por producto y banda;
- la regla exacta de `<AAA>` como identidad autorizada de producción;
- HDU lógico de image/invvar/nexp/psfsize;
- HDU físico frente a imagen lógica comprimida;
- tamaños, ETag/checksum proveedor y headers de los 26 mapas;
- URL/parametrización y vínculo independiente del servicio coadd-PSF;
- identidades de tablas CCD opcionales.

No se completan esos campos por memoria, intuición o sustitución. Antes de cualquier GET, un contrato de recursos prospectivo separado debe fijar cada URL literal, producto, banda, HDU, región/generación, cota y evidencia. Una discrepancia de header/HDU durante adquisición produce STOP/revisión; no incorpora un layout nuevo automáticamente.

## 14. Plan de red futuro y contabilidad

Esta especificación realiza cero solicitudes. El plan futuro conserva los caps globales:

| Dimensión | Cap global acumulado |
|---|---:|
| cuerpos HTTP | 1,610,612,736 bytes |
| solicitudes | 200 |
| reintentos | 2 adicionales por identidad exacta |
| concurrencia | 1 |
| PSF | 54 MiB; 1 MiB por punto/banda |
| RAM / threads / GPU | 2 GiB / 1 / 0 |
| disco incremental | 4 GiB |
| I/O local | 8 GiB |
| CPU activo / wall por invocación | 1800 s / 3600 s |

El bootstrap real ya consumió 89,461,646 bytes y 8 solicitudes. Antes de nuevas operaciones quedan como máximo **1,521,151,090 bytes** y **192 solicitudes**; ninguna reanudación reinicia estos contadores. El ledger futuro debe importar o ligar de forma inmutable ese consumo antes de reservar.

Orden prospectivo, siempre con `Accept-Encoding: identity`, TLS, timeout 30 s, sin redirects:

1. validar offline autoridades, CSV, derechos locales, contrato de recursos, ledger y plan completo;
2. HEAD de los 14 auxiliares, sólo si tamaño/identidad no están ya fijados;
3. si todos los auxiliares y la reserva completa posterior caben, GET de los 14 en orden south/north; dentro de cada región `nexp g,r,z`, `psfsize g,r,z`, `maskbits`;
4. validar auxiliares y seleccionar/sellar ubicaciones offline, sin image;
5. HEAD/GET de los 12 image/invvar en el mismo orden de región y banda;
6. resolver y sellar PSF contra las ubicaciones; luego hasta 54 GET; tablas CCD opcionales sólo si estaban previamente enumeradas;
7. extracción y verificación offline; cero red para corregir resultados inconvenientes.

Con HEAD para todos los 26 mapas, GET para ellos, hasta dos tablas con HEAD+GET y 54 GET PSF, el plan primario máximo adicional es **110 solicitudes sin retries**. Los retries compiten por el saldo global restante; nunca elevan 200. Requests fallidos, cuerpos de error y bytes parciales cuentan.

La suma de `max_bytes` de recursos pendientes, cuerpos de error y reserva PSF debe ser ≤1,521,151,090 antes del primer request. Reservar 54 MiB PSF deja como máximo 1,464,527,986 bytes para mapas, procedencia y errores. La estimación histórica de 26 arrays 3600²×4 bytes es ~1.26 GiB sin compresión y no certifica tamaños FITS. Si HEAD/tamaños sellados no demuestran cabida, no se inicia GET y no se amplía el presupuesto.

Range es opcional y no se presume válido para DR9 por la evidencia DR5/C0. Sólo puede usarse tras demostrar en el producto DR9 exacto 206/Content-Range, identidad estable, layout soportado y equivalencia con lectura del mismo archivo oficial. Un servidor que devuelve 200 a Range no autoriza aceptar un cuerpo completo fuera del plan.

## 15. Separación adquisición → selección → extracción

La cadena metodológica es:

```text
contrato y plan de recursos
→ adquisición inmutable de auxiliares
→ validación nativa de producto
→ selección técnica y sello de seis ubicaciones
→ adquisición inmutable de image/invvar/PSF
→ extracción directa 129×129
→ auditoría observacional posterior
→ preprocessing futuro, todavía no definido
```

El crop es extracción observacional. No es feature extraction, segmentación, recentrado, resize, augmentación, normalización o preparación de entrenamiento.

## 16. Terminales y anti-cherry-picking

Terminal de selección exitoso:

`LOCATION_SELECTION_VALIDATED`

Significa únicamente: seis centros distintos, tres por brick, reproducibles desde auxiliares validados y materializados en `OC3_LOCATIONS.json`. No significa que el estrato N3 alcanzó V≥0.10, que los píxeles son limpios, que exista una galaxia o que la morfología esté preservada.

Terminal posterior de adquisición exitosa:

`BOUNDED_NATIVE_PRODUCTS_ACQUIRED`

Exige los 26 recursos nativos requeridos completos/verificados o una estrategia de fragmentos previamente validada, headers/WCS/procedencia y el estado explícito de las 54 identidades PSF. No certifica todavía los crops: la extracción exacta y su verificación son el paso offline siguiente. No implica resultado A/B, contrato observacional, MIP PASS ni inicio de aprendizaje.

Fallo de selección, recurso ausente, PSF inconveniente, contaminación, imagen vacía, pixels “feos”, ausencia de galaxia o contenido científicamente aburrido no permiten mover ubicaciones o cambiar bricks. Una modificación exige enmienda prospectiva y nuevo stage ID; los artifacts originales se preservan.

## 17. Plan de implementación y siguiente etapa ejecutable

La implementación se divide sin conflar terminales:

1. **RESOURCE_CONTRACT_AND_AUXILIARY_ACQUISITION:** resolver offline el contrato exacto de los 14 auxiliares y los 12 productos fijos, implementar manifiesto/ledger/reanudación y preparar autorización humana. La adquisición bulk será ejecución humana obligatoria.
2. **OFFLINE_LOCATION_SELECTION:** validar los 14 auxiliares, aplicar §§5–10, publicar sólo el manifiesto y evidencia agregada, y emitir `LOCATION_SELECTION_VALIDATED` o fallo cerrado.
3. **FIXED_NATIVE_PRODUCT_ACQUISITION:** ligar PSF a la selección, adquirir image/invvar/PSF sin cambiar centros y emitir `BOUNDED_NATIVE_PRODUCTS_ACQUIRED` o fallo cerrado.
4. **OFFLINE_NATIVE_EXTRACTION:** extraer y verificar crops 129×129 desde los recursos fijados, sin red ni modificación de ubicaciones; pertenece a la auditoría observacional posterior.

El próximo trabajo ejecutable es **implementar y validar sintéticamente `RESOURCE_CONTRACT_AND_AUXILIARY_ACQUISITION`**. No se autoriza aún su red: primero debe cerrar filenames/HDU/URLs mediante evidencia prospectiva, demostrar límites, no-fuga y resume, producir `--help`/`--dry-run`, documentar comando/coste/log/sentinels y quedar comprometido. Sólo entonces se prepara un handoff humano concreto.

## 18. Cierre de esta especificación

En esta tarea no se selecciona ninguna ubicación, no se abre ningún mapa, no se resuelve una URL por intuición, no se descarga un byte y no se inicia análisis morfológico. La pareja de bricks y su exclusión confirmatoria permanecen inmutables.

**OC-3 MORPHOLOGICAL SCIENTIFIC PHASE REMAINS NOT STARTED.**
