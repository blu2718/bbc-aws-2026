# Guía de la Política de Calidad Educativa de Integra (2017) para agentes de IA

Documento de referencia exhaustivo sobre la Política de Calidad Educativa de Integra, segunda edición, 2017 (120 páginas). Pensado como guía moral de Kimün: qué valora Integra, qué entiende por calidad, y qué exige (y qué prohíbe) eso a cada decisión de diseño, de IA y de producto.

Fuente: <https://integra.cl/wp-content/uploads/2018/03/POLITICA-DE-CALIDAD-EDUCATIVA-2017-2.pdf> (el PDF no se versiona). Resumen para el equipo en `resumen-politica-calidad.md`; implicancias ya cruzadas con `PLAN.md` en `hallazgos-politica-calidad-educativa-integra.md`. Autor: Fundación Integra, 2017. Registro de Propiedad Intelectual 262448, ISBN 978-956-8482-62-6. Textos: Oriele Rossel, Karen Pérez Molina (coord.) y equipo (p. 1). "Derechos reservados, prohibida su reproducción" (p. 1): por eso no se transcribe en bloque; aquí se parafrasea y solo se citan frases breves.

## Cómo usar esta guía

Para qué sirve. Es la brújula ética de Kimün. Antes de diseñar una funcionalidad, redactar un prompt, elegir una palabra para la interfaz o decidir una alerta, consulta la "Brújula" y la lista de verificación. Cada sección temática termina en un bloque "Qué exige a Kimün" con reglas de hacer/no hacer y el estado respecto de `PLAN.md`.

Convención de páginas. Las páginas citadas (p. N) son las del PDF, que coinciden con el índice de la p. 11. Verificado contra el texto extraído: el índice declara capítulo 1 en p. 13, cap. 4 en p. 21, cap. 5 en p. 23, cap. 6 en p. 31, cap. 7 en p. 39, cap. 8 en p. 45, cap. 9 en p. 67 y bibliografía en p. 114; todas calzan con el contenido en esas páginas. Cita siempre la página.

Aviso de vigencia. El documento es de 2017, anterior a las Bases Curriculares de la Educación Parvularia 2018 y al Referente Curricular de Integra 2025. Su vocabulario curricular está desactualizado: usa "aprendizajes esperados" (p. 87), núcleos antiguos como "Relaciones Lógico-matemáticas", "Seres vivos y su entorno" y "Grupos humanos" (p. 87), y "Primer/Segundo Ciclo" (p. 87). No uses ese vocabulario en la app. Lo que no caduca son sus principios: enfoque de derechos, calidad contextual, bienestar, protagonismo, juego, buen trato, inclusión, evaluación por observación sin juicios perentorios. La guía distingue siempre principio (vigente) de vocabulario (caduco).

Índice.
- Brújula: principios rectores y lista de verificación.
- 1. Declaraciones estratégicas (visión, misión, valores).
- 2. Presentaciones y palabras de terceros.
- 3. Por qué una política y qué contiene.
- 4. Contexto nacional e institucional.
- 5. Historia institucional e instrumentos de evaluación.
- 6. Proceso participativo.
- 7. Bases: enfoque de derechos e inclusión.
- 8. Concepto de calidad.
- 9. La política propiamente tal: declaración y condiciones.
- 10. Desplegando los conceptos clave (niño, felicidad, convivencia bientratante, PEI, bienestar, aprendizaje oportuno, protagonismo, personas y equipos, ambientes, familias, comunidad, gestión).
- 11. "Lo esencial de la calidad educativa" (gráfica).
- 12. Componente 1: Bienestar y Protagonismo (DIT, modelo ecológico, 5 ejes).
- 13. Componente 2: Educación Transformadora (fundamentos, 4 ejes, evaluación).
- 14. Componente 3: Familias y Comunidades (5 ejes).
- 15. Componente 4: Personas y Equipos (fundamentos, 6 ejes).
- 16. Glosario.
- 17. Bibliografía relevante.
- 18. Tabla resumen de tensiones con el diseño actual.

## Brújula

Principios rectores condensados. Aplícalos a cualquier decisión.

1. El niño al centro, como sujeto de derecho. No es "beneficiario pasivo" ni un déficit a corregir; es una persona única, ciudadana, capaz de conocer y transformar el mundo (pp. 40-41, 48). Toda decisión debe pasar el filtro del interés superior del niño: lo que mejor favorezca su integridad y bienestar (p. 50).
2. La calidad tiene como centro el bienestar, el aprendizaje oportuno y pertinente y el protagonismo, principalmente a través del juego (p. 46). Es la definición operativa de calidad; todo lo demás la sirve.
3. La calidad es contextual y en desarrollo, no un conjunto de indicadores universales (p. 45). Hay criterios generales (flexibles) y específicos (de cada comunidad). No estandarizar lo que debe ser local.
4. La evaluación se sustenta en la observación como fuente fundamental, con visión constructivista y valoración de la diversidad (p. 90). Evaluar es recoger datos para valorar y luego decidir (p. 89); el juicio es humano.
5. Convivencia bientratante: relaciones de confianza, respeto e inclusión entre niños, niñas y adultos (p. 49). El buen trato es la base de todo proyecto educativo.
6. Inclusión y talentos: responder a la diversidad sin etiquetar ni excluir; modificar el sistema para acoger al niño, no al revés (p. 42). Ver también fortalezas y talentos, no solo carencias.
7. Protagonismo real: el niño elige, propone, decide y es escuchado (pp. 52-53, 77). Su voz importa.
8. Protección de derechos: prevenir, proteger y derivar ante vulneraciones; interés superior del niño como factor protector (pp. 78-79).
9. Las familias son las primeras educadoras y aliadas; socializar con ellas los resultados de aprendizaje (pp. 59, 96).
10. Las personas y equipos son agentes de cambio social; equipos bien tratados cuidan mejor (pp. 53, 80). La calidad de vida laboral es un eje, no un adorno.
11. Oferta integral por quincena que cubra todos los núcleos (p. 87). La planificación mira el grupo, no solo al individuo.
12. Transparencia y rendición de cuentas sobre la gestión (p. 61). La información debe ser clara y accesible.

Lista de verificación (preguntas sí/no para evaluar una funcionalidad, un prompt o un texto de la app).

- ¿La decisión final sobre el niño queda en manos humanas (la educadora), con evidencia visible, y la IA solo propone? (pp. 46, 89-90)
- ¿El texto evita etiquetas que estigmatizan ("rezagado", "déficit", "atrasado" como juicio) y usa el lenguaje de sugerencia de revisión, sin juicios perentorios? (pp. 42, 48; Bases 2018)
- ¿Muestra también fortalezas y talentos, no solo vacíos? (pp. 42, 54)
- ¿Respeta el ritmo individual del niño y no asume que el avance es lineal ni universal? (pp. 45, 71)
- ¿La propuesta se apoya en observación de la conducta real, separando lo que el niño hizo o dijo de la interpretación del adulto? (p. 90; Referente 2025)
- ¿Preserva la privacidad y dignidad del niño (interés superior) en el dato, el almacenamiento y lo que se muestra? (pp. 40, 50)
- ¿Hay una vista de grupo que ayude a cubrir todos los núcleos en la quincena, no solo fichas individuales? (p. 87)
- ¿Si un registro sugiere una posible vulneración de derechos, el sistema lo deriva al protocolo humano en vez de tratarlo como evidencia de aprendizaje? (pp. 78-79)
- ¿La herramienta reduce carga de escritorio de las trabajadoras sin reemplazar la reflexión pedagógica? (pp. 55, 108-110)
- ¿La rúbrica y los parámetros son configurables (contextuales), no reglas fijas en el código? (p. 45)
- ¿El vocabulario curricular es el vigente (Bases 2018), no el de 2017? (p. 87)
- ¿La herramienta complementa los instrumentos de evaluación de Integra (EEDP, IEA, PLAEP-R) sin presentarse como tamizaje clínico? (p. 90)

