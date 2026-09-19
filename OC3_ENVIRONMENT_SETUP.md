# OC-3 — preparación humana de un entorno independiente

Fecha: 2026-09-18. **Preparación documental solamente. Ningún comando de instalación, creación de entorno o replay mostrado aquí se ejecutó en esta tarea.** OC-3 permanece NOT STARTED. El preflight y sus otros bloqueos están definidos en `OC3_EXECUTION_PREFLIGHT_SPEC.md`; completar este documento no habilita por sí solo metadata, auxiliares ni ciencia.

## 1. Versiones verificadas documentalmente y aislamiento

| Componente | Requisito | Evidencia histórica |
|---|---|---|
| Python | 3.12.x; registrar patch/build exactos | 3.12.14 en la verificación original |
| NumPy | **2.5.3** | requirements.lock y reporte coinciden |
| Astropy | **8.0.1** | requirements.lock y reporte coinciden |
| PyArrow | **25.0.1** | requirements.lock y reporte coinciden |

SHA-256 de `oc3/requirements.lock`: `79228cc4d2577f7bd2d127db4d9e78a3cf1224736a8736610933f363af16205d`.
SHA-256 del informe histórico: `bd3c3c2f30c346c8514de6056311cfdd84b61efb7bfa23cc8537ad226460b864`.
SHA-256 del log histórico de 100 pruebas: `3551c4977367da87bbfd143033b7960f329b98405513010fbbba68d4e76fd4f8`.

No se cambia ninguna versión para resolver una incompatibilidad de instalación. Si el índice revisado no ofrece esos pins para Python/plataforma, o una dependencia es incompatible, corresponde PREFLIGHT_BLOCKED_ENVIRONMENT; no escoger otra versión, compilar silenciosamente, activar system-site-packages ni usar C0. Otro patch 3.12 requiere registro y replay completo; no se promete identidad binaria entre builds.

El entorno de producción será `/home/jzsalinas/Documents/galaxy-morphology-discovery/oc3/.venv`, creado desde un Python base independiente. **Prohibido usar, copiar o enlazar `c0/.venv` para producción**, incluidos site-packages, binarios, activación o fallback. Su uso anterior fue un préstamo de intérprete de solo lectura para fixtures sintéticos; no acredita aislamiento operativo. Separar OC-3 evita alterar C0 y permite fijar dependencias/procedencia propias. No se requiere volver a ejecutar C0 ni reexaminar sus datos.

## 2. Qué falta en el lock actual

El lock contiene tres pins directos y el comentario de Python histórico. No es un lock de instalación completo con hashes. Faltan:

- pins exactos de todas las dependencias transitivas;
- versión fijada del instalador pip y herramientas empaquetadoras;
- hashes y nombres de los wheels efectivos, su índice/origen y tags de plataforma/ABI;
- distribución/build/binario exactos de Python, sistema/libc y librerías numéricas nativas.

Por tanto, `pip install -r` prepara un **entorno candidato**, no reproduce bit a bit el entorno C0 histórico ni garantiza otra instalación idéntica en el futuro. No se inventan hashes de PyPI ni se afirma haber verificado disponibilidad online. La instalación humana debe registrar su reporte de descarga, todas las versiones efectivas y los hashes locales; el entorno resultante se revisa y fija antes de replay/uso. Reinstalación reproducible posterior requerirá además un lock transitivo con hashes y wheels revisados o un archivo del entorno/imagen compatible. Este documento no crea ni sustituye ese lock.

El fingerprint de abajo acredita el estado instalado inspeccionado, no sustituye la procedencia de los wheels ni demuestra su confianza. No actualizar pip o paquetes entre fingerprint, tests y futura ejecución. Una actualización invalida ese replay y exige revisión/repetición explícita, no continuación silenciosa.

## 3. Handoff humano y reglas generales

Ejecutar los pasos de uno en uno desde:

```bash
cd /home/jzsalinas/Documents/galaxy-morphology-discovery
```

Todos los comandos siguientes son **HUMAN EXECUTION / NOT EXECUTED** por el agente. Solo el paso 3 de instalación puede contactar repositorios de paquetes; ningún paso debe contactar un survey. No ejecutar todavía ningún comando científico ni `plan --resolve-metadata`, aunque aparezca en documentación histórica.

