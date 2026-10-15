# Requirements Document

Ficha del niño, validación manual y tabla de metas (Task 3).

## Introduction

La Task 3 cierra el flujo sin IA. La educadora abre la ficha de un niño y ve, por núcleo, su nivel actual, qué dice la rúbrica de ese nivel y del siguiente, la evolución, la evidencia por OA y las observaciones aceptadas. Desde la ficha fija un nivel con un comentario y, desde una pantalla aparte, edita la tabla de metas del curso.

Estos requisitos se derivan de `design.md`. No hay modelos ni migraciones nuevas.

Decisión sobre `registro/alertas.py`: la Task 3 no lo implementa (opción a, elegida por el equipo el 15-10). La ficha lo consume cuando exista y funciona sin él (Requisito 4). Quedan diferidos hasta la Task 2 el test "editar metas cambia las alertas" y la parte de la demo "la alerta desaparece".

Fuera de alcance: implementar `alertas.py`, las propuestas de nivel con IA, la revisión de observaciones, la distribución del curso, el resumen de la quincena (Task 2) y la vista de la directora (Task 12).

Si la Task 2 ya modificó `curso.html`, los cambios del Requisito 8 se le piden a la Task 2 en vez de hacerlos aquí.

## Glossary

- **Kimun**: la aplicación web Django del proyecto (app `registro`).
- **Ficha**: la vista `ficha` (GET `/ninos/<id>/`) y la página que muestra con los datos de un niño.
- **Sección_de_núcleo**: el parcial `_nucleo_ficha.html` de un núcleo, con raíz `<section id="nucleo-<sigla>">`.
- **Armador_de_ficha**: el módulo `registro/ficha.py` (`armar_ficha`, `descriptores_vecinos`, `es_provisorio` y `_situaciones`).
- **Formulario_de_nivel**: `FijarNivelForm`, el formulario para fijar el nivel de un niño en un núcleo.
- **Vista_fijar_nivel**: la vista `fijar_nivel` (POST `/ninos/<id>/nucleos/<sigla>/nivel/`).
- **Formulario_de_metas**: `MetasForm`, el formulario de la tabla de metas de un curso.
- **Vista_metas**: la vista `metas` (GET y POST `/cursos/<id>/metas/`).
- **Filtro_de_permisos**: el módulo `registro/permisos.py`.
- **Tabla_del_curso**: la vista `curso` y su plantilla `curso.html`.
- **Módulo_de_alertas**: `registro/alertas.py`, que entrega la Task 2 con la interfaz de la sección 2 de `design.md` (`situacion_del_curso`, `SituacionNucleo` y `Senal`).
- **Situación_del_núcleo**: el objeto `SituacionNucleo` que el Módulo_de_alertas entrega para un niño y un núcleo (nivel esperado, mediana del curso, señales y estado de los datos).
- **Educadora_del_curso**: la usuaria registrada como `Curso.educadora`.
- **Usuaria_sin_validación**: una asistente del curso o la directora del jardín del curso. Ve el curso pero no valida niveles ni edita metas.
- **Usuaria_ajena**: una usuaria autenticada que no es educadora, asistente ni directora del curso.
- **Nivel_máximo**: el valor de `Rubrica.nivel_maximo` para el nivel educativo del curso.
- **Descriptor**: un `DescriptorNivel`, la celda de la rúbrica para un núcleo y un nivel. Es oficial si `provisorio` es falso.
- **Nivel_actual**: el `NivelValidado` más reciente del niño en el núcleo (mayor fecha y, con la misma fecha, el último registrado).
- **Etiqueta_de_nivel**: el texto de un nivel según `texto_nivel`: "n · nombre" si el Descriptor del nivel es oficial y tiene nombre, o "n" en otro caso.
- **Observación_aceptada**: una `Observacion` del niño con estado aceptada y no grupal.
- **Petición_HTMX**: una petición con el encabezado `HX-Request: true`.
- **Metas_por_defecto**: los valores {semestre 1: 1, semestre 2: 3, semestre 3: 5, semestre 4: 7}.

## Requirements

### Requisito 1: Acceso y permisos

