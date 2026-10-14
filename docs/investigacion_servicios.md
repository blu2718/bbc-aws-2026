# Investigación de servicios AWS para el pipeline de IA (us-east-1)

Fecha: 2026-10-14. Cuenta del evento ****6948, rol `WSParticipantRole` (Workshop Studio). Región: us-east-1.
Convención: **[CLI]** = verificado por AWS CLI en la cuenta. **[DOC]** = según documentación o Pricing API, no probado en la cuenta.

## 1. Resumen ejecutivo

- La cuenta tiene una allowlist IAM (`ws-bedrock-model-allowlist-policy-1`) que bloquea con deny explícito varios modelos listados (Sonnet 5.5, Haiku 5.5, Opus 5.5, Fable 5.1, GPT-6.x, Qwen, Gemma, DeepSeek V3.2). Los Claude 4.5 a 5 permitidos solo funcionan con perfil `us.` o `global.`. [CLI]
- Extracción: **Claude Sonnet 4.6 (`us.anthropic.claude-sonnet-4-6`)**. En la prueba de texto acertó las 2 manifestaciones esperadas (MAN-L08-MF-01 y MAN-L08-SE-02, nivel 8) en 3,8 s, con JSON válido según el schema. Sonnet 5 obtuvo el mismo resultado, pero fue más lento (5,3 s) y no acepta `temperature`. Conviene dejarlo como alternativa en `BEDROCK_MODEL_ID`. [CLI]
- Modelo barato: **Claude Haiku 4.5** (mismo resultado, 3,1 s, $1.1/$5.5 por 1M). Para tareas triviales de texto sirven Nova Micro y Nova Lite, pero no para la extracción: Nova Lite eligió una manifestación de nivel incoherente. [CLI]
- Audio: **Amazon Transcribe batch es-US** (necesita S3, $0.006/min). La prueba de audio está pendiente porque todavía no hay muestra.
- Foto: Claude con imagen en Converse, en la misma llamada de extracción. Video: ffmpeg (audio a Transcribe más 3 a 5 fotogramas a Claude) o Nova directo. Foto y video son investigación sin pruebas.
- **BDA no conviene para 2 días.** Es asíncrono, necesita S3 y admite un solo blueprint fijo por modalidad, lo que obliga a duplicar el catálogo y las reglas. Con Converse y tool use ya tenemos JSON validado, en una sola ruta y con el mismo código para todos los formatos.

## 2. Modelos en us-east-1 (relevantes)

`list-foundation-models` devolvió 123 modelos y `list-inference-profiles` 99 perfiles [CLI]. La columna "hola" muestra el resultado de `converse` con `maxTokens=10` [CLI]: `inputTokens/outputTokens` y la latencia `metrics.latencyMs`. Las cuotas vienen de `service-quotas list-service-quotas`, son valores aplicados a la cuenta y **no se pueden aumentar**, porque `servicequotas:RequestServiceQuotaIncrease` está denegado [CLI]. Los precios son on-demand por 1M de tokens (entrada/salida) según la Pricing API (`AmazonBedrock` y `AmazonBedrockFoundationModels`, us-east-1, consultada el 2026-10-14) [DOC]. En Claude, la línea "regional/geo" aplica a `us.` y "global" a `global.`.

