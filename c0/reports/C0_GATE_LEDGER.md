# C0 — ledger parcial de Gates

Autoridad operativa: C0_EXECUTION_DECISION_001.md. Evaluación por Codex; no decisión global hasta C0-C–F. No se inicia C1.

## C0-A — PASS

Hipótesis: fuente fija y auditable. Zenodo record 4573248, DOI versionado 10.5281/zenodo.4573248, versión 0.0.2, licencia CC-BY-4.0. Catálogo GZD-5 de 40528939 bytes; MD5 oficial y SHA-256 local verificados. Repetición del diccionario pequeño reproduce SHA-256 y coincide con MD5 oficial.

Evidencia: C0_SOURCE_REGISTER.yaml; C0_REMOTE_FILE_MANIFEST.csv; S2_version.raw; S2_schema.raw y S2_schema_repeat.raw; C0_INGEST_VERIFICATION.json. Desviación: incidencias temporales de transporte resueltas; se conservaron fallos y contadores. Sin cambio de fuente ni seed. Este PASS no aprueba licencias de imágenes, que corresponden a los Gates pendientes.

## C0-B — PASS

Hipótesis: identidad de campaña sin semántica morfológica. 253286 identificadores únicos de 253286 filas (100%); coordenadas válidas 100%; cero fallback UUIDv5. CDS y Zenodo coinciden en 253286 nombres únicos y coordenadas, sin ausencias ni duplicados por nombre. La pertenencia procede del archivo volunteers_5 y su diccionario. Índice separado; lockbox con permisos 0700, archivos 0400.

Evidencia: SUBJECT_INDEX.parquet; CONFOUND_AUDIT_C0.parquet; C0_ZENODO_INGEST_SUMMARY.json; C0_CDS_RECONCILIATION_SUMMARY.json; C0_INGEST_VERIFICATION.json; C0_CDS_VERIFICATION.json; C0_CARDINALITY_FLOW.csv.

Limitaciones explícitas: la cifra de campaña publicada de aproximadamente 262000 no se fuerza a coincidir con el catálogo voluntario; otras cardinalidades de imágenes tienen denominadores distintos y aún no están verificadas operativamente. No se ha evaluado duplicación espacial de fuentes ni disponibilidad PNG; eso no se infiere de la unicidad nominal. Los permisos bajo el mismo usuario no constituyen aislamiento frente al propietario. No se propone cambiar el seed por esta evidencia.

## C0-C, C0-D, C0-E y C0-F — evaluación no iniciada

Pendientes de probe, productos científicos y presupuesto empírico. No se asignan estados científicos INCONCLUSIVE por el mero hecho de esperar ejecución humana. Ningún claim dependiente está autorizado.

## Aceptación de implementación

26 pruebas offline pasan. La prueba de reordenamiento del probe real se ejecutará en el siguiente paso manual; las pruebas sintéticas no la sustituyen. Quedan pruebas FITS, pareo y regeneración final. C0 no está completo.

## Cierre vinculante posterior — 2026-09-18T10:33:53.686935+00:00

Esta entrada sustituye el estado histórico «evaluación no iniciada» de C0-C–F y la prohibición histórica de decisión global antes de C0-C–F: aplica el addendum.

C0-A PASS y C0-B PASS preservados con evidencia anterior. C0-C **INCONCLUSIVE**, decisión global **STOP**. Hipótesis: semántica científica del cutout normal DR5 verificable. Evidencia esperada: cadena de procedencia/unidades y contraste explicado según protocolo. Resultado: 33/36 combinaciones completas y tres parciales compatibles numéricamente con candidatos, sin cadena independiente suficiente para certificar unidades/operador. La auditoría acotada separó mecanismo de borde de procedencia; no hay test pixelar decisivo pendiente.

Informe: C0_BOUNDED_AUDIT_REPORT.md; SHA256 7d5f58cfedfee2a1c62cc8b9b4d68e915dda2d253acb40ea07c83f164590c9f6. Resultados reproducibles: C0_BOUNDED_AUDIT_RESULTS.json y c0_pipeline/bounded_audit.py; protocolo predeclarado C0_BOUNDED_AUDIT_PROTOCOL.md. Decisión: Codex aplicando instrucción de cierre y addendum del usuario. Sin cambio al seed; cualquier ruta alternativa requiere propuesta autorizada. No se prepara adquisición rank5.

C0-D **INCONCLUSIVE**: auxiliares parcialmente demostrados, no evaluación completa del contrato; no determina este STOP. C0-E **INCONCLUSIVE**: SDSS no adquirido ni pareo validado por restricción de etapa; no es prueba de inviabilidad. C0-F **INCONCLUSIVE**: inventario parcial y presupuestos medidos, escala/licencias completas no concluidas; no es prueba de imposibilidad. Son estados de cierre sin demostración suficiente tras STOP crítico, no fallos experimentales. Ninguna afirmación dependiente autorizada.

Contadores: 465348528 bytes / 383 solicitudes de datos / 936 HTTP. Se detienen trabajos científicos dependientes; solo cierre administrativo permitido.