**Historia de usuario:** Como educadora, asistente o directora, quiero abrir la ficha de los niños de mis cursos y que solo la educadora pueda cambiar niveles y metas, para que cada rol vea lo suyo sin exponer niños de otros cursos.

#### Criterios de aceptación

1. CUANDO una usuaria autenticada pide la Ficha de un niño de un curso que puede ver, LA Ficha DEBERÁ responder 200 con el nombre del niño, el nombre del curso y un enlace a la Tabla_del_curso.
2. SI una Usuaria_ajena pide la Ficha de un niño, o una usuaria pide la Ficha de un niño inexistente, ENTONCES LA Ficha DEBERÁ responder 404.
3. SI una persona sin sesión iniciada pide la Ficha, la Vista_fijar_nivel o la Vista_metas, ENTONCES Kimun DEBERÁ responder con una redirección al inicio de sesión.
4. MIENTRAS la usuaria es la Educadora_del_curso, LA Ficha DEBERÁ incluir el Formulario_de_nivel en cada Sección_de_núcleo y el enlace "Editar metas del curso".
5. MIENTRAS la usuaria es una Usuaria_sin_validación, LA Ficha DEBERÁ mostrarse sin Formulario_de_nivel y sin el enlace "Editar metas del curso".
6. EL Filtro_de_permisos DEBERÁ entregar con `ninos_que_valida(usuaria)` exactamente los niños de los cursos donde la usuaria es la Educadora_del_curso.
7. SI una Usuaria_sin_validación o una Usuaria_ajena envía un POST a la Vista_fijar_nivel, ENTONCES LA Vista_fijar_nivel DEBERÁ responder 404 y dejar el historial de niveles sin cambios.
8. SI la sigla del núcleo de la URL no corresponde a un núcleo, ENTONCES LA Vista_fijar_nivel DEBERÁ responder 404.
9. SI una usuaria distinta de la Educadora_del_curso pide la Vista_metas, con GET o con POST, ENTONCES LA Vista_metas DEBERÁ responder 404 y dejar las metas del curso sin cambios.
10. SI la Vista_fijar_nivel recibe una petición GET, ENTONCES LA Vista_fijar_nivel DEBERÁ responder 405.

### Requisito 2: La rúbrica en cada núcleo

**Historia de usuario:** Como educadora, quiero ver por núcleo el nivel actual y qué dice la rúbrica de ese nivel y del siguiente, para decidir qué observar y qué nivel fijar.

#### Criterios de aceptación

1. LA Ficha DEBERÁ mostrar una Sección_de_núcleo por cada núcleo, en el orden de `Nucleo`.
2. LA Sección_de_núcleo DEBERÁ mostrar el nombre del núcleo y el Nivel_actual como Etiqueta_de_nivel.
3. DONDE el núcleo no tenga Descriptores o tenga al menos un Descriptor provisorio, LA Sección_de_núcleo DEBERÁ mostrar la etiqueta "Rúbrica provisoria".
4. CUANDO existe un Descriptor para el Nivel_actual, LA Sección_de_núcleo DEBERÁ mostrar su nombre, descripción y conducta, con los ejemplos plegados en un elemento `<details>`.
5. SI no existe un Descriptor para el Nivel_actual, ENTONCES LA Sección_de_núcleo DEBERÁ mostrar el número del nivel y el texto "Sin descriptor en la rúbrica para este nivel".
6. CUANDO el Nivel_actual es menor que el Nivel_máximo y existe el Descriptor del nivel siguiente, LA Sección_de_núcleo DEBERÁ mostrar "Qué observar después" con la descripción y la conducta de ese Descriptor.
7. SI el Nivel_actual es igual al Nivel_máximo o no existe el Descriptor del nivel siguiente, ENTONCES LA Sección_de_núcleo DEBERÁ omitir "Qué observar después".
8. CUANDO el Descriptor del Nivel_actual tiene pasos sugeridos no vacíos, LA Sección_de_núcleo DEBERÁ mostrar la sección "Pasos sugeridos" con ese texto.
9. SI no existe Descriptor para el Nivel_actual o sus pasos sugeridos están vacíos, ENTONCES LA Sección_de_núcleo DEBERÁ omitir la sección "Pasos sugeridos".

### Requisito 3: Evolución, evidencia por OA y observaciones