Si alguna respuesta es "no", hay un conflicto con la política que debe resolverse o justificarse de forma explícita.

## 1. Declaraciones estratégicas (p. 4)

La p. 4 es una infografía con dibujos de niños (revisada como imagen; el texto plano salía desordenado). Contiene las tres declaraciones:

- Visión ("lo que queremos ser"): una fundación educativa en la que niños y niñas aprenden jugando felices y transforman el mundo, contribuyendo a un Chile más inclusivo, solidario, justo y democrático.
- Misión ("lo que hacemos"): lograr desarrollo pleno y aprendizajes significativos de niños y niñas entre tres meses y cuatro años de edad, a través de un proyecto educativo de calidad, con la participación activa de los equipos de trabajo, familias y comunidad. (Nota de vigencia: el tramo "tres meses a cuatro años" es de 2017; hoy Integra atiende transición. No usar ese rango como dato operativo.)
- Valores: Calidad, Inclusión, Participación, Respeto, Confianza, Transparencia y Apreciación de los talentos.

Los valores no vienen con una definición cerrada en la p. 4; su sentido se despliega en el resto del documento (inclusión en pp. 41-42; participación como derecho en pp. 39, 94; apreciación de talentos en pp. 54, 104; transparencia en pp. 61, 107).

Qué exige a Kimün.
- Hacer: que cada decisión de producto pueda explicarse como aporte a "niños y niñas aprenden jugando felices" (visión, p. 4). Si una funcionalidad no sirve a eso, revisar su sentido.
- Hacer: que la app encarne los valores: transparencia (mostrar la evidencia detrás de cada propuesta), apreciación de talentos (destacar fortalezas), inclusión (accesibilidad y sin etiquetas), participación (la educadora decide).
- No hacer: usar el rango de edad de 2017 ni la misión literal como dato del modelo pedagógico; la demo es Transición. `PLAN.md` ya trabaja en Transición: cumple.

## 2. Presentaciones y palabras de terceros (pp. 6-9, 15)

Palabras de autoridades y expertos. Lo que aportan como señales de valor:

- Michelle Bachelet (p. 4-6, discurso 2017): los primeros años son esenciales para el desarrollo posterior; cobertura con calidad.
- Iván Núñez, Premio Nacional de Ciencias de la Educación (p. 6): valora que la política sea "paidocéntrica" (centrada en el educando y su derecho a aprender en condiciones de felicidad), sin excluir el rol de las educadoras ni el entorno enriquecido.
- Camila Vallejo (p. 6): educación como derecho social, con criterios de equidad, cohesión, colaboración e inclusión, y respeto de los derechos humanos.
- Giorgio Jackson (p. 7): sin condiciones materiales (recursos, política pública) no se llega a ninguna parte; la calidad necesita soporte.
- Lorena Fries, INDH (p. 7): releva que la política garantice el derecho a educación de calidad con base en una convivencia bientratante.
- Selma Simonstein, OMEP Chile (p. 8): el cambio es parte de la educación infantil; hay que interpretar la vida de los niños en sus contextos.
- Mónica Manhey, U. de Chile (p. 8): valora el proceso participativo y la voz de los niños, con enfoque humanista y foco en la felicidad.
- Marta Edwards, CEDEP (p. 9): la política incluye todo el sistema que influye en el bienestar; releva ambientes afectivos y buen trato; destaca que Integra evalúa constantemente sus procesos y resultados y usa la información para rendir cuentas y retroalimentar.
- Humberto Maturana (p. 9): "sólo una red de cuidado en el amar podrá conectar los derechos de los niños y las niñas al desarrollo humano deseado". El amar y la convivencia como condición del desarrollo.
- Dra. María Victoria Peralta (p. 15, presentación formal): postular una política de calidad con enfoque de derechos es un desafío mayor; obliga a abordar el tema de forma integral y sistémica, interrelacionando la multiplicidad de factores (niños, familias, educadores, comunidad) en contextos diversos. El enfoque de derechos implica que la educación de calidad es un deber del Estado, no una concesión a "beneficiarios".

Qué exige a Kimün.
- Hacer: en el pitch, apoyarse en estas voces para enmarcar la herramienta como aporte a una educación como derecho, centrada en el niño, con soporte a las trabajadoras.
- No hacer: presentar la herramienta como un fin técnico; el discurso debe ser paidocéntrico y de derechos, no "optimización de procesos" a secas. `PLAN.md` ya alinea el pitch con la definición de calidad (Task 11): cumple.

## 3. Por qué una política y qué contiene (pp. 17-21)

Por qué una política (cap. 4, pp. 21). Contar con una Política de Calidad Educativa permite a Integra organizar a la comunidad en torno a un camino común, declarar públicamente qué entiende por calidad y comprometerse a lograrla y mejorarla. Antes existían dos políticas (Bienestar y Protagonismo Infantil; Participación de Familias y Comunidad), el Referente Curricular y el Concepto de Calidad. En 2015 se optó por una gran política única, "estrategia institucional", que absorbe las anteriores como componentes. Sus características (p. 21): construida participativamente, consensuada y contextualizada, apreciativa (reconoce buenas prácticas) y dinámica (se resignifica).

Qué contiene (cap. 3, pp. 17-18). Propósito declarado (p. 18): "garantizar el derecho a una educación parvularia de calidad a los niños y niñas... para que puedan desarrollarse plenamente y ser felices, con el foco en su bienestar, aprendizaje, protagonismo y habilidades para la vida, en un marco de convivencia bientratante". El documento explica por qué se necesita la política, en qué contexto surge, cómo se construyó, la declaración y sus atributos, la gráfica "Lo esencial" y los componentes. La p. 17 recoge la voz de los niños en los diálogos regionales ("Queremos pastito y plantitas, mascotas, decir lo que queremos, que nos hagamos más cariño...").

Qué exige a Kimün.
- Hacer: tratar la política como "el lente con el cual se mira la realidad" (p. 66). Kimün es una herramienta para que ese lente se aplique mejor a los datos de aprendizaje.
- Hacer: que la herramienta sea contextualizable (parámetros editables), coherente con que la política se concreta distinto en cada comunidad (PEI). `PLAN.md` hace la rúbrica, núcleos, niveles y metas un dato editable: cumple.

## 4. Contexto nacional e institucional (cap. 5, pp. 23-29)

La calidad en primera infancia es un tema debatido, por su alta inversión y su complejidad teórico-práctica (p. 23). La educación inicial de calidad impacta en aprendizaje, autoestima, cohesión social, superación de pobreza y descenso del gasto público (pp. 23-24). Chile fue pionero (primera escuela de párvulos 1864, primer kindergarten fiscal 1906, JUNJI 1970, Integra 1990). Hitos legales relevantes (pp. 25-27): ratificación de la Convención de los Derechos del Niño (1990, rango constitucional), creación de las Bases Curriculares (BCEP, 2001), LGE 20.370 (2009, educación parvularia como primer nivel del sistema y Sistema Nacional de Aseguramiento de la Calidad con Consejo Nacional de Educación, Agencia de Calidad y Superintendencia), Chile Crece Contigo (Ley 20.379, 2009), obligatoriedad del segundo nivel de transición (Ley 20.710, 2013), Subsecretaría e Intendencia de Educación Parvularia (Ley 20.835, 2015), Desarrollo Profesional Docente (Ley 20.903, 2016).

Qué exige a Kimün.
- Hacer: ubicar la herramienta dentro del Sistema de Aseguramiento de la Calidad (la acreditación de jardines es un desafío declarado, p. 62). Argumento de escalabilidad para el pitch.
- Contexto, sin regla directa: este capítulo es historiográfico. No hay reglas de diseño nuevas más allá de reforzar el marco de derechos.

