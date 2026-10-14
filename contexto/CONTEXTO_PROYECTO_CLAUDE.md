# Ruta de Aprendizaje: contexto del proyecto (Hackatón AWS Breaking Barriers Chile 2026)

> Documento de contexto para Kiro y para el equipo. Describe el problema, las reglas del dominio, el contrato de datos, la arquitectura propuesta y las tareas. Las secciones marcadas con **[DECIDIR]** están abiertas y pueden cambiar.

---

## 0. Cómo usar este documento con Kiro

1. Guardarlo en el repo como `.kiro/steering/contexto.md` para que Kiro lo tenga siempre presente.
2. Pedirle a Kiro que genere la spec (`requirements.md`, `design.md`, `tasks.md`) a partir de este archivo, un módulo a la vez (sección 9).
3. Copiar el dataset público a `data/dataset_e1/` sin modificarlo.
4. Regla para Kiro: **no inventar campos ni IDs fuera del contrato de la sección 5.** Si algo falta, preguntar.

---

## 1. Contexto

- **Desafío:** Fundación Integra, desafío 1, "IA para el Desarrollo Infantil: de la Observación a la Acción".
- **Evento:** AWS Breaking Barriers Chile 2026, Universidad de Chile, 14 al 16 de octubre de 2026. Se entrega un MVP y se presenta un pitch el último día.
- **Equipo:** 5 estudiantes de Ingeniería en Computación (DCC, FCFM).
- **Recursos:** Kiro, Amazon Bedrock y servidores MCP en la cuenta AWS del evento.
- **Criterios del jurado:** innovación técnica 25%, impacto social 25%, factibilidad y sustentabilidad 20%, escalabilidad 15%, calidad de la presentación 15%.

### Fundación Integra en números
- Más de 1.200 jardines y salas cuna, presentes en 320 comunas (95% del país).
- Más de 85.000 niños y niñas al año, del 60% más vulnerable.
- 27.500 trabajadoras, 98% mujeres. En cada sala hay 1 educadora de párvulos y 2 técnicas.

---

## 2. El problema

### En una frase
Las tías pierden en promedio 4 horas a la semana transformando lo que observan en sala (notas en papel, post-its, memoria) en una evaluación ordenada por niño según la rúbrica de Integra. Ese proceso manual hace que la información llegue tarde, quede desactualizada y que el rezago de un niño se detecte cuando ya se perdió tiempo en la ventana de los primeros 1.000 días.

### Dolores
| # | Dolor | Fuente |
|---|---|---|
| D1 | 4 h por semana por tía, más de 11.000 h semanales en la institución, cerca del 10% de la jornada | Presentación de Integra |
| D2 | Observaciones diarias en papel, difíciles de procesar e interpretar | Mentora |
| D3 | Mapear cada conducta a un nivel de la rúbrica requiere conocerla de memoria | Presentación y mentora |
| D4 | El rezago se detecta tarde (ejemplo: se espera nivel 7 y el niño está en 4) | Mentora |
| D5 | Nadie avisa cuando un niño o un dominio lleva mucho tiempo sin observaciones | Mentora y dataset |

### Usuarios
| Rol | Qué necesita |
|---|---|
| Tía o técnica | Registrar rápido en sala, con el celular, sin dejar de atender a los niños |
| Educadora de párvulos | Revisar y aprobar lo que propone el sistema. **Tiene la decisión final sobre el nivel** |
| Equipo educativo de Integra | Ver alertas de rezago y de datos desactualizados, decidir derivaciones |
| Niño y familia | Sus datos son sensibles y deben protegerse |

### Necesidades (requisitos de alto nivel)
- **N1. Captura en sala** con audio, foto, video corto o texto desde el celular.
- **N2. De crudo a estructurado.** Convertir cada registro en observaciones con el formato del dataset (sección 5).
- **N3. Proponer, no decidir.** Toda sugerencia de la IA pasa por aprobación humana.
- **N4. Ficha por niño** con el nivel por dominio comparado con el esperado para su edad.
- **N5. Alertas** de rezago, de datos añejos y de dominios sin observaciones.
- **N6. Privacidad desde el diseño** (datos de menores, Ley 21.719 de protección de datos personales).
- **N7. Escalable** a 1.200 jardines y 85.000 niños, y replicable en otras instituciones.