**Historia de usuario:** Como educadora, quiero ver en cada núcleo la evolución del niño, la evidencia por OA y las observaciones aceptadas, para respaldar el nivel que fijo.

#### Criterios de aceptación

1. LA Sección_de_núcleo DEBERÁ mostrar la evolución del niño en el núcleo con el parcial `_evolucion.html`, a partir de `grafico.evolucion_del_nino`.
2. LA Sección_de_núcleo DEBERÁ mostrar, por cada OA del núcleo, el código, la cantidad de evidencias y la fecha de la evidencia más reciente, según `cobertura.cobertura_del_nino`.
3. CUANDO un OA del núcleo no tiene evidencia, LA Sección_de_núcleo DEBERÁ mostrar junto al OA el texto "Sin evidencia todavía: sugerencia de qué observar".
4. LA Sección_de_núcleo DEBERÁ listar dentro de un elemento `<details>` solo las Observaciones_aceptadas del niño etiquetadas con el núcleo, de la más reciente a la más antigua, cada una con su fecha en formato `d-m-Y` y su cita.
5. SI el niño no tiene Observaciones_aceptadas en el núcleo, ENTONCES LA Sección_de_núcleo DEBERÁ mostrar el texto "Sin observaciones aceptadas".
6. EL Armador_de_ficha DEBERÁ armar la Ficha con una cantidad de consultas a la base que no dependa de la cantidad de núcleos, niveles validados ni observaciones.

### Requisito 4: Situación del curso cuando exista el Módulo_de_alertas

**Historia de usuario:** Como educadora, quiero ver en la ficha el nivel esperado, la mediana del curso y las señales de revisión cuando ese cálculo esté disponible, para comparar al niño, sin que la ficha dependa de que la Task 2 ya esté entregada.

#### Criterios de aceptación

1. DONDE el Módulo_de_alertas existe, EL Armador_de_ficha DEBERÁ obtener la situación del curso con una sola llamada a `situacion_del_curso(curso, hoy)` por Ficha.
2. DONDE el Módulo_de_alertas existe y entrega una Situación_del_núcleo para el niño y el núcleo, LA Sección_de_núcleo DEBERÁ mostrar el nivel esperado, la mediana del curso y el texto de cada señal con la clase `senal-aviso` o `senal-alerta` según su gravedad.
3. DONDE el Módulo_de_alertas existe y la Situación_del_núcleo indica que el niño nunca tuvo Observaciones_aceptadas en el núcleo, LA Sección_de_núcleo DEBERÁ mostrar el aviso "Sin observaciones aceptadas en este núcleo".
4. DONDE el Módulo_de_alertas existe y la Situación_del_núcleo indica más de 14 días sin Observaciones_aceptadas en el núcleo, LA Sección_de_núcleo DEBERÁ mostrar el aviso "Sin observaciones aceptadas en los últimos 14 días".
5. SI el Módulo_de_alertas no existe, ENTONCES EL Armador_de_ficha DEBERÁ dejar vacía (`None`) la situación de cada núcleo y armar el resto de la Ficha.
6. SI el resultado del Módulo_de_alertas no incluye al niño o al núcleo, ENTONCES EL Armador_de_ficha DEBERÁ dejar vacía (`None`) la situación de ese núcleo.
7. MIENTRAS la situación de un núcleo está vacía, LA Sección_de_núcleo DEBERÁ omitir el nivel esperado, la mediana, las señales y el aviso de datos, sin texto de reemplazo.
8. SI el Módulo_de_alertas existe pero su importación falla por una causa distinta de su ausencia, ENTONCES EL Armador_de_ficha DEBERÁ propagar el error.
9. EL Armador_de_ficha DEBERÁ usar del Módulo_de_alertas solo `situacion_del_curso` y los atributos de `SituacionNucleo` y `Senal` definidos en la sección 2 de `design.md`, de modo que agregar el módulo no requiera cambiar `registro/ficha.py`.

### Requisito 5: Formulario para fijar un nivel

**Historia de usuario:** Como educadora del curso, quiero comparar las opciones de la rúbrica antes de fijar un nivel, para decidir con la descripción de cada nivel a la vista.

#### Criterios de aceptación

