# Log de trabajo — Desafío Integra E-1

**Autor:** Fabián Pereira
**Fecha:** 14 de octubre de 2026, 17:53 (hora de Santiago, UTC−3)
**Contexto:** AWS Breaking Barriers Chile 2026 · Hackatón de IA Generativa · 14 al 16 de octubre de 2026, Universidad de Chile
**Desafío:** 1 — "IA para el Desarrollo Infantil: de la Observación a la Acción" (Fundación Integra)

---

## 1. El desafío

Las educadoras de Integra registran observaciones de los niños y niñas en formatos dispersos (notas adhesivas, cuadernos, fotos, audios, videos) y luego deben sistematizarlas y evaluarlas frente a una rúbrica. Esto les toma en promedio **4 horas semanales** (10 % de su jornada, más de 11.000 horas semanales a nivel institucional), tiempo que no pasan en la sala.

- **Objetivo:** una herramienta que tome ese material heterogéneo, lo sistematice y apoye la evaluación de cada niño o niña, resguardando la información sensible.
- **KPI estrella:** reducir el tiempo de documentación de 4 horas a 0 horas semanales.
- **Beneficio de fondo:** identificar rezagos a tiempo y potenciar el desarrollo.
- **Contacto de la contraparte:** Lissette Saavedra, Dirección Ejecutiva (lsaavedrag@integra.cl).

## 2. Materiales revisados

| Material | Contenido relevante |
|---|---|
| Presentación del desafío (`.pptx` y `.pdf`) | Rúbrica de 8 niveles, KPI, fotos de registros reales de educadoras |
| `dataset_e1_publico.zip` | Dataset sintético: 500 niños/as, 2.950 observaciones, 90 conductas observables, ruta de 9 niveles |
| Referente Curricular Integra 2025 (PDF, 110 páginas) | Marco pedagógico y de evaluación de Integra |
| Búsqueda web | Instrumentos públicos de Integra (IEA, PLAEP-R, Battelle) |

## 3. Hallazgos sobre la rúbrica de 8 niveles

- **Lo único disponible** (diapositiva 7): 10 núcleos de aprendizaje (ejemplo: Identidad y Autonomía), 8 niveles por núcleo, 3 niveles educativos (sala cuna, nivel medio y transición).
- **Nombres de los niveles:** 1 Comenzando, 2 Explorando, 3 Desarrollando, 4 Afianzando, 5 Integrando, 6 Ampliando, 7 Consolidando, 8 Profundizando. Se presentan como una escalera ascendente continua.
- **No están disponibles:** descriptores, conductas observables, rangos de edad ni la lista de los 10 núcleos.
- **No es pública:** no aparece en internet ni en el Referente Curricular 2025. Parece ser un instrumento nuevo, no publicado.
- **Precedente público (IEA, versión 2018):** 8 núcleos de las Bases Curriculares; indicadores calificados en 3 niveles (incipiente, en desarrollo, adquirido); nivel por núcleo (Inicial, Intermedio, Final) según **umbrales** (por ejemplo, Final con 8 o más indicadores adquiridos y ninguno incipiente). Lo aplica el equipo de aula 3 veces al año (abril, agosto y noviembre).
- **Otros instrumentos:** PLAEP-R (prueba estandarizada, muestral, bienal, aplicada por evaluadores externos) y Battelle (usado en 2021).

## 4. Hallazgos del dataset

- Usa una **ruta sintética de 9 niveles** (0 a 36 meses) con **5 dominios** (motor grueso, motor fino, lenguaje y comunicación, socioemocional, cognitivo), distinta de la rúbrica real de 8 niveles.
- Cada nivel × dominio tiene 2 conductas observables (90 en total), redactadas como evidencia positiva.
- Cada observación tiene un nivel estimado global y vincula de 1 a 5 conductas **de ese mismo nivel**.
- No hay archivos multimedia reales; las notas breves son 6 frases genéricas.
- La ausencia de registro no implica ausencia de aprendizaje (lo declara el propio dataset).

### ¿Se puede entrenar un modelo para predecir el nivel?

| Enfoque (validación cruzada agrupada por niño/a) | Acierto exacto |
|---|---:|
| Regla de edad de `ruta_niveles.csv` | 98,4 % |
| Árbol de decisión solo con edad | 98,5 % |
| Edad + nivel anterior | 98,8 % |
| Metadatos sin edad (formato, nota, rol, etc.) | 12,6 % (bajo la línea base de 15 %) |
| Nivel de las conductas vinculadas | 100 % (circular) |
| Texto de una conducta nueva → nivel (TF-IDF) | 15,6 % |

**Conclusión:** el nivel es casi una función de la edad. Las únicas 45 desviaciones son bajas de un nivel que parecen ruido inyectado (bajas aisladas que se revierten) y no tienen señal predictiva. Un modelo entrenado aquí aprendería "nivel = edad" y **nunca detectaría un rezago**. No es viable ni útil entrenar un clasificador de nivel con este dataset.

## 5. Hallazgos del Referente Curricular 2025

- Evaluación **diversificada y auténtica**: recolección de información (observación y registro cualitativo, el juego como instancia privilegiada), emisión del juicio valorativo por el equipo, y toma de decisiones.
- **Documentación pedagógica:** apuntes, audio, video, fotos y producciones, sin una estructura fija.
- **Aprendizajes emergentes:** aprendizajes no planificados que luego se asocian a un Objetivo de Aprendizaje.
- El juicio evaluativo es cualitativo, reflexivo y **del equipo educativo**.

## 6. Planificación del producto

### Propuesta del equipo

