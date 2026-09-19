# OC-3 — enmienda prospectiva 003: boundary de esquema proveedor DR9

**Fecha:** 2026-09-18  
**Estado:** especificación prospectiva; no implementada y no ejecutada.  
**Preflight:** `PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS`.  
**OC-3 REMAINS NOT STARTED.**

## 1. Autoridad e integridad

Antes de redactar esta enmienda se verificaron localmente los bindings mínimos exigidos:

| Autoridad o evidencia | SHA-256 verificado |
|---|---|
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md` | `7fc040829847e26e6231c95b18d5debcd3785db0198915b1f93a5b45859f38bd` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_001.md` | `2f87cec954167bc51ab442d1dbd803bae622bb5411a2b88642fecde8d920cd66` |
| `OC3_DR9_COADD_BOUNDED_PILOT_SPEC_AMENDMENT_002.md` | `4f6d921204645a0289c6f3c4ce4e5818419ade97d42b8b1d8def7cd2e6d723fe` |
| `OC3_AMENDMENT_002_IMPLEMENTATION_REPORT.md` | `8ca240b5855c5196a78b8cfa2a1860a179b1d1f360a3f4aa95893f74f16da0f0` |
| `OC3_PREFLIGHT_ENVIRONMENT_VERIFICATION.md` | `ae131bbfe69efaae983cc353518c1a8cafde97893cb935fc8ec86a7079b71ded` |
| `OC3_DR9_BOOTSTRAP_DOCUMENTARY_EVIDENCE.md` | `07f2e20994d52783a84a176113b3f8cdf3d3ba4a0f0e0cf4fc33868e5277769b` |
| `OC3_DR9_PROVIDER_SCHEMA_CONTRACT.md` | `d02815a66f27df67e60f0cb1dc4d38a977e70c492417d3397946911159bf31c9` |

También se verificaron:

- agregado de implementación actual: `37d85f4ed38c0ff9fa91061eebf330c4d35065a69c249e721a8027593b4d27d4`;
- fingerprint ambiental: `b49e26767922123113707a13434821d6bf1d7711f28a2b9de7e5ce46d64e3bdf`;
- SHA-256 de `oc3/environment_setup/PREPARATION_RECEIPT.json`: `0bce87d275ca71f6d6bef39f597fb354a3c1813c150830b395a1628d3b638654`.

No se encontró una discrepancia. De haber existido, esta enmienda no se habría creado y el resultado habría sido `AMENDMENT_003_AUTHORITY_INTEGRITY_FAILURE`.

El SHA-256 de esta enmienda se calcula sobre sus bytes finales y se informa fuera del documento para evitar una autorreferencia imposible.

## 2. Alcance exclusivo

Amendment 003 define prospectivamente solo:

1. validación del esquema del proveedor;
2. clasificación de campos permitidos, conocidos pero prohibidos y desconocidos;
3. construcción del DTO técnico candidato;
4. predicado técnico de disponibilidad g/r/z;
5. procedencia de generación north/south;
6. conducta ante discrepancias entre documentación y layout FITS observado;
7. interfaz y prerrequisitos del futuro adaptador de la lista 9012.

No cambia la pregunta científica OC-3, el diseño de seis slots, el límite de dos bricks, T01–T12, las estadísticas T10 de Amendment 001, las guardas de ingeniería PSF, los límites de recursos, el orden determinista por hash, la promoción padre→hijo, la exclusión permanente de bricks de desarrollo ni la interpretación científica terminal.

Esta enmienda no autoriza red, adquisición, manifiesto de producción, ledger, selección real ni comienzo de OC-3.

## 3. Separación obligatoria de operaciones

La validación del esquema proveedor y la proyección técnica son operaciones distintas y causalmente ordenadas:

```text
VALIDACIÓN DE ESQUEMA PROVEEDOR
  ≠
PROYECCIÓN TÉCNICA PARA SELECCIÓN
```