1. EL Formulario_de_nivel DEBERÁ ofrecer como opciones exactamente los niveles del 1 al Nivel_máximo, en orden creciente, cada una con su Etiqueta_de_nivel y la descripción de su Descriptor, o una descripción vacía si no hay Descriptor.
2. CUANDO el niño tiene Nivel_actual en el núcleo, EL Formulario_de_nivel DEBERÁ marcar como seleccionada la opción de ese nivel.
3. EL Formulario_de_nivel DEBERÁ usar la sigla del núcleo como prefijo de sus campos.
4. EL Formulario_de_nivel DEBERÁ aceptar un comentario opcional de hasta 500 caracteres.
5. EL Formulario_de_nivel DEBERÁ ser válido con un nivel solo si el nivel es un entero entre 1 y el Nivel_máximo.
6. SI el nivel enviado no es un entero entre 1 y el Nivel_máximo, ENTONCES EL Formulario_de_nivel DEBERÁ informar el error "Elige un nivel entre 1 y N", con N igual al Nivel_máximo.
7. SI el comentario enviado supera los 500 caracteres, ENTONCES EL Formulario_de_nivel DEBERÁ informar un error en el campo comentario.
8. SI el guardado del `NivelValidado` lanza `ValidationError`, ENTONCES EL Formulario_de_nivel DEBERÁ agregar ese error a sus errores.
9. MIENTRAS la usuaria es la Educadora_del_curso, LA Sección_de_núcleo DEBERÁ mostrar el Formulario_de_nivel con un radio por opción (número, nombre y descripción), el campo de comentario, el botón "Guardar nivel" y el token CSRF.

### Requisito 6: Guardar un nivel

**Historia de usuario:** Como educadora del curso, quiero fijar el nivel de un niño en un núcleo con un comentario y ver el resultado sin recargar la página, para que el historial refleje mi juicio profesional.

#### Criterios de aceptación

1. CUANDO la Educadora_del_curso envía a la Vista_fijar_nivel un formulario válido, LA Vista_fijar_nivel DEBERÁ crear un `NivelValidado` con el niño, el núcleo, el nivel y el comentario enviados, la fecha de hoy del servidor y la usuaria de la sesión como `validado_por`.
2. CUANDO el POST a la Vista_fijar_nivel incluye campos `fecha` o `validado_por`, LA Vista_fijar_nivel DEBERÁ ignorarlos y usar la fecha del servidor y la usuaria de la sesión.
3. CUANDO la Educadora_del_curso fija el mismo nivel que el Nivel_actual, LA Vista_fijar_nivel DEBERÁ registrarlo como una nueva validación en el historial.
4. CUANDO se guarda un nivel, Kimun DEBERÁ tomar el nivel guardado como Nivel_actual del niño en el núcleo, incluso si ya había otra validación con la misma fecha.
5. SI el formulario enviado a la Vista_fijar_nivel es inválido, ENTONCES LA Vista_fijar_nivel DEBERÁ dejar el historial de niveles sin cambios.
6. CUANDO la Vista_fijar_nivel recibe una Petición_HTMX con un formulario válido, LA Vista_fijar_nivel DEBERÁ responder 200 con la Sección_de_núcleo actualizada y el mensaje "Nivel guardado: <Etiqueta_de_nivel>." en un elemento con `role="status"`.
7. CUANDO la Vista_fijar_nivel recibe una Petición_HTMX con un formulario inválido, LA Vista_fijar_nivel DEBERÁ responder 200 con la Sección_de_núcleo y los errores del formulario.
8. CUANDO la Vista_fijar_nivel recibe una petición sin HTMX con un formulario válido, LA Vista_fijar_nivel DEBERÁ registrar un mensaje de éxito y redirigir a la Ficha con el ancla `#nucleo-<sigla>`.
9. CUANDO la Vista_fijar_nivel recibe una petición sin HTMX con un formulario inválido, LA Vista_fijar_nivel DEBERÁ mostrar la Ficha completa con el Formulario_de_nivel del núcleo y sus errores.
10. LA Sección_de_núcleo DEBERÁ enviar el Formulario_de_nivel con `method="post"` y `action` hacia la Vista_fijar_nivel, y con `hx-post`, `hx-target="#nucleo-<sigla>"`, `hx-swap="outerHTML"` y `hx-disabled-elt` sobre el botón.
11. DONDE la Sección_de_núcleo se pliegue en un elemento `<details>`, LA Vista_fijar_nivel DEBERÁ devolver la Sección_de_núcleo abierta.