### KPI del desafío
Reducir el tiempo de documentación de 4 h semanales a 0 h. En el MVP lo demostramos midiendo el tiempo de procesar una observación a mano frente a revisarla en el sistema.

### Fuera de alcance
- Que el sistema cambie el nivel de un niño sin aprobación humana.
- Reconocimiento facial o cualquier dato biométrico.
- Diagnóstico clínico. La ruta de niveles **no es un instrumento clínico**, el sistema solo sugiere evaluar una derivación.

---

## 3. La solución en una frase

Una app web móvil donde la tía registra lo que observa (audio, foto, video o texto), la IA generativa lo convierte en observaciones estructuradas según la rúbrica con evidencia y justificación, la educadora las aprueba, y el sistema mantiene actualizada la ficha de cada niño con alertas de rezago y de información desactualizada.

### Flujo principal
```
[Tía en sala] --audio/foto/video/texto + niño(s) + actividad-->
   [Pipeline IA] --> borrador de observación (formato dataset) -->
      [Bandeja de revisión: educadora aprueba / corrige / descarta] -->
         [Observación aprobada en la base] -->
            [Ficha del niño + Vista del jardín + Alertas (reglas fijas)]
```

### Estrategia de desarrollo: dos frentes en paralelo
El formato del dataset es el **contrato** entre ambos frentes.

- **Frente A, la app.** Se construye desde el inicio sobre el dataset público (500 niños, 2.950 observaciones), como si la media ya estuviera procesada.
- **Frente B, el pipeline de IA.** Convierte media en observaciones con exactamente el mismo formato.
- Cuando B funciona, sus resultados entran como "borradores" a la bandeja de revisión de A. La app no cambia.

---

## 4. El dataset público (`dataset_e1_publico.zip`)

Todo es **sintético**. No hay archivos multimedia: `formato_captura` es solo una etiqueta y `nota_breve` son frases genéricas (885 de 2.950 vacías). Fecha de referencia del dataset: `2026-10-13`.

| Archivo | Filas | Contenido |
|---|---:|---|
| `jardines.csv` | 20 | `id_jardin, nombre_fantasia, comuna, region, numero_salas, numero_educadoras` |
| `educadoras.csv` | 80 | `id_educadora, id_jardin, rol (educadora_parvulos/tecnico_parvulos), anios_experiencia` |
| `ninos.csv` | 500 | `id_nino, fecha_nacimiento, sexo_registrado, id_jardin, sala_grupo, fecha_ingreso` |
| `ruta_niveles.csv` | 9 | `nivel, nombre_nivel, edad_min_meses, edad_max_meses, dominios, descripcion` |
| `manifestaciones.csv` | 90 | `id_manifestacion, nivel, dominio, texto_observable` (la rúbrica concreta) |
| `observaciones.csv` | 2.950 | `id_observacion, id_nino, id_educadora, fecha_observacion, formato_captura, nivel_estimado, nota_breve` |
| `observacion_manifestaciones.csv` | 8.850 | `id_observacion, id_manifestacion` (1 a 5 por observación) |
| `consolidado.json` | | Vista anidada jardín → niños → observaciones → manifestaciones, con `edad_meses_observacion` |

### La rúbrica del dataset
- **9 niveles**, de 0 a 36 meses:

| Nivel | Nombre | Edad orientativa (meses) |
|---:|---|---|
| 1 | Atención y regulación inicial | 0 a 2 |
| 2 | Interacción y control emergente | 2 a 4 |
| 3 | Alcance y exploración corporal | 4 a 6 |
| 4 | Sedestación y comunicación intencional | 6 a 9 |
| 5 | Movilidad y propósito | 9 a 12 |
| 6 | Autonomía funcional inicial | 12 a 18 |
| 7 | Representación y combinación inicial | 18 a 21 |
| 8 | Combinación y participación | 21 a 27 |
| 9 | Secuencias y autonomía creciente | 27 a 36 |

