# Política del proyecto

Leer GALAXY_RESEARCH_SEED.md, CODEX_PHASE_C0_SPEC.md y C0_EXECUTION_DECISION_001.md antes de trabajar. No modificar los documentos autoritativos sin autorización. El addendum resuelve Gates y estados inconclusos.

## Ejecución humana obligatoria — C0 y todas las fases posteriores

Todo proceso que cumpla cualquiera de estas condiciones debe ser delegado al usuario para ejecución manual:

- tiempo estimado superior a 5 minutos;
- descarga estimada superior a 250 MiB;
- lectura o escritura intensiva superior a 1 GiB;
- operación bulk sobre catálogos, bricks, frames o imágenes;
- proceso sujeto a throttling, esperas o reintentos prolongados;
- cualquier entrenamiento futuro;
- cualquier operación cuyo seguimiento interactivo consumiría tiempo o tokens sin requerir razonamiento del agente.

Para esos procesos:

1. Implementa primero un script reproducible, idempotente y reanudable.
2. Añade `--help`, `--dry-run` cuando sea aplicable y límites explícitos.
3. Ejecuta solamente una prueba pequeña o smoke test.
4. No ejecutes el proceso completo.
5. Entrega al usuario la línea de comando exacta para ejecutarlo.
6. Indica:
   - directorio desde el cual ejecutarla;
   - tiempo y espacio estimados;
   - archivos de entrada;
   - artefactos de salida;
   - ubicación del log;
   - forma de reanudar;
   - señal inequívoca de éxito o fracaso.
7. La salida extensa debe escribirse a un log, no imprimirse completa en terminal.
8. El proceso debe producir un resumen compacto y un código de salida.
9. Después de entregar el comando, detente y espera a que el usuario confirme su finalización.
10. Cuando el usuario regrese, inspecciona los artefactos producidos; no repitas el proceso.

No uses `nohup`, procesos en background o polling prolongado para evitar esta delegación, salvo que el usuario lo solicite expresamente.

Los procesos inferiores a esos umbrales pueden ejecutarse directamente si respetan los límites C0.


## C0

Implementar exclusivamente C0.0–C0.6. Prohibidos entrenamiento, embeddings, PCA, clustering, UMAP, anomalías, galerías y optimización de preprocessing. No usar votos o Zoobot para selección. Mantener RAW_IMMUTABLE, SUBJECT_INDEX, CONFOUND_AUDIT e INTERPRETATION_LOCKBOX separados. No imprimir nombres ni valores de respuestas morfológicas.

Límites acumulados: 96 objetos, 2 GiB descargados, 1000 solicitudes no metadata, 3 reintentos por recurso y 4 solicitudes simultáneas por servicio. Ninguna reanudación reinicia contadores. No sustituir releases ni equivalencias semánticas. Detener dependencias de Gates fallidos según addendum.

No inicializar, eliminar ni reparar .git. Preservar cambios ajenos. Antes de continuar más allá de C0.1 informar archivos, pruebas, transferencia, solicitudes, discrepancias y próximo proceso delegado.
