# Enciclopedia: Bases Curriculares de la Educación Parvularia (MINEDUC, reimpresión 2018)

Referencia exhaustiva de la malla curricular oficial de la educación parvularia chilena, para agentes de IA del proyecto Kimün. Toda la información sale del PDF `bases-curriculares-educacion-parvularia-2018.pdf` (136 páginas, Subsecretaría de Educación Parvularia, MINEDUC, ISBN 978-956-292-706-2, reimpresión diciembre 2018). Fuente pública: <https://www.curriculumnacional.cl/614/articles-69957_bases.pdf> (el PDF no se versiona; se descarga desde ahí). Resumen para el equipo en `resumen-bases-curriculares.md`; implicancias ya cruzadas con `PLAN.md` en `hallazgos-bases-curriculares.md`.

El documento es público y hecho para difundirse, así que aquí se transcriben fragmentos literales entre comillas o en bloque citado (>), con su página. Donde se parafrasea, es para orientar al agente, no para reemplazar el texto oficial.

## Cómo usar este documento

Para agentes que escriben prompts, deciden qué OA toca una observación, redactan alertas o diseñan vistas.

- Convención de páginas. Se cita siempre la página impresa (p. 40), que es la que aparece al pie de cada página del PDF. La página del PDF = página impresa + 2.
- Objetivos de Aprendizaje (OA). Cada OA tiene dos formas de referencia:
  - Identificador estable de Kimün: `SIGLA-NIVEL-N`, por ejemplo `IA-T-5` (Identidad y Autonomía, Transición, OA 5). Niveles: `SC` = Sala Cuna (1er nivel), `M` = Medio (2° nivel), `T` = Transición (3er nivel).
  - Forma de cita del Programa y del propio documento: `OA 5 IA` (número + sigla). El PDF cita así: "OA 1 LV", "OA 5 IA".
- Siglas de los 8 núcleos: IA, CC, CM (ámbito Desarrollo Personal y Social); LV, LA (Comunicación Integral); EEN, CES, PM (Interacción y Comprensión del Entorno).
- Total de OA: 206 (50 Sala Cuna, 71 Medio, 85 Transición). Verificado con script contra el texto extraído del PDF: los 206 aparecen literales y el conteo por núcleo y nivel coincide con el de `hallazgos-bases-curriculares.md` (ver sección Verificación al final).
- El proyecto hoy solo carga los 85 OA de Transición (`datos/curriculo_transicion.json`). Los OA de Sala Cuna y Medio de este documento son la fuente oficial si el alcance se amplía.

### Índice

