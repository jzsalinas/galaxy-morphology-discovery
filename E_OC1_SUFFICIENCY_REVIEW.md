# E-OC1 — revisión documental de suficiencia

## 1. Status and scope

**OBSERVED:** Etapa documental terminada el 2026-09-18. Se revisaron únicamente las tres páginas autorizadas y evidencia local preexistente. No se adquirieron datos astronómicos, ejecutaron contrastes numéricos nuevos ni implementaron pipelines. Esta evaluación corresponde a la candidata B1 (crop nativo local de un brick), sin aprobarla ni ampliar su definición.

**INFERRED:** Las tres áreas tienen soporte parcial, pero ninguna satisface íntegramente su pregunta congelada. `PARTIALLY_SUFFICIENT` reconoce contenido útil; no significa aprobación condicional. La procedencia íntegra de una página y su suficiencia científica son evaluaciones diferentes.

## 2. Integrity verification

**OBSERVED:** Se leyó MIPS y se verificó antes de adquirir documentos su SHA-256 esperado: `f7f27acbe42a0caecd1f0e4e2e86eedea6c546434d95c16143c0a7d122f38f24`. También se leyeron la revisión contractual y la gobernanza aplicable. Los cuerpos HTML preservados tienen tamaño y SHA-256 concordantes con el registro de recuperación. ETag y Last-Modified se conservan como metadatos HTTP, no como comprobantes criptográficos ni fechas de validez histórica de todas las afirmaciones.

**OBSERVED:** DQ-DR5 coincide byte a byte con la evidencia histórica S6.raw; RES-DR5 con S5.raw. La nueva recuperación confirma esas versiones documentales, sin añadir por sí misma garantías técnicas. RIGHTS-DR5 se preserva como documento general actual. La comprobación final de autoridades y evidencia histórica consta en `e_oc1/evidence/integrity_verification.json`: hashes de los archivos controlados y comparación de inventario/tamaño/mtime de c0; esta última no se presenta como un rehash completo de todos los datos históricos.

## 3. Frozen E-OC1 question

**DOCUMENTED — mandato congelado:** Q1 exige semántica espacial suficiente para distinguir soporte, validez, máscara, saturación, interpolación, cosmic rays, bleed, artefactos y cero válido en todo el crop, sin proxies falsos. Q2 exige caracterización suficiente de PSF efectiva, remuestreo y ruido/covarianza para A11 y B2/B4, preservando la limitación sobre precisión. Q3 exige distinguir análisis, preservación local, publicación/atribución, reproducción de imágenes y redistribución de FITS/derivados/metadata.

**DOCUMENTED — criterio de decisión:** La revisión contractual §19 y el expediente autorizado requieren suficiencia afirmativa conjunta. Evidencia ausente, ambigua o insuficiente concluye la etapa por insuficiencia; no habilita búsquedas adicionales. No se introducen umbrales numéricos ni requisitos de identidad forense universal.

## 4. Documentary evidence register

**OBSERVED:** Los tres GET concluyeron con HTTP 200, `text/html; charset=utf-8`, sin redirecciones. URL final igual a solicitada. El JSON complementario conserva timestamps UTC, cabeceras, tamaños, hashes, secciones, afirmaciones y limitaciones por documento.