## 5. Historia institucional e instrumentos de evaluación (cap. 6, pp. 31-33, y cap. 9.2 eje 4, pp. 89-90)

Línea de tiempo de instrumentos de evaluación (p. 32):
- 2006: se crea el PLAEP (Perfil de Logros de Aprendizajes Esperados), herramienta de evaluación de niveles de logro; en 2009 se revisa y re-estandariza (PLAEP-R); su aplicación se externaliza en 2015.
- 2013: se crea el IEA, Instrumento de Evaluación de Aprendizajes "Evaluar para aprender", que retroalimenta la planificación y la práctica pedagógica.
- 2017: se inicia la implementación del SFPP (Sistema de Fortalecimiento de las Prácticas Pedagógicas).

Sistema de evaluación en dos niveles (pp. 89-90):
- Nivel establecimiento (retroalimenta planificación y práctica):
  - EEDP (Escala de Evaluación del Desarrollo Psicomotor): nivel de desarrollo psicomotor de 0 a 2 años, para apoyos específicos e individuales.
  - IEA "Evaluar para aprender": "evaluar los niveles de logro y movilidad de los aprendizajes" durante la participación en el programa, orientar la planificación y retroalimentar a las familias (cita p. 90).
  - SFPP: observación y retroalimentación de las prácticas pedagógicas; no evalúa a los niños.
- Nivel regional y nacional (decisiones institucionales y cuenta pública):
  - PLAEP-R: estandarizado, aplicado a una muestra; permite comparar rendimientos. 

Principio de evaluación (cita, p. 90): "La evaluación de los aprendizajes de los niños y niñas se sustenta en la valoración de la diversidad, la visión constructivista del aprendizaje, y el apoyo en la observación, como fuente fundamental de información sobre qué y cómo están aprendiendo los niños y niñas." Y, antes, la definición de evaluar (cita de García Ramos en Lavilla, p. 89): "identificar, recoger o tratar datos sobre elementos o hechos educativos, con el objetivo de valorarlos primero y, sobre dicha valoración, tomar decisiones."

Lectura para Kimün. La herramienta trabaja sobre la fuente que Integra considera fundamental, la observación. La "movilidad de los aprendizajes" que mide el IEA es exactamente lo que registra el historial de niveles validados de Kimün. La rúbrica de niveles de Integra probablemente sucede al IEA, pero falta confirmarlo (ver `hallazgos`, preguntas 8-9 de `PLAN.md`). La EEDP es un instrumento psicomotor para sala cuna; Kimün no debe presentarse como tamizaje clínico. Kimün automatiza el primer paso de la evaluación (recoger datos por observación) y prepara el segundo (valorar), pero el juicio valorativo y la decisión siguen siendo humanos.

Qué exige a Kimün.
- Hacer: presentar la herramienta como registro de la movilidad de aprendizajes que mide el IEA y complemento de EEDP/IEA/PLAEP-R, no como su reemplazo ni como tamizaje. `PLAN.md`: parcial. El pitch (Task 11) encaja la herramienta en el sistema de evaluación, pero `hallazgos` marca como pendiente decir explícitamente "complementa, no reemplaza, y no es tamizaje clínico". Falta esa frase explícita.
- Hacer: respetar los tres pasos de la evaluación (recoger, valorar, decidir); la IA solo asiste el primero y el segundo. `PLAN.md`: cumple (la educadora valida).
- No hacer: comparar a los niños con una norma estandarizada tipo PLAEP-R dentro de la vista de la educadora; el nivel es contextual, por conducta observable. `PLAN.md`: cumple (el nivel sale de la rúbrica y la conducta, no de una norma externa).

## 6. Proceso participativo (cap. 6, pp. 31-37)

La política se construyó con más de 9.000 personas de la Comunidad Integra: niños, familias, trabajadores y organizaciones sindicales (p. 2). Hubo diálogos regionales (2014, ~2.000 personas), consultas lúdicas a niños, encuentros, entrevistas y consultas a especialistas. Los cuatro componentes vienen de políticas previas construidas participativamente: Bienestar y Protagonismo (de la Política de Bienestar y Protagonismo Infantil, 2012-2013), Educación Transformadora (del Referente Curricular 2014), Familias y Comunidades (de la Política de Participación de Familias y Comunidad, 2011) y Personas y Equipos (del Proyecto Súmate 2015, con más de 7.000 participaciones).

Qué exige a Kimün.
- Hacer: honrar que la calidad es construida con la comunidad; validar supuestos con Integra y con las educadoras antes de fijarlos. `PLAN.md` tiene una lista de "Preguntas pendientes para Integra" y marca supuestos: cumple el espíritu.
- Hacer: incluir la voz de la educadora en el diseño (mostrarle la pantalla de revisión y preguntarle si la usaría, pregunta 6 de `PLAN.md`). `PLAN.md`: planificado.

## 7. Bases: enfoque de derechos e inclusión (cap. 7, pp. 39-42)

Enfoque de Derechos. Es la base de toda la política (p. 39). La educación es un derecho humano fundamental que posibilita el desarrollo pleno y potencia los demás derechos. Principios generales de derechos humanos (p. 39): igualdad y no discriminación, pro-persona, participación, no regresividad. El enfoque de derechos centra el desarrollo no solo en satisfacer necesidades, sino en realizar derechos como obligación jurídica. En la niñez se materializa en la Convención de los Derechos del Niño (1989; Chile 1990), con tres principios (p. 40): (a) niños y niñas son sujetos de derechos civiles, sociales y políticos; (b) el interés superior del niño debe sustentar toda medida que se tome respecto de ellos; (c) no discriminación. Cambio de mirada clave (p. 41): los niños ya no son "menores", objetos de compasión o beneficiarios pasivos con déficit, sino sujetos plenos de derechos y agentes de transformación social.

Inclusión (pp. 41-42). Integra se compromete con la inclusión porque la dignidad pasa por considerar a las personas únicas, irrepetibles y diversas. La inclusión implica (p. 42): beneficiar a todos sin etiquetar ni excluir; acceso equitativo con ajustes permanentes; valorar el aporte de cada persona. La educación inclusiva asume que el sistema educativo debe responder a la diversidad modificándose a sí mismo (currículo, métodos, evaluación, normas) en función de las características, necesidades y talentos de los niños, en vez de que el niño se adapte al sistema. El mayor desafío es responder a quienes tienen más riesgo de exclusión (vulnerabilidad social, necesidades educativas especiales, diversidad cultural).

Qué exige a Kimün. Esta es la sección más vinculante para la IA y la redacción.
- Hacer: tratar al niño como sujeto, no como déficit. Las señales y textos describen situaciones a observar, no clasifican al niño como problema. `PLAN.md`: cumple en intención (alertas "redactadas como sugerencias", Task 2), pero ver la tensión del término "rezago".
- No hacer: etiquetar ("rezagado", "atrasado", "déficit", "bajo rendimiento") como atributo del niño. La política pide "no etiquetar ni excluir" (p. 42). Tensión real: Integra pide en su correo "levantar alarma si tengo niños rezagados" y usa la palabra "rezagados" (`respuestas-integra.md`). Resolución: usar la palabra de Integra en la comunicación interna y en el pitch si es su término, pero en la interfaz dirigida a la educadora redactar como sugerencia de revisión sin adjetivar al niño ("Revisar: 3 niveles bajo sus pares en Lenguaje Verbal"), no "Niño rezagado". Las Bases 2018 piden evaluar "sin juicios perentorios"; es compatible con avisar a la educadora. `PLAN.md` ya adopta esta redacción (Task 2): cumple, pero conviene auditar cada cadena de texto de la UI para que ninguna adjetive al niño.
- Hacer: diseñar para la diversidad (accesibilidad: color + texto, tabla equivalente al gráfico, pensado primero para celular). `PLAN.md`: cumple (Tasks 2 y 3 exigen color y texto, SVG con tabla equivalente, contraste ≥ 4,5:1).
- Hacer: que el sistema se adapte al niño y a la comunidad, no al revés: parámetros editables (niveles, núcleos, metas, rúbrica). `PLAN.md`: cumple.
- Hacer: aplicar el interés superior del niño a cada decisión de datos (privacidad, qué se guarda, qué se muestra). `PLAN.md`: cumple fuerte (seudónimos para Bedrock al proponer nivel, fotos y audios borrados tras extraer el texto, S3 privado).