La primera examina metadata estructural de todas las columnas contra un contrato exacto. La segunda construye una vista nueva usando exclusivamente valores permitidos. Reconocer una columna durante la primera operación no autoriza materializar sus celdas durante la segunda.

## 4. Clases del esquema proveedor

Se congelan exactamente tres clases:

| Clase | Regla normativa |
|---|---|
| `TECHNICAL_ALLOWED` | Sus valores pueden entrar únicamente en las transformaciones técnicas fijadas por esta enmienda. |
| `KNOWN_BUT_FORBIDDEN` | Se puede inspeccionar su metadata estructural para validar el esquema, pero sus valores de celda no se leen, copian, materializan, serializan, registran ni exponen al pipeline de selección. |
| `UNKNOWN_PROVIDER_FIELD` | Causa fallo cerrado antes de iterar filas y antes de selección. |

No existe una cuarta clase implícita, una categoría “ignorada” ni aceptación de campos extra. Un campo conocido con dtype, shape u otra semántica binaria incompatible también causa fallo cerrado.

## 5. Esquema lógico root `survey-bricks.fits.gz`

Se congela el siguiente inventario documental. Todos sus campos son `TECHNICAL_ALLOWED`:

| Campo | Tipo lógico documentado |
|---|---|
| `BRICKNAME` | `char[8]` |
| `BRICKID` | `int32` |
| `BRICKQ` | `int16` |
| `BRICKROW` | `int32` |
| `BRICKCOL` | `int32` |
| `RA` | `float64` |
| `DEC` | `float64` |
| `RA1` | `float64` |
| `RA2` | `float64` |
| `DEC1` | `float64` |
| `DEC2` | `float64` |

La tabla root establece identidad y geometría de la retícula. No establece cobertura DR9, pertenencia a la lista 9012 ni idoneidad morfológica.

La lista anterior congela tipos lógicos documentales. No decide HDU, TFORM, endian, scaling, null sentinels, unidades ni reglas de padding/decodificación de strings.

## 6. Inventario documental regional exhaustivo

Para Amendment 003, el siguiente es el inventario documental completo prospectivamente reconocido. Ningún otro campo regional está permitido.

### 6.1 `TECHNICAL_ALLOWED`

| Campo | Tipo lógico documentado | Uso máximo permitido |
|---|---|---|
| `brickname` | `char[8]` | identidad y join exacto |
| `ra` | `float64` | auditoría geométrica |
| `dec` | `float64` | auditoría geométrica |
| `nexp_g` | `int16` | `GRZ_MEDIAN_PRESENT_V1` |
| `nexp_r` | `int16` | `GRZ_MEDIAN_PRESENT_V1` |
| `nexp_z` | `int16` | `GRZ_MEDIAN_PRESENT_V1` |
| `nexphist_g` | `int32[6]` | validación de esquema y auditoría posterior |
| `nexphist_r` | `int32[6]` | validación de esquema y auditoría posterior |
| `nexphist_z` | `int32[6]` | validación de esquema y auditoría posterior |
| `brickid` | `int16` `DOCUMENTED_TYPE` | identidad técnica sujeta al conflicto de §8 |
| `ra1` | `float32` | auditoría geométrica |
| `ra2` | `float32` | auditoría geométrica |
| `dec1` | `float32` | auditoría geométrica |
| `dec2` | `float32` | auditoría geométrica |
| `area` | `float32` | auditoría técnica; nunca ranking |
| `survey_primary` | `boolean` | DTO/auditoría; no ranking ni conveniencia |

### 6.2 `KNOWN_BUT_FORBIDDEN`

