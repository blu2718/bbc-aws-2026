# Informe: Bases Curriculares de la Educación Parvularia (2018)

**Autor:** Fabián Pereira
**Fecha:** 14 de octubre de 2026, 22:37 (hora de Santiago, UTC−3)
**Proyecto:** AWS Breaking Barriers Chile 2026 · Desafío 1 de Fundación Integra, "IA para el Desarrollo Infantil: de la Observación a la Acción"
**Documento analizado:** *Bases Curriculares de la Educación Parvularia*, Subsecretaría de Educación Parvularia, Ministerio de Educación de Chile (versión 2018, reimpresión de diciembre de 2018, 136 páginas)
**Archivo complementario:** `oa_bases_curriculares_2018.csv` (catálogo de los 206 Objetivos de Aprendizaje extraídos del documento)

---

## 1. Resumen del documento

Las Bases Curriculares (BCEP) son el **currículum nacional obligatorio** de la educación parvularia en Chile: definen **qué y para qué** deben aprender los niños y niñas desde los primeros meses hasta el ingreso a la educación básica. Todas las instituciones, incluida Integra, trabajan sobre ellas. Actualizan las bases de 2001.

El documento tiene tres capítulos:

1. **Fundamentos:** enfoque de derechos, inclusión, rol de la familia y la comunidad, y **8 principios pedagógicos** (bienestar, unidad, singularidad, actividad, juego, relación, significado y potenciación).
2. **Organización curricular:** la estructura de ámbitos, núcleos, niveles y Objetivos de Aprendizaje (la parte central para el proyecto).
3. **Contextos para el aprendizaje:** planificación y **evaluación**, ambientes de aprendizaje, y familia y comunidad.

Principales cambios respecto de 2001: se pasa de ciclos de 3 años a **tramos de 2 años**; los "aprendizajes esperados" pasan a llamarse **Objetivos de Aprendizaje (OA)**, redactados para ser **fundamentales, observables y susceptibles de progresar**; y los núcleos del ámbito personal y social se vuelven **transversales**.

## 2. Por qué este documento es clave para el proyecto

Es la **fuente oficial y pública** más cercana a la rúbrica que nos falta. La rúbrica de Integra (10 núcleos, 8 niveles, 3 niveles educativos) casi con seguridad está construida sobre estas bases: comparte los mismos 3 niveles educativos y usa núcleos de las BCEP (por ejemplo, Identidad y Autonomía). Mientras Integra no entregue su rúbrica, **los OA de las BCEP son el mejor catálogo real que podemos usar**, mucho más fiel que la ruta sintética de 9 niveles del dataset.

## 3. La estructura curricular

| Componente | Qué es |
|---|---|
| **Ámbitos** (3) | Grandes campos donde se organizan los OA |
| **Núcleos** (8) | Focos de experiencias que agrupan OA |
| **Niveles curriculares** (3) | Tramos de 2 años: Sala Cuna (hacia los 2 años), Medio (hacia los 4) y Transición (hacia los 6) |
| **Objetivos de Aprendizaje** (206) | Aprendizajes esperados al **final** de cada nivel |

### Cantidad de OA por núcleo y nivel (extraídos del documento)

| Ámbito | Núcleo | Sala Cuna | Medio | Transición | Total |
|---|---|---:|---:|---:|---:|
| Desarrollo Personal y Social (transversal) | Identidad y Autonomía | 7 | 12 | 13 | 32 |
| | Convivencia y Ciudadanía | 6 | 10 | 11 | 27 |
| | Corporalidad y Movimiento | 7 | 8 | 9 | 24 |
| Comunicación Integral | Lenguaje Verbal | 8 | 8 | 10 | 26 |
| | Lenguajes Artísticos | 6 | 7 | 7 | 20 |
| Interacción y Comprensión del Entorno | Exploración del Entorno Natural | 5 | 9 | 12 | 26 |
| | Comprensión del Entorno Sociocultural | 5 | 7 | 11 | 23 |
| | Pensamiento Matemático | 6 | 10 | 12 | 28 |
| | **Total** | **50** | **71** | **85** | **206** |

Ejemplos de OA de Sala Cuna:
- *Identidad y Autonomía:* "Expresar vocal, gestual o corporalmente distintas necesidades o emociones (alegría, miedo, pena, entre otras)."
- *Pensamiento Matemático:* adquirir la noción de permanencia de objetos y personas significativas mediante juegos.

> **Nota:** las BCEP tienen **8 núcleos**, pero la presentación de Integra habla de **10**. La diferencia no se explica en ningún documento revisado. Es una pregunta pendiente para la contraparte.

### Características importantes de los OA

- **Se redactan para ser observables.** Esto los hace ideales para que un LLM vincule notas de las educadoras con objetivos concretos.
- **Un mismo OA puede manifestarse de muchas formas.** El documento lo dice explícitamente: un niño o niña puede evidenciar el aprendizaje mediante distintos desempeños concretos. La app no debe buscar coincidencias exactas de texto, sino interpretar la conducta.
- **Se enuncian para el final de un tramo de 2 años**, no por año ni por mes. En Sala Cuna están más secuenciados (por la mayor incidencia del desarrollo); en Medio y Transición la secuencia es más flexible. Por eso, **las BCEP no dicen en qué nivel fino está un niño o niña dentro del tramo**: eso es lo que agregaría la rúbrica de 8 niveles de Integra.
- **Trayectoria flexible.** Los tramos son una referencia de períodos óptimos, pero **no deben limitar las expectativas** de quienes no se ajustan a ellos. Para la inclusión, se pueden seleccionar OA de un nivel distinto al del grupo (Decreto 83/2015 sobre adecuaciones curriculares).
- **Los OA del ámbito personal y social son transversales**: deben estar presentes de forma permanente en toda la planificación.

## 4. Lo que dicen las BCEP sobre la evaluación

Este es el apartado más directamente aplicable al cuello de botella del proyecto (capítulo 3, "Consideraciones para la evaluación"):

1. **Evaluación para el aprendizaje, no solo del aprendizaje.** Es una herramienta de apoyo, no un juicio final.
2. **Los equipos deben definir colectivamente criterios para reconocer un OA como logrado.** Es decir, las propias BCEP esperan que cada equipo especifique sus criterios.
3. **La evidencia se recoge en situaciones cotidianas** (fotos, grabaciones, observaciones; un cumpleaños, un paseo, una actividad). No hace falta crear momentos formales de evaluación: es **evaluación auténtica**.
4. **Documentación pedagógica:** observar, documentar e interpretar ideas, anécdotas y conflictos de cada niño o niña en distintos momentos.
5. **La conclusión evaluativa la construye la educadora**, considerando **la distancia entre lo que el niño o niña es capaz de hacer y lo que plantea el OA**, siempre para decidir cómo apoyarlo mejor.
6. **Instrumentos habituales:** registros de observación, piezas audiovisuales, listas de cotejo, escalas de apreciación, informes al y del hogar, portafolios y documentación pedagógica.
7. **Retroalimentación** al niño o niña con lenguaje acogedor, que valore la diversidad de ritmos.
8. **Autoevaluación** de los propios párvulos, de forma progresiva.
9. **Mientras más pequeños, más individual, integral y flexible** debe ser la planificación y la evaluación.
10. **Formativa y sumativa:** la formativa identifica logros y dificultades durante el proceso; la sumativa verifica logros y suele usarse para **informar a las familias** y decidir la transición entre niveles, siempre sin juicios perentorios.

## 5. Implicancias concretas para la app

### 5.1 Usar los OA como catálogo real desde hoy

- Cargar los 206 OA del archivo `oa_bases_curriculares_2018.csv` como catálogo base, con la jerarquía ámbito → núcleo → nivel → OA.
- El LLM vincula cada registro de la educadora con uno o más OA y cita el fragmento que lo respalda; la educadora confirma o corrige.
- Esto **reemplaza la ruta sintética del dataset** por un currículum oficial, y es un argumento fuerte ante el jurado: la app funciona sobre lo que Integra ya usa.

### 5.2 La regla de sugerencia ahora tiene respaldo oficial

Las BCEP piden exactamente lo que planificamos:
- **"Criterios definidos por el equipo"** → cada OA puede tener un campo editable de criterios de logro, que el equipo ajusta. Así las reglas de sugerencia son configurables y legítimas.
- **"Distancia entre lo que hace y lo que plantea el OA"** → es la matriz de cobertura: por cada OA, si hay evidencia, cuánta y qué tan reciente.
- Un estado por OA puede seguir la escala del IEA, que las educadoras ya conocen: **sin evidencia → incipiente → en desarrollo → adquirido** (este último siempre confirmado por la educadora).

### 5.3 Diseño alineado con el currículum

- **Vista de núcleos transversales:** destacar Identidad y Autonomía, Convivencia y Ciudadanía, y Corporalidad y Movimiento, que deben aparecer de forma permanente.
- **Trayectorias flexibles:** permitir que un niño o niña tenga OA de un nivel adyacente (por adecuación o por avance), sin marcarlo como "fuera de rango".
- **Más detalle individual en Sala Cuna,** donde los OA están más secuenciados y la evaluación debe ser más individual.
- **Formatos de evidencia:** foto, audio, video y texto ya son los medios que las BCEP reconocen.
- **Resumen para la familia** (uso sumativo), con lenguaje acogedor y validado por la educadora.
- **Voz del niño o niña:** espacio para registrar sus propias apreciaciones (autoevaluación).

### 5.4 Puente con el dataset para la demo

El dataset usa 5 dominios del desarrollo; su correspondencia aproximada con los núcleos de las BCEP es:

| Dominio del dataset | Núcleo BCEP más cercano |
|---|---|
| Motor grueso y motor fino | Corporalidad y Movimiento |
| Lenguaje y comunicación | Lenguaje Verbal |
| Socioemocional | Identidad y Autonomía; Convivencia y Ciudadanía |
| Cognitivo | Pensamiento Matemático; Exploración del Entorno Natural |

Lenguajes Artísticos y Comprensión del Entorno Sociocultural no tienen equivalente en el dataset. La correspondencia es aproximada y conviene presentarla como tal.

### 5.5 Cómo encaja la rúbrica de 8 niveles cuando llegue

Las BCEP dan el **qué** (los OA por tramo de 2 años). La rúbrica de Integra probablemente da el **cuánto** (8 niveles de progresión por núcleo). En la app, la rúbrica podría entrar como una **capa adicional** sobre el mismo catálogo, sin rehacer nada: cada nivel de la rúbrica se asociaría a un conjunto de OA o conductas.

## 6. Preguntas que este documento deja para Integra

1. ¿Cuáles son los 10 núcleos de la rúbrica, si las BCEP tienen 8?
2. ¿Cómo se relacionan los 8 niveles de la rúbrica con los 3 niveles curriculares (por ejemplo, niveles 1 a 3 en Sala Cuna)?
3. ¿Los equipos de Integra tienen criterios de logro ya definidos para cada OA, como piden las BCEP?
4. ¿La rúbrica trabaja directamente con los OA de las BCEP o con indicadores propios?

## 7. Sobre el archivo complementario

`oa_bases_curriculares_2018.csv` contiene los 206 OA con las columnas: `id_oa` (por ejemplo, `IA-SC-01`), `ambito`, `nucleo`, `nivel_curricular`, `numero`, `transversal` y `texto`. Se extrajo automáticamente del PDF y se verificó que la numeración de cada núcleo y nivel sea continua. Conviene revisar algunos textos contra el original antes de usarlo en producción.
