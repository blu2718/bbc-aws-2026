# Hallazgos: Bases Curriculares de la Educación Parvularia (MINEDUC, 2018)

- Autores: Fabián Pereira y Julio Yáñez, 14 de octubre de 2026. Este archivo unifica `informe-bases-curriculares-2018.md` con la versión anterior de estos hallazgos.
- Archivo: `bases-curriculares-educacion-parvularia-2018.pdf` (136 páginas, reimpresión de diciembre de 2018).
- Fuente: <https://www.curriculumnacional.cl/614/articles-69957_bases.pdf>
- Autor del documento: Subsecretaría de Educación Parvularia, MINEDUC.
- Datos derivados: `oa_bases_curriculares_2018.csv`, con los 206 OA (detalle al final).
- Páginas: se citan las impresas. En el PDF hay que sumar 2.

## Qué es

Es el marco curricular nacional de la educación parvularia. Define qué y para qué deben aprender los niños desde los primeros meses hasta el ingreso a la educación básica. Todo programa propio debe cubrir sus OA (Programa Pedagógico de Transición, p. 8). El Programa Pedagógico de Transición los lleva a la sala para NT1 y NT2, y el Referente Curricular de Integra se declara coherente con ellas. Reemplazan a las Bases de 2001.

Tiene tres capítulos:

1. **Fundamentos.** Enfoque de derechos, inclusión, familia y comunidad, y 8 principios pedagógicos: bienestar, unidad, singularidad, actividad, juego, relación, significado y potenciación (p. 30).
2. **Organización curricular.** Ámbitos, núcleos, niveles y OA. Es la parte central para el proyecto.
3. **Contextos para el aprendizaje.** Planificación y evaluación, ambientes de aprendizaje, y familia y comunidad.

Cambios respecto de 2001:
- se pasa de ciclos de 3 años a tramos de 2 años;
- los "aprendizajes esperados" pasan a llamarse Objetivos de Aprendizaje (OA);
- los núcleos del ámbito Desarrollo Personal y Social se vuelven transversales.

## Por qué es útil

### 1. Fija la estructura oficial (pp. 36–41)

| Componente | Qué es |
|---|---|
| Ámbitos (3) | Grandes campos donde se organizan los OA |
| Núcleos (8) | Focos de experiencias que agrupan OA |
| Niveles curriculares (3) | Tramos de 2 años: "1° Nivel (Sala Cuna) hacia los dos años; 2° Nivel (Medio) hacia los cuatro años y 3° Nivel (Transición) hacia los seis años" (p. 41) |
| Objetivos de Aprendizaje (206) | Lo esperado al final de cada nivel |

- "Se organizan de acuerdo a ocho núcleos y tres niveles educativos" (p. 40).
- Los OA "se enuncian desde lo que se espera al final de cada nivel, es decir abarcando tramos curriculares de dos años" (p. 40). Coincide con el modelo de Integra: 8 niveles en 2 años, con el nivel 8 como lo esperado al salir.
- Hay una diferencia de núcleos. La presentación de Integra habla de 10, mientras que la mentora (`dudas-integra.txt`) y las Bases hablan de 8. `PLAN.md` asume 8.

### 2. Trae los OA de los tres niveles

Coinciden dos conteos independientes: el CSV y un conteo automático sobre el PDF. Además, el total de Transición coincide con el del Programa Pedagógico (85).

| Ámbito | Núcleo | Sala cuna | Medio | Transición | Total |
|---|---|---:|---:|---:|---:|
| Desarrollo Personal y Social (transversal) | Identidad y Autonomía (IA) | 7 | 12 | 13 | 32 |
| | Convivencia y Ciudadanía (CC) | 6 | 10 | 11 | 27 |
| | Corporalidad y Movimiento (CM) | 7 | 8 | 9 | 24 |
| Comunicación Integral | Lenguaje Verbal (LV) | 8 | 8 | 10 | 26 |
| | Lenguajes Artísticos (LA) | 6 | 7 | 7 | 20 |
| Interacción y Comprensión del Entorno | Exploración del Entorno Natural (EEN) | 5 | 9 | 12 | 26 |
| | Comprensión del Entorno Sociocultural (CES) | 5 | 7 | 11 | 23 |
| | Pensamiento Matemático (PM) | 6 | 10 | 12 | 28 |
| **Total** | | **50** | **71** | **85** | **206** |