App web móvil donde las educadoras ingresan información en formato de chat. La app cataloga cada registro en el perfil del niño o niña correspondiente y ofrece dashboards.

### Cuello de botella

Una vez extraídos los datos, cómo transformarlos en una recomendación o plan para cada niño o niña, sin reglas oficiales de evaluación y sin un modelo predictivo viable.

### Decisión recomendada: sugerir a partir de evidencia, no predecir

No delegar el 100 % del juicio a la educadora sin apoyo: si la app solo resume, ella todavía debe cruzar todo con la rúbrica, que es la parte que más tiempo consume. En cambio, la app muestra **qué conductas de la rúbrica tienen evidencia y cuáles no**, sugiere con reglas simples y visibles, y **la educadora siempre tiene la última palabra**.

### Escalera de automatización

| Peldaño | Qué hace la app | Riesgo |
|---|---|---|
| 1. Organizar | Asocia cada registro al niño/a correcto, con fecha, contexto y archivo de origen | Muy bajo |
| 2. Etiquetar evidencia | El LLM vincula el registro con conductas del catálogo y cita el fragmento de respaldo; la educadora acepta o corrige con un toque | Bajo |
| 3. Cobertura y vacíos | Matriz por núcleo × nivel: con evidencia, sin evidencia, evidencia antigua | Bajo |
| 4. Sugerir nivel | Regla explícita y configurable (por ejemplo, nivel más alto con al menos N conductas confirmadas en dos observaciones distintas) | Medio (mitigado por transparencia) |
| 5. Próximos pasos | Experiencias y observaciones pendientes basadas en las conductas del nivel siguiente | Medio (mitigado si se basa en el catálogo) |

**Prioridad:** hacer muy bien los peldaños 1 a 3; presentar 4 y 5 como sugerencias claramente marcadas.

### Principios de diseño

1. **La rúbrica como dato, no como código.** Catálogo configurable (núcleo/dominio, nivel, conducta, edad orientativa). Hoy: 90 conductas y 9 niveles del dataset. Cuando Integra entregue la rúbrica real, se reemplaza la tabla sin cambiar la app.
2. **Reglas de umbral, como el IEA.** Integra ya decide niveles con umbrales; la regla de cobertura sigue esa lógica.
3. **Evidencia, no diagnóstico.** Ejemplo: "No hay registros de 3 conductas de motor fino esperadas para su edad; última evidencia hace 6 semanas", en vez de "tiene rezago".
4. **Los vacíos se convierten en sugerencias de observación** ("esta semana podrías observar si apila 4 bloques").
5. **Experiencias para el nivel siguiente**, generadas a partir del catálogo y alineadas con el Referente Curricular (juego, exploración, ambientes).
6. **Sugerencias grupales:** si varios niños/as comparten un vacío, proponer una experiencia para el grupo.
7. **Trayectorias suavizadas:** no bajar el nivel sugerido por una sola observación; exigir confirmación.
8. **Siempre mostrar el porqué:** cada sugerencia enlaza a los registros que la respaldan; las correcciones de la educadora se guardan para calibrar umbrales a futuro.
9. **La edad es referencia, no predictor:** el nivel esperado por edad sirve para contrastar, no para asignar.

### Flujo de demo propuesto

1. La educadora escribe o dicta: "Hoy Maite apiló cuatro bloques sola y pidió agua diciendo 'más agua'".
2. La app identifica a la niña y propone dos conductas: torre de 4 bloques (motor fino) y combinación de dos palabras (lenguaje). La educadora confirma con un toque.
3. El perfil actualiza la matriz de cobertura y el nivel sugerido por dominio, con su evidencia.
4. La sección de próximos pasos propone qué observar y qué experiencia ofrecer.

### Validación del peldaño crítico (vinculación)

Generar notas sintéticas a partir de las 90 conductas del dataset (reescritas al estilo de una educadora, con variaciones, errores y varias conductas por nota) y medir cuántas veces la app recupera la conducta correcta. Esto da una métrica concreta de precisión para el jurado.

## 7. Próximos pasos

- [ ] Pedir a la contraparte de Integra la rúbrica operativa de 8 niveles (aunque sea un núcleo completo) y la lista de los 10 núcleos.
- [ ] Definir el esquema del catálogo de rúbrica configurable y cargar las 90 conductas del dataset.
- [ ] Construir el conjunto de prueba de notas sintéticas.
- [ ] Prototipar el paso de vinculación (LLM + catálogo) y medir su precisión.
- [ ] Diseñar el perfil del niño/a: matriz de cobertura, nivel sugerido con evidencia y próximos pasos.
- [ ] Preparar el argumento de escalabilidad para el pitch (rúbrica intercambiable).

## 8. Fuentes

- [IEA Medio Mayor (copia en PDFCoffee)](https://pdfcoffee.com/iea-mediomayor-5-pdf-free.html)
- [IEA Transición Mayor 2023 (copia en Studocu)](https://www.studocu.com/cl/document/universidad-del-bio-bio/didactica-general/iea-transicion-mayor-instrumento-de-evaluacion-para-nivel-transicion/102054935)
- [Informe final de evaluación de programas, Dipres](https://www.dipres.gob.cl/597/articles-205701_informe_final.pdf)
- [PLAEP-R (Prezi)](https://prezi.com/wl60jauu-1wf/plaep-r/)
- [Fundación Integra: evaluación 2021 con Battelle](https://integra.cl/fundacion-integra-llama-a-retornar-a-los-jardines-infantiles-para-recuperar-aprendizajes/)
- [Reporte Integra 2025](https://integra.cl/wp-content/uploads/2026/04/Reporte_Integra_2025.pdf)