Estimaciones no medidas para este host: creación <1 minuto; instalación 1–10 minutos y aproximadamente 100–500 MiB de transferencia según wheels transitivos; entorno/logs aproximadamente 0.3–1.5 GiB; fingerprint 1–5 minutos según disco; replay aproximadamente 10–60 segundos, históricamente 10.96 s en el otro entorno; dry-run segundos. Cualquier duración mayor, descarga >250 MiB o IO >1 GiB sigue siendo ejecución humana según AGENTS. No hay instalación en background ni polling del agente.

Salidas futuras de preparación: `oc3/.venv` y `oc3/environment_setup/` (logs, install report, versiones/fingerprint y resultados nuevos). Esos archivos **no existen por esta entrega** y no son evidencia de survey. No sobrescribir `oc3/tests/SYNTHETIC_TEST_RESULTS.*` ni `oc3/provenance/OC3_ENVIRONMENT.json`: los primeros son históricos y el último lo crea la futura corrida científica.

El RuntimeGuard actual suma el espacio bajo `oc3`, incluyendo entorno/logs, para su tope de disco de 4 GiB. Antes de producción hay que medir y presupuestar ese footprint; no suponer que queda excluido. La transferencia de paquetes se registra como provisioning, separada del tráfico survey, sin ampliar topes OC-3.

No encadenar pasos después de un fallo. Los bloques usan subshell/set -eu o excepciones para no imprimir éxito tras un error. Conservar logs/parciales; no eliminar automáticamente un entorno existente para reiniciar. Si ya existe uno, inspeccionarlo en una tarea posterior y reanudar únicamente el paso fallido cuando sea seguro. Un sentinel de entorno no es PREFLIGHT_READY_FOR_METADATA_RESOLUTION.

### Paso 1 — primer comando humano: comprobar Python base disponible

No instala nada ni crea archivos:

```bash
python3.12 --version
```

Esperado: exit 0 y `Python 3.12.x`. Command-not-found o versión distinta: detener con PREFLIGHT_BLOCKED_ENVIRONMENT y comunicar salida. Esta comprobación solo acredita disponibilidad; el paso 2 verifica explícitamente que sea un intérprete base independiente antes de crear el entorno. No usar la ruta de C0 como sustituto ni instalar Python automáticamente. Este es el primer comando que debe ejecutar el humano al recibir el handoff.

### Paso 2 — crear entorno independiente, sin red

Solo después del paso 1 correcto:

```bash
(
set -eu
python3.12 -I -B -c 'import sys; from pathlib import Path; assert sys.version_info[:2] == (3,12) and sys.prefix == sys.base_prefix; assert not Path(sys.executable).resolve().is_relative_to(Path("c0").resolve()); assert not Path("oc3/.venv").exists() and not Path("oc3/.venv").is_symlink(), "Existing environment: preserve and review"'
mkdir -p oc3/environment_setup
python3.12 -I -B -m venv --copies oc3/.venv
oc3/.venv/bin/python -I -B -c 'import sys; from pathlib import Path; p=Path("oc3/.venv"); assert not p.is_symlink(); assert Path(sys.prefix).resolve()==p.resolve(); assert sys.prefix!=sys.base_prefix; assert "include-system-site-packages = false" in (p/"pyvenv.cfg").read_text().lower(); print("OC3_ENVIRONMENT_CREATED")'
)
```

Se usa ensurepip local de la distribución Python; no `--upgrade-deps`, no `--system-site-packages`, no copia ni symlink de C0. Si falta venv/ensurepip o el Python base no es utilizable, parar y conservar el directorio parcial para revisión; no caer a pip global. Repetir el bloque sobre un entorno existente se rechaza deliberadamente, no se borra evidencia.

### Paso 3 — instalar los pins revisados

**HUMAN EXECUTION / NETWORK TO PACKAGE INDEX / NOT EXECUTED.** Requiere que el humano acepte la preparación de paquetes; no autoriza red survey. Se fuerza wheels binarios para evitar compilación/build-dependencies implícitos. No se actualiza pip automáticamente.