## 8. Concepto de calidad (cap. 8, pp. 45-46)

Características generales del concepto de calidad (p. 45), extraídas del Concepto de Calidad Educativa 2013:
- "Calidad" viene del latín qualitas, cualidad: el conjunto de cualidades o atributos centrales de la educación.
- La calidad no es un concepto único sino relativo: implica un juicio valorativo construido socialmente en un tiempo y espacio, según el contexto, los actores y las concepciones de educación, ser humano, niño y sociedad. (Esta es la visión "postmoderna"; la "moderna", que estandariza indicadores universales sin considerar contextos, se menciona y se descarta, nota 11, p. 45.)
- La calidad, aunque relativa, no es arbitraria: surge de una construcción dialogada y consensuada por los actores, con el aporte del saber especializado.
- La calidad tiene carácter normativo: orienta sobre lo importante y deseable según la concepción educativa.
- La educación es un proceso: importa tanto el resultado como la forma de llegar a él y los recursos. Ejemplo de Blanco (p. 45): dos jardines con resultados de aprendizaje similares en lenguaje no son de igual calidad si en uno hubo participación, clima seguro y resolución pacífica de conflictos y en el otro no.
- La calidad se expresa en criterios generales (operan en cualquier experiencia, flexibles y dinámicos) y criterios específicos (propios de cada comunidad, rescatan sus intereses y énfasis).
- La calidad debe verse desde una perspectiva dinámica o "en desarrollo", de permanente evolución y mejora.

Qué exige a Kimün.
- No hacer: convertir la calidad en un puntaje cerrado que reemplace el juicio del equipo. La política dice que importa el proceso y que el nivel es contextual. `PLAN.md`: cumple (la IA sugiere con evidencia, no cierra; sin umbrales de cantidad).
- Hacer: la rúbrica como criterio general flexible, cargable por comunidad; las metas por curso editables como criterio específico. `PLAN.md`: cumple.
- Hacer: en el pitch, cuidar no vender "medición de calidad". Lo que Kimün hace es registrar la movilidad de aprendizajes y proponer un nivel por conducta observable; la calidad en el sentido de la política es más amplia (clima, participación, buen trato) y no la mide la app. `PLAN.md`: la Task 10 se llama "medición de calidad" pero se refiere a precisión del modelo (asignación de niños, núcleos, OA, nivel), no a la calidad educativa de la política. Mantener esa distinción clara en el pitch para no sobreprometer.

## 9. La política propiamente tal: declaración y condiciones (cap. 8, pp. 46-47)

Declaración de la Política de Calidad Educativa (p. 46). Integra garantiza, a través de sus establecimientos, el derecho de los niños y niñas a una educación parvularia de calidad que les permita desarrollarse plenamente y ser felices, reconociéndolos como personas únicas, ciudadanos capaces de conocer y transformar el mundo, principalmente a través del juego. Esta educación se basa en una convivencia bientratante que respeta los derechos de niños y adultos, y conforma comunidades educativas inclusivas que participan en su PEI.

Frase central (cita, p. 46): "Esta educación parvularia de calidad tiene como centro el bienestar, el aprendizaje oportuno y pertinente y el protagonismo de los niños y niñas, fortaleciendo los aprendizajes, talentos y habilidades que les permitirán enfrentar el diario vivir, aportando a la construcción de una sociedad inclusiva, solidaria, justa y democrática."

Las cinco condiciones para lograrla (pp. 46-47). "Para lograr la educación de calidad que queremos, es fundamental contar con":
1. Personas y equipos multidisciplinarios comprometidos con su rol de agentes de cambio social.
2. Ambientes educativos y laborales enriquecidos y confortables (humanos y físicos).
3. Una estrecha alianza con las familias, primeras educadoras.
4. Una estrecha alianza con la comunidad y sus redes.
5. Un sistema de gestión en completa sintonía con lo anterior, al servicio de los establecimientos: integrado, eficaz, eficiente, transparente, participativo, inclusivo, sostenible y que rinde cuentas.

Qué exige a Kimün.
- Hacer: anclar el pitch en la frase central (bienestar, aprendizaje oportuno y pertinente, protagonismo). `PLAN.md`: cumple (Task 11).
- Hacer: entender que Kimün es, sobre todo, soporte a la condición 1 (dar tiempo y foco a las personas y equipos) y a la condición 5 (un sistema de gestión transparente). `PLAN.md`: cumple (el problema que resuelve es las ~4 h semanales de las educadoras; paneles agregados para la directora, Task 12).
- No hacer: pretender que la app por sí sola produce "calidad"; las cinco condiciones son humanas y materiales. La app es un instrumento dentro de la condición 5.

## 10. Desplegando los conceptos clave (cap. 8.1, pp. 48-62)

Cada atributo de la declaración se despliega. Resumen fiel y su exigencia a Kimün.

Niño y niña (pp. 48-49). Sujetos de derecho, personas únicas e irrepetibles, en crecimiento, que desarrollan su identidad, descubren sus potencialidades y aprenden a regular frustraciones. Educativamente, implica potenciar su desarrollo individual: autoconocimiento, autoestima y autonomía, con aprendizajes integrales que abarquen todas las dimensiones y consideren el potencial de cada uno. Son ciudadanos activos capaces de incidir en su realidad, portadores de saberes y estilos propios. El juego es doble: fin en sí mismo (goce) y medio de aprendizaje.

Felicidad (cita, p. 48): "la sensación, opinión o percepción positiva que el niño o niña tiene con respecto a sí mismo y al medio en que vive"; es un fin en sí mismo y un medio que lo predispone a alcanzar su máximo potencial.

Convivencia bientratante (pp. 49-50). Relaciones y prácticas basadas en la confianza, el respeto y la inclusión, donde se acogen las particularidades de cada niño y adulto. Requiere espacios de diálogo y mecanismos de resolución pacífica de conflictos. El interés superior del niño es la base de cualquier decisión (p. 50).

Comunidades educativas inclusivas y PEI (pp. 50-52). Se distinguen prácticas educativas (de todos los adultos del establecimiento, basadas en todas las declaraciones institucionales) y prácticas pedagógicas (del equipo de aula, basadas en el Referente Curricular). El PEI es la declaración de sueños, valores, principios y objetivos de cada comunidad; se construye participativamente y es un proceso reflexivo permanente.

Bienestar (centro de la educación parvularia, p. 52). Condición que favorece el desarrollo integral, en un marco de respeto de derechos; estado de armonía y equilibrio. Lo influyen los adultos significativos que median y toman decisiones. Requiere ambientes saludables, protegidos, acogedores y ricos en aprendizaje.

Aprendizaje oportuno y pertinente (p. 52). Los aprendizajes deben construirse en los momentos óptimos ("ventanas de oportunidades"), con estrategias pertinentes a las características de desarrollo, los saberes, intereses y capacidades del niño y sus contextos, con currículum flexible.

Protagonismo (pp. 52-53). El niño aprende mientras está activo: investigando, descubriendo, eligiendo materiales, dónde y con quién jugar, tomando decisiones según sus preferencias, proponiendo acciones. Integra crea condiciones para que desplieguen sus talentos particulares.

Personas y equipos agentes de cambio social (pp. 53-55). Equipos multidisciplinarios con diversos saberes, que valoran su trabajo como aporte social; con capacidad de reflexión crítica permanente; liderazgo apreciativo y distribuido que descubre y destaca las fortalezas de cada uno; con desarrollo de carrera, formación continua y condiciones de bienestar.

