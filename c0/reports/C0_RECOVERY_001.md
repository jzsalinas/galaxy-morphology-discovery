# Recuperación 001 — timeout previo a la ingesta

Ejecución humana: 2026-09-17T01:23:47Z; fallo registrado a 01:24:24Z.

La rueda PyArrow 25.0.1 se descargó (50.102.437 bytes), verificó por SHA-256 y se instaló. La solicitud del catálogo Zenodo terminó en TimeoutError antes de registrar cabeceras HTTP, con cero bytes recibidos. No existen archivos de catálogo ni proyecciones. No se atribuye un fallo científico a este incidente de transporte.

No se repitieron solicitudes de red ni ingesta real durante el diagnóstico. Los contadores originales permanecen: 52.205.627 bytes acumulados, 19 intentos HTTP, 2 solicitudes no metadata. El catálogo tiene un intento consumido; quedan como máximo tres reintentos, sin automatizarlos.

Corrección: timeout de catálogo configurable entre 1 y 120 segundos, predeterminado manual 120; registro de etapa de transferencia. Misma URL versionada, tamaño y MD5. Sin cambio de fuente, release, criterios o límites. Se preservan log y eventos originales.

Validación: 18 pruebas pasan en el entorno instalado, incluida simulación de timeout y una ingesta de dos filas sintéticas con cuarentena y repetición idéntica de hashes de las proyecciones. Pruebas sin red. Log: c0/logs/test_timeout_recovery.log.

## Próxima ejecución humana

Desde /home/jzsalinas/Documents/galaxy-morphology-discovery:

```bash
/home/jzsalinas/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m c0_pipeline.manual_ingest --max-additional-mib 100 --http-timeout-seconds 120
```

Añadir --dry-run permite inspeccionar la configuración sin red. El total declarado mostrado incluye la rueda; la caché verificada evita descargarla otra vez. Transferencia nueva esperada: 40.528.939 bytes (38,65 MiB), únicamente catálogo. Tiempo estimado 2–10 minutos, condicionado por Zenodo. Reservar 1 GiB libre. Entradas: metadata versionada, lock de dependencia y rueda existente. Salidas: proyecciones de cuarentena y resumen de ingesta; no probe ni imágenes.

Log: c0/logs/C0_MANUAL_INGEST.log (se añade a lo existente). Éxito: C0_MANUAL_INGEST_OK, código 0 y C0_MANUAL_STATUS.json actualizado. Fallo: C0_MANUAL_INGEST_FAILED, código 2; detenerse e informar, sin repetir. Reanudación controlada: mismo comando, caché SHA-256 y contadores persistentes.

La ejecución se delega porque AGENTS.md dispone: «operación bulk sobre catálogos, bricks, frames o imágenes». El agente espera confirmación y después inspeccionará los artefactos, sin repetir el proceso.