Los OA de sala cuna y medio llenan el vacío del Programa Pedagógico, que solo cubre Transición. Sus redacciones ya describen conductas que se pueden observar. Ejemplos de sala cuna:

- IA 1: "Expresar vocal, gestual o corporalmente distintas necesidades o emociones (alegría, miedo, pena, entre otras)."
- IA 2: "Manifestar satisfacción cuando percibe que adultos significativos le expresan afecto."

### 3. Características de los OA que importan para la app

- **Se pueden evidenciar de muchas formas.** "El párvulo que ha adquirido el aprendizaje especificado en alguno de los objetivos de estas Bases, lo puede evidenciar a través de diferentes desempeños concretos" (p. 40). La app no debe buscar coincidencias exactas de texto, sino interpretar la conducta. Eso justifica que el modelo asocie notas libres a OA.
- **Son metas de fin de tramo, no de año ni de mes.** En sala cuna vienen "con una estructura más secuenciada" y en medio y transición la secuencia es más flexible (p. 40). Por eso las Bases no dicen en qué nivel fino está un niño dentro del tramo: eso es lo que agrega la rúbrica de 8 niveles de Integra.
- **El nivel esperado es una referencia blanda.**
  - "Una temporalidad más corta de prescripción, anual, por ejemplo, tiene el inconveniente de que no respetaría diferencias individuales en el aprendizaje" (p. 40).
  - Los tramos orientan "los periodos óptimos, pero en ningún caso implica limitar las expectativas de progreso de los párvulos que no se ajustan a ellos" (p. 42).
- **Admiten trayectorias flexibles.** Para la inclusión se pueden seleccionar OA de otro nivel, según el Decreto N°83/2015 de adecuaciones curriculares (p. 107).
- **Los OA del ámbito Desarrollo Personal y Social son transversales.** Deben estar presentes de forma permanente en la planificación.

### 4. Su enfoque de evaluación coincide con el diseño de la herramienta (pp. 104–112)

1. **Evaluación para el aprendizaje, no solo del aprendizaje.** Es una herramienta de apoyo, no un juicio final.
2. **Criterios de logro.** Los equipos deben especificar "algunos criterios para reconocerlo como logrado". Es lo que hace nuestra rúbrica provisoria.
3. **Evidencia cotidiana.** "Son múltiples las formas de recogida de información (por ejemplo, fotografías, grabaciones, observaciones)", y "no es imprescindible construir situaciones especiales ni momentos formales de evaluación". Es evaluación auténtica.
4. **Documentación pedagógica.** Observar, documentar e interpretar ideas, anécdotas y conflictos de cada niño en distintos momentos.
5. **La educadora concluye.** "Reunidas las evidencias, el o la educadora debe construir una conclusión evaluativa acerca del desempeño del párvulo, teniendo en cuenta la distancia entre lo que él o ella es capaz de hacer y lo que plantea el objetivo de aprendizaje." Es el mismo flujo de nuestra propuesta con evidencia más la validación humana.
6. **Medios habituales.** "Registros de observación, piezas audiovisuales, listas de cotejo, escalas de apreciación, informes al/del hogar, portafolios y documentación pedagógica."
7. **Retroalimentación al niño**, con lenguaje acogedor que valore la diversidad de ritmos.
8. **Autoevaluación** de los propios párvulos, de forma progresiva.
9. **Más individual en los más pequeños.** "Mientras más pequeños los párvulos, las planificaciones y la evaluación deben tener un carácter más individual, integral y flexible" (p. 106).
10. **Formativa y sumativa.** La formativa identifica logros y dificultades durante el proceso. La sumativa verifica logros y suele servir para informar a las familias y decidir la transición entre niveles, siempre "sin juicios perentorios" (p. 112).

## Qué no trae

- Conductas observables por año. Para Transición están en el Programa Pedagógico; para sala cuna y medio no tenemos una fuente oficial equivalente.
- Los 8 niveles de Integra ni una rúbrica.
- Experiencias de aprendizaje ni instrumentos concretos.

## Relación con lo que ya tenemos

- **Programa Pedagógico de Transición.** Aporta unas 500 conductas observables para los mismos 85 OA de Transición.
- **Rúbrica de 8 niveles de Integra.** Las Bases dan el qué (OA por tramo de 2 años) y la rúbrica probablemente da el cuánto (8 niveles por núcleo). La rúbrica puede entrar como una capa sobre el mismo catálogo, que es lo que hace el mapeo provisorio de `PLAN.md`.
- **Dataset E-1 (0 a 36 meses).** Sus edades corresponden a sala cuna y a parte de medio, cuyos OA oficiales están aquí. Sus 5 dominios calzan aproximadamente con núcleos de las Bases:

  | Dominio E-1 | Núcleo más cercano |
  |---|---|
  | Motor fino y motor grueso | Corporalidad y Movimiento |
  | Lenguaje y comunicación | Lenguaje Verbal |
  | Socioemocional | Identidad y Autonomía, y Convivencia y Ciudadanía |
  | Cognitivo | Pensamiento Matemático, y Exploración del Entorno Natural |

  Lenguajes Artísticos y Comprensión del Entorno Sociocultural no tienen equivalente. La correspondencia es nuestra, no oficial, y conviene presentarla como aproximada.

## Implicancias para la app

La última columna indica si `PLAN.md` ya las recoge.

| Implicancia | En `PLAN.md` |
|---|---|
| Usar los nombres, siglas y OA de las Bases como fuente de verdad | Sí |
| Vincular cada registro con uno o más OA, citando el fragmento; la educadora confirma o corrige | Sí (Tasks 5 y 6) |
| Redactar las alertas como sugerencias de revisión y tratar el nivel esperado como referencia blanda | Sí |
| Formatos de evidencia: foto, audio y texto (las Bases también reconocen el video) | Sí, sin video en el MVP |
| Cargar los 206 OA del CSV como catálogo, con la jerarquía ámbito → núcleo → nivel → OA | Parcial: Task 1 carga solo los 85 de Transición, porque la demo usa solo Transición |
| Criterios de logro por OA, editables por el equipo | Parcial: la rúbrica provisoria se edita en el panel de administración |
| Matriz de cobertura por OA: si hay evidencia, cuánta y qué tan reciente | Sí (Task 3) |
| Estado por OA con la escala del IEA: sin evidencia, incipiente, en desarrollo, adquirido (ver `docs/log-desafio-integra-e1.md`) | No: el plan usa niveles 1 a 8 por núcleo y nivel de apoyo por observación |
| Vista que destaque los núcleos transversales | No |
| Trayectorias flexibles: OA de un nivel adyacente sin marcarlo como "fuera de rango" | No |
| Más detalle individual en sala cuna | Fuera del alcance (la demo es Transición) |
| Resumen para la familia, validado por la educadora | Fuera del MVP |
| Voz del niño: sus apreciaciones e intereses | Descartado por el equipo |

## Preguntas para Integra

1. ¿Cuáles son los 10 núcleos de la presentación, si las Bases tienen 8?
2. ¿Cómo se relacionan los 8 niveles de la rúbrica con los 3 niveles curriculares?
3. ¿Los equipos ya tienen criterios de logro definidos para cada OA, como piden las Bases?
4. ¿La rúbrica trabaja directamente con los OA de las Bases o con indicadores propios?

## Sobre `oa_bases_curriculares_2018.csv`

Contiene los 206 OA con estas columnas:

| Columna | Contenido |
|---|---|
| `id_oa` | Identificador, por ejemplo `IA-SC-01` |
| `ambito` | Ámbito |
| `nucleo` | Núcleo |
| `nivel_curricular` | Sala Cuna, Medio o Transición |
| `numero` | Número del OA dentro del núcleo y nivel |
| `transversal` | `si` o `no` |
| `texto` | Texto del OA |

Se extrajo automáticamente del PDF y se verificó que la numeración de cada núcleo y nivel fuera continua. Los conteos por núcleo y nivel coinciden con la tabla anterior. Conviene revisar algunos textos contra el original antes de usarlo en producción.