Ambientes enriquecidos (pp. 56-59). Humanos (interacciones afectivas positivas, clima amable) y físicos (cómodos, seguros, con equipamiento y materiales suficientes, pertinentes, estéticos). El juego ocupa un lugar central. El rol mediador del adulto es central: tiende puentes entre quien aprende y el medio, sobre la zona de desarrollo próximo. Áreas verdes y espacios públicos (plazas, museos, bibliotecas) también son "aula" (concepto amplio).

Familias (pp. 59). Primeras educadoras, actor central; se reconoce su diversidad; se promueve su participación permanente y se fortalecen las competencias parentales para una crianza amorosa. Incluye "la socialización de los resultados de aprendizaje" con las familias.

Comunidad (pp. 59-61). Redes comunitarias (instituciones, organizaciones, actores) con las que se articula en colaboración y reciprocidad.

Sistema de gestión (pp. 60-62). Integrado (conecta nivel nacional, regional y de jardín), eficaz, eficiente, transparente (rinde cuentas con información clara, precisa y oportuna), participativo, inclusivo, sostenible, orientado a la mejora continua y a la acreditación.

Qué exige a Kimün.
- Hacer: que la IA y la ficha muestren fortalezas y talentos, no solo vacíos. El protagonismo y la apreciación de talentos lo exigen (pp. 52-54). `PLAN.md`: no explícito; la ficha muestra OA sin evidencia "como sugerencia de qué observar" y la cobertura por OA. Tensión real: el diseño actual pone el foco en los vacíos (OA sin evidencia, brechas, alertas) y poco en lo que el niño ya logra. Resolución: en la ficha, presentar primero el nivel actual con la conducta lograda y los OA con evidencia (fortalezas), y después lo que falta como sugerencia. `hallazgos` ya marca "mostrar fortalezas y talentos" como "No" en `PLAN.md`. Recomendación concreta: reordenar la ficha para que lo logrado sea visible antes que lo pendiente, sin cambiar la lógica de cobertura.
- Hacer: respetar el ritmo individual y las ventanas de oportunidad: la referencia de nivel esperado es blanda, no una norma rígida; no asumir avance lineal. `PLAN.md`: cumple ("No se asume que el avance sea lineal", "referencia blanda").
- Hacer: el rol mediador y la zona de desarrollo próximo justifican los "pasos a seguir" y mostrar la conducta del nivel siguiente como referencia de qué observar. `PLAN.md`: cumple (la ficha muestra el nivel siguiente y cargará las orientaciones de Integra; el MVP no genera pasos con IA).
- Hacer: la socialización de resultados con las familias (p. 59) respalda la vista de informes a familias. `PLAN.md`: fuera del MVP, mencionado en el pitch. Correcto.
- Hacer: el sistema de gestión transparente e integrado respalda la vista del jardín para la directora y, a futuro, vistas regionales/nacionales. `PLAN.md`: Task 12 (si alcanza) y pitch. Correcto.
- No hacer: medir "bienestar" o "clima" con la app; esos son atributos de la convivencia y los ambientes, no del registro de aprendizajes. No sobrecargar la herramienta.

## 11. "Lo esencial de la calidad educativa" (gráfica, pp. 64-65)

Revisada como imagen (la p. 64 es una infografía con forma de flor; la p. 65 es un relato creativo). Estructura (confirmada visualmente):
- Centro de la flor (objetivo): "Desarrollo pleno y felicidad" de niños y niñas, rodeado por el anillo "Bienestar, Protagonismo, Aprendizajes Oportunos y Pertinentes, Habilidades para la vida".
- Cuatro pétalos (los elementos/condiciones): Personas y equipos agentes de cambio social; Ambientes educativos y laborales enriquecidos; Estrecha alianza con las familias; Estrecha alianza con la comunidad.
- Suelo (soporte): "Sistema de gestión al servicio de salas cuna, jardines infantiles y otras modalidades".

El relato de la p. 65 ("de una oruga nació una bella mariposa que está buscando una flor muy especial") es una explicación poética de la gráfica para niños y familias; el color principal de la flor "era el color de los niños y niñas plenos y felices".

Qué exige a Kimün.
- Hacer: usar esta gráfica mental como mapa: el objetivo es el niño pleno y feliz; Kimün es una pieza del "suelo" (sistema de gestión) que sostiene a los pétalos (en particular, personas y equipos). El pitch puede apoyarse en esta imagen.

## 12. Componente 1: Bienestar y Protagonismo de niños y niñas (cap. 9.1, pp. 69-80)

Propósito (p. 69): favorecer el bienestar y protagonismo de los niños, en un marco de reconocimiento y respeto de sus derechos, mejorando sus oportunidades de aprendizaje. Bienestar integral (p. 69): estado que se logra con equilibrio entre factores físicos, emocionales, biológicos, sociales y espirituales.

Desarrollo Infantil Temprano, DIT (pp. 70-71). Desarrollo físico, cognitivo, lingüístico y socioemocional desde la gestación hasta la transición a la escuela básica. La primera infancia es el período de cambios más acelerados. Idea clave (cita, p. 71): "el progreso de una dimensión actúa como catalizador para el progreso de otras. Inversamente, el retraso de un área de desarrollo puede gatillar el retraso de otras áreas también." A pesar de los ritmos individuales, hay factores de desarrollo común que permiten diseñar modelos de acompañamiento.

Seis dimensiones del DIT (diagrama p. 71, confirmado como imagen): seguridad y protección; salud y nutrición; afecto y buen trato; educación temprana; juego y recreación; participación y protagonismo infantil (pp. 72). Cada dimensión se describe en p. 72.

Modelo ecológico de Bronfenbrenner (pp. 72-74). El desarrollo es resultado de la interacción entre la persona y los sistemas de su entorno. Sistemas: microsistema (familia, barrio, jardín), mesosistema (interacciones entre microsistemas), exosistema (ámbitos distantes que influyen: trabajo de los padres, redes), macrosistema (marco político, cultural, ideológico), cronosistema (efecto del tiempo y los cambios históricos). El desarrollo siempre se considera en relación al ambiente.

Cinco ejes estratégicos del componente (pp. 75-80):
1. Vida saludable y cuidado del medio ambiente: vida activa (juego y movimiento), salud y hábitos higiénicos, cuidado del medio ambiente.
2. Ambientes educativos físicos seguros: infraestructura, equipamiento, higiene y seguridad.
3. Participación y protagonismo infantil: autonomía progresiva e inclusión de la voz de niños y niñas (buscar estrategias para recoger su opinión y visión; el lenguaje del juego y la expresión artística como base de la comunicación, p. 77). La opinión de los niños debe considerarse en la evaluación de satisfacción del servicio.
4. Protección de derechos (pp. 78-79). Desarrollado abajo, en "Eje 4 en detalle".
5. Convivencia bientratante (pp. 79-80): educación inclusiva que responda a la diversidad y atienda las necesidades educativas especiales y los talentos individuales; buen trato para los equipos.

Eje 4 en detalle: Protección de derechos (pp. 78-79). Paráfrasis por partes, con citas breves.