- **5 dominios** con código: `cognitivo (CO)`, `lenguaje_comunicacion (LC)`, `motor_fino (MF)`, `motor_grueso (MG)`, `socioemocional (SE)`.
- **2 manifestaciones por dominio y nivel** = 90 en total. ID con formato `MAN-L{nivel:02}-{dominio}-{01|02}`, por ejemplo `MAN-L08-MF-01` = "Construye una torre de cuatro o más bloques estables".
- Cada observación del dataset tiene un `nivel_estimado` global y se vincula a manifestaciones **de ese mismo nivel**.

### Cálculo de edad (del diccionario de datos)
```
edad_meses = 12*(año_obs - año_nac) + (mes_obs - mes_nac) - (1 si dia_obs < dia_nac, si no 0)
```

### Hechos útiles del dataset
- 60 niños tienen 1 o 2 observaciones (ingreso reciente); 440 tienen entre 4 y 9.
- Formatos: texto 1.454, video 563, audio 494, foto 439.
- Casi no hay rezago (la diferencia con el nivel esperado es 0 o 1). **Para la demo hay que crear casos de rezago.**
- La mayoría de los niños lleva meses sin observaciones respecto a la fecha de referencia. Sirve para la alerta de datos añejos.
- Existe un set de validación interna que la organización **no** entrega. El sistema no debe depender de nada específico de estos 500 niños.

> **[DECIDIR] Rúbrica.** La presentación de Integra habla de 10 núcleos, 8 niveles y 3 niveles educativos. El dataset trae 9 niveles y 5 dominios (0 a 36 meses). Por defecto usamos la del dataset y dejamos la rúbrica como dato configurable (tablas `ruta_niveles` y `manifestaciones`), para poder cargar otra sin tocar código.

---

## 5. Contrato de datos

### 5.1 Entidades base (iguales al dataset)
`Jardin`, `Educadora`, `Nino`, `NivelRuta`, `Manifestacion`, `Observacion`, `ObservacionManifestacion`. Se cargan tal cual desde los CSV.

### 5.2 Entidades nuevas
**`Captura`** (registro crudo que sube la tía)
| Campo | Tipo | Nota |
|---|---|---|
| `id_captura` | string `CAP-...` | PK |
| `id_educadora` | FK | quién capturó |
| `ids_ninos` | lista de FK | niño(s) seleccionados antes de capturar; puede venir vacía |
| `id_actividad` | string opcional | actividad o contexto elegido en la app |
| `formato` | `audio`, `foto`, `video`, `texto` | |
| `uri_media` | string | ruta en S3 (cifrado); vacío si es texto |
| `texto` | string opcional | nota escrita o transcripción |
| `fecha_captura` | datetime | |
| `estado` | `pendiente`, `procesando`, `procesada`, `error` | |

**`ObservacionBorrador`** (lo que propone la IA, antes de aprobar)
| Campo | Tipo | Nota |
|---|---|---|
| `id_borrador` | string `BOR-...` | PK |
| `id_captura` | FK | origen |
| `id_nino` | FK o null | null si la IA no pudo identificar al niño |
| `descripcion_nino` | string opcional | p. ej. "niño de polera azul" cuando no hay identificación |
| `manifestaciones` | lista de objetos | ver 5.3 |
| `nivel_sugerido` | entero 1 a 9 | |
| `justificacion` | string | explicación breve en lenguaje simple |
| `confianza` | `alta`, `media`, `baja` | |
| `estado` | `pendiente_revision`, `aprobada`, `corregida`, `descartada` | |
| `id_revisora`, `fecha_revision` | | quién y cuándo decidió |

Al aprobar o corregir un borrador se crea una `Observacion` + sus `ObservacionManifestacion` con el **mismo formato del dataset**, y `formato_captura` toma el formato de la captura.