### Requisito 7: Tabla de metas del curso

**Historia de usuario:** Como educadora del curso, quiero editar el nivel esperado por semestre de permanencia, para ajustar la tabla de metas de mi curso.

#### Criterios de aceptación

1. EL Formulario_de_metas DEBERÁ tener un campo por semestre de permanencia, del 1 al 4.
2. EL Formulario_de_metas DEBERÁ ofrecer en cada campo los niveles del 1 al Nivel_máximo, cada uno con su Etiqueta_de_nivel.
3. EL Formulario_de_metas DEBERÁ usar el nombre de un nivel en la Etiqueta_de_nivel solo si todos los núcleos con Descriptores oficiales usan ese mismo nombre para ese nivel.
4. CUANDO la Educadora_del_curso abre la Vista_metas, EL Formulario_de_metas DEBERÁ mostrar la meta guardada de cada semestre y, para cada semestre sin meta guardada, el valor de Metas_por_defecto.
5. CUANDO la Educadora_del_curso envía metas válidas, EL Formulario_de_metas DEBERÁ crear o actualizar una `MetaSemestre` por semestre, en una sola transacción.
6. CUANDO las metas se guardan, LA Vista_metas DEBERÁ registrar el mensaje "Metas guardadas." y redirigir a la Tabla_del_curso.
7. CUANDO la Educadora_del_curso guarda metas válidas y vuelve a abrir la Vista_metas, EL Formulario_de_metas DEBERÁ mostrar los mismos valores guardados.
8. SI algún valor enviado no es un nivel entre 1 y el Nivel_máximo, ENTONCES LA Vista_metas DEBERÁ mostrar el formulario con los errores y dejar las metas del curso sin cambios.
9. LA Vista_metas DEBERÁ mostrar la nota de que desde el semestre 5 de permanencia se espera el Nivel_máximo de la rúbrica.

### Requisito 8: Cambios mínimos en la tabla del curso

**Historia de usuario:** Como educadora, quiero llegar a la ficha de cada niño y a la tabla de metas desde la tabla del curso, y ver los niveles con su nombre, para moverme por el curso sin buscar URLs.

#### Criterios de aceptación

1. LA Tabla_del_curso DEBERÁ mostrar cada nivel como Etiqueta_de_nivel, con los nombres de `DescriptorNivel.nombres_por_nucleo`.
2. LA Tabla_del_curso DEBERÁ enlazar el nombre de cada niño a su Ficha.
3. MIENTRAS la usuaria es la Educadora_del_curso, LA Tabla_del_curso DEBERÁ mostrar el enlace "Editar metas del curso".
4. CUANDO la Educadora_del_curso fija un nivel desde la Ficha, LA Tabla_del_curso DEBERÁ mostrar ese nivel como nivel actual del niño en el núcleo.

### Requisito 9: Presentación, accesibilidad y seguridad

**Historia de usuario:** Como educadora que usa el celular en la sala, quiero una ficha legible y segura, para consultarla y validar niveles en cualquier pantalla sin exponer datos de los niños.

#### Criterios de aceptación

1. LA Ficha DEBERÁ presentarse en una sola columna en pantallas de celular, con las tablas anchas dentro de un contenedor con desplazamiento horizontal (`overflow-auto`).
2. LA Sección_de_núcleo DEBERÁ comunicar cada señal y cada OA sin evidencia con texto, además del color.
3. LA Ficha DEBERÁ mostrar los colores de las señales con un contraste de al menos 4,5:1 frente al fondo.
4. LA Ficha DEBERÁ escapar el HTML de las citas, los comentarios y los textos de la rúbrica antes de mostrarlos.
5. LA Ficha DEBERÁ incluir el token CSRF en cada formulario y enviar las Peticiones_HTMX con el encabezado `X-CSRFToken`.
6. LA Ficha DEBERÁ redactar las señales como sugerencias de revisión y los OA sin evidencia como sugerencias de qué observar.