- Responsabilidad (p. 78). Integra debe promover el derecho a la educación de los niños según la cobertura comprometida: acceso, permanencia, asistencia y progreso. Aunque son titulares de derechos, por su ciclo de vida necesitan "una acción especial y sistemática por parte del mundo adulto" para que esos derechos se cumplan.
- Respuesta a la vulneración (p. 78). El sistema debe tener "mecanismos pertinentes y oportunos para responder a situaciones de vulneración", velando por el interés superior del niño y por su continuidad en el sistema educativo "como factor protector". El énfasis está en generar condiciones favorables para que el niño siga aprendiendo. Para la app, mantener al niño en el jardín es parte de protegerlo, y nada en la respuesta debe excluirlo ni exponerlo.
- Prevención y protección (p. 78). La prevención crea conciencia, en adultos y niños, de los factores de riesgo, y promueve prácticas con relaciones cuidadosas y afectivas con los niños y entre ellos. La protección es el abordaje cuidadoso de cada situación: visibilizar las necesidades del niño para contenerlo, acompañarlo, interrumpir la vulneración o favorecer la restitución oportuna de sus derechos.
- Acceso y permanencia (pp. 78-79). Instrumentos y orientaciones para la matrícula, la permanencia y el progreso, incluidas las transiciones entre niveles y hacia la educación básica, con trato digno, respetuoso y no discriminatorio.
- Prevención como condición (p. 79). Ante factores de riesgo: fortalecer sentidos, clarificar expectativas, delimitar ámbitos de acción y responsabilidades, y coordinarse dentro y fuera de la institución para un "contexto protector vigilante de los derechos infantiles".
- Protección como condición (p. 79). Al gestionar casos se consideran cuatro puntos:
  - (i) actualizar y mejorar los protocolos de gestión de casos de vulneración;
  - (ii) fortalecer la información y la comunicación hacia las familias, con contención ante denuncias o presunción de agresión;
  - (iii) en los equipos, gestionar las crisis para restituir el funcionamiento del jardín;
  - (iv) con los niños "presuntamente vulnerados", profundizar la acogida y el cuidado desde su interés superior y su derecho a la educación.
- Gestión (p. 79). Coordinar asesoría, supervisión y gestión de personas para acortar los tiempos de indagatoria y sanción en las denuncias internas, y seguir "el trabajo en red para la atención especializada y derivación de casos".

Qué se desprende para Kimün:

- Todo está en clave de presunción. La política habla de niños "presuntamente vulnerados" y de "presunción de agresión", y la calificación de un hecho es tarea del protocolo y de los organismos competentes, no de la app.
- El punto (iii) y las denuncias internas reconocen que la vulneración puede ocurrir dentro del jardín, cometida por un adulto del equipo. Un aviso que solo ve quien escribió la nota no basta.
- La política no define maltrato ni sus tipos. Las definiciones operativas (maltrato físico, psicológico, negligencia y agresión sexual; qué no es maltrato; cómo actuar sin revictimizar) están en el anexo "Protección de derechos y vulneraciones" de `enciclopedia-bases-curriculares.md`, tomadas de los protocolos públicos de la JUNJI. Integra tiene su propio protocolo, que no tenemos (pregunta 9 de `PLAN.md`).

Qué exige a Kimün. Varias reglas de alto impacto.
- Hacer (voz del niño): el protagonismo pide incluir la voz, intereses y preferencias del niño (pp. 52-53, 77). `PLAN.md`: descartado por el equipo ("Descartado por el equipo: un registro propio de la voz del niño"). Tensión real con la política. Resolución honesta: es una decisión de alcance del MVP, no una negación del principio. En el pitch, nombrarla como extensión futura coherente con el protagonismo, no como algo fuera de la visión. No fingir que la app cubre el protagonismo del niño por sí sola.
- Hacer (protección de derechos): si una nota podría describir una posible vulneración de derechos (un relato del niño, marcas, negligencia, prácticas de un adulto del equipo), Kimün no la usa como evidencia de aprendizaje ni la muestra en vistas agregadas. Avisa a la educadora del curso y a la directora para que activen el protocolo de Integra, sin calificar el hecho, sin nombrar al presunto responsable y sin preguntar detalles que empujen a interrogar al niño (pp. 78-79). `PLAN.md`: planificado (requisito "Protección de derechos" y Task 13). Las definiciones de qué constituye maltrato están en el anexo de `enciclopedia-bases-curriculares.md`.
- Hacer (DIT, dimensiones cruzadas): como "el retraso de un área de desarrollo puede gatillar el retraso de otras áreas" (p. 71), la ficha debería permitir ver los núcleos juntos para detectar brechas simultáneas. `PLAN.md`: cumple (la ficha muestra todos los núcleos; Task 3).
- Hacer (factores comunes): los factores de desarrollo común justifican una referencia de nivel esperado como contexto, respetando ritmos. `PLAN.md`: cumple (nivel esperado como referencia blanda).
- Hacer (inclusión y NEE): atender necesidades educativas especiales y talentos. `PLAN.md`: no modela NEE explícitamente; aceptable para el MVP, pero no diseñar nada que las invisibilice (los textos de rúbrica y las señales no deben asumir un único camino de desarrollo).
- No hacer: tratar el modelo ecológico como dato de la app. Es marco conceptual; su efecto práctico es recordar que el contexto del niño (familia, comunidad) importa y no todo lo explica el aula.

## 13. Componente 2: Educación Transformadora (cap. 9.2, pp. 83-90)

Propósito (p. 83): ofrecer el marco curricular institucional (del Referente Curricular 2014) para que las comunidades construyan su Proyecto Curricular dentro del PEI.

Tres fundamentos de la concepción de desarrollo y aprendizaje (pp. 83-85):
- Ecológico: las personas se desarrollan en un sistema de relaciones (ver modelo ecológico).
- Socioconstructivista (Vygotski): el aprendizaje es activo; la persona incorpora nuevos conocimientos a sus estructuras previas; las funciones mentales superiores emergen primero en el plano social (interpsicológico) y luego pasan al personal (intrapsicológico). La mediación debe hacerse sobre la zona de desarrollo próximo: una exigencia por sobre esa zona genera ansiedad; por debajo, desmotivación (p. 84).
- Neurocientífico: el ambiente y las experiencias moldean el desarrollo neurológico; los primeros tres años son el período de más intensa formación de conexiones; hay períodos críticos o sensibles ("ventanas de oportunidades").

Trabajo colaborativo del equipo educativo (pp. 85). Roles: la directora como líder de la gestión y movilizadora de aprendizajes; la educadora como formadora, mediadora e investigadora en la acción; agentes educativas, auxiliares de servicio, asistentes de extensión horaria y administrativas, cada uno con su aporte a la convivencia bientratante y al bienestar.

Cuatro ejes estratégicos (pp. 86-90):
1. Ambiente educativo enriquecido y confortable (humano y físico; el juego como elemento central).
2. Organización del tiempo (pp. 86-87). Períodos permanentes (acogida, alimentación, descanso, higiene, actividad) y períodos variables (focalizados en un aprendizaje esperado, dos veces al día). Clave (p. 87): el primer período variable del día aborda, en la quincena, aprendizajes de los núcleos priorizados institucionalmente (dos nacionales: Lenguaje Verbal y Relaciones Lógico-matemáticas; uno a elección del jardín según resultados IEA); el segundo, los no priorizados. La organización debe asegurar una oferta pedagógica integral en la quincena que potencie todos los núcleos. (Vocabulario caduco: los núcleos "Relaciones Lógico-matemáticas", "Seres vivos y su entorno", "Grupos humanos" y la escala Primer/Segundo Ciclo son de 2017, previos a las Bases 2018.)
3. Planificación educativa (pp. 88-89): proceso sistemático que anticipa y organiza el trabajo; a largo plazo (anual) y a corto plazo (diaria); la realiza el equipo con reflexión crítica, liderada por la directora y las educadoras, considerando las voces de los niños y las familias.
4. Evaluación educativa (pp. 89-90): ver sección 5 de esta guía (instrumentos EEDP, IEA, SFPP, PLAEP-R y el principio de evaluación por observación).

