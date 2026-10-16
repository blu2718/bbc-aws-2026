# Hallazgos: Programa Pedagógico de Transición (MINEDUC)

- Archivo: `programa-pedagogico-transicion-mineduc.pdf` (452 páginas). No se versiona; se descarga desde la fuente.
- Fuente: <https://www.curriculumnacional.cl/614/articles-210511_programa.pdf>
- Autor: Unidad de Currículum y Evaluación, MINEDUC. Informado por el CNED mediante Resolución N° 257/2019.
- Revisión: se leyeron el índice, la introducción, los componentes del programa, el núcleo Identidad y Autonomía (OA 1 y 2), las orientaciones de evaluación (pp. 380–399) y los instrumentos y rúbricas (pp. 436–451). Los conteos de los demás núcleos son automáticos y aproximados.

## Qué es

Es el programa del MINEDUC que orienta cómo trabajar los Objetivos de Aprendizaje (OA) del tercer tramo de las Bases Curriculares 2018: Primer y Segundo Nivel de Transición (NT1 y NT2, niños de 4 a 6 años). Cubre justo los dos años del tramo. No es el instrumento de 8 niveles de Integra.

Está dirigido sobre todo a establecimientos sin programa propio. Integra tiene su propio referente curricular, pero todo programa propio debe cubrir los mismos OA de las Bases Curriculares (p. 8). Por eso los OA son terreno común. La rúbrica de Integra llegó solo para Identidad y Autonomía (`datos/rubrica_integra.json`); en los demás núcleos, las conductas de este programa son una aproximación razonable a lo que mide Integra.

## Por qué es útil

### 1. Trae los 8 núcleos oficiales

Son los mismos de las Bases Curriculares. La rúbrica de Integra apunta a 10 y la cantidad puede cambiar (FAQ de Integra); la demo usa estos 8 hasta tener su lista.

| Ámbito | Núcleo | Sigla | OA | Conductas observables | Páginas |
|---|---|---|---:|---:|---|
| Desarrollo Personal y Social | Identidad y Autonomía | IA | 13 | 59 | 26–65 |
| | Convivencia y Ciudadanía | CC | 11 | 68 | 66–101 |
| | Corporalidad y Movimiento | CM | 9 | 46 | 102–129 |
| Comunicación Integral | Lenguaje Verbal | LV | 10 | 79 | 134–183 |
| | Lenguajes Artísticos | LA | 7 | 49 | 184–219 |
| Interacción y Comprensión del Entorno | Exploración del Entorno Natural | EEN | 12 | 52 | 224–275 |
| | Comprensión del Entorno Sociocultural | CES | 11 | 55 | 276–321 |
| | Pensamiento Matemático | PM | 12 | 96 | 322–378 |
| **Total** | | | **85** | **≈ 500** | |

El propio documento cita los OA así: "OA 1 LV", "OA 5 IA".

### 2. Trae las conductas observables que le faltaban a nuestra rúbrica

Cada OA tiene una sección "¿Cómo se podría reconocer el logro de este aprendizaje?", con conductas separadas para NT1 y NT2. Por ejemplo, para OA 1 IA (comunicar emociones y sentimientos que le provocan narraciones o situaciones):

- NT1: "Señala (indica o nombra) la emoción o sentimiento que le provocan diversas narraciones o situaciones observadas."
- NT2: "Explica por qué ha sentido miedo, alegría, tristeza, amor o ira frente a diversas narraciones o situaciones observadas."

En total son unas 10.000 palabras, entre 1.000 y 2.000 por núcleo. Caben directamente en el prompt, sin búsqueda vectorial.

### 3. Define lo esperado al entrar y lo que viene después

Cada núcleo tiene una "Trayectoria educativa" con dos partes:

- Lo que se espera al iniciar NT1. Sirve como ancla del nivel 1.
- Cómo continúan esos aprendizajes en Enseñanza Básica. Sirve como referencia de lo que está sobre lo esperado.

### 4. Tiene formatos de registro que sirven de modelo para nuestra salida (pp. 436–437)

- **Registro anecdótico.** Incluye fecha, nombre, edad, lugar, observador, situación o contexto, otras circunstancias relevantes y "descripción objetiva de los hechos".
- **Registro con apoyo visual.** Indica sus "focos" (núcleo y OA), como "Lenguajes Artísticos/OA3".
- **Registro fotográfico.** Reúne citas textuales de los niños, separadas de las "interpretaciones del observador".

### 5. Trae instrumentos y escalas (pp. 438–451)

- Lista de cotejo (p. 438) y escala de frecuencia: siempre, generalmente, a veces, nunca (p. 439).
- Escala según autonomía (p. 439):
  - 3: lo realiza de manera autónoma;
  - 2: lo realiza luego de recibir ayuda;
  - 1: lo realiza de manera parcial con ayuda;
  - 0: no lo realiza.

  Aplica directo a notas como "logra pasar por circuitos de obstáculos sin ayuda de adulto".
- Rúbricas de ejemplo por OA, con 4 niveles de desempeño: Muy bueno, Bueno, Regular, En proceso (pp. 443–451).

### 6. Respalda nuestro enfoque de evaluación (pp. 380–399)

- La evaluación puede ser diagnóstica, formativa o sumativa, y se basa en observación y documentación en situaciones auténticas.
- Pide que "los registros y evidencias recopiladas sean objetivas, sistemáticas, acuciosas y fidedignas".
- La educadora lidera el proceso. Coincide con que la herramienta propone y la educadora decide.

## Qué no trae

- Los niveles de Integra ni sus nombres (Comenzando a Profundizando). Están en `datos/rubrica_integra.json`, por ahora solo para IA.
- Sala cuna ni nivel medio. De medio solo describe lo esperado al ingresar a NT1.
- La mayor parte del documento son experiencias de aprendizaje sugeridas. No sirven para un MVP que solo propone el nivel.

## Cómo lo usamos

1. **La demo usa Transición.** Es el único nivel educativo con conductas observables oficiales, así que la rúbrica provisoria se deriva de ellas en vez de inventarse.
2. **Rúbrica provisoria.** Es una hipótesis nuestra que hay que validar con Integra, y solo se usa en los núcleos que todavía no tienen rúbrica de Integra (hoy, todos menos IA). Calza con la tabla de metas por defecto (1, 3, 5 y 7 por semestre):

   | Nivel | Criterio provisorio |
   |---|---|
   | 1 | Muestra lo esperado al iniciar NT1 |
   | 2 | Muestra algunas conductas de NT1, con ayuda |
   | 3 | Muestra varias conductas de NT1, algunas de forma autónoma |
   | 4 | Muestra las conductas de NT1 de forma autónoma |
   | 5 | Muestra algunas conductas de NT2, con ayuda |
   | 6 | Muestra varias conductas de NT2, algunas de forma autónoma |
   | 7 | Muestra la mayoría de las conductas de NT2 de forma autónoma |
   | 8 | Muestra las conductas de NT2 de forma autónoma (lo esperado al egresar) |

3. **Datos estructurados.** El contenido se pasa a `datos/curriculo_transicion.json`, con núcleos, OA, conductas de NT1 y NT2 y trayectoria. Los prompts usan ese archivo, no el PDF.
4. **Observaciones.** Cada una se etiqueta con sus OA ("OA 4 LV") y con el nivel de apoyo según la escala de autonomía. Además, lo que el niño hizo o dijo se separa de la interpretación de la educadora.

## Preguntas abiertas

Si los demás núcleos de Integra seguirán la lógica de IA y si el mapeo provisorio les parece razonable está en "Preguntas pendientes para Integra" de `PLAN.md` (pregunta 7).