- [Introducción general](#introducción-general)
  - [Requerimientos](#requerimientos)
  - [Fuentes](#fuentes)
  - [Principales innovaciones](#principales-innovaciones)
  - [Objetivos Generales de la Educación Parvularia (LGE)](#objetivos-generales-de-la-educación-parvularia-ley-general-de-educación-n-20370)
  - [Contenido del documento](#contenido-del-documento)
- [Capítulo 1 — Fundamentos](#capítulo-1--fundamentos-de-la-educación-parvularia)
  - [Orientaciones valóricas](#orientaciones-valóricas)
  - [Enfoque de derechos](#enfoque-de-derechos-eje-del-concepto-de-niño-y-niña)
  - [Inclusión](#inclusión)
  - [Labor educativa conjunta (familia, institución, comunidad)](#labor-educativa-conjunta)
  - [El enfoque pedagógico (la pedagogía, la educadora, principios)](#el-enfoque-pedagógico-de-la-educación-parvularia)
  - [Principios pedagógicos (los 8)](#principios-pedagógicos)
  - [Fin y propósitos](#fin-y-propósitos-de-la-educación-parvularia)
- [Capítulo 2 — Organización curricular](#capítulo-2--organización-curricular)
  - [Definiciones de los componentes estructurales](#definiciones-fundamentales-de-los-componentes-estructurales)
  - [Niveles curriculares (tramos de 2 años)](#niveles-curriculares)
  - [Tabla resumen de los componentes estructurales](#tabla-resumen-de-los-componentes-estructurales-p-44)
  - [Ámbito Desarrollo Personal y Social](#ámbito-desarrollo-personal-y-social)
    - [Núcleo Identidad y Autonomía (IA)](#núcleo-identidad-y-autonomía-ia)
    - [Núcleo Convivencia y Ciudadanía (CC)](#núcleo-convivencia-y-ciudadanía-cc)
    - [Núcleo Corporalidad y Movimiento (CM)](#núcleo-corporalidad-y-movimiento-cm)
  - [Ámbito Comunicación Integral](#ámbito-comunicación-integral)
    - [Núcleo Lenguaje Verbal (LV)](#núcleo-lenguaje-verbal-lv)
    - [Núcleo Lenguajes Artísticos (LA)](#núcleo-lenguajes-artísticos-la)
  - [Ámbito Interacción y Comprensión del Entorno](#ámbito-interacción-y-comprensión-del-entorno)
    - [Núcleo Exploración del Entorno Natural (EEN)](#núcleo-exploración-del-entorno-natural-een)
    - [Núcleo Comprensión del Entorno Sociocultural (CES)](#núcleo-comprensión-del-entorno-sociocultural-ces)
    - [Núcleo Pensamiento Matemático (PM)](#núcleo-pensamiento-matemático-pm)
- [Capítulo 3 — Contextos para el aprendizaje](#capítulo-3--contextos-para-el-aprendizaje)
  - [Planificación](#contexto-planificación-y-evaluación-para-el-aprendizaje)
  - [Evaluación (clave para Kimün)](#consideraciones-para-la-evaluación)
  - [Ambientes de aprendizaje](#contexto-ambientes-de-aprendizaje)
  - [Familia y comunidad educativa](#contexto-familia-y-comunidad-educativa)
- [Glosario de términos del documento](#glosario-de-términos-del-documento)
- [Referencias normativas citadas](#referencias-normativas-citadas-leyes-decretos-y-convenios)
- [Anexo: protección de derechos y vulneraciones](#anexo-protección-de-derechos-y-vulneraciones) (fuera de las Bases: qué constituye maltrato y qué hacer)
- [Consideraciones para Kimün](#consideraciones-para-kimün)
- [Verificación de los 206 OA](#verificación-de-los-206-oa)

---

## Introducción general

> El Ministerio de Educación, haciendo uso de las facultades que le otorga la Ley General de Educación [n. 1], ha elaborado una nueva versión de Bases Curriculares de la Educación Parvularia. Este es el referente que define principalmente qué y para qué deben aprender los párvulos desde los primeros meses de vida hasta el ingreso a la Educación Básica, según requerimientos formativos que emanan de las características de la infancia temprana, contextualizada en nuestra sociedad del presente. Así, ellas toman en cuenta las condiciones y requerimientos sociales y culturales que enmarcan y dan sentido al quehacer educativo en esta etapa. Son premisas indiscutibles de su contenido, el reconocimiento de niñas y niños como sujetos de derecho, junto al derecho de la familia de ser la primera educadora de sus hijos e hijas. (p. 9)

> Las Bases Curriculares de la Educación Parvularia (BCEP) presentes, corresponden a una modificación y actualización de las que fueron elaboradas el año 2001. Incorporan, por una parte, la actualización permanente de los avances en el conocimiento sobre el aprendizaje y el desarrollo en esta etapa de la vida y los aportes en el campo de la pedagogía del nivel de Educación Parvularia [n. 2], y por otra, los desafíos y las oportunidades que generan el fortalecimiento de las instituciones y del entorno normativo relacionado con la primera infancia. (p. 9)

> La formulación de esta nueva versión conserva parte de las definiciones, conceptos curriculares y principios estructurales que orientaron el primer currículum nacional para el nivel de Educación Parvularia, y destaca elementos que responden a nuevos requerimientos y énfasis de formación para la primera infancia, tales como la inclusión social, la diversidad, la interculturalidad, el enfoque de género, la formación ciudadana, el desarrollo sostenible, entre otros. (p. 9)

> De acuerdo a lo anterior, estas BCEP han sido enriquecidas con el aporte de nuevos conocimientos derivados de la investigación y de buenas prácticas pedagógicas, tanto del país como internacionales. Sus definiciones curriculares fundamentales se centran en los Objetivos de Aprendizaje, elaborados en función de los objetivos formativos generales que para esta primera etapa educativa determina la Ley General de Educación (LGE). Estas definiciones establecen una base curricular común a nivel nacional, que admite diversas modalidades de implementación y programas de enseñanza, de acuerdo a las necesidades institucionales y a las características de sus proyectos educativos. (p. 9)

Nota: la base curricular común que admite diversas modalidades de implementación es lo que permite que Integra tenga su propio referente mientras cubre los mismos OA.

> [n. 1] Ley General de Educación Nº 20.370 / 2009. Chile. (p. 9)

> [n. 2] Existe amplio consenso científico, por lo menos desde hace medio siglo, reafirmado más recientemente por las ciencias cognitivas y las neurociencias, en que los primeros años de vida constituyen un período crucial en el desarrollo futuro de las personas. El creciente posicionamiento de la infancia temprana en las políticas públicas y las agendas gubernamentales, ha traído una renovación y ampliación de ese consenso, y nuevas evidencias, las que se refieren a cómo el ambiente influye en las potencialidades del niño y la niña y, a cómo el bienestar en esta etapa temprana genera beneficios a largo plazo para las economías y las sociedades. (p. 9)

> Estas Bases Curriculares ofrecen a los y las educadoras en general, un conjunto de fundamentos, Objetivos de Aprendizaje y orientaciones para el trabajo pedagógico con los párvulos. De este modo, han sido concebidos como un referente para la organización integral de una trayectoria formativa de calidad, respetuosa de las características, intereses, fortalezas y necesidades de las niñas y los niños, de modo que potencien el desarrollo y el aprendizaje en esta etapa decisiva. (p. 10)

### Requerimientos

> Las BCEP que se presentan a continuación, han sido actualizadas por el MINEDUC, respondiendo a los siguientes requerimientos:
>
> Las necesidades de actualización, reorientación y enriquecimiento de los objetivos y contextos de aprendizaje que se ofrecen a niñas y niños. Estos se derivan de cambios importantes que se han dado en la sociedad y en la cultura, que a su vez implican nuevas oportunidades y necesidades formativas. El desarrollo social, político y económico del país demanda, cada vez más, que el nivel de Educación Parvularia promueva, a partir del nacimiento y de manera inclusiva, una educación de calidad, oportuna y pertinente, cuyo currículum responda a la necesidad de propiciar una formación integral y favorecer aprendizajes relevantes y significativos.
>
> La necesidad de armonizar los sentidos y oportunidades de aprendizaje que ofrece la Educación Parvularia con la reforma educacional implementada en el sistema educativo en su conjunto; específicamente en lo que supone comprender a la educación como un derecho social.
>
> La necesidad de resguardar la trayectoria formativa de las niñas y los niños, reconociendo que la base y solidez de su desarrollo y aprendizaje integral se construye en los primeros años de vida.
>
> La necesidad de actualizar los instrumentos curriculares de acuerdo a la Ley N° 20.370 General de Educación (LGE), que establece una nueva definición de objetivos generales para todos los niveles educativos; por primera vez para la Educación Parvularia. De acuerdo a la LGE, las Bases Curriculares deben definir objetivos de aprendizaje (OA) coherentes y que conduzcan al logro de los objetivos generales establecidos en ella. (p. 10)

### Fuentes

> Esta actualización de las BCEP se nutre de un conjunto de fuentes de múltiples ámbitos que abarcan desde lo normativo, lo sociocultural, los aportes teóricos y hallazgos de diferentes disciplinas y ciencias de la educación. A modo de síntesis se destacan los siguientes:
>
> A. Definición de nuevos marcos normativos relevantes para la Educación Parvularia, como: La Ley Nº 20.370 General de Educación; la Ley N°20.379 que Crea el Sistema Intersectorial de Protección Social e Institucionaliza el Subsistema de Protección Integral a la Infancia "Chile Crece Contigo"; la Ley N° 20.529 que crea el Sistema Nacional de Aseguramiento de la Calidad de la Educación; la Ley Nº 20.835 que crea la Subsecretaría de Educación Parvularia; la Ley N°20.845 llamada de Inclusión Escolar; la Ley N° 20.911 que Crea el Plan de Formación Ciudadana para los Establecimientos Educacionales reconocidos por el Estado; entre otros. Los principios y compromisos de la Política Nacional de Niñez y Adolescencia, sustentada en los tratados y convenciones internacionales de derechos humanos que Chile ha ratificado, donde se establece un Sistema Integral de Garantías de Derechos de Niños, Niñas y Adolescentes (2015 – 2025).
>
> B. Aportes derivados de diversos ámbitos que comprenden cambios socioculturales, hallazgos y avances teóricos de distintas disciplinas y ciencias, especialmente de las neurociencias y de las ciencias de la educación: Dentro de los cambios socioculturales, resulta necesario destacar aquellos vinculados a fenómenos sociales contemporáneos que están afectando a nuestra sociedad desde la primera infancia. Es así como la evidencia señala que el sedentarismo, la falta de movimiento y la alimentación poco saludable, son considerados factores de riesgo para la salud y el bienestar, lo que demanda favorecer aprendizajes y orientaciones para la adopción de prácticas saludables permanentes [n. 3]. Del mismo modo, frente a problemáticas asociadas a fenómenos socioecológicos que afectan la sostenibilidad ambiental, resulta fundamental incorporar desde los primeros años, acciones educativas cotidianas para abordar estos desafíos que enfrenta la sociedad. (p. 11)

> C. Investigaciones y requerimientos que provienen del campo de las neurociencias aplicadas a la educación: Los hallazgos evidencian que lo que sucede en etapas tempranas del desarrollo influye en la estructura cerebral, afectando la diferenciación y función neuronal, lo que implica un gran desafío y responsabilidad para la práctica pedagógica. La plasticidad cerebral ofrece la posibilidad de aprender y desaprender en forma permanente, reorganizándose y formando nuevas conexiones acorde a las experiencias que va vivenciando cada niño y niña, las que a su vez potencian aprendizajes cada vez más complejos. Esta etapa es considerada como el período más significativo en la formación del individuo, por lo tanto, la calidad de los ambientes es sustancial para el desarrollo de sus capacidades físicas, sociales, emocionales, cognitivas y de lenguaje. Así, los primeros años de vida constituyen las bases formativas del ser humano, las que se desplegarán, consolidarán y perfeccionarán en las siguientes etapas. En consecuencia, si los niños y las niñas no cuentan con entornos protectores y enriquecidos donde las familias y equipos educativos cumplen un rol protagónico, estarán perdiendo oportunidades de desarrollo y aprendizaje. Las neurociencias en diálogo con las ciencias cognitivas y de educación, han aportado evidencia de la influencia de las emociones en los procesos psicológicos, tales como la capacidad de enfocar la atención, resolver problemas y apoyar las relaciones. Asimismo, han mostrado cómo las emociones positivas "abren puertas" dentro del cerebro, y cómo el miedo y el estrés reducen la capacidad analítica. Además, sus hallazgos han validado los enfoques holísticos en educación, que reconocen la estrecha interdependencia del bienestar físico e intelectual, de lo emocional y lo cognitivo, de lo analítico y lo creativo. De ello se desprende la pertinencia de relevar un enfoque de esta naturaleza, en estas Bases y en la práctica formativa que promueve. (p. 12)

> Finalmente, es importante destacar que esta actualización es resultado de un proceso participativo de estudio de documentos curriculares y discusión de diversas temáticas de la Educación Parvularia, coordinado desde la Subsecretaría de Educación Parvularia (SdEP) del Ministerio de Educación, con distintos actores del sector. A saber:
>
> 1. El análisis de los currículos internacionales de Educación Parvularia, temprana o inicial en los cuales se consideraron fundamentos, estructuras curriculares, objetivos y contenidos de aprendizaje, además de otros aspectos relacionados con la calidad de la educación de la primera infancia [n. 4].
> 2. La revisión bibliográfica de producciones curriculares y didácticas de instituciones educativas nacionales públicas y privadas, como las de la Junta Nacional de Jardines Infantiles, Fundación Integra, Sociedad de Instrucción Primaria (SIP), Montessori, y otras.
> 3. El análisis de textos y documentaciones que reflejan los principales debates y avances de la investigación en el ámbito del desarrollo curricular, a nivel nacional e internacional para este nivel educativo [n. 5]. Incluye una serie de documentos académicos elaborados por un panel de expertos locales en Educación Parvularia.
> 4. La revisión de los Mapas de Progreso del Aprendizaje para el tramo de 0 a 6 años, publicados por el Ministerio de Educación el año 2008, constituidos como una herramienta de apoyo al currículum, que proporciona criterios para observar trayectorias de aprendizajes.
> 5. El análisis de los Programas Pedagógicos para los niveles de Transición, publicados por el Ministerio de Educación el año 2009. Estos se constituyen en una herramienta de apoyo al currículum, donde se precisan, especifican y gradúan los aprendizajes esperados para los niveles de transición.
> 6. La revisión detallada de las Bases Curriculares de Educación Básica definidas los años 2012 y 2013, con el propósito de resguardar una trayectoria educativa para las niñas y los niños entre la Educación Parvularia y la Educación Básica.
> 7. Las conclusiones de las jornadas nacionales de Diálogos Temáticos, acerca de una propuesta preliminar de BCEP actualizadas, con actores de la Educación Parvularia [n. 6].
> 8. Las conclusiones de una consulta [n. 7] ampliada, destinada a recoger la opinión de profesionales que se desempeñan en establecimientos que imparten Educación Parvularia en los diferentes niveles educativos.
> 9. La retroalimentación permanente de la Comisión Interinstitucional de Currículum y Evaluación, integrada por las instituciones que proveen Educación Parvularia con financiamiento público (Junta Nacional de Jardines Infantiles y Fundación Integra). (pp. 13–14)

Nota: el punto 9 y la revisión de producciones de Integra (punto 2) confirman que Integra participó en la elaboración y que sus instrumentos son coherentes con estas Bases.

> [n. 6] Estas consultas se enmarcaron en el Plan Nacional de Participación Ciudadana. Durante el periodo 2015-2016, se llevaron a cabo tres jornadas sucesivas de diálogos temáticos regionales, conformándose más de 530 mesas de trabajo y participando en ellas, más de 5.000 personas a lo largo de todo el territorio nacional. Participaron actores diversos relacionados con la Educación Parvularia: educadoras de párvulos; directoras; técnicos/as en Educación Parvularia; equipos técnicos de Junji, Integra y Mineduc; equipos técnicos de instituciones relacionadas; las o los docentes de Educación Básica; académicas de Educación Superior. Ver Martinic (2016). (p. 14)

> [n. 7] Este proceso fue desarrollado a través de una encuesta on-line a fines de 2014, en la que participaron más de 6.000 profesionales de todo el país, ligados a la Educación Parvularia en establecimientos de la Junta Nacional de Jardines Infantiles (JUNJI), Fundación Integra y escuelas municipales y particulares subvencionadas. (p. 14)

### Principales innovaciones

> Respecto a las Bases Curriculares 2001, se describen las principales innovaciones:
>
> Se enriquecen los fundamentos, principios y núcleos de aprendizaje con nuevas perspectivas acerca de la infancia, el aprendizaje, la enseñanza y orientaciones valóricas, enfatizando la inclusión y la diversidad social, y las actitudes ciudadanas desde los primeros años. Del mismo modo, se renuevan las orientaciones para los procesos educativos, integrando las visiones actuales acerca de la planificación y la evaluación, como también los factores que contribuyen a la generación de ambientes de aprendizaje significativos.
>
> Se destacan con especial énfasis en los fundamentos, principios, objetivos y orientaciones, todos aquellos factores y aspectos distintivos de la identidad pedagógica del nivel educativo, como son el enfoque de derechos, la incorporación del juego como eje fundamental para el aprendizaje, el protagonismo de los niños y las niñas en las experiencias de aprendizaje y el resguardo de la formación integral.
>
> Se realizan modificaciones en la estructura curricular, ajustando la forma de ordenar temporalmente el proceso educativo pasando de ciclos de tres años a tramos de dos años, respondiendo con mayor precisión a las necesidades y características del aprendizaje y desarrollo de los párvulos. Por otra parte, los núcleos de aprendizaje del Ámbito Desarrollo Personal y Social, adoptan mayor transversalidad, y relevancia para la planificación. No se altera la cantidad de Núcleos de Aprendizaje considerados fundamentales, pero se reorganizan y actualizan algunas de sus temáticas centrales, constituyéndose así el núcleo de Corporalidad y Movimiento, dimensiones que son sinérgicas y de reconocida relevancia en la niñez temprana, lo mismo que el núcleo Identidad y Autonomía. Además, al núcleo de Convivencia se agrega la dimensión de Ciudadanía.
>
> En cuanto a los aprendizajes prescritos, se modifica la denominación de los aprendizajes esperados por objetivos de aprendizaje, de acuerdo a la Ley General de Educación. En su formulación, se integran criterios de trayectoria educativa, además de actualizar su relevancia y pertinencia. Esto implica trazar un vínculo de mayor articulación entre los niveles de sala cuna, medio, transición y primer año de Educación Básica, facilitando la labor de planificación y evaluación.
>
> Además, se unifican criterios para la redacción y para la comunicabilidad de los objetivos (fundamentales, observables, susceptibles de progresar). En este sentido y con el propósito de clarificar el alcance del aprendizaje a lograr, se incorporan en los casos que corresponda, ejemplos de elementos que facilitan su comprensión. En la nueva propuesta, la cantidad de objetivos de aprendizaje disminuye, aunque aumentan de dos a tres los niveles de prescripción. Esta importante modificación no implica una disminución de las expectativas acerca de lo que se espera que aprendan los párvulos. (p. 15)

### Objetivos Generales de la Educación Parvularia (Ley General de Educación N° 20.370)

Son el referente obligatorio para la elaboración de las Bases. Transcripción literal:

> En el marco de la Ley N° 20.370 General de Educación, se explicitan a continuación, los objetivos generales, estipulados para el nivel de Educación Parvularia, y que sirven de referente obligatorio para la elaboración de estas Bases Curriculares: (p. 16)

> Art. 18. La Educación Parvularia es el nivel educativo que atiende integralmente a niños desde su nacimiento hasta su ingreso a la educación básica, sin constituir antecedente obligatorio para ésta [n. 8]. Su propósito es favorecer de manera sistemática, oportuna y pertinente el desarrollo integral y aprendizajes relevantes y significativos en los párvulos, de acuerdo a las bases curriculares que se determinen en conformidad a esta ley, apoyando a la familia en su rol insustituible de primera educadora.

> Art. 28. Sin que constituya un antecedente obligatorio para la educación básica, la Educación Parvularia fomentará el desarrollo integral de los niños y las niñas y promoverá los aprendizajes, conocimientos, habilidades y actitudes que les permitan:
>
> a) Valerse por sí mismos en el ámbito escolar y familiar, asumiendo conductas de autocuidado y de cuidado de los otros y del entorno.
> b) Apreciar sus capacidades y características personales.
> c) Desarrollar su capacidad motora y valorar el cuidado del propio cuerpo.
> d) Relacionarse con niños y adultos cercanos en forma armoniosa, estableciendo vínculos de confianza, afecto, colaboración y pertenencia.
> e) Desarrollar actitudes de respeto y aceptación de la diversidad social, étnica, cultural, religiosa y física.
> f) Comunicar vivencias, emociones, sentimientos, necesidades e ideas por medio del lenguaje verbal y corporal.
> g) Contar y usar los números para resolver problemas cotidianos simples.
> h) Reconocer que el lenguaje escrito ofrece oportunidades para comunicarse, informarse y recrearse.
> i) Explorar y conocer el medio natural y social, apreciando su riqueza y manteniendo una actitud de respeto y cuidado del entorno.
> j) Desarrollar su curiosidad, creatividad e interés por conocer.
> k) Desarrollar actitudes y hábitos que les faciliten seguir aprendiendo en los siguientes niveles educativos.
> l) Expresarse libre y creativamente a través de diferentes lenguajes artísticos.
> m) En el caso de establecimientos educacionales con alto porcentaje de alumnos indígenas se considerará, además, como objetivo general, que los alumnos y alumnas desarrollen los aprendizajes que les permitan comprender y expresar mensajes simples en lengua indígena reconociendo su historia y conocimientos de origen. (pp. 16–17)

### Contenido del documento

> El primer capítulo explicita el conjunto de fundamentos y principios pedagógicos que sustentan estas Bases Curriculares. Incorpora la finalidad y propósitos de la Educación Parvularia.
>
> El segundo capítulo describe la organización curricular con sus diferentes componentes, contiene las caracterizaciones de los ámbitos de experiencias para el aprendizaje, las definiciones de los núcleos de aprendizaje con sus propósitos generales y los Objetivos de Aprendizaje para los tres niveles educativos.
>
> El tercer capítulo refiere a los contextos para el aprendizaje proponiendo un conjunto de criterios y orientaciones para la implementación de estas Bases Curriculares en relación con la planificación y evaluación, con los ambientes de aprendizaje y, con las familias y comunidades educativas. (p. 17)

---

## Capítulo 1 — Fundamentos de la Educación Parvularia

### Orientaciones valóricas

> Las Bases Curriculares de la Educación Parvularia se enmarcan en principios y valores inspirados en la Constitución Política del Estado, la Ley General de Educación y el ordenamiento jurídico de la nación, así como en la concepción antropológica y ética que orienta la Declaración Universal de los Derechos Humanos y la Convención sobre los Derechos del Niño [n. 9] y los tratados en materia de derechos humanos ratificados por Chile. En cuanto a su concepción de educación, este currículum oficial se acoge a la expresada en la Ley General de Educación (2009, Artículo 2º): (p. 20)

> "el proceso de aprendizaje permanente que abarca las distintas etapas de la vida de las personas y que tiene como finalidad alcanzar su desarrollo espiritual, ético, moral, afectivo, intelectual, artístico y físico, mediante la transmisión y el cultivo de valores, conocimientos y destrezas. Se enmarca en el respeto y valoración de los derechos humanos y de las libertades fundamentales, de la diversidad multicultural y de la paz, y de nuestra identidad nacional, capacitando a las personas para conducir su vida en forma plena, para convivir y participar en forma responsable, tolerante, solidaria, democrática y activa en la comunidad, y para trabajar y contribuir al desarrollo del país". (p. 20)

> Así también, los principios y valores que inspiran este referente curricular se basan en la convicción fundamental de que los seres humanos nacen libres e iguales en dignidad y derechos y que la perfectibilidad inherente a la naturaleza humana se despliega en procesos de autoafirmación personal y de búsqueda permanente de trascendencia. A la libertad que hace de cada individuo, persona y sujeto de derechos, le es intrínseca la capacidad de razonar, discernir, valorar y actuar de forma responsable. (p. 20)

> [n. 9] Chile firmó y suscribió la Convención en enero de 1990, y en agosto de 1990 fue promulgada como ley de la República. (p. 20)

### Enfoque de derechos: eje del concepto de niño y niña

> En esta línea, el niño y la niña se conciben como personas singulares y diversas entre sí, sujetos de derechos, en crecimiento y desarrollo de todas sus potencialidades (biológicas, psicológicas, socioculturales). Ellos y ellas se relacionan interactivamente con su entorno natural y sociocultural y, a partir de esta interacción, van construyendo un conocimiento propio del mundo y de sí mismos, en cambio continuo, el cual merece atención y respeto. Por tanto, su comportamiento no es meramente pasivo o reactivo, sino que lleva la impronta original de su voluntad y pensamiento. (p. 21)

> Siguiendo a la Convención de los Derechos del Niño, estas Bases reconocen los derechos económicos, sociales, culturales y otros del niño y la niña, tales como su derecho a la salud, a la educación, a no ser discriminado, a ser escuchado y que su opinión se tome en cuenta, a la libertad de pensamiento y de asociación, a ser protegido de toda forma de maltrato y de injerencias arbitrarias en sus vidas privadas, a tener acceso a información sobre asuntos que le competen, a participar libremente en la vida cultural y en las artes, a jugar y descansar. (p. 21)

> De acuerdo con este referente, la Educación Parvularia asegura al niño y la niña la protección y el cuidado que sean necesarios para su bienestar e interés superior, como sujetos con derecho a una vida plena, protagonistas de los contextos en los que se desenvuelven. Lo anterior implica, entre otras cosas, superar prácticas centradas en la identificación y satisfacción de las necesidades básicas de la población beneficiaria y reemplazarlas por prácticas basadas en el reconocimiento de que toda persona es titular de unos derechos inherentes. El enfoque ya no es la satisfacción de necesidades, sino la realización de derechos. Al mismo tiempo, se reafirma una visión del niño y la niña, en especial de los más pequeños, como sujetos activos de su educación, superando posturas que les atribuyen un rol pasivo y reactivo. (p. 21)

> En consideración a lo anterior, es constitutivo de estas orientaciones valóricas el reconocimiento del rol y responsabilidad del Estado, como garante de los derechos de los niños y las niñas, sin perjuicio del reconocimiento de la responsabilidad primordial a las madres, padres o tutores, por su crianza y desarrollo. En este sentido, al Estado le corresponde otorgar el acompañamiento y las oportunidades para que las familias puedan cumplir su papel principal en lo que respecta a la crianza, disponer instituciones, instalaciones y servicios para el cuidado de los párvulos [n. 10], y asegurar la provisión de una educación de calidad [n. 11]. (pp. 21–22)

> Por último, la Educación Parvularia, asumiendo a niñas y niños en su calidad de sujetos de derecho, manifiesta un propósito compartido por construir una sociedad justa y solidaria, fundada en relaciones de colaboración y co responsabilización de todos sus actores, por la provisión de oportunidades para el pleno desarrollo y bienestar de cada habitante del país, sin importar su origen y particularidades individuales o colectivas. (p. 22)

### Inclusión

> El concepto y la práctica de la educación inclusiva constituye una orientación valórica central en la Educación Parvularia [n. 12]. De acuerdo con diversos textos de UNESCO (2005, 2009, 2015), y del Ministerio de Educación de Chile (2016), la educación inclusiva es un proceso que comporta la transformación de los jardines infantiles, las escuelas y de otros centros de aprendizaje para atender a todos los niños y las niñas, con especial énfasis en aquellos quienes requieren mayor protección, tales como: pueblos indígenas, migrantes, poblaciones rurales, diversidad sexual y de género, privados de libertad, con discapacidad, con alguna enfermedad y con dificultades de aprendizaje, para brindar oportunidades de aprendizaje a todos los párvulos, jóvenes y adultos. (p. 22)

> Tiene por objetivo acabar con la discriminación arbitraria y toda forma de exclusión social, que es consecuencia de actitudes negativas y de una falta de atención a la diversidad. Esta labor exige que se preste atención al currículum, la índole de la enseñanza y la calidad, entre otras medidas. Significa además que los establecimientos educativos y otros contextos de aprendizaje no solo han de ser eficaces, sino también seguros, saludables y respetuosos de las diferencias. (p. 22)

> El valor de la inclusión se expresa en la apertura, acogida y respuesta a la diversidad de todos los niños y las niñas. La educación garantizada como un derecho social fundamental, debe ser inclusiva, y se encuentra a la base de una sociedad más justa, que valora a todas y a todos por igual. Constituye uno de los fundamentos de las sociedades democráticas y es un valor que permite resguardar el cumplimiento de los fines y propósitos de la educación. (p. 23)

> La inclusión trae aparejada de manera estrecha, la valoración de la diversidad social y cultural en el aula como escenario enriquecido para el aprendizaje, que propicia una implementación situada del currículum. En este sentido, la pedagogía necesita dar respuesta a las particularidades que presenta el aula, contextualizando las actividades de aprendizaje de acuerdo con las diferencias de todo tipo que presenten los párvulos. Esto, sin perder de vista la equidad de los aprendizajes esperados para ellos, por cuanto considerar la diversidad no implica esperar aprendizajes de calidad para unos y no para otros. (p. 23)

Nota: la frase anterior ("considerar la diversidad no implica esperar aprendizajes de calidad para unos y no para otros") es clave para no sobre-interpretar las brechas de nivel.

> Por otra parte, si los niños y las niñas aprenden a convivir junto a otros pares y adultos diversos, se aporta a la valoración de la diferencia y a la cohesión social y por tanto, a la equidad. De este modo, la educación inclusiva favorece directamente los propósitos de la formación ciudadana [n. 13], y por ello, brinda oportunidades para construir presentes y futuros más sostenibles para todos y todas. (p. 23)

> La Educación Parvularia inclusiva, debe entenderse como un proceso construido junto a las familias y con toda la comunidad educativa. Para ello, resulta fundamental promover la reflexión personal y colectiva, reconocer las características de nuestra sociedad, los prejuicios y estereotipos arraigados en nuestra cultura y generar acceso a fuentes de información respetuosas de los derechos humanos, como base para compartir significados sobre la diversidad y su valor, impulsar prácticas inclusivas en forma permanente y por parte de todos los integrantes de la comunidad educativa y generar redes para apoyar iniciativas que la favorezcan. (p. 23)

> [n. 10] La Ley N°20.379 de 2009 de protección integral a la infancia conocida como "Chile Crece Contigo", establece que el Estado garantizará, a los niños de familias que integren el 60% más vulnerable, socioeconómicamente, de la población nacional, el acceso a sala cuna y jardín infantil en jornada parcial, y si los padres, madres o guardadores de estos niños y niñas se encuentran trabajando, estudiando o buscando trabajo, tendrán acceso a sala cuna y jardín infantil en jornada extendida. (p. 22)

> [n. 11] En 2013 se promulgó la Ley N° 20.710, que modifica la Constitución estableciendo el último año de la Educación Parvularia obligatorio y extendiendo el acceso universal y gratuito a partir de los 2 años. (p. 22)

> [n. 12] Un antecedente importante de esta orientación, es la Ley N°20.845 de Inclusión Escolar. Si bien esta ley regula los procesos de admisión escolar para favorecer una distribución socioeconómicamente heterogénea de la matrícula, también establece, en su Artículo 1°, que "el sistema propenderá a eliminar todas las formas de discriminación arbitraria que impidan el aprendizaje y la participación de los y las estudiantes (…)". (p. 22)

### Labor educativa conjunta

La niña y el niño, miembros de una familia y de una sociedad:

> A lo largo de la infancia, niñas y niños aprenden y se desarrollan en el seno de una familia, la que a su vez está inserta en un medio social y cultural. En este proceso, construyen aprendizajes que les permiten vincularse con su entorno, respondiendo a su cultura de pertenencia y forjando, a la vez, su identidad, autoestima y sentido como personas. (p. 24)

> La sociedad chilena ha venido cambiando sostenidamente en el último cuarto de siglo. Consecuentemente con ello, la educación debe responder hoy, en forma dinámica a estos nuevos escenarios y también, preparar a las nuevas generaciones para una participación plena acorde a sus potencialidades y características. Entre otros cambios relevantes, se encuentra, la globalización y el avance de las tecnologías de la información y comunicación, que redefinen radicalmente lo próximo y lo lejano; el cambio climático y sus consecuencias tanto en la naturaleza como en la vida diaria de los seres humanos; la evolución del fenómeno migratorio en el país; la estructura de la familia, más diversa; la actitud hacia las instituciones políticas y las elites económicas, cada vez más crítica; la participación en el consumo, más masiva; la cobertura de la educación superior, en expansión. Estos cambios influyen en las dinámicas familiares y en las expectativas que se construyen respecto de los hijos e hijas. (p. 24)

> La Educación Parvularia no permanece ajena a estas dinámicas, las cuales se expresan de diversas maneras, a través de las inquietudes, opiniones, intereses de descubrimiento e interacción, que tanto los párvulos como sus familias traen a las aulas. En consecuencia, la educación en este nivel es una oportunidad para que los párvulos desarrollen desde temprano las actitudes y habilidades para participar progresivamente en la toma de decisiones sobre asuntos que les afectan; por ejemplo, el autocuidado, el respeto y la valoración de la diversidad social, la resolución pacífica de conflictos, la solidaridad, la ciudadanía y el desarrollo sostenible [n. 14]. (p. 24)

La Familia:

> Considerada en su diversidad, la familia constituye el espacio privilegiado para el desarrollo de niños y niñas, independientemente de su composición y estructura. La familia nuclear, así como la extendida, la monoparental, la que está al cuidado de padres, madres, parientes o tutores, están llamadas a otorgarles protección, afecto, estimulación, cuidado y oportunidades para el aprendizaje y desarrollo integral. (p. 25)

> La familia constituye el núcleo central básico en el cual la niña y el niño encuentran sus significados más personales. En ella, establecen los primeros y más importantes vínculos afectivos; incorporan los valores, pautas y hábitos de su grupo social y cultural; desarrollan sus primeros aprendizajes y realizan sus primeras actuaciones como integrantes activos de la sociedad. (p. 25)

> La Educación Parvularia acoge a un niño o niña arraigado en su familia, y le corresponde compartir con ella la labor educativa, complementándola y ampliando las experiencias de aprendizaje y desarrollo integral que se le ofrecen. Por ello, es fundamental que se establezcan perspectivas y líneas de trabajo en común y se potencie el esfuerzo educativo que unas y otras realizan en favor de las niñas y los niños. (p. 25)

Institución Educativa:

> La Educación Parvularia, desplegada en diversos contextos geográficos, sociales y culturales, permite hacer realidad la educación como un derecho social de las niñas y los niños, donde la familia contribuye desde sus particulares saberes y experiencias al enriquecimiento y desarrollo del proceso educativo. Cuando se desarrolla en establecimientos educacionales (salas cuna, jardines infantiles y escuelas), tiene como función especializada otorgar una educación integral presencial lo que requiere de condiciones previamente establecidas y normadas de infraestructura, equipamiento y equipos profesionales responsables del cumplimiento de tareas distintivas. (p. 25)

> Algunas características que definen a los establecimientos de Educación Parvularia son: la intención de responder pertinentemente a las necesidades y características del aprendizaje y desarrollo integral de los párvulos desde su nacimiento hasta su ingreso a la Educación Básica, como un imperativo actual y no sólo como preparación para los aprendizajes futuros. También, la voluntad de considerar la diversidad de niñas y de niños como seres únicos e igualmente valiosos [n. 15]. Asimismo, la integralidad de la formación que brindan, orientada a diversas dimensiones de la persona del párvulo –su corporalidad, sus emociones, sus valores, sus facultades cognitivas- mediante dispositivos pedagógicos también integrales, que se organizan a través del juego, el buen trato, las interacciones potenciadoras y los ambientes enriquecidos. (pp. 25–26)

> Otra característica de estos establecimientos consiste en el tipo de aproximación pedagógica predominante en ellos, según su diferenciación en tres niveles educativos, asociados a las edades y desarrollo de los párvulos que atienden. En la sala cuna, por ejemplo, la atención individual de los párvulos pequeños asume un cariz preponderante, en el vínculo y la interacción con los adultos del equipo pedagógico; gran parte de la actividad lúdica está orientada a promover los aprendizajes relacionados con la adquisición del lenguaje, del desplazamiento y los hábitos que le permitirán crecientes niveles de autonomía. En los jardines infantiles, la actividad rectora es el juego, en cuyo marco se reestructura la interacción para permitir al párvulo el desarrollo de creatividad, habilidades sociales y normas, así como un conocimiento más amplio de su entorno. En los niveles de transición, el juego educativo continúa siendo la aproximación pedagógica predominante, pero inserta en una cultura escolar con la cual debe dialogar. (p. 26)

> En relación a lo anterior, la Educación Parvularia enfrenta el desafío de resguardar su identidad pedagógica cuando se encuentra tensionada por la organización escolar. Al mismo tiempo, requiere articularse adecuadamente con esta para que los párvulos hagan la transición esperada, en los términos que definen estas Bases Curriculares. Dicha articulación, que forma parte de los desafíos actuales de la trayectoria educativa, debe insistir en el valor pedagógico de los principios de la Educación Parvularia, extendiéndolos para el primer y segundo año de la Educación Básica. (p. 26)

La comunidad educativa [n. 16] en la Educación Parvularia:

> La Educación Parvularia de calidad es fruto del esfuerzo común entre todas las personas que directa o indirectamente se encuentran comprometidas en la educación de las niñas y los niños: las familias, los equipos pedagógicos y directivos, entre otros. A todos ellos les asiste la responsabilidad de contribuir al proceso de aprendizaje y desarrollo integral de los párvulos. Esto por cuanto la participación y la colaboración solidaria constituyen piezas claves, en la formación de ciudadanos responsables y comprometidos con la infancia y su educación. (p. 27)

> A través de sus acciones y el compromiso que demuestran por la educación de los párvulos, aportan fundamentos culturales y valóricos a las experiencias de aprendizaje que se proponen a niñas y niños. Los saberes, historias, tradiciones, trayectorias y creencias, entre otras, de una comunidad educativa, contribuyen a resolver su necesidad de identificación cultural y de pertenencia y constituyen el conjunto de significados a partir de los que las niñas y los niños van dando forma y reconfiguran su mundo. (p. 27)

> De esta manera, el compromiso y la participación de la comunidad educativa dan soporte, pertinencia y riqueza a los proyectos educativos que se desarrollan. Para ello, resultan fundamentales los siguientes criterios:
>
> Reconocer su singularidad. Cada comunidad educativa resulta ser única; su cultura y, sobre todo, las interacciones que se dan en su interior, le aportan identidad. Dado que la comunidad educativa es un medio social y cultural en el que también se despliega la cotidianeidad de niñas, niños y adultos, resulta fundamental reconocer, respetar y aprovechar estas particularidades.
>
> Promover y valorar su participación activa en el proceso educativo. La comunidad es parte de la realidad cotidiana de los párvulos, y su participación aporta raigambre a la implementación curricular. Potenciar su compromiso con la labor educativa, asegura una transición respetuosa y fluida de las niñas y los niños, entre la educación familiar y la educación formal. (p. 27)

> [n. 14] El Desarrollo Sostenible es el paradigma global de las Naciones Unidas. El concepto de Desarrollo Sostenible fue descrito en 1987 en el Informe de la Comisión de Bruntland como un desarrollo que satisface las necesidades de la generación presente, sin comprometer la capacidad de las generaciones futuras de satisfacer sus propias necesidades (Organización de las Naciones Unidas, 2015b). Chile fue uno de los 193 Estados miembros de la Organización de las Naciones Unidas que en septiembre de 2015 aprobó la Agenda 2030 para el Desarrollo Sostenible (Organización de las Naciones Unidas, 2015a). (p. 24)

> [n. 16] La Ley General de Educación N° 20.370/ 2009. Art. 9, señala que la comunidad educativa es una agrupación de personas que inspiradas en un propósito común integran una institución educativa. Ese objetivo común es contribuir a la formación y el logro de aprendizajes de todos los alumnos que son miembros de ésta, propendiendo a asegurar su pleno desarrollo espiritual, ético, moral, afectivo, intelectual, artístico y físico. La comunidad educativa está integrada por alumnos, alumnas, padres, madres y apoderados, profesionales de la educación, asistentes de la educación, equipos docentes directivos y sostenedores educacionales. (p. 27)

### El enfoque pedagógico de la Educación Parvularia

La Pedagogía:

> La pedagogía en la Educación Parvularia se define en base a aquellas interacciones que ocurren con la intención de acoger, iniciar y mantener procesos que promueven el aprendizaje significativo de los párvulos. Para los equipos pedagógicos, esto implica identificar las oportunidades que existen para integrar y potenciar los aprendizajes de los distintos ámbitos del currículum y reconocer las relaciones de interdependencia y complementariedad que existen entre ellos. Supone utilizar diversos recursos en la preparación e implementación curricular y en la evaluación educativa, gestionando, seleccionando o elaborando aquellos más apropiados para favorecer la globalidad de las oportunidades educativas y la pertinencia de las interacciones pedagógicas. (p. 28)

> Se trata de un ejercicio integrador y centrado en los niños, las niñas y sus experiencias. En el marco de la Educación Parvularia, son especialmente relevantes aquellas en las que cada niña y niño, juega, decide, participa, se identifica, construye, se vincula, dialoga, trabaja con otros, explora su mundo, confía, percibe y se mueve, se autorregula, se conoce a sí mismo, atribuye significados, opina, expresa sus sentimientos, se asombra, desarrolla sus talentos, se organiza, disfruta, se hace preguntas, escucha y busca respuestas. La enseñanza representa entonces, la acción pedagógica al servicio de las potencialidades de aprendizajes de todas las niñas y los niños. (p. 28)

La Educadora y el Educador de Párvulos:

> Son considerados actores claves que guían el proceso educativo que ocurre en las salas cuna, jardines infantiles, escuelas y otros tipos de programas de Educación Parvularia, coordinando las actividades con los párvulos, sus familias, el equipo pedagógico y la comunidad en general, y mediando pedagógicamente entre todos ellos. Esto implica desplegar habilidades, disposiciones y conocimientos que favorecen la interacción con otros, tales como la empatía, la comunicación, la asertividad, la creatividad, la resolución de conflictos, la flexibilidad. (p. 28)

> Ejercer su rol profesional significa, por tanto, valorar la relevancia y el sentido de su labor pedagógica y asumir en forma autónoma y responsable (a través de un código ético específico) la toma de decisiones para el diseño, implementación y evaluación de un proceso educativo sistemático. Asimismo, requiere disponer de un saber profesional especializado con el que fundamentar las decisiones tomadas, saber que incluye la reflexión individual y colectiva sobre la propia práctica, construyendo así el conocimiento pedagógico para hacer su tarea cada vez mejor. (pp. 28–29)

> La interacción social con adultos especializados y portadores de los códigos y productos de la cultura, es la que permite a los párvulos construir y desarrollar los aprendizajes que se esperan de ellos. La interacción intencionada de las o los educadores con los párvulos ocurre en –y conforma- un contexto relacional que debe ser esencialmente positivo para que la intención pedagógica concluya en aprendizajes significativos. Es una interacción que la o el educador debe diseñar, preparando e implementando ambientes enriquecidos de aprendizaje, desafiantes al mismo tiempo que seguros, en los cuales todas las niñas y los niños se sientan considerados, desafiados pero confiados en sus potencialidades, dispuestos a aprender y protagonistas de sus propios aprendizajes. En ocasiones, la interacción verdaderamente pedagógica será aquella donde el docente creará un ambiente propicio y permanecerá presente, observando en silencio el despliegue de la actividad espontánea del niño o niña en su juego, individual o con otros. (p. 29)

> Lo anterior supone saber en profundidad cómo aprenden y se desarrollan los párvulos, y el lugar importantísimo que le cabe al juego en estos procesos; supone saber cómo y cuándo promover juegos y otras actividades lúdicas. Supone reconocer y responder pedagógicamente a la singularidad de cada uno en cuanto a ritmos, distintas formas de aprendizaje, género, cultura, contexto social, religión, entre otros. Asimismo, supone comprender cabalmente los Objetivos de Aprendizaje del currículum de la Educación Parvularia, para diseñar, contextualizar e implementar oportunidades de aprendizaje adecuadas a los objetivos intencionados, desarrollando además procesos de evaluación pertinentes, que permitan observar el progreso de las niñas y los niños, y utilizar sus resultados para retroalimentar el aprendizaje y la práctica pedagógica. (p. 29)

> Teniendo presente que las teorías de aprendizaje poseen un carácter dinámico y que están siempre en permanente análisis, es importante de igual modo precisar que las niñas y los niños, desde los primeros meses, aprenden y se aproximan al conocimiento de diferentes formas, como, por ejemplo, a través de interacción con objetos, experiencias con situaciones de la vida cotidiana, imitación, y especialmente a través de interacciones mediadas, que le permiten avanzar con el apoyo pertinente de un mediador que reconoce sus conocimientos y experiencias previas. Todas estas formas de aprender se deben tener presente al momento de planificar y poner en acción las prácticas pedagógicas. (p. 29)

> Las o los educadores de párvulos, desarrollan su quehacer con y junto a otros, razón por la cual resulta fundamental la constitución, fortalecimiento y liderazgo de equipos. El equipo pedagógico se encuentra conformado por todas aquellas personas que tienen una responsabilidad directa en la implementación de prácticas intencionadas, destinadas a acompañar y apoyar a las niñas y los niños en su aprendizaje. (p. 29)

> Al respecto, las o los docentes ejercen un activo rol para generar sentidos compartidos acerca de la tarea de educar y asumen la responsabilidad que le cabe al equipo en su conjunto, en la formación integral de las niñas y los niños. Esta conducción implica esencialmente proveer una visión acerca de aquello que resulta relevante y pertinente que los párvulos aprendan, así como de las oportunidades de aprendizaje que el equipo debe ofrecer para ello. (p. 30)

> Los niños y las niñas acceden a la Educación Parvularia con una historia y un bagaje que es primordial conocer y valorar, tarea en que sus familias tienen mucho que decir. Pero, la relación de la educadora y el educador con ellas tiene un propósito superior. La familia ejerce un fuerte influjo formativo en los niños y las niñas. En consecuencia, el docente requiere generar alianzas con las familias de los párvulos y una relación cercana con ellas para cooperar mutuamente en una labor formativa conjunta y coherente. (p. 30)

> Junto con todo lo anterior, el rol de la o el educador conlleva establecer relaciones de trabajo inter y transdisciplinar dentro y fuera del establecimiento, con los equipos directivos, las o los profesores de educación básica, las y los educadores tradicionales, psicólogos, educadores diferenciales, fonoaudiólogos, personal de salud de los consultorios y otros. Asimismo, implica establecer relaciones de colaboración con redes organizacionales y comunitarias, en función del Proyecto Educativo Institucional (PEI), no solo para atraer recursos que beneficien a los párvulos, sino para mostrarles un mundo de personas, actividades y relaciones más amplio y diverso. (p. 30)

### Principios pedagógicos

> Los principios pedagógicos constituyen un conjunto de orientaciones centrales de teoría pedagógica avalados por la investigación, proveniente tanto de los paradigmas fundantes de la Educación Parvularia, como de las construcciones teóricas que han surgido de la investigación del sector en las últimas décadas. Contribuyen a concebir, organizar, implementar y evaluar la práctica pedagógica, en torno a una visión común sobre cómo y para qué aprenden los párvulos en esta etapa de sus vidas y, por ende, cómo se deben promover estos procesos de aprendizaje. Este conjunto de principios permite configurar una educación eminentemente humanista, potenciadora, inclusiva y bien tratante. Deben ser considerados de manera integrada, sistémica y permanente. (p. 30)

Son 8 (pp. 31–33), transcritos completos:

1. Principio de bienestar.
   > Busca garantizar en todo momento la integridad física, psicológica, moral y espiritual del niño y la niña, así como el respeto de su dignidad humana. En virtud de ello, toda situación educativa debe propiciar que niñas y niños se sientan plenamente considerados en sus necesidades e intereses y avancen paulatina y conscientemente en la identificación de aquellas situaciones que les permiten sentirse integralmente bien. Con todo, serán activos en la creación de condiciones para su propio bienestar, desarrollando sentimientos de aceptación, plenitud, confortabilidad y seguridad, que los lleven a gozar del proceso de aprender. (p. 31)

2. Principio de unidad.
   > Cada niña y niño es una persona esencialmente indivisible, por lo que enfrenta todo aprendizaje en forma integral, participando con todo su ser en cada experiencia. Construye sus aprendizajes desde sus sentidos, su emoción, su pensamiento, su corporalidad, su espiritualidad, sus experiencias anteriores, sus deseos. A partir de este principio se considera la integralidad y completitud de los párvulos en todo momento. Por ello, desde la perspectiva del currículum, es necesario establecer el aprendizaje en diálogo con los objetivos del Ámbito de Desarrollo Personal y Social, aunque para efectos evaluativos, se definan ciertos énfasis. (p. 31)

3. Principio de singularidad.
   > Cada niño y niña, independientemente de la etapa de vida y nivel de desarrollo en que se encuentre, es un ser único con características, necesidades, intereses y fortalezas que se deben conocer, respetar y considerar efectivamente en toda situación de aprendizaje. Esta diversidad implica, entre otros, que cada niña y niño aprende a través de diversas formas y ritmos que le son propios, y también que posee formas de interpretar el mundo a partir de su cultura, situando el aprendizaje en contexto. (p. 31)

4. Principio de actividad.
   > La niña y el niño deben ser protagonistas de sus aprendizajes, a través de procesos de apropiación, construcción y comunicación. Por tanto, resulta fundamental que el equipo pedagógico potencie este rol en las interacciones y experiencias de las que participa, disponiendo de ambientes enriquecidos y lúdicos, que activen su creatividad, favorezcan su expresión y les permitan generar cambios en su entorno, creando su propia perspectiva de la realidad en la que se desenvuelven. (p. 31)

5. Principio del juego.
   > El juego es, en la Educación Parvularia, un concepto central. Se refiere tanto a una actividad natural del niño o niña como a una estrategia pedagógica privilegiada. De acuerdo con autores clásicos del desarrollo y el aprendizaje [n. 17], el juego cumple un rol impulsor del desarrollo de las funciones cognitivas superiores, de la afectividad, de la socialización, de la adaptación creativa a la realidad. El juego es, a la vez, expresión de desarrollo y aprendizaje y condición para ello. Son innumerables las actividades que pueden llamarse juego en los párvulos a diferentes edades, desde tocar, golpear, manipular, llevarse todo a la boca, juntar hojas o piedras, amontonar, insertar anillos, cabalgar en un palo de escoba, imitar a la mamá, hasta participar en una dramatización, en juegos y actividades con determinadas reglas. Hay algunas diferencias sutiles entre actividades lúdicas y juego. Cualquier actividad de aprendizaje puede y debe ser lúdica, en el sentido de entretenida, motivante, con un enmarcamiento flexible. Por ejemplo, recoger hojas, pintar piedras, danzar al ritmo de una melodía, entre otros. Sin embargo, los juegos a diferencia de las actividades lúdicas como las anteriores, tienen una estructura interna creada espontáneamente por los propios niños y niñas, que los hace muy valiosos para la Educación Parvularia, por cuanto responden plena y singularmente no solo a sus motivaciones internas, sino a sus requerimientos de desarrollo. (p. 32) [n. 17: Como Bruner (2003), Piaget (1961), Vigotsky (1933) y otros.]

6. Principio de relación.
   > La interacción positiva de la niña y el niño con pares y adultos, permite la integración y la vinculación afectiva y actúa como fuente de aprendizaje e inicio de su contribución social. Reconocer la dimensión social del aprendizaje en la infancia temprana, es asumir que las experiencias educativas que se propicien, deben favorecer que los párvulos interactúen significativa y respetuosamente con otros, y asuman en forma progresiva la responsabilidad de crear espacios colectivos inclusivos y armónicos, y aportar al bien común, como inicio de su formación ciudadana. (p. 32)

7. Principio de significado.
   > El niño y la niña construyen significativamente sus aprendizajes, cuando éstos se conectan con sus conocimientos y experiencias previas, responden a sus intereses y tienen algún tipo de sentido para ellos y ellas. Esto implica que las experiencias cumplen alguna función que puede ser lúdica, gozosa, sensitiva o práctica, entre otras. (p. 32)

8. Principio de potenciación.
   > Cuando el niño y la niña participan de ambientes enriquecidos para el aprendizaje, desarrolla progresivamente un sentimiento de confianza en sus propias fortalezas y talentos para afrontar mayores y nuevos desafíos y aprender de sus errores, tomando conciencia progresiva de sus potencialidades. (p. 33)

### Fin y propósitos de la Educación Parvularia

> La Educación Parvularia, como primer nivel del sistema educativo, tiene como fin favorecer una educación de calidad, oportuna y pertinente, que propicie aprendizajes relevantes y significativos en función del bienestar, el desarrollo pleno y la trascendencia de la niña y del niño como personas. Ello en estrecha relación y complementación con la labor educativa de la familia, propiciando a la vez su continuidad en el sistema educativo y su contribución a la sociedad, en un marco de valores nacionalmente compartidos que reconoce a niñas y niños en su calidad de sujetos de derecho. (p. 33)

> Para favorecer lo anterior, se plantean los siguientes propósitos:
>
> Promover el bienestar integral de la niña y el niño mediante la creación de ambientes saludables, protegidos, acogedores y ricos en términos de oportunidades de aprendizaje, donde ellos vivan y aprecien el cuidado, la seguridad y la confortabilidad y potencien su confianza, curiosidad e interés por las personas y el mundo que los rodea.
>
> Propiciar el desarrollo de experiencias de aprendizaje que, junto con la familia, inicien a las niñas y los niños en su formación valórica y como ciudadanos, considerándolos en su calidad de sujetos de derecho, en función de la búsqueda de la trascendencia y el bien común.
>
> Promover en la niña y el niño la identificación y valoración progresiva de sus propias características personales, necesidades, preferencias y fortalezas, para favorecer una imagen positiva de sí mismos y el desarrollo de su identidad y autonomía, así como la consideración y respeto hacia los demás.
>
> Favorecer aprendizajes oportunos, pertinentes y con sentido para las niñas y los niños, que fortalezcan su disposición por aprender en forma activa, creativa y permanente; y que promuevan el desarrollo personal y social, la comunicación integral y la interacción y comprensión del entorno.
>
> Propiciar aprendizajes de calidad en las niñas y los niños que sean pertinentes y consideren las necesidades educativas especiales, las diversidades culturales, lingüísticas, de género, religiosas y sociales, junto a otros aspectos culturales significativos de ellos, sus familias y comunidades.
>
> Favorecer la transición de la niña y del niño a la Educación Básica, propiciando el desarrollo y aprendizaje de las actitudes, habilidades y conocimientos necesarios para esta trayectoria educativa e implementando los procesos pedagógicos que la facilitan.
>
> Potenciar la participación permanente de la familia en función de la realización de una labor educativa conjunta, complementaria y congruente, que favorezca el desarrollo y aprendizaje de las niñas y los niños.
>
> Propiciar un trabajo conjunto con la comunidad educativa, con respeto a las características y necesidades educativas de la niña y del niño, para generar condiciones más pertinentes a su atención y formación integral. (pp. 33–34)

Nota: los tres aprendizajes del cuarto propósito (desarrollo personal y social, comunicación integral, interacción y comprensión del entorno) corresponden a los tres ámbitos del Capítulo 2.

---

## Capítulo 2 — Organización curricular

La jerarquía es: Ámbito (3) → Núcleo (8) → Nivel curricular (3 tramos de 2 años) → Objetivos de Aprendizaje (206). Las definiciones de cada componente se transcriben a continuación. El Capítulo 2 abre con un diagrama de "Componentes Estructurales de las Bases Curriculares" (p. 36) que cruza los ocho núcleos de los tres ámbitos con los tres tramos; su contenido es el que desarrollan las definiciones de las pp. 37–44.

### Definiciones fundamentales de los componentes estructurales

Ámbitos de Experiencias para el Aprendizaje:

> Constituyen campos curriculares donde se organizan y distribuyen los Objetivos de Aprendizaje, con el propósito de orientar los procesos educativos. (p. 38)

> Los Objetivos de Aprendizaje que se proponen en estas Bases Curriculares se organizan en tres grandes ámbitos que los párvulos experimentan: Desarrollo Personal y Social, Comunicación Integral e Interacción y Comprensión del Entorno. En su conjunto, éstos abarcan campos de acción donde se llevan a cabo procesos claves para la tarea formativa y de aprendizaje de la Educación Parvularia. (p. 38)

> Estos ámbitos de experiencias comprenden aspectos que se contienen y vinculan unos con otros: en un nivel más personal e interpersonal, la niña y el niño aprenden sobre sí mismos y los demás, creciendo en autonomía, identidad y sociabilidad. Al mismo tiempo, forman parte de sus familias y comunidades, inmersos en un entorno más amplio. Entre estos dos niveles la comunicación, da cuenta de la necesaria interacción entre ellos y actúa como mediador entre ambos. (p. 38)

> La organización de estos tres ámbitos, estrechamente relacionados entre sí, da cuenta de la integralidad en la que se construyen los aprendizajes. Tiene la intención de ordenar la prescripción curricular y el proceso formativo, permitiendo a las y los educadores mayor claridad para planificar, implementar y evaluar el trabajo educativo. (p. 38)

> En estas Bases Curriculares, el Ámbito de Desarrollo Personal y Social adquiere un carácter transversal en la estructura e implementación curricular, debido a la relevancia formativa que tienen sus componentes para el desarrollo humano y por lo cual se requiere, que sean visibilizados de manera permanente en todas las acciones educativas que se propician con los niños y las niñas. (p. 38)

> Así, los Ámbitos de Experiencias para el Aprendizaje se constituyen en una propuesta, que aporta claridad respecto de la intencionalidad pedagógica. (p. 38)

Núcleos de Aprendizajes:

> Al interior de cada ámbito se definen núcleos de aprendizaje. Constituyen distinciones curriculares que delimitan focos centrales de experiencias en torno a los cuales se agrupan e integran un conjunto de Objetivos de Aprendizaje (OA) con el propósito de contribuir a la organización y sistematización del trabajo educativo. (p. 39)

> Los núcleos permiten promover el aprendizaje integral de las niñas y los niños, considerando los conocimientos, habilidades y actitudes, que fortalecen el desarrollo personal y social, la comunicación integral, y la interacción y comprensión del entorno. (p. 39)

> En cuanto a su contenido, los núcleos proponen objetivos que destacan aprendizajes fundamentales de favorecer en el nivel de Educación Parvularia. Las distintas intencionalidades que se explicitan en estos, son esenciales para fortalecer una formación humana integral que potencia a la niña y el niño como personas únicas, con una multiplicidad de capacidades en todos los planos. (p. 39)

> Todos los núcleos que se presentan son igualmente importantes para promover el aprendizaje integral de los párvulos, por lo que deben favorecerse en el proceso educativo. (p. 39)

> Cada núcleo se presenta con una definición general que busca situar el enfoque desde el cual se lo concibe, explicitando aspectos fundamentales de los aprendizajes desde una mirada integradora. Además, cada uno define las intencionalidades educativas que se buscan desarrollar desde los primeros meses, hasta el ingreso a la educación básica, resguardando los sentidos de trayectoria educativa. (p. 39)

> Los núcleos que integran el Ámbito de Desarrollo Personal y Social, como se señaló anteriormente, adquieren un carácter transversal en la arquitectura e implementación curricular. Representan énfasis o dominios que se consideran fundamentales para la disposición para el aprendizaje, fortaleciendo las relaciones de confianza, afecto y colaboración, basadas en el respeto y valoración de las personas. Alcanzan una especial relevancia en el currículum de Educación Parvularia, dado que en esta etapa comienzan a establecerse y desarrollarse las bases del comportamiento humano para valerse por sí mismo, interactuar y contribuir en distintos ámbitos. (p. 39)

> Desde esa mirada, los Objetivos de Aprendizaje que forman parte de estos núcleos buscan alcanzar en la formación personal y social, que los niños y las niñas a través del desarrollo de la autonomía, la conciencia gradual de sus posibilidades corporales y motrices, la identidad, junto con los aspectos involucrados en una convivencia positiva y democrática, puedan enfrentar diversos desafíos de aprendizaje. (p. 39)

Objetivos de Aprendizaje:

> Definen los aprendizajes esenciales que se espera potenciar en las niñas y los niños durante la Educación Parvularia, integrando las principales habilidades, conocimientos y actitudes que les permitirán construir una base sólida de aprendizajes para avanzar en su desarrollo armónico e integral. Las habilidades constituyen capacidades para llevar a cabo procedimientos, estrategias y acciones con precisión y adaptabilidad. Pueden desarrollarse tanto en el ámbito cognitivo, psicomotriz, como afectivo y/o social. Los conocimientos corresponden a conceptos, redes de conceptos e información sobre hechos, procedimientos y operaciones. Las actitudes son disposiciones comportamentales aprendidas hacia objetos, ideas o personas; incluyen componentes afectivos, cognitivos y valorativos que orientan a determinados tipos de actuación. (p. 40)

> Se conforma de esta manera un currículum centrado en el aprendizaje, que declara explícitamente cuál es el foco del quehacer pedagógico. Se organizan de acuerdo a ocho núcleos y tres niveles educativos. (p. 40)

Objetivos de Aprendizaje (p. 40):

> Definen los aprendizajes esenciales que se espera potenciar en las niñas y los niños durante la Educación Parvularia, integrando las principales habilidades, conocimientos y actitudes que les permitirán construir una base sólida de aprendizajes para avanzar en su desarrollo armónico e integral. Las habilidades constituyen capacidades para llevar a cabo procedimientos, estrategias y acciones con precisión y adaptabilidad. Pueden desarrollarse tanto en el ámbito cognitivo, psicomotriz, como afectivo y/o social. Los conocimientos corresponden a conceptos, redes de conceptos e información sobre hechos, procedimientos y operaciones. Las actitudes son disposiciones comportamentales aprendidas hacia objetos, ideas o personas; incluyen componentes afectivos, cognitivos y valorativos que orientan a determinados tipos de actuación. (p. 40)

Tres características de los OA que son críticas para Kimün:

> Los Objetivos de Aprendizaje en el nivel de Educación Parvularia, evidencian en forma clara y precisa cuál es el aprendizaje que se busca lograr. Se enuncian desde lo que se espera al final de cada nivel, es decir abarcando tramos curriculares de dos años. En el primer nivel (sala cuna) se presentan con una estructura más secuenciada, por la mayor incidencia del desarrollo en el logro de los aprendizajes. En cambio, para el segundo y tercer nivel curricular (medio y transición), la secuencia es más flexible, puesto que muchos de ellos dependen de los aprendizajes previos o de los niveles de desarrollo alcanzados anteriormente. Se prescriben de este modo, porque los párvulos presentan una amplia variabilidad natural en la adquisición de logros de aprendizaje. Una temporalidad más corta de prescripción, anual, por ejemplo, tiene el inconveniente de que no respetaría diferencias individuales en el aprendizaje. (p. 40)

> En el caso de los Objetivos de Aprendizaje transversales, para lograr su consolidación, resulta fundamental incorporarlos en forma permanente de acuerdo a criterios de selección pedagógica en las distintas planificaciones educativas. De esta manera, la frecuencia y profundización en las diversas experiencias de aprendizaje, se traducen en factores indispensables para su efectiva apropiación, otorgando una concepción más integradora al proceso de aprendizaje. (p. 40)

> Las Bases Curriculares se constituyen como un referente amplio y flexible que admite diversas formas de implementación; estos objetivos pueden ser complementados y especificados de acuerdo a las necesidades de aprendizaje de las niñas y los niños y, a las características de los proyectos educativos. (p. 40)

> Es conveniente destacar que cada uno de los Objetivos de Aprendizaje puede manifestarse de diversas maneras; esto significa que el párvulo que ha adquirido el aprendizaje especificado en alguno de los objetivos de estas Bases, lo puede evidenciar a través de diferentes desempeños concretos. (p. 40)

> Los Objetivos de Aprendizaje se han concebido como equitativos, en el sentido de que se espera que todos los párvulos, sin distinciones, alcancen las expectativas de logro que implican. No obstante, sus manifestaciones pueden variar de acuerdo a las características propias de las comunidades, y de las niñas y los niños en especial. (p. 41)

Nota sobre los OA transversales (OAT): son los de los tres núcleos del Ámbito Desarrollo Personal y Social, en los tres niveles. En el documento, los OA de IA, CC y CM aparecen titulados "Objetivos de Aprendizaje transversales".

### Niveles curriculares

> Constituyen una forma de organización temporal de los Objetivos de Aprendizaje en tres niveles curriculares, respondiendo con mayor precisión a las necesidades y características del aprendizaje y desarrollo de los párvulos. Los tres niveles curriculares, que abarcan tramos de dos años cada uno, se denominan: 1° Nivel (Sala Cuna) hacia los dos años; 2° Nivel (Medio) hacia los cuatro años y 3° Nivel (Transición) hacia los seis años. A continuación, se describen brevemente. (p. 41)

> 1° Nivel (Sala Cuna). Lo que caracteriza a estos meses o años es la marcada dependencia del niño o niña frente al adulto, por quien desarrolla un fuerte apego en casi todas las tareas relacionadas con su subsistencia. A partir de esta situación se pone en marcha una sostenida conquista de autonomía, posibilitada por la emergencia de ciertas capacidades fundamentales que marcan el punto de inflexión: la locomoción independiente mediante la adquisición de la marcha y, luego, la ampliación de su capacidad de comunicar y pensar gracias a la adquisición del lenguaje verbal. Este punto de inflexión más o menos universal se sitúa hacia los 18/24 meses, aproximadamente en la mayoría de los niños y las niñas, pues, aunque ellos suelen lograr antes de los 18 meses las capacidades de locomoción, deben esperar unos meses para la adquisición plena del lenguaje verbal y la autoafirmación de la identidad. (p. 41)

> 2° Nivel (Medio). Posteriormente, a partir de este punto de inflexión, el niño y niña van adquiriendo cada vez más el control y dominio progresivo de todas las habilidades motoras que le permiten explorar y participar en sus entornos. Actúan con mayor independencia, participan en juegos grupales, se expresan oralmente, empleando estructuras oracionales simples. Al mismo tiempo, se esfuerzan por comprender el mundo que les rodea y elaboran sus propias explicaciones, comprenden y resuelven algunos problemas. La construcción de identidad, la afectividad y la relación con los demás, sigue este mismo patrón, desde una relación de apego del niño y niña en la etapa anterior, hacia los adultos significativos de quienes depende y que deciden por él, hacia una noción de sí cada vez más separada y diferenciada de ellos. (p. 42)

> 3° Nivel (Transición). Después de esta etapa, los párvulos mayores siguen en la lógica de adquisición de autonomía e identidad de la anterior, pero se pueden diferenciar de sus pares más pequeños del 2º Nivel (Medio) gracias a sus mayores capacidades motrices, cognitivas, afectivas y sociales. Se produce una expansión del lenguaje, incremento del dominio, control y equilibrio en sus movimientos, mayor conciencia corporal, más empatía, autorregulación, respeto de normas, mayor desarrollo de las funciones ejecutivas, interés por descubrir el contenido de textos escritos. Se justifica, además, como grado o grupo independiente, porque constituye un nivel de transición entre la Educación Parvularia y la Educación Básica, con diseños curriculares que intentan hacer un puente entre ambos. (p. 42)

> De este modo, se configuran los tres niveles que se proponen: 1º Nivel (Sala cuna), 2º Nivel (Medio) y 3º Nivel (Transición), los que se justifican curricularmente en sus características distintivas. (p. 42)

> [n. 18] La estructura organizacional y administrativa del nivel de Educación Parvularia respecto a la normativa de funcionamiento en los establecimientos educativos, es la siguiente: Sala Cuna (Menor y Mayor), Medio (Menor y Mayor) y Transición (Primer y Segundo). (p. 42)

Dos citas que fundamentan el "nivel esperado como referencia blanda" de Kimün:

> La nueva organización de Objetivos de Aprendizaje en tres niveles curriculares, que se alinea con la estructura administrativa general de la Educación Parvularia [n. 18], está diseñada como una referencia que orienta los periodos óptimos, pero en ningún caso implica limitar las expectativas de progreso de los párvulos que no se ajustan a ellos. Al contrario, se espera que continúen avanzando desde una mirada de trayectoria educativa. (p. 42)

> En consecuencia, la organización de los objetivos, en tres niveles o tramos curriculares exige ser aplicada con flexibilidad, al asumirse que el aprendizaje es un continuo que puede describirse en trayectorias referenciales. (p. 43)

Y la base de "OA de nivel adyacente sin marcarlo fuera de rango" (adecuaciones curriculares):

> Así, en el marco de las adecuaciones curriculares para la inclusión, se pueden seleccionar Objetivos de Aprendizaje de un nivel diferente al del grupo o curso de párvulos, correspondiendo al saber profesional de las y los educadores, tomar las decisiones pedagógicas pertinentes para propiciar aprendizajes relevantes y significativos. (p. 43)

Nota: administrativamente, el Tercer Nivel se denomina NT1 (Primer) y NT2 (Segundo), según la nota [n. 18].

### Tabla resumen de los componentes estructurales (p. 44)

Transcripción literal de la tabla resumen que cierra el apartado:

> Ámbitos de Experiencias: Constituyen campos curriculares donde se organizan y distribuyen los Objetivos de Aprendizaje, con el propósito de orientar los procesos de enseñanza y aprendizaje.
>
> Núcleos de Aprendizajes: Corresponden a focos de experiencias para el aprendizaje, en torno a los cuales se integra y articula un conjunto determinado de objetivos de aprendizaje. Los que pertenecen al Ámbito de Desarrollo Personal y Social adquieren un carácter transversal en el currículum.
>
> Objetivos de Aprendizaje: Establecen los aprendizajes que se esperan de los párvulos en cada nivel educativo, precisando las habilidades, actitudes y conocimientos que se busca lograr mediante la práctica pedagógica de la Educación Parvularia. Al interior de ellos, se distinguen Objetivos de Aprendizaje transversales (OAT).
>
> Niveles o tramos Curriculares: Constituyen una forma de organización temporal de los Objetivos de Aprendizaje en tres niveles curriculares, respondiendo con mayor precisión a las necesidades y características del aprendizaje y desarrollo de los párvulos. Los tres niveles curriculares, que abarcan tramos de dos años cada uno, se denominan: 1° Nivel (Sala Cuna), 2° Nivel (Medio) y 3° Nivel (Transición). (p. 44)

### Tabla de conteo de OA

Conteo verificado por script contra el texto del PDF (coincide con `hallazgos-bases-curriculares.md`).

| Ámbito | Núcleo | Sigla | Sala Cuna | Medio | Transición | Total |
|---|---|---|---:|---:|---:|---:|
| Desarrollo Personal y Social (transversal) | Identidad y Autonomía | IA | 7 | 12 | 13 | 32 |
| | Convivencia y Ciudadanía | CC | 6 | 10 | 11 | 27 |
| | Corporalidad y Movimiento | CM | 7 | 8 | 9 | 24 |
| Comunicación Integral | Lenguaje Verbal | LV | 8 | 8 | 10 | 26 |
| | Lenguajes Artísticos | LA | 6 | 7 | 7 | 20 |
| Interacción y Comprensión del Entorno | Exploración del Entorno Natural | EEN | 5 | 9 | 12 | 26 |
| | Comprensión del Entorno Sociocultural | CES | 5 | 7 | 11 | 23 |
| | Pensamiento Matemático | PM | 6 | 10 | 12 | 28 |
| Total | | | 50 | 71 | 85 | 206 |

---

## Ámbito: Desarrollo Personal y Social

Núcleos: Identidad y Autonomía (IA), Convivencia y Ciudadanía (CC), Corporalidad y Movimiento (CM). Carácter transversal (sus OA se titulan "Objetivos de Aprendizaje transversales").

> El ámbito de experiencias para el aprendizaje referido al Desarrollo Personal y Social, articula el conjunto de aprendizajes que niñas y niños requieren desarrollar para enfrentar sus interacciones desde la confianza, seguridad y valoración positiva de sí mismos y de los demás, y así disfrutar su presente. En este ámbito, los correspondientes núcleos y Objetivos de Aprendizaje, adquieren un carácter transversal, por el significado formativo que tienen sus componentes en los procesos de aprendizaje. (p. 46)

> En este sentido, el Desarrollo Personal y Social integra equilibradamente la relación entre la creciente autonomía que le permiten el desarrollo de la corporalidad y el movimiento, la afirmación de la identidad debido al reconocimiento y aceptación de las propias necesidades, emociones, afectos, características, intereses, fortalezas, habilidades personales, así como las de los otros que son miembros de los grupos que lo rodean. La conciencia de sí mismo(a), la expresión y regulación de emociones, el sentido de pertenencia, la convivencia con otros, el sentido del bien común y el inicio en la ciudadanía -si se encuentran en equilibrio-, se traduce finalmente en un estado vital de satisfacción y plenitud de los párvulos. (p. 46)

> Por consiguiente, este ámbito favorece el desarrollo de párvulos que experimentan el mundo sintiéndose sujetos protagonistas de este proceso desde el momento en que nacen; llenos de curiosidad y de ganas de vivir. Si niñas y niños perciben que son considerados y respetados en sus características, necesidades e intereses, desarrollan sentimientos de aceptación, respeto y valoración, así como sensaciones de confortabilidad y seguridad. (p. 46)

> Lo anterior tiene varias implicancias. En primer término, sus experiencias cotidianas, niñas y niños, las viven en y a través del cuerpo. Es a partir de él, que experimentan, expresan, comprenden y se vinculan con otros -pares y adultos-, y con el mundo que habitan. Estas distintas interacciones, proveen el contexto en el que los párvulos desarrollan conocimientos acerca de sí mismos, integrando las distintas dimensiones que los conforman (cuerpo, emociones, afectos, ideas). Así, simultáneamente, en este vínculo con otros, los párvulos descubren características, intereses y emociones que los hacen únicos y desarrollan las herramientas que les permiten tomar decisiones e incidir en su entorno. (p. 46)

> En consecuencia, se expresa en núcleos de aprendizaje que consideran: Identidad y Autonomía, Convivencia y Ciudadanía, Corporalidad y Movimiento. Todos ellos potencian la activa participación de niñas y niños en su propio desarrollo, fortaleciendo su capacidad para mirarse a sí mismos y establecer vínculos positivos y de respeto con los demás. (p. 46)

Nota: la caracterización de cada ámbito y sus núcleos abre con una nota [n. 19] (p. 45) que sitúa las áreas más frecuentes en los currículos europeos de educación inicial según la OECD (2017): desarrollo personal y social, lenguaje y comunicación, conocimiento del mundo circundante, expresión creativa, desarrollo físico y movimiento, orientación ética y la responsabilidad; y, hacia el final del período, alfabetización, numeración, educación física, ciencia, artes, música, habilidades prácticas, salud y bienestar, ciencias sociales, ética y ciudadanía, TIC y lenguas extranjeras.

### Núcleo Identidad y Autonomía (IA)

Introducción (definición):

> El Núcleo Identidad y Autonomía, refiere al proceso de construcción gradual de una conciencia de sí mismo que realiza la niña y el niño, como individuo singular diferente de los otros, en forma paralela y complementaria con la adquisición progresiva de independencia y autovalencia en los distintos planos de su actuar. Se trata de procesos integrados especialmente relevantes en esta etapa de la vida, que se inician tempranamente y se desarrollan durante todo el período y más allá de los seis años. A través de ellos, los párvulos adquieren una concepción y aprecio de sí mismos como personas únicas, con determinadas características físicas, habilidades, gustos, preferencias, opiniones e iniciativas, con confianza para aventurarse a explorar el entorno y desenvolverse en él en forma autónoma, relacionarse con otros, aprender y disfrutar de sus avances y logros. Estos logros se apoyan en aprendizajes de otros núcleos, como el desarrollo del lenguaje verbal, de las funciones ejecutivas del pensamiento, de la afectividad y alfabetización emocional. (p. 47)

> El cimiento que sostiene a estos procesos que llevan a la construcción de una identidad positiva y a la autonomía creciente, es el vínculo afectivo de los niños y las niñas con sus adultos significativos, que les permite sentirse queridos y experimentar una confianza básica en el mundo, y luego la aceptación incondicional permanente por parte de ellos. Es en el contexto de las interacciones que establecen con otras personas significativas, que los párvulos comienzan a tomar conciencia gradual de sus características y atributos personales, entre ellos su sexo e identidad de género, sus fortalezas, habilidades, apegos, intereses y preferencias. A la vez que afirman su identidad, requieren más autonomía. Los niños y las niñas, dependientes de los adultos en los comienzos de su vida en casi todas las acciones vitales, necesitan ensayar y conquistar las habilidades que les permitirán realizarlas por sí mismos, diferenciándose e independizándose de los adultos, con quienes, no obstante, mantienen una relación de afecto y confianza. (p. 47)

Orientaciones pedagógicas:

> Considerando lo anterior, resulta fundamental generar ambientes de aprendizaje en los cuales los adultos se relacionen con niños y niñas en forma estable, atenta y sensible, enfatizando la cercanía física y emocional, el respeto, el afecto, el buen trato; validando claramente las potencialidades de los párvulos en su singularidad. Con este fin, es importante el reconocimiento y valoración respetuosa por parte del adulto de cada una de sus características, sus esfuerzos y logros, y de sus preferencias en situaciones cotidianas y de juego, ofreciendo al niño y niña las decisiones que le competen, por ejemplo, con quién compartir sus juegos, cómo y con qué recursos desarrollarlos. (pp. 47–48)

> En estas interacciones positivas y enriquecedoras, las niñas y los niños deben sentirse libres de explorar, expresar, sentir y comunicar, desarrollando sentimientos de seguridad, aprendiendo a aceptar la contención y protección de los adultos, así como también desarrollando progresivamente habilidades y actitudes que les permiten entregar apoyo a sus pares. (p. 48)

> En función de su alfabetización emocional, crear diversas oportunidades en que los párvulos identifiquen sus emociones y las de los demás, por ejemplo, a través de experiencias de arte en que pueden imaginar lo que "sentirían si" ocurriera algún suceso especial, expresándolo a través de títeres o muñecos, o a través de la plástica o el dibujo. También son enriquecedoras las oportunidades asociadas a la literatura, en las que los niños y las niñas pueden escuchar breves historias o relatos de cuentos en las que van reconociendo sus emociones y las de los demás, incorporando nuevas palabras a su repertorio lingüístico. Asimismo, dando oportunidades y acompañando instancias en que puedan desarrollar tolerancia a la frustración y autorregulación, al resolver situaciones y superar desafíos motrices, cognitivos, afectivos, sociales. (p. 48)

> Especial consideración merece, por tanto, el juego autodeterminado, de imaginación, particularmente desde los dos años, a través de los cuales los niños y las niñas actúan espontáneamente sus necesidades, motivos profundos, aspiraciones afectivas. La situación imaginaria que el párvulo crea no es cualquiera. En este tipo de juegos, por ejemplo, las situaciones creadas por él y ella ya tienen límites y reglas de comportamiento (que él o ella pone), sin ser propiamente un juego de reglas; el párvulo es capaz de renunciar a sus impulsos inmediatos por considerar los límites que voluntariamente (se) impone en la situación de juego. Así, aprende a regular su comportamiento y emociones, fortaleciendo su voluntad, lo que forma parte de los aprendizajes esenciales para su desarrollo integral. En este tipo de juego el niño y la niña están por encima de su actuación diaria, en el sentido que son capaces de hacer lo que no pueden cotidianamente; solo él o ella saben inventar el juego que crea su zona de desarrollo proximal, por eso el equipo pedagógico debe crear instancias apropiadas para que jueguen libremente. (p. 48)

> Por otra parte, con la finalidad de potenciar la expresión de iniciativas de interés de los mismos niños y niñas, y de que logren apreciar los resultados de sus ideas, acciones y compromisos asumidos, resulta fundamental que se incorporen estrategias en que se desarrollen iniciativas que les motiven, lo que fortalecerá habilidades asociadas a las funciones ejecutivas, como asociar ideas, orientar la acción hacia una meta, planificar, definir objetivos, poner en juego su memoria de trabajo al recordar algunas secuencias de acción necesarias, concentrar su atención para avanzar en su logro, flexibilizar sus definiciones para buscar diferentes alternativas de acción, tomar decisiones, prever consecuencias y paralelamente tomar progresiva conciencia de las posibilidades que le permite el ser autónomo. (p. 48)

> La mayor autonomía conlleva comprensión del autocuidado. Es importante que los niños y las niñas vayan comprendiendo poco a poco, la necesidad de realizar prácticas de autocuidado, identificando, por ejemplo, los beneficios que posee el adoptar hábitos saludables, y por qué razón un objeto o situación es riesgosa o peligrosa para su bienestar. Para ello, el adulto requiere, junto con mostrarles el propio ejemplo, conversar en forma directa y sencilla acerca de las ventajas o las precauciones al respecto, utilizando preguntas, ejemplos y relatos. (pp. 48–49)

Propósito general del núcleo:

> A través de la Identidad y Autonomía se espera potenciar en las niñas y en los niños habilidades, actitudes y conocimientos que les permitan la construcción gradual de su identidad como sujetos únicos y valiosos, y a la vez adquieran progresiva independencia, confianza, autovalencia y autorregulación, en los distintos planos de su actuar. De esta manera, amplían la conciencia de sí mismos y sus recursos de autoestima e iniciativa. (p. 49)

Nota: en Transición, este es el único núcleo que hoy tiene rúbrica oficial de Integra (`datos/rubrica_integra.json`), cuyos textos retoman la redacción de estos OA.

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 50

| ID | Cita | OA |
|---|---|---|
| `IA-SC-1` | OA 1 IA | Expresar vocal, gestual o corporalmente distintas necesidades o emociones (alegría, miedo, pena, entre otras). |
| `IA-SC-2` | OA 2 IA | Manifestar satisfacción cuando percibe que adultos significativos le expresan afecto. |
| `IA-SC-3` | OA 3 IA | Reconocer algunas emociones en adultos significativos, reaccionando frente a ellas. |
| `IA-SC-4` | OA 4 IA | Manifestar sus preferencias por algunas situaciones, objetos y juegos. |
| `IA-SC-5` | OA 5 IA | Manifestar interés por nuevas situaciones u objetos, ampliando su campo y repertorio de acción habitual. |
| `IA-SC-6` | OA 6 IA | Reconocer algunos rasgos distintivos de su identidad, tales como: su nombre y su imagen física en el espejo. |
| `IA-SC-7` | OA 7 IA | Incorporar rutinas básicas vinculadas a la alimentación, vigilia, sueño, higiene, y vestuario dentro de un contexto diferente a su hogar y sensible a sus necesidades personales. |

Segundo Nivel (Medio) — p. 51

| ID | Cita | OA |
|---|---|---|
| `IA-M-1` | OA 1 IA | Representar verbal y corporalmente diferentes emociones y sentimientos, en sus juegos. |
| `IA-M-2` | OA 2 IA | Manifestar disposición y confianza al separarse de los adultos significativos. |
| `IA-M-3` | OA 3 IA | Reconocer en sí mismo, en otras personas y en personajes de cuentos, emociones tales como: tristeza, miedo, alegría, pena y rabia. |
| `IA-M-4` | OA 4 IA | Manifestar disposición para regular sus emociones y sentimientos, en función de las necesidades propias, de los demás y de algunos acuerdos para el funcionamiento grupal. |
| `IA-M-5` | OA 5 IA | Manifestar sus preferencias cuando participa o cuando solicita participar, en diversas situaciones cotidianas y juegos. |
| `IA-M-6` | OA 6 IA | Actuar con progresiva independencia, ampliando su repertorio de acciones, acorde a sus necesidades e intereses. |
| `IA-M-7` | OA 7 IA | Comunicar algunos rasgos de su identidad, como su nombre, sus características corporales, género y otros. |
| `IA-M-8` | OA 8 IA | Apreciar sus características identitarias, fortalezas y habilidades. |
| `IA-M-9` | OA 9 IA | Manifestar progresiva independencia en sus prácticas de alimentación, vigilia y sueño, vestimenta, higiene corporal, bucal y evacuación. |
| `IA-M-10` | OA 10 IA | Manifestar satisfacción y confianza por su autovalía, comunicando algunos desafíos alcanzados, tales como: saltar, hacer torres, sacar cáscara de huevos, entre otros. |
| `IA-M-11` | OA 11 IA | Identificar alimentos que se consumen en algunas celebraciones propias de su familia y comunidad. |
| `IA-M-12` | OA 12 IA | Representar sus pensamientos y experiencias, atribuyendo significados a objetos o elementos de su entorno, usando la imaginación en situaciones de juego. |

Tercer Nivel (Transición) — p. 52

| ID | Cita | OA |
|---|---|---|
| `IA-T-1` | OA 1 IA | Comunicar a los demás, emociones y sentimientos tales como: amor, miedo, alegría, ira, que le provocan diversas narraciones o situaciones observadas en forma directa o a través de TICs. |
| `IA-T-2` | OA 2 IA | Manifestar disposición y confianza para relacionarse con algunos adultos y pares que no son parte del grupo o curso. |
| `IA-T-3` | OA 3 IA | Reconocer emociones y sentimientos en otras personas, observadas en forma directa o a través de TICs. |
| `IA-T-4` | OA 4 IA | Expresar sus emociones y sentimientos autorregulándose en función de las necesidades propias, de los demás y las normas de funcionamiento grupal. |
| `IA-T-5` | OA 5 IA | Comunicar sus preferencias, opiniones, ideas, en diversas situaciones cotidianas y juegos. |
| `IA-T-6` | OA 6 IA | Planificar proyectos y juegos, en función de sus ideas e intereses, proponiendo actividades, organizando los recursos, incorporando los ajustes necesarios e iniciándose en la apreciación de sus resultados. |
| `IA-T-7` | OA 7 IA | Comunicar rasgos de su identidad de género, roles (nieta/o, vecino/a, entre otros), sentido de pertenencia y cualidades personales. |
| `IA-T-8` | OA 8 IA | Comunicar sus características identitarias, fortalezas, habilidades y desafíos personales. |
| `IA-T-9` | OA 9 IA | Cuidar su bienestar personal, llevando a cabo sus prácticas de higiene, alimentación y vestuario, con independencia y progresiva responsabilidad. |
| `IA-T-10` | OA 10 IA | Comunicar a otras personas desafíos alcanzados, identificando acciones que aportaron a su logro y definiendo nuevas metas. |
| `IA-T-11` | OA 11 IA | Distinguir parámetros establecidos para la regulación de alimentos, tales como: etiquetado de sellos, fechas de vencimiento, entre otros. |
| `IA-T-12` | OA 12 IA | Anticipar acciones y prever algunas situaciones o desafíos que se pueden presentar, en juegos, proyectos, sucesos que experimenta o que observa a través de TICs. |
| `IA-T-13` | OA 13 IA | Representar en juegos sociodramáticos, sus pensamientos y experiencias atribuyendo significados a objetos, personas y situaciones. |

### Núcleo Convivencia y Ciudadanía (CC)

Introducción (definición):

> El Núcleo Convivencia y Ciudadanía, está referido al conjunto de actitudes, conocimientos y habilidades sociales y emocionales, que permiten al niño y la niña, convivir pacíficamente con otros, tomar decisiones que favorecen el bien común, y desarrollar progresivamente un sentido de pertenencia a una comunidad cada vez más amplia, compartiendo valores y responsabilidades sobre la base de los derechos humanos [n. 20]. Este núcleo busca promover el ejercicio de una ciudadanía activa, a través de la participación, la colaboración y el respeto. (p. 53)

> Aprender a convivir, reconociendo los ideales y las prácticas en las que se sustenta la ciudadanía, es un proceso fundamental para la formación integral que se inicia desde la primera infancia. La Educación Parvularia, a partir de la convivencia con otras personas, constituye un espacio y una oportunidad para que los párvulos avancen en la construcción de relaciones significativas con pares y adultos, en un marco de respeto mutuo. Este aprendizaje permanente, continuo y transversal a los distintos ámbitos de experiencia, promueve el desarrollo progresivo de valores como la empatía, el respeto de la diversidad y la solidaridad, entre otros, los que constituyen las bases para ejercer la ciudadanía de un modo constructivo, comprometido y responsable. (p. 53)

> Es también de vital importancia promover en estas etapas iniciales, el desarrollo de normas y acuerdos establecidos o creados colectivamente para el bienestar común. Las relaciones horizontales basadas en el diálogo y la generación de acuerdos y normas con sentido, fortalecen el desarrollo de la ciudadanía, pues progresivamente los párvulos asumen las responsabilidades por sus actos, la preocupación por el bien común y el ejercicio pleno de sus derechos. (p. 53)

> En este proceso gradual de formación para la ciudadanía, resulta fundamental que niños y niñas se sientan parte y miembros activos de su familia y de su comunidad, base que les permitirá ampliar progresivamente su identificación social. Se trata de construir un sentido de pertenencia crecientemente inclusivo, integrando valores y costumbres socialmente compartidos, descubriendo el valor de otras comunidades humanas, promoviendo así un progresivo desarrollo del sentido de justicia y responsabilidad en las relaciones entre todas las personas. (p. 53)

Orientaciones pedagógicas:

> Para favorecer los Objetivos de Aprendizaje de este núcleo, es necesario generar oportunidades donde los niños y las niñas participen activamente y en forma progresiva, en diferentes actividades y juegos grupales de carácter colaborativo, en los cuales puedan disfrutar por estar junto a otros, expresar opiniones, respetar las normas y reglas acordadas, hacer propuestas para la resolución pacífica de conflictos cotidianos, participar en la elaboración de proyectos grupales, siendo parte de las decisiones colectivas desde una perspectiva inclusiva. (p. 54)

> Aquellas estrategias donde los párvulos puedan sugerir las áreas de juego, seleccionar recursos, proponer y decidir sobre los aspectos estéticos y de organización de los espacios educativos, consensuar estrategias para el desarrollo de proyectos, entre otras, generan hábitos de participación y ciudadanía a partir de los primeros años. (p. 54)

> Es importante que las primeras experiencias de participación y colaboración de los párvulos en pequeños grupos sean gratificantes, por lo que estas actividades deben acentuar lo entretenido y lúdico, permitiendo que descubran las potencialidades de "estar con otros". El equipo pedagógico debe reconocer sus decisiones, logros y esfuerzos al respecto, fortaleciendo el incremento de nuevas palabras a su repertorio lingüístico. (p. 54)

> Un ambiente de aprendizaje que promueve la convivencia y la ciudadanía, se fortalece cuando los equipos pedagógicos, generan oportunidades guiadas para que los niños y las niñas conozcan y se interesen por la existencia y costumbres de otras comunidades tanto del país como de otros lugares del mundo, utilizando diversos recursos, entre los cuales también se incorporan tecnologías de información y comunicación. (p. 54)

> Ampliar las interacciones con diversos grupos o cursos en un marco de respeto por las costumbres, singularidades personales y culturales, como son: celebraciones, juegos colectivos, ceremonias o la participación en producciones artísticas y encuentros interculturales, contribuyen a apreciar la diversidad en las personas, incorporando el principio de igualdad y no discriminación. (p. 54)

> La integración de familiares o miembros de la comunidad en las experiencias pedagógicas, asumiendo distintas funciones que se realizan en el aula o en otros espacios, favorece el intercambio, la confianza y el conocimiento de los propósitos educativos de cada una de las estrategias. (p. 54)

> Uno de los principales recursos de los adultos para promover experiencias de participación, y prácticas democráticas y colaborativas en el nivel parvulario, consiste en modelar el tipo de relaciones que se desea construir, por lo que es importante dialogar, facilitando instancias cotidianas para que las niñas y los niños expresen opiniones, respeten acuerdos, propongan estrategias pacificas frente a situaciones de conflicto y puedan organizarse en torno a propósitos comunes. (p. 54)

> Por otra parte, es conveniente favorecer que las niñas y los niños desde muy temprana edad, conozcan sus diferencias con otros grupos de párvulos y aprecien la diversidad. Es importante que el equipo pedagógico, propicie la comprensión de sus derechos, tales como: tener un nombre, ser bien tratado, jugar, y participar de la educación, entre otros. (p. 55)

Propósito general del núcleo:

> A través de Convivencia y Ciudadanía, se espera potenciar en los niños y las niñas, las habilidades, actitudes y conocimientos que les permitan convivir en armonía, descubriendo y ejerciendo progresivamente su ciudadanía y generando identificación con una comunidad inclusiva sobre la base de los derechos propios y los de los demás. (p. 55)

> [n. 20] Este núcleo sigue la concepción amplia de formación ciudadana formulada en el marco de la Ley N° 20.911, referida al Plan de Formación Ciudadana, ley que fue creada para promover la formación ciudadana en el sistema educacional. Allí, la ciudadanía es entendida como una vida responsable en una sociedad libre y de orientación hacia el mejoramiento integral de la persona humana, como fundamento del sistema democrático, la justicia social y el progreso. En atención al nivel de desarrollo de los párvulos, esta Ley cautela que la formación ciudadana se hará de acuerdo a las características particulares del nivel y su contexto, por ejemplo, a través del juego. El Núcleo Convivencia y Ciudadanía comparte contenidos relacionados con la formación ciudadana con el Núcleo Entorno Sociocultural (ver nota aclaratoria en Núcleo Entorno Sociocultural). (p. 53)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 56

| ID | Cita | OA |
|---|---|---|
| `CC-SC-1` | OA 1 CC | Interactuar con pares y adultos significativos (a través de gestos y vocalizaciones, entre otros), en diferentes situaciones y juegos. |
| `CC-SC-2` | OA 2 CC | Disfrutar de la cercanía de niños, niñas y adultos en juegos y situaciones cotidianas. |
| `CC-SC-3` | OA 3 CC | Manifestar interés por lo que le sucede a otros niños y niñas, a través de acciones tales como: abrazar a quien está llorando, hacer cariños, entre otros. |
| `CC-SC-4` | OA 4 CC | Manifestar interés por participar en celebraciones de su entorno significativo. |
| `CC-SC-5` | OA 5 CC | Practicar algunas normas de convivencia, tales como: sentarse en su silla para almorzar, saludar, despedirse, y colaborar en acciones cotidianas. |
| `CC-SC-6` | OA 6 CC | Manifestar disposición para responder positivamente o cambiar su comportamiento, frente a requerimientos del adulto, asociados a su seguridad y bienestar. |

Segundo Nivel (Medio) — p. 57

| ID | Cita | OA |
|---|---|---|
| `CC-M-1` | OA 1 CC | Participar en actividades y juegos grupales con sus pares, conversando, intercambiando pertenencias, cooperando. |
| `CC-M-2` | OA 2 CC | Disfrutar de instancias de interacción social con diversas personas de la comunidad. |
| `CC-M-3` | OA 3 CC | Colaborar en situaciones cotidianas y de juego, proponiendo acciones simples frente a necesidades que presentan sus pares. |
| `CC-M-4` | OA 4 CC | Colaborar en actividades, conmemoraciones o celebraciones culturales de su familia y comunidad. |
| `CC-M-5` | OA 5 CC | Iniciarse en la resolución pacífica de conflictos, dialogando respecto de la situación, escuchando, opinando y proponiendo acciones para resolver. |
| `CC-M-6` | OA 6 CC | Manifestar disposición para practicar acuerdos de convivencia básica que regulan situaciones cotidianas y juegos. |
| `CC-M-7` | OA 7 CC | Identificar objetos, comportamientos y situaciones de riesgo que pueden atentar contra su seguridad, bienestar y el de los demás. |
| `CC-M-8` | OA 8 CC | Reconocer acciones correctas e incorrectas para la convivencia armónica del grupo, que se presentan en diferentes situaciones cotidianas y juegos. |
| `CC-M-9` | OA 9 CC | Manifestar interés por algunos de sus derechos, tales como: ser escuchados, tener un nombre, jugar, entre otros. |
| `CC-M-10` | OA 10 CC | Manifestar interés para interactuar con niños y niñas, reconociendo la diversidad de sus características y formas de vida (costumbres, fisonomía, lingüística, entre otras). |

Tercer Nivel (Transición) — p. 58

| ID | Cita | OA |
|---|---|---|
| `CC-T-1` | OA 1 CC | Participar en actividades y juegos colaborativos, planificando, acordando estrategias para un propósito común y asumiendo progresivamente responsabilidades en ellos. |
| `CC-T-2` | OA 2 CC | Participar en actividades solidarias, que integran a las familias, la comunidad educativa y local. |
| `CC-T-3` | OA 3 CC | Manifestar empatía y solidaridad frente a situaciones que vivencian sus pares, o que observa en textos o TICs, practicando acciones de escucha, apoyo y colaboración. |
| `CC-T-4` | OA 4 CC | Apreciar el significado que tienen para las personas y las comunidades, diversas manifestaciones culturales que se desarrollan en su entorno. |
| `CC-T-5` | OA 5 CC | Aplicar estrategias pacíficas frente a la resolución de conflictos cotidianos con otros niños y niñas. |
| `CC-T-6` | OA 6 CC | Respetar normas y acuerdos creados colaborativamente con pares y adultos, para el bienestar del grupo. |
| `CC-T-7` | OA 7 CC | Identificar objetos, comportamientos y situaciones de riesgo que pueden atentar contra su bienestar y seguridad, o la de los demás, proponiendo alternativas para enfrentarlas. |
| `CC-T-8` | OA 8 CC | Comprender que algunas de sus acciones y decisiones respecto al desarrollo de juegos y proyectos colectivos, influyen en las de sus pares. |
| `CC-T-9` | OA 9 CC | Reconocer, y progresivamente hacer respetar el derecho a expresarse libremente, a ser escuchado y a que su opinión sea tomada en cuenta. |
| `CC-T-10` | OA 10 CC | Reconocer progresivamente requerimientos esenciales de las prácticas de convivencia democrática, tales como: escucha de opiniones divergentes, el respeto por los demás, de los turnos, de los acuerdos de las mayorías. |
| `CC-T-11` | OA 11 CC | Apreciar la diversidad de las personas y sus formas de vida, tales como: singularidades fisonómicas, lingüísticas, religiosas, de género, entre otras. |

### Núcleo Corporalidad y Movimiento (CM)

Introducción (definición):

> Este Núcleo busca articular equilibradamente los distintos factores neurológicos, fisiológicos, psicológicos y sociales que permiten el desarrollo armónico de la corporalidad y el movimiento. A partir del movimiento las niñas y los niños adquieren conciencia de su propio cuerpo, desarrollan grados crecientes de autonomía, fortalecen su identidad, descubren su entorno, expanden sus procesos de pensamiento, resuelven problemas prácticos, establecen relaciones de orientación espacio temporal y potencian su expresión. (p. 59)

> El cuerpo y el movimiento se configuran en una unidad que integra y moviliza aspectos sensoriales, emocionales, afectivos, cognitivos y socioculturales para ser y actuar en contextos de diversidad; la conciencia gradual de su corporalidad y de sus posibilidades motrices se construyen y amplían, mediante un proceso de interacción permanente con el entorno. (p. 59)

> En este sentido, a través del movimiento, el párvulo va conociéndose y expandiendo las potencialidades de su cuerpo. No se trata de ejercicio físico mecánico, sino de interacciones que le permitan gradualmente la apropiación, comprensión y anticipación de las distintas situaciones que le interesan, sobre las que actúa y le rodean. (p. 59)

> Los procesos de toma de conciencia de la corporalidad no ocurren en un vacío social. La representación y significación que las personas tienen del cuerpo propio y de los otros está determinada en gran medida por el contexto sociocultural donde circulan sentidos diversos en torno al cuerpo. En este sentido es importante que la formación en este núcleo ponga atención a esos mensajes y a la manera que los párvulos los están significando. (p. 59)

> Resulta fundamental generar las condiciones necesarias para que los niños y niñas aprecien su cuerpo y se sientan cómodos con él, se expresen con libertad, exploren activamente y experimenten; ello contribuirá al desarrollo de una percepción adecuada de su imagen, conciencia de su esquema corporal, más adelante, la definición de su lateralidad y la identificación cada vez más precisa de sus recursos corporales. (p. 59)

Orientaciones pedagógicas:

> La toma de conciencia progresiva del propio cuerpo y sus potenciales, es un proceso que requiere de la observación del adulto para identificar y ofrecer experiencias en forma oportuna, otorgar tiempo suficiente para el desarrollo, seleccionar los recursos más pertinentes, y así potenciar el descubrimiento cotidiano de sus avances, alcanzados en forma autómata. (p. 60)

> De tal modo, se hace necesario que la o el educador genere un ambiente de aprendizaje que ofrece permanentes y variadas oportunidades de exploración libre, confiada e intuitiva de los niños y las niñas, que respete sus necesidades de confortabilidad y que acoja el goce que le produce el movimiento. Lo anterior, incluye la reorganización del mobiliario para hacer el espacio más amplio, el uso de vestimenta cómoda y flexible por parte de los párvulos, la compañía y mediación del equipo pedagógico para moverse autónomamente en forma segura, y la implementación de variados y atractivos lugares de juego. El diseño y recreación de los espacios debe posibilitar, que las niñas y los niños libremente puedan ensayar diversas posiciones, transitar y circular de manera fluida, ejecutar múltiples desplazamientos, alternar y equilibrar posturas en superficies planas e inclinadas, crear juegos corporales y motrices, conquistar espacios con más altura que la habitual, practicar movimientos de fuerza, resistencia, tracción y empuje. (p. 60)

> Por lo anterior, los recursos para el aprendizaje requieren cumplir criterios esenciales de calidad, de manera que permitan a los niños y niñas explorar su corporalidad y diversos movimientos. Las piezas en volumen con diferentes densidades y texturas que permiten alternar distintas disposiciones espaciales, favorecen la oportunidad de trepar, apilar, empujar, entre otras acciones motrices que decidan desarrollar. Así también, objetos tales como: balones, aros, telas, cajas, botellas recuperables, conos, tubos, cintas y cuerdas de diferente tamaño, y a los que se les puede otorgar diversa utilidad, dan la posibilidad de realizar prácticas lúdicas variadas que involucran probar, reiterar, enfrentar y resolver nuevas formas de movimiento, contribuyendo no tan solo a los componentes motrices, sino conjuntamente a otras capacidades relacionadas con la autonomía, el lenguaje, el pensamiento lógico matemático y también la creatividad. (p. 60)

> Especialmente para los primeros años, se requiere una exigente y rigurosa selección de recursos para el aprendizaje de manera que cumplan criterios de seguridad, variabilidad y desafío exploratorio. Los materiales deben poseer contenedores adecuados, permitiendo que progresivamente los párvulos más pequeños puedan tomarlos, explorarlos y volver a depositarlos en su lugar. (p. 60)

> Por otra parte, se requiere intencionar situaciones para que el niño y la niña reconozcan sus sensaciones de agrado o desagrado, a través de experiencias tales como el uso de cojines más duros o blandos, objetos de diferentes tamaños, el contacto con telas transparentes (para apreciar diversas luminosidades a través de éstas), el uso de juguetes con texturas más rugosas o lisas para manipular, la exploración de hierbas, flores o especias que le permitan distinguir olfativamente o momentos para percibir la temperatura del adulto significativo cuando lo abraza. Asimismo, dar tiempo suficiente para relajar y distenderse corporalmente en plenitud y para tener oportunidad de observar y hablar de su cuerpo, y los cambios que se producen en este, con el movimiento. (pp. 60–61)

> Todo ello forma parte de las claves didácticas para potenciar el conocimiento corporal y el desarrollo de movimientos cada vez más precisos y fluidos. (p. 61)

Propósito general del núcleo:

> A través de corporalidad y movimiento, se espera potenciar en las niñas y los niños, habilidades, actitudes y conocimientos que le permitan reconocer y apreciar sus atributos corporales, descubrir sus posibilidades motrices, adquirir una progresiva autonomía para desplazarse y moverse, y que contribuyan a expandir sus procesos de pensamiento, satisfacer sus intereses de exploración, fortalecer su identidad, resolver problemas prácticos y expresar su creatividad. De esta manera, ampliarán sus recursos para actuar en el entorno, desarrollando un sentido de autonomía, bienestar, confianza y seguridad. (p. 61)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 62

| ID | Cita | OA |
|---|---|---|
| `CM-SC-1` | OA 1 CM | Manifestar su agrado, al sentirse cómodo, seguro y contenido corporalmente. |
| `CM-SC-2` | OA 2 CM | Descubrir partes de su cuerpo y algunas de sus características físicas, a través de diversas experiencias sensoriomotrices. |
| `CM-SC-3` | OA 3 CM | Manifestar interés y satisfacción al moverse libremente en situaciones cotidianas y lúdicas. |
| `CM-SC-4` | OA 4 CM | Ampliar sus posibilidades de exploración sensoriomotriz, adquiriendo control de la prensión palmar voluntaria (toma objetos, se pasa objetos de una mano a otra, entre otros) y la postura sedente. |
| `CM-SC-5` | OA 5 CM | Adquirir desplazamiento gradual en sus distintas formas (girar, reptar, ponerse de pie, caminar), para disfrutar la ampliación de sus posibilidades de movimiento, exploración y juego. |
| `CM-SC-6` | OA 6 CM | Coordinar movimientos de manipulación ubicando objetos en relación a su propio cuerpo, tales como: acercar objetos pequeños utilizando índice y pulgar en oposición. |
| `CM-SC-7` | OA 7 CM | Explorar la alternancia de posturas y movimientos en acciones tales como: trepar, lanzar objetos o hacer ronda, adquiriendo control gradual de su cuerpo al jugar. |

Segundo Nivel (Medio) — p. 63

| ID | Cita | OA |
|---|---|---|
| `CM-M-1` | OA 1 CM | Reconocer situaciones en que se siente cómodo corporalmente, manifestando al adulto su bienestar y su interés por mantener estas condiciones. |
| `CM-M-2` | OA 2 CM | Reconocer las principales partes, características físicas de su cuerpo y sus funciones en situaciones cotidianas y de juego. |
| `CM-M-3` | OA 3 CM | Experimentar diversas posibilidades de acción con su cuerpo, en situaciones cotidianas y de juego, identificando progresivamente el vocabulario asociado. |
| `CM-M-4` | OA 4 CM | Reconocer el bienestar que le produce el movimiento libre en situaciones cotidianas y lúdicas, manifestando su interés por desarrollarlo en forma frecuente. |
| `CM-M-5` | OA 5 CM | Perfeccionar su coordinación visomotriz fina, a través del uso de diversos objetos, juguetes y utensilios. |
| `CM-M-6` | OA 6 CM | Adquirir control y equilibrio en movimientos, posturas y desplazamientos que realiza en diferentes direcciones y en variadas situaciones cotidianas y juegos, con y sin implementos. |
| `CM-M-7` | OA 7 CM | Resolver desafíos prácticos en situaciones cotidianas y juegos, incorporando mayor precisión y coordinación en la realización de posturas, movimientos y desplazamientos, tales como: esquivar obstáculos o mantener equilibrio al subir escalas. |
| `CM-M-8` | OA 8 CM | Utilizar categorías de ubicación espacial y temporal, tales como: adelante/atrás, arriba/ abajo, adentro/afuera, antes/ después, rápido/lento, en situaciones cotidianas y lúdicas. |

Tercer Nivel (Transición) — p. 64

| ID | Cita | OA |
|---|---|---|
| `CM-T-1` | OA 1 CM | Manifestar iniciativa para resguardar el autocuidado de su cuerpo y su confortabilidad, en función de su propio bienestar. |
| `CM-T-2` | OA 2 CM | Apreciar sus características corporales, manifestando interés y cuidado por su bienestar y apariencia personal. |
| `CM-T-3` | OA 3 CM | Tomar conciencia de su cuerpo, de algunas de sus características internas (tales como: ritmo cardíaco, de respiración), de su esquema y progresivamente de su tono corporal y lateralidad, por medio de juegos. |
| `CM-T-4` | OA 4 CM | Comunicar nuevas posibilidades de acción logradas a través de su cuerpo en situaciones cotidianas y de juego, empleando vocabulario preciso. |
| `CM-T-5` | OA 5 CM | Comunicar el bienestar que le produce el movimiento, al ejercitar y recrear su cuerpo en forma habitual, con y sin implementos u obstáculos. |
| `CM-T-6` | OA 6 CM | Coordinar con precisión y eficiencia sus habilidades psicomotrices finas en función de sus intereses de exploración y juego. |
| `CM-T-7` | OA 7 CM | Resolver desafíos prácticos manteniendo control, equilibrio y coordinación al combinar diversos movimientos, posturas y desplazamientos tales como: lanzar y recibir, desplazarse en planos inclinados, seguir ritmos, en una variedad de juegos. |
| `CM-T-8` | OA 8 CM | Coordinar sus habilidades psicomotoras practicando posturas y movimientos de fuerza, resistencia y tracción tales como: tirar la cuerda, transportar objetos, utilizar implementos, en situaciones cotidianas y de juego. |
| `CM-T-9` | OA 9 CM | Utilizar categorías de ubicación espacial y temporal, tales como: adelante/atrás/al lado/entre, día/noche, hoy/ mañana, antes/durante/después, en situaciones cotidianas y lúdicas. |

---

## Ámbito: Comunicación Integral

Núcleos: Lenguaje Verbal (LV) y Lenguajes Artísticos (LA).

> La comunicación constituye el proceso central mediante el cual niñas y niños desde los primeros años de vida intercambian y construyen significados con los otros. La interacción con el medio, a través de diferentes instrumentos de comunicación, permite exteriorizar vivencias de todo tipo, acceder a los contenidos culturales, producir y comprender mensajes cada vez más elaborados y ampliar la capacidad de actuar en el medio. La comunicación potencia las relaciones que los párvulos establecen consigo mismo, con las personas y con los distintos ambientes en los que participan. (p. 66)

> Los lenguajes que constituyen el Ámbito de la Comunicación Integral, son el Lenguaje Verbal y los Lenguajes Artísticos. Desde los primeros momentos de su vida, niñas y niños se encuentran inmersos en distintos procesos comunicativos, interactuando y comunicando a través de diversos recursos gestuales y corporales, lo que les permite participar y desenvolverse en los contextos que les son propios. A medida que crecen, y habitan mundos cada vez más amplios y complejos, requieren manejar y desarrollar el lenguaje verbal en el que se comunican las personas. Mediante la adquisición y desarrollo de este lenguaje, los párvulos se inician también en procesos de mayor amplitud cultural, posibilitando la adquisición de otros lenguajes especializados, como son las artes en sus diversas expresiones, las que les abren nuevas oportunidades. (p. 66)

> Estos dos lenguajes, que operan en forma integrada en el encuentro del párvulo con su entorno, potencian su pensamiento y capacidad de expresión y de acción. Comunicar sus experiencias y actuar, implica hacer uso de ideas, palabras, símbolos y signos, que hacen comprensible, para sí y para otros, el contexto en el que se desenvuelven, exteriorizando las vivencias emocionales, disfrutando y desarrollando el pensamiento creativo y la imaginación. De esta forma, mediante las habilidades, actitudes y conocimientos vinculados al Lenguaje Verbal y a los Lenguajes Artísticos, los párvulos fortalecen sus procesos de pensamiento con categorías y conceptos que circulan en la cultura general, al mismo tiempo que robustecen referentes culturales propios. (p. 66)

> Más allá de centrarse exclusivamente en los conceptos y el pensamiento reforzando un sesgo cognitivo, en este ámbito se favorece la interdependencia del bienestar integral, la estrecha interacción entre lo emocional y lo cognitivo, lo analítico y las artes creativas. (p. 66)

### Núcleo Lenguaje Verbal (LV)

Introducción (definición):

> El lenguaje verbal, es uno de los recursos más significativos mediante los cuales los párvulos se comunican. Es un instrumento imprescindible para el desarrollo del pensamiento del niño o niña especialmente en su dimensión oral. A través del habla, no sólo expresan sus sensaciones, necesidades, emociones, opiniones y vivencias, sino que, además, organizan y controlan su comportamiento e interpretan y construyen el mundo que habitan. (p. 67)

> Este núcleo se refiere fundamentalmente al desarrollo y potenciación del lenguaje oral de los párvulos y a su centralidad como herramienta de comunicación y de desarrollo cognitivo. Desde que aparece el lenguaje oral, el pensamiento da un salto cualitativo y adquiere una base verbal, y el habla, a su vez, se empieza a usar para pensar. (p. 67)

> El lenguaje guarda una estrecha relación con la interacción social. No hay lenguaje sin interacción social. Para el desarrollo del niño y la niña, especialmente en sus etapas iniciales, lo que reviste importancia primordial son las interacciones con los adultos significativos, en tanto portadores de los contenidos de la cultura que el niño o niña acomoda y asimila. No obstante, la comunicación es una interacción social típica de la lengua oral, que incluye también a los pares. (p. 67)

> Entre el nacimiento y los 6 años, la dimensión oral es la que presenta mayor relevancia, puesto que es la primera que se desarrolla; está más vinculada al contexto cotidiano de niñas y niños y, por tanto, más cercana. A través de la interacción con el entorno, los párvulos van ampliando sus posibilidades de significación y comunicación. En tanto instrumento de comunicación, el lenguaje oral incluye componentes no verbales, esto es, expresiones faciales, gestos corporales, movimientos del cuerpo, entre otros; y paraverbales, es decir, timbre, volumen, entonación y tono de voz, que contribuyen a significar y contextualizar la comunicación. (p. 67)

> En relación a la dimensión escrita, las niñas y los niños, si bien están expuestos a diversos textos escritos desde temprano, la adquieren en la medida que acceden a ambientes alfabetizados y cuentan con procesos de mediación ajustada. Lo anterior, hace posible que los párvulos reconozcan las particularidades y las diferencias entre el lenguaje oral y el escrito, y que vayan adquiriendo progresivamente la conciencia fonológica y gráfica, incorporando los recursos y las convenciones propias del modo escrito. (p. 67)

> El lenguaje verbal posibilita que todos los niños y las niñas desplieguen una intensa actividad para construir e intercambiar significados en distintos contextos, con diferentes propósitos y personas. De esta manera, pueden participar activa y creativamente de la sociedad y de la red de significados compartidos que constituye la cultura: expresando sentimientos, emociones e ideas, reconociendo e interpretando ciertos aspectos particulares de culturas distintas a la propia, accediendo a diferentes tipos de información, potenciando su autonomía. Este conjunto integrado de habilidades de pensamiento, posibilitan y modulan a su vez los diversos aprendizajes que ha de construir el párvulo en el futuro. (pp. 67–68)

Orientaciones pedagógicas:

> Resulta fundamental generar ambientes de aprendizaje que contemplen múltiples oportunidades para la expresión oral de las niñas y los niños, que ofrezcan instancias para que, a través de relatos y comentarios sobre sus vivencias, pensamientos y emociones, puedan dar cuenta de la riqueza de su mundo interno, y otorgarle sentido y significado a su entorno. Esto es especialmente significativo en el marco de proyectos y juegos colaborativos, reconociendo que estas instancias generan oportunidades para intercambiar opiniones, información e ideas. (p. 68)

> Importa generar oportunidades de aprendizaje en los cuales los adultos respondan a las primeras iniciativas comunicativas de los niños y las niñas (gestos, sonrisas, balbuceos, sonidos), y les hablen con un claro propósito comunicativo, complementado con gestos y movimientos. Ambientes que, luego, ofrezcan instancias para escuchar y producir relatos; intercambiar comentarios sobre sus experiencias; expresar pensamientos y emociones, ampliar el vocabulario para dar significado a objetos, acontecimientos, situaciones; siempre considerando el contexto de comunicación en el que se expresa. (p. 68)

> Por supuesto, el carácter lúdico que puedan tener estas instancias es un elemento motivador. Junto con las experiencias organizadas por el o la educadora, aquellas que se constituyen como juego espontáneo y autodeterminado por niños y niñas merecen un lugar central, por cuanto en ellas se desarrolla el pensamiento en un nivel óptimo de complejidad para los requerimientos particulares del desarrollo de cada párvulo. (p. 68)

> Así también, el lenguaje verbal se favorece a través de la utilización de preguntas que propician el planteamiento de problemas o la formulación de conjeturas. Las preguntas, del párvulo y del equipo pedagógico, contribuyen a la construcción y comprensión de mensajes, sirven para que niños y niñas den a conocer sus opiniones, incrementen su vocabulario y fomenten su curiosidad natural. (p. 68)

> También es importante que estos ambientes enriquecidos, cuenten con diversos materiales escritos que despierten el interés y la curiosidad de niños y niñas por acceder a los significados involucrados en ellos, promoviendo el contacto cotidiano con la lectura. Esto implica disponer distintos tipos de imágenes, recursos digitales, textos variados y auténticos para ser manipulados en forma autónoma por los párvulos, desde los primeros años. (pp. 68–69)

> Junto con lo anterior, resulta conveniente poner a disposición, en los distintos niveles educativos, variados tipos de papeles, formatos, soportes, lápices y otros recursos o elementos que les permitan explorar y experimentar su producción escrita de carácter emergente y auténtica. (p. 69)

> Para la iniciación a la lectura, el relato periódico de cuentos seleccionados según su valor literario e intereses de los niños y las niñas es una buena oportunidad para conocer, escuchar con atención, comentar y promover la motivación por la lectura. Así mismo es también valioso incentivar estrategias como las "caminatas de lectura" a través de paseos y visitas en los cuales tengan contacto con mensajes escritos. (p. 69)

> Dentro de las habilidades metalingüísticas que se requieren para iniciar el desarrollo del aprendizaje de la lectura, es fundamental desarrollar la conciencia fonológica cuyo elemento central, es la toma de conciencia de que las palabras están formadas por sonidos (fonemas y sílabas). En un sentido amplio, la conciencia fonológica implica tomar conciencia lexical (que las frases u oraciones están compuestas por palabras), conciencia silábica (que las palabras están compuestas por sílabas) y conciencia fonémica (que las sílabas están compuestas por fonemas). (p. 69)

> Estas habilidades se pueden potenciar a través de diversos recursos y juegos, como distinguir palabras largas y cortas, buscar palabras que comiencen con un mismo sonido, marcar mediante percusión de palmas o movimientos gestuales las sílabas de algunas palabras, agrupar objetos o recopilar imágenes que comienzan con la misma sílaba, resolver desafíos identificando palabras iguales que escucha en juegos digitales, segmentar palabras, entre otros. (p. 69)

Propósito general del núcleo:

> A través de Lenguaje Verbal, se espera potenciar en las niñas y los niños, las habilidades, actitudes y conocimientos que les posibiliten desarrollar su pensamiento, comprender el entorno que habitan y comunicarse, relacionándose con otras personas, construyendo e intercambiando significados. De esta manera, amplían progresivamente sus recursos comunicativos verbales y paraverbales para expresar sus sensaciones, vivencias, emociones, sentimientos, necesidades, ideas y opiniones, construyendo una base sólida sobre la cual asimilar otros aprendizajes presentes y futuros. (p. 69)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 70

| ID | Cita | OA |
|---|---|---|
| `LV-SC-1` | OA 1 LV | Expresar oralmente sus emociones y necesidades, a través de balbuceos, vocalizaciones y diversos recursos gestuales. |
| `LV-SC-2` | OA 2 LV | Expresar oralmente sus necesidades e intereses, mediante la combinación de palabras y gestos, el uso de palabra-frase y progresivamente el empleo de frases simples. |
| `LV-SC-3` | OA 3 LV | Identificar progresivamente la intención comunicativa de las distintas personas de su entorno a partir de sus expresiones verbales, no verbales y paraverbales. |
| `LV-SC-4` | OA 4 LV | Comprender mensajes simples y breves en juegos y situaciones comunicativas cotidianas, respondiendo en forma gestual y corporal. |
| `LV-SC-5` | OA 5 LV | Reconocer sonidos de diferentes fuentes sonoras de su entorno cotidiano, tales como objetos, artefactos, instrumentos musicales, animales, naturaleza. |
| `LV-SC-6` | OA 6 LV | Incorporar nuevas palabras a su repertorio lingüístico para comunicarse con otros, en juegos y conversaciones. |
| `LV-SC-7` | OA 7 LV | Disfrutar de distintos textos gráficos (libros de cuentos, láminas, entre otros) al manipularlos y observar sus imágenes. |
| `LV-SC-8` | OA 8 LV | Comprender progresivamente, a partir de la escucha atenta, algunos contenidos explícitos de textos literarios y no literarios, respondiendo preguntas simples, en forma oral o gestual (¿qué es?, ¿quién es?, ¿dónde está?). |

Segundo Nivel (Medio) — p. 71

| ID | Cita | OA |
|---|---|---|
| `LV-M-1` | OA 1 LV | Expresarse oralmente, empleando estructuras oracionales simples y respetando patrones gramaticales básicos, en distintas situaciones cotidianas y juegos. |
| `LV-M-2` | OA 2 LV | Comprender mensajes simples como instrucciones explícitas, explicaciones y preguntas relativas a objetos, personas, acciones, tiempo y lugar, identificando la intencionalidad comunicativa de diversos interlocutores. |
| `LV-M-3` | OA 3 LV | Identificar algunos atributos de los sonidos de diferentes fuentes sonoras como intensidad (fuerte/suave), velocidad (rápido/lento). |
| `LV-M-4` | OA 4 LV | Incorporar progresivamente nuevas palabras, al comunicar oralmente temas variados de su interés e información básica, en distintas situaciones cotidianas. |
| `LV-M-5` | OA 5 LV | Manifestar interés por descubrir el contenido de textos de diferentes formatos, a través de la manipulación, la exploración, la escucha atenta y la formulación de preguntas. |
| `LV-M-6` | OA 6 LV | Comprender a partir de la escucha atenta, contenidos explícitos de textos literarios y no literarios, reconociendo ideas centrales, señalando preferencias, realizando sencillas descripciones, preguntando sobre el contenido. |
| `LV-M-7` | OA 7 LV | Reconocer progresivamente el significado de diversas imágenes, logos, símbolos de su entorno cotidiano, en diversos soportes (incluye uso de TICs). |
| `LV-M-8` | OA 8 LV | Producir sus propios signos gráficos en situaciones lúdicas. |

Tercer Nivel (Transición) — p. 72

| ID | Cita | OA |
|---|---|---|
| `LV-T-1` | OA 1 LV | Expresarse oralmente en forma clara y comprensible, empleando estructuras oracionales completas, conjugaciones verbales adecuadas y precisas con los tiempos, personas e intenciones comunicativas. |
| `LV-T-2` | OA 2 LV | Comprender textos orales como preguntas, explicaciones, relatos, instrucciones y algunos conceptos abstractos en distintas situaciones comunicativas, identificando la intencionalidad comunicativa de diversos interlocutores. |
| `LV-T-3` | OA 3 LV | Descubrir en contextos lúdicos, atributos fonológicos de palabras conocidas, tales como conteo de palabras, segmentación y conteo de sílabas, identificación de sonidos finales e iniciales. |
| `LV-T-4` | OA 4 LV | Comunicar oralmente temas de su interés, empleando un vocabulario variado e incorporando palabras nuevas y pertinentes a las distintas situaciones comunicativas e interlocutores. |
| `LV-T-5` | OA 5 LV | Manifestar interés por descubrir el contenido y algunos propósitos de diferentes textos escritos (manipulando, explorando, realizando descripciones y conjeturas) a través del contacto cotidiano con algunos de ellos, o del uso de TICs. |
| `LV-T-6` | OA 6 LV | Comprender contenidos explícitos de textos literarios y no literarios, a partir de la escucha atenta, describiendo información y realizando progresivamente inferencias y predicciones. |
| `LV-T-7` | OA 7 LV | Reconocer palabras que se encuentran en diversos soportes asociando algunos fonemas a sus correspondientes grafemas. |
| `LV-T-8` | OA 8 LV | Representar gráficamente algunos trazos, letras, signos, palabras significativas y mensajes simples legibles, utilizando diferentes recursos y soportes en situaciones auténticas. |
| `LV-T-9` | OA 9 LV | Comunicar mensajes simples en la lengua indígena pertinente a la comunidad donde habita. |
| `LV-T-10` | OA 10 LV | Reconocer algunas palabras o mensajes sencillos de lenguas maternas de sus pares, distintas al castellano. |

### Núcleo Lenguajes Artísticos (LA)

Introducción (definición):

> El núcleo de Lenguajes Artísticos articula Objetivos de Aprendizaje que buscan promover la capacidad para expresar la imaginación y las vivencias propias, representar y recrear la realidad mediante diversas elaboraciones originales que hacen los niños y las niñas, y por otra parte, apreciar y disfrutar manifestaciones estéticas presentes en la naturaleza y la cultura. Integra a todos aquellos medios de expresión que favorecen la sensibilidad estética, la apreciación y la manifestación creativa, como son lo plástico visual, lo corporal y musical, entre otros. Los lenguajes artísticos tienen un potencial simbólico, divergente y sensible que contribuyen a explicitar los múltiples significados que tienen las experiencias. (p. 73)

> A través de la interacción con el entorno, los lenguajes artísticos se constituyen en instrumentos privilegiados para exteriorizar las vivencias emocionales, desarrollar el pensamiento creativo y disfrutar de manifestaciones culturales y artísticas. (p. 73)

> En este proceso gradual de apropiación y construcción de significados, los niños y las niñas van ampliando y enriqueciendo las posibilidades de representar su mundo interior y su relación con el entorno, lo que les permitirá mayores grados de elaboración, abstracción y simbolización de sus experiencias, sensaciones, sentimientos e ideas. (p. 73)

> El énfasis en la sensibilidad y en la apreciación estética, significa ampliar las capacidades de observación, kinestésicas, auditivas y expresivas con el propósito de que los niños y las niñas, se interesen, disfruten, reconozcan, identifiquen, describan e interpreten dentro de sus posibilidades, diferentes aspectos. (p. 73)

Orientaciones pedagógicas:

> La mirada integrada de los lenguajes artísticos supone disponer de ambientes de aprendizaje que permitan reconocer y valorar las múltiples y particulares formas de expresión de los niños y las niñas y puedan poner en juego sus capacidades creativas. Se trata de que los párvulos puedan experimentar y tomar contacto con producciones de diversos lenguajes artísticos, es decir, pintura, modelado, escultura, música, danza, teatro, entre otros. (p. 73)

> El juego, en un sentido amplio, es un tipo de actividad muy afín con los Objetivos de Aprendizaje de este núcleo, especialmente con la dimensión expresiva de los lenguajes artísticos. Por ejemplo, crear una historia simple con títeres, puede ser a la vez un juego y una ocasión de expresión teatral. Reproducir sonidos del entorno, interpretar y crear patrones rítmicos, imitar gestos y movimientos, son actividades de innegable carácter lúdico. (p. 74)

> La creatividad implica el desarrollo de ciertos procesos de pensamiento que le son muy propios, tales como: la flexibilidad, la fluidez, la originalidad y la sensibilidad. Para potenciarla, el equipo pedagógico requiere organizar experiencias para el aprendizaje que usen recursos cotidianos, simples y atractivos que provoquen sorpresa y asombro, como objetos de variadas características sensoriales (texturas, sonidos, colores y aromas), así como otras que permitan ir ampliando y diversificando el uso de recursos, tales como: juegos melódicos, fotografías, recursos digitales, videos de obras teatrales y danza, esculturas, grabaciones de piezas musicales pertenecientes a repertorios tradicionales y contemporáneos. Visitas a centros de exposición de producciones artísticas diversas, también cuentan como valiosas experiencias. Además, se deben generar oportunidades para potenciar su memoria auditiva, ampliar sus expresiones gráficas, descubrir y comentar utilizando nuevas palabras asociadas a características visuales, sonoras y de movimiento, de objetos y obras de arte. (p. 74)

> La expresión creativa a través del dibujo es una importante manifestación de la función simbólica, que involucra un proceso en el cual se aprende a observar la realidad y a representarla en una superficie. Esta elaboración se va ampliando progresivamente a medida que los párvulos van incorporando otros aspectos y dimensiones como, por ejemplo: detalles más específicos de la figura humana. Para conocer los avances de las capacidades de representación, es valioso organizar registros de la secuencia de los dibujos, a través de bitácoras personales. Esta estrategia, además de favorecer el seguimiento evaluativo, permite evidenciar en los propios párvulos, sus descubrimientos y progresos. (p. 74)

> La interiorización de las imitaciones constituye la base de las primeras imágenes mentales, por tanto, la riqueza de experiencias personales en ese ámbito es fundamental para una progresiva adquisición de la función simbólica. Por la importancia que tiene la imitación en esta etapa, es necesario asegurar la calidad de los modelos que se les ofrecen a los niños y las niñas, respecto a los gestos, el lenguaje, la expresión corporal. (p. 74)

> La organización del espacio debe ofrecer a los párvulos una estructura particular que los ayude a reconocer los diversos recursos con los que pueden contar, así como sus múltiples posibilidades para el proceso creativo. En este sentido, es relevante disponer de diferentes espacios y contenedores, cuyo propósito sea resguardar, preservar y valorar las creaciones de los niños y las niñas. (p. 74)

> A través de la colección de objetos, se agudizan las percepciones distinguiendo las diferencias de forma, sonido, color y materialidad. La acción de coleccionar, es una estrategia que permite demostrar que los objetos y también los elementos de la naturaleza pueden ser representados a través de distintas formas, todas igualmente válidas y legítimas, contribuyendo así al desarrollo de la creatividad. (p. 74)

> Por otra parte, también resulta necesario, incorporar estrategias de mediación que propicien que los párvulos puedan explorar, descubrir, experimentar sensorialmente, con recursos cotidianos, simples y atractivos que provoquen sorpresa y asombro. Progresivamente será necesario incorporar otras estrategias tales como las analogías, las preguntas divergentes, los comentarios de carácter metafóricos, ayudándolos así, a focalizar su percepción respecto de las características de los objetos que se exploran y con los que se crea. (p. 75)

Propósito general del núcleo:

> A través de Lenguajes Artísticos, se espera potenciar en las niñas y los niños, habilidades, actitudes y conocimientos para la expresión creativa de la realidad, y la adquisición de la sensibilidad y apreciación estética. De esta manera, amplían sus posibilidades de percibir, disfrutar y representar tanto su mundo interno como la relación con el entorno cultural y natural, empleando progresivamente diversos medios y recursos. (p. 75)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 76

| ID | Cita | OA |
|---|---|---|
| `LA-SC-1` | OA 1 LA | Manifestar interés por los sonidos, las texturas, los colores y la luminosidad de su entorno, respondiendo a través de diversas formas, tales como balbuceo, gestos, sonrisas, entre otros. |
| `LA-SC-2` | OA 2 LA | Producir sonidos con su voz, su cuerpo y diversos objetos sonoros, en forma espontánea o por imitación. |
| `LA-SC-3` | OA 3 LA | Imitar gestos, movimientos, sonidos de su entorno significativo, a través de diversos medios. |
| `LA-SC-4` | OA 4 LA | Manifestar sus preferencias por recursos expresivos presentes en piezas musicales, visuales, y escénicas, a través de gestos, movimientos, palabras, entre otros. |
| `LA-SC-5` | OA 5 LA | Expresar corporalmente las emociones y sensaciones que le provocan algunas piezas musicales, bailando, cantando e intentando seguir el ritmo. |
| `LA-SC-6` | OA 6 LA | Experimentar sus posibilidades de expresión plástica a través de diversos recursos, produciendo sus primeros garabateos espontáneos. |

Segundo Nivel (Medio) — p. 77

| ID | Cita | OA |
|---|---|---|
| `LA-M-1` | OA 1 LA | Manifestar interés por diversas producciones artísticas (arquitectura, modelado, piezas musicales, pintura, dibujos, títeres, obras de teatro, danzas, entre otras), describiendo algunas características. |
| `LA-M-2` | OA 2 LA | Expresar sus preferencias, sensaciones y emociones relacionadas con diferentes recursos expresivos que se encuentran en sencillas obras visuales (colorido, formas), musicales (fuente, intensidad del sonido) o escénicas (desplazamiento, vestimenta, carácter expresivo). |
| `LA-M-3` | OA 3 LA | Interpretar canciones y juegos musicales, experimentando con diversos recursos tales como, la voz, el cuerpo, instrumentos musicales y objetos. |
| `LA-M-4` | OA 4 LA | Expresar corporalmente sensaciones y emociones experimentando con mímica, juegos teatrales, rondas, bailes y danzas. |
| `LA-M-5` | OA 5 LA | Expresar emociones, ideas y experiencias por medio de la plástica experimentando con recursos pictóricos, gráficos y de modelado. |
| `LA-M-6` | OA 6 LA | Experimentar diversas posibilidades de expresión, combinando lenguajes artísticos en sus producciones. |
| `LA-M-7` | OA 7 LA | Representar a través del dibujo, diversos elementos de su entorno, incorporando figuras cerradas, trazos intencionados y primeros esbozos de la figura humana. |

Tercer Nivel (Transición) — p. 78

| ID | Cita | OA |
|---|---|---|
| `LA-T-1` | OA 1 LA | Apreciar producciones artísticas de diversos contextos (en forma directa o a través de medios tecnológicos), describiendo y comparando algunas características visuales, musicales o escénicas (desplazamiento, ritmo, carácter expresivo, colorido, formas, diseño, entre otros). |
| `LA-T-2` | OA 2 LA | Comunicar sus impresiones, emociones e ideas respecto de diversas obras de arte, producciones propias y de sus pares (artesanías, piezas musicales, obras plásticas y escénicas, entre otras). |
| `LA-T-3` | OA 3 LA | Interpretar canciones y juegos musicales, utilizando de manera integrada diversos recursos tales como, la voz, el cuerpo, instrumentos musicales y objetos. |
| `LA-T-4` | OA 4 LA | Expresar corporalmente sensaciones, emociones e ideas a partir de la improvisación de escenas dramáticas, juegos teatrales, mímica y danza. |
| `LA-T-5` | OA 5 LA | Representar plásticamente emociones, ideas, experiencias e intereses, a través de líneas, formas, colores, texturas, con recursos y soportes en plano y volumen. |
| `LA-T-6` | OA 6 LA | Experimentar diversas combinaciones de expresión plástica, corporal y musical, comunicando las razones del proceso realizado. |
| `LA-T-7` | OA 7 LA | Representar a través del dibujo, sus ideas, intereses y experiencias, incorporando detalles a las figuras humanas y a objetos de su entorno, ubicándolos en parámetros básicos de organización espacial (arriba/abajo, dentro/fuera). |

---

## Ámbito: Interacción y Comprensión del Entorno

Núcleos: Exploración del Entorno Natural (EEN), Comprensión del Entorno Sociocultural (CES) y Pensamiento Matemático (PM).

> El Ámbito de Interacción y Comprensión del Entorno, es el campo curricular que organiza los objetivos de aprendizaje referidos a la interacción con procesos y fenómenos naturales, sociales y culturales que constituyen el lugar donde ocurre la existencia humana. Los procesos de aprendizaje que aquí se intencionan, se orientan a resignificar este entorno y constituirlo como el espacio que niñas y niños construyen y se construyen en él. La adquisición progresiva de un razonamiento lógico matemático, se concibe como una herramienta valiosa para progresar en esta interacción, por cuanto los conceptos y categorías asociados a él posibilitan que el párvulo no reaccione simplemente a los estímulos de los entornos, sino que los interrogue, los relacione, los jerarquice y organice. (p. 80)

> Así, partiendo de su curiosidad natural, de su interés y de su capacidad de cuestionamiento, las habilidades, actitudes y conocimientos que aquí se orientan, pretenden que niñas y niños, puedan ampliar su campo de acción para distinguir, comprender y, progresivamente, explicar los fenómenos naturales y socioculturales desde una perspectiva cada vez más sistemática. Los Objetivos de Aprendizaje organizados en sus tres núcleos, promueven asimismo que los párvulos desarrollen actitudes de respeto y valoración, tomando progresiva conciencia de la influencia que sus acciones tienen en este entorno, en la vida de otros y en su propia vida. (p. 80)

> Así, se espera que descubran un mundo natural y social, donde los seres humanos, que son diversos, construyen las condiciones que les permiten sustentar su existencia, con resultados positivos en muchos aspectos, pero también con riesgos y consecuencias indeseadas. Asimismo, se intenciona que comprendan que, en la naturaleza, las sociedades y la cultura ocurren cambios, más lentos o más rápidos, a medida que pasa el tiempo. (p. 80)

> Este ámbito busca favorecer el desarrollo de actitudes y conocimientos que llevan a niñas y niños a, tomar conciencia progresivamente, que la existencia y desarrollo de las sociedades están intrínsecamente vinculadas con el entorno natural en el que se sitúan, ambiente en el que, a su vez, sus múltiples dimensiones se encuentran conectadas entre sí. Por ello, el enfoque de la sostenibilidad es clave, en tanto conlleva favorecer aprendizajes que permitan a niñas y niños comprender las potencialidades, oportunidades y riesgos que implica sostener la vida humana en un planeta con recursos limitados. (p. 80)

> En este ámbito, los Objetivos de Aprendizaje buscan orientar, experiencias que respondan a temas desafiantes y problemas auténticos y significativos para las niñas y los niños, que los involucren activamente en procesos de exploración e indagación; que favorezcan la búsqueda de efectos, explicaciones y evidencias, y que los lleven a dotar de sentido los procesos de representación a través de los que recrean sus búsquedas y descubrimientos. (p. 80)

### Núcleo Exploración del Entorno Natural (EEN)

Introducción (definición):

> Este núcleo hace referencia al desarrollo de habilidades, actitudes y conocimientos relacionados con el descubrimiento activo, valoración, cuidado del entorno natural, y al avance progresivo de los párvulos en un proceso de alfabetización científica inicial [n. 21]. (p. 81)

> Las niñas y los niños se sienten cada vez más partícipes del entorno natural, en tanto tienen frecuentes oportunidades de convivir con él. Así, mediante actividades de exploración espontáneas, observan, se asombran, hacen preguntas, formulan interpretaciones, sobre diversos elementos y seres vivos que encuentran, como el agua, la luz, los animales, la trayectoria seguida por el sol; y sobre fenómenos como la lluvia, los sismos, y otros. Este núcleo propicia que los párvulos, además de estas actividades espontáneas, participen en experiencias guiadas e intencionadas de exploración e indagación del entorno, mediante las cuales ellos y ellas pueden incrementar y profundizar su conocimiento del entorno natural. Así, puedan darse cuenta, por ejemplo, de la existencia de una diversidad más amplia de animales y plantas, cuyas características se relacionan con el hábitat en que se desenvuelven. (p. 81)

> A partir de experiencias guiadas relacionadas con este entorno, los párvulos avanzan en el desarrollo de sus habilidades indagatorias, como observar, preguntar, inferir, predecir, comunicar, buscando establecer relaciones entre los hechos, y explicar lo que observan a partir de los conocimientos y experiencias que poseen. En interacción con el equipo pedagógico, este los va guiando hacia explicaciones y comprensiones que progresivamente se sustentan en evidencias y en una concepción del entorno natural más informada por las ciencias. (p. 81)

> En este sentido, se busca promover intencionadamente aquellas experiencias que potencien la alfabetización científica, resguardando el derecho de los párvulos a participar del conocimiento, partiendo de sus propias vivencias. De esta manera, se aproximan progresivamente al manejo de conceptos, procedimientos e instrumentos, mediante experiencias e intercambios pedagógicos significativos que les ayuden a comprender y explicarse el entorno y sus fenómenos, de forma pertinente a edades tempranas y, en el marco de estas Bases. (p. 81)

> Este núcleo, busca ofrecer a los párvulos experiencias de aprendizaje que les resulten significativas, les conmuevan e involucren afectivamente, sentando las bases del conocimiento, aprecio, respeto y cuidado de la naturaleza y su biodiversidad, especialmente considerando que parte importante de niños y niñas viven en espacios antrópicos (con alta intervención humana). Se espera propiciar una actitud positiva hacia el entorno natural, entendiendo que sirve a múltiples propósitos de la vida de las personas y seres vivos, por lo que cobra especial relevancia que los párvulos contribuyan en sus acciones al cuidado del ambiente natural y su biodiversidad, en una perspectiva de la sostenibilidad. (p. 82)

Orientaciones pedagógicas:

> Es importante que los y las educadoras organicen diferentes experiencias educativas donde los niños y niñas puedan explorar activamente el medio, considerando un repertorio de estrategias lúdicas que incorporan la indagación como fuente de aprendizajes. La mediación pedagógica debe acompañar siempre la exploración y descubrimiento; preguntarles por sus hallazgos, dialogar en torno a sus explicaciones, reorientar concepciones erróneas, promover que ellos formulen interpretaciones, predicciones, reflexiones, y que cuestionen y reconstruyan sus propios conocimientos sobre el entorno natural, sus seres y fenómenos. La formulación de preguntas, adquiere un especial protagonismo, tanto al inicio, durante y en el cierre de las experiencias educativas. Interrogantes que les demandan buscar respuestas activamente pensadas, como describir, comparar, predecir, explicar, buscar información. (p. 82)

> No es necesario que las o los educadores organicen experiencias para seguir completa y secuencialmente el llamado método científico, sino algunos procedimientos representativos de este, como por ejemplo: la observación y registro (mediante dibujos o fotos). Las actividades a través de las cuales el equipo pedagógico promueve un pensamiento indagatorio en los párvulos, pueden expresarse en distintas situaciones y en diversos momentos, sea o no en el curso de procedimientos de carácter experimental. (p. 82)

> Explorar el entorno natural, significará algunas veces organizar ambientes de aprendizaje trayendo al aula objetos y elementos del entorno físico y natural, seleccionados con intención pedagógica. Esto implica reunir elementos naturales, materiales u objetos, generando colecciones que posibiliten ampliar sus experiencias de exploración y experimentación. En un mismo sentido, la preparación de situaciones educativas que involucren desafíos como manejar diversos instrumentos simples, realizar registros en bitácoras, comunicar a los demás sus hallazgos, fortalecerán el interés por descubrir y profundizar sobre el entorno natural. (p. 82)

> Teniendo presente que gran parte de las experiencias para el aprendizaje de este núcleo promueven acciones de trabajo colaborativo, se debe considerar la perspectiva de género en los roles y responsabilidades que asumen cada uno de los integrantes. Desde los primeros años es fundamental promover, frente a las diferentes actividades, roles y responsabilidades equitativos para las niñas y los niños. (p. 82)

> Es útil recurrir al uso de las TICs como una herramienta para ampliar el conocimiento en distintos ámbitos sobre el entorno natural, por ejemplo, software o programas específicos sobre seres vivos, fenómenos, acciones que contribuyen al desarrollo de ambientes sostenibles, cuerpos celestes, entre otros. (p. 83)

Propósito general del núcleo:

> A través de Exploración del Entorno Natural, se espera potenciar en las niñas y los niños, las habilidades, actitudes y conocimientos que les permitan comprender, apreciar y cuidar su entorno natural, potenciando su curiosidad y capacidad de asombro. De esta manera, amplían sus recursos personales favoreciendo el desarrollo de personas activas, que exploran, descubren, aprecian, respetan y se involucran afectivamente con el contexto natural en el que habitan, desarrollando el pensamiento científico. (p. 83)

> [n. 21] Por alfabetización científica se entiende un paradigma de enseñanza de las ciencias, muy difundido, que hace hincapié en que todos los ciudadanos, no solo quienes optarán en el futuro por seguir profesiones científicas, deben manejar conceptos y conocimientos fundamentales acumulados por las ciencias, así como manejar habilidades de pensamiento indagatorio y crítico que son propias de ellas. Se espera de esta formación, que ellas y ellos apliquen críticamente estos conocimientos y habilidades en la vida diaria, y asuman una postura personal frente a los usos del conocimiento científico, sus aplicaciones y sus consecuencias para las personas y el ambiente. OECD. (2006). Assessing scientific, Reading and Mathematical Literacy. A Framework for PISA 2006. El currículum nacional de la educación básica y media adhiere a este enfoque. (p. 81)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 84

| ID | Cita | OA |
|---|---|---|
| `EEN-SC-1` | OA 1 EEN | Manifestar curiosidad y asombro por algunos elementos, situaciones y fenómenos que ocurren en su entorno natural cercano, tales como: arena, lluvia, viento, entre otros. |
| `EEN-SC-2` | OA 2 EEN | Reconocer algunos elementos representativos de su entorno natural, tales como: animales, plantas, ríos, cerros, desierto. |
| `EEN-SC-3` | OA 3 EEN | Explorar su entorno, observando, manipulando y experimentando con diversos materiales de su interés, tales como: mezclar agua con tierra, recoger hojas o ramas, trasladar piedras, hacer huellas. |
| `EEN-SC-4` | OA 4 EEN | Descubrir características de animales al observarlos en forma directa, en textos y en imágenes. |
| `EEN-SC-5` | OA 5 EEN | Colaborar en actividades sencillas de cuidado de la naturaleza, tales como: regar, recoger hojas, trasladar ramitas, entre otras. |

Segundo Nivel (Medio) — p. 85

| ID | Cita | OA |
|---|---|---|
| `EEN-M-1` | OA 1 EEN | Manifestar interés y asombro por diversos elementos, situaciones y fenómenos del entorno natural, explorando, observando, preguntando, describiendo, agrupando, entre otros. |
| `EEN-M-2` | OA 2 EEN | Comunicar verbalmente características de elementos y paisajes de su entorno natural, tales como cuerpos celestes, cerros, desierto, flora; y de fenómenos como marejadas, sismos, tormentas, sequías. |
| `EEN-M-3` | OA 3 EEN | Descubrir que el sol es fuente de luz y calor para el planeta, a través de experiencias directas o TICs. |
| `EEN-M-4` | OA 4 EEN | Comunicar algunas propiedades básicas de los elementos naturales que explora, tales como: colores, texturas, tamaños, temperaturas entre otras. |
| `EEN-M-5` | OA 5 EEN | Distinguir una variedad progresivamente más amplia de animales y plantas, respecto a sus características (tamaño, color, textura y morfología), sus necesidades básicas y los lugares que habitan, al observarlos en forma directa, en libros ilustrados o en TICs. |
| `EEN-M-6` | OA 6 EEN | Colaborar en situaciones cotidianas, en acciones que contribuyen al desarrollo de ambientes sostenibles, tales como cerrar las llaves de agua, apagar aparatos eléctricos, entre otras. |
| `EEN-M-7` | OA 7 EEN | Emplear instrumentos y herramientas de observación y recolección (lupas, frascos, recipientes, botellas, cucharas, embudos, pinzas, entre otros) en la exploración del entorno natural. |
| `EEN-M-8` | OA 8 EEN | Experimentar mezclas y disoluciones con materiales cotidianos tales como: burbujas de jabón, agua salada, gelatina, describiendo los cambios observados. |
| `EEN-M-9` | OA 9 EEN | Reconocer que el aire y el agua son elementos vitales para las personas, los animales y las plantas, y que estos elementos pueden encontrarse con o sin contaminación. |

Tercer Nivel (Transición) — p. 86

| ID | Cita | OA |
|---|---|---|
| `EEN-T-1` | OA 1 EEN | Manifestar interés y asombro al ampliar información sobre cambios que ocurren en el entorno natural, a las personas, animales, plantas, lugares y cuerpos celestes, utilizando diversas fuentes y procedimientos. |
| `EEN-T-2` | OA 2 EEN | Formular conjeturas y predicciones acerca de las causas o consecuencias de fenómenos naturales que observa, a partir de sus conocimientos y experiencias previas. |
| `EEN-T-3` | OA 3 EEN | Reconocer la importancia del agua y la energía solar para la vida humana, los animales y las plantas, a partir de experiencias directas o TICs. |
| `EEN-T-4` | OA 4 EEN | Comunicar propiedades básicas de los objetos y elementos naturales que explora, tales como: transparencia/opacidad, flexibilidad/rigidez, rugosidad/lisura, relacionándolos con posibles usos. |
| `EEN-T-5` | OA 5 EEN | Explorar los cambios o efectos que se producen en los materiales al aplicarles fuerza, calor o agua. |
| `EEN-T-6` | OA 6 EEN | Establecer relaciones de semejanzas y diferencias de animales y plantas, a partir de algunas características (tamaño, color, textura y morfología), sus necesidades básicas (formas de alimentación y abrigo), y los lugares que habitan, al observarlos en forma directa, en libros ilustrados o en TICs. |
| `EEN-T-7` | OA 7 EEN | Describir semejanzas y diferencias respecto a características, necesidades básicas y cambios que ocurren en el proceso de crecimiento, en personas, animales y plantas. |
| `EEN-T-8` | OA 8 EEN | Practicar algunas acciones cotidianas, que contribuyen al cuidado de ambientes sostenibles, tales como manejo de desechos en paseos al aire libre, separación de residuos, utilizar envases o papeles, plantar flores o árboles. |
| `EEN-T-9` | OA 9 EEN | Comunicar sus observaciones, los instrumentos utilizados y los hallazgos obtenidos en experiencias de indagación en el entorno natural, mediante relatos, representaciones gráficas o fotografías. |
| `EEN-T-10` | OA 10 EEN | Formular conjeturas a partir de los cambios observados en mezclas y disoluciones, estableciendo relaciones de posible causalidad y comunicándolas a través de diferentes medios. |
| `EEN-T-11` | OA 11 EEN | Identificar las condiciones que caracterizan los ambientes saludables, tales como: aire y agua limpia, combustión natural, reciclaje, reutilización y reducción de basura, tomando conciencia progresiva de cómo estas contribuyen a su salud. |
| `EEN-T-12` | OA 12 EEN | Comprender que la acción humana puede aportar al desarrollo de ambientes sostenibles y también al deterioro de estos. |

### Núcleo Comprensión del Entorno Sociocultural (CES)

Introducción (definición):

> Este núcleo refiere al conjunto de habilidades, actitudes y conocimientos que se espera aprendan niñas y niños acerca de los grupos humanos que conforman su entorno social y cultural, sus formas de vida y organizaciones; así como también las creaciones, obras tangibles e intangibles y acontecimientos relevantes de las comunidades. Los Objetivos de Aprendizaje que se favorecen en este núcleo, promueven que los párvulos pongan en juego sus capacidades para explorar, conocer y apreciar el entorno sociocultural inmediato y más lejano, tanto desde una perspectiva espacial como temporal. (p. 88)

> En este contexto resulta fundamental que los párvulos puedan conocer acerca de sus familias y comunidades -sus rutinas, historias, anécdotas, sus gustos, sus tradiciones- descubriendo e internalizando algunas de sus costumbres, normas y valores. Así, se inician en aprendizajes relacionados con la historicidad del mundo en el que viven, a partir de lo que pueden ir conociendo del pasado, del presente y de los cambios que acontecen. Esta construcción se lleva a cabo integrando conocimientos de sucesos, acontecimientos y personajes relevantes de la historia del país y del mundo, reconociendo con ello el legado patrimonial y material que mujeres y hombres hicieron en el pasado y que impacta en la actualidad. (p. 88)

> Este núcleo también busca que niños y niñas puedan comprender que el entorno sociocultural involucra a diversos grupos humanos que desarrollan distintas actividades necesarias para la vida, tales como: producción de alimentos, vestuario, transporte, vivienda; actividades a las que se asocian múltiples materiales, artefactos, herramientas y procesos. (p. 88)

> Entre los contenidos de este núcleo, ocupan un lugar los objetos tecnológicos, entendidos de manera amplia como los utensilios, instrumentos, herramientas que se usan en el entorno, por ser productos de la cultura creados con ingenio para resolver desafíos y satisfacer necesidades que enfrentan las personas. (p. 88)

> En la perspectiva de la sostenibilidad, se apunta a favorecer el desarrollo progresivo de la conciencia sobre el impacto que tiene la acción del ser humano en el entorno que habita. Así, se incentiva en los párvulos la valoración de la diversidad humana y cultural del mundo actual, constituyéndose en un aporte a la construcción de una sociedad más inclusiva. (p. 88)

> Los Objetivos de Aprendizaje de este núcleo promueven que niños y niñas pongan en juego su potencial para explorar, conocer y apreciar el entorno sociocultural en el que se sitúan, profundizando aspectos propios de la vida en sociedad, reconociendo y dando significado a las distintas relaciones que se generan en su entorno [n. 22]. (p. 89)

Orientaciones pedagógicas:

> En torno a este núcleo se intencionan experiencias para el aprendizaje eventualmente lúdicas, que promuevan la curiosidad e interés de los párvulos por conocer personas, objetos, acontecimientos y hechos cercanos y significativos, distintas formas de organización e instituciones de su comunidad. A través de ellas, los niños y las niñas pueden desarrollar un sentido de identificación con distintos grupos: su familia, su jardín infantil, su escuela, su comunidad y otras comunidades más lejanas [n. 23]. Conocen e internalizan algunas rutinas, celebraciones, costumbres, ritos, normas y valores de su contexto, se interiorizan de las principales organizaciones e instituciones que van dando forma a la vida con otros, a la vez que descubren algunos utensilios, herramientas -creaciones tecnológicas y artísticas- que han ido enriqueciendo la vida en sociedad. (p. 89)

> Dentro de las estrategias que son fundamentales de considerar en este núcleo, se encuentran todas aquellas que buscan incrementar progresivamente sus posibilidades de visitar distintos lugares, tales como: su barrio, espacios públicos, diversas instituciones y organizaciones propias de su comunidad, pero también museos, bibliotecas, centros culturales, entre otros lugares, que permiten ir internalizando y ampliando su identidad sociocultural. (p. 89)

> En este sentido, también se deben considerar para expandir su conocimiento, el uso de fuentes orales, gráficas y diversas herramientas tecnológicas, tales como: fotografías, imágenes, videos, diarios, relatos, cuentos, artesanía, vestimentas y otros múltiples elementos y objetos culturales. A partir de estos, se busca que los párvulos construyan, amplíen y profundicen su visión del entorno. (p. 89)

> Una estrategia para obtener conocimiento y apreciar acontecimientos que constituyen y dan sentido a su comunidad, es la creación de muestras colectivas, que representan conmemoraciones, sucesos significativos, personas relevantes para la historia del país o del mundo (por ejemplo: la producción de maquetas, libros gigantes, murales, presentaciones en medios digitales, entre otros). (p. 89)

> Se debe tener presente que los niños y las niñas interactúan habitualmente con variados utensilios y objetos tecnológicos, los cuales se constituyen en una amplia fuente de aprendizaje que se puede incorporar a los diferentes espacios educativos, favoreciendo la curiosidad e interés por descubrir sus finalidades y conocerlos con mayor profundidad. De este modo, un conjunto de objetos, como teléfonos, relojes, batidoras, lámparas, pesas, entre otros, les sirven para comunicar información sencilla sobre ellos, manipularlos, distinguir su funcionamiento, destacar su utilidad y comentar sobre las necesidades que les dieron origen. (p. 90)

Propósito general del núcleo:

> A través de Comprensión del Entorno Sociocultural, se espera potenciar en los niños y las niñas, las habilidades, actitudes y conocimientos que les permitan comprender y apreciar la dimensión social y cultural de su contexto. De esta manera, amplían sus recursos personales para actuar en él y transformarlo al convivir con otros, reconociendo y respetando su diversidad. (p. 90)

> [n. 22] El Núcleo Comprensión del Entorno Sociocultural comparte con el Núcleo Convivencia y Ciudadanía contenidos relacionados con la formación ciudadana de los párvulos. Mientras en este último el énfasis apunta al reconocimiento y el respeto del otro, aprendidos en la práctica de una interacción cotidiana donde todos tienen los mismos derechos y responsabilidades, el primero, contribuye a la ciudadanía ampliando el conocimiento y descubrimiento de los otros, más allá del entorno inmediato, en contextos nacionales e internacionales, a quienes se hace extensivo el respeto y la tolerancia y el enfoque de derechos. (p. 89)

> [n. 23] Una fuente, complementaria a la Ley Nº 20.911, de lo que en estas Bases se entiende por ciudadanía, es UNESCO (2016). Esta institución sostiene que la paz, el bienestar y la sostenibilidad son bienes globales que necesitan "ciudadanos del mundo" -es decir, una identidad colectiva ampliada a otros más lejanos-, socialmente conectados, éticos y comprometidos. Por supuesto, estas BCEP adaptan tales requerimientos formativos a la primera infancia. UNESCO (2016). Educación para la Ciudadanía Mundial. Preparar a los educandos para los retos del siglo XXI. Paris: UNESCO. (p. 89)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 91

| ID | Cita | OA |
|---|---|---|
| `CES-SC-1` | OA 1 CES | Imitar gestos y acciones que realizan personas de su entorno cercano. |
| `CES-SC-2` | OA 2 CES | Identificar algunas actividades habituales que se realizan en su vida cotidiana, tales como: preparación de alimentos, rutinas antes de dormir, entre otras. |
| `CES-SC-3` | OA 3 CES | Manifestar interés por canciones, juegos y bailes que forman parte de su cotidianeidad. |
| `CES-SC-4` | OA 4 CES | Explorar utensilios domésticos y objetos tecnológicos que forman parte de su vida cotidiana, tales como: pocillos, envases de botellas, escobas, cucharas, teléfonos, entre otros, utilizándolos progresivamente en situaciones cotidianas y juegos. |
| `CES-SC-5` | OA 5 CES | Reconocer objetos y personas, asociándolos a ciertos lugares, tales como: educadora/ técnico y jardín infantil; mamá/papá y casa; cama y dormir, recinto de cocina y comida, de su entorno sociocultural. |

Segundo Nivel (Medio) — p. 92

| ID | Cita | OA |
|---|---|---|
| `CES-M-1` | OA 1 CES | Describir actividades habituales de su comunidad, como ir de compras, jugar en la plaza, viajar en bus, entre otras, señalando su participación en ellas. |
| `CES-M-2` | OA 2 CES | Describir características de las formas de vida de su comunidad (viviendas, paisajes, costumbres), a través de canciones, juegos, relatos y fotos familiares, entre otras. |
| `CES-M-3` | OA 3 CES | Seleccionar utensilios domésticos y objetos tecnológicos que les permiten resolver problemas en contextos sociales auténticos. |
| `CES-M-4` | OA 4 CES | Reconocer sucesos significativos de su historia personal y familiar, en diversas situaciones, tales como: conversaciones familiares, relatos de un agente comunitario, visitas a lugares, observación de fotografías, entre otros. |
| `CES-M-5` | OA 5 CES | Identificar instituciones significativas de su entorno, describiendo actividades y rutinas representativas que en ellas se realizan. |
| `CES-M-6` | OA 6 CES | Identificar algunas normas de protección y seguridad de su entorno cotidiano referidas a alimentación, tránsito y sismos, y otras pertinentes a su contexto geográfico. |
| `CES-M-7` | OA 7 CES | Distinguir en paisajes de su localidad, elementos naturales (bosque, cerros, ríos), y culturales (caminos, edificios, puentes). |

Tercer Nivel (Transición) — p. 93

| ID | Cita | OA |
|---|---|---|
| `CES-T-1` | OA 1 CES | Comprender los roles que desarrollan miembros de su familia y de su comunidad, y su aporte para el bienestar común. |
| `CES-T-2` | OA 2 CES | Apreciar diversas formas de vida de comunidades, del país y del mundo, en el pasado y en el presente, tales como: viviendas, paisajes, alimentación, costumbres, identificando mediante diversas fuentes de documentación gráfica y audiovisual, sus características relevantes. |
| `CES-T-3` | OA 3 CES | Comparar características de diseño, funcionamiento, utilidad, precaución de uso e impacto en el entorno, de diferentes objetos tecnológicos. |
| `CES-T-4` | OA 4 CES | Formular interpretaciones respecto de las necesidades y situaciones que dieron origen a creaciones e inventos, tales como: refrigerador, radio, avión, naves espaciales, cámara fotográfica, entre otros. |
| `CES-T-5` | OA 5 CES | Comunicar algunos relatos sociales sobre hechos significativos del pasado de su comunidad y país, apoyándose en recursos tales como: fotografías, videos, utensilios u objetos representativos. |
| `CES-T-6` | OA 6 CES | Reconocer diversas acciones para el cuidado del patrimonio cultural material (construcciones, obras de carácter arqueológico, lugares) e inmaterial (tradiciones, celebraciones), de su comunidad local. |
| `CES-T-7` | OA 7 CES | Reconocer la importancia del servicio que prestan instituciones, organizaciones, lugares y obras de interés patrimonial, tales como: escuelas, transporte público, empresas, iglesias, museos, bibliotecas, entre otros. |
| `CES-T-8` | OA 8 CES | Conocer sobre la vida de algunas mujeres y hombres, que han realizado en el pasado y en el presente, aportes diversos en su comunidad, país, y el mundo, a través de relatos, o con apoyo de TICs. |
| `CES-T-9` | OA 9 CES | Ampliar sus estrategias de indagación utilizando diversas fuentes, instrumentos y tecnologías de la información y comunicación, que le permitan expandir su entorno. |
| `CES-T-10` | OA 10 CES | Comprender normas de protección y seguridad referidas a tránsito, incendios, inundaciones, sismos, y otras pertinentes a su contexto geográfico. |
| `CES-T-11` | OA 11 CES | Identificar lugares de su entorno a través de su representación geográfica, tales como: maquetas, fotografías aéreas, dibujos y planos. |

### Núcleo Pensamiento Matemático (PM)

Introducción (definición):

> Este núcleo refiere a los diferentes procesos a través de los cuales los niños y niñas tratan de interpretar y explicar los diversos elementos y situaciones del entorno, tales como ubicación en el espacio-tiempo, relaciones de orden, comparación, clasificación, seriación, identificación de patrones. A esto se agrega la construcción de la noción de número y el uso inicial de la función ordenadora y cuantificadora del mismo en un ámbito numérico pertinente a los párvulos. (p. 94)

> Los niños y niñas comienzan a desarrollar actividades y conceptos matemáticos desde muy temprano, con referencia en acciones o percepciones de situaciones o experiencias de la vida cotidiana, lo que no implica necesariamente una matemática formal, de abstracción, modelación y lenguaje simbólico. (p. 94)

> Al actuar en el entorno y sobre los objetos, van conformando nociones básicas sobre sus características y sobre las relaciones existentes entre ellos, las que conllevan propiedades pre numéricas y numéricas. Mediante el desarrollo del lenguaje verbal y de un vocabulario cada vez más amplio, el párvulo puede pensar con conceptos que, teniendo sus raíces en la vida cotidiana práctica, alcanzan más generalidad y vinculación con otros conceptos. Todo este conocimiento, actúa como base para la comprensión de las matemáticas que posteriormente en su trayectoria educativa profundizarán en la educación básica. (p. 94)

> El pensamiento matemático es una herramienta cuya adquisición progresiva, lleva a niños y niñas a ampliar su mundo, ayudando a comprender la realidad y a desenvolverse en la vida cotidiana. Posibilita el intercambio de nuevos significados con otras personas, favorece la resolución de situaciones significativas de manera flexible y les permite enfrentar diversos desafíos imaginando nuevas soluciones. Comunicar sus experiencias, implica hacer uso de ideas, palabras, símbolos y signos, muchos de los cuales expresan relaciones lógicas, de cuantificación –matemáticas- que hacen comprensible, para sí y para otros, el contexto en el que se desenvuelven. (p. 94)

Orientaciones pedagógicas:

> Los Objetivos de Aprendizaje de este núcleo se desarrollan a través de la exploración activa de situaciones y objetos del entorno, y de una interacción claramente intencionada con el equipo pedagógico. Para ello, se requiere organizar una serie de actividades específicas, con materiales concretos, que facilite la adquisición de determinados conceptos. En virtud de lo anterior, es esencial que el aprendizaje en este núcleo se despliegue a partir de acciones y situaciones cotidianas, y materiales factibles de manipular para los diversos desafíos, propiciando además la resolución de problemas significativos y auténticos. Para el o la educadora esto conlleva una práctica pedagógica alejada de situaciones descontextualizadas y ficticias, y cercana a las situaciones reales que el párvulo enfrenta cotidianamente. Así, en este núcleo se optó por formular Objetivos de Aprendizaje que evitan, en lo posible, incorporar la fórmula "resolver problemas", para dar a entender que todo conocimiento matemático en este núcleo se construye en tanto el niño y la niña resuelve problemas auténticos que las situaciones cotidianas le presentan. (pp. 94–95)

> Al orientarlos a visualizar que los problemas prácticos cotidianos pueden tener varias soluciones y muchas maneras diferentes de llegar a ellas, los párvulos reconocen que los errores, son oportunidades y desafíos que les permiten aprender. En esa dirección, los procesos de mediación deben considerar, entre otros, diversos tipos de preguntas para ampliar el conocimiento y las estrategias de indagación. (p. 95)

> Es relevante, que estas habilidades se desarrollen en situaciones lúdicas y cotidianas, significativas y auténticas que los involucren en su corporalidad, afectividad y cognición. (p. 95)

> Como se mencionó anteriormente, no se trata aun de la adquisición de un lenguaje formal disciplinario; se trata de construir los significados intrínsecos de orden matemático, de acuerdo con procedimientos apropiados para ello en este nivel. Primero, manipulando una variedad de materiales concretos; luego, representando pictóricamente lo concreto con íconos e imágenes, para posteriormente aproximarse a su representación en el lenguaje simbólico de la matemática, propio de los siguientes niveles educativos [n. 24]. A través de estos procesos, niños y niñas son protagonistas de sus aprendizajes, buscando y probando distintas respuestas, de acuerdo a sus características, necesidades, intereses, ritmos y formas de aprender. (p. 95)

> Es preciso considerar dentro de las estrategias, que el entorno inmediato, ofrece múltiples alternativas para aproximar naturalmente a la niña y el niño a las primeras nociones matemáticas. A través de objetos y elementos de la naturaleza, pueden descubrir atributos, comparar, establecer relaciones de semejanza y diferencia al clasificar, como también descubrir figuras 3D. (p. 95)

> Aquellos juegos grupales que implican resolver desafíos en forma conjunta, son una estrategia que genera gran interés en los niños y las niñas, especialmente cuando conjugan procedimientos como: observación, búsqueda de información, uso de diferentes materiales, ensayos, registros y exposiciones grupales. (p. 95)

Propósito general del núcleo:

> A través de Pensamiento Matemático, se espera potenciar en los niños y las niñas, las habilidades, actitudes y conocimientos relacionados con el pensar lógico y los números, que les posibiliten comunicar y resolver situaciones prácticas cotidianas. De esta manera, amplían sus recursos para comprender y actuar en el entorno, intercambiando significados con otras personas. (p. 96)

> [n. 24] En la Educación Básica, los Objetivos de Aprendizaje de Matemática se abordan permanentemente mediante una actividad pedagógica que progresa de lo concreto a lo pictórico (icónico) y a lo simbólico (abstracto). MINEDUC. (2012). Bases Curriculares para la Educación Básica. DECRETO Nº439/2012. En este Núcleo se propone un método pedagógico similar. (p. 95)

Objetivos de Aprendizaje:

Primer Nivel (Sala Cuna) — p. 97

| ID | Cita | OA |
|---|---|---|
| `PM-SC-1` | OA 1 PM | Adquirir la noción de permanencia de objetos y de personas significativas, mediante juegos con diversos objetos de uso cotidiano. |
| `PM-SC-2` | OA 2 PM | Explorar a través de sus experiencias sensoriales y motrices, atributos de los objetos tales como: tamaño, textura y dureza. |
| `PM-SC-3` | OA 3 PM | Experimentar con los objetos, resolviendo situaciones concretas, tales como: alcanzar objetos, apretar botones en aparatos sonoros, sacar juguetes de contenedores, juntar objetos, entre otros. |
| `PM-SC-4` | OA 4 PM | Utilizar en situaciones lúdicas, nociones de ubicación en relación con su propio cuerpo tales como: dentro/fuera; encima/debajo. |
| `PM-SC-5` | OA 5 PM | Orientarse temporalmente en situaciones cotidianas, siguiendo secuencias breves tales como: antes/después. |
| `PM-SC-6` | OA 6 PM | Emplear cuantificadores (más/menos, mucho/poco), en situaciones cotidianas. |

Segundo Nivel (Medio) — p. 98

| ID | Cita | OA |
|---|---|---|
| `PM-M-1` | OA 1 PM | Reproducir patrones sonoros, visuales, gestuales, corporales u otros, de dos o tres elementos. |
| `PM-M-2` | OA 2 PM | Experimentar con diversos objetos, estableciendo relaciones al clasificar por dos atributos a la vez (forma, color, entre otros) y seriar por altura o longitud. |
| `PM-M-3` | OA 3 PM | Describir la posición de objetos y personas, respecto de un punto u objeto de referencia, empleando conceptos de ubicación y distancia tales como: dentro/fuera; encima/debajo; cerca /lejos. |
| `PM-M-4` | OA 4 PM | Orientarse temporalmente en situaciones cotidianas, mediante la utilización progresiva de algunas nociones y relaciones de secuencias, tales como: antes/después, día/noche, hoy/mañana. |
| `PM-M-5` | OA 5 PM | Emplear cuantificadores, tales como: más/menos, mucho/poco, todo/ninguno, al comparar cantidades de objetos en situaciones cotidianas. |
| `PM-M-6` | OA 6 PM | Emplear progresivamente los números, para contar, identificar, cuantificar y comparar cantidades, hasta el 10 e indicar orden o posición de algunos elementos en situaciones cotidianas o juegos. |
| `PM-M-7` | OA 7 PM | Representar progresivamente, números y cantidades en forma concreta y pictórica hasta el 10. |
| `PM-M-8` | OA 8 PM | Resolver progresivamente problemas simples, de manera concreta y pictórica, agregando o quitando hasta 5 elementos. |
| `PM-M-9` | OA 9 PM | Descubrir atributos de figuras 3D, mediante la exploración de objetos presentes en su entorno. |
| `PM-M-10` | OA 10 PM | Identificar algunas acciones que se llevaron a cabo para resolver problemas. |

Tercer Nivel (Transición) — p. 99

| ID | Cita | OA |
|---|---|---|
| `PM-T-1` | OA 1 PM | Crear patrones sonoros, visuales, gestuales, corporales u otros, de dos o tres elementos. |
| `PM-T-2` | OA 2 PM | Experimentar con diversos objetos estableciendo relaciones al clasificar por dos o tres atributos a la vez (forma, color, tamaño, función, masa, materialidad, entre otros) y seriar por altura, ancho, longitud o capacidad para contener. |
| `PM-T-3` | OA 3 PM | Comunicar la posición de objetos y personas respecto de un punto u objeto de referencia, empleando conceptos de ubicación (dentro/fuera; encima/debajo/entre; al frente de/detrás de); distancia (cerca/lejos) y dirección (adelante/atrás/hacia el lado), en situaciones lúdicas. |
| `PM-T-4` | OA 4 PM | Emplear cuantificadores, tales como: “más que”, “menos que”, “igual que”, al comparar cantidades de objetos en situaciones cotidianas. |
| `PM-T-5` | OA 5 PM | Orientarse temporalmente en situaciones cotidianas, empleando nociones y relaciones de secuencia (antes/ahora/después/al mismo tiempo, día/noche), frecuencia (siempre/a veces/ nunca) y duración (larga/corta). |
| `PM-T-6` | OA 6 PM | Emplear los números, para contar, identificar, cuantificar y comparar cantidades hasta el 20 e indicar orden o posición de algunos elementos en situaciones cotidianas o juegos. |
| `PM-T-7` | OA 7 PM | Representar números y cantidades hasta el 10, en forma concreta, pictórica y simbólica. |
| `PM-T-8` | OA 8 PM | Resolver problemas simples de manera concreta y pictórica agregando o quitando hasta 10 elementos, comunicando las acciones llevadas a cabo. |
| `PM-T-9` | OA 9 PM | Representar objetos desde arriba, del lado, abajo, a través de dibujos, fotografías o TICs, formulando conjeturas frente a sus descubrimientos. |
| `PM-T-10` | OA 10 PM | Identificar atributos de figuras 2D y 3D, tales como: forma, cantidad de lados, vértices, caras, que observa en forma directa o a través de TICs. |
| `PM-T-11` | OA 11 PM | Emplear medidas no estandarizadas, para determinar longitud de objetos, registrando datos, en diversas situaciones lúdicas o actividades cotidianas. |
| `PM-T-12` | OA 12 PM | Comunicar el proceso desarrollado en la resolución de problemas concretos, identificando la pregunta, acciones y posibles respuestas. |

Nota sobre las "orientaciones o notas que acompañan a los OA": en las Bases Curriculares los OA se presentan como listas numeradas por nivel, sin notas al pie por OA individual. Las orientaciones son por núcleo (secciones "Orientaciones pedagógicas", resumidas arriba). Las conductas observables por OA (NT1/NT2) no están aquí: están en el Programa Pedagógico de Transición (ver `hallazgos-programa-pedagogico-transicion.md` y `datos/curriculo_transicion.json`).

---

## Capítulo 3 — Contextos para el aprendizaje

> Este capítulo describe los principales contextos de prácticas formativas que ocurren en los establecimientos de Educación Parvularia; proponiendo principios y orientaciones para llevarlas a cabo. En el marco de un currículo con foco en el aprendizaje de los párvulos, los contextos representan la organización coherente de todos aquellos factores que intervienen en la acción pedagógica, para que la implementación de estas Bases Curriculares se desarrolle en coherencia con lo delineado en sus fundamentos y en los Objetivos de Aprendizaje. Es decir, de acuerdo al reconocimiento de niñas y niños sujetos de derechos, diferentes, insertos en ambientes de aprendizaje inclusivos, que disfrutan el proceso educativo, que participan de éste como protagonistas, y construyen progresivamente su propia identidad y ciudadanía. (p. 102)

> Los contextos para el aprendizaje propuestos son: Planificación y Evaluación para el aprendizaje. Ambientes de Aprendizaje. Familia y Comunidad Educativa. (p. 102)

> Es importante considerar que los procesos de aprendizaje y desarrollo integral son de naturaleza interactiva, que no dependen sólo de las potencialidades y características, necesidades e intereses de las niñas y los niños, sino que también de las oportunidades de aprendizaje que brindan y se generan en estos contextos. (p. 102)

> Estas orientaciones están planteadas en términos generales, para ser implementadas y enriquecidas flexiblemente por las o los educadores, en función del Proyecto Educativo Institucional que se desarrolla en cada comunidad educativa. (p. 102)

### Contexto Planificación y Evaluación para el Aprendizaje

> Este apartado se enfoca en la planificación de las oportunidades para el aprendizaje de las niñas y los niños, y en la evaluación del avance que los párvulos evidencian respecto de los objetivos intencionados. (p. 103)

> La planificación y la evaluación son aspectos constitutivos de todo proceso educativo. Se planifica y se evalúan los diversos componentes de este proceso y en distintos niveles, tales como los Objetivos de Aprendizaje, los ambientes de aprendizaje, la participación y el trabajo colaborativo con la familia, los planes de mejoramiento de la institución, entre otros. Sin embargo, este primer contexto se refiere principalmente a la planificación y evaluación para el aprendizaje, actividades ambas que encuentran en estas BCEP su referente fundamental. (p. 103)

> La planificación y la evaluación se enriquecen mutuamente, potenciando las oportunidades reales de aprendizaje y las prácticas docentes. La planificación, por una parte, ordena, orienta y estructura el trabajo educativo en tiempos determinados, pero a la vez es flexible y sensible a la evaluación permanente de cómo las niñas y los niños van reaccionando a la enseñanza realizada y de lo que van aprendiendo. (p. 103)

> La evaluación, por su parte, es la práctica mediante la cual el equipo pedagógico recoge y analiza información en forma sistemática de los procesos y logros de los párvulos, en situaciones auténticas y funcionales, y retroalimenta a los involucrados. En cuanto al párvulo, la retroalimentación de sus avances y logros, hecha cuidadosamente, es una ocasión de fortalecer los aprendizajes construidos. Para el equipo pedagógico, la información obtenida podría eventualmente dar lugar al rediseño del proceso educativo para el próximo período. Entendida así, la evaluación es una instancia más de aprendizaje, formadora en sí misma. (p. 103)

> En este marco, se requiere de una interrelación permanente y coherente entre la planificación y la evaluación, que propicie la toma de decisiones compartidas entre docentes y otros integrantes del equipo pedagógico, y la niña y el niño. El diálogo entre planificación y evaluación se constituye en un contexto que da soporte permanente a todo el proceso educativo y a los esfuerzos por mejorarlo continuamente. (p. 103)

> Respecto de los y las docentes, tienen el rol de liderar el proceso de enseñanza y aprendizaje, planificando, implementando y evaluando, mediante el análisis sistemático de las evidencias de aprendizaje provenientes de diversas fuentes. Tanto la planificación como la evaluación son herramientas de apoyo, las cuales se benefician de la reflexión con otros, por lo que es relevante llevarlas a cabo colectivamente. (p. 103)

Consideraciones para la planificación de los aprendizajes:

> La tarea de planificar implica cumplir con lo declarado y concretar lo que se pretende alcanzar. Para ello, toda planificación efectiva debe considerar un plazo en el que se espera se logren los Objetivos de Aprendizaje. Este plazo dependerá de la complejidad de los OA, del tiempo que el currículum dispone para su logro y de la estimación de la cantidad y duración de experiencias requeridas para su enseñanza y aprendizaje. De acuerdo con ello, se reconocen a lo menos dos tipos: largo/mediano y corto plazo. (p. 104)

Planificación de largo y mediano plazo:

> Este tipo de planificación constituye una actividad preparatoria de la enseñanza y corresponde a una selección, secuenciación y ordenamiento general de los objetivos de aprendizaje a intencionar o promover durante la práctica pedagógica, asegurando la cobertura completa de los aprendizajes prescritos en el currículum para un nivel determinado. Habitualmente, el horizonte temporal de la planificación de largo o mediano plazo es el año escolar y/o sus subdivisiones semestrales. (p. 104)

> A continuación, se presentan algunas consideraciones importantes a tener en cuenta para desarrollar la planificación de largo y mediano plazo:
>
> Planificar lo que es relevante que los párvulos aprendan. Los equipos pedagógicos disponen de estas BCEP que ya realizaron esta reflexión, la cual se manifiesta en los fundamentos, los ámbitos, núcleos y OA. De modo que el norte de la planificación ha de encontrarse siempre en la implementación equilibrada de los ocho núcleos y de sus correspondientes Objetivos de Aprendizaje.
>
> Revisar y jerarquizar los OA del currículum, del nivel que se está planificando, para determinar cuáles de ellos serían más apropiados para el primer año de implementación y cuáles para el segundo año, en función de su complejidad y del conocimiento teórico de las trayectorias de desarrollo infantil.
>
> Contar con un conocimiento evaluativo inicial lo más acabado posible de las características, necesidades e intereses de las niñas y los niños, enriquecido por la información proporcionada por la familia y los informes evaluativos anteriores. Ello debe darse en función de un profundo análisis de la información que se va recopilando en relación con los objetivos propuestos. También se debe disponer de una información acabada de la familia y la comunidad: de sus costumbres, valores, compromisos, etc., de tal modo de conocer sus fortalezas en relación con la formación de los párvulos, así como sus desafíos.
>
> Priorizar y distribuir los Objetivos de Aprendizaje, en el marco temporal definido (anual, semestral, trimestral), asignando plazos a cada uno, considerando el tiempo diferencial que tomaría su aprendizaje. Todo esto, de acuerdo con las características, necesidades y aprendizajes previos de los integrantes del grupo/curso de párvulos. Según lo anterior, pueden planificarse Objetivos de Aprendizaje distintos para niños o niñas que así lo ameritan en el grupo. Esto implicaría, en algunos casos, seleccionar OA de los niveles adyacentes.
>
> Seleccionar o proponer experiencias para el aprendizaje bajo criterios que consideren el protagonismo de niñas y niños, sus intereses y el juego como herramienta esencial de aprendizaje. Asimismo, debe considerarse que no alteren la unicidad de los OA de estas Bases Curriculares, esto es, que otorgue importancia tanto a las habilidades, como a las actitudes y conocimientos implicados en ellos.
>
> Integrar a la planificación una propuesta de recursos que se usarán para el desarrollo de los OA. También, los procedimientos generales de evaluación a utilizar, en concordancia a los objetivos de aprendizaje planificados.
>
> Considerar durante el proceso de diseño e implementación de la planificación, las necesarias adaptaciones que puedan surgir para responder con pertinencia y oportunidad a los requerimientos de la comunidad educativa y, en especial, de las niñas y los niños quienes, por sus características e intereses, presentan avances en el aprendizaje de manera cambiante.
>
> Integrar en la planificación, momentos o iniciativas propias de la comunidad local o nacional, como parte de las experiencias, puesto que son una oportunidad para establecer vínculos cercanos y sólidos con personas del entorno o que pueden ser muy aportadoras para el desarrollo de la pertenencia y construcción de la identidad de las niñas y los niños.
>
> Utilizar formatos de planificación que faciliten la labor. Lo importante es que se pueda explicitar de manera anticipada, ordenada y coherente la intención educativa, que tiene su referente en las Bases Curriculares. Asimismo, es necesario disponer de formas de planificaciones que permitan flexibilidad y adaptabilidad a las diferentes situaciones que se van presentando. (pp. 104–105)

Planificación de corto plazo:

> Esta práctica constituye una especificación en el corto plazo, de lo que se ha propuesto en la planificación de largo y mediano plazo. Se refiere al diseño particular de las experiencias de aprendizaje que se desarrollarán en la jornada diaria o en la semana. Su aporte principal radica en organizar de forma coherente la práctica pedagógica, con el fin de que los ambientes de aprendizaje actúen en la dirección intencionada por determinados OA. Por lo tanto, se tratará siempre de una formulación anticipatoria de aquello que se pretende realizar en el aula o donde se desee situar la acción formadora. (p. 105)

> Este tipo de planificación está sujeto a cambios en el momento de la jornada, dependiendo de las reacciones de los párvulos frente a la propuesta inicial; si no se está logrando lo esperado, es útil modificar o reorientar la experiencia de aprendizaje. (p. 106)

> La planificación de corto plazo puede y suele variar en relación a los estilos y orientaciones metodológicas de los equipos pedagógicos. Existen diversas formas para organizar coherentemente las experiencias y oportunidades de aprendizajes, como, por ejemplo, proyectos, centro de interés, unidades, entre otras. (p. 106)

> Las experiencias de aprendizaje que se planifiquen deben integrar el desarrollo de los diversos procesos que se requieren para la construcción de las habilidades, actitudes y conocimientos implicados en los OA, con especial énfasis en la exploración, la problematización y la transferencia a realidades cotidianas. (p. 106)

> A continuación, se presentan algunas consideraciones para planificar a corto plazo:
>
> En los niveles de Sala Cuna y Medio, las experiencias para el aprendizaje ofrecidas deben poseer una duración más breve, debiendo estar el equipo pedagógico atento a las variaciones de interés y necesidades de las niñas y los niños. En estos niveles, se ocupa mucho tiempo en la exploración de sí y progresivamente, del entorno más cercano a través de interacciones eminentemente individuales. Considérese, por ejemplo, el desarrollo del juego heurístico en este ciclo; la niña y el niño inmediatamente después de encontrarse con los recursos de apoyo, los explora y descubre, prueba sus características, efectos y usos. Es importante que el tiempo dedicado a este tipo de experiencias, y al juego libre, sea más prolongado que las experiencias más enmarcadas.
>
> Mientras más pequeños los párvulos, las planificaciones y la evaluación deben tener un carácter más individual, integral y flexible. Se trata de acompañarlos intencionadamente a lograr el máximo en su trayectoria potencial de desarrollo y aprendizaje. Para ello, el o la educadora debe conocer a cabalidad el desarrollo integral de la niña y el niño, sus recursos cognitivos, afectivos, sociales y emocionales y, muy especialmente, los modos de activar en cada uno de ellos los aprendizajes que van a alcanzar su plena expresión más adelante.
>
> En niveles mayores, las niñas y los niños cuentan con una mayor persistencia en relación a los tiempos de concentración, lo que propicia el diseño de experiencias para el aprendizaje por períodos más prolongados, especialmente en el nivel de transición.
>
> En este nivel se pueden organizar estas oportunidades con un progresivo carácter colaborativo, de manera de propiciar la valoración de procesos educativos en que los párvulos aprenden de sí y con otros.
>
> Es apropiado ampliar la participación y la autonomía de las niñas y los niños, planificando ambientes en que sean ellos quienes deliberadamente definan y desarrollen libremente una variedad de oportunidades integrales mediadas por adultos. Por ejemplo, en un primer momento de un juego de zonas, niñas y niños comunican las actividades que pretenden hacer en la zona escogida, para luego dar paso al momento de desarrollo del juego, y al final del período, a un momento de puesta en común respecto de su proceso de aprendizaje.
>
> Seleccionar y producir recursos educativos -de tipo tangible o intangible-, significativos y pertinentes a los OA, es importante para propiciar y acoger interacciones pedagógicas de calidad, que potencien el descubrimiento de nuevas posibilidades de uso. Es relevante considerar la usabilidad, para que las niñas y los niños puedan interactuar con los recursos educativos de la forma más accesible, intuitiva y desafiante posible.
>
> Resguardar una alta frecuencia de experiencias en grupo pequeño y de interacciones pedagógicas uno a uno, entre adulto y párvulo, y niños y niñas. Esto es fundamental para ofrecer mayor calidad en el proceso educativo. Esta orientación convoca a estar atentos a las oportunidades de interacción que ofrecen los diferentes tipos de agrupaciones que se pueden conformar: homogéneas, heterogéneas o mixtas, según criterios tradicionales de edad y género, u otros, como intereses diversos, lazos afectivos, niveles de aprendizaje y aquellos que los párvulos propongan. Es importante que la planificación favorezca los vínculos afectivos, el respeto y la valoración de los otros, y progresivamente se vayan propiciando las relaciones de cooperación, el aprendizaje entre pares y el sentido de pertenencia al grupo.
>
> Es conveniente considerar la participación de familiares y adultos significativos en las actividades que se planifiquen, así como la participación de la comunidad, por ejemplo, en lectura o relato de cuentos, dramatización de historias cotidianas, expresión artística de canto o baile.
>
> En relación a los distintos períodos de la jornada diaria se considera que aquellos momentos destinados a la alimentación, a la higiene y al descanso también tienen propósitos formativos relevantes, constituyendo un escenario propicio para el desarrollo de diversos OA. Por lo tanto, es necesario resguardar su sentido pedagógico, por ejemplo, que los períodos constantes - tales como encuentro y despedida, alimentación, juego libre - potencien hábitos de autocuidado, habilidades sociales, lenguaje, creatividad, entre otros.
>
> Las experiencias que se diseñen deben poseer la flexibilidad para realizar las adecuaciones necesarias, a los elementos del currículum o bien de acceso a este, para responder a los párvulos que lo necesiten [n. 25]. (pp. 106–107)

Planificación de los Objetivos de Aprendizaje Transversales:

> Estas Bases Curriculares han definido como transversales a los tres núcleos del Ámbito Desarrollo Personal y Social y, por consiguiente, a todos sus OA (en los tres niveles educativos). Esta definición tiene consecuencias directas para la planificación.
>
> Los OA Transversales deben estar presentes en forma permanente en la planificación de largo, mediano y corto plazo.
>
> En el plazo de dos años que dura cada nivel, se espera que estos OA hayan sido seleccionados en la planificación e implementados sistemáticamente en la práctica pedagógica (así como también se espera que lo hayan sido todos los OA del resto de los núcleos no definidos como transversales).
>
> En la planificación de corto plazo se debe escoger para cada tipo de planificación (proyecto, experiencia variable, entre otros), alguno o algunos de los OA transversales, acompañados de otro u otros OA de los núcleos no transversales, guardando coherencia y sinergia entre ellos.
>
> También es posible que, en la planificación de algún período, día o semana, se seleccionen solo algunos OA transversales, sin acompañarlos de OA no transversales; con la precaución de que, en el largo plazo, todos los OA sean seleccionados. (p. 108)

Planificación del juego:

> Todo juego, en tanto herramienta pedagógica privilegiada para el aprendizaje en los párvulos, requiere la consideración y la intervención de las o los educadores, pero en diferentes modos y grados, según el tipo de juego de que se trate, y sus ventajas formativas.
>
> Para efectos de la planificación, es útil distinguir entre actividades lúdicas y juegos. Por ejemplo, salir al patio a observar las diferentes clases de seres vivos, es una actividad lúdica que aporta al logro de un OA de Exploración del Entorno Natural. Transportar en parejas balones, sorteando obstáculos, es una actividad lúdica, apropiada para un OA de Corporalidad y Movimiento.
>
> En este sentido, cualquier actividad de aprendizaje puede y debe ser lúdica, si con esto queremos decir que debe ser entretenida, motivante, con un enmarcamiento flexible, placentera. El rol de la o el educador en su planificación es fundamental. Siguiendo las orientaciones de planificación de este capítulo, en función del OA seleccionado, debe definir, diseñar y llevar a cabo las actividades (lúdicas) de aprendizaje que propondrá a los párvulos para su logro. La iniciativa es suya. (p. 108)

> El juego en sentido estricto difiere de la actividad lúdica en que tiene una estructura creada espontáneamente por los propios niños y niñas, y una poderosa motivación intrínseca. También son entretenidos, motivantes y placenteros. Los juegos así entendidos, son muy valiosos, por cuanto responden plena y singularmente a sus motivaciones internas y requerimientos de desarrollo. El juego de ejercicio sensorio motor, en los que niños y niñas en forma individual utilizan todos los sentidos y los movimientos, es frecuente desde los primeros meses, pero no es exclusivo del nivel sala cuna. Ocurren espontáneamente y la iniciativa es de ellos y ellas, pero necesitan que el o la educadora esté presente aportando confianza y seguridad, sin intervenir directamente en la actividad. La planificación en este caso, se circunscribe a la habilitación de escenarios y momentos adecuados para que surjan. Más adelante, toman la forma de actividades motrices, donde correr, saltar, empujar y otros movimientos intervienen en otros juegos o actividades lúdicas, ejercitando sus nuevas destrezas corporales y/o liberando energía y tensiones. El núcleo Corporalidad y Movimiento, en particular, se puede beneficiar mucho de este tipo de juego. Otro tipo de juego, más propio del nivel de transición, es el de reglas, donde la estructura básica es grupal y consensual. El grupo determina la actividad a realizar, la cual se organiza en torno a unas reglas voluntariamente aceptadas. La naturaleza de las reglas es variable, pueden emerger en el momento o preexistir. Como el anterior, ocurre espontáneamente y la iniciativa es de los niños y las niñas. La planificación, se circunscribe a la habilitación de escenarios y momentos adecuados, no al contenido de los juegos. El núcleo Convivencia y Ciudadanía requeriría preferentemente, de este tipo de juego, así como el de Identidad y Autonomía. A partir de los dos años aproximadamente, es frecuente el juego simbólico, en el que los niños y las niñas crean espontáneamente situaciones con su imaginación y a menudo dan un nuevo significado a los objetos y situaciones reales. La situación imaginaria que crean no es cualquiera; a través de estos juegos actúan sus necesidades, motivos profundos, aspiraciones afectivas. En este tipo de juego los párvulos ensayan comportamientos que aún no son capaces de hacer cotidianamente. Es ideal para el desarrollo de la identidad y la autonomía; por consiguiente, es importante planificar momentos de juego libre. (p. 109)

> En síntesis, de acuerdo a las consideraciones señaladas anteriormente, las planificaciones alcanzan valor pedagógico efectivo cuando se realiza un trabajo de reflexión profunda, respecto a los criterios de coherencia, pertinencia y flexibilización que debe presentarse en la selección, jerarquización, distribución y organización de los objetivos de aprendizajes. (p. 109)

> [n. 25] Esto, de acuerdo con el decreto N°83/2015 del Mineduc, que "Aprueba Criterios y Orientaciones de Adecuación Curricular para Estudiantes con Necesidades Educativas Especiales de Educación Parvularia y Educación Básica". (p. 107)

### Consideraciones para la evaluación

Esta es la sección más relevante para Kimün. Transcripción literal (pp. 110–112):

> La evaluación puede concebirse como una instancia formadora y una herramienta de apoyo al aprendizaje, que aporta efectivamente al logro de los OA. Vista así, es una evaluación para el aprendizaje y no solo del aprendizaje, trascendiendo la noción de que solo es un juicio de qué o cuánto aprendió una niña o niño para constituirse en una oportunidad más de aprendizaje. (p. 110)

> A continuación, se plantean algunas consideraciones para evaluar desde un enfoque de apoyo al desarrollo y aprendizaje integral de las niñas y los niños.
>
> Es importante comprender la naturaleza íntima del aprendizaje propuesto en los OA: su estructura, alcance y profundidad. Una tarea imprescindible de los equipos es discutirlo colectivamente, especificando algunos criterios para reconocerlo como logrado; los que, a su vez, ayudarían a favorecerlo de manera adecuada.
>
> Evaluar consiste en seleccionar y construir progresivamente, de preferencia, en conjunto con los párvulos, evidencias de sus procesos de aprendizajes. Son múltiples las formas de recogida de información (por ejemplo, fotografías, grabaciones, observaciones), y múltiples los escenarios en que puede evidenciarlos (por ejemplo, la celebración de un cumpleaños, una actividad de aprendizaje, un paseo por la plaza).
>
> La información se obtiene en situaciones cotidianas y funcionales, que se realizan habitualmente. En principio, no es imprescindible construir situaciones especiales ni momentos formales de evaluación. Las diversas situaciones cotidianas pueden ser suficientes; una experiencia de aprendizaje de ayer, repetida hoy, puede devenir una ocasión para evaluar aquello que se estaba aprendiendo. Esto es evaluación auténtica, es decir, correspondencia entre las situaciones reales en las cuales la niña o el niño se expresa o despliega, y el desempeño a evaluar.
>
> Tanto en la enseñanza como en la evaluación, el foco debe estar en la niña o el niño. Pero no necesariamente se espera que él o ella defina criterios de una "buena ejecución o comportamiento", porque la mayoría de las veces es el adulto quien propone indicadores o reactivos que representan un OA. Sin embargo, el párvulo progresivamente debe tener la oportunidad de expresarse respecto de sus propios avances, dificultades y desafíos, así como de sus vivencias en las situaciones de aprendizaje. Es en este sentido que importa el protagonismo, como involucramiento frente a la experiencia de aprender.
>
> La autoevaluación es una herramienta que se utiliza en forma habitual en la Educación Parvularia. Al respecto, se requiere montar experiencias situadas en las que los párvulos puedan, colaborativamente con compañeros y adultos, "analizar" lo que sucedió, así como también los aspectos que impidieron o facilitaron los resultados. Vista así, la autoevaluación contribuye no sólo a la comprobación de aprendizajes, sino al proceso de autorregulación y metacognición del párvulo. (p. 110)

> La selección de los procedimientos e instrumentos de recolección de evidencias se realiza en coherencia con el núcleo y OA intencionados, y con la situación de evaluación. Es importante que no alteren la autenticidad de esta. Registros de observación, piezas audiovisuales, listas de cotejo, escalas de apreciación, informes al/del hogar, portafolios y documentación pedagógica son medios habituales de recolección de evidencias en este nivel. (p. 111)

> Especial utilidad tiene la documentación pedagógica, como una herramienta referida al acompañamiento del proceso integral que vivencia el niño y la niña. Se desarrolla a través de un proceso riguroso de observación, documentación e interpretación de las diversas experiencias de la que los párvulos son partícipes. Se recogen ideas, anécdotas, conflictos de cada uno de los niños y las niñas, en momentos diversos, de tal modo que se pueden convertir en una poderosa herramienta para la toma de decisiones pedagógicas, y que pueden constituir una buena estrategia para potenciar su identidad. (p. 111)

> Reunidas las evidencias, el o la educadora debe construir una conclusión evaluativa acerca del desempeño del párvulo, teniendo en cuenta la distancia entre lo que él o ella es capaz de hacer y lo que plantea el objetivo de aprendizaje. Es importante que la evidencia se vincule al propósito de tomar decisiones pedagógicas respecto de cómo apoyar mejor los aprendizajes de las niñas y los niños, de lo contrario, pierde su sentido. Esto que parece sencillo, requiere un conocimiento y comprensión profunda de la progresión, contenidos y habilidades que integra cada uno de los OA, y también de la información proveniente de la documentación técnica del proceso. (p. 111)

> La enseñanza y la evaluación están, en más de un sentido, profundamente imbricadas. Los equipos pedagógicos suelen evaluar aquello que han enseñado, y por tanto los párvulos han tenido oportunidad de aprender. En cambio, a veces se implementan evaluaciones externas, es decir, organizadas y/o llevadas a cabo por actores diferentes al establecimiento; este tipo de evaluación podría considerar aprendizajes que los párvulos no han tenido oportunidad de aprender. A los equipos directivos y pedagógicos corresponde decidir acerca de su conveniencia. (p. 111)

> La comprensión del error lleva al aprendizaje significativo. Existe la tendencia por parte de algunos docentes, de pensar que los niños y las niñas no están preparados para conocer sus errores y superar dificultades. Por ello, la evaluación tiende a negar su valor como indicador del proceso, y a cambio se utiliza la estrategia de que todo "lo hace bien", lo que atenta contra el sentido de calidad de los aprendizajes. Tampoco se trata de sobredimensionar su importancia; la retroalimentación ajustada es una competencia del o la educadora -más bien del equipo- y conlleva a considerarla como fuente de aprendizaje. Debe realizarse retroalimentación contingente al momento del desempeño, en formas sencillas tales que el párvulo progresivamente las entienda y las acoja. Se trata de generar un contexto (espacio, tiempo y apoyo) para la mejora. Esta debe ser una postura colectiva de la comunidad educativa. (p. 111)

> En la retroalimentación reside el potencial de la evaluación para constituirse en una nueva oportunidad de aprendizaje. Es la comunicación de la distancia entre los desempeños de la niña o el niño y lo definido en el objetivo de aprendizaje. El contenido de esa comunicación debe informar al párvulo de sus avances, logros y desafíos con relación al OA, con un lenguaje acogedor, que valora la diversidad de ritmos y formas de aprender. Durante las experiencias para el aprendizaje, a menudo ya hay retroalimentación, bajo la forma de preguntas y comentarios del aprendizaje que se está construyendo. (p. 112)

> En este sentido, la retroalimentación, aporta también a la calidad y adecuación de las experiencias para el aprendizaje implementadas; nutriendo la reflexión docente sobre su práctica pedagógica. (p. 112)

> La evaluación es un insumo importante para la planificación de mediano o largo plazo. La información puede provenir de una evaluación inicial y/o de la evaluación final del periodo precedente a fin de que permita orientar la enseñanza, ajustar las planificaciones y las estrategias. (p. 112)

> La evaluación formativa, que ocurre mientras se desarrolla el proceso de aprendizaje, cristaliza el aporte de la evaluación para este. El foco de la evaluación formativa no es necesariamente cuánto sabe el párvulo, sino cuáles están constituyendo sus principales logros y dificultades, para, con él, generar estrategias para sus avances. No solo compromete al niño o la niña, sino que interpela al docente en su enseñanza. (p. 112)

> La evaluación final o sumativa, que permite verificar el logro de los OA, suele coincidir con otros propósitos, como informar a las familias y tomar decisiones de la transición del niño y la niña entre niveles. Posibilita contar con información valiosa acerca de lo que son, saben, conocen y hacen los párvulos. Lo importante es que se desarrolle siempre desde una perspectiva de evaluación auténtica y formadora, sin juicios perentorios, preparando el camino para seguir avanzando en el aprendizaje. Del mismo modo, permite una evaluación de las acciones docentes emprendidas, para identificar en qué medida es necesario cambiar o afirmar esas prácticas educativas. (p. 112)

### Contexto Ambientes de Aprendizaje

> Los ambientes de aprendizaje refieren a sistemas integrados de elementos consistentes entre sí, que generan condiciones que favorecen el aprendizaje de los niños y las niñas. Estos sistemas están conformados por las interacciones pedagógicas que se desarrollan en espacios educativos y en tiempos determinados. (p. 113)

> El espacio educativo es concebido como un tercer educador, en tanto se transforma con la acción del niño y la niña, y con una práctica pedagógica que acoge esta reconstrucción permanente, en las interacciones que se producen en este. (p. 113)

> Los elementos que componen estos, son físicos (la materialidad, la luz, el diseño, la ventilación, las dimensiones, entre otros), organizacionales, funcionales y estéticos (la distribución del equipamiento, la disposición de los materiales, entre otros). (p. 113)

> Cuando se hace referencia a los ambientes de aprendizaje, no sólo se está aludiendo al aula de un establecimiento, sino a los más diversos escenarios donde se organizan y tienen lugar relaciones educativas, tales como una plaza, un lugar de trabajo, una cancha de deportes, una sala de exposiciones. (p. 113)

> Para lograr que los ambientes de aprendizaje sean significativos, es importante velar por la consistencia y congruencia entre estos componentes, en relación con las características, necesidades e intereses de los niños y las niñas, las experiencias previas que poseen, las fortalezas que los potencian y el contexto sociocultural, intercultural y lingüístico al que pertenecen. (p. 113)

> Cualquier lugar y momento donde interactúen las o los educadores y párvulos, dentro o fuera del establecimiento, puede constituirse en un ambiente de aprendizaje. Las diversas experiencias que se suceden en ellos dan cuerpo y sustancia a estos ambientes. Es la riqueza de estos ambientes la característica que importa construir, en la medida que su calidad dispone a los niños y las niñas a aprender. Que los ambientes de aprendizaje sean más o menos enriquecidos, depende de que las y los educadores se dispongan para ello. Así, los diversos ambientes que son posibles de distinguir en un establecimiento, no pueden resultar de la casualidad, sino de la conciencia y la intención educativa de configurarlos como tales. En esto la planificación es una herramienta útil. (p. 113)

Interacciones pedagógicas:

> La interacción es la principal herramienta pedagógica del proceso de aprendizaje, desde temprana edad. El o la educadora y el equipo pedagógico, deben asegurar que las interacciones entre adultos y párvulos, entre las niñas y los niños y entre los adultos, constituyan un escenario favorable para el bienestar, el aprendizaje y desarrollo integral, así como para aquellos sentidos que de manera particular cada comunidad educativa se ha propuesto imprimir a su proyecto educativo. Algunas consideraciones a tener en cuenta, son las siguientes:
>
> Promover la participación activa de los párvulos en la generación de interacciones pedagógicas. Esto conlleva atender sus preguntas e iniciativas como valiosos puntos de partida de diálogos y experiencias de aprendizaje. Implica también atender a la significación que posee para la niña y el niño la organización de los ambientes.
>
> Construir vínculos afectivos positivos y estables con las niñas y los niños, que les permita sentirse queridos, seguros y aceptados por los adultos que los rodean. El desarrollo de los objetivos de aprendizaje se beneficia enormemente de interacciones asentadas en una relación de cierto apego. Para establecer esta relación, se requiere que las o los educadores, equipos pedagógicos y otros agentes educativos observen y escuchen activamente a las niñas y los niños. Requieren también ser empáticos y respondientes a sus características, necesidades e intereses, acompañándolos en su proceso de aprendizaje y en la resolución de conflictos en todo ámbito.
>
> Las interacciones entre el o la educadora y los párvulos, y entre los niños y niñas deben tener como base un conjunto de normas relacionadas con el respeto mutuo, en la forma y en el fondo. Normas comprendidas por todo el grupo de niñas y niños y consensuadas con cada párvulo. El o la educadora debe velar, por tanto, que toda dificultad que surja se resuelva en un clima de buen trato, considerando en todo momento la calidad de sujetos de derecho de todas las niñas y los niños, velando así que sus derechos sean promovidos y respetados por todos. Esto también es válido para las interacciones entre pares.
>
> Frente a un conflicto cotidiano, la y el educador debe promover el diálogo, la empatía, comprensión y la resolución creativa de conflictos, con la participación cada vez más protagonista de las niñas y los niños en la definición de normas y la búsqueda de soluciones colectivas. Al respecto, los planes de convivencia son un aporte en la construcción colectiva de un ambiente positivo y dialogante, especialmente si en ellos participa la familia.
>
> La educación de los párvulos implica por parte del equipo pedagógico, asumir su rol fundamental como mediadores del aprendizaje. Implica el reconocimiento de que el docente es puente para que la niña o niño alcance niveles crecientes de aprendizaje, superiores a los que podrían lograr por sí solos. Estrategias pedagógicas para ello son: la escucha activa del o la educadora, el juego, uso de preguntas movilizadoras, la curiosidad, el modelamiento, la verbalización detallada de sus acciones, guía y sugerencia de acciones, confrontación de distintos puntos de vista, planteamiento de hipótesis o problemas, el uso del error como instancia de aprendizaje.
>
> En muchas situaciones, los mismos niños y niñas pueden actuar como mediadores del aprendizaje de otros compañeros. Párvulos que han consolidado un aprendizaje determinado pueden ayudar a otros a desarrollarlo, en una experiencia de aprendizaje entre pares. Esto, sin perjuicio del aporte que cualquier niña o niño hace al avance de los otros en su proceso de aprendizaje, cuando comunica sus experiencias y conocimientos previos, cuando genera interacciones que invitan a conocer, reconocer, reordenar o transformar el entorno.
>
> Construir un clima positivo de relaciones en el establecimiento. La calidad de las interacciones pedagógicas que establecen los equipos pedagógicos con los párvulos, con otros grupos/cursos y entre sí, no es ajena al clima general de trabajo. Se requiere de ambientes institucionales motivadores, respetuosos y altamente coordinados, lo cual debe constituir un tema permanente de reflexión. (pp. 114–115)

Espacios y recursos educativos:

> Espacios educativos son los diferentes lugares donde ocurren interacciones pedagógicas. El concepto incluye atributos tales como diseño, construcción, dimensiones, ventilación, luz, colores, texturas, la distribución del mobiliario y el equipamiento, accesos y vías de circulación. Su carácter de educativos, expresa la intención de la comunidad de promover su calidad para acoger el protagonismo de todas las niñas y los niños en su proceso de aprendizaje. Esto implica contar con espacios como las zonas de juego en que los mismos niños y niñas toman decisiones, y con salas despejadas para que desplieguen su actividad motriz y expresión corporal. (p. 115)

> Los espacios pueden presentar dificultades que limitan su carácter de educativos, en la medida en que se descuidan sus características físicas, de habitabilidad o de funcionalidad, haciéndolos poco propicios para los propósitos implicados en los OA. (p. 115)

> Dentro de los variados espacios educativos se pueden distinguir algunos más permanentes y otros más transitorios. Ejemplos de los primeros son: sala de actividades, biblioteca, comedor, sala multiuso, patio. Ejemplos de los segundos son: plaza, feria, museo, bosque, invernadero, entre otros. (p. 115)

> Recursos educativos, por su parte, son todos aquellos elementos tangibles e intangibles que se utilizan o se encuentran a disposición de los párvulos y las o los docentes como insumos del proceso de enseñanza y aprendizaje. En este nivel el aporte del material concreto es fundamental para el aprendizaje a través de la acción. Entre estos elementos, algunos de los más importantes son los libros, utensilios y objetos cotidianos, elementos naturales, juguetes, instrumentos y recursos tecnológicos. Mientras que respecto a los elementos intangibles se pueden reconocer: canciones, juegos, melodías, narraciones, poemas, sonidos, entre otros. (pp. 115–116)

> Para la implementación de los espacios y recursos educativos, son útiles las siguientes consideraciones.
>
> La configuración del espacio y la selección de recursos educativos pueden comunicar poderosos mensajes de acogida o exclusión. Asumir el principio de inclusión no es posible sin transformar también los espacios para convertirlos en ambientes apropiados a la diversidad sociocultural de los párvulos. Por ejemplo, incluir objetos característicos de los países de origen de los niños y las niñas. Al incorporar creencias, rituales, costumbres, música, leyendas, narraciones e imágenes de su vida cotidiana y de su tradición familiar, se aumenta la significatividad de las experiencias para el aprendizaje. Asimismo, es fundamental considerar las adaptaciones necesarias tanto en los espacios educativos como respecto de los recursos, para favorecer la movilidad y uso de éstos por parte de niños y niñas que así lo requieran.
>
> Reorganizar y renovar los espacios y recursos para el aprendizaje en forma constante, en base el interés y las propuestas de los párvulos, de manera de potenciar su resignificación y reutilización. Ello puesto que los procesos de exploración, creación y descubrimiento, modifican las relaciones que se han establecido con anterioridad y los desafíos, por tanto, no son siempre los mismos.
>
> Generar y utilizar espacios y recursos educativos diversos y estéticamente interesantes, agradables, que inviten a los niños y las niñas a actuar con mayor autonomía, sentirse cómodos y acogidos para el proceso de aprendizaje. Para lograr esto, los espacios y recursos deben ser sensibles a las características, necesidades e intereses y a las propuestas de los mismos niños y niñas, de manera que los sientan propios.
>
> Considerar y viabilizar la utilización pedagógica de ambientes que posibiliten alternativas de actividades para el desarrollo de diversos OA. La ubicación, disposición y organización de espacios y recursos educativos, aquellos con que se cuenta y los que se pueden gestionar, son claves para ofrecer experiencias para el aprendizaje enriquecidas. Algunos de estos espacios pueden ser una plaza, una industria, un taller artesanal, una cancha de deportes, bibliotecas y museos, la feria o el almacén, un bosque u otros sitios naturales seguros.
>
> Es importante responder oportunamente a los requerimientos educativos de los párvulos a través de la selección de espacios y recursos para el aprendizaje, evitar espacios recargados (respecto de los coloridos, contrastes, implementos o equipamiento, entre otros), para facilitar la posibilidad de concentración de los niños y las niñas en su proceso de aprendizaje. Asimismo, evitar las imágenes y figuras estereotipadas que cierran la imaginación. Seleccionar lo que aporte a los objetivos de aprendizaje, implica intencionalidad y reflexión por parte de los equipos pedagógicos.
>
> Incluir el desarrollo de interacciones pedagógicas utilizando espacios educativos naturales con presencia de árboles, arbustos, plantas, huertos; algunos de estos espacios pueden ser conformados en conjunto con la comunidad educativa. También el desarrollo de experiencias para el aprendizaje referidas a la recolección, reciclaje o reutilización de basura o el uso de compostera, facilitan la toma de conciencia progresiva de los párvulos respecto del compromiso de todos y todas con el ambiente. Además, el uso de recursos educativos recolectados en condiciones naturales o confeccionados con materias primas reciclables y sanas para su objetivo, posibilitan también un compromiso cada vez más consciente con la mantención y mejoramiento de las condiciones en que aprende cada niño y niña.
>
> Proveer un conjunto de condiciones que garanticen el bienestar y la seguridad de las niñas y los niños, para una exploración confiada, implica por ejemplo asegurar una mantención de la infraestructura, el mobiliario, equipamiento y recursos educativos que resguarde las variadas situaciones de riesgo que pudieran acontecer, acorde a las características, necesidades e intereses y el desplazamiento de todas las niñas y los niños. (pp. 116–117)

Organización del tiempo:

> La organización del tiempo dice relación con la definición de los diferentes períodos de jornada diaria, sus duraciones y la secuencia que éstos deben asumir para responder a los propósitos formativos que pretenden estas Bases Curriculares. En este sentido, la organización del tiempo tiene que ver con la planificación de los aprendizajes, de largo, mediano y corto plazo. Sin embargo, aquí se trata del tiempo en tanto componente de los ambientes de aprendizaje, es decir de una variable asociada al espacio educativo y a las interacciones pedagógicas que ocurren en ellos, cuyo manejo puede potenciar o empobrecer los ambientes de aprendizaje. (p. 117)

> Algunas consideraciones a tener en cuenta para organizar el tiempo, son las siguientes:
>
> Al diseñar una jornada es necesario el desarrollo de experiencias variadas y equilibradas. Por ejemplo, entre periodos constantes y periodos variables. Los primeros proveen estabilidad y seguridad a las niñas y niños y les permitan anticipar situaciones. Los segundos, les aportan curiosidad, cambio, creatividad. Asimismo, es necesario resguardar variedad y equilibrio en las agrupaciones, alternando actividades colectivas e individuales, en grupos pequeños, entre niños y niñas con distintos niveles de aprendizaje y distintas edades. También, variedad y equilibrio en grados de movimiento, actividades de mayor y menor movilidad física y gasto energético. Además, entre actividades de reflexión y de expresión; instancias que favorecen la relajación, el ocio, la contemplación y la meditación. Por último, utilizar diversos espacios educativos interiores, exteriores, y naturales.
>
> Se requiere fluidez entre las experiencias para el aprendizaje, de manera que los párvulos no tengan que esperar entre éstas por razones administrativas o falta de organización, evitando que existan tiempos que no sean aprovechados pedagógicamente. Además, implica ofrecer oportunidades alternativas a aquellas niñas y niños que han finalizado con antelación a sus compañeros y compañeras, respetando así, sus ritmos individuales de aprendizaje.
>
> En cuanto a la duración de las experiencias de aprendizaje, su extensión debe ser siempre flexible y variar de acuerdo a: los OA que se pretenden favorecer, capacidad de atención de los párvulos, concentración y perseverancia; y su grado de motivación frente a una determinada situación. Implica, por tanto, la observación atenta del desarrollo de las experiencias, de manera de reducirlas o ampliarlas cuanto sea necesario. La duración de los períodos debe hacerse de manera tal que permita a los niños y las niñas tener tiempo para explorar, ensayar, cometer errores, reflexionar y rehacer y, por cierto, para jugar, evitando su cansancio y propiciando en todo momento el disfrute del aprendizaje y el trabajo colaborativo. (pp. 117–118)

### Contexto Familia y Comunidad Educativa

> La familia, considerada en su diversidad, constituye el núcleo central básico en el cual la niña y el niño encuentran sus significados más personales, debiendo el sistema educacional apoyar la labor formativa insustituible que ésta realiza. (p. 119)

> En consecuencia, este contexto refiere al reconocimiento por parte de la Educación Parvularia de que la familia y la comunidad educativa son, de hecho, agentes formadores de las niñas y niños en múltiples formas, constituyendo un contexto educativo en sí mismo. Se trata entonces de que todos ellos construyan y adhieran al proyecto educativo común que se implementa, y que compartan la responsabilidad de contribuir a sus aprendizajes y desarrollo integral de los párvulos. De esta manera, la participación de todos estos actores que se suman a la labor educativa común, contribuye a dar pertinencia, soporte valórico y cultural, a los proyectos educativos que se desarrollarán a partir de estas Bases Curriculares o los ya definidos por las familias y comunidades de salas cuna, jardines infantiles, escuelas u otros programas educativos. (p. 119)

> De la misma forma, este contexto concibe también que la comunidad educativa, y los equipos pedagógicos en particular, influyen en la calidad del proceso de aprendizaje, mediante la reflexión pedagógica colaborativa. Así, ellos son también aprendientes, que recrean nuevos significados respecto de su práctica, a partir de una mirada evaluativa de la experiencia cotidiana de aprendizaje de los párvulos, y las interacciones pedagógicas que las originan. El contar con una comunidad educativa abierta al diálogo, a aprender de la experiencia y de otros, que promueve los cambios necesarios, que busca nuevas oportunidades para las niñas y los niños, que involucra a otras instituciones para una mejor calidad de vida, es sin duda un factor clave en un proceso de enseñanza y aprendizaje. (p. 119)

Consideraciones para el trabajo colaborativo de la Familia y la Comunidad Educativa:

> La comunidad educativa requiere forjar una convergencia de voluntades para favorecer el proceso de aprendizaje de las niñas y los niños. Equipos pedagógicos, familia, y otros agentes de la comunidad, deben sentirse parte de los objetivos que se promueven en los establecimientos o programas. En ese sentido, el Proyecto Educativo Institucional (PEI), debe ser convocante y constituir el marco que explicite los sentidos, propósitos y desafíos educativos específicos a los que la comunidad educativa adhiere. Facilitar una comprensión clara y precisa de las características del proyecto educativo, es esencial. (p. 119)

> Que se reconozca explícitamente, en los diferentes instrumentos o a través de distintas estrategias, el valor de la familia y la comunidad, con su diversidad de creencias y costumbres, como un aporte al desarrollo y contextualización curricular y a la generación del aprendizaje situado. Para tal efecto, las instituciones educativas disponen de instrumentos de gestión existentes, tales como el PEI, los Reglamentos Internos, Reglamentos y/o Manuales de Convivencia, los Planes de Mejoramiento Educativo, entre otros. También se cuenta con instancias de participación, tales como: Consejo de Educación Parvularia y Escolares, Consejo de Profesores/as, reuniones de apoderados/as. (p. 120)

> Integrar a las madres, padres, adultos significativos y apoderados, velando porque se sientan bienvenidos, respetados y escuchados. Especiales esfuerzos se requieren para acoger la participación de los hombres de la familia y la comunidad. Los equipos pedagógicos deben generar condiciones para producir puentes de acercamiento, confianza y la seguridad necesaria, para que las familias se sientan parte activa del proceso. Cabe tener presente el aporte de la familia y de otros agentes educativos de la comunidad en el desarrollo de actividades directas con los niños y las niñas, situación que es particularmente significativa para ambos. (p. 120)

> De acuerdo a lo anterior, es importante conocer e implementar una relación permanente con las familias, a través de, conversaciones abiertas, que no se centren exclusivamente en la entrega de información, sino que, en escuchar sus ideas, expectativas, experiencias, prácticas y estilos de crianza. La niña y el niño deben sentir y percibir concordancia y coherencia entre los mundos de su familia y el establecimiento educativo. Los encuentros y reuniones que puedan generarse con estos fines son vitales en la construcción de una relación transparente, desprejuiciada y participativa que valore los aportes de la familia como un agente educativo que se sienta parte en la toma de decisiones. (p. 120)

> Es útil que las o los educadores y los equipos pedagógicos levanten registros, mediante bitácoras de trabajo, que evidencien el proceso de aprendizaje que se está llevando a cabo, y faciliten la reflexión del sentido que este tiene para ellos. A partir de estas evidencias, se pueden desarrollar diálogos reflexivos en torno a situaciones concretas, mirar las propias prácticas con mayor rigor, y ofrecer escenarios reales para que la comunidad aprenda conjuntamente y tenga parámetros de referencia para orientar las decisiones de mejora. (p. 120)

> Se deben generar y ampliar redes de trabajo permanentes y frecuentes con los servicios locales de salud, de apoyo psicosocial y otros servicios relevantes, con el fin de promover el aprendizaje y desarrollo integral de los párvulos. La participación en redes comunitarias, ya sea de organizaciones o instituciones locales, posibilita además el conocimiento del territorio en el que se inserta el centro educativo y en el que niños y niñas y sus familias se desenvuelven, otorgando importante información para nutrir los diversos instrumentos de gestión y las acciones que, desde dichos instrumentos, se pueden intencionar. (p. 120)

> Finalmente, es importante destacar el valor que posee la reflexión colectiva respecto de la propia práctica docente, nutrida por el análisis de evidencias y el contraste con los planteamientos de la política pública y de las Bases Curriculares, así como con el proyecto educativo del establecimiento. No se trata de una reflexión circunstancial, sino enmarcada en procesos sistemáticos de mejora continua de los establecimientos, que permita compartir una mirada respecto de los desafíos educativos. Una adecuada organización del tiempo implica destinar momentos a la reflexión pedagógica; una actividad tan importante para el progreso profesional de los equipos pedagógicos, que necesita encontrar su tiempo propio para desarrollarse. (p. 121)

### Bibliografía

El documento cierra con "Bibliografía consultada" (pp. 122–131). Son referencias académicas (Ainscow, Ausubel, Bruner, Piaget, Vigotsky/Vygotsky, Diamond, UNESCO, OECD, marcos curriculares de Australia, Inglaterra, Ontario y Uruguay, entre muchas otras). No se transcriben aquí por no ser relevantes para la aplicación; están en el PDF si se necesitan.

---

## Glosario de términos del documento

Definiciones tal como las usa este documento (con su página de referencia principal).

- Ámbito de experiencias para el aprendizaje: campo curricular donde se organizan y distribuyen los OA (3 en total). p. 38.
- Núcleo de aprendizaje: foco central de experiencias que agrupa e integra OA (8 en total). p. 39.
- Objetivo de Aprendizaje (OA): aprendizaje esencial que se espera potenciar, enunciado desde lo esperado al final de cada nivel (tramo de 2 años). pp. 40–41.
- Objetivo de Aprendizaje Transversal (OAT): OA de los tres núcleos del Ámbito Desarrollo Personal y Social; deben estar presentes de forma permanente. pp. 40, 108.
- Nivel o tramo curricular: organización temporal de los OA en tres tramos de 2 años: 1° Sala Cuna (hacia los 2 años), 2° Medio (hacia los 4), 3° Transición (hacia los 6). p. 41.
- Transición: tercer nivel; administrativamente NT1 (Primer) y NT2 (Segundo). nota 18, p. 42.
- Evaluación auténtica: correspondencia entre las situaciones reales en que el niño se expresa y el desempeño a evaluar; información recogida en situaciones cotidianas. p. 110.
- Documentación pedagógica: proceso riguroso de observación, documentación e interpretación de las experiencias de cada niño en momentos diversos. p. 111.
- Conclusión evaluativa: juicio que construye la educadora sobre el desempeño, considerando la distancia entre lo que el niño hace y lo que plantea el OA. p. 111.
- Evaluación formativa / sumativa: la primera, durante el proceso, enfocada en logros y dificultades; la segunda, verifica el logro de los OA, "sin juicios perentorios". p. 112.
- Ambiente de aprendizaje: sistema integrado de interacciones pedagógicas en espacios y tiempos determinados; el espacio como "tercer educador". p. 113.
- Adecuación curricular: ajustes para la inclusión que pueden incluir seleccionar OA de un nivel distinto al del grupo (Decreto N° 83/2015). pp. 43, 107.
- Alfabetización científica inicial: manejo de conceptos y habilidades indagatorias propias de las ciencias, aplicadas a la vida diaria. nota 21, p. 81.
- Trayectoria educativa: mirada del aprendizaje como un continuo descrito en trayectorias referenciales, articulando parvularia con básica. pp. 42–43.

---

## Referencias normativas citadas (leyes, decretos y convenios)

- Ley N° 20.370, General de Educación (LGE), 2009: define los objetivos generales de la Educación Parvularia (Arts. 18 y 28). pp. 9, 16.
- Ley N° 20.379 (2009), "Chile Crece Contigo": acceso a sala cuna y jardín infantil. nota 10, p. 22.
- Ley N° 20.710 (2013): establece obligatorio el último año de parvularia y acceso universal gratuito desde los 2 años. nota 11, p. 22.
- Ley N° 20.529: Sistema Nacional de Aseguramiento de la Calidad de la Educación. p. 11.
- Ley N° 20.835: crea la Subsecretaría de Educación Parvularia. p. 11.
- Ley N° 20.845, de Inclusión Escolar. pp. 11, 22.
- Ley N° 20.911: Plan de Formación Ciudadana. pp. 11, 23.
- Convención sobre los Derechos del Niño (firmada por Chile en 1990). p. 20, nota 9.
- Decreto N° 83/2015 (MINEDUC): Criterios y Orientaciones de Adecuación Curricular para estudiantes con Necesidades Educativas Especiales. nota 25, p. 107.
- Decreto N° 439/2012 (MINEDUC): Bases Curriculares de la Educación Básica (referencia de continuidad). nota 24, p. 95.

---

## Anexo: protección de derechos y vulneraciones

Este anexo complementa las Bases con otras fuentes, porque las Bases no definen maltrato ni dicen qué hacer ante él. Kimün lee notas libres sobre niños de 0 a 6 años, así que tarde o temprano una nota va a describir una posible vulneración. Un agente que escribe prompts, procesa notas o diseña vistas debe saber qué es, qué no es y qué hacer.

Fuentes:

- Bases Curriculares (este documento): páginas impresas, como en el resto de la enciclopedia.
- Política de Calidad Educativa de Integra 2017, pp. 78–79 (Componente 1, Eje estratégico N° 4, "Protección de derechos"). Tiene derechos reservados: se parafrasea, con citas breves. Detalle en `guia-politica-calidad.md`, sección 12.
- JUNJI (2025), Protocolo de actuación frente a la detección de situaciones de vulneración de derechos en niños y niñas: <https://stgaccdatostransparencia.blob.core.windows.net/wpprod/2025/11/Protocolo-actuacion-vulneracion-infantil.pdf>. Cubre lo que no es delito. Se cita "JUNJI-V, p. N" (página del PDF).
- JUNJI (2025), Protocolo de actuación frente a hechos de maltrato infantil, connotación sexual o agresiones sexuales: <https://stgaccdatostransparencia.blob.core.windows.net/wpprod/2025/11/Protocolo-actuacion-maltrato-infantil.pdf>. Cubre lo que es delito. Se cita "JUNJI-M, p. N".

Los protocolos de la JUNJI son documentos públicos del Estado para jardines infantiles. Integra tiene su propio protocolo, que no tenemos (pregunta 9 de `PLAN.md`). Mientras no llegue, las definiciones de la JUNJI son la mejor referencia del sector, porque se basan en las orientaciones del MINEDUC de 2017 y en las instrucciones de la Superintendencia de Educación Parvularia. Cuando haya contradicción, manda el protocolo de Integra.

### Qué dicen las Bases

Las Bases no tratan el maltrato, pero fijan el piso:

> Siguiendo a la Convención de los Derechos del Niño, estas Bases reconocen los derechos económicos, sociales, culturales y otros del niño y la niña, tales como su derecho a la salud, a la educación, a no ser discriminado, a ser escuchado y que su opinión se tome en cuenta, a la libertad de pensamiento y de asociación, a ser protegido de toda forma de maltrato y de injerencias arbitrarias en sus vidas privadas [...] (p. 21)

> De acuerdo con este referente, la Educación Parvularia asegura al niño y la niña la protección y el cuidado que sean necesarios para su bienestar e interés superior [...] (p. 21)

El principio de bienestar "busca garantizar en todo momento la integridad física, psicológica, moral y espiritual del niño y la niña, así como el respeto de su dignidad humana" (p. 31). El contexto Familia y Comunidad pide redes permanentes "con los servicios locales de salud, de apoyo psicosocial y otros servicios relevantes" (p. 120).

Los OA que se acercan al tema son aprendizajes del niño, no mecanismos de protección. No sirven para detectar nada: `CC-M-7` y `CC-T-7` (identificar situaciones de riesgo para su bienestar y seguridad), `CC-M-9` y `CC-T-9` (sus derechos, entre ellos a ser escuchado), `CM-M-1` y `CM-T-1` (comodidad corporal y autocuidado) e `IA-T-4` (expresar y regular emociones). Que un niño muestre o no estos aprendizajes no indica, por sí solo, que esté vulnerado.

### Qué pide la Política de Calidad (pp. 78–79)

Es el eje estratégico 4 del componente Bienestar y Protagonismo. Paráfrasis fiel, por partes:

1. Responsabilidad. Integra debe promover el derecho a la educación según la cobertura comprometida, en el acceso, la permanencia, la asistencia y el progreso de los niños. Aunque los niños son titulares de derechos, por su etapa de vida requieren "una acción especial y sistemática por parte del mundo adulto" que haga efectivos esos derechos (p. 78).
2. Respuesta a la vulneración. El sistema debe tener "mecanismos pertinentes y oportunos para responder a situaciones de vulneración" (p. 78), resguardando el interés superior del niño y su continuidad en el sistema educativo, que la Política llama "factor protector". Seguir asistiendo al jardín protege al niño: la respuesta no debe expulsarlo ni hacerlo faltar.
3. Dos funciones (p. 78):
   - Prevención: que adultos y niños tomen conciencia de los factores de riesgo, y prácticas educativas con relaciones cuidadosas y afectivas.
   - Protección: abordar cada situación con cuidado, visibilizando las necesidades del niño para contenerlo, acompañarlo, interrumpir la vulneración o favorecer que sus derechos se restituyan a tiempo.
4. Tres condiciones (pp. 78–79):
   - Acceso y permanencia: instrumentos y orientaciones para la matrícula, la permanencia, el progreso y las transiciones (entre niveles y hacia la Educación Básica), con trato digno, respetuoso y no discriminatorio.
   - Prevención: ante factores de riesgo, fortalecer sentidos, clarificar expectativas, delimitar ámbitos de acción y responsabilidades, y coordinarse dentro y fuera de Integra para un "contexto protector vigilante" de los derechos de la infancia (p. 79).
   - Protección, con cuatro puntos (p. 79): (i) actualizar y mejorar los protocolos de gestión de casos; (ii) fortalecer la información y la comunicación con las familias, asegurando contención frente a denuncias o presunción de agresión; (iii) en los equipos, gestionar las crisis para restituir el funcionamiento del jardín; (iv) con el niño presuntamente vulnerado, profundizar la acogida y el cuidado desde su interés superior y su derecho a la educación.
5. Gestión (p. 79): coordinar asesoría, supervisión y gestión de personas para acortar los tiempos de indagatoria y sanción en denuncias internas, y trabajar en red para la atención especializada y la derivación de casos.

Tres lecturas para Kimün:

- La Política nombra la presunción ("presuntamente vulnerados", "presunción de agresión"). Nadie en el jardín decide si hubo maltrato, y menos un modelo de IA. El jardín detecta, acoge, informa y deriva.
- Las vulneraciones pueden ocurrir dentro del jardín, porque el punto (iii) y las denuncias internas lo suponen. Una nota puede describir el actuar de un adulto del equipo.
- Lo central es el niño: acoger, cuidar, mantener su asistencia y evitar la revictimización. Un sistema que expone el caso o lo usa como dato lo daña.

### Qué constituye maltrato

Jerarquía de términos:

- Vulneración de derechos: el término amplio. Toda situación en que no se respetan o no se satisfacen los derechos del niño. Incluye el maltrato.
- Maltrato infantil: una forma de vulneración. Tiene cuatro tipos: físico, psicológico, negligencia y agresión sexual. Algunas formas son delito.
- "Abuso": en el habla común abarca todo lo anterior. En el lenguaje institucional, "abuso sexual" es un delito específico. La JUNJI prefiere "agresión sexual" porque es más amplio (JUNJI-M, p. 23).

En la interfaz y en los prompts, Kimün dice "posible vulneración de derechos". No usa "abuso" ni "maltrato" como etiqueta, porque son calificaciones que hace el protocolo y no la app.

Definición general (JUNJI-V, p. 20; igual en JUNJI-M, p. 20):

> La JUNJI define maltrato infantil como "cualquier acción u omisión, no accidental, por parte de los padres, madres, cuidadores o terceros que provoca daño a la salud o desarrollo psicológico de la niña o niño". En la misma línea, el MINEDUC entiende por maltrato infantil "todos aquellos actos de violencia física, sexual o emocional, sea en el grupo familiar o en el entorno social, que se cometen en contra de niños, niñas y adolescentes, de manera habitual u ocasional".

Los tres elementos que definen el maltrato son: lo comete un adulto (padres, cuidadores o terceros, incluido personal del jardín), puede ser acción u omisión, y no es accidental. Puede presentarse "en más de una de sus formas, en más de un contexto a la vez, así como en distintas frecuencias e intensidades" (JUNJI-V, pp. 20–21). Basta un hecho aislado: el MINEDUC dice "habitual u ocasional".

#### Maltrato físico (JUNJI-V, p. 21)

> Se define como la acción no accidental por parte de los padres, madres, cuidadores o terceros que provoque daño físico o sea causal de enfermedad en la niña o niño, o lo ponga en grave riesgo de padecerla. La aflicción de daño físico y dolor puede tener distintos propósitos, incluso aquellos validados socialmente como corregir o controlar la conducta de la niña o niño. Por lo tanto, conductas constitutivas de maltrato físico son el castigo corporal, incluyendo golpes, palmadas, tirones de pelo, empujones, azotes, zamarrones, pellizcos u otras medidas que causen dolor o sufrimiento físico.

Según su gravedad:

- No es delito, "maltrato físico no relevante": una acción física no accidental "sin mayor notoriedad o magnitud y que no ocasiona una lesión física". El ejemplo de la JUNJI: "cuando se toma de manera brusca la mano de una niña o niño para que se incorpore a alguna experiencia pedagógica" (JUNJI-V, p. 21). Sigue siendo maltrato y activa el protocolo.
- Es delito (JUNJI-M, p. 21):
  - "Maltrato físico con lesiones": provoca "daño físico observable (lesiones)".
  - "Maltrato físico relevante": se ejerce "de manera violenta, no justificada, desproporcionada e inesperada", sin lesión, "donde la única explicación es el ejercicio abusivo de poder y la pérdida de control por parte del adulto".

El castigo corporal "para corregir" es maltrato, aunque la familia o el adulto lo consideren normal.

#### Maltrato psicológico (JUNJI-V, pp. 22–23)

Incluye el abandono emocional, el maltrato emocional y la exposición a la violencia intrafamiliar (VIF).

> El maltrato psicológico, por definición, consiste en la hostilidad hacia la niña o niño manifestada por ofensas verbales, descalificaciones, críticas constantes, humillaciones, ridiculizaciones realizadas en privado o en público, rechazo emocional y afectivo. También se incluye ser testigo de violencia, discriminación sufrida en razón de raza, género, características físicas y capacidad mental, entre otros. Algunos ejemplos son el lenguaje con groserías o que menoscabe a la niña o niño, cualquier forma de burla, humillación pública o privada, incluyendo amenazas de castigo físico, cualquier forma destinada a aterrorizar o aislar a una niña o niño, sanciones o castigos que impliquen el retiro de alimentos, descanso o prohibición de acceso a servicios higiénicos o encuentros con su familia, etc. En este sentido, también constituye una forma de maltrato psicológico la falta persistente de respuesta a las señales de los niños y niñas, entre las que es posible encontrar expresiones emocionales y conductas que los párvulos despliegan en la búsqueda de proximidad y contacto afectivo, entre lo que es posible incluir la falta de iniciativa de interacción y contacto por parte de la figura adulta estable, incurriendo con esto en un abandono emocional de niños y niñas.

En un jardín esto incluye prácticas del propio equipo: dejar a un niño sin colación o sin siesta como castigo, no dejarlo ir al baño, aislarlo, burlarse, amenazarlo, o ignorar de forma persistente su búsqueda de contacto.

- No es delito, "maltrato psicológico no degradante": las mismas conductas cuando "no producen como efecto en las víctimas sentimientos de terror y de inferioridad" que las humillen o quiebren su resistencia física y moral (JUNJI-V, pp. 22–23).
- Es delito, "maltrato psicológico degradante": "un trato cruel, degradante y humillante que afecta gravemente la integridad psíquica del niño o niña y su dignidad humana, bastando con una acción única de estas características para constituir un delito" (JUNJI-M, pp. 22–23).

#### Negligencia (JUNJI-V, p. 23)

> Se refiere a situaciones en que los padres, madres, cuidadores o terceros, estando en condiciones de hacerlo, no brindan el cuidado y la protección que niñas y niños necesitan para su desarrollo. La negligencia se manifiesta en el descuido en diversos ámbitos como son la alimentación, la estimulación, la educación, la recreación, la salud y la higiene, entre otras. En este sentido, existe negligencia cuando los responsables del cuidado y educación de los niños y niñas no atienden ni satisfacen sus necesidades básicas.

La clave es "estando en condiciones de hacerlo". La pobreza no es negligencia: Integra atiende sobre todo a familias vulnerables. Que un niño llegue con hambre o sin abrigo es una señal que la educadora interpreta con lo que sabe de la familia, no un hecho que la app califica.

#### Agresión sexual (JUNJI-M, p. 23)

> Las agresiones sexuales corresponden a cualquier tipo de actividad sexual con una niña o niño, en la cual el agresor o agresora está en una posición de poder y utiliza la seducción, el chantaje, las amenazas y/o la manipulación, para obligar a la niña o niño a realizar actos de carácter sexual que no es capaz de comprender ni detener, tales como insinuaciones, caricias, exhibicionismo, voyeurismo, masturbación, sexo oral, penetración oral, anal o vaginal, exposición a material pornográfico, explotación y comercio sexual infantil, el abuso sexual, la violación, entre otros. Este tipo de maltrato infantil se caracteriza por la utilización del niño o niña como un objeto sexual en la relación de desigualdad y asimetría antes descrita.

"Todas las formas de agresiones sexuales son hechos que tienen carácter de delito" (JUNJI-M, p. 23).

#### Contextos (JUNJI-V, p. 24)

- Intrafamiliar: el presunto responsable es de la familia o el hecho ocurre en el ámbito familiar.
- Intrajardín: lo comete "un funcionario, funcionaria o bien un tercero que se encuentra realizando labores dentro el establecimiento educativo".
- Otros contextos: alguien fuera de la familia y del jardín, por ejemplo un transportista escolar o un vecino.
- Indeterminado: no hay antecedentes claros.

Para Kimün, el contexto intrajardín significa que quien escribe la nota, o una colega, puede ser parte del hecho. Por eso el aviso no puede quedar solo en manos de quien registró.

### Qué no constituye maltrato

- Las agresiones entre niños. "Por su parte, agresiones entre niños y niñas no constituyen maltrato infantil" (JUNJI-V, p. 21). Un empujón, un mordisco o una pelea entre párvulos son conflictos de convivencia. Kimün los registra como observación de aprendizaje (CC o IA, "por reforzar"), como ya hace el prompt de separación. Que un niño agreda a otros de forma repetida o desproporcionada no es maltrato, pero sí puede ser una señal de que algo le pasa. Esa lectura la hace la educadora.
- Los accidentes. La definición exige que el hecho no sea accidental. Una caída en el patio sigue el procedimiento de accidentes del jardín. Una lesión con una explicación que no calza, o lesiones repetidas, sí son indicadores.
- Los límites dados con buen trato: contener a un niño desregulado para que no se dañe, retirarlo un momento del juego acompañado, decirle que no. Lo que distingue el maltrato es el daño, la humillación, el dolor como medio o la privación de necesidades básicas.
- El juego y la fantasía. Un niño que juega a que el lobo se come a los chanchitos, que dibuja monstruos o que representa una pelea en el rincón de la casa está jugando. Las Bases valoran ese juego simbólico (IA, CC, LA).
- La pobreza y la falta de recursos (ver negligencia).
- Las emociones y conductas propias del desarrollo o de un cambio: llorar al separarse de la familia, berrinches, regresiones ante la llegada de un hermano. Son observaciones de aprendizaje o de bienestar.

Ningún indicador aislado prueba una vulneración, y la falta de indicadores no prueba que no exista. Por eso Kimün no decide: avisa y deja la decisión en personas.

### Cómo se detecta (JUNJI-V, p. 26)

Los hechos pueden conocerse por:

- el relato de un niño;
- el relato o la información de terceros (familias, funcionarios, vecinos, redes de salud o protección, redes sociales, anónimos, entre otros);
- "la observación de indicadores físicos, emocionales y/o comportamentales en la niña o niño";
- la observación de indicadores comportamentales en las familias o cuidadores.

La JUNJI distingue el conocimiento directo (presenciar el hecho, recibir un relato u observar indicadores) del indirecto (redes sociales, comentarios de vecinos o apoderados, "comentarios de pasillo"). Los dos obligan a informar (JUNJI-V, p. 27).

Para Kimün, una nota de una educadora es conocimiento directo de quien la escribió. Si la nota lo menciona, la situación ya existe para la institución, aunque la app no haga nada. Lo que Kimün decide es si la ayuda a llegar a quien corresponde o si la entierra como "observación de convivencia".

Ejemplos de lo que una nota podría traer. Son ilustrativos y no son criterios diagnósticos:

- Relato del niño: "Tomás dice que su papá le pega con la correa cuando se porta mal"; "la Sofi contó que el tío del furgón le toca la pierna".
- Indicadores físicos: moretones o marcas en zonas poco expuestas al juego, lesiones repetidas o con explicaciones que no calzan, quemaduras.
- Indicadores emocionales o de conducta: temor marcado a un adulto en particular o a irse a la casa, cambios bruscos de conducta, conductas sexualizadas impropias de la edad, retraimiento persistente.
- Negligencia: llega con hambre de forma habitual, la misma ropa sucia por días, una enfermedad sin atender.
- Prácticas del equipo: "la tía la dejó sin colación por pegarle a otro", "lo encerraron en el baño", gritos o burlas a un niño.

### Qué hacer: pasos de la JUNJI como referencia

Los plazos son de la JUNJI. Los de Integra pueden ser otros.

1. Informar. Quien toma conocimiento, directo o indirecto, informa "de manera inmediata" a la directora o encargada, en un plazo máximo de 2 horas, por la vía más expedita. La directora informa al equipo regional (JUNJI-V, p. 27).
2. Resguardar la intimidad y la identidad del niño en todo momento, y la identidad del adulto involucrado hasta que haya claridad, sin que eso obstaculice la protección del niño. También hay que dejar registro de las acciones en el instrumento oficial del protocolo (JUNJI-V, p. 25; p. 50).
3. No interrogar. Para evitar la revictimización:

   > se debe evitar realizar intervenciones que aborden de manera inadecuada la situación vivenciada por el párvulo, como, por ejemplo, interrogar o indagar sobre los hechos, así como cansar al niño o niña ante la presión de recabar antecedentes de la situación de vulneración de derechos. [...] Sólo se debe escuchar y acoger el relato del niño o la niña sin intervenciones de ningún tipo, ya que dichas intervenciones pueden contaminar el relato de los párvulos, el cual podría tener un rol relevante como prueba en el caso que se desarrolle un proceso penal. (JUNJI-V, p. 44)

4. Ante un relato: actitud cálida, calma, "escuchar y creer el relato espontáneo", no reforzar la culpa, explicarle al niño que, por su bienestar, la persona en quien confió deberá contarlo a otros, y mostrar disponibilidad (JUNJI-V, p. 45). Sin relato pero con indicadores: un adulto sensible que, "sin interrogar al párvulo", lo acoja y le dé confianza (JUNJI-V, p. 45).
5. Registrar el relato "lo más textual posible", o los indicadores observados, al comunicar la situación (JUNJI-V, p. 39).
6. Derivar y proteger. Según el caso: solicitar una medida de protección al Tribunal de Familia; si el hecho podría ser delito, orientar a la familia a denunciar o denunciar la institución "dentro de las 24 horas" siguientes (JUNJI-V, p. 29; JUNJI-M, p. 30); avisar a las redes de salud y protección.
7. Acompañar en la sala: ambiente acogedor y seguro, vínculo afectivo, validar emociones, juego libre sin presionar, más tiempo y flexibilidad para separarse de la familia y estrategias de calma (JUNJI-V, pp. 45–48).

Marco legal, citado por los protocolos de la JUNJI. Antes de usarlo en la app o en el pitch, confirmarlo con Integra:

- Ley 21.430 (2022), sobre garantías y protección integral de los derechos de la niñez y adolescencia: el derecho a la protección contra la violencia y el deber de quienes trabajan con niños de asegurarla; además, confidencialidad de los datos sensibles.
- Ley 21.013 (2017): tipifica el maltrato corporal relevante y el trato degradante contra menores. De ahí salen las categorías "relevante" y "degradante".
- Código Procesal Penal, arts. 175 y 176: los directores, inspectores y profesores de establecimientos educacionales deben denunciar los delitos que afecten a sus estudiantes dentro de las 24 horas siguientes a conocerlos.
- Ley 20.066, de violencia intrafamiliar.

### Reglas para Kimün

Salen de lo anterior. Su diseño en la app está en `PLAN.md` ("Protección de derechos" en Requisitos y Task 13).

1. Kimün no detecta, no diagnostica y no califica maltrato. Ofrece una red de seguridad: si una nota podría describir una posible vulneración, lo dice. El sistema nunca concluye que hubo maltrato, ni quién lo cometió, ni de qué tipo.
2. Ante la duda, avisar. Un aviso de más le cuesta a la educadora un clic. Uno de menos puede dejar a un niño sin protección. Aun así, el aviso no reemplaza la obligación de las personas: que Kimün no avise no significa que no pase nada.
3. Lo marcado no es evidencia de aprendizaje. No genera observaciones de aprendizaje y no entra en la propuesta de nivel, la cobertura, las alertas de rezago, la tabla del curso, la vista del jardín ni la medición de calidad.
4. Las agresiones entre niños, los accidentes, el juego simbólico y la pobreza no se marcan por sí solos.
5. La IA no indaga. Si la nota se marcó, el modelo no pregunta quién, cómo ni cuándo. Esas preguntas empujan a interrogar al niño, que es lo que el protocolo prohíbe.
6. El aviso le dice a la educadora qué hacer según el protocolo de Integra: informar a la directora y no interrogar al niño. No muestra otro texto que el de la nota, no nombra al presunto responsable, no usa "abuso" ni "maltrato" como etiqueta y no adjetiva al niño.
7. El aviso no puede depender de una sola persona, por el contexto intrajardín: lo ve la educadora del curso y también la directora del jardín.
8. Resguardo de la intimidad: el texto marcado lo ven solo esas personas. No aparece en listados, contadores con detalle, registros del servidor ni exportaciones.
9. Kimün no reemplaza el registro oficial del protocolo. La educadora registra el caso en el instrumento de Integra. La app guarda la nota tal como se escribió, sin resumirla ni reescribirla, porque el relato textual importa.
10. El niño sigue en Kimün como siempre: su ficha, sus niveles y sus otras observaciones no cambian, y nada en la app revela que hubo un aviso. Su continuidad en el jardín es un factor protector.

## Consideraciones para Kimün

Lo que un agente debe tener presente al aplicar la malla en la app. Cada punto se apoya en una cita verificada del PDF.

1. Los OA son metas de fin de tramo (2 años), no de año ni de mes. No esperar que un niño "cumpla" todos los OA de Transición en un semestre.
   > Se enuncian desde lo que se espera al final de cada nivel, es decir abarcando tramos curriculares de dos años. (p. 40)

2. Un OA se evidencia de muchas formas distintas. El modelo que etiqueta observaciones con OA debe interpretar la conducta, no buscar coincidencia textual con el enunciado del OA.
   > el párvulo que ha adquirido el aprendizaje especificado en alguno de los objetivos de estas Bases, lo puede evidenciar a través de diferentes desempeños concretos. (p. 40)

3. La educadora concluye; el sistema solo propone con evidencia. Es exactamente el flujo de las Bases.
   > Reunidas las evidencias, el o la educadora debe construir una conclusión evaluativa acerca del desempeño del párvulo... (p. 111)

4. El nivel esperado es una referencia blanda, no un umbral rígido. Las alertas de rezago deben redactarse como sugerencias de revisión.
   > ...orienta los periodos óptimos, pero en ningún caso implica limitar las expectativas de progreso de los párvulos que no se ajustan a ellos. (p. 42)
   > ...sin juicios perentorios... (p. 112)

5. Un OA de nivel educativo adyacente (Medio o Básica) no es "fuera de rango": las Bases permiten seleccionar OA de niveles adyacentes para la inclusión. Si una observación de Transición calza mejor con un OA de Medio, no debe marcarse como error.
   > ...se pueden seleccionar Objetivos de Aprendizaje de un nivel diferente al del grupo o curso de párvulos... (p. 43)

6. Los núcleos de Desarrollo Personal y Social (IA, CC, CM) son transversales: aparecen de forma permanente y una observación casi siempre toca alguno. Es esperable que IA, CC y CM reciban mucha evidencia.
   > el Ámbito de Desarrollo Personal y Social adquiere un carácter transversal... sean visibilizados de manera permanente en todas las acciones educativas... (p. 38)

7. La evidencia válida es cotidiana y multimodal (fotos, audios, observaciones). Respalda el diseño de captura de Kimün (texto, foto, audio).
   > Son múltiples las formas de recogida de información (por ejemplo, fotografías, grabaciones, observaciones)... no es imprescindible construir situaciones especiales ni momentos formales de evaluación. (p. 110)

8. Separar lo observado de la interpretación es coherente con la documentación pedagógica de las Bases (recoger ideas, anécdotas, conflictos). Refuerza la regla de Kimün de separar la cita literal de la interpretación de la educadora.
   > ...un proceso riguroso de observación, documentación e interpretación de las diversas experiencias... (p. 111)

9. El nivel debe decidirse por la conducta y la progresión, no por cantidad de observaciones. Las Bases no fijan mínimos de evidencia; piden una conclusión sobre la distancia entre lo que el niño hace y el OA (p. 111). (Integra lo confirma por otra vía.)

10. La cobertura equilibrada de los 8 núcleos tiene respaldo curricular: la planificación debe cubrir todos los núcleos. Esto apoya el resumen de la quincena de Kimün, que destaca los núcleos sin observaciones.
    > el norte de la planificación ha de encontrarse siempre en la implementación equilibrada de los ocho núcleos y de sus correspondientes Objetivos de Aprendizaje. (p. 104)

11. La cantidad de 8 núcleos y 3 niveles es la de las Bases, pero la app no debe asumirla fija: Integra apunta a 10 núcleos y la cantidad de niveles de rúbrica (hoy 8) puede cambiar (ver PLAN.md). Las Bases son la fuente de los OA oficiales de los 8 núcleos; si el alcance se amplía a Sala Cuna y Medio, sus OA están aquí (secciones por núcleo).

12. Los OA que la app carga hoy son solo los 85 de Transición. Las conductas observables por OA (NT1/NT2) no están en las Bases: vienen del Programa Pedagógico de Transición. Las Bases dan el "qué" (OA por tramo); la rúbrica de Integra da el "cuánto" (niveles por núcleo).

13. Una nota puede describir una posible vulneración de derechos (un relato del niño, marcas, negligencia, prácticas de un adulto). Eso no es evidencia de aprendizaje y no se etiqueta con OA, aunque toque IA, CC o CM: se marca para que la educadora y la directora activen el protocolo de Integra. Las agresiones entre niños sí son observaciones de convivencia. Definiciones y reglas en el [anexo de protección de derechos](#anexo-protección-de-derechos-y-vulneraciones).
   > a ser protegido de toda forma de maltrato y de injerencias arbitrarias en sus vidas privadas (p. 21)

---

## Verificación de los 206 OA

Verificación hecha con un script sobre el texto extraído del PDF (`pdftotext -layout`), separando páginas por el carácter form feed y usando el mapeo página impresa = página PDF − 2.

- Conteo total extraído: 206 OA. Coincide con la tabla de `hallazgos-bases-curriculares.md` (50 Sala Cuna + 71 Medio + 85 Transición).
- Conteo por núcleo y nivel (extraído = esperado en todos los casos):

| Sigla | Sala Cuna | Medio | Transición | Total |
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

- Presencia literal: los 206 OA aparecen literales en el texto extraído del PDF (206/206), normalizando espacios y uniendo los guiones de corte de línea.
- Cruce con el catálogo de Transición (`datos/curriculo_transicion.json`): los 85 OA de Transición coinciden salvo diferencias cosméticas (el JSON escribe "TIC" donde el PDF dice "TICs"; y algunos espacios alrededor de las barras "/"). El texto de esta enciclopedia respeta la forma literal del PDF ("TICs").
- Nota de extracción: una sola salvedad en el parseo automático inicial (PM Medio OA 7 y 8 se fundían porque el OA 7 termina en "hasta el 10." y el parser lo confundía con un ítem numerado); se verificó la página 98 del PDF y se corrigieron a mano. El resto se extrajo sin incidentes. No hubo páginas ilegibles ni tablas o esquemas que impidieran leer el contenido relevante (el diagrama de componentes de la p. 36 es decorativo; su contenido está en las definiciones de las pp. 37–44).

### Verificación de cobertura y literalidad (texto ampliado)

Al ampliar las secciones de prosa (introducción, Capítulo 1 completo, partes generales del Capítulo 2, introducción y orientaciones de cada ámbito y núcleo, y Capítulo 3 completo) se corrió un script de verificación sobre el texto extraído del PDF (`pdftotext`), separando páginas por form feed, con el mapeo página impresa = página PDF − 2, normalizando a NFC, pasando a minúsculas y uniendo los guiones de corte de línea.

- Cobertura por 6-gramas (fracción de 6-gramas de cada página impresa presentes en el archivo). Casi todas las páginas de prosa pasaron de 0,0–0,5 a 0,79–0,99. Páginas que siguen bajo 0,6, con su justificación:
  - pp. 10, 11, 12, 13 (0,31–0,55): páginas a dos columnas. El extracto de `pdftotext` entrelaza ambas columnas línea por línea, de modo que sus 6-gramas contiguos cruzan de una columna a la otra y no calzan con la reconstrucción en orden de lectura. Se comprobó que el 90–100 % de las palabras de cada una de esas páginas sí está en el archivo (cobertura por unigramas), es decir, el texto está completo y literal; lo que baja el puntaje es el artefacto de columnas del extractor, no una omisión.
  - pp. 19, 35, 36, 45, 65, 79, 101 (0,00–0,25): páginas de portada de capítulo o de sección y el diagrama decorativo de componentes de la p. 36 (entre 10 y 204 palabras, en su mayoría títulos y rótulos del diagrama). No tienen prosa sustantiva que transcribir; el contenido del diagrama de la p. 36 está desarrollado en las definiciones de las pp. 37–44.
  - pp. 50, 97 (0,56–0,59): páginas de tablas de OA (`IA` Sala Cuna; `PM` Medio). Las tablas de los 206 OA se mantienen intactas por indicación; el texto de los OA está literal, pero el breve encabezado/nivel de la página rebaja el puntaje de 6-gramas.
- Literalidad de los bloques citados: de 347 bloques citados (`> …`), 341 aparecen literales en el PDF de forma contigua o separados únicamente por un pie/encabezado de página. Los 6 restantes provienen de las páginas a dos columnas (pp. 10–13): se verificó palabra por palabra que todo su contenido está en esas páginas (0 palabras ausentes), por lo que también son literales; solo el entrelazado de columnas del extractor impide verlos como una cadena contigua.
- Los 206 OA no se tocaron: tras guardar una copia previa de las filas de las tablas, se comparó y las 206 filas quedaron idénticas carácter a carácter, y los 206 identificadores siguen presentes.
