# OC-3 — especificación prospectiva de selección técnica y materialización del piloto

**Stage futuro:** `OC3-TECHNICAL-SELECTION-001`

**Naturaleza:** especificación offline; no implementa ni ejecuta selección.

**Estado:** `NOT_STARTED`. La fase científica OC-3 permanece no iniciada.

## 1. Propósito y unidad

Esta etapa materializará solamente la **cohorte técnica del piloto**: exactamente un brick DR9 south/DECaLS y un brick DR9 north/BASS-MzLS, marcados permanentemente como `INSTRUMENTAL_DEVELOPMENT`. La unidad de selección es el **brick**. Las filas resultantes no son galaxias, sujetos morfológicos ni una población científica.

Las seis ubicaciones S1–S3/N1–N3 siguen sin seleccionarse: requieren NEXP, MASKBITS y PSFSIZE nativos y pertenecen a la adquisición auxiliar posterior. Ninguna identidad de la futura población de galaxias cruza esta etapa.

## 2. Inputs cerrados

La implementación futura aceptará únicamente evidencia local ya adquirida:

- `OC3-METADATA-BOOTSTRAP-001`, terminal `METADATA_BOOTSTRAP_PARTIALLY_RESOLVED`;
- `OC3-PATCH-METADATA-DECODE-001`, terminal `PATCH_METADATA_DECODE_VALIDATED`;
- los RAW inmutables ROOT, NORTH, SOUTH y PATCH de ese mismo attempt, con sus paths, tamaños y SHA-256 ya ligados;
- las autoridades OC-3 vigentes, incluido Amendment 002, Amendment 003/004, contratos físicos, semántica de valores y esta especificación.

No existe un allowlist row-level de entrada: usar uno reintroduciría la circularidad corregida por Amendment 002. El CSV producido por esta etapa será el allowlist de desarrollo, bajo la política prospectiva vinculante de exclusión confirmatoria.

Antes de filas debe revalidarse el binding completo, incluido:

```text
ROOT  dc943d702357f93553b9e5d15e87ace38df94eb7095f4100657407b3f9919c5f
NORTH 2edd5c295fdad26852c6f224a3ff023cff43dd0e03a53acd35b767e726ee72fb
SOUTH 7360414f5d53571ca70fa0cb483eb8c80cfcbe80df0856a117246f442a0b9a3f
PATCH f87e7aa55360b935033fc0638491038e7170cc9b88fc6c0905000d420280f6b6
```

El PATCH conserva `PROVIDER_PUBLISHED_CHECKSUM_KNOWN=false`. No se modifica ningún input ni evidencia previa.

## 3. Boundary de campos

La lectura será column-selective y fail-closed. Sólo pueden observarse:

- ROOT: `BRICKNAME`, `BRICKID`, `RA`, `DEC`, `RA1`, `RA2`, `DEC1`, `DEC2`;
- NORTH/SOUTH: `brickname`, `brickid`, `ra`, `dec`, `ra1`, `ra2`, `dec1`, `dec2`, `nexp_g`, `nexp_r`, `nexp_z`;
- PATCH: `RELEASE`, `BRICKID`, `BRICKNAME`.

`brickid` y geometría sirven sólo para gates exactos de identidad/consistencia. `nexp_g/r/z` sirve únicamente para derivar `grz` mediante `GRZ_MEDIAN_PRESENT_V1`: los tres enteros deben ser `>=1`. No se leen `nexphist`, `survey_primary`, `area`, métricas de fuentes, PSF, profundidad, color, masa, SFR, ambiente, Sérsic, concentración, píxeles ni variables de validación física.

El selector recibe exactamente estos campos derivados o de procedencia:

```text
region, survey, release_family, generation, brickname, grz, corrected_9012
```

Sólo `region` y `brickname` intervienen en el orden. Los demás son gates de elegibilidad congelados. `brickid` no es fallback ni desempate.

## 4. Elegibilidad y PATCH