```bash
(
set -eu
oc3/.venv/bin/python -I -B -c 'import hashlib; from pathlib import Path; assert hashlib.sha256(Path("oc3/requirements.lock").read_bytes()).hexdigest()=="79228cc4d2577f7bd2d127db4d9e78a3cf1224736a8736610933f363af16205d"'
test ! -e oc3/environment_setup/install.log
test ! -e oc3/environment_setup/install-report.json
if oc3/.venv/bin/python -I -B -m pip --isolated --disable-pip-version-check --retries 0 --timeout 30 install --only-binary=:all: --no-cache-dir --index-url https://pypi.org/simple --report oc3/environment_setup/install-report.json -r oc3/requirements.lock > oc3/environment_setup/install.log 2>&1; then
  printf '%s\n' 'OC3_ENVIRONMENT_PACKAGES_INSTALLED'
else
  printf '%s\n' 'OC3_ENVIRONMENT_INSTALL_FAILED; inspect oc3/environment_setup/install.log'
  exit 1
fi
)
```

Entradas: lock revisado e intérprete independiente. Salidas: paquetes en .venv, log completo e install-report con URLs/hashes/versiones resueltos. El reporte debe revisarse para el origen de todas las dependencias y sus hashes; no aceptar una fuente adicional desconocida. Cualquier pin no disponible, ausencia de wheel compatible, error TLS, conflicto o instalación parcial implica fallo, no una licencia para quitar el pin o usar otro índice. El lock incompleto no se usa con `--require-hashes` fingiendo que contiene hashes.

Reanudación tras fallo: conservar log/reporte y revisar el estado del entorno. El bloque no los sobreescribe; una repetición necesita nombres de intento nuevos explícitamente acordados y el mismo lock. No ejecutar bucles de reintento. El entorno parcial no es válido hasta que pip check, verificación de versiones, fingerprint y replay hayan terminado.

### Paso 4 — verificar dependencias y registrar el entorno

**Offline.** Primero consistencia de paquetes:

```bash
(
set -eu
test ! -e oc3/environment_setup/pip-check.log
oc3/.venv/bin/python -I -B -m pip --isolated --disable-pip-version-check check > oc3/environment_setup/pip-check.log 2>&1
printf '%s\n' 'OC3_DEPENDENCY_CHECK_OK'
)
```

Después verificar lo realmente importado y capturar un fingerprint con rutas relativas y SHA-256 de archivos instalados. Este paso puede leer cientos de MiB; permanece manual. No utiliza C0 ni importa el pipeline científico.

