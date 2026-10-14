# Plan de construcción: servicio de IA (frente B)

> Para Kiro. Leer antes `CONTEXTO_PROYECTO_CLAUDE.md` (secciones 5, 6, 7, 7.5 y 8) y `docs/investigacion_servicios.md`.
> Avanzar fase por fase. Al terminar cada fase, mostrar el resultado de sus criterios de aceptación y esperar confirmación antes de seguir.

---

## Objetivo

Construir un **servicio independiente** que convierta capturas (texto, audio, foto) en observaciones estructuradas según el contrato de la sección 5.3. El stack de la app todavía no está definido, así que el servicio:

- Es una **librería Python** (`pipeline/`) que se puede importar directamente si el backend es Python.
- Tiene una **API HTTP delgada** (`api/`, FastAPI) para que cualquier backend la llame por red.
- **No tiene base de datos propia.** Recibe lo que necesita en cada llamada y devuelve el resultado; guardar borradores es trabajo de la app.

Si después cambia el stack, solo se ajusta la capa `api/`. La lógica de `pipeline/` no cambia.

---

## Decisiones fijas

| Tema | Decisión |
|---|---|
| Lenguaje | Python 3.12, boto3, FastAPI, pydantic, pytest |
| Región | `us-east-1` |
| Modelo de extracción | `us.anthropic.claude-sonnet-4-6` |
| Modelo de respaldo y tareas baratas | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |
| API de Bedrock | Converse con tool use forzado (`toolChoice.tool`) |
| Audio | Amazon Transcribe batch `es-US` vía S3 |
| Dataset | `Dataset/datos_publicos/` (solo lectura) |
| Configuración | Variables de entorno con valores por defecto en `pipeline/config.py` y un `.env.example` |

---

## Estructura de archivos

```
contrato/
  salida_pipeline.schema.json     # salida de extracción (sección 5.3)
  entrada_extraccion.schema.json  # request de /extraer
pipeline/
  __init__.py
  config.py
  catalogo.py        # carga rúbrica y niños, edad, nivel esperado, filtro de catálogo
  prompt.py          # system prompt y mensajes
  bedrock.py         # cliente Converse, reintentos, métricas, prompt caching si aplica
  validacion.py      # reglas de validación del contrato
  extraccion.py      # extraer(...)
  transcripcion.py   # Transcribe (fase 4)
  imagen.py          # preparación de imágenes (fase 5)
  sugerencias.py     # qué observar e informe familia (fase 7)
  cli.py
api/
  main.py            # FastAPI
  trabajos.py        # cola en memoria para procesos asíncronos
eval/
  generar_casos.py
  correr_eval.py
  casos/             # casos generados (json)
  resultados/        # métricas (json)
tests/
research/samples/    # audios e imágenes de prueba (no versionar media real)
```

---

## Interfaces (contrato con la app)

### Función principal
```python
def extraer(
    texto: str | None,
    ids_ninos: list[str] | None = None,
    actividad: str | None = None,
    imagenes: list[bytes] | None = None,
    ninos: list[dict] | None = None,      # [{id_nino, nombre, fecha_nacimiento}] si la app los manda
    fecha_referencia: date | None = None,
    id_captura: str | None = None,
) -> dict  # {"resultado": <salida 5.3>, "metricas": {...}}
```
- Si `ninos` no viene, se buscan en `ninos.csv` por `ids_ninos`. Los nombres son ficticios.
- `metricas`: `modelo`, `intentos`, `tokens_entrada`, `tokens_salida`, `latencia_ms`, `errores_validacion`.