Qué exige a Kimün. Este componente es el que más directamente justifica la herramienta.
- Hacer (oferta integral por quincena): la política pide cubrir todos los núcleos en cada quincena (p. 87). `PLAN.md`: cumple fuerte. La vista del grupo por quincena (`cobertura.py`, Task 2) muestra, por núcleo, las observaciones del curso y destaca los núcleos sin observaciones "porque la Política de Calidad de Integra pide una oferta que cubra todos los núcleos en cada quincena". Alineación directa con el eje de organización del tiempo.
- Hacer (zona de desarrollo próximo): mostrar la conducta del nivel siguiente y, cuando lleguen, las orientaciones de Integra, apunta justo a la ZDP: qué puede lograr el niño con apoyo. `PLAN.md`: cumple (ficha, Task 3; propuesta de nivel considera la progresión "de con ayuda a autónomo", Task 7).
- Hacer (ventanas de oportunidad / aprendizaje oportuno): el aviso de datos desactualizados (14 días sin observaciones) y la cobertura por OA ayudan a que ningún núcleo quede sin oferta en el momento oportuno. `PLAN.md`: cumple.
- Hacer (reflexión pedagógica): la planificación y la evaluación son actos reflexivos del equipo. Mensaje del Referente 2025 recogido en `PLAN.md`: Kimün elimina transcribir y ordenar, no la reflexión. `PLAN.md`: cumple (pitch, Task 11).
- Hacer (vocabulario vigente): usar los 8 núcleos de las Bases 2018 (IA, CC, CM, LV, LA, EEN, CES, PM), no los de 2017. `PLAN.md`: cumple.
- No hacer: automatizar la planificación o la toma de decisiones pedagógicas. La planificación es del equipo (p. 88). Kimün aporta insumos (cobertura, distribución), no planifica.

## 14. Componente 3: Familias y Comunidades comprometidas con la Educación (cap. 9.3, pp. 93-98)

Propósito (p. 93): potenciar la alianza entre establecimientos, familias y comunidad para favorecer el desarrollo pleno de los niños. La familia es primera educadora y aliada estratégica; la comunidad es el escenario físico, natural y cultural de identidad. Se trabaja según las Bases Curriculares (p. 93). Derecho de participación (p. 94): de beneficiarias pasivas a partícipes activas; la participación es garantía de todas las familias, no privilegio.

Cinco ejes estratégicos (pp. 95-98):
1. Desarrollo de roles parentales: estrategias conjuntas familia-equipo; incluye "la socialización de los resultados de aprendizaje" con las familias (p. 96); promoción del buen trato y patrones de crianza positivos; habilidades para la vida.
2. Participación en el PEI: niveles de participación informativa, colaborativa, consultiva, deliberativa y de control (p. 97); mesa PEI; centros de padres.
3. Promoción de competencias de los equipos para el trabajo con familias.
4. Gestión integral del conocimiento: perfil de las familias; comunicación corporativa; soportes (libreta de comunicaciones, reuniones, boletines, diario mural).
5. Articulación con redes comunitarias: trabajo en red; y apoyo a los procesos de transición educativa, donde es relevante "el registro y valoración, entre familias y establecimientos, de su experiencia educativa en los distintos niveles de Integra" (p. 98).

Qué exige a Kimün.
- Hacer (socializar resultados): la política pide socializar los resultados de aprendizaje con las familias (pp. 59, 96). `PLAN.md`: informes a familias están fuera del MVP, en el pitch. Correcto como alcance, pero es una extensión alineada con la política; nombrarla así.
- Hacer (transiciones y portabilidad del registro): el historial de niveles validados con su evidencia cumple el rol de registrar y valorar la experiencia educativa del niño en los distintos niveles (p. 98), útil en las transiciones. `PLAN.md`: cumple en estructura (historial de `NivelValidado`); el uso en transiciones es futuro.
- No hacer: exponer datos del niño a las familias sin validación de la educadora. Si se construyen informes a familias, deben ir validados por la educadora (es coherente con "nada se aplica solo"). `hallazgos`: lo marca así.

## 15. Componente 4: Personas y Equipos que trabajan por la Educación (cap. 9.4, pp. 101-111)

Propósito (p. 101): desarrollo y bienestar de todos los trabajadores, orientado a la mejora continua, en una cultura de derechos. Cuatro fundamentos transversales (p. 101): personas y equipos que trabajan por la educación; perspectiva de género (Integra es 97% mujeres, p. 102; busca igualdad y corresponsabilidad); liderazgo para la calidad educativa; sembrando inclusión (equipos diversos, sin discriminación por condición social, origen, nacionalidad, género, etnia, orientación sexual, religión o discapacidad, p. 104).

Seis ejes estratégicos (pp. 106-111):
1. Desarrollo de carrera con énfasis en la formación continua (AprendeS); promoción y traslado; reconocimiento; retroalimentación.
2. Ambientes laborales bientratantes (promoción, prevención y recuperación).
3. Liderazgo (distribuido, apreciativo y pedagógico).
4. Incorporación de personas para la calidad educativa (atracción, selección e incorporación inclusiva).
5. Calidad de vida laboral (p. 110): compromiso institucional por el bienestar personal y familiar de los trabajadores; servicios de gestión administrativa; sistema de compensaciones; plan de salida asistida.
6. Relaciones laborales (participación, comunicación, relación con organizaciones sindicales).

Idea clave para el proyecto (p. 80): "Equipos bien tratados están en mejores condiciones de cuidar", favoreciendo la entrega de una educación de calidad.

Qué exige a Kimün. Este componente respalda el KPI central del desafío.
- Hacer: el objetivo de reducir las ~4 h semanales de escritorio de las educadoras es, en términos de la política, un aporte a la calidad de vida laboral y al bienestar de los equipos (pp. 55, 80, 110). `PLAN.md`: cumple (es el problema que resuelve). Fuerte argumento para el pitch (impacto social).
- Hacer: distinguir roles (educadora, asistente, directora) y permisos, coherente con el liderazgo distribuido y los roles del equipo (p. 85). `PLAN.md`: cumple (permisos por rol; `permisos.py`).
- Hacer: respetar el tiempo de la educadora. Tensión real: añadir una pantalla de revisión y validación agrega trabajo. Resolución: la revisión debe ser rápida (segundos desde el teléfono, "aceptar todas" por captura) para que el saldo neto sea menos trabajo, no más. `PLAN.md`: cumple en intención (Task 6: "revisa lo pendiente en segundos"). Auditar que la carga de revisión no supere el ahorro de transcripción.
- No hacer: la app no gestiona personas ni calidad de vida laboral; su contribución es indirecta (dar tiempo). No sobreextender.

## 16. Glosario

Términos de la política (con su página). Marca entre paréntesis si el vocabulario está vigente o es de 2017.

