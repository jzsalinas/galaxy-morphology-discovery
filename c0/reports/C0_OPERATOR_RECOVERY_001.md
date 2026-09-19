# Recuperación tras interrupción por créditos — operador/soporte

Fecha: 2026-09-17. Inspección offline; ninguna adquisición ni repetición de lotes.

## Estado confirmado

- C0_NORMAL_BATCH_OK permanece íntegro: 36 checkpoints coinciden con el resumen, procedencia vigente y hashes de entradas FITS verificados. SHA-256 del resumen: 65f292baf46feb8016fba25de9ab9295553090b778820e7fb94a94118b9fb5f4.
- Contadores SQLite coinciden con exportación: 465348528 bytes, 383 solicitudes de datos, 936 solicitudes HTTP totales. Ningún contador reiniciado.
- C0_OPERATOR_SUPPORT_PLAN.md existe. C0_NORMAL_CUTOUT_PROTOCOL.md y addendum vinculante mantienen los criterios; no hay nuevos umbrales de aceptación.
- operator_support.py tiene 179 líneas y diez funciones: union, subtract, spline_axis, build_kernel, c_values, geometry, coordinates, descriptor_table, stats, stratify. Es un prototipo parcial: carece de main/CLI, ejecución integrada A/B, checkpoints, inventario final y handoff ejecutable.
- No existen directorios operator_build ni reports/operator_support, ni logs/status/resultados de ese lote. No hay evidencia local de compilación del kernel ni ejecución del diagnóstico nuevo. El texto del plan describe trabajo previsto, no resultados.
- Git sigue sin ser funcional; no se inicializó ni reparó.

## Preservación y comprobaciones nuevas

Se conservaron copias exactas del prototipo y plan en c0/provenance/recovery_operator_001/, con registro de hashes. No se alteró el prototipo ni los resultados anteriores.

Sintaxis Python válida. Comprobaciones sintéticas mínimas de unión/resta de intervalos y reproducción de polinomios hasta grado tres por la spline local pasaron; log C0_OPERATOR_RECOVERY_CHECKS.log. No son validación del kernel C, de SciPy/FITPACK, de toda la geometría ni del servicio desplegado. No se repitió la suite completa ni el lote científico.

## Mejor punto de reanudación

1. Completar y probar las funciones de geometría, soporte y validación de descriptores; especialmente límites de archivo/heap, coordenadas, clipping al brick y soporte desconocido. El lector parcial de descriptores todavía necesita controles equivalentes a range_plan.py antes de sustentar costes.
2. Compilar el fragmento C auditado con procedencia explícita y controles sintéticos pequeños. Mantener la spline local como implementación distinta: SciPy no está instalado y una prueba polinómica no certifica FITPACK ni el WCS de astrometry.net. No instalar dependencias ni adquirir código sin nueva autorización de red.
3. Integrar A: variantes prefijadas, máscara común, desgloses de residuales y orden de operaciones. No ajustar parámetros ni umbrales a los resultados. Primero los diez objetos de soporte casi completo, luego ranks 3 y 5.
4. Integrar B: tiles efectivamente necesarios, descriptores comprimidos, resta de rangos presentes, deduplicación y cobertura marginal. Reportar mínimos condicionados a bricks/operador conocidos, solicitudes e intentos restantes; no confundir envolvente con mínimo ni presencia de bricks con exhaustividad del servicio.
5. Crear un único CLI offline reanudable, --help/--dry-run, límites de IO, checkpoints, logs y sentinel; ejecutar solo smoke mínimo y entregar el lote al usuario conforme a AGENTS.md.
6. Revisar los resultados humanos antes de decidir si se justifica una adquisición. No existe todavía un coste incremental mínimo verificado ni un comando de adquisición listo.

C0-C sigue pendiente de evaluación, sin PASS ni equivalencia funcional nueva. No se ha iniciado SDSS, Tractor, nexp, máscaras o PSF. No ejecutar el prototipo como lote: actualmente importarlo/ejecutarlo no realiza las fases A/B y una salida vacía no sería señal de éxito científico.
