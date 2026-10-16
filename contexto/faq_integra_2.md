# Respuestas de Integra a nuestras preguntas (correo)

Transcripción de un correo con nuestras preguntas al equipo de Integra. Las respuestas venían destacadas en amarillo, intercaladas en el texto de las preguntas; aquí van separadas. Se corrigieron errores de tipeo evidentes ("tb" → "también", "levanta runa" → "levantar una").

<!-- indice:inicio -->
## Índice

Generado por `scripts/indice_contexto.py`. Cada entrada indica sus líneas en este archivo; lee solo las que necesites.

- [1. Alcance de la herramienta](#1-alcance-de-la-herramienta) · líneas 19–28
- [2. Rúbrica](#2-rúbrica) · líneas 30–34
- [3. Cómo se decide el nivel](#3-cómo-se-decide-el-nivel) · líneas 36–40
- [4. Pasos a seguir](#4-pasos-a-seguir) · líneas 42–46
- [5. Rezago y frecuencia de actualización](#5-rezago-y-frecuencia-de-actualización) · líneas 48–56
- [Qué cambia para nosotros](#qué-cambia-para-nosotros) · líneas 58–72
- [Pendiente con Integra](#pendiente-con-integra) · líneas 74–76
<!-- indice:fin -->

## 1. Alcance de la herramienta

**Pregunta:** ¿Qué tanto debería hacer la herramienta? Nuestra idea es que organice las observaciones y proponga un nivel con la evidencia que lo respalda, dejando siempre la decisión final a la educadora. ¿Les parece adecuado o prefieren que solo organice y resuma la información, sin sugerir niveles?

**Respuesta:**

- Organizar y proponer un nivel con su evidencia: "eso está perfecto".
- Que la educadora pueda modificar o ajustar el nivel: "también está perfecto".
- "Con niveles sí o sí, pero ajustables por ellas. Ideal que se pueda ver la evolución del niño de manera individual en el tiempo. Así como también poder identificar en el grupo-curso (sala de clase) en qué nivel está la mayoría de los niños y levantar alarma si tengo niños rezagados."
- "También sería interesante analizar a nivel de jardín cómo está el desarrollo. Por ejemplo, si tengo 3 salas de niveles medios, y hay 2 que tienen a los niños en promedio en nivel 6 y la otra tiene a los niños en promedio en nivel 3, significa que hay un grupo curso que está más rezagado y sería importante levantar una alerta ahí también para la directora."

## 2. Rúbrica

**Pregunta:** ¿Es posible acceder a la rúbrica completa de la presentación, con las conductas observables de cada nivel y núcleo? El dataset que recibimos usa una ruta de 9 niveles y 5 dominios para niños de 0 a 36 meses, distinta a la de 8 niveles y 10 núcleos de la presentación, por lo que quisiéramos saber cuál deberíamos usar.

**Respuesta:** "La rúbrica completa está siendo ajustada en la institución, por eso solo les pasamos el ejemplo de un núcleo. Pero es importante que la herramienta esté pensada en que serán 10 núcleos. Actualmente tenemos 8 niveles, pero existe la posibilidad de que terminen siendo 9, por lo que es importante que ese parámetro en la herramienta también sea ajustable."

## 3. Cómo se decide el nivel

**Pregunta:** ¿Cómo se decide hoy el nivel de un niño o niña? Por ejemplo, cuántas observaciones se necesitan y si el nivel se asigna por núcleo o de forma global.

**Respuesta:** "Más que número de observaciones, se decide según la conducta observable, es decir, los avances del niño (mándenme un WhatsApp y les mando un audio donde les puedo explicar con un ejemplo). Recuerden que las observaciones las puede hacer la educadora de párvulo (hay 1 por sala) o las asistentes de párvulo (hay 1 cada 7 niños en la sala)."

## 4. Pasos a seguir

**Pregunta:** Además del nivel, ¿sería útil que la herramienta sugiriera pasos a seguir para cada niño, como conductas a observar en las próximas actividades?

**Respuesta:** "En la rúbrica que estamos trabajando como institución estamos incluyendo eso. Sin embargo, en la versión que les pasamos no está eso aún. Pero sería genial que la herramienta incorporara la posibilidad de a futuro poder cargar eso también. Sería un tremendo plus."

## 5. Rezago y frecuencia de actualización

**Pregunta:** ¿A partir de qué diferencia entre el nivel esperado y el observado se considera que hay rezago y se evalúa una derivación?

**Respuesta:** "Compararía el rezago con sus pares del nivel, con la lógica que les comenté en la pregunta 1."

**Pregunta:** ¿Y cada cuánto tiempo debería actualizarse la información de cada niño?

**Respuesta:** "Lo hacen todo el tiempo, a medida que van observando nuevos avances."

## Qué cambia para nosotros

| Tema | Lo que suponíamos | Lo que dice Integra | Efecto |
|---|---|---|---|
| Propuesta de nivel | La herramienta propone y la educadora decide | Confirmado | Sin cambios |
| Núcleos | 8, los de las Bases Curriculares | Serán 10 | La cantidad de núcleos es un dato de la rúbrica. La demo sigue con los 8 de las Bases, los únicos con OA oficiales, hasta tener la lista de Integra |
| Niveles | 8 fijos | 8 hoy, quizás 9 | La cantidad de niveles es un parámetro de la rúbrica. Nada en el código asume 8 |
| Rúbrica real | La pedíamos completa | Está en ajuste; solo nos pasaron el ejemplo de un núcleo | El ejemplo es IA y está en `datos/rubrica_integra.json`. Los demás núcleos siguen con la rúbrica provisoria |
| Dataset E-1 (9 niveles, 5 dominios) | Posible catálogo alternativo | Hay que pensar en 10 núcleos | No se usa como rúbrica |
| Cómo se decide el nivel | Evidencia citada, sin umbral de cantidad | Por la conducta observable y los avances, no por cantidad de observaciones | Confirma no usar un mínimo de observaciones |
| Quién observa | Solo la educadora | Educadora (1 por sala) y asistentes (1 cada 7 niños) | Las asistentes también registran. Revisar y validar niveles queda en la educadora (decisión nuestra, por confirmar) |
| Rezago | Brecha con el nivel esperado por semestre | Comparar con los pares del nivel | Se agrega la comparación con el curso. La brecha con lo esperado se mantiene como segunda señal |
| Vistas | Solo la de la educadora | También el curso completo, la evolución individual y el jardín para la directora | Distribución de niveles del curso, gráfico de evolución y vista del jardín que compara cursos del mismo nivel educativo |
| Pasos a seguir | Fuera del MVP | Vendrán en su rúbrica; quieren poder cargarlos | Campo en la rúbrica para cargarlos. No se generan con IA en el MVP |
| Actualización | Se calcula al pedirla | Continua, a medida que observan | Sin cambios |

## Pendiente con Integra

Ver "Preguntas pendientes para Integra" en `PLAN.md`.