**`Alerta`** (calculada, no se guarda o se guarda como caché)
| Campo | Tipo |
|---|---|
| `id_nino` | FK |
| `tipo` | `rezago`, `atencion`, `dato_anejo`, `sin_datos_dominio`, `sin_observaciones` |
| `dominio` | dominio o null |
| `detalle` | string |
| `prioridad` | `alta`, `media`, `baja` |

### 5.3 Salida del pipeline de IA (JSON obligatorio)
```json
{
  "id_captura": "CAP-000123",
  "observaciones": [
    {
      "id_nino": "NINO-00002",
      "descripcion_nino": null,
      "manifestaciones": [
        {
          "id_manifestacion": "MAN-L04-MF-02",
          "evidencia": "La tía dice: 'Simón tomó la pasa con dos dedos y se la llevó a la boca'",
          "confianza": "alta"
        }
      ],
      "nivel_sugerido": 4,
      "justificacion": "Recoge un objeto pequeño con dedos y palma de forma intencionada, conducta del nivel 4 en motor fino.",
      "confianza": "alta"
    }
  ],
  "advertencias": ["No se pudo identificar al segundo niño que aparece en la foto"]
}
```
Reglas de validación (en código, no en el prompt):
- Todo `id_manifestacion` debe existir en `manifestaciones.csv`. Los que no existen se descartan y se registra el error.
- `id_nino` debe existir y pertenecer a la sala de la educadora, o ser `null`.
- `nivel_sugerido` debe ser coherente con las manifestaciones elegidas (por defecto, el nivel máximo entre ellas).
- Una captura puede producir varias observaciones (una por niño).
- Si la IA no encuentra ninguna manifestación, devuelve lista vacía y una advertencia. **Nunca inventa.**

---

## 6. Reglas de negocio (código determinista, no IA)

Todas las constantes van en un archivo de configuración.

### 6.1 Nivel esperado
```
nivel_esperado(edad_meses) = máximo nivel tal que edad_min_meses <= edad_meses
si edad_meses > 36 → 9
```
### 6.2 Nivel logrado por dominio
```
nivel_logrado(niño, dominio) = nivel más alto con al menos MIN_EVIDENCIAS (por defecto 1)
                               manifestación aprobada de ese dominio
```
Mostrar también el nivel global (el que trae el dataset), pero la ficha se organiza **por dominio**: un niño puede ir al día en motor grueso y atrasado en lenguaje, y el nivel global lo esconde.

### 6.3 Alertas
| Tipo | Condición (por defecto) | Prioridad |
|---|---|---|
| `rezago` | `nivel_esperado - nivel_logrado >= 2` en algún dominio | alta (texto: "Sugerir evaluación de derivación") |
| `atencion` | brecha = 1 | media |
| `dato_anejo` | último registro aprobado del dominio con más de `DIAS_ANEJO` = 30 días | media; alta si supera 60 |
| `sin_datos_dominio` | dominio sin ninguna observación | media |
| `sin_observaciones` | niño sin observaciones en `DIAS_ANEJO` días | alta |

- `FECHA_REFERENCIA` configurable: `2026-10-13` para el dataset, fecha actual para la demo en vivo.
- **[DECIDIR] con la mentora:** umbrales de brecha para rezago y derivación, y `DIAS_ANEJO`.

---

## 7. Pipeline de IA (Frente B)

### 7.1 Entradas y procesamiento
| Formato | Procesamiento |
|---|---|
| `texto` | Directo al paso de extracción |
| `audio` | Amazon Transcribe (español) → texto → extracción |
| `foto` | Imagen + texto o audio de contexto → modelo multimodal de Bedrock |
| `video` (fase 2) | ffmpeg: separar audio (→ Transcribe) y extraer pocos fotogramas (1 por segundo o cambios de escena) → modelo multimodal. Algunos modelos (p. ej. Amazon Nova) aceptan video directo. |

