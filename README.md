# bbc-aws-2026
Hackathon Breaking Barriers 2026 · Desafío 1 Fundación Integra. El plan está en `PLAN.md`; las fuentes y sus hallazgos, en `contexto/`, y los servicios AWS de la cuenta, en `docs/investigacion_servicios.md`.

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
| `kimun/registro/contexto.py` | Context processor con el contador de pendientes de la barra de navegación (solo para quien revisa) |
| `kimun/registro/grafico.py` | SVG de la evolución de niveles por núcleo, con tabla equivalente en `_evolucion.html` |
| `kimun/registro/permisos.py` | `cursos_de(usuario)` para ver, `cursos_donde_registra` para capturar y `cursos_que_valida` para revisar y validar: filtro obligatorio en toda vista con datos de un curso. `ninos_de` y `ninos_que_valida` hacen lo mismo para la ficha |
| `kimun/registro/management/commands/cargar_demo.py` | Currículo, semestres y curso de demo con 15 niños ficticios, niveles históricos y unas 40 observaciones aceptadas (fechas contadas desde el día de la carga, o desde `--hoy AAAA-MM-DD`) |
| `kimun/templates/`, `kimun/registro/templates/` | Plantillas base, login, tabla del curso, ficha del niño (`ficha.html` y `_nucleo_ficha.html`, que HTMX reemplaza al fijar un nivel), metas y revisión (`revision.html`; `_tarjeta_revision.html` es lo que HTMX reemplaza en cada acción) |
| `kimun/static/vendor/` | Pico.css y HTMX con versión fija (sin CDN) |
| `kimun/static/registro/registro.css` | Estilos de la ficha y de la revisión (colores de las señales con contraste ≥ 4,5:1) |
| `datos/` | `curriculo_transicion.json` (85 OA, trayectoria por núcleo), `rubrica_integra.json` (rúbrica oficial de Integra, hoy solo IA) y `demo_curso.json` |
| `scripts/extraer_curriculo.py` | Regenera el currículo desde el PDF, que no se versiona: descargarlo desde <https://www.curriculumnacional.cl/614/articles-210511_programa.pdf> a `contexto/programa-pedagogico-transicion-mineduc.pdf` y correr `python -X utf8 scripts/extraer_curriculo.py --todos` (requiere `pdftotext` de Poppler; en Windows, `winget install oschwartz10612.Poppler`) |

La cantidad de niveles (hoy 8) se define en la rúbrica de cada nivel educativo, no en el código: nunca usar un 8 fijo. Para el máximo, usar `Rubrica.nivel_maximo(nivel_educativo)`.

Al agregar campos a los modelos, crear la migración en la misma rama (`python manage.py makemigrations`) para evitar choques entre ramas.

## Task 7: contrato de propuestas (punto 1)

`PropuestaNivel` incorpora los estados `procesando` y `obsoleta`, el inicio y la cantidad de intentos, y la usuaria y fecha de resolución. La base impide dos solicitudes en estado `solicitada` o `procesando` para el mismo niño y núcleo. Una propuesta sin evidencia suficiente debe tener el nivel vacío.

`registro/propuestas.py` prepara una huella SHA-256 de la evidencia aceptada, el nivel de referencia, la rúbrica y la versión del prompt. Guarda también la referencia y la procedencia oficial/provisoria. `comprobar_vigencia` marca como obsoletas las sugerencias listas cuya entrada cambió; no altera decisiones históricas ni niveles validados. La huella no sustituye el reemplazo de nombres por códigos, que corresponde al punto 2. Cuando cambie el contenido del futuro prompt debe actualizarse `VERSION_PROMPT`.

Aplicar con `python manage.py migrate`. La migración `0003` conserva las propuestas anteriores, pero deja obsoletas las solicitudes y sugerencias listas sin huella verificable. No inventa quién resolvió decisiones históricas. Si encuentra niveles incompatibles con la suficiencia de evidencia, detiene la migración y señala los ids que deben revisarse, sin corregirlos automáticamente.

La generación y el proceso de fondo se describen en los puntos 3 y 4 siguientes. Las acciones de decisión desde la ficha corresponden al punto 5. El plan completo está en `docs/plan_task7.md`.

