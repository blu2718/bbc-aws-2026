# Índice de `contexto/`

Punto de entrada para agentes. Léelo primero y no abras un archivo completo. El flujo:

1. En "Dónde buscar", elige el archivo que responde tu pregunta.
2. Lee solo el bloque "Índice" de ese archivo. Va al inicio, entre `<!-- indice:inicio -->` y `<!-- indice:fin -->`, y cada entrada trae el rango de líneas de su sección.
3. Lee solo esas líneas (por ejemplo, con `offset` y `limit`). Para un OA concreto, busca su identificador con grep (`IA-T-5`) en `enciclopedia-bases-curriculares.md`.

Los rangos de líneas los genera `python scripts/indice_contexto.py`. Si editas un archivo de esta carpeta, vuelve a correrlo. `--comprobar` avisa si quedó alguno desactualizado.

## Archivos

| Archivo | Qué es | Para quién | Cuándo leerlo |
|---|---|---|---|
| [`resumen-politica-calidad.md`](resumen-politica-calidad.md) | Resumen ejecutivo de la Política de Calidad Educativa de Integra (2017), el faro del proyecto | Equipo | Para entender en 5 minutos qué valora Integra |
| [`guia-politica-calidad.md`](guia-politica-calidad.md) | Guía completa de la Política para agentes. Abre con la "Brújula" (12 principios y una lista de verificación) y cada sección termina en "Qué exige a Kimün" | Agentes | Antes de diseñar una funcionalidad, un prompt o un texto de la interfaz, y para revisar uno |
| [`hallazgos-politica-calidad-educativa-integra.md`](hallazgos-politica-calidad-educativa-integra.md) | Análisis previo de la Política, cruzado con `PLAN.md` | Ambos | Para saber qué implicancias ya recoge el plan |
| [`resumen-bases-curriculares.md`](resumen-bases-curriculares.md) | Resumen ejecutivo de las Bases Curriculares 2018 (la malla oficial) | Equipo | Para entender la estructura: ámbitos, núcleos, niveles y OA |
| [`enciclopedia-bases-curriculares.md`](enciclopedia-bases-curriculares.md) | Texto literal de las Bases y los 206 OA con identificador estable. Incluye un anexo de protección de derechos: qué constituye maltrato y qué hacer | Agentes | Para citar un OA o un principio, etiquetar una observación o redactar una alerta, y ante cualquier nota que podría describir una vulneración |
| [`hallazgos-bases-curriculares.md`](hallazgos-bases-curriculares.md) | Análisis previo de las Bases, cruzado con `PLAN.md` | Ambos | Para saber qué implicancias ya recoge el plan |
| [`hallazgos-programa-pedagogico-transicion.md`](hallazgos-programa-pedagogico-transicion.md) | Programa Pedagógico de Transición: conductas observables por OA, escala de autonomía, formatos de registro y mapeo de la rúbrica provisoria | Ambos | Para la rúbrica provisoria y el nivel de apoyo. Las conductas en sí están en `datos/curriculo_transicion.json` |
| [`faq_integra_2.md`](faq_integra_2.md) | Respuestas de Integra por correo y qué cambió para nosotros | Ambos | Para saber qué pidió Integra sobre el alcance, la rúbrica, el rezago y las vistas |
| [`ocr-presentacion.md`](ocr-presentacion.md) | Texto de la presentación del desafío, con los post-its de ejemplo transcritos | Ambos | Para el problema, el KPI (4 h a 0 h), la escala de 8 niveles y notas reales de ejemplo |
| [`instrumentos-estandarizados.md`](instrumentos-estandarizados.md) | EEDP, TEPSI, Pauta Breve, IEA, PLAEP, Battelle y ASQ-3: quién los aplica, áreas, puntajes, puntos de corte, qué trae la hoja y licencias | Ambos | Para cargar o mostrar un resultado de un instrumento, o agregar uno a `datos/instrumentos.json` (Task 14) |

Fuera de git: `faq_integra.json` (el FAQ de Integra de los tres retos, resumido en "FAQ de Integra" de `PLAN.md`) y los PDF fuente, que se descargan desde los enlaces de cada archivo.

## Dónde buscar