Todas las filas deben satisfacer `OC3_BRICKNAME_SEMANTICS_V1`, tipos exactos, finitud geométrica y joins uno-a-uno ROOT↔regional. La geometría ROOT y regional debe coincidir conforme al contrato vigente; una discrepancia detiene el conjunto completo, no excluye una fila.

- South elegible: `region=south`, `survey=DECaLS`, `release_family=DR9`, `generation=9012`, `grz=true` y `corrected_9012=true` por match exacto en las 1.691 filas PATCH validadas.
- North elegible: `region=north`, `survey=BASS_MzLS`, `release_family=DR9`, `generation=9011`, `grz=true`, `corrected_9012=false`. North nunca consulta PATCH.

PATCH membership se compara por los ocho bytes canónicos exactos de `BRICKNAME` y exige el mismo `BRICKID`. No se limpia, repara, normaliza, infiere ni amplía. Un south no miembro es inelegible; una inconsistencia PATCH es fallo del stage completo.

Cada exclusión se clasifica únicamente como cobertura técnica g/r/z o membership/generación PATCH. Los fallos de binding, schema, identidad o joins son gates, no criterios de conveniencia. No existe exclusión morfológica.

## 5. Algoritmo determinista congelado

1. Revalidar bindings, hashes, contratos físicos y semántica antes de construir candidatos.
2. Construir por región el conjunto completo de candidatos elegibles usando sólo §3–4; registrar únicamente sus conteos y el SHA-256 de su secuencia canónica ordenada.
3. Para cada candidato calcular:

   `SHA256(UTF-8("OC3-v1|brick|<region>|<brickname>"))`.

4. Ordenar por ese digest hexadecimal ascendente y, ante empate, por `brickname` ASCII ascendente.
5. Elegir el primero de south y después el primero de north. No se usa RNG ni seed.
6. Exigir dos bricknames distintos. Si falta una región, fallar sin sustituir release, survey, criterio o tercer brick.
7. Marcar inmediatamente ambos territorios, futuras ventanas y productos directos como `INSTRUMENTAL_DEVELOPMENT`, excluidos prospectivamente de toda evaluación morfológica confirmatoria.
8. Publicar atómicamente el membership sólo después de pasar todos los gates. No se inspeccionan auxiliares, píxeles ni apariencia antes o después de elegir.

La permutación del orden de filas proveedor no cambia candidatos, hashes ni resultado.

Para el hash agregado de candidatos de cada región, serializar cada fila ordenada como `<selection_hash>|<brickname>\n`, concatenar sin header en UTF-8 y aplicar SHA-256 a esos bytes. No se serializa esa secuencia fuera de memoria.

## 6. Límites heredados del piloto

No se amplían los límites congelados:

| Dimensión | Límite OC-3 |
|---|---:|
| Bricks | máximo 2; éxito de esta etapa exige 1 south + 1 north |
| Ubicaciones futuras | máximo 6, tres por región, sin reposición; esta etapa materializa 0 |
| Ventanas futuras | 129×129 píxeles nativos, radio 64 |
| Bandas futuras | g/r/z; máximo 18 combinaciones ubicación×banda |
| Productos nativos futuros | máximo 26, más hasta 2 tablas CCD de procedencia |
| Red de esta etapa | 0 solicitudes, 0 bytes |
| Global OC-3 | 1.5 GiB (1.610.612.736 bytes), 200 solicitudes, 2 reintentos adicionales/recurso, concurrencia 1 |
| Recursos globales | RAM 2 GiB, 1 thread, GPU 0, disco 4 GiB, I/O 8 GiB, CPU 1800 s, wall 3600 s/invocación |

La etapa es offline y no reinicia ni consume presupuesto de red. No resuelve todavía URLs, HDUs o tamaños de productos del pixel pilot.

## 7. Output row-level cerrado

Único artifact row-bearing permitido:

`oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv`

Schema y orden exactos:

```text
region,brickname,development,holdout_disjoint,evidence_ref
```

