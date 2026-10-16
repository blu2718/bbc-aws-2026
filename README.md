<img src="kimun/static/registro/img/logo.svg" alt="Logo: araucaria con dos niños" width="120">

# bbc-aws-2026
Hackathon Breaking Barriers 2026 · Desafío 1 Fundación Integra. El plan está en `PLAN.md`; las fuentes y sus hallazgos, en `contexto/`, y los servicios AWS de la cuenta, en `docs/investigacion_servicios.md`.

Para entender el dominio, empezar por los resúmenes de `contexto/`: `resumen-politica-calidad.md` (la Política de Calidad Educativa de Integra, el faro del proyecto) y `resumen-bases-curriculares.md` (la malla curricular). Las versiones completas, pensadas para agentes, son `guia-politica-calidad.md` y `enciclopedia-bases-curriculares.md`.

La app web (Django) vive en `kimun/`. Los datos compartidos (`datos/`) y los scripts (`scripts/`) quedan en la raíz.

## Desarrollo local

Requiere Python 3.12. Todos los comandos se corren dentro de `kimun/`.

```powershell
cd kimun
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # en Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python manage.py migrate
python manage.py cargar_demo          # muestra las contraseñas de "educadora" y "asistente" la primera vez
python manage.py runserver
```

Si Windows bloquea `Activate.ps1` ("la ejecución de scripts está deshabilitada"), ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, o usa `.\.venv\Scripts\python.exe` en lugar de `python`.

Abrir http://127.0.0.1:8000 y entrar como `educadora` (revisa y valida) o `asistente` (solo registra). Para el panel de administración, crear un usuario con `python manage.py createsuperuser` y entrar en `/admin/`. Ahí se cambia la cantidad de niveles de la rúbrica (Rúbricas) y se asigna la directora de un jardín.

`cargar_demo` se puede correr varias veces sin duplicar datos. Para fijar la contraseña, define `DEMO_PASSWORD` antes de correrlo y usa `--cambiar-password` si la usuaria ya existe.

Variables de entorno: ver `kimun/.env.example`.

## Medición de calidad (Task 10)

