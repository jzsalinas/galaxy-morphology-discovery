# Entrega manual 6 — inventario HEAD DR5, sin descargar productos

Desde `/home/jzsalinas/Documents/galaxy-morphology-discovery`:

```bash
c0/.venv/bin/python -m c0_pipeline.manual_resource_inventory --max-metadata-requests 600
```

Entradas: C0_BRICK_ROUTES.parquet (118 bricks asociados a los 96 objetos fijados), documentación de rutas DR5, ledger persistente. No lee imágenes, catálogo Galaxy Zoo ni lockbox.

Plan: 514 recursos únicos — 118 tablas Tractor, 42 imágenes coadd para los doce objetos fijados (algunos cruzan bricks), 354 mapas nexp (g,r,z por brick). Solo HEAD: cero bytes de cuerpos de producto y cero solicitudes de datos no metadata. Las respuestas previas HEAD 200 se reutilizan. Todas las consultas nuevas quedan registradas como metadata. Las rutas `.fits.fz` son candidatas según el patrón observado en el listado oficial del brick smoke; cada existencia se valida por su propia respuesta.

Tiempo estimado: 10–40 minutos, dependiente del servidor; espacio local inferior a 10 MiB. Máximo 600 consultas planificadas, secuenciales, sin reintentos automáticos. Detiene ante HTTP 429 o tres respuestas fallidas consecutivas; no espera throttling ni consume intentos indefinidamente.

Salidas: c0/provenance/C0_DR5_RESOURCE_PLAN.json; C0_DR5_RESOURCE_INVENTORY.json; c0/reports/C0_DR5_RESOURCE_INVENTORY_SUMMARY.json; C0_RESOURCE_INVENTORY_STATUS.json. Log: c0/logs/C0_MANUAL_RESOURCE_INVENTORY.log.

Éxito: C0_RESOURCE_INVENTORY_OK y código 0; un inventario exitoso puede demostrar que no caben los archivos completos. Fallo: C0_RESOURCE_INVENTORY_FAILED, código 2; detenerse e informar. Reanudación, solo tras revisión: mismo comando; reutiliza HEAD satisfactorios del ledger y conserva límites. --help y --dry-run disponibles.

No autoriza descargar esos 514 productos ni implica PASS en Gates. El primer Tractor consultado declara 8893440 bytes: extrapolar sin inventario podría consumir demasiado presupuesto. Tras inspeccionar los tamaños se decidirá una estrategia limitada (archivos completos solo si caben; acceso parcial solo si se valida explícitamente).

33 tests offline pasan. Se delega según AGENTS.md por duración estimada superior a cinco minutos y por consultas cuyo seguimiento interactivo no requiere razonamiento. El agente no ejecutó el inventario completo y espera confirmación para inspeccionar resultados.