| Modelo | ID que funciona | Entrada → salida | Tool use | "hola" | Cuota TPM / RPM | $ entrada / salida por 1M |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` o `global.` (el ID directo falla: on-demand no soportado) | texto, imagen → texto | Sí [CLI 3a] | OK 9/10, 845 ms | 6M / 10.000 (us. y global) | 3.30/16.50 (us.), 3.00/15.00 (global) |
| Claude Sonnet 5 | `us.anthropic.claude-sonnet-5` | texto, imagen → texto | Sí [CLI 3a]; rechaza `temperature` | OK 8/10, 984 ms | 6M / RPM no listada | 2.20/11.00 (us.), 2.00/10.00 (global) |
| Claude Sonnet 4.5 | `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (LEGACY) | texto, imagen → texto | Probable (misma familia que los modelos probados), no verificado | OK 9/10, 1330 ms | 5M / 10.000 | 3.30/16.50, 3.00/15.00 |
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | texto, imagen → texto | Sí [CLI 3a] | OK 9/10, 710 ms | 5M / 10.000 | 1.10/5.50, 1.00/5.00 |
| Claude Opus 5 | `us.anthropic.claude-opus-5` | texto, imagen → texto | Probable, no verificado; devuelve `reasoningContent` por defecto | OK 8/10, 787 ms | 30M / no listada | 5.50/27.50, 5.00/25.00 |
| Claude Opus 4.8 / 4.7 / 4.6 | `us.` o `global.` + `anthropic.claude-opus-4-8` / `-4-7` / `-4-6-v1` | texto, imagen → texto | Probable (misma familia que los modelos probados), no verificado | OK (722 a 1619 ms) | 30M (4.8 y 4.7), 3M / 10.000 (4.6) | 5.50/27.50 (4.8, 4.7 y 4.6) |
| Amazon Nova Pro | `amazon.nova-pro-v1:0` o `us.` | texto, imagen, video → texto | Sí [CLI 3a] | OK 2/10, 420 ms | On-demand: 1M / 250; cross-region: 2M / 500 | 0.80/3.20 |
| Amazon Nova Lite | `amazon.nova-lite-v1:0` o `us.` | texto, imagen, video → texto | Sí [CLI 3a] | OK 2/10, 515 ms | On-demand: 4M / 2.000; cross-region: 8M / 4.000 | 0.06/0.24 |
| Amazon Nova Micro | `amazon.nova-micro-v1:0` o `us.` | texto → texto | Probable (misma familia que los modelos probados), no verificado | OK 2/10, 274 ms | On-demand: 4M / 2.000; cross-region: 8M / 4.000 | 0.035/0.14 |
| Amazon Nova 2 Lite | `us.amazon.nova-2-lite-v1:0` o `global.` (el ID directo falla) | texto, imagen, video → texto | Sí [CLI 3a] | OK 47/10, 462 ms | 8M / 2.000 | 0.33/2.75, 0.30/2.50 (global) |
| Amazon Nova 2 Sonic | `amazon.nova-2-sonic-v1:0` (stream bidireccional) | voz → voz, texto | n/a | No probado: la CLI no hace streaming bidireccional | 20 solicitudes concurrentes | voz 3.00/12.00; texto 0.33/2.75 |
| Meta Llama 4 Maverick / Scout | `us.meta.llama4-maverick-17b-instruct-v1:0` / `-scout-` | texto, imagen → texto | No verificado | OK 37/10, 307 / 267 ms | 600k / 800 | 0.24/0.97 y 0.17/0.66 |
| Meta Llama 3.3 70B | `us.meta.llama3-3-70b-instruct-v1:0` | texto → texto | No verificado | OK, pero respondió en inglés | 600k / 800 | no consultado |
| Mistral Large 3 | `mistral.mistral-large-3-675b-instruct` | texto, imagen → texto | No verificado | OK 5/10, 429 ms | 100M / 10.000 | 0.50/1.50 |
| Ministral 3 8B | `mistral.ministral-3-8b-instruct` | texto, imagen → texto | No verificado | OK 5/10, 250 ms | 100M / 10.000 | 0.15/0.15 |
| Pixtral Large | `us.mistral.pixtral-large-2502-v1:0` | texto, imagen → texto | No verificado | OK 5/10, 397 ms | **80k / 10** (muy bajo) | 2.00/6.00 |
| Voxtral Small 24B / Mini 3B | `mistral.voxtral-small-24b-2507` / `mistral.voxtral-mini-3b-2507` | voz, texto → texto | "Structured outputs" según el model card [DOC] | OK 5/10, 379 / 193 ms (solo texto) | 100M / 10.000 | 0.10/0.30 y 0.04/0.04 |
| DeepSeek R1 | `us.deepseek.r1-v1:0` | texto → texto | No verificado | OK 7/10, 374 ms | 200k / 200 | no consultado |

