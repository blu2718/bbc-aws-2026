# Resumen: Bases Curriculares de la Educación Parvularia (MINEDUC, 2018)

Resumen ejecutivo para el equipo. Para el detalle, ver `enciclopedia-bases-curriculares.md`. Para las implicancias ya cruzadas con el plan, ver `hallazgos-bases-curriculares.md`.

<!-- indice:inicio -->
## Índice

Generado por `scripts/indice_contexto.py`. Cada entrada indica sus líneas en este archivo; lee solo las que necesites.

- [Qué es y para qué sirve](#qué-es-y-para-qué-sirve) · líneas 17–21
- [Estructura](#estructura) · líneas 23–45
- [Las ideas que más pesan para el proyecto](#las-ideas-que-más-pesan-para-el-proyecto) · líneas 47–67
- [Qué NO trae](#qué-no-trae) · líneas 69–74
- [Dónde profundizar](#dónde-profundizar) · líneas 76–78
<!-- indice:fin -->

## Qué es y para qué sirve

Es el marco curricular nacional de la educación parvularia chilena (MINEDUC, reimpresión 2018). Define qué y para qué deben aprender los niños desde los primeros meses hasta el ingreso a la Educación Básica. Reemplaza a las Bases de 2001. Es público. Todo programa propio (como el de Integra) debe cubrir sus Objetivos de Aprendizaje, así que son terreno común. Para Kimün, son la fuente de verdad de los núcleos y de los OA.

Tiene tres capítulos: Fundamentos (enfoque de derechos, inclusión, 8 principios), Organización curricular (ámbitos, núcleos, niveles y OA: lo central) y Contextos para el aprendizaje (planificación, evaluación, ambientes, familia).

## Estructura

Jerarquía: Ámbito (3) → Núcleo (8) → Nivel curricular (3 tramos de 2 años) → Objetivos de Aprendizaje (206).

- Ámbitos: Desarrollo Personal y Social (transversal), Comunicación Integral, Interacción y Comprensión del Entorno.
- Núcleos (sigla): Identidad y Autonomía (IA), Convivencia y Ciudadanía (CC), Corporalidad y Movimiento (CM), Lenguaje Verbal (LV), Lenguajes Artísticos (LA), Exploración del Entorno Natural (EEN), Comprensión del Entorno Sociocultural (CES), Pensamiento Matemático (PM).
- Niveles: 1° Sala Cuna (hacia los 2 años), 2° Medio (hacia los 4), 3° Transición (hacia los 6; NT1 y NT2).

Conteo de OA, verificado con script contra el PDF (los 206 aparecen literales):

| Núcleo | Sala Cuna | Medio | Transición | Total |
|---|---:|---:|---:|---:|
| IA | 7 | 12 | 13 | 32 |
| CC | 6 | 10 | 11 | 27 |
| CM | 7 | 8 | 9 | 24 |
| LV | 8 | 8 | 10 | 26 |
| LA | 6 | 7 | 7 | 20 |
| EEN | 5 | 9 | 12 | 26 |
| CES | 5 | 7 | 11 | 23 |
| PM | 6 | 10 | 12 | 28 |
| Total | 50 | 71 | 85 | 206 |

La demo usa solo los 85 OA de Transición. Los de Sala Cuna y Medio quedan como fuente oficial si el alcance se amplía.

## Las ideas que más pesan para el proyecto

1. Los OA son metas de fin de tramo, no de año ni de mes. "Se enuncian desde lo que se espera al final de cada nivel, es decir abarcando tramos curriculares de dos años" (p. 40). Por eso el nivel esperado de Kimün es una referencia blanda.

2. Un OA se evidencia de muchas formas. "lo puede evidenciar a través de diferentes desempeños concretos" (p. 40). El modelo debe interpretar la conducta, no buscar coincidencia textual con el enunciado del OA.

3. La educadora concluye; el sistema propone con evidencia. "Reunidas las evidencias, el o la educadora debe construir una conclusión evaluativa... teniendo en cuenta la distancia entre lo que él o ella es capaz de hacer y lo que plantea el objetivo de aprendizaje" (p. 111). Es exactamente el flujo de Kimün.

4. El nivel esperado es blando y las alertas van sin juicios. Los tramos "orientan los periodos óptimos, pero en ningún caso implica limitar las expectativas de progreso" (p. 42); la evaluación debe ser "sin juicios perentorios" (p. 112). Respalda redactar las señales de rezago como sugerencias de revisión.

5. La evidencia es cotidiana y multimodal. "Son múltiples las formas de recogida de información (por ejemplo, fotografías, grabaciones, observaciones)" y "no es imprescindible construir situaciones especiales ni momentos formales de evaluación" (p. 110). Respalda la captura por texto, foto y audio.

6. Separar lo observado de la interpretación. La documentación pedagógica recoge "ideas, anécdotas, conflictos" en momentos diversos (p. 111). Coincide con la regla de separar cita literal e interpretación.

7. Los OA de Desarrollo Personal y Social (IA, CC, CM) son transversales. Deben estar presentes de forma permanente (p. 38). Es esperable que reciban mucha evidencia; conviene que la vista los distinga.

8. OA de nivel adyacente, sin marcarlo "fuera de rango". Para la inclusión "se pueden seleccionar Objetivos de Aprendizaje de un nivel diferente al del grupo" (p. 43). Si una observación de Transición calza mejor con un OA de Medio, no es un error.

9. Cobertura equilibrada de los 8 núcleos. "el norte de la planificación ha de encontrarse siempre en la implementación equilibrada de los ocho núcleos" (p. 104). Respalda el resumen de la quincena que destaca núcleos sin observaciones.

10. 8 núcleos y 3 niveles son los de las Bases, pero no son un dato fijo para la app: Integra apunta a 10 núcleos y la cantidad de niveles de rúbrica puede cambiar. Las Bases dan el "qué" (OA por tramo); la rúbrica de Integra da el "cuánto" (niveles por núcleo).

## Qué NO trae

- Conductas observables por año (NT1/NT2). Para Transición están en el Programa Pedagógico de Transición; para Sala Cuna y Medio no hay fuente oficial equivalente.
- Los niveles de Integra (Comenzando a Profundizando) ni una rúbrica de progresión.
- Experiencias de aprendizaje concretas ni instrumentos cerrados con sus escalas (esos están en el Programa de Transición).
- Umbrales de rezago, nivel esperado por semestre o la lógica de "entra en nivel 1": eso es decisión de Integra o del equipo, no de las Bases.

## Dónde profundizar

Para el texto completo (los 206 OA uno por uno con identificadores estables como `IA-T-5`, los 8 principios, las definiciones de cada componente, la sección de evaluación entera y las consideraciones para Kimün con citas), ir a `enciclopedia-bases-curriculares.md`. Para las implicancias ya cruzadas con `PLAN.md` y la relación con la rúbrica de Integra y el Programa de Transición, ir a `hallazgos-bases-curriculares.md`. Las conductas observables por OA y la escala de apoyo están en `hallazgos-programa-pedagogico-transicion.md` y en `datos/curriculo_transicion.json`.
