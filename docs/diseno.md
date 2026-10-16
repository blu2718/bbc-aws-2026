# Diseño de la interfaz de Kimün

Guía del estilo visual de Kimün y registro del pulido de la rama `frontend-pulido` (16-oct-2026, antes del
congelamiento). Se actualiza con cada commit: la sección [Estado](#estado-del-pulido) dice qué está hecho y qué falta.

Base técnica: Django con plantillas en `kimun/templates/` y `kimun/registro/templates/registro/`, Pico.css 2.1.1 y
HTMX 2.0.11 sin CDN (`kimun/static/vendor/`), estilos propios en `kimun/static/registro/registro.css` y
comportamiento en `kimun/static/registro/kimun.js`. El boceto de las cuatro pantallas principales es
`diseno-interfaz.jpg` (I registrar, II suceso, III menú lateral, IV perfil del niño).

## Identidad

### Paleta

Sale del logo de Integra (`docs/marca/logo-integra.jpg`) en versión pastel. Todas son variables CSS en `:root`
(`registro.css`). Regla: todo texto con al menos 4,5:1 sobre su fondo y el color nunca va solo (siempre con texto).

| Variable | Valor | Uso |
|---|---|---|
| `--kimun-celeste` | `#a0c9e9` | Fondo de botones primarios y avatar del curso. Texto encima `--kimun-tinta` (7,9:1) |
| `--kimun-celeste-hover` | `#88b8dd` | Hover de botones primarios |
| `--kimun-celeste-suave` | `#ecf5fb` | Burbujas, ítems del menú, fondos suaves |
| `--kimun-celeste-medio` | `#daeaf6` | Hover sobre celeste suave |
| `--kimun-celeste-borde` | `#c9deee` | Bordes de cajas celestes |
| `--kimun-celeste-claro` | `#f5f9fc` | Citas, bandejas, fondo del gráfico |
| `--kimun-azul` | `#125a91` | Enlaces y textos destacados (7,3:1 sobre blanco) |
| `--kimun-azul-hover` | `#0d4773` | Hover de enlaces |
| `--kimun-tinta` | `#142f43` | Texto sobre celeste y títulos de tarjetas |
| `--kimun-fondo` | `#fafcfd` | Fondo de página |
| `--kimun-linea` | `#dbe4eb` | Borde de tarjetas |
| `--kimun-gris` / `--kimun-gris-oscuro` | `#606060` / `#484c51` | Botones secundarios (texto blanco 6,3:1) |
| `--kimun-gris-suave` | `#eef1f4` | Etiquetas neutras |
| `--kimun-aviso*` | `#754200`, fondo `#fef2cd`, texto `#4c3300`, borde `#987916` | Señal amarilla: «Observar», pendientes, sugerencias |
| `--kimun-alerta*` | `#a51c18`, fondo `#fde6e5`, texto `#5b1310`, borde `#cc3833` | Señal roja: «Revisar», errores, protección de derechos |
| `--kimun-naranjo` | `#b35400` | Íconos «observar» del menú lateral |
| `--kimun-ok` / `--kimun-ok-fondo` | `#326412` / `#e3f4d7` | Lo que está bien: aceptada, avance, autónomo |
| `--integra-*-pastel` | azul `#a0c9e9`, rojo `#f5b0ad`, verde `#b6dd9d`, amarillo `#fcde7e` | Solo la franja decorativa bajo la barra superior |

La página va siempre en tema claro (`<html data-theme="light">` en `base.html`): los colores de las señales están
medidos sobre blanco. Las variables de modo oscuro de `registro.css` quedan por si se activa a futuro.

### Tipografía, tamaños y espaciado

- Familia: la del sistema que trae Pico (`system-ui`, Segoe UI, Roboto, Noto Sans…). No se carga ninguna fuente
  externa (rápido en celulares y sin CDN).
- Escala: la de Pico (base 16 px en celular, crece a 17–21 px en pantallas anchas). Dentro de las tarjetas:
  título de tarjeta 1,05–1,2 rem, texto 1 rem, ayudas `.ayuda` 0,85 rem, etiquetas 0,75–0,85 rem.
- Peso: 700 para la marca y títulos de tarjeta, 600 para etiquetas y enlaces del menú.
- Espaciado: ritmo de Pico (`--pico-spacing` = 1 rem). Tarjetas con `padding: 1rem 1.1rem` y `margin-bottom: 1.25rem`.
  Entre ítems de listas en tarjeta: 0,4–0,6 rem.
- Radio: `--kimun-radio` (0,75 rem) en tarjetas y botones; 999 px en etiquetas tipo píldora; 1,25 rem en burbujas.
- Sombra: `--kimun-sombra`, una sola, suave y azulada.

### Logo e íconos

- Logo: `kimun/static/registro/img/logo.svg` (araucaria con dos niños, fondo celeste). Versiones PNG:
  `logo-512.png`, `favicon-32.png`, `apple-touch-icon.png`. Fuente: `docs/marca/logo-kimun.pdf`.
  Se usa en la barra (36 px), menú lateral (52 px), login (112 px), registrar (88 px) e informe (48 px), siempre con
  `alt=""` porque va junto al nombre «Kimün».
- `docs/marca/logo-integra.jpg` es solo la fuente de la paleta: no se muestra en la app.
- Íconos de interfaz: SVG en línea, trazo 2–2,2 px, `stroke="currentColor"`, 24 px, `aria-hidden="true"` y texto
  `.visualmente-oculto` al lado (menú, adjuntar, micrófono, enviar, cerrar).
- Íconos de núcleos: PNG en `static/registro/img/nucleos/` usados como máscara (`.icono-nucleo`), así toman el color
  del texto. Los arma `registro/iconos.py`; aparecen en el gráfico de pétalos y en «Para tener presentes».

## Componentes

| Componente | Clases | Notas |
|---|---|---|
| Barra superior | `.barra-app`, `.marca`, `.boton-menu`, `#contador-avisos`, `#contador-pendientes` | Fija arriba, franja de cuatro colores debajo |
| Menú lateral | `dialog.menu-lateral`, `.menu-cabecera`, `.menu-secciones`, `.menu-seccion`, `.lista-ninos`, `.menu-pie` | `<dialog>` modal; lo abre `kimun.js` |
| Tarjeta | `.tarjeta` (= `.perfil-seccion`, sección con título), `.suceso` (tarjeta de registro), `article` de Pico | Fondo blanco, borde `--kimun-linea`, sombra |
| Encabezado de página | `.encabezado-pagina` (h1 + bajada gris), `.titulo-largo` (h1 que es una frase) | |
| Lista de enlaces | `.lista-enlaces` (filas tipo tarjeta, `small` en segunda línea) | Avisos, cursos |
| Pasos | `.pasos` (lista numerada) | Solo para secuencias reales |
| Cita | `.cita-nota` | Nota tal como se registró |
| Caja suave | `.bandeja-propuestas`, `.resumen-nota`, `.pregunta-kimun` | Fondo celeste claro, sin sombra |
| Botones | `button`, `[role=button]` (primario celeste), `.secondary` (gris), `.secondary.outline` (borde) | Uno primario por bloque |
| Botón ícono | `.boton-icono` | Círculo de 2,75 rem (área táctil de 44 px) |
| Etiquetas de estado | `.estado-obs` (+ `.estado-pendiente`, `.estado-aceptada`), `.efecto-*`, `.apoyo`, `.etiqueta-referencia`, `.etiqueta-provisoria`, `.etiqueta-sin-evidencia` | Píldoras con texto |
| Señales | `.senal` + `.senal-aviso` / `.senal-alerta` | Caja con borde izquierdo de color y texto |
| Alertas | `.aviso` (amarilla), `.aviso-error` (roja), `.aviso-proteccion` (roja, Task 13), `.mensajes` (celeste) | |
| Tablas | `<table>` de Pico dentro de `.overflow-auto` y de una `.tarjeta`; `.tabla-curso`, `.tabla-jardin`, `.distribucion`; la página lleva `body.pagina-tabla` | Primera columna fija al desplazar; `caption` gris a la izquierda |
| Cómo leer | `details.como-leer` | Explicación larga de una tabla, plegada |
| Avatares | `.avatar`, `.avatar-chico`, `.avatar-grande`, `.avatar-curso` | Color por nombre (`color_avatar`) |
| Composer | `.composer`, `.composer-barra`, `.composer-adjunto` | Barra de registrar (pantalla I) |
| Burbuja | `.burbuja`, `.burbuja-pie` | Nota registrada (pantalla II) |
| Historial | `.historial`, `.evento` | Línea de tiempo del perfil |

## Decisiones de diseño

(Se completan con cada arreglo; ver [Estado](#estado-del-pulido).)

- Se ordena la identidad que ya existe; no se cambia la paleta ni el logo.
- Botones primarios en celeste pastel con texto tinta, como ya documentaba `registro.css`: es lo que pedía la
  identidad y no se veía por un problema de especificidad, no un cambio de paleta.
- Contadores de la barra: no se acortó el texto «Avisos de protección» porque `test_proteccion.py` compara el HTML
  exacto; en celular se apilan en dos píldoras chicas.
- Arrastre: causa real era que el `input type=file` oculto no recibe el arrastre y no había manejadores; se arregló
  solo en JS, sin tocar el formulario ni la vista. Solo acepta imágenes: los audios se graban con el micrófono.
- Protección de derechos: el rojo de alerta solo como borde y numeración; el texto de los pasos queda en tinta
  normal para que se lea tranquilo. Un solo botón primario («Informé a la directora…»); «No es una vulneración»
  queda de borde y separado, porque es la acción menos frecuente y pide un motivo.
- Tablas: la explicación (que los tests y la directora necesitan) no se borra: se pliega en «Cómo leer esta
  tabla» para que lo primero que se vea sea la tabla y las sugerencias.
- La interfaz nueva (registrar, suceso, menú, perfil) es la referencia de estilo: las pantallas más antiguas
  (curso, jardín, Task 13, informe) se llevan a sus tarjetas y etiquetas.

## Skills y guías usadas

- `frontend-design` (plugin oficial): criterio de jerarquía, restricción («gastar la audacia en un solo lugar»),
  piso de calidad (celular, foco visible, movimiento reducido) y textos desde la mirada de quien usa la app. No se
  usó su parte de «identidad nueva»: manda la del repo.
- `web-design-guidelines` (Vercel): la skill pide descargar las reglas de GitHub y el dominio está bloqueado en este
  entorno, así que se aplicaron de memoria sus puntos principales (áreas táctiles, foco, contraste, textos que no
  se cortan, `prefers-reduced-motion`, nada de desplazamiento horizontal de la página).
- `playwright-cli` (skill de `@playwright/cli`): para recorrer las pantallas. Se usó su librería `playwright` con
  un script propio (no versionado) que recorre las pantallas por rol y tamaño, guarda capturas e informa errores de
  consola y desbordes horizontales.
- `run`: receta para levantar el servidor y manejarlo con un navegador sin cabeza.

## Diagnóstico (16-oct, capturas en `/tmp/kimun-capturas/antes/`)

Recorrido como educadora, asistente y directora, en 390×844 y 1366×900. Sin errores de consola ni respuestas 4xx/5xx.
Ordenado por impacto en la demo:

1. **La paleta de Kimün no se aplica a Pico.** `registro.css` define los colores primarios en `[data-theme="light"]`
   (especificidad 0,1,0), pero Pico los define en `:root:not([data-theme=dark])` (0,2,0) y gana. Resultado: los
   botones salen en el azul por defecto de Pico (`#0172ad`) y los secundarios en su gris pizarra, no en el celeste
   y el gris de Integra que documenta el CSS. Afecta a todas las pantallas.
2. **Barra superior en celular:** «Avisos de protección: 1» y «Por revisar: 3» se montan sobre el nombre «Kimün».
   Además, en escritorio la barra (64 rem) no se alinea con el contenido (contenedor de Pico).
3. **Arrastrar una foto a la barra de registrar no funciona.** El `input type=file` está oculto y no hay
   manejadores `dragover`/`drop`: el navegador abre la imagen en la pestaña y se pierde lo escrito.
4. **Registro en proceso desborda en celular:** el texto «Ordenando el registro…» no se corta (Pico pone
   `white-space: nowrap` a todo `[aria-busy=true]`) y la página se desplaza a lo ancho (690 px).
5. **Pantallas fuera del estilo:**
   - Vista del jardín (directora): sugerencias como viñetas con enlace suelto, texto largo antes de la tabla,
     estilos en línea en la plantilla.
   - Tabla del curso: cuatro secciones sin tarjetas, mucho texto explicativo antes de cada tabla, estilos en línea;
     la tabla principal (niveles) queda al final.
   - Bandeja de propuestas: cuando solo hay propuestas «en preparación» es una caja grande con una línea.
   - Informe para la familia: botón y ayuda sueltos; nivel del núcleo baja a otra línea en celular.
   - Task 13 (avisos, aviso, protocolo): `.aviso-proteccion` no tiene estilos; listas con viñetas, título de
     5 líneas en celular, botones sin jerarquía.
   - Inicio (educadora/asistente): lista plana con «·» entre enlaces.
6. **Revisión:** cada grupo usa un `<h2>` de tamaño de página («Texto de Carolina Demo · 16 de octubre…»), muy
   grande en celular.
7. **Menores:** metas y capturar (interfaz antigua) sin tarjetas; `body > header` y `.marca` definidos dos veces
   en `registro.css`.

## Estado del pulido

| # | Arreglo | Commit | Estado |
|---|---|---|---|
| 1 | Paleta de Pico: overrides con el mismo selector que Pico (`:root:not([data-theme=dark]), [data-theme="light"]`) y `--pico-secondary*` en gris de Integra | `fix(estilo): paleta` | hecho |
| 2 | Barra superior: contadores como píldoras (rojo pastel avisos, celeste por revisar), apiladas en celular; la barra usa los mismos anchos que `.container` | `fix(barra)` | hecho |
| 3 | Arrastrar foto: `kimun.js` recibe `dragover`/`drop` en el composer, pone la foto en `[data-foto]` y dispara `change` (mismo camino que «+»); fuera de la barra el drop se ignora para no perder la nota; borde punteado `.composer-soltar` mientras se arrastra | `fix(registrar)` | hecho, probado con Playwright |
| 4 | Desborde «procesando»: `.procesando p { white-space: normal }` | `fix(suceso)` | hecho |
| 5a | Task 13: avisos en `.tarjeta` con `.lista-enlaces` y píldora «Por atender»; aviso con `.aviso-proteccion` (borde rojo, pasos numerados `.pasos`), la nota en `.cita-nota`, el formulario de resolver en tarjeta con «No es una vulneración» como botón de borde; protocolo con `.encabezado-pagina`, formulario en tarjeta; resguardo en el suceso como caja roja suave | `style(proteccion)` | hecho, tests `test_proteccion` y `test_protocolo` pasan |
| 5b | Vista del jardín: `.encabezado-pagina` con el protocolo como botón de borde, sugerencias y tabla en `.tarjeta`, explicación en `<details class="como-leer">`, estilos en línea movidos a `registro.css` (`body.pagina-tabla`) | `style(jardin)` | hecho, `test_jardin` pasa |
| 5c | Curso, bandeja, informe, inicio | | pendiente |
| 6 | Títulos de revisión | | pendiente |

Pantallas para mirar primero: registrar y suceso (celular), tabla del curso, vista del jardín, aviso de protección.

Pendiente que requiere tocar código fuera de la interfaz: nada por ahora.

## Cómo seguir

1. Cargar la demo en una base temporal y levantar el servidor:
   ```
   cd kimun
   export DJANGO_DB_PATH=/tmp/kimun-front.sqlite3 DEMO_PASSWORD=demo1234   # solo local
   .venv/bin/python manage.py migrate && .venv/bin/python manage.py cargar_demo
   .venv/bin/python manage.py runserver 127.0.0.1:8765
   ```
   Usuarias: `educadora`, `asistente`, `directora` (y `educadora_b`, `educadora_c`).
2. Antes de agregar estilos, buscar en `registro.css` una clase que ya sirva (tabla de componentes de arriba).
3. Colores: solo variables `--kimun-*`. Si falta un tono, agregarlo a `:root` con su contraste en un comentario.
4. Nada de `<style>` en las plantillas: todo en `registro.css`, en la sección de su pantalla.
5. No cambiar ids, `name` de formularios, atributos `hx-*` ni URLs: las vistas y los tests dependen de ellos.
6. Probar en 390×844 y en escritorio, y correr los tests de las vistas de las plantillas tocadas
   (`.venv/bin/pytest registro/tests/test_<vista>.py`).