| Campo | Tipo lógico documentado |
|---|---|
| `nobjs` | `int16` |
| `npsf` | `int16` |
| `nsimp` | `int16` |
| `nrex` | `int16` |
| `nexp` | `int16` |
| `ndev` | `int16` |
| `ncomp` | `int16` |
| `nser` | `int16` |
| `ndup` | `int16` |
| `psfsize_g` | `float32` |
| `psfsize_r` | `float32` |
| `psfsize_z` | `float32` |
| `psfdepth_g` | `float32` |
| `psfdepth_r` | `float32` |
| `psfdepth_z` | `float32` |
| `galdepth_g` | `float32` |
| `galdepth_r` | `float32` |
| `galdepth_z` | `float32` |
| `ebv` | `float32` |
| `trans_g` | `float32` |
| `trans_r` | `float32` |
| `trans_z` | `float32` |
| `cosky_g` | `float32` |
| `cosky_r` | `float32` |
| `cosky_z` | `float32` |
| `ext_g` | `float32` |
| `ext_r` | `float32` |
| `ext_z` | `float32` |
| `wise_nobs` | `int16[4]` |
| `trans_wise` | `float32[4]` |
| `ext_w1` | `float32` |
| `ext_w2` | `float32` |
| `ext_w3` | `float32` |
| `ext_w4` | `float32` |
| `in_desi` | `boolean` |

Los campos prohibidos no pueden influir en elegibilidad, desempate, orden, selección, sustitución, logs de selección o decisiones de conveniencia. Su presencia con el layout exacto futuro no invalida por sí sola el archivo proveedor.

### 6.3 `UNKNOWN_PROVIDER_FIELD`

Cualquier nombre regional que no figure en §§6.1–6.2 pertenece a `UNKNOWN_PROVIDER_FIELD` y detiene el adaptador antes de iterar filas. La implementación no puede proyectarlo silenciosamente, aceptarlo por prefijo, normalizarlo a un nombre conocido ni agregarlo automáticamente al contrato después de observarlo.

El inventario lógico es exhaustivo para esta enmienda. El contrato binario físico continúa pendiente según §15.

## 7. Identificadores estables de campos

La futura configuración no podrá nombrar columnas fuente mediante strings libres. Cada campo del proveedor tendrá un identificador estable definido por el contrato versionado, ligado a:

- rol proveedor;
- nombre exacto;
- clase;
- tipo lógico;
- contrato FITS físico cuando exista;
- transformación técnica autorizada, si corresponde.

Un mapping de manifiesto solo podrá referirse a esos IDs enumerados. El adaptador resuelve internamente ID→columna después de validar el contrato. No se permite que el manifiesto convierta, por ejemplo, `nobjs` en `grz` mediante un target aparentemente permitido.

## 8. Inconsistencia documental de `brickid`

Se congela explícitamente:

```text
ROOT DOCUMENTATION:
BRICKID = int32

REGIONAL DOCUMENTATION:
brickid = int16

OTHER DR9 DOCUMENTATION:
brick IDs can occupy the range [1, 662174]
```

Un entero signed `int16` no representa el rango completo documentado. La clasificación es:

**DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY**

Amendment 003 no decide si el tipo real es `int16`, `int32` u otro layout. No se permite cast, truncation, reinterpretation, wraparound ni normalización silenciosa.

El adaptador futuro comparará el esquema FITS observado con un contrato binario revisado prospectivamente. Si el layout observado contradice la expectativa documental congelada aplicable, se detiene con:

**PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP**

Los bytes observados no modifican automáticamente esta enmienda. Una corrección documental prospectiva posterior puede resolver el conflicto sin cambiar los criterios científicos de selección.

Mientras no exista esa resolución, `brickid` puede ejercitarse solo con fixtures sintéticos explícitamente tipados; no puede promoverse un DTO candidato de producción.

## 9. Predicado técnico g/r/z

Se congela el predicado:

**GRZ_MEDIAN_PRESENT_V1**

Para una fila regional:

```text
grz =
    finite_integer(nexp_g) AND nexp_g >= 1
AND finite_integer(nexp_r) AND nexp_r >= 1
AND finite_integer(nexp_z) AND nexp_z >= 1
```

`finite_integer(x)` exige un valor escalar entero, finito y no nulo ya validado contra el tipo físico autorizado. Un null, máscara, NaN, valor no escalar, valor no entero o scaling inesperado causa fallo cerrado; no se convierte a cero ni a false. Un entero válido menor que 1 produce `grz=false`.