| Pregunta | Archivo y sección |
|---|---|
| ¿Qué dice textualmente un OA? ¿Cuántos OA tiene un núcleo? | `enciclopedia-bases-curriculares.md`: la tabla del núcleo y nivel, o grep del identificador (`CC-T-7`) |
| ¿Qué significa un núcleo o un ámbito? ¿Qué orientaciones tiene? | `enciclopedia-bases-curriculares.md`, "Núcleo …" |
| Principios pedagógicos, enfoque de derechos, inclusión | `enciclopedia-bases-curriculares.md`, "Capítulo 1" |
| Cómo se evalúa en párvulos (evidencia, la educadora concluye, sin juicios perentorios) | `enciclopedia-bases-curriculares.md`, "Consideraciones para la evaluación" |
| Reglas para aplicar la malla en la app | `enciclopedia-bases-curriculares.md`, "Consideraciones para Kimün" |
| Qué constituye maltrato, qué no y qué hacer ante una posible vulneración | `enciclopedia-bases-curriculares.md`, "Anexo: protección de derechos y vulneraciones". El diseño en la app está en `PLAN.md`, "Protección de derechos" y Task 13 |
| ¿Esta funcionalidad, prompt o texto respeta a Integra? | `guia-politica-calidad.md`, "Brújula" y "Lista de verificación" |
| Definición de calidad de Integra, visión, misión y valores | `guia-politica-calidad.md`, secciones 1, 8 y 9 |
| Palabras y tono: "rezagado", alertas, fortalezas | `guia-politica-calidad.md`, sección 7 ("Qué exige a Kimün") y sección 18 (tensiones) |
| Instrumentos de evaluación de Integra (IEA, EEDP, PLAEP-R) | `guia-politica-calidad.md`, sección 5 |
| Tensiones entre la Política y el diseño actual | `guia-politica-calidad.md`, sección 18 |
| Conductas observables de NT1 y NT2, escala de autonomía | `hallazgos-programa-pedagogico-transicion.md`, y `datos/curriculo_transicion.json` |
| Qué pidió Integra (niveles ajustables, 10 núcleos, rezago relativo a la sala, vista de la directora) | `faq_integra_2.md` y "FAQ de Integra" en `PLAN.md` |
| Ejemplos reales de notas de las educadoras | `ocr-presentacion.md`, "Diapositiva 5" |
| Cómo funciona un instrumento estandarizado (puntajes, cortes, quién lo aplica) | `instrumentos-estandarizados.md` |
| Preguntas abiertas a Integra | `PLAN.md`, "Preguntas pendientes para Integra" |

## Convenciones

- Páginas: la enciclopedia cita la página impresa de las Bases (la del PDF es esa más 2). La guía cita la página del PDF de la Política. El anexo de protección cita los protocolos de la JUNJI como "JUNJI-V, p. N" y "JUNJI-M, p. N".
- OA: identificador `SIGLA-NIVEL-N` (`SC`, `M`, `T`), por ejemplo `IA-T-5`, y forma de cita del Programa, `OA 5 IA`.
- Derechos: la Política de Calidad tiene derechos reservados. Se parafrasea, con citas breves; no copies pasajes largos al repo. Las Bases y los protocolos de la JUNJI son públicos.

## Tamaño de cada archivo

<!-- catalogo:inicio -->
| Archivo | Líneas | Palabras |
|---|---:|---:|
| [`enciclopedia-bases-curriculares.md`](enciclopedia-bases-curriculares.md) | 1701 | 42.238 |
| [`faq_integra_2.md`](faq_integra_2.md) | 77 | 1.080 |
| [`guia-politica-calidad.md`](guia-politica-calidad.md) | 469 | 9.633 |
| [`hallazgos-bases-curriculares.md`](hallazgos-bases-curriculares.md) | 128 | 1.721 |
| [`hallazgos-politica-calidad-educativa-integra.md`](hallazgos-politica-calidad-educativa-integra.md) | 161 | 1.867 |
| [`hallazgos-programa-pedagogico-transicion.md`](hallazgos-programa-pedagogico-transicion.md) | 120 | 1.268 |
| [`instrumentos-estandarizados.md`](instrumentos-estandarizados.md) | 166 | 3.549 |
| [`ocr-presentacion.md`](ocr-presentacion.md) | 167 | 1.368 |
| [`resumen-bases-curriculares.md`](resumen-bases-curriculares.md) | 79 | 1.039 |
| [`resumen-politica-calidad.md`](resumen-politica-calidad.md) | 58 | 967 |
<!-- catalogo:fin -->