## Task 7: sustitución de nombres (punto 2)

`registro/ia/seudonimo.py` recibe una lista de diccionarios con `nombre`, `codigo` (formato actual `N-XXXXXX` hexadecimal) y `alias` opcionales. `Seudonimizador.texto` sustituye nombres completos, prefijos como «María José» y «María», y alias, sin distinguir mayúsculas o tildes y respetando límites de palabras. Las coincidencias compartidas se reemplazan por `[NINO_AMBIGUO]`. Conserva literalmente el resto del texto y permite repetir la operación sin alterar códigos o marcadores existentes.

`datos` limpia las cadenas de estructuras JSON sin modificar los originales. Rechaza identidades en claves para conservar los campos del contrato. `invocar` limpia el prompt, el mensaje y las descripciones y ejemplos de la herramienta antes de delegar en `ClienteBedrock`; admite mensajes estructurados o JSON serializado y no añade el diccionario de identidades. La integración con la propuesta de nivel corresponde al punto 3.

La coincidencia usa el catálogo conocido del curso: variantes de escritura, otros nombres de uso o apellidos aislados deben declararse como alias. No se deducen por similitud. El módulo no utiliza Django ni registra textos o identidades en logs. La separación de notas de la Task 5 conserva su flujo existente.

## Task 7: generación y validación de propuestas (punto 3)

`registro/propuestas.py` expone `preparar_evidencia(nino, nucleo)` y `generar_propuesta(nino, nucleo, cliente=...)`. Selecciona observaciones aceptadas, individuales, del niño y curso, asociadas directamente al núcleo o mediante sus OA del nivel educativo. Las ordena por fecha e id. El resultado incluye la respuesta validada, la captura de entrada con su huella, el nivel de referencia, la procedencia de la rúbrica y los metadatos del cliente. La huella incluye el contenido del prompt para detectar cambios en el archivo.

El módulo puro `registro/ia/propuesta.py` usa el prompt de `registro/ia/prompts/propuesta.md` y el `Seudonimizador` del punto 2. Para rúbrica oficial envía descriptores y solo el primer ejemplo de cada nivel; para provisoria, el mapeo cargado, trayectoria y conductas NT1/NT2. Una rúbrica incompleta genera `ErrorConfiguracionPropuesta` antes de llamar a Bedrock. No impone una cantidad mínima de observaciones ni obliga a subir el nivel.

La salida exige un nivel entero dentro del máximo dinámico, citas únicas del conjunto enviado, conductas y justificación. Si la evidencia no alcanza, el nivel debe ser `null`; sin observaciones se devuelve esa situación localmente. Los errores de respuesta o servicio se expresan como `ErrorPropuesta` sin incluir citas ni respuestas crudas.

La llamada usa el cliente Bedrock existente, fuera de la transacción que captura la evidencia, y admite un cliente falso. Esta función de generación no guarda propuestas ni niveles. El procesamiento y su persistencia se describen en el punto 4; las decisiones desde la ficha corresponden al punto 5.

## Task 7: solicitudes y proceso de fondo (punto 4)

Aplicar `python manage.py migrate` para instalar `0004_propuesta_procesamiento`. Aceptar una observación solicita propuestas para los núcleos asociados directamente o mediante OA de su nivel educativo. Aceptar todas agrupa por niño y núcleo, y excluye notas grupales y observaciones sin niño o sin destino. La aceptación y sus solicitudes se confirman juntas; un fallo de escritura revierte ambas.

La educadora puede usar **Solicitar propuesta** o **Reintentar propuesta** desde la ficha, con HTMX o navegación normal. Las solicitudes activas se reutilizan, y una sugerencia lista y vigente también se reutiliza. Los errores requieren reintento explícito; el reintento crea una solicitud nueva y conserva el error anterior. Las asistentes, directoras y educadoras ajenas reciben 404 al intentar estas acciones.

Desde `kimun/`, con las variables de Bedrock configuradas en el entorno:

```powershell
# Ejecutar el proceso de fondo en una terminal distinta de runserver.
.\.venv\Scripts\python.exe manage.py procesar_propuestas

# Procesar como máximo una solicitud y terminar.
.\.venv\Scripts\python.exe manage.py procesar_propuestas --once
```

El proceso comprueba la cola cada 2 segundos cuando está vacía (`--intervalo`, mayor que 0 y hasta 60). Una actualización condicional toma cada trabajo; la generación ocurre fuera de la transacción. Un token por intento impide que un proceso anterior sobrescriba el resultado de otro. Al guardar se comprueba otra vez la huella: si la evidencia, la rúbrica o el nivel de referencia cambiaron, el resultado queda obsoleto y se solicita otro. Los resultados listos conservan nivel, suficiencia, justificación, conductas, observaciones citadas, modelo y métricas. Los errores guardados son mensajes genéricos sin citas ni respuestas crudas.

Los trabajos sin terminar se recuperan después de 300 segundos (`--caducidad`, mínimo 120), en lotes de hasta 100 por ciclo. Cada solicitud admite hasta tres intentos de procesamiento en total antes de quedar en error. El plazo debe superar la duración máxima configurada para la llamada al modelo; un intento anterior que siguiera vivo pierde la capacidad de publicar, aunque la llamada remota ya estuviera en curso. El modo `--once` también recupera vencidos antes de tomar un trabajo.

En despliegue, ejecutar este comando como un proceso supervisado junto al servidor web, usando el mismo entorno, base y permisos de Bedrock. El futuro proceso común de capturas puede reutilizar `procesar_siguiente`. La presentación y las decisiones de nivel se describen en el punto 5. Procesar una propuesta nunca crea un `NivelValidado`.

## Task 7: decisión en la ficha (punto 5)

Aplicar `python manage.py migrate` para instalar `0005_propuesta_decision`. La ficha muestra la última propuesta de cada núcleo con nivel y nombre, justificación, conductas y enlaces a las observaciones citadas. La etiqueta de rúbrica provisoria corresponde a la usada al generar la propuesta. Cada observación tiene un ancla única por núcleo, incluso cuando aporta evidencia a varios núcleos.

Solo la educadora del curso puede decidir mediante POST con CSRF:

- **Aceptar propuesta**: valida el nivel sugerido y enlaza el nuevo registro del historial con la propuesta.
- **Fijar otro nivel**: usa el formulario de niveles del 1 al máximo dinámico y admite un comentario. La propuesta conserva su nivel original y pasa a `ajustada`; el historial conserva el nivel elegido por la educadora.
- **Rechazar propuesta**: registra la decisión y conserva el nivel validado actual.

La decisión, usuaria, fecha y nuevo historial se guardan juntos. Repetir la misma decisión no crea otro nivel ni reescribe su autoría. Una restricción de la base permite como máximo un `NivelValidado` ligado a cada propuesta. La migración se detiene e identifica los ids afectados si encuentra varias validaciones previas; conserva esos registros para revisión.

Antes de validar se comprueba que la propuesta esté lista, tenga evidencia suficiente y mantenga su huella y citas válidas para ese niño y núcleo. Si cambió la entrada, queda obsoleta y se pide solicitar otra. Las propuestas sin evidencia suficiente muestran qué falta observar y no ofrecen aceptación o ajuste. El formulario manual independiente sigue disponible y deja obsoletas las sugerencias basadas en el nivel anterior. Los trabajos pendientes o en ejecución usan la comprobación de vigencia del procesador.

Con HTMX, el panel consulta el estado cada tres segundos solo mientras está en cola o generándose y se detiene al terminar. Se actualiza únicamente el panel para conservar cualquier edición del formulario manual. Aceptar o ajustar actualiza la sección del núcleo con historial y señales; la tabla del curso usa los mismos cálculos al cargarla. Sin JavaScript se puede actualizar el estado mediante el enlace de la ficha y decidir mediante formularios normales.

Para verificar el recorrido: aceptar observaciones pendientes, ejecutar el proceso del punto 4, abrir la ficha como educadora, revisar las citas y decidir. Las pruebas de integración usan un cliente falso; una comprobación con Bedrock real y la revisión visual final corresponden al cierre del punto 6.