Los valores `nexp_*` no pueden utilizarse más allá de este booleano. Su magnitud por encima de 1 no influye en orden, desempate, ranking, sustitución o conveniencia.

`nexphist_g/r/z` no participa en elegibilidad ni orden. Permanece `TECHNICAL_ALLOWED` exclusivamente para validar el esquema y para una auditoría técnica posterior separada.

Interpretación exacta: `GRZ_MEDIAN_PRESENT_V1` significa únicamente que la mediana documentada del número de exposiciones contribuyentes es al menos uno en g, r y z. No significa cobertura de todos los píxeles, solapamiento de las tres bandas en todos los píxeles, alta profundidad, buen seeing, uniformidad ni idoneidad morfológica.

El soporte local se comprobará posteriormente con los mapas nativos `nexp` autorizados en las seis ubicaciones del piloto. Esta enmienda no los adquiere. El threshold no puede cambiar después de observar valores DR9.

## 10. Constantes de procedencia y generaciones

La identidad inmutable del recurso proveedor, no una columna científica, suministra:

| Rama | `region` | `survey` | `release_family` |
|---|---|---|---|
| south | `south` | `DECaLS` | `DR9` |
| north | `north` | `BASS_MzLS` | `DR9` |

### North

Para todo candidato north admisible se congela `generation="9011"`. La representación canónica del DTO es string ASCII para coincidir con el contrato de ejecución existente; no se acepta coerción desde un valor arbitrario.

North rechaza cualquier candidato cuya generación derivada no sea 9011. Nunca consulta la lista 9012 y siempre lleva `corrected_9012=false`.

### South

South obtiene `generation="9012"` y `corrected_9012=true` únicamente si existe pertenencia exacta y no ambigua en la lista oficial congelada de patches.

Un brick south no miembro no es elegible. Si no puede establecerse membership, se bloquea. OC-3 no lo sustituye por una reducción 9010. Si un candidato ya seleccionado falla posteriormente, tampoco se selecciona otro brick por conveniencia.

## 11. Lista oficial de patches 9012

Se congela esta identidad documental:

`https://www.legacysurvey.org/files/dr9-south-patched-bricks.fits`

Propósito: lista oficial asociada a los 1.691 bricks south reprocesados como `RELEASE=9012`.

El estado del parser permanece:

**PATCH_LIST_ADAPTER_DISABLED**

Permanecen sin resolver:

- checksum del proveedor;
- HDU y layout FITS;
- inventario exacto de columnas;
- clave y tipo exactos de membership;
- cardinalidad observada de filas;
- semántica de null/scaling.

No se supone `BRICKNAME` ni se diseña un parser alrededor de un esquema inventado.

### Interfaz futura mínima

Una enmienda posterior podrá habilitar un adaptador de patch list solamente si este produce una relación de membership:

- derivada de bytes completos verificados;
- ligada a rol, URL final, checksum proveedor/local y contrato binario exacto;
- con clave de identidad explícitamente documentada;
- sin nulls, aliases, duplicados ni coerciones;
- con cardinalidad observada registrada;
- capaz de distinguir exactamente `member`, `nonmember` y conflicto/integridad.

Esta interfaz no prescribe el nombre de la columna ni su mapping interno.

## 12. Boundary `ProviderSchemaAdapter`

El orden causal obligatorio es:

```text
verified immutable resource
→ exact role identity
→ checksum verification
→ FITS structural/schema validation
→ classification of every provider column
→ TECHNICAL_ALLOWED-only view
→ frozen technical transforms/constants
→ candidate DTO
→ deterministic eligibility
→ deterministic SHA-256 brick ordering
```

El selector nunca recibe la tabla proveedor cruda. El boundary no expone un accessor para celdas `KNOWN_BUT_FORBIDDEN`. Ninguna configuración puede suministrar un source column libre.