Reglas:

- exactamente dos filas en éxito, primero `south` y luego `north`;
- `(region,brickname)` y `brickname` únicos;
- `development=true` y `holdout_disjoint=true` como strings lowercase;
- `evidence_ref=OC3-TECHNICAL-SELECTION-001` en ambas filas;
- UTF-8 sin BOM, campos ASCII sin quoting, coma literal, LF y un único LF final;
- SHA-256 del archivo completo, incluido el LF final.

`holdout_disjoint=true` registra la exclusión prospectiva vinculante; no afirma haber abierto o comparado un holdout. Si esa política no puede imponerse, no se publica el CSV.

No se persisten DTOs candidatos, listas completas de elegibles, orden por brick, geometría, `brickid`, NEXP, PATCH membership, identidades de galaxias ni tablas unidas. `OC3_INPUT_MANIFEST.json` y los seis slots quedan para etapas separadas.

## 8. Auditoría cerrada

Directorio futuro:

`oc3/technical_selection/OC3-TECHNICAL-SELECTION-001/`

Únicos artifacts permitidos:

```text
TECHNICAL_SELECTION_INPUT_BINDING.json
TECHNICAL_SELECTION_AGGREGATE_EVIDENCE.json
TECHNICAL_SELECTION_TERMINAL.json
TECHNICAL_SELECTION_RUN.log
```

Pueden contener bindings/hashes, conteos de inputs y elegibles por región, exclusiones agregadas por `grz` y PATCH, hashes de las secuencias candidatas, selected/brick count, tie count, hash del CSV, consumos, primer error y terminal. No contienen nombres o IDs individuales; esos aparecen sólo en el CSV autorizado.

Los JSON son canónicos: UTF-8, claves ordenadas, separadores compactos, `ensure_ascii=false`, `allow_nan=false` y un LF final. El output directory y el CSV son de publicación única; un conflicto preexistente falla cerrado.

## 9. Terminales y anti-cherry-picking

Éxito único:

`TECHNICAL_PILOT_COHORT_MATERIALIZED`

Fallo único:

`TECHNICAL_PILOT_COHORT_MATERIALIZATION_FAILED`

Éxito significa solamente que dos bricks técnicos de desarrollo fueron seleccionados y materializados reproduciblemente. No valida galaxias, imágenes, preprocessing, encoder, preservación morfológica, representatividad DR9 ni inicio científico de OC-3.

Después de comprometer esta especificación, una apariencia inconveniente, producto ausente, coste desfavorable o resultado científicamente poco interesante no permite cambiar criterios ni reemplazar bricks. Todo cambio posterior a observar el resultado requiere enmienda prospectiva, motivo explícito y nuevo stage ID; nunca sobrescritura de `OC3-TECHNICAL-SELECTION-001`.

## 10. Implementación futura y siguiente frontera

CLI futuro simple:

```text
oc3/oc3_technical_selection.py --execute-offline \
  --attempt-directory oc3/metadata_bootstrap/OC3-METADATA-BOOTSTRAP-001 \
  --patch-evidence-directory oc3/patch_metadata_decode/OC3-PATCH-METADATA-DECODE-001 \
  --output-csv oc3/INPUTS/OC3_DEVELOPMENT_BRICKS.csv \
  --audit-directory oc3/technical_selection/OC3-TECHNICAL-SELECTION-001
```

La implementación tendrá `--help`, `--dry-run`, paths cerrados, cero argumento URL, decoder column-selective, pruebas sintéticas de no-fuga/determinismo/gates y regresión offline completa. Si su lectura bulk supera la política de `AGENTS.md`, se entregará para ejecución humana.

Tras éxito sólo podrá diseñarse la planificación/adquisición acotada de auxiliares y píxeles ya definida por OC-3. Esta especificación no define preprocessing, representación, clustering ni clases morfológicas.

**En esta entrega no se ejecuta selección, no se crea membership, no se accede a red y no se inicia OC-3 científico.**