- Enfoque de derechos: paradigma que concibe la educación como derecho exigible y al niño como sujeto de derechos, no beneficiario pasivo (pp. 39-41). Vigente.
- Interés superior del niño: criterio según el cual toda medida sobre el niño debe basarse en lo que mejor favorezca su integridad y bienestar (pp. 40, 50). Vigente.
- Convivencia bientratante: relaciones basadas en confianza, respeto e inclusión, con resolución pacífica de conflictos (p. 49). Vigente.
- Buen trato: forma de relación respetuosa y afectiva, base del proyecto educativo, aplicada también a los equipos (pp. 79-80). Vigente.
- Calidad educativa: conjunto de cualidades centrales de la educación; relativa, contextual, consensuada, normativa y en desarrollo (p. 45). Vigente.
- Criterios generales / específicos: los generales operan en cualquier experiencia (flexibles); los específicos son propios de cada comunidad (p. 45). Vigente.
- Desarrollo Infantil Temprano (DIT): desarrollo físico, cognitivo, lingüístico y socioemocional de la gestación a la escuela básica, multifuncional y sistémico (pp. 70-71). Vigente.
- Dimensiones del DIT: seguridad y protección; salud y nutrición; afecto y buen trato; educación temprana; juego y recreación; participación y protagonismo infantil (pp. 71-72). Vigente.
- Modelo ecológico (Bronfenbrenner): micro, meso, exo, macro y cronosistema (pp. 72-74). Vigente.
- Mediación / zona de desarrollo próximo: interacción en que un adulto más aventajado tiende puentes para que el niño avance; debe hacerse sobre la zona donde el niño puede progresar con apoyo (pp. 57, 84). Vigente.
- Bienestar: estado de armonía y equilibrio entre factores físicos, emocionales, biológicos, sociales y espirituales; condición del desarrollo (pp. 52, 69). Vigente.
- Aprendizaje oportuno y pertinente: construido en las ventanas de oportunidad, pertinente al contexto y a las características del niño (p. 52). Vigente.
- Protagonismo: el niño activo, que elige, decide, propone y es escuchado (pp. 52-53, 77). Vigente.
- PEI (Proyecto Educativo Institucional): declaración participativa de sueños, valores, principios y objetivos de cada comunidad educativa (pp. 50-52). Vigente.
- Prácticas educativas / pedagógicas: las educativas, de todos los adultos del establecimiento; las pedagógicas, del equipo de aula (p. 51). Vigente.
- IEA "Evaluar para aprender": instrumento que evalúa los niveles de logro y movilidad de los aprendizajes (pp. 32, 90). Nombre institucional; su relación con la rúbrica de niveles de 8 (hoy) está por confirmar.
- EEDP: Escala de Evaluación del Desarrollo Psicomotor, 0 a 2 años (p. 90). Vigente como instrumento psicomotor.
- PLAEP-R: Perfil de Logro de Aprendizajes en la Educación Parvularia, estandarizado, aplicado a una muestra (pp. 32, 90). Vigente.
- SFPP: Sistema de Fortalecimiento de las Prácticas Pedagógicas; observa y retroalimenta prácticas, no evalúa a los niños (pp. 33, 90). Vigente.
- Aprendizajes esperados: término curricular de 2017 (p. 87). Caduco. Las Bases 2018 usan "Objetivos de Aprendizaje" (OA).
- Núcleos de 2017 (Relaciones Lógico-matemáticas, Seres vivos y su entorno, Grupos humanos, Autonomía, Identidad, Convivencia, Lenguajes artísticos) y Primer/Segundo Ciclo (p. 87). Caducos. Usar los 8 núcleos de las Bases 2018.
- Modalidades no convencionales (MNC): alternativas de atención (Jardín sobre Ruedas, salas cuna en recinto penitenciario, etc., pp. 27, 29). Vigente como concepto institucional; fuera del alcance de Kimün.
- Liderazgo apreciativo / distribuido: liderazgo que descubre y destaca las fortalezas de cada persona y se comparte en el equipo (pp. 54, 109). Vigente.

## 17. Bibliografía relevante (pp. 114-115)

Referencias del documento útiles para contextualizar (selección):
- Mineduc (2001). Bases Curriculares de la Educación Parvularia. (Nota: las vigentes para la app son las de 2018, posteriores a esta política.)
- Fundación Integra (2014b). Referente Curricular de Integra. Base de los componentes de Educación Transformadora y de las definiciones del niño y la mediación.
- Fundación Integra (2013a). Concepto de Calidad Educativa. Fuente del capítulo 8.
- Fundación Integra (2013b). Política de Bienestar y Protagonismo Infantil. Fuente del componente 1.
- Fundación Integra (2011b). Política de Participación de Familias y Comunidad. Fuente del componente 3.
- Bronfenbrenner, U. (1987). La Ecología del Desarrollo Humano. Base del modelo ecológico.
- Vygotski, L. S. (1985). Pensamiento y Lenguaje. Base del fundamento socioconstructivista y la zona de desarrollo próximo.
- Peralta, V. (varios, 2007-2012). Calidad en educación infantil desde la post-modernidad; el "bien-estar" como fin.
- ONU (1948) Declaración Universal de Derechos Humanos; (2005) Convención sobre los Derechos del Niño, Observación General N°7. Base del enfoque de derechos.
- Blanco, R. (2012); Reveco, O. (2012); Tokman, A. (2010). Calidad e impacto de la educación parvularia.

Para la implementación, el currículo y las conductas observables salen de las Bases Curriculares 2018 y del Programa Pedagógico de Transición 2019 (ver `hallazgos-bases-curriculares.md` y `hallazgos-programa-pedagogico-transicion.md`), no de esta política, cuyo vocabulario curricular es de 2017.

## 18. Tabla resumen de tensiones con el diseño actual

| Tensión | Qué dice la política | Qué hace / planea Kimün | Estado en PLAN.md | Cómo resolverla |
|---|---|---|---|---|
| Palabra "rezagado" | No etiquetar ni excluir; sin juicios perentorios (pp. 42, 48) | Integra pide avisar de "rezagados"; la UI redacta señales como sugerencia de revisión | Parcial (Task 2 redacta como sugerencia) | Usar "rezago" solo en lenguaje interno/pitch; en la UI, describir la situación sin adjetivar al niño. Auditar cada cadena de texto. |
| Alertas automáticas | Interés superior del niño; sin juicios perentorios (pp. 48, 50) | Alertas por mediana y nivel esperado, redactadas como sugerencias | Cumple en intención (Task 2) | Mantener redacción de sugerencia; nunca "diagnóstico". La educadora decide. |
| Comparación con pares | Calidad contextual, respeto a ritmos individuales (pp. 45, 71) | Brecha con la mediana del curso | Cumple (umbrales propios, provisorios) | Enmarcar como señal de revisión del grupo, no juicio del niño. No usar norma estandarizada externa. |
| Foco en vacíos, no en fortalezas | Protagonismo, apreciación de talentos (pp. 52-54) | Ficha destaca OA sin evidencia y brechas | No (hallazgos lo marca así) | Reordenar la ficha: primero lo logrado (nivel actual, OA con evidencia), después lo pendiente como sugerencia. |
| Tiempo de la educadora | Calidad de vida laboral, bienestar de equipos (pp. 55, 80, 110) | Revisión y validación agregan pasos | Cumple en intención (Task 6, "en segundos") | Mantener revisión rápida ("aceptar todas"); el saldo neto debe ser menos trabajo. |
| Privacidad del niño | Interés superior del niño (pp. 40, 50) | Seudónimos a Bedrock al proponer nivel; fotos/audios borrados tras extraer texto; S3 privado | Cumple fuerte | Mantener; no mostrar fotos ni audios; solo texto en la base. |
| Voz del niño | Protagonismo e inclusión de su voz (pp. 52-53, 77) | Registro de la voz del niño descartado | Descartado por el equipo | Decisión de alcance; nombrarla como extensión futura coherente con el protagonismo, no negarla. |
| Protección de derechos | Prevenir, proteger y derivar vulneraciones (pp. 78-79) | Marca posibles vulneraciones, las excluye de la evaluación y avisa a la educadora y a la directora | Planificado (Task 13) | Implementar la Task 13. Confirmar con Integra su protocolo y quién recibe el aviso (pregunta 9). |
| Oferta integral por quincena | Cubrir todos los núcleos en la quincena (p. 87) | Vista de grupo por quincena, núcleos sin observaciones destacados | Cumple fuerte | Mantener. |
| Complementar, no reemplazar | EEDP/IEA/PLAEP-R; evaluación por observación (p. 90) | Registra la movilidad del IEA | Parcial | Decir explícitamente en el pitch: complementa, no reemplaza, y no es tamizaje clínico. |
| Reflexión pedagógica | Planificación y evaluación son actos reflexivos del equipo (pp. 88-89) | Elimina transcribir y ordenar, no la reflexión | Cumple (pitch) | Mantener el mensaje; la IA no planifica ni decide. |

Donde `PLAN.md` ya cumple, mantener. Donde está "parcial" o "no", las dos salvaguardas con mayor peso ético son: (1) la protección de derechos (no tratar posibles vulneraciones como dato de aprendizaje) y (2) mostrar fortalezas antes que vacíos. Ninguna exige rehacer la arquitectura; son ajustes de redacción, de orden de la ficha y de reglas sobre qué se procesa y qué se deriva.