La validación debe completarse antes de la primera iteración de filas. Solo después se abre una vista column-selective con campos `TECHNICAL_ALLOWED`. Si la librería disponible no puede impedir la materialización de arrays prohibidos, la implementación falla cerrado y requiere otro mecanismo revisado; no carga la tabla completa para descartarlos después.

## 13. Regla de no observación de valores prohibidos

Para columnas `KNOWN_BUT_FORBIDDEN` puede inspeccionarse únicamente metadata de esquema:

- nombre;
- TFORM/dtype;
- shape;
- TUNIT, TNULL, TSCAL y TZERO cuando sean pertinentes.

Sus celdas no se materializan en memoria por el adaptador de selección. La implementación debe preferir lectura FITS selectiva de columnas `TECHNICAL_ALLOWED` después de validar la metadata estructural.

Los arrays o valores prohibidos no pueden aparecer en:

- DTOs candidatos;
- objetos técnicos de cobertura;
- logs o excepciones de selección;
- índices técnicos usados para ordenar;
- CSV de desarrollo;
- manifiesto final;
- registro de promoción.

Los fallos de esquema usan códigos generales y hashes de contrato. No imprimen nombres desconocidos ni valores prohibidos en logs destinados al pipeline de selección.

## 14. DTO candidato y objeto técnico de auditoría

Se define el DTO inmutable versionado:

**OC3_TECHNICAL_CANDIDATE_V1**

| Campo | Tipo/valor permitido | Fuente |
|---|---|---|
| `region` | enum `south|north` | identidad del recurso |
| `survey` | enum `DECaLS|BASS_MzLS` | identidad del recurso |
| `release_family` | literal `DR9` | identidad del recurso |
| `generation` | string `9012` south o `9011` north | procedencia/membership congelados |
| `brickname` | identidad ASCII exacta bajo contrato binario | join root/regional |
| `brickid` | entero exacto, sin cast | root/regional después de resolver §8 |
| `ra` | float técnico validado | geometría root, con auditoría regional |
| `dec` | float técnico validado | geometría root, con auditoría regional |
| `primary_bounds` | objeto inmutable `{ra1,ra2,dec1,dec2}` | geometría root, con auditoría regional |
| `grz` | boolean | `GRZ_MEDIAN_PRESENT_V1` |
| `corrected_9012` | boolean | false north; membership exacta south |
| `survey_primary` | boolean técnico | resumen regional |
| `evidence_refs` | secuencia no vacía, estable y ordenada de referencias inmutables | recursos/contratos/checksums |

El DTO no contiene `nexp_*`, `nexphist_*` ni campos prohibidos. `survey_primary` se conserva para auditoría técnica, pero Amendment 003 no lo convierte en ranking ni quality-shopping.

Si se necesita trazabilidad de cobertura, se crea un objeto separado `OC3_GRZ_TECHNICAL_AUDIT_V1` con los seis campos `nexp_*`/`nexphist_*`, hash del contrato y resultado booleano. Ese objeto no entra en la función de orden; solo `grz` pasa al DTO.

La serialización canónica y el esquema exacto del DTO deberán implementarse y probarse prospectivamente. No se genera ningún DTO real en esta tarea.

## 15. Contrato binario FITS

Los tipos lógicos documentales no fijan por sí solos:

- HDU;
- TFORM exacto;
- representación endian;
- TSCAL/TZERO;
- TNULL o masked values;
- TUNIT;
- padding/encoding de strings;
- orden físico de columnas;
- cardinalidad de filas.

Estos son hechos observacionales del layout proveedor. Deben verificarse antes de decodificar filas. No se infiere `HDU=1` por tratarse de una binary table.

La futura implementación puede soportar contratos binarios exactos, versionados y ligados por hash a un rol proveedor. Hasta que cada contrato tenga evidencia prospectivamente revisada, la ruta de producción falla cerrado.

Una diferencia de nombre, tipo, shape, HDU, scaling, null semantics o unidad normativa produce `PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP`. No se parchea el contrato en runtime ni se prueba una HDU alternativa.