| Evidencia | Fuente oficial preservada | Bytes | Evaluación de contenido |
|---|---|---:|---|
| DQ-DR5 | [DR5 files](https://www.legacysurvey.org/dr5/files/) | 88349 | INFERRED: PARTIALLY_SUFFICIENT |
| RES-DR5 | [DR5 description](https://www.legacysurvey.org/dr5/description/) | 41199 | INFERRED: PARTIALLY_SUFFICIENT |
| RIGHTS-DR5 | [Acknowledgment](https://www.legacysurvey.org/acknowledgment/) | 21688 | INFERRED: PARTIALLY_SUFFICIENT |

**OBSERVED:** SHA-256 de cuerpos exactos:

- DQ-DR5: `b7818d98910f16b81e235994926f888e47bd4f2c6b58283d1ec7383c6d585e9e`.
- RES-DR5: `7dd4e5ca9ae476508c09b35104a4846eeef10a72b076a1382d4a7a35c3fd1575`.
- RIGHTS-DR5: `adb1c5b41ad8aee7544a23d1b499b317d97c82222b4f69f65efa3ad13f6a9a1c`.

## 5. DQ-DR5 assessment

**DOCUMENTED:** Image Stacks describe image como coadd ponderado por inverse variance, en nanomaggies por píxel, con Lanczos-3; invvar como suma de inverse variances de entradas. Nexp cuenta exposiciones contribuyentes; depth/galdepth expresan sensibilidad a flujo de fuentes. ANYMASK/ALLMASK son flags del píxel central entre exposiciones, FRACMASKED una fracción ponderada y PSFSIZE una FWHM resumida. Las tablas CCD describen geometría y versiones de calibración. [DQ-DR5](https://www.legacysurvey.org/dr5/files/).

**DOCUMENTED:** Las notas de histogramas consideran enmascaramiento de exposiciones (por ejemplo saturación y cosmic rays). **INFERRED:** Esto acredita tratamiento upstream de ciertos defectos, no una clasificación exhaustiva del coadd final. [DQ-DR5](https://www.legacysurvey.org/dr5/files/).

**UNRESOLVED:** El documento no establece un mapa completo de estados de calidad DR5 o alternativa suficiente para A10, ni una regla que distinga cero válido de falta de soporte en cada píxel. Su listado no prueba inexistencia física de otros productos. **INFERRED:** Nexp, ivar positiva y finitud no acreditan limpieza científica. FLUX_IVAR de catálogo no es inverse variance por píxel. Q1 queda parcialmente sustentada, sin cierre afirmativo.

## 6. RES-DR5 assessment

**DOCUMENTED:** Los stacks son productos de conveniencia, en TAN a 0.262 arcsec/píxel, remuestreados con Lanczos-3. La advertencia explícita es: “These stacks should not be used for "precision" work.” Tractor ajusta exposiciones individuales y evita complicaciones de interpolación y covarianza. La PSF descrita es espacial por CCD/exposición, mediante PSFEx. [RES-DR5](https://www.legacysurvey.org/dr5/description/).

**DOCUMENTED:** Sky Level describe procesamiento previo del cielo y una estimación espacial por spline a partir de medianas en ventanas de 512 píxeles con enmascaramiento. **UNRESOLVED:** Esto no cuantifica por sí mismo el efecto sobre luz tenue de cada crop. [RES-DR5](https://www.legacysurvey.org/dr5/description/).

**UNRESOLVED:** Faltan una PSF efectiva espacial del coadd o proxy de suficiencia demostrada, y límites cuantitativos de correlación/ruido y precisión relevantes para MIPS. **INFERRED:** Ni el aviso de precisión ni el uso de exposiciones por Tractor demuestran inutilidad general para morfología; tampoco autorizan declarar adecuación al proyecto. Q2 tiene soporte parcial.

**INFERRED:** El Lanczos-3 documentado aquí es upstream, de construcción del coadd. No certifica el operador posterior ni el commit desplegado del cutout normal. La referencia aproximada de la guía de descarga a píxeles usados por Tractor no invalida la distinción explícita entre exposiciones y stacks ni demuestra identidad.

## 7. RIGHTS-DR5 assessment

**DOCUMENTED:** La sección de imágenes del Sky Viewer distingue términos de los diferentes surveys. Para capas producidas por Legacy Surveys, incluyendo DECaLS, declara CC BY 4.0 y condiciones de crédito visible. Para Legacy Surveys pide “Legacy Surveys / D. Lang (Perimeter Institute)”. Otra sección prescribe agradecimientos para publicaciones científicas que usan los datos. [RIGHTS-DR5](https://www.legacysurvey.org/acknowledgment/).

| Operación | Alcance establecido en el expediente |
|---|---|
| Análisis científico | DOCUMENTED: se contempla uso científico de datos en publicaciones. UNRESOLVED: no queda especificado integralmente el permiso para la operación FITS propuesta. |
| Preservación local | UNRESOLVED: no hay alcance explícito separado para preservar el conjunto científico FITS y auxiliares previsto. |
| Publicación/atribución | DOCUMENTED: existen agradecimientos prescritos; la fórmula abreviada para colaboradores DESI tiene condiciones. |
| Reproducción de imágenes | DOCUMENTED: términos CC BY 4.0 y crédito para las capas producidas nombradas, sin extenderlos a todos los surveys alojados. |
| Redistribución de cutouts FITS/coadd y metadata | UNRESOLVED: la página no equipara expresamente ese conjunto científico con las imágenes/capas cubiertas por la declaración. |

**INFERRED:** Q3 es parcialmente suficiente. No se infiere permiso de redistribución de la mera posibilidad de publicar, ni una prohibición legal de la falta de definición. No se siguieron enlaces a licencias ni otros documentos.

## 8. Mapping to MIPS A10/A11/B2/B3/B4/O1

**DOCUMENTED:** Se usan los identificadores y niveles definidos en §6 de la revisión contractual, sin reinterpretar MIPS ni convertir toda metadata deseable en requisito absoluto.

| Criterio | Evidencia y juicio |
|---|---|
| A10 BLOCKING | DOCUMENTED: flags centrales y tratamiento de defectos upstream. UNRESOLVED: validez espacial del crop o alternativa suficiente independiente. No cerrado. |
| A11 BLOCKING | DOCUMENTED: muestreo y PSF por exposición. UNRESOLVED: resolución efectiva espacial o aproximación cuya suficiencia esté demostrada. No cerrado. |
| B2 REQUIRED_FOR_AUDIT | DOCUMENTED: unidades y relación general image/ivar. UNRESOLVED: ceros/flags, soporte y límites de correlación suficientes. No cerrado. |
| B3 REQUIRED_FOR_AUDIT | DOCUMENTED: sustracción de cielo upstream. UNRESOLVED: auditoría del efecto sobre luz tenue y disponibilidad aplicable del modelo/metadata. Soporte parcial, no prueba de pérdida. |
| B4 REQUIRED_FOR_AUDIT | DOCUMENTED: metadata de exposición y FWHM catalogal. UNRESOLVED: PSF efectiva del crop o aproximación justificada con dominio y calidad. No cerrado. |
| O1 operativo | DOCUMENTED: atribución e imágenes. UNRESOLVED: alcance científico FITS/derivados. No cerrado para la operación completa. |

**INFERRED:** B1 no añadiría remuestreo al recortar índices nativos, pero heredaría propiedades del coadd. Esta simplificación no resuelve A10/A11. La opción de deshabilitar redistribución contemplada en O1 tampoco elimina los bloqueos científicos ni constituye aquí autorización de un contrato reducido.

## 9. Adversarial interpretation review

| Lectura que excedería la evidencia | Revisión |
|---|---|
| No se lista máscara, luego no existe | UNRESOLVED: solo queda establecida insuficiencia documental. |
| Usar MASKBITS/PSFSIZE maps de releases posteriores | OBSERVED: no se consultaron; INFERRED: no son evidencia DR5. |
| ANYMASK/ALLMASK centrales describen el crop | DOCUMENTED: dominio central; INFERRED: extrapolación inválida. |
| Nexp/ivar/finitud certifican píxel limpio | UNRESOLVED: no se ha demostrado esa garantía. |
| PSF CCD o FWHM escalar equivale a PSF efectiva | UNRESOLVED: falta justificación de suficiencia del proxy. |
| Coadds inútiles porque Tractor no los usa | INFERRED: conclusión no sustentada. |
| Coadds adecuados porque están disponibles | INFERRED: conclusión no sustentada. |
| Aviso de precisión garantiza fallo o éxito MIPS | UNRESOLVED: no especifica tal resultado. |
| CC BY de capas cubre todo FITS y metadata | UNRESOLVED: falta equivalencia explícita de alcance. |
| Igualdad de arrays demuestra commit desplegado | INFERRED: no certifica procedencia/versionado. |

## 10. Remaining uncertainty

**UNRESOLVED:** Permanecen la validez espacial y los estados de píxel, la PSF efectiva, el ruido correlacionado, los límites sobre precisión/luz tenue y el alcance de derechos del conjunto científico pretendido. No se reemplazan por valores supuestos, proxies optimistas, futuros tests prometidos ni una búsqueda en otra release.

**INFERRED:** Estas carencias bastan para cerrar por insuficiencia del expediente. No hace falta demostrar inexistencia de productos ni incompatibilidad intrínseca de todos los coadds. Tampoco falta necesariamente un commit exacto: una garantía independiente suficiente sería conceptualmente admisible según MIPS, pero no está establecida aquí.

## 11. Explicit terminal outcome

**INFERRED — decisión única:** `NO_CURRENTLY_ADMISSIBLE_ROUTE_WITH_AVAILABLE_EVIDENCE`.

**INFERRED:** Se aplica la rama congelada de insuficiencia: los tres contenidos contienen información útil, pero subsisten vacíos materiales. No hay soporte afirmativo conjunto para redactar el contrato B1 como suficientemente sustentado, ni una demostración directa de incompatibilidad científica o prohibición de derechos. La etapa queda terminada, sin estado pendiente ni otra etapa de evidencia propuesta.

## 12. Effect on project state

**OBSERVED:** C0 permanece históricamente CLOSED con global STOP: A/B PASS; C INCONCLUSIVE; D/E/F INCONCLUSIVE por cierre anticipado. E-OC1 no modifica Gates, presupuestos o conclusiones históricas. El cutout normal no se declara incorrecto.

**OBSERVED — evidencia histórica limitada:** La equivalencia Range/subimage corresponde a 42 regiones image de 12 objetos, tres bandas y 14 bricks, en los layouts soportados y con igualdad de valores decodificados bajo el tratamiento NaN registrado. No demuestra igualdad de archivos completos, auxiliares, normal cutout ni otros layouts. No se repitió el experimento.

**INFERRED:** No se habilitan un contrato B1, preprocessing, adquisición de auxiliares, entrenamiento ni cambio de survey. No se modificaron MIPS, la revisión contractual ni autoridades C0.

## 13. Files created and network accounting

**OBSERVED:** Archivos nuevos de esta etapa:

- `E_OC1_EVIDENCE_REGISTER.json`.
- `E_OC1_SUFFICIENCY_REVIEW.md`.
- `e_oc1/evidence/DQ-DR5.html`.
- `e_oc1/evidence/RES-DR5.html`.
- `e_oc1/evidence/RIGHTS-DR5.html`.
- `e_oc1/evidence/retrieval.json`.
- `e_oc1/evidence/preservation_before.json`.
- `e_oc1/evidence/integrity_verification.json`.

**OBSERVED:** Tres documentos lógicos, tres GET HTTP 200, cero redirecciones, 151236 bytes de cuerpos preservados frente al máximo de 10485760. Hubo además un intento fallido de resolución DNS antes de HTTP, registrado sin cuerpo ni status; por ello hay cuatro registros de intento, no cuatro documentos ni cuatro respuestas HTTP. La repetición tras resolver la restricción de entorno está explicitada en retrieval.json. No hubo descarga de enlaces ni otras páginas. Estos bytes no incluyen overhead HTTP/TLS.

**OBSERVED:** Cero solicitudes/bytes de datos astronómicos adicionales. Los contadores históricos C0 permanecen en 465348528 bytes, 383 solicitudes de datos y 936 HTTP; E-OC1 tiene contabilidad documental separada, no reinicia ni sobrescribe ese ledger. La verificación final es local y documental; no se añadieron ni ejecutaron tests científicos.