```bash
oc3/.venv/bin/python -I -B - <<'PY'
import contextlib, hashlib, importlib, importlib.metadata, io, json, os
import platform, sys, sysconfig
from datetime import datetime, timezone
from pathlib import Path

base = Path.cwd().resolve()
assert base == Path('/home/jzsalinas/Documents/galaxy-morphology-discovery')
venv = base / 'oc3/.venv'
assert not venv.is_symlink()
assert Path(sys.prefix).resolve() == venv.resolve()
assert sys.prefix != sys.base_prefix and sys.version_info[:2] == (3, 12)
assert not Path(sys.base_prefix).resolve().is_relative_to(base / 'c0')
assert 'include-system-site-packages = false' in (venv / 'pyvenv.cfg').read_text().lower()
assert not any(Path(p).resolve().is_relative_to(base / 'c0') for p in sys.path if p)
threads = ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
           'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')
for key in threads:
    os.environ[key] = '1'
expected = {'numpy': '2.5.3', 'astropy': '8.0.1', 'pyarrow': '25.0.1'}
imports = {}
for name, version in expected.items():
    module = importlib.import_module(name)
    location = Path(module.__file__).resolve()
    assert module.__version__ == version
    assert importlib.metadata.version(name) == version
    assert location.is_relative_to(venv), 'Dependency outside independent environment'
    imports[name] = {'version': version, 'path': str(location)}

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')

files = {}
for path in sorted(venv.rglob('*')):
    if '__pycache__' in path.parts or path.suffix == '.pyc':
        continue
    rel = str(path.relative_to(venv))
    if path.is_symlink():
        target = path.resolve()
        assert not target.is_relative_to(base / 'c0'), 'C0 link forbidden'
        files[rel] = {'symlink': os.readlink(path),
                      'target_sha256': sha(target) if target.is_file() else None}
    elif path.is_file():
        files[rel] = {'size': path.stat().st_size, 'sha256': sha(path)}

packages = []
for distribution in importlib.metadata.distributions():
    assert Path(distribution.locate_file('')).resolve().is_relative_to(venv)
    packages.append({'name': distribution.metadata['Name'], 'version': distribution.version})
packages.sort(key=lambda item: (item['name'].lower(), item['version']))
config = io.StringIO()
with contextlib.redirect_stdout(config):
    importlib.import_module('numpy').show_config()
root = base / 'oc3/environment_setup'
report = root / 'install-report.json'
assert report.is_file(), 'Missing reviewed installation provenance'
state = {'python': sys.version, 'executable': sys.executable,
         'executable_sha256': sha(Path(sys.executable)),
         'base_prefix': sys.base_prefix, 'platform': platform.platform(),
         'machine': platform.machine(), 'libc': platform.libc_ver(),
         'SOABI': sysconfig.get_config_var('SOABI'), 'imports': imports,
         'packages': packages, 'threads': {k: os.environ[k] for k in threads},
         'gpu': False, 'numpy_config': config.getvalue(),
         'requirements_sha256': sha(base / 'oc3/requirements.lock'),
         'install_report_sha256': sha(report), 'installed_files': files,
         'bytecode_excluded': True}
fingerprint = hashlib.sha256(canonical(state)).hexdigest()
record = {'recorded_utc': datetime.now(timezone.utc).isoformat(),
          'environment_sha256': fingerprint, 'state': state,
          'scope': 'ENVIRONMENT_PREPARATION_ONLY_NOT_SURVEY_EVIDENCE'}
out = root / 'ENVIRONMENT.json'
with out.open('xb') as stream:
    stream.write(canonical(record) + b'\n')
print('OC3_ENVIRONMENT_VERSIONS_OK; environment_sha256=' + fingerprint)
PY
```

Se excluyen caches .pyc del fingerprint de contenido, y se usa -B para evitar crearlos durante verificación. El fingerprint incluye fuentes/extensiones/binarios presentes y enlaces, no es un hash universal de toda la máquina ni una prueba de reproducibilidad entre arquitecturas. UTC está fuera del contenido fingerprint; el SHA-256 de ENVIRONMENT.json completo se registra además en el recibo final. Cambios posteriores requieren un registro nuevo/revisión, nunca sobrescribir este mediante `w`.

Antes de producción, la futura `OC3_ENVIRONMENT.json` de la corrida debe enlazar este fingerprint/recibo o una referencia externa inmutable revisada. **Limitación actual:** `workflow.environment()` registra versiones/plataforma/thread flags, pero no verifica por sí mismo el lock completo ni enlaza este fingerprint; el control de preflight debe imponerlo antes de llamar al harness. No se modifica esa función en esta tarea.

### Paso 5 — replay independiente de las 100 pruebas sintéticas

Se usa el runner que bloquea sockets/DNS antes de importar tests. Se permite su prueba de funciones con fixtures temporales; no equivale a invocar los subcomandos científicos contra el estado de producción. No se cambia código, thresholds ni el resultado histórico para conseguir pasar.

```bash
(
set -eu
test -f oc3/environment_setup/ENVIRONMENT.json
test ! -e oc3/environment_setup/synthetic-tests.log
oc3/.venv/bin/python -I -B oc3/tests/run_tests.py > oc3/environment_setup/synthetic-tests.log 2>&1
oc3/.venv/bin/python -I -B - <<'PY'
import json
from pathlib import Path
path = Path('oc3/environment_setup/synthetic-tests.log')
result = json.loads(path.read_text().splitlines()[-1])
assert result['tests'] == result['passed'] == 100
assert result['failed'] == result['skipped'] == result['real_network_requests'] == 0
assert result['synthetic_only'] is True
with Path('oc3/environment_setup/synthetic-tests.json').open('x') as stream:
    json.dump(result, stream, indent=2)
    stream.write('\n')
print('OC3_SYNTHETIC_TESTS_OK; passed=100; failed=0; skipped=0; real_network_requests=0')
PY
)
```