### 7.2 Paso de extracción (núcleo de IA generativa)
- API: **Bedrock Converse**, con el ID de modelo en variable de entorno (`BEDROCK_MODEL_ID`) para cambiarlo sin tocar código.
- Salida estructurada: usar **tool use** con un JSON Schema igual a la sección 5.3, para que el modelo devuelva siempre JSON válido.
- Contexto del prompt:
  - El catálogo de manifestaciones **filtrado** a los niveles cercanos a la edad del niño (nivel esperado ±2), para acortar el prompt y reducir errores. Si no hay niño identificado, el catálogo completo (90 filas, cabe sin problema).
  - Lista de niños de la sala con su edad, solo con ID y nombre ficticio.
  - Actividad elegida por la tía, si existe.
- Instrucciones clave del prompt:
  - Solo elegir manifestaciones del catálogo y citar la evidencia textual o visual.
  - Si no hay evidencia suficiente, no elegir nada.
  - No inferir emociones ni diagnósticos.
  - Responder en español neutro.

> **[DECIDIR] Modelos.** Revisar en la consola de Bedrock ("Model access") qué modelos están habilitados y en qué región. Se necesita uno multimodal (imagen) para la extracción y, si es posible, uno más barato para tareas de texto.

### 7.3 Identificación del niño sin biometría
En orden de preferencia:
1. La tía selecciona al niño en la app antes de capturar.
2. La tía lo nombra en el audio ("Simón ordenó las hojas por color").
3. La IA describe al niño ("polera azul") y la educadora lo asigna al revisar.

No se usa reconocimiento facial.

### 7.4 Funciones extra con IA generativa (si hay tiempo)
- **Qué observar después:** para cada niño, sugerir 1 o 2 conductas del catálogo en los dominios sin datos o atrasados.
- **Informe para la familia** en lenguaje simple, solo con observaciones aprobadas.
- **Asistente para la educadora** (agente con herramientas o MCP): "¿quiénes no tienen observaciones de lenguaje este mes?", "resume el avance de la sala A".

---

## 8. Evaluación de calidad (diferenciador ante el jurado)

Usar el dataset como verdad de referencia:
1. Tomar una muestra estratificada de observaciones (p. ej. 100, distintos niveles y dominios).
2. Para cada una, generar con un LLM una **nota realista de tía** a partir de sus manifestaciones, en lenguaje cotidiano, **sin copiar el texto del catálogo** y mencionando al niño por un nombre ficticio. Guardar `(nota, manifestaciones_reales, nivel_real)`.
3. Grabar algunas de esas notas como audio (el equipo) para probar también el camino de Transcribe.
4. Pasar las notas por el pipeline y calcular:
   - Precisión, recall y F1 de `id_manifestacion`.
   - Exactitud de `nivel_sugerido` (exacto y ±1).
   - Exactitud por dominio.
   - Tiempo promedio de procesamiento por captura.
5. Guardar resultados en `eval/resultados.json` y mostrarlos en el pitch.

Además, para la demo, crear 3 o 4 niños con **rezago real** en algún dominio y algunos con datos añejos.

---

## 9. Módulos y tareas

### Módulo 1. Datos y backend
- Cargar los CSV en la base y exponer la API.
- Endpoints mínimos:
  - `GET /jardines`, `GET /jardines/{id}/ninos`
  - `GET /ninos/{id}` (ficha: datos, nivel por dominio, esperado, historial, alertas)
  - `GET /jardines/{id}/alertas`
  - `POST /capturas` (subir media o texto, devuelve `id_captura`)
  - `GET /borradores?estado=pendiente_revision&sala=...`
  - `POST /borradores/{id}/aprobar`, `/corregir`, `/descartar`
- Implementar las reglas de la sección 6 con tests.

### Módulo 2. Pipeline de IA
- Función `procesar_captura(id_captura) -> salida 5.3`.
- Transcripción de audio, extracción con Bedrock, validación del JSON.
- Procesamiento asíncrono (la tía no espera en pantalla).

### Módulo 3. App de captura y revisión (móvil)
- Pantalla de captura: elegir sala, niño(s), actividad opcional, botón grande para grabar audio, sacar foto o escribir.
- Bandeja de revisión: lista de borradores con evidencia, manifestación sugerida, nivel y confianza; botones aprobar, corregir (cambiar niño o manifestaciones) y descartar.