### API HTTP
| Método | Ruta | Entrada | Salida |
|---|---|---|---|
| GET | `/salud` | | `{"ok": true, "modelo": "..."}` |
| GET | `/catalogo` | | manifestaciones y ruta de niveles |
| POST | `/extraer` | JSON: `id_captura`, `texto`, `ids_ninos`, `actividad`, `imagenes_base64`, `ninos`, `fecha_referencia` | `{"resultado": ..., "metricas": ...}` (síncrono) |
| POST | `/capturas/audio` | multipart: `audio` + mismos campos que `/extraer` | `{"id_trabajo": "..."}` (asíncrono) |
| GET | `/trabajos/{id}` | | `{"estado": "pendiente|transcribiendo|extrayendo|listo|error", "transcripcion": ..., "resultado": ..., "metricas": ..., "error": ...}` |
| POST | `/sugerencias/que-observar` | `id_nino` + observaciones aprobadas | lista de 1 a 3 manifestaciones sugeridas con motivo |
| POST | `/informes/familia` | `id_nino` + observaciones aprobadas | texto en lenguaje simple |

Los trabajos se guardan en memoria (diccionario). Es suficiente para el MVP; si se reinicia el servicio se pierden.

---

## Fases

### Fase 0. Base del proyecto (15 min)
- Estructura de carpetas, `requirements.txt`, `config.py`, `.env.example`, `README.md` con cómo correr.
- `contrato/salida_pipeline.schema.json` a partir del schema usado en la prueba 3a de la investigación.

**Aceptación:** `python -c "import pipeline"` funciona y `pytest` corre (aunque no haya tests aún).

### Fase 1. Catálogo y reglas (30 min)
- `catalogo.py`: cargar `manifestaciones.csv`, `ruta_niveles.csv`, `ninos.csv`.
- `edad_meses(fecha_nac, fecha)` con la fórmula del diccionario de datos.
- `nivel_esperado(edad)` según sección 6.1.
- `catalogo_filtrado(edad)` = niveles esperado ±2; completo si no hay edad.

**Aceptación:** tests unitarios con casos de borde (cumpleaños el mismo día, edad > 36 meses, edad 0). NINO-00002 al 2026-10-13 da nivel esperado 8.

### Fase 2. Extracción de texto (1 h, la más importante)
- `prompt.py` según sección 7.2: solo IDs del catálogo, citar evidencia, no inventar, no inferir emociones ni diagnósticos, español neutro, `descripcion_nino = null` si el niño está identificado, y si un niño mencionado no está en la lista, dejar `id_nino = null` con su descripción y una advertencia.
- `bedrock.py`: Converse con tool use forzado, `temperature=0`, `maxTokens` configurable. Investigar si Converse permite prompt caching con este modelo; si sí, cachear system prompt y catálogo; si no se puede verificar, dejarlo anotado.
- `validacion.py`: validar contra el JSON Schema; descartar IDs inexistentes; recalcular `nivel_sugerido` como el máximo nivel de las manifestaciones; verificar `id_nino`; forzar `descripcion_nino = null` si hay `id_nino`.
- `extraccion.py`: si falla la llamada o la validación deja la salida inválida, un reintento con el modelo de respaldo.
- `cli.py`: `python -m pipeline.cli --texto "..." --ninos NINO-00002`.

**Aceptación:**
1. Nota de Simón (la de la prueba 3a) devuelve `MAN-L08-MF-01` y `MAN-L08-SE-02`, nivel 8, `descripcion_nino = null`.
2. Nota ambigua "los niños jugaron harto rato en la sala" devuelve `observaciones` sin manifestaciones o vacía, con advertencia.
3. Nota con dos niños, uno sin ID ("Simón armó una torre y la Sofía pateó la pelota"), devuelve dos observaciones, la de Sofía con `id_nino = null`.
4. Tests de validación sin llamar a Bedrock (respuestas simuladas).

### Fase 3. API HTTP (30 min)
- `api/main.py` con `/salud`, `/catalogo`, `/extraer`.
- CORS abierto en desarrollo.
- Documentación automática en `/docs`.

**Aceptación:** `uvicorn api.main:app` levanta y `curl -X POST /extraer` con la nota de Simón devuelve el mismo resultado que el CLI.