`manage.py evaluar` corre el set `datos/eval/notas_separacion.json` contra Bedrock real y muestra una tabla con niños bien asignados, precisión y cobertura de núcleos y OA, nivel de apoyo, fecha, interpretación, segundos, tokens y costo por nota. No usa la base de datos. Requiere las credenciales del workshop en el entorno (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` y `AWS_SESSION_TOKEN`, desde el panel del evento).

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; $env:PYTHONUTF8 = "1"   # tildes bien en la consola de Windows
.\.venv\Scripts\python.exe manage.py evaluar                  # BEDROCK_MODEL_ID o Sonnet 5, las 20 notas
.\.venv\Scripts\python.exe manage.py evaluar --modelo sonnet --modelo haiku   # comparación lado a lado
.\.venv\Scripts\python.exe manage.py evaluar --ids n04 n15 --detalle          # qué no calzó, nota por nota
.\.venv\Scripts\python.exe manage.py evaluar --json $env:TEMP\eval.json       # guarda lo obtenido (fuera del repo)
```

Audios (Task 9): `manage.py generar_audios` crea con Polly `datos/eval/audios/<id>.mp3`, uno por nota, rotando las 4 voces es-US (usa `texto_audio`, la nota como se dictaría, si la nota lo trae). Ya están versionados; solo hace falta volver a generarlos si cambia el set (`--forzar`). Después, `manage.py evaluar --fuente audio` transcribe cada audio con Transcribe y el vocabulario de nombres del curso (`kimun-eval-*`), y mide lo mismo que con texto más el error de palabras de la transcripción. Requiere `KIMUN_BUCKET` (salida `NombreBucket` del stack `kimun-mvp`) o `--bucket`. La primera vez el vocabulario tarda unos minutos en quedar listo y esa corrida va sin él.

Cómo se cuenta, en `kimun/registro/evaluacion.py`: una observación que falta resta en niños y en cobertura; una de más, en precisión; dejar sin niño un nombre ambiguo o desconocido (las dos Sofías, Abel) es lo correcto. Cada observación esperada trae en `nino` el niño que debe quedar asignado. La propuesta de nivel (Task 7) y las fotos (Task 8) se suman cuando existan; `casos_propuesta_ia` ya arma los 8 casos con el segundo ejemplo de cada nivel de IA (el que el prompt de la Task 7 no debe mostrar).

## Tests

Dentro de `kimun/`, en una sola terminal y una sola corrida a la vez:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --durations=10
```

La suite completa tarda menos de 1 minuto. Para iterar, corre solo el archivo que cambiaste (`pytest registro/tests/test_alertas.py`) y deja la suite completa para el final.

Por qué se demoraban (15-10-2026) y cómo evitarlo:

- Se lanzaban varias corridas de pytest y varios `Start-Sleep` en la misma terminal. Quedaban en cola y cada comando esperaba a los anteriores, así que parecía que los tests se colgaban. No lances una corrida nueva mientras otra sigue viva, no uses `sleep` para esperar y, si una terminal quedó tomada, ciérrala y revisa que no queden procesos (`Get-Process python`).
- `cargar_demo` tarda unos 2 s, y cada test de `test_cargar_demo.py` lo corría completo. Ahora corre una vez por módulo (fixture `_demo_del_modulo`, dentro de una transacción que se deshace al final), y cada test trabaja en un savepoint que también se deshace. Los tests nuevos que necesiten la demo deben usar el fixture `cargada`, no volver a llamar `cargar_demo` salvo que prueben justamente la recarga.
- `--durations=10` muestra los tests más lentos. Si uno pasa de ~2 s, revisa si repite una carga pesada (currículo, demo) que se pueda compartir. `test_rubrica_integra.py` todavía recarga el currículo en cada test.
- Si rediriges la salida a un archivo (`> salida.txt`), Python la escribe por bloques y el archivo se ve vacío hasta el final. Para ver el avance, usa `Tee-Object` o corre sin redirigir. Borra el archivo después.

## Estructura

| Ruta | Contenido |
|---|---|
| `kimun/config/` | Configuración de Django (todo lo variable se lee del entorno) |
| `kimun/registro/models.py` | Todas las entidades del plan, con sus restricciones |
| `kimun/registro/curriculo.py`, `kimun/registro/rubrica.py` | Carga del currículo de Transición y rúbrica provisoria 8×8 |
| `kimun/registro/alertas.py` | Semestre de permanencia, nivel esperado, brechas con pares y con lo esperado, datos desactualizados y distribución del curso (funciones puras; `tabla_del_curso` es la única que consulta) |
| `kimun/registro/cobertura.py` | Cobertura de evidencia por OA de cada niño y resumen de la quincena del curso |
| `kimun/registro/ficha.py` | Datos de la ficha del niño por núcleo: rúbrica del nivel actual y del siguiente, evolución, cobertura por OA, observaciones y situación frente al curso (sale de `alertas.tabla_del_curso`) |
| `kimun/registro/forms.py` | `FijarNivelForm` (niveles del 1 al máximo de la rúbrica) y `MetasForm` (nivel esperado por semestre de permanencia) |
| `kimun/registro/revision.py`, `kimun/registro/views_revision.py` | Revisión de observaciones pendientes (Task 6): agrupar por captura, aceptar, editar, descartar, asignar niño y "aceptar todas". Solo la educadora del curso; las vistas responden a HTMX y también sin JavaScript |
| `kimun/registro/views_captura.py`, `kimun/registro/forms_captura.py` | Pantalla de registro (`capturar`): nota escrita (Task 5), foto (Task 8) y audio (Task 9), con la lista de las últimas capturas. Las fotos y los audios no se muestran en ninguna parte y `/media/` no se sirve |
| `kimun/registro/procesamiento.py`, `kimun/registro/lectura.py` | Proceso de fondo (`manage.py procesar_capturas`): `texto_para_separar` lee la foto con Claude o transcribe el audio con Transcribe, guarda el texto en `texto_extraido` y borra el archivo (S3 o disco); luego se separa, se emparejan los nombres (`coincidencia.py`) y se crean las observaciones pendientes. El archivo solo queda guardado mientras espera ser leído o si la lectura falló y se puede reintentar |
| `kimun/registro/ia/` | Cliente de Bedrock (`bedrock.py`, texto e imágenes), separación en observaciones (`separacion.py`), lectura de fotos (`foto.py`) y transcripción de audios (`transcripcion.py`, que borra del bucket su copia del audio y la salida de Transcribe), con sus prompts en `prompts/`. Sin Django |
| `kimun/static/registro/captura_foto.js`, `kimun/static/registro/grabar.js` | Achica la foto en el teléfono (1600 px, JPEG) antes de subirla; graba el audio con MediaRecorder (máximo 2 minutos) |
| `kimun/registro/contexto.py` | Context processor con el contador de pendientes de la barra de navegación (solo para quien revisa) |
| `kimun/registro/grafico.py` | SVG de la evolución de niveles por núcleo, con tabla equivalente en `_evolucion.html` |
| `kimun/registro/permisos.py` | `cursos_de(usuario)` para ver, `cursos_donde_registra` para capturar y `cursos_que_valida` para revisar y validar: filtro obligatorio en toda vista con datos de un curso. `ninos_de` y `ninos_que_valida` hacen lo mismo para la ficha |
| `kimun/registro/management/commands/cargar_demo.py` | Currículo, semestres y curso de demo con 15 niños ficticios, niveles históricos y unas 40 observaciones aceptadas (fechas contadas desde el día de la carga, o desde `--hoy AAAA-MM-DD`) |
| `kimun/registro/evaluacion.py`, `kimun/registro/management/commands/evaluar.py`, `generar_audios.py` | Métricas de calidad de la IA (Task 10): funciones puras, el comando que las corre contra Bedrock (y Transcribe, con `--fuente audio`) con el set de `datos/eval/`, y la generación de los audios de prueba con Polly |
| `kimun/templates/`, `kimun/registro/templates/` | Plantillas base, login, tabla del curso, ficha del niño (`ficha.html` y `_nucleo_ficha.html`, que HTMX reemplaza al fijar un nivel), metas y revisión (`revision.html`; `_tarjeta_revision.html` es lo que HTMX reemplaza en cada acción) |
| `kimun/static/vendor/` | Pico.css y HTMX con versión fija (sin CDN) |
| `kimun/static/registro/registro.css` | Estilos de toda la app sobre Pico: los colores del logo de Integra en pastel (azul, rojo, verde, amarillo y gris), con texto de contraste ≥ 4,5:1 en modo claro y oscuro |
| `kimun/static/registro/img/` | Logo de Kimün (`logo.svg`, `logo-512.png`) y favicons, sacados de `docs/marca/logo-kimun.pdf` con el fondo cambiado a `#579bce` (azul de Integra suavizado; las siluetas blancas quedan a 3:1) |
| `docs/marca/` | Originales de marca: `logo-kimun.pdf` (Canva) y `logo-integra.jpg`, del que sale la paleta |
| `datos/` | `curriculo_transicion.json` (85 OA, trayectoria por núcleo), `rubrica_integra.json` (rúbrica oficial de Integra, hoy solo IA) y `demo_curso.json`. En `eval/`, las notas (`notas_separacion.json`) y los post-its (`postits_fotos.json`) de prueba; las fotos van en `eval/fotos/<id>.jpg`, sin versionar |
| `scripts/probar_separacion.py`, `scripts/probar_foto.py` | Prueban la separación y la lectura de fotos contra Bedrock real y comparan con el set de `datos/eval/` |
| `scripts/extraer_curriculo.py` | Regenera el currículo desde el PDF, que no se versiona: descargarlo desde <https://www.curriculumnacional.cl/614/articles-210511_programa.pdf> a `contexto/programa-pedagogico-transicion-mineduc.pdf` y correr `python -X utf8 scripts/extraer_curriculo.py --todos` (requiere `pdftotext` de Poppler; en Windows, `winget install oschwartz10612.Poppler`) |

La cantidad de niveles (hoy 8) se define en la rúbrica de cada nivel educativo, no en el código: nunca usar un 8 fijo. Para el máximo, usar `Rubrica.nivel_maximo(nivel_educativo)`.

Al agregar campos a los modelos, crear la migración en la misma rama (`python manage.py makemigrations`) para evitar choques entre ramas.