Esperado: exit 0 y sentinel anterior. Cualquier fallo/skip/diferencia del RNG dorado bloquea el entorno. No modificar golden values para eludirlo. No reducir permutaciones. Conservar todo el log y comunicar el error, sin volver al intérprete de C0. Si un futuro cambio de implementación aumenta el inventario de tests, deberá revisarse explícitamente este recibo; hoy se verifica el conjunto histórico exacto de 100.

### Paso 6 — dry-run seguro y recibo de preparación

Se usa -E -s, no -I, para que el script CLI conserve su directorio local `oc3` en sys.path y encuentre `oc3lib`; se ignoran variables PYTHON* y user-site. El intérprete sigue siendo el de .venv. El runner del paso anterior sí soporta -I porque añade explícitamente su ruta de módulos.

```bash
(
set -eu
test ! -e oc3/environment_setup/dry-run.json
oc3/.venv/bin/python -B -E -s oc3/oc3_pilot.py plan --spec OC3_DR9_COADD_BOUNDED_PILOT_SPEC.md --inputs oc3/INPUTS/OC3_INPUT_MANIFEST.json --dry-run --offline > oc3/environment_setup/dry-run.json
oc3/.venv/bin/python -I -B - <<'PY'
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
root = Path('oc3/environment_setup')
dry = json.loads((root / 'dry-run.json').read_text())
assert dry['status'] == 'OC3_DRY_RUN_OK'
assert dry['authorities_verified'] is True
assert dry['network'] is False and dry['evidence_mutation'] is False
assert dry['scientific_execution'] == 'NOT_STARTED'
assert dry['dependencies'] == {'numpy': '2.5.3', 'astropy': '8.0.1', 'pyarrow': '25.0.1'}
names = ['ENVIRONMENT.json', 'install-report.json', 'install.log', 'pip-check.log',
         'synthetic-tests.log', 'synthetic-tests.json', 'dry-run.json']
receipt = {'utc': datetime.now(timezone.utc).isoformat(),
           'files': {name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in names},
           'meaning': 'ENVIRONMENT_PREPARATION_ONLY', 'oc3_scientific_execution': 'NOT_STARTED',
           'preflight_ready_assigned': False}
with (root / 'PREPARATION_RECEIPT.json').open('x') as stream:
    json.dump(receipt, stream, sort_keys=True, indent=2)
    stream.write('\n')
print('OC3_ENVIRONMENT_PREPARATION_OK; OC3_NOT_STARTED; PREFLIGHT_READINESS_NOT_ASSIGNED')
PY
)
```

Esperado: exit 0, dependencies correctas y sentinel de preparación. `missing_inputs` seguirá incluyendo el input final ausente; no se crea para silenciar el aviso. El archivo dry-run.json es un log de preparación, no una evidencia científica. No se llama a plan sin --dry-run.

**Detenerse después de este recibo y comunicar resultados.** El agente deberá inspeccionar los archivos producidos, sin repetir procesos exitosos. Incluso con entorno verificado persiste el bloqueo de arranque metadata/allowlist/binding y límites por etapa descrito en el preflight. No continuar con ningún comando de red survey ni habilitar acquire-aux por tener un sentinel de software.

## 4. Evidencia de cierre necesaria y estado actual

La revisión posterior comprobará rutas reales, pins importados, build Python, transitivas, procedencia/hash de instalación, fingerprint, pip check, 100 tests y dry-run. Comparará autoridades y preservación del repositorio y comprobará que los directorios científicos continúan vacíos. No se promueve automáticamente a READY leyendo el recibo: se aplican los cuatro estados y requisitos A–H de la especificación preflight.

En esta entrega: no entorno creado, no paquete instalado, no replay nuevo, no solicitud de red a paquetes o surveys. Solo se escribió este documento y `OC3_EXECUTION_PREFLIGHT_SPEC.md`; ningún archivo de implementación/documentación anterior fue modificado. Los cinco hashes de autoridad se verificaron; los tests anteriores permanecen evidencia histórica de 100/0/0.

**OC-3 REMAINS NOT STARTED.** No se adquirieron datos astronómicos ni píxeles. No se seleccionó ningún brick DR9, no se selló manifiesto de producción y no se asignó desenlace observacional A/B/C/D.