### Fase 4. Audio con Transcribe (1 h)
- **Pedir confirmación antes de crear el bucket.** Bucket privado, bloqueo de acceso público, cifrado, regla de ciclo de vida que borre objetos después de 1 día.
- `transcripcion.py`: subir audio, lanzar job `es-US`, esperar con polling, leer el texto, borrar el audio y el job al terminar.
- Evaluar vocabulario personalizado (nombres ficticios, "tía", "bloques", "sala cuna"). Si toma más de 20 min, dejarlo para después.
- `/capturas/audio` asíncrono con `/trabajos/{id}`.
- **Medir latencia** (subida, transcripción, extracción) con 3 audios de `research/samples/`.
- Si la transcripción tarda más de ~30 s, probar como plan B Voxtral Small con `AudioBlock` en Converse y comparar calidad y latencia.

**Aceptación:** un audio grabado por el equipo pasa de punta a punta y el informe de latencias queda en `docs/latencias_audio.md`.

### Fase 5. Imagen (45 min)
- `imagen.py`: redimensionar a un máximo de 1568 px por lado y comprimir a JPEG bajo 3,75 MB.
- `extraer(..., imagenes=[...])` manda texto más imagen en la misma llamada.
- Probar con fotos de **productos** de actividades (torre de bloques, dibujo, clasificación de objetos) sin caras, y con foto de un post-it escrito a mano.

**Aceptación:** foto de una torre de bloques + texto "Simón hizo esto" devuelve `MAN-L08-MF-01`; foto de post-it legible se transcribe y extrae.

### Fase 6. Evaluación (1 h)
- `eval/generar_casos.py`: tomar ~60 observaciones del dataset, estratificadas por nivel y dominio. Para cada una, generar con Haiku una nota realista de tía en lenguaje cotidiano chileno-neutro, **sin copiar el texto del catálogo**, mencionando al niño con un nombre ficticio. Guardar `nota`, `id_nino`, `manifestaciones_reales`, `nivel_real`.
- Agregar 10 casos ambiguos (sin evidencia) y 10 con dos niños.
- `eval/correr_eval.py`: correr `extraer()` sobre los casos y calcular precisión, recall y F1 de manifestaciones, exactitud de nivel (exacto y ±1), exactitud por dominio, tasa de "no inventar" en los ambiguos, latencia y costo promedio.
- Opcional: comparar Sonnet 4.6 vs Haiku 4.5.

**Aceptación:** `eval/resultados/` con un JSON y un resumen en Markdown listo para poner en el pitch.

### Fase 7. Extras con IA generativa (si hay tiempo)
- `/sugerencias/que-observar`: dados los dominios sin datos o atrasados, sugerir 1 a 3 manifestaciones del catálogo a observar en la próxima actividad, con una idea de actividad.
- `/informes/familia`: resumen en lenguaje simple y positivo, solo con observaciones aprobadas, sin diagnósticos ni comparaciones con otros niños.

### Fase 8. Video (solo si todo lo anterior está estable)
- ffmpeg: separar audio → Transcribe; extraer 3 a 5 fotogramas → extracción con imágenes.

---

## Reglas generales

- Nunca modificar el dataset.
- Solo datos sintéticos y muestras grabadas por el equipo. No subir datos reales de niños.
- No usar reconocimiento facial.
- No registrar en logs el texto completo de las capturas fuera del modo debug.
- Toda llamada a Bedrock registra modelo, tokens y latencia.
- Pedir confirmación antes de crear recursos AWS que cuesten o queden corriendo, y documentar cómo borrarlos.
- Si algo del contrato no calza con lo que necesita la app, **avisar antes de cambiarlo**: el schema es compartido con el resto del equipo.

---

## Orden sugerido si falta tiempo

Fases 0, 1, 2 y 3 hoy o mañana temprano (con eso el resto del equipo ya puede integrar). Luego 4 (audio) y 6 (evaluación), que son lo que más pesa en la demo y el pitch. La 5 (imagen) es rápida una vez que existe la 2. La 7 y la 8 son opcionales.
