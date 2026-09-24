# Política del proyecto

Leer `GALAXY_RESEARCH_SEED.md`, `CODEX_PHASE_C0_SPEC.md` y `C0_EXECUTION_DECISION_001.md` antes de trabajar. No modificar autoridades históricas sin autorización. El addendum resuelve Gates y estados inconclusos.

## Principios

- AAC es disciplina metodológica, no una teoría que deba confirmarse.
- Nunca forzar clases.
- Mantener separados observación, preprocessing, representación, estructura descubierta, interpretación física y etiquetas humanas.
- Nunca reinterpretar evidencia histórica retrospectivamente.
- Fallar cerrado en límites científicos, de procedencia e integridad.

## Estado de misiones

- La misión PHOTSYS es histórica y terminal en `oc3/OC3_AUTONOMY_STATE_001.json`; no reabrirla ni reutilizar su autorización.
- Estado prospectivo actual: `oc3/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_STATE_001.json`.
- Mandato prospectivo actual: `OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001.md` y `oc3/INPUTS/OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMY_MANDATE_001.json`.
- Runbook actual: `OC3_OBSERVATIONAL_MULTIPLICITY_AUTONOMOUS_RESEARCH_RUNBOOK_001.md`.
- Mientras no exista una autorización permanente nueva, la misión permanece inactiva y no puede emitir permisos.

## Regla autónoma

Cuando una autorización permanente válida esté `ACTIVE`, continuar sin pedir aprobación entre Gates intermedios elegibles. Las ejecuciones epistémicamente materiales requieren permisos deterministas, de uso único, derivados del mandato. Versionar artefactos compactos; conservar evidencia pesada localmente. Detenerse únicamente en un terminal científico o `STOP_REQUIRES_HUMAN`.

Mientras la autonomía esté `ACTIVE`, el policy core congelado no puede modificarse. Toda modificación necesaria exige `STOP_REQUIRES_HUMAN`.

Detenerse siempre ante expansión del mandato, aumento de presupuesto, observación astronómica o de valores PHOTSYS/BRICKNAME/BRICKID/ROOT no autorizada, acciones destructivas o irreversibles, credenciales nuevas, clases de autoridad externas, criterios modificados después de observar evidencia, Panel V2/P1/resolver, o un conflicto de integridad que exija cambiar gobernanza.

## Git

Nunca forzar push, reescribir historia, borrar evidencia local ni versionar árboles runtime pesados. Código, pruebas, especificaciones, estado, ledger y reportes compactos pertenecen a Git. No mezclar ni fusionar autónomamente a `main`.