## 16. Joins exactos

Los joins root↔regional y, una vez habilitado, regional↔patch list son uno-a-uno por identidad de brick documentada.

Se rechazan:

- identidades duplicadas;
- identidad root ausente;
- desacuerdo exacto de brickname entre root y regional;
- conflicto de identidad geométrica;
- membership ambiguo;
- múltiples matches en patch list;
- aliases obtenidos mediante normalización de case;
- trim/padding no definido por el contrato binario;
- coerción numérica implícita;
- fuzzy matching.

`primary_bounds`, `ra` y `dec` del DTO provienen de la geometría root. Los valores regionales se usan para auditoría de identidad, no para sobrescribir root. No se introduce tolerancia numérica en esta enmienda: si las precisiones documentales distintas requieren una regla de comparación, esa regla debe fijarse prospectivamente después de resolver el contrato binario y antes de observar candidatos. Hasta entonces una comparación no resoluble bloquea el join.

## 17. Elegibilidad y orden

Después de crear DTOs válidos:

- north elegible: `region=north`, `survey=BASS_MzLS`, `release_family=DR9`, `generation=9011`, `grz=true`, `corrected_9012=false`;
- south elegible: `region=south`, `survey=DECaLS`, `release_family=DR9`, `generation=9012`, `grz=true`, `corrected_9012=true` por membership exacta.

No se añaden criterios de profundidad, seeing, PSF, fuente, extinción, cielo, footprint DESI, histograma o apariencia.

El orden permanece exactamente SHA-256 UTF-8 de `OC3-v1|brick|<region>|<brickname>` ascendente, con brickname ASCII como desempate. `nexp` por encima de 1, `nexphist`, `brickid`, coordenadas y `survey_primary` no modifican el orden.

## 18. Comportamiento ante discrepancias

La secuencia fail-closed es:

1. identidad/checksum inválidos: detener antes de abrir FITS;
2. contrato binario ausente: detener antes de decodificar filas;
3. HDU/layout diferente: `PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP`;
4. campo desconocido: detener antes de iterar filas;
5. campo conocido con tipo/shape/semántica incompatible: `PROVIDER_SCHEMA_DOCUMENTATION_CONFLICT_STOP`;
6. valor permitido inválido o join ambiguo: detener sin selección;
7. patch list no habilitada: `PATCH_LIST_ADAPTER_DISABLED`, sin candidatos south promovibles.

Una discrepancia no autoriza casts, aliases, fallback a otra release, DR9sv, 9010, otra tabla o un parser heurístico. Los bytes y recibos se conservan para revisión, pero no cambian la especificación.

## 19. Requisitos sintéticos prospectivos

La implementación futura deberá añadir, sin red real, al menos estos tests:

1. esquema regional proveedor completo válido;
2. campos prohibidos presentes pero inaccesibles;
3. source prohibido no puede mapearse a target permitido;
4. columna desconocida falla antes de iterar filas;
5. ausencia de columna permitida falla;
6. dtype incorrecto falla;
7. shape vectorial incorrecto falla;
8. HDU incorrecta falla;
9. TSCAL/TZERO/TNULL inesperados fallan cuando el contrato los restringe;
10. valores prohibidos nunca aparecen en logs, errores o DTOs;
11. `GRZ_MEDIAN_PRESENT_V1` es true para 1/1/1;
12. es false cuando cualquiera de las tres bandas vale cero, cubriendo cada banda;
13. nexp inválido, null o no entero falla cerrado;
14. magnitudes nexp superiores a 1 no cambian el orden;
15. cambios en `nexphist` no cambian elegibilidad ni orden;
16. north deriva 9011 y rechaza cualquier otra generación;
17. north nunca consulta patch list;
18. south requiere membership 9012 exacta;
19. south no miembro no recibe reemplazo;
20. joins duplicados, ausentes o conflictivos fallan;
21. permutar filas preserva conjunto candidato y hashes de selección;
22. variar arbitrariamente valores prohibidos no cambia ningún artefacto candidato/selección;
23. la inconsistencia documental `brickid` produce el stop explícito bajo fixture observado conflictivo;
24. el parser patch list permanece deshabilitado sin esquema congelado;
25. la regresión completa existente conserva 142 tests sin cambios en sus resultados.

