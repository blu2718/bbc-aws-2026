# Servicios AWS en la cuenta del evento (us-east-1)

Revisado el 14 de octubre de 2026 con el rol `WSParticipantRole`. [CLI] = verificado en la cuenta; [DOC] = según la documentación, sin probar.

## Restricciones de la cuenta (Task 4)

- Todo, salvo `bedrock:Invoke*` y S3, está restringido a us-east-1 (`DenyAllOutsideAllowedRegions`). [CLI]
- Las cuotas no se pueden aumentar (`DenyServiceQuotaModifications`). Los valores por defecto sobran para la demo. [CLI]
- No hay acceso a `organizations:*`. [CLI]

## Bedrock (Tasks 4, 5, 7 y 10)

- Una allowlist IAM (`ws-bedrock-model-allowlist-policy-1`) bloquea con deny explícito Sonnet 5.5, Haiku 5.5 y Opus 5.5, entre otros. [CLI]
- Modelos que usa el plan. Los dos aceptan texto e imagen y tool use forzado (`toolChoice.tool`). [CLI]

  | Modelo | ID (solo funciona con perfil `us.`; el ID directo falla) | Cuota | $ por 1M tokens, entrada / salida |
  |---|---|---|---|
  | Claude Sonnet 5 | `us.anthropic.claude-sonnet-5` | 6M TPM | 2,20 / 11,00 |
  | Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 5M TPM, 10.000 RPM | 1,10 / 5,50 |

- Sonnet 5 rechaza el parámetro `temperature` (ValidationException): no enviarlo. [CLI]
- Línea base para la Task 10: en una prueba de extracción con tool use y un prompt de unos 5.400 tokens, Sonnet 5 tardó 5,3 s y Haiku 4.5, 3,1 s. Los dos devolvieron JSON válido. [CLI]
- En esa prueba, todos los modelos llenaron un campo que debía quedar en `null`. Hay que validar y normalizar la salida en código, no confiar solo en el prompt (Task 5). [CLI]

## Fotos (Task 8)

- Converse acepta hasta 20 imágenes por mensaje, de hasta 3,75 MB y 8000 × 8000 px cada una, en png, jpeg, gif o webp. [DOC]
- Textract lee escritura manuscrita solo en inglés, así que los post-its en español los transcribe Claude. [DOC]

## Audio (Task 9)

- Transcribe batch admite `es-US` y `es-ES` (no existe `es-419`). El audio tiene que estar en S3. [DOC]
- Formatos: AMR, FLAC, M4A, MP3, MP4, Ogg, WebM y WAV, de 8 a 48 kHz. Cubre WebM/Opus (Android) y MP4 (iPhone), pero falta probarlo con grabaciones reales. [DOC]
- Cuesta $0,006/min, con cobro por segundo y sin mínimo. El vocabulario personalizado está incluido. [DOC]
- La latencia con audios cortos no está medida; se mide en la Task 9.

## Privacidad (Task 11)

- Transcribe puede guardar el contenido para mejorar sus modelos, y el opt-out requiere AWS Organizations, que está denegado en la cuenta. Por eso en el evento solo se usa audio sintético (Polly) o grabado por el equipo. En producción se aplica una política de opt-out. [DOC]

## Fuentes (consultadas el 14 de octubre de 2026)

- Precios: Pricing API de AWS (`AmazonBedrock`, `AmazonBedrockFoundationModels` y `transcribe`, us-east-1) y [precios de Transcribe](https://aws.amazon.com/transcribe/pricing/).
- [Converse: límites de imágenes](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_Message.html) · [ImageBlock](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ImageBlock.html)
- [Transcribe: idiomas](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html) · [Transcribe: formatos de entrada](https://docs.aws.amazon.com/transcribe/latest/dg/how-input.html)
- [Textract FAQ](https://aws.amazon.com/textract/faqs/)

Contenido de fuentes externas parafraseado para cumplir con las licencias.
