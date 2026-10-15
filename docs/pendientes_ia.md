# Pendientes del pipeline de IA

## Task 10: caché del prompt de separación

- Hoy cada nota envía unos 9.500 tokens de entrada, casi todos del catálogo de OA.
- En `kimun/registro/ia/prompts/separacion.md`, la fecha de captura y la lista del curso van antes del catálogo. Como cambian en cada nota, Bedrock no puede cachear la parte más grande del prompt.
- Propuesta: mover el catálogo al principio del system prompt, agregar un `cachePoint` después de él y dejar la fecha y la lista del curso al final.
- Medir latencia y costo antes y después con `scripts/probar_separacion.py`, y confirmar que los resultados del set `datos/eval/notas_separacion.json` no empeoran.