También deben probarse la ausencia de accesores a valores prohibidos, lectura column-selective, IDs estables de campos, serialización canónica de DTO/auditoría y que el selector jamás acepte la tabla cruda.

No se modifican golden values de Amendment 001.

## 20. Implementación prospectiva y revisión

La siguiente tarea autorizada podrá implementar y verificar sintéticamente este boundary. Esa implementación deberá:

1. modificar prospectivamente el schema bootstrap para referenciar contrato/field IDs versionados;
2. insertar `ProviderSchemaAdapter` antes del DTO;
3. separar schema metadata de lectura de celdas;
4. construir `OC3_TECHNICAL_CANDIDATE_V1` y, si se necesita, `OC3_GRZ_TECHNICAL_AUDIT_V1`;
5. imponer 9011 north y mantener deshabilitada la patch list;
6. añadir todos los tests de §19 y ejecutar la regresión completa en el entorno independiente;
7. producir un nuevo agregado de implementación y replay/fingerprint aplicable antes de cualquier red.

Implementar el adapter no autoriza el bootstrap y no resuelve el contrato binario de archivos reales.

## 21. Precedencia limitada

Amendment 003 prevalece sobre documentos anteriores únicamente para:

- boundary de esquema proveedor;
- clases y clasificación de campos proveedor;
- `GRZ_MEDIAN_PRESENT_V1`;
- DTO candidato y procedencia técnica;
- enforcement de generación north 9011;
- conducta ante conflicto de esquema/documentación.

Amendment 001 conserva autoridad sobre T10 y sus golden values. Amendment 002 conserva autoridad sobre bootstrap causal, límites anidados, ledger único, promoción padre→hijo, firewall, derechos/autorización y recursos dependientes fuera de esta precedencia. El contrato científico original y los restantes elementos de OC-3 no cambian.

## 22. Estado y bloqueos remanentes

Crear esta enmienda no asigna READY. El estado sigue siendo:

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

Los bloqueos exactos después de congelar Amendment 003 son:

1. implementación y verificación sintética del `ProviderSchemaAdapter`;
2. contratos binarios FITS root/regionales con HDU, TFORM, endian, scaling, nulls, unidades, strings y reglas de comparación geométrica revisadas;
3. resolución prospectiva de `DOCUMENTED_PROVIDER_TYPE_INCONSISTENCY` para `brickid` mediante evidencia de bytes proveedor;
4. checksum, layout, columnas, membership key, cardinalidad y null/scaling de la lista 9012;
5. habilitación prospectiva del parser de patch list después de resolver el punto anterior;
6. verificación futura de bytes/checksums y tamaños dentro de los caps congelados;
7. production rights binding con análisis/cache local afirmativos y redistribución deshabilitada;
8. manifiesto bootstrap de producción sellado y revisado;
9. autorización humana concreta `METADATA_BOOTSTRAP_ONLY` para el manifiesto y comando exactos.

Incluso después de implementar satisfactoriamente el adapter, la adquisición metadata continúa bloqueada hasta resolver como mínimo la lista 9012, derechos, manifiesto y autorización humana.

## 23. Contabilidad y terminal

Esta tarea crea exactamente este Markdown. No modifica código, tests, autoridades, informes ni enmiendas anteriores.

- Solicitudes reales de red: **0**.
- Bytes DR9 adquiridos: **0**.
- FITS descargados: **0**.
- Manifiestos de producción creados: **0**.
- Ledgers creados: **0**.
- Bricks reales seleccionados: **0**.
- Ejecuciones OC-3 iniciadas: **0**.

**PREFLIGHT_BLOCKED_MANIFEST_OR_RIGHTS**

**OC-3 REMAINS NOT STARTED.**