### Módulo 4. Seguimiento (web)
- Ficha del niño: niveles por dominio frente al esperado (gráfico simple), historial y alertas.
- Vista del jardín o sala: niños ordenados por prioridad de alerta.

### Módulo 5. Evaluación y demo
- Script de la sección 8.
- Datos de prueba: audios grabados, fotos de **productos** de actividades (torre de bloques, dibujo) sin caras de niños.
- Guion de demo y pitch.

---

## 10. Arquitectura y stack propuesto **[DECIDIR según lo que maneje el equipo]**

| Capa | Propuesta por defecto |
|---|---|
| Frontend | Next.js (React) + Tailwind, mobile-first |
| Backend | Python + FastAPI (boto3 para Bedrock, Transcribe y S3) |
| Base de datos | SQLite o PostgreSQL para el MVP (DynamoDB si se prefiere serverless) |
| Media | Amazon S3 con cifrado (SSE-KMS) y URLs prefirmadas |
| IA | Amazon Bedrock (Converse API + tool use), Amazon Transcribe |
| Despliegue | Lo más simple que funcione en la cuenta del evento (App Runner, EC2 o Amplify) |

Principio: **el stack que el equipo ya domina gana al ideal.**

---

## 11. Privacidad y seguridad

- Niños identificados por ID seudónimo; nombres reales en una tabla separada con acceso restringido (en el MVP, nombres ficticios).
- Separación por institución y por jardín (multi-tenant): cada usuario solo ve su sala o jardín.
- Media cifrada en S3; borrar la media cruda después de procesarla y aprobarla (retención configurable). Se conserva solo la observación estructurada.
- Registro de auditoría: quién creó, revisó o vio cada observación.
- Los datos enviados a Bedrock no se usan para entrenar modelos.
- Captura iniciada por la tía; sin grabación continua ni reconocimiento facial en el MVP.
- La decisión sobre el nivel siempre es humana; la IA solo propone con evidencia.

> **[DECIDIR] Captura continua.** La mentora mencionó un celular grabando toda la clase. Para el MVP proponemos captura puntual iniciada por la tía y dejar la continua como visión futura, sujeta a consentimiento de apoderados.

---

## 12. Demo (guion de 2 a 3 minutos)

1. Contexto en una frase: "Una tía pierde 4 horas a la semana en esto".
2. En el celular, la tía elige a un niño y graba: "Simón construyó una torre de cinco bloques y le pidió ayuda a la Sofía para tapar la caja".
3. A los segundos aparece el borrador: dos manifestaciones (motor fino y socioemocional), nivel 8, evidencia citada.
4. La educadora aprueba con un toque.
5. La ficha de Simón se actualiza. Se muestra a otro niño con alerta de rezago en lenguaje y sugerencia de derivación, y uno con datos añejos.
6. Métricas: F1 de extracción sobre el set de prueba y tiempo por observación.
7. Escalabilidad: misma solución para 1.200 jardines, rúbrica configurable para otras instituciones.

---

## 13. Decisiones abiertas

| # | Decisión | Por defecto |
|---|---|---|
| 1 | Rúbrica (dataset o presentación) | Dataset, configurable |
| 2 | Umbral de rezago y derivación | Brecha ≥ 2 = rezago |
| 3 | Días para dato añejo | 30 (alta prioridad sobre 60) |
| 4 | Captura puntual o continua | Puntual |
| 5 | Cómo evalúa el jurado o la organización | Preguntar |
| 6 | Modelos de Bedrock disponibles y región | Revisar en consola |
| 7 | Stack | Sección 10 |

---

## 14. Glosario
- **Tía:** educadora o técnica en párvulos.
- **Manifestación:** conducta observable concreta de la rúbrica, asociada a un nivel y un dominio.
- **Dominio:** área del desarrollo (cognitivo, lenguaje, motor fino, motor grueso, socioemocional).
- **Rezago:** el nivel logrado está por debajo del esperado para la edad.
- **Dato añejo:** información que no se ha actualizado en el plazo definido.
- **Borrador:** observación propuesta por la IA, pendiente de revisión humana.