Modelos que **no** funcionan [CLI]:

| Modelo | Resultado |
|---|---|
| Claude Sonnet 5.5, Haiku 5.5, Opus 5.5, Fable 5.1 (directo, `us.` y `global.`) | AccessDenied: deny explícito de `ws-bedrock-model-allowlist-policy-1` |
| Claude Sonnet 4 (`us.`) | AccessDenied (fuera de la allowlist) |
| Claude Fable 5 (`us.`) | ValidationException: "data retention mode 'default' is not available for this model" |
| Nova Premier (`us.amazon.nova-premier-v1:0`) | ResourceNotFound: modelo en fin de vida |
| Qwen3 VL, Gemma 3 27B, gpt-oss-120b, GPT-6.1 Sol, DeepSeek V3.2 | AccessDenied (fuera de la allowlist) |
| TwelveLabs Pegasus 1.2 (`us.`) | Converse no lo soporta (solo InvokeModel). Está en la allowlist; no se probó con InvokeModel |

`get-foundation-model-availability --model-id anthropic.claude-sonnet-4-6` devolvió `AUTHORIZED / AVAILABLE` [CLI]. La allowlist IAM, sin embargo, manda por encima de ese resultado.

## 3. Ruta por formato

| Formato | Ruta recomendada | Alternativas | Límites clave | Riesgos |
|---|---|---|---|---|
| **Texto** | Converse con tool use forzado (`toolChoice.tool`) en Sonnet 4.6, más validación en código (IDs, nivel = máximo) | Haiku 4.5 (más barato, mismo acierto en la prueba); Sonnet 5 | Sin problema: el prompt con el catálogo completo ocupa unos 5,4k tokens | El modelo puede rellenar `descripcion_nino` con el nombre en vez de `null` (pasó en los 6 modelos). Hay que corregirlo en el prompt o normalizarlo en código |
| **Audio** (10 a 60 s, celular) | Transcribe **batch** `es-US` (o `--identify-language` con `es-US,es-ES`) → texto → extracción | Transcribe streaming (es-US, $0.01/min); Voxtral Small en Converse con `AudioBlock` [DOC]; Nova 2 Sonic | Batch: formatos AMR, FLAC, **M4A**, MP3, MP4, Ogg, **WebM** y WAV; 8 a 48 kHz; necesita S3. Cobro por segundo, sin mínimo. Free tier de 60 min/mes [DOC] | Latencia de batch con audios cortos: **no medida** (pendiente de muestra). El ruido de sala y las voces infantiles bajan la precisión. Transcribe puede guardar contenido para mejorar sus modelos y el opt-out requiere AWS Organizations, que está denegado en la cuenta. Usar solo audio sintético o grabado por el equipo |
| **Foto** (INVESTIGACIÓN SIN PRUEBAS) | La imagen como `image` en el mismo Converse de extracción con Sonnet 4.6, sumando el texto o la transcripción de contexto | Nova Lite/Pro (más baratos); Textract solo para texto impreso | Converse: hasta 20 imágenes por mensaje, 3,75 MB y 8000×8000 px por imagen, formatos png, jpeg, gif y webp [DOC]. En Nova, payload total de 25 MB o S3 [DOC] | Fotos con caras: aceptables solo como **productos** de actividades (sección 11). Las notas manuscritas en español no las lee Textract (ver abajo) |
| **Video** (INVESTIGACIÓN SIN PRUEBAS, fase 2) | ffmpeg: audio → Transcribe y 3 a 5 fotogramas → Sonnet 4.6 con imágenes | Nova Lite/Pro o Nova 2 Lite con `video` directo; BDA video; Rekognition etiquetas; TwelveLabs Pegasus 1.2 (InvokeModel) | Nova: **1 video por llamada**, hasta 25 MB en bytes o 1 GB por S3. Formatos MP4, MOV, MKV, WebM, 3GP y otros; muestreo a 1 fps; se reescala a 672×672 [DOC] | Nova no siguió bien el catálogo en la prueba de texto. Videos con caras de niños: datos sensibles. Más latencia y costo |

