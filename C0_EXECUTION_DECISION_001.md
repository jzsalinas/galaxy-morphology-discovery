# C0_EXECUTION_DECISION_001 — Addendum operativo vinculante

Fuente: autorización textual del usuario. Prevalece sobre las reglas operativas incompatibles de CODEX_PHASE_C0_SPEC.md; no altera la intención científica.

Autorizo iniciar la implementación de C0 y las solicitudes de red ligeras, con las siguientes decisiones vinculantes.

Antes de implementar el pipeline científico, registra estas decisiones en:

C0_EXECUTION_DECISION_001.md

Este documento será un addendum operativo de CODEX_PHASE_C0_SPEC.md. No modifiques todavía GALAXY_RESEARCH_SEED.md ni CODEX_PHASE_C0_SPEC.md.

1. RESOLUCIÓN DE LA POLÍTICA DE GATES

Tu observación sobre la contradicción de cierre es correcta.

Los Gates no tienen todos la misma criticidad.

Gates críticos para la viabilidad del núcleo:

- C0-A: fuente reproducible;
- C0-B: identidad GZD-5 sin fuga morfológica;
- C0-C: semántica científica verificable de DECaLS DR5;
- C0-D: disponibilidad suficiente de pesos, cobertura, máscaras y PSF para formular un contrato honesto.

Un estado FAIL en C0-A, C0-B o C0-C implica STOP.

Un estado FAIL o INCONCLUSIVE en C0-D implica STOP solamente si no existe una revisión científicamente honesta del contrato que permita evaluar cobertura, ruido y calidad observacional. Si existe una revisión explícita y verificable, la decisión será GO_WITH_REVISION y deberá proponerse seed v0.2 antes de C1.

Gates de capacidad adicional:

- C0-E prueba la viabilidad cross-survey de O3.
- C0-F prueba la viabilidad operacional de la escala propuesta.

Un FAIL en C0-E no invalida automáticamente el núcleo DECaLS:

- abandona o difiere O3;
- prohíbe cualquier claim cross-survey;
- exige seed v0.2;
- permite GO_WITH_REVISION si C0-A–D sostienen el núcleo.

Un FAIL en C0-F permite GO_WITH_REVISION si una cohorte piloto reducida, seleccionada sin morfología, sigue siendo viable. Implica STOP únicamente si existe incompatibilidad legal, ausencia de acceso reproducible o imposibilidad incluso para una cohorte piloto científicamente útil.

2. ESTADOS INCONCLUSIVE

INCONCLUSIVE no debe convertirse silenciosamente en PASS ni FAIL.

- En C0-A, C0-B o C0-C: INCONCLUSIVE implica STOP de C0, porque no puede demostrarse la identidad o semántica del dato.
- En C0-D: aplica la regla de revisabilidad definida arriba.
- En C0-E: O3 queda diferido y la decisión máxima posible es GO_WITH_REVISION.
- En C0-F: no se autoriza materialización completa; puede proponerse un piloto reducido con GO_WITH_REVISION.

Un resultado INCONCLUSIVE bloquea todas las afirmaciones que dependan de ese Gate.

3. COMPORTAMIENTO DESPUÉS DE UN FAIL

Después de un FAIL:

- detén inmediatamente las adquisiciones y procesos que dependan del Gate fallido;
- no continúes intentando “rescatar” ese Gate mediante cambios no autorizados;
- puedes completar artefactos administrativos, registrar evidencia y evaluar Gates independientes necesarios para emitir el informe final;
- no ejecutes nuevos análisis científicos dependientes del componente fallido.

4. IDENTIFICADOR ALTERNATIVO

Acepto tu interpretación.

La fila original se fija durante la lectura del archivo RAW_IMMUTABLE y se conserva como procedencia estable. Nunca se recalcula después de ordenar, filtrar o particionar.

Para el fallback UUIDv5 registra también:

- checksum del archivo fuente;
- record/version de origen;
- índice de fila inmutable;
- coordenadas normalizadas.

`iauname` continúa siendo el identificador primario cuando sea válido y único.

5. C0_ACCESS_POLICY

Ubica C0_ACCESS_POLICY.yaml en:

c0/provenance/C0_ACCESS_POLICY.yaml

Aunque no aparezca en el árbol resumido de §13, es un artefacto obligatorio.

6. PROTOCOLO DE EJECUCIÓN HUMANA PARA PROCESOS PESADOS

Esta regla debe aplicarse en C0 y en todas las fases posteriores del proyecto.

Crea un AGENTS.md en la raíz del proyecto antes de implementar el resto. Incluye en él esta política:

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

7. RED Y DESCARGAS

Autorizo:

- consultas documentales;
- HEAD y metadatos;
- resolución de DOI y versiones;
- descarga de diccionarios, schemas y catálogos pequeños;
- smoke tests de endpoints;
- muestras mínimas necesarias para validar scripts.

No autorizo todavía que ejecutes directamente:

- descargas bulk;
- recuperación completa del probe si supera los umbrales de delegación;
- descarga completa de bricks, frames o archivos de imágenes;
- ninguna operación cercana al límite de 2 GiB.

Para esas operaciones debes preparar el script y entregarme el comando conforme al protocolo anterior.

8. GIT

No inicialices Git, no elimines `.git` y no intentes repararlo todavía. Registra la anomalía en el snapshot de entorno. La configuración del repositorio se decidirá por separado.

9. ORDEN AUTORIZADO

Procede ahora con:

1. crear C0_EXECUTION_DECISION_001.md;
2. crear AGENTS.md;
3. implementar C0.0 y sus pruebas;
4. implementar C0.1;
5. realizar las consultas de red ligeras autorizadas;
6. preparar C0.2 y fases posteriores;
7. detenerte antes del primer proceso que deba ejecutarse manualmente y entregarme el comando exacto.

Antes de continuar más allá de C0.1, informa:

- archivos creados;
- pruebas ejecutadas;
- volumen descargado;
- solicitudes realizadas;
- discrepancias encontradas;
- próximo proceso delegado, si corresponde.

Puedes comenzar.