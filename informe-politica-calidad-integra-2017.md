# Informe: Política de Calidad Educativa de Integra (2017)

**Autor:** Fabián Pereira
**Fecha:** 14 de octubre de 2026, 22:31 (hora de Santiago, UTC−3)
**Proyecto:** AWS Breaking Barriers Chile 2026 · Desafío 1 de Fundación Integra, "IA para el Desarrollo Infantil: de la Observación a la Acción"
**Documento analizado:** *Política de Calidad Educativa de Integra*, segunda edición, 2017 (120 páginas)

---

## 1. Resumen del documento

Es el documento marco que define qué entiende Integra por **educación parvularia de calidad**. Fue construido con un proceso participativo de más de 9.000 personas (niños y niñas, familias y trabajadores). Contiene:

- **Declaraciones estratégicas:** visión, misión (en 2017, niños y niñas de 3 meses a 4 años) y valores (calidad, inclusión, participación, respeto, confianza, transparencia y apreciación de los talentos).
- **Historia institucional** de los instrumentos de evaluación y de las políticas de Integra.
- **Concepto de calidad:** contextual y en desarrollo, no un conjunto de indicadores universales estandarizados.
- **Declaración de la política:** la calidad tiene como centro el **bienestar**, el **aprendizaje oportuno y pertinente** y el **protagonismo** de los niños y niñas, principalmente a través del juego.
- **Cinco condiciones** para lograrla: personas y equipos agentes de cambio; ambientes educativos y laborales enriquecidos; alianza con las familias; alianza con la comunidad; y un sistema de gestión al servicio de los jardines.
- **Cuatro componentes**, cada uno con ejes estratégicos:
  1. Bienestar y protagonismo de niños y niñas.
  2. Educación transformadora (aquí está la **evaluación educativa**).
  3. Familias y comunidades comprometidas con la educación.
  4. Personas y equipos que trabajan por la educación.

> **Advertencia de vigencia:** el documento es de 2017. Es anterior a las Bases Curriculares de 2018 y al Referente Curricular 2025, por lo que algunos elementos (nombres de núcleos, versión del IEA) están desactualizados. Sirve para entender la **lógica institucional**, no para tomar detalles operativos.

## 2. Lo más relevante para el proyecto

### 2.1 El sistema de evaluación de Integra (componente Educación Transformadora, eje 4)

Integra organiza la evaluación en **dos niveles**:

| Nivel | Instrumento | Para qué sirve |
|---|---|---|
| **Establecimiento** (retroalimenta la planificación y la práctica) | **EEDP** (Escala de Evaluación del Desarrollo Psicomotor) | Conocer el desarrollo psicomotor de niños y niñas de **0 a 2 años** y dar apoyos individuales |
| | **IEA "Evaluar para aprender"** | Evaluar **niveles de logro y movilidad de los aprendizajes**, orientar la planificación y **retroalimentar a las familias** |
| | **SFPP** (Sistema de Fortalecimiento de las Prácticas Pedagógicas) | Observar y retroalimentar las prácticas de los equipos |
| **Regional y nacional** (decisiones institucionales y cuenta pública) | **PLAEP-R** | Prueba estandarizada aplicada a una muestra; permite comparar resultados |

Principios declarados de la evaluación:
- Se basa en la **valoración de la diversidad** y en una **visión constructivista** del aprendizaje.
- La **observación es la fuente fundamental** de información sobre qué y cómo aprenden los niños y niñas.
- Su propósito es que la evaluación sea **fuente de aprendizaje** y sirva para **tomar decisiones**.

**Implicancias para la app:**
- La app trabaja exactamente sobre la fuente que Integra considera fundamental: la observación.
- Las salidas de la app deberían cubrir los tres usos del IEA: **movilidad o progreso de cada niño o niña**, **apoyo a la planificación** y **retroalimentación a las familias**.
- El EEDP indica que en sala cuna ya existe una escala específica de desarrollo psicomotor. La app no debe presentarse como un instrumento de tamizaje clínico; debe complementar, no reemplazar.

### 2.2 El ciclo evaluación → planificación

El documento muestra cómo los resultados de evaluación alimentan la planificación:
- La planificación es **anual** (fases inicial, de implementación y de cierre) y **diaria**, con períodos permanentes (acogida, alimentación, descanso, higiene) y **períodos variables** centrados en aprendizajes específicos, dos veces al día.
- En la **quincena** debe haber una oferta integral que cubra **todos los núcleos**.
- En 2017 había **núcleos priorizados**: dos nacionales (Lenguaje Verbal y Relaciones Lógico-matemáticas) y uno elegido por cada jardín **según los resultados del IEA** y el diagnóstico del equipo.

**Implicancias para la app:**
- Un dashboard a nivel de **grupo** es tan importante como el perfil individual: ayuda a decidir qué núcleos priorizar y qué experiencias planificar.
- La app puede mostrar la **cobertura de núcleos en la quincena**: qué núcleos tienen observaciones recientes y cuáles no. Así ayuda a mantener la oferta integral que pide la política.
- Las sugerencias deben conectarse con la planificación (experiencias para el grupo), no quedar como datos sueltos.

### 2.3 Concepto de calidad: contextual, no estandarizado

Integra adopta explícitamente una **visión contextual** de la calidad y la contrasta con la visión que busca estandarizar indicadores universales sin considerar contextos. Distingue **criterios generales** (comunes a todos) y **criterios específicos** (propios de cada comunidad).

**Implicancias para la app:**
- Refuerza la decisión de tratar la **rúbrica como dato configurable** y no como reglas fijas en el código.
- Las sugerencias de la app deben ser **flexibles y explicables**, y nunca un puntaje cerrado que reemplace el juicio del equipo.

### 2.4 Bienestar y desarrollo infantil temprano

El componente de bienestar presenta un modelo de **Desarrollo Infantil Temprano con seis dimensiones**: seguridad y protección, salud y nutrición, afecto y buen trato, educación temprana, juego y recreación, y participación y protagonismo infantil. Usa además el modelo ecológico de Bronfenbrenner (el niño o niña en sus distintos entornos).

Dos ideas clave del documento:
- El desarrollo es **multifuncional y sistémico**: el avance en una dimensión impulsa a otras y, a la inversa, **el retraso en un área puede gatillar retrasos en otras**.
- Aunque cada niño o niña tiene su propio ritmo, existen **factores de desarrollo comunes** que permiten planificar el acompañamiento.

**Implicancias para la app:**
- El perfil del niño o niña debería permitir una **vista cruzada entre dominios o núcleos**, para ver si una brecha en un área coincide con otras.
- Los "factores comunes" justifican usar una referencia por edad como **contexto**, siempre respetando ritmos individuales.

### 2.5 Protección de derechos: una barrera de seguridad necesaria

El documento exige **mecanismos pertinentes y oportunos frente a situaciones de vulneración de derechos**, con protocolos de prevención, protección y derivación a redes especializadas.

**Implicancias para la app:**
- Las educadoras escribirán libremente en el chat. Si un registro sugiere una posible vulneración (por ejemplo, señales de maltrato), la app **no debe procesarlo como evidencia de aprendizaje** ni resumirlo en un dashboard. Debe alertar a la educadora para que active el protocolo institucional.
- Esto refuerza la necesidad de un manejo cuidadoso de la información sensible, como pide el desafío.

### 2.6 Inclusión, diversidad y talentos

Integra se compromete con una educación inclusiva que atienda las **necesidades educativas especiales y los talentos** de todos los niños y niñas, sin prácticas discriminatorias.

**Implicancias para la app:**
- Evitar etiquetas que estigmaticen ("rezagado"). Hablar de **evidencia y oportunidades**, como ya se planificó.
- Mostrar también **fortalezas y talentos**, no solo vacíos.
- Permitir trayectorias diversas y registrar adecuaciones (por ejemplo, niños o niñas con NEE).

### 2.7 Protagonismo infantil

Los niños y niñas son protagonistas de su aprendizaje: eligen materiales, dónde jugar y con quién, y proponen acciones. Se debe escuchar su voz.

**Implicancias para la app:**
- Permitir registrar **intereses, preferencias y palabras del propio niño o niña**, no solo conductas observadas. Esto enriquece las sugerencias de experiencias.

### 2.8 Familias

La política pide **socializar los resultados de aprendizaje con las familias** y desplegar estrategias conjuntas entre familia y equipo educativo (materiales para el hogar, participación en experiencias). Menciona canales como la libreta de comunicaciones, reuniones y boletines.

**Implicancias para la app:**
- Una funcionalidad de **resumen para la familia**, en lenguaje simple y siempre validado por la educadora antes de enviarse, con sugerencias de juego en casa.
- Esto conecta con el uso declarado del IEA y suma valor al pitch.

### 2.9 Personas y equipos: el argumento del bienestar laboral

El documento afirma que **equipos bien tratados están en mejores condiciones de cuidar** y establece la **calidad de vida laboral** como eje estratégico.

**Implicancias para la app:**
- Respalda el KPI del desafío: reducir las horas de escritorio no es solo eficiencia, es **bienestar de las trabajadoras**, un objetivo institucional explícito.
- La planificación la lideran **la directora y las educadoras** con reflexión colaborativa del equipo. La app debería contemplar **roles** (educadora, técnico o asistente, directora) y apoyar la reflexión en equipo.

### 2.10 Sistema de gestión e información

Integra declara un sistema **integrado** que conecta los niveles nacional, regional y de jardín, con información **clara, precisa y oportuna**.

**Implicancias para la app:**
- Dashboards agregados y **anonimizados** para directoras y equipos regionales son coherentes con la política y son un buen argumento de escalabilidad.

## 3. Síntesis: qué refuerza y qué agrega al plan

**Refuerza:**
- Basarse en la **observación** como fuente principal.
- La **rúbrica configurable** (visión contextual de la calidad).
- **Sugerir sin decidir**: el juicio es del equipo, con evidencia visible.
- El KPI de tiempo como parte del **bienestar laboral**.

**Agrega:**
1. **Vista de grupo** y cobertura de núcleos por quincena para apoyar la planificación.
2. **Barrera de protección de derechos**: detectar posibles vulneraciones y derivarlas al protocolo, sin procesarlas como evaluación.
3. **Fortalezas y talentos** en el perfil, no solo vacíos.
4. **Voz del niño o niña**: registrar intereses y preferencias.
5. **Resumen para familias**, validado por la educadora.
6. **Roles** y apoyo a la reflexión en equipo.
7. **Complementar, no reemplazar** instrumentos existentes (EEDP, IEA, PLAEP-R).