### Detalle por servicio

- **Amazon Transcribe.** Disponible en la cuenta: `list-transcription-jobs` y `list-vocabularies` responden vacíos [CLI]. Admite `es-US` y `es-ES` en batch y streaming, y `es-MX` con soporte parcial; no existe `es-419` [DOC](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html). El batch necesita el audio en S3; el streaming va por WebSocket o HTTP/2, no por la CLI, y exige FLAC, Ogg Opus o PCM [DOC](https://docs.aws.amazon.com/transcribe/latest/dg/how-input.html). Precio según la Pricing API (`transcribe`): $0.0001/s en batch ($0.006/min) y $0.0001667/s en streaming ($0.01/min); la página de precios indica cobro por segundo sin mínimo [DOC](https://aws.amazon.com/transcribe/pricing/). Para audios cortos de celular conviene vocabulario personalizado con nombres de niños y palabras como "tía" o "bloques" (incluido en el precio). Precisión y latencia: **no verificadas**.
- **Bedrock Data Automation (BDA).** Disponible: `list-data-automation-projects` responde con 0 proyectos y `list-blueprints --resource-owner SERVICE` lista blueprints públicos (General-Audio, Media-Search, etc.) [CLI]. Procesa documentos, imágenes, audio (transcripción y resumen) y video (resumen, escenas, texto en pantalla). Los blueprints personalizados con salida estructurada se pueden usar en las 4 modalidades, pero solo **1 blueprint por proyecto** para imagen, audio y video [DOC](https://docs.aws.amazon.com/bedrock/latest/userguide/bda-custom-output-idp.html), con un máximo de 100 campos [DOC](https://docs.aws.amazon.com/bedrock/latest/userguide/bda-limits.html). Los audios en español están soportados, de 500 ms a 240 min, en AMR, FLAC, M4A, MP3, Ogg o WAV. Las imágenes solo en JPEG o PNG, hasta 5 MB. Se invoca con `InvokeDataAutomationAsync` (S3 de entrada y salida). Precio según la Pricing API, salida custom: audio $0.009/min, video $0.084/min, imagen $0.005; salida estándar: audio $0.006/min, video $0.05/min, imagen $0.003. Cuotas [CLI]: 20 jobs concurrentes por modalidad. Para nuestro caso, el blueprint no recibe el catálogo filtrado por edad ni la lista de niños por solicitud, y habría que modelar 90 manifestaciones dentro de un blueprint fijo. Agrega S3, polling y un segundo formato de salida. **No conviene en 2 días.**
- **Video directo en Bedrock.** Nova Lite y Pro (v1) y Nova 2 Lite aceptan `video` en Converse [CLI: modalidades listadas] con los límites de la tabla [DOC](https://docs.aws.amazon.com/nova/latest/userguide/modalities-video.html). Un video de 10 a 30 s equivale a 10 a 30 fotogramas a 1 fps. Nova Premier ya está en fin de vida [CLI]. TwelveLabs Pegasus 1.2 (video → texto) está en la allowlist, pero no responde a Converse [CLI].
- **Imágenes.** Las aceptan Claude (Sonnet, Haiku y Opus), Nova Lite y Pro, Nova 2 Lite, Llama 4, Mistral Large 3, Ministral y Pixtral (según `inputModalities`) [CLI]. Formatos de `ImageBlock`: png, jpeg, gif y webp [DOC](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ImageBlock.html). Hasta 20 imágenes de 3,75 MB y 8000 px por mensaje [DOC](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html). Nova reescala, y una imagen de 900×900 equivale a unos 1300 tokens [DOC](https://docs.aws.amazon.com/nova/latest/userguide/modalities-image.html).
- **Audio directo.** Voxtral Small y Mini aceptan voz y Converse tiene `AudioBlock` (mp3, wav, m4a, webm, ogg y otros) [DOC](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_AudioBlock.html). Voxtral está en estado **Legacy**, con fin de vida en marzo de 2027 y contexto de 32K [DOC](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-mistral-ai-voxtral-small-24b-2507.html). Desde la CLI solo se verificó el "hola" de texto. Nova 2 Sonic es voz a voz por stream bidireccional (`InvokeModelWithBidirectionalStream`, no está en la CLI) y soporta es-US [DOC](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-language-support.html). Está pensado para conversación en tiempo real, no para transcribir una nota. **Transcribe es más simple y predecible**; Voxtral sería un plan B sin S3.
- **Notas manuscritas.** Textract detecta escritura manuscrita solo en inglés; el texto impreso sí lo lee en español [DOC](https://aws.amazon.com/textract/faqs/). Precio: DetectDocumentText $0.0015/página [DOC](https://aws.amazon.com/textract/pricing/). `list-adapters` responde [CLI]. Para post-its en español conviene **Claude Sonnet con la imagen**, que puede transcribir y extraer en la misma llamada. Sin pruebas.
- **Rekognition (solo etiquetas y escenas, sin rostros).** `list-collections` responde [CLI], y para `StartLabelDetection` / `StartSegmentDetection` no hay un comando de lectura inocuo, así que no se verificó. Funciona de forma asíncrona sobre video en S3; cuesta $0.10/min en etiquetas y $0.05/min en segmentos (Pricing API) [DOC]. Para nuestro caso aporta poco: etiquetas como "Toy" o "Block" no mapean a manifestaciones. **No usar reconocimiento facial** (sección 11 del contexto).
- **ffmpeg.** Está instalado localmente (`/usr/bin/ffmpeg`, n9.0.1) [CLI, no se procesó nada]. Comandos típicos:
  - `ffmpeg -i in.mp4 -vn -ac 1 -ar 16000 audio.flac` separa el audio para Transcribe.
  - `ffmpeg -i in.mp4 -vf "fps=1/3,scale=1024:-1" -q:v 3 f_%02d.jpg` extrae un fotograma cada 3 s.
  - `-vf "select='gt(scene,0.3)'" -vsync vfr` extrae fotogramas en los cambios de escena.

  Puede correr en el backend (contenedor o EC2) o en Lambda con una layer de ffmpeg. Es la opción más barata y deja toda la lógica en Converse.

## 4. Recomendación (2 días, 5 personas, demo confiable)

1. **Modelo de extracción:** `BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6`. Acertó en la prueba, tiene la latencia más baja entre los Sonnet, cuotas de 6M TPM y 10k RPM, y es multimodal (sirve para fotos). Alternativa: `us.anthropic.claude-sonnet-5`, más barato por token pero más lento, y sin `temperature`. Si se usa el perfil `global.`, el precio baja un 10 %, pero el tráfico puede salir de EE. UU.
2. **Modelo barato:** `us.anthropic.claude-haiku-4-5-20251001-v1:0` para el borrador rápido o un reintento, el informe a la familia y "qué observar después". Para clasificación trivial, `amazon.nova-micro-v1:0` ($0.035/$0.14).
3. **BDA vs. pipeline propio:** **pipeline propio.** Texto → Converse; audio → Transcribe batch → Converse; foto → Converse con imagen; video (si alcanza) → ffmpeg → Transcribe + fotogramas → Converse. Así hay una sola función de extracción y un solo schema. BDA queda como mejora futura.
4. Para robustez de la demo: validar en código (IDs contra el CSV, nivel igual al máximo, `id_nino` en la sala) y reintentar una vez con Haiku si falla. Hacer una corrida completa de audio antes del pitch para medir la latencia real de Transcribe.

## 5. Resultados de las pruebas

### 3a. Texto (ejecutada) [CLI]

- Catálogo: `Dataset/datos_publicos/manifestaciones.csv` **completo (90 filas)**. Cabe sin problema: el system prompt ocupa unos 11.700 caracteres y 5.400 tokens.
- Contexto según la sección 7.2: lista de niños (`NINO-00002 | Simón | 24 meses`; edad al 2026-10-13 calculada desde `ninos.csv`, nivel esperado 8) y actividad no indicada.
- Instrucciones del prompt: solo catálogo, citar evidencia, no inventar, no inferir emociones ni diagnósticos, español neutro.
- Schema: la sección 5.3 trae un **ejemplo**, no un JSON Schema formal. Se tradujo a JSON Schema sin agregar campos: `id_captura`, `observaciones[]` con `id_nino` (string o null), `descripcion_nino` (string o null), `manifestaciones[]` con `id_manifestacion`, `evidencia` y `confianza` (enum alta/media/baja), `nivel_sugerido` (entero de 1 a 9), `justificacion` y `confianza`, y `advertencias[]`; todo con `additionalProperties: false`.
- Comando:

```
aws bedrock-runtime converse --region us-east-1 --model-id <modelo> \
  --system file://system.json --messages file://msg_texto.json \
  --tool-config file://tool.json \   # toolSpec registrar_observaciones + toolChoice {"tool":{"name":"registrar_observaciones"}}
  --inference-config '{"maxTokens":1500,"temperature":0}'   # Sonnet 5: sin temperature
```

| Modelo | Manifestaciones devueltas | ¿Existen en el CSV? | Nivel sugerido (coherente con el máximo) | Schema | Tokens entrada/salida | latencyMs | Pared (CLI) |
|---|---|---|---|---|---|---|---|
| Sonnet 5 | L08-MF-01, L08-SE-02 | Sí, Sí | 8 (sí) | OK | 6801 / 529 | 5323 | 7,6 s |
| **Sonnet 4.6** | L08-MF-01, L08-SE-02 | Sí, Sí | 8 (sí) | OK | 5374 / 338 | 3798 | 5,7 s |
| Haiku 4.5 | L08-MF-01, L08-SE-02 | Sí, Sí | 8 (sí) | OK | 5373 / 360 | 3101 | 5,0 s |
| Nova 2 Lite | L08-MF-01 (omitió la petición de ayuda) | Sí | 8 (sí) | OK | 4450 / 229 | 2650 | 4,7 s |
| Nova Pro | L08-MF-01, **L07-LC-01** (discutible) | Sí, Sí | 8 (sí) | OK | 4344 / 207 | 2077 | 4,2 s |
| Nova Lite | L08-MF-01, **L05-LC-02** (nivel incoherente) | Sí, Sí | 8 (sí) | OK | 4344 / 215 | 1761 | no registrada |

La salida esperada según el guion de la demo (sección 12) son dos manifestaciones, motor fino y socioemocional, nivel 8. Solo los tres modelos Claude la reproducen exactamente.

Salida completa de Sonnet 4.6 (`toolUse.input`):

```json
{"id_captura":"CAP-TEST-0001","observaciones":[{"id_nino":"NINO-00002","descripcion_nino":"Simón, 24 meses","manifestaciones":[{"id_manifestacion":"MAN-L08-MF-01","evidencia":"construyó una torre de cinco bloques sin que se le cayera","confianza":"alta"},{"id_manifestacion":"MAN-L08-SE-02","evidencia":"le pidió ayuda a la tía para abrir la caja de los juguetes","confianza":"alta"}],"nivel_sugerido":8,"justificacion":"Simón construyó una torre de cinco bloques (supera el umbral de cuatro del nivel 8) y comunicó una necesidad de ayuda a la educadora de forma clara, ambas conductas correspondientes al nivel 8.","confianza":"alta"}],"advertencias":[]}
```

Salida completa de Sonnet 5:

```json
{"id_captura":"CAP-TEST-0001","observaciones":[{"id_nino":"NINO-00002","descripcion_nino":"Simon","manifestaciones":[{"id_manifestacion":"MAN-L08-MF-01","evidencia":"construyó una torre de cinco bloques sin que se le cayera","confianza":"alta"},{"id_manifestacion":"MAN-L08-SE-02","evidencia":"le pidió ayuda a la tía para abrir la caja de los juguetes","confianza":"alta"}],"nivel_sugerido":8,"justificacion":"La nota describe dos conductas observables con evidencia textual directa: la construcción de una torre de cinco bloques estables, que cumple e incluso supera el criterio de MAN-L08-MF-01 (cuatro o más bloques), y la solicitud de ayuda mediante palabra, que corresponde a MAN-L08-SE-02. Ambas manifestaciones corresponden a nivel 8, por lo que ese es el nivel sugerido.","confianza":"alta"}],"advertencias":["No se registró evidencia sobre otros dominios (lenguaje más allá de la petición de ayuda, cognitivo, motor grueso), por lo que no se incluyeron manifestaciones adicionales para evitar inferencias sin respaldo textual."]}
```

Observaciones:
- Todos los modelos llenaron `descripcion_nino` aunque el niño estaba identificado; el contrato pide `null` en ese caso. Hay que decirlo explícitamente en el prompt o forzarlo en código.
- Costo aproximado por nota con Sonnet 4.6: unos $0.023. Con Haiku 4.5, unos $0.008.
- En `ninos.csv`, NINO-00002 tiene `sexo_registrado=f` y el texto de prueba lo llama "Simón". Es un dato sintético y no afecta la prueba.

### 3b. Audio: **pendiente, todavía no hay muestra**

`research/samples/` no existe y no se creó ningún recurso. Cuando haya un audio, este es el procedimiento. Primero hay que **confirmar la creación del bucket**: costo despreciable (centavos) y se borra al final.

```
set B bbc-research-transcribe-(random 1000 9999)
aws s3api create-bucket --bucket $B --region us-east-1
aws s3api put-public-access-block --bucket $B --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3 cp research/samples/<nota>.m4a s3://$B/in/nota.m4a
set J bbc-test-(date +%s); set T0 (date +%s%N)
aws transcribe start-transcription-job --region us-east-1 --transcription-job-name $J \
  --language-code es-US --media MediaFileUri=s3://$B/in/nota.m4a --output-bucket-name $B --output-key out/
#   variante: --identify-language --language-options es-US es-ES
aws transcribe get-transcription-job --region us-east-1 --transcription-job-name $J --query TranscriptionJob.TranscriptionJobStatus   # repetir hasta COMPLETED; T1=(date +%s%N)
aws s3 cp s3://$B/out/$J.json /tmp/bbc-research/tr.json    # texto en .results.transcripts[0].transcript
# poner la transcripción en msg_texto.json y repetir el comando converse de 3a; registrar usage y metrics.latencyMs
# limpieza y verificación:
aws transcribe delete-transcription-job --region us-east-1 --transcription-job-name $J
aws s3 rm s3://$B --recursive; aws s3api delete-bucket --bucket $B --region us-east-1
aws s3api head-bucket --bucket $B        # debe dar 404
aws transcribe list-transcription-jobs --region us-east-1 --job-name-contains bbc-test   # debe quedar vacío
```

Hay que registrar dos latencias: la del job (de la creación a COMPLETED) y la de Converse.

## 6. Problemas encontrados y cómo resolverlos

| Problema | Evidencia | Resolución |
|---|---|---|
| Allowlist IAM de modelos con deny explícito | `ws-bedrock-model-allowlist-policy-1` [CLI] | Usar solo los modelos de la tabla 2. Pedir otros modelos a la organización del evento |
| Claude 4.5+ y Nova 2 Lite no admiten el ID on-demand directo | ValidationException "on-demand throughput isn't supported" [CLI] | Usar perfiles `us.` o `global.` en `BEDROCK_MODEL_ID` |
| Sonnet 5 rechaza `temperature` | ValidationException [CLI] | No enviar `temperature` para ese modelo, o usar Sonnet 4.6 |
| Opus 5 devuelve `reasoningContent` por defecto | Respuesta "hola" [CLI] | No usarlo con `toolChoice` forzado sin probar antes |
| Nova Premier en fin de vida; Fable 5 falla por el modo de retención de datos | [CLI] | Descartados |
| No se pueden aumentar las cuotas | `DenyServiceQuotaModifications` en `ws-dont-modify-policy-0` [CLI] | Los valores por defecto sobran para la demo. Ojo con Pixtral (10 RPM) |
| Todo, salvo `bedrock:Invoke*` y S3, está restringido a us-east-1 | `DenyAllOutsideAllowedRegions` en `ws-default-policy` [CLI] | Crear recursos solo en us-east-1. Los perfiles `us.` y `global.` funcionan |
| Sin `organizations:*`: no hay opt-out de uso de datos en servicios de IA (Transcribe, Textract, Rekognition) | `ws-dont-modify-policy-0` [CLI] + nota de Transcribe [DOC] | En el evento, solo datos sintéticos o audio grabado por el equipo. En producción, aplicar una política de opt-out |
| `ListStreamProcessors` y `ListMediaAnalysisJobs` de Rekognition devuelven AccessDenied | [CLI] | No afecta: el video de archivo (`StartLabelDetection`) no se verificó y no se usaría |
| Ruta real del dataset: `Dataset/datos_publicos/` y no `data/dataset_e1/` como dice el contexto | `ls` [CLI] | Actualizar la sección 0 del contexto o crear la ruta esperada sin modificar los archivos. El código debe leer la ruta desde configuración |
| Prueba de audio sin muestra | `research/samples/` no existe | Dejar un m4a o wav de 10 a 60 s y correr el procedimiento de 3b |
| `jq` no está instalado | `which jq` | Se usó `python3` para filtrar JSON |
| La sección 5.3 no trae un JSON Schema formal, solo un ejemplo | Contexto | El schema se derivó del ejemplo y de las tablas de 5.2 (ver 5.3a). Conviene guardarlo como archivo del contrato |

## 7. Recursos creados y borrados

- **Recursos AWS creados: ninguno.** Solo hubo llamadas `converse` (unas 45 en total, unos 60k tokens, menos de $0.50) y comandos list, get o describe. No se crearon buckets, jobs de Transcribe ni proyectos o blueprints de BDA.
- Verificación al cierre:
  - `aws s3api list-buckets` → 0 buckets.
  - `aws transcribe list-transcription-jobs` → vacío.
  - `aws bedrock-data-automation list-data-automation-projects` → vacío.
- Archivos temporales: solo en `/tmp/bbc-research/`, borrados al terminar. Lo único que quedó en el repo es este informe (`docs/investigacion_servicios.md`). `Dataset/` ya estaba sin trackear y no se modificó.

## 8. Fuentes (consultadas el 2026-10-14)

- Pricing API de AWS (`aws pricing get-products`, us-east-1): servicios `AmazonBedrock`, `AmazonBedrockFoundationModels`, `transcribe` y `AmazonRekognition`.
- [Bedrock: API compatibility](https://docs.aws.amazon.com/bedrock/latest/userguide/models-api-compatibility.html) · [Converse Message (límites de imágenes)](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html) · [ImageBlock](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ImageBlock.html) · [AudioBlock](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_AudioBlock.html) · [ContentBlock](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ContentBlock.html)
- [Nova: video understanding](https://docs.aws.amazon.com/nova/latest/userguide/modalities-video.html) · [Nova: image understanding](https://docs.aws.amazon.com/nova/latest/userguide/modalities-image.html) · [Nova 2 Sonic: idiomas](https://docs.aws.amazon.com/nova/latest/nova2-userguide/sonic-language-support.html)
- [Voxtral Small model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-mistral-ai-voxtral-small-24b-2507.html)
- [Transcribe: idiomas](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html) · [Transcribe: formatos de entrada](https://docs.aws.amazon.com/transcribe/latest/dg/how-input.html) · [Transcribe: precios](https://aws.amazon.com/transcribe/pricing/)
- [BDA: límites](https://docs.aws.amazon.com/bedrock/latest/userguide/bda-limits.html) · [BDA: custom output y blueprints](https://docs.aws.amazon.com/bedrock/latest/userguide/bda-custom-output-idp.html) · [Bedrock: precios (BDA)](https://aws.amazon.com/bedrock/pricing/)
- [Textract FAQ (manuscrita)](https://aws.amazon.com/textract/faqs/) · [Textract: precios](https://aws.amazon.com/textract/pricing/)

Contenido de fuentes externas parafraseado para cumplir con las licencias.
