# Plan de implementación de la Task 7

Preparado sobre la rama `task7`, con base en `PLAN.md` y el código actual.

## Resultado esperado

Al aceptar observaciones, el sistema solicita una propuesta de nivel por niño y núcleo. Un proceso de fondo consulta Bedrock con evidencia y rúbrica, reemplazando los nombres por códigos. La ficha muestra la sugerencia, su justificación y las observaciones que la respaldan. Solo la educadora del curso puede aceptarla, fijar otro nivel o rechazarla. Generar una propuesta nunca cambia el nivel validado.

## Punto de partida y alcance

- Ya existen `PropuestaNivel`, `NivelValidado.propuesta`, `Nino.codigo` y `Nino.alias`; se amplían cuando sea necesario, sin recrearlos.
- Se reutilizan `ClienteBedrock`, las rúbricas cargadas, la ficha, el formulario de nivel manual y los filtros de `permisos.py`.
- `revision.aceptar` y `revision.aceptar_todas` son los puntos de integración para las solicitudes automáticas.
- No existe aún `procesar_capturas`. Se creará `procesar_propuestas` como comando independiente, con una función de procesamiento reutilizable por el futuro proceso común. Documentar este comando para su incorporación al despliegue.
- La captura de texto, fotos, audio y la evaluación completa de calidad pertenecen a otras tareas. La demo de esta tarea podrá partir de observaciones pendientes preparadas como datos de prueba.

## 1. Contrato de datos y estados

Archivos: `registro/models.py`, una nueva migración y tests del modelo y del servicio.

- Conservar los estados existentes y agregar `procesando` y `obsoleta` para distinguir un trabajo tomado de una sugerencia que ya no corresponde a los datos actuales.
- Registrar la versión de entrada: nivel validado de referencia, evidencia utilizada y rúbrica, mediante una representación reproducible o huella. Conservar la procedencia oficial/provisoria y la versión del prompt.
- Registrar inicio del procesamiento, intentos y quién/cuándo resolvió una propuesta.
- Definir como máximo una solicitud activa por niño y núcleo; respaldar la regla con una restricción compatible con la base del proyecto y transacciones cortas.
- Una respuesta sin evidencia suficiente tendrá `nivel=null`; no será aceptable como nivel.
- Si una propuesta lista pierde vigencia por nueva evidencia, nueva rúbrica o validación manual, marcarla obsoleta antes de permitir su aceptación.

Entregable: migración y contrato verificable de estados, vigencia y relaciones.

Implementado el punto 1: estados y restricciones en `PropuestaNivel`, huella y comprobación de vigencia en `registro/propuestas.py`, migración `0003_propuesta_contrato` y pruebas de contrato y de migración. La generación, la cola de trabajos y la resolución atómica con `NivelValidado` se incorporarán en los puntos siguientes.

## 2. Sustitución de nombres por códigos

Archivo nuevo: `registro/ia/seudonimo.py`; tests puros en `registro/tests/ia/test_seudonimo.py`.

- Recibir los nombres, alias y códigos de todos los niños del curso; la función no dependerá de Django.
- Reconocer nombres completos, nombres de pila y alias, contemplando tildes, mayúsculas y límites de palabras. Resolver primero las coincidencias más largas para evitar reemplazos parciales.
- Para nombres compartidos o alias ambiguos, usar un marcador neutral: ocultar la identidad sin atribuir el texto a un niño incorrecto.
- Aplicar la sustitución a todos los textos derivados de evidencia que se envíen al modelo. No enviar el diccionario que relaciona nombres y códigos.
- Verificar también los ejemplos incluidos en el prompt si contienen nombres presentes en el curso. No registrar prompts con nombres en logs.

Entregable: pruebas con Naiara/Nayara, dos Sofías, nombres compuestos, apodos y nombres de otros niños mencionados en una cita.

Implementado el punto 2: `Seudonimizador` y `seudonimizar_texto` en `registro/ia/seudonimo.py`, con pruebas puras. La coincidencia usa nombres completos, prefijos del nombre y alias explícitos; una forma compartida se convierte en `[NINO_AMBIGUO]`. El módulo conserva el texto no coincidente, protege códigos ya insertados y permite limpiar estructuras JSON y envíos completos con `invocar`. No agrega el diccionario de identidades al envío. La conexión con el prompt específico de nivel se realizará en el punto 3.

## 3. Evidencia, prompt y validación de respuesta

Archivos nuevos: `registro/ia/propuesta.py`, `registro/ia/prompts/propuesta.md`; coordinación ORM en `registro/propuestas.py`.

- Seleccionar únicamente observaciones aceptadas, individuales, del niño y del núcleo. Contar tanto la etiqueta directa del núcleo como la relación mediante OA, igual que la ficha actual.
- Ordenar por fecha y usar el identificador como desempate. Enviar id, fecha, cita con códigos, OA y apoyo, junto al nivel validado actual.
- Para rúbrica oficial: enviar número, nombre, descripción, conducta y el primer ejemplo disponible de cada nivel. Reservar el segundo ejemplo para la Task 10.
- Para rúbrica provisoria: enviar las conductas NT1/NT2, la trayectoria y el mapeo vigente. Si faltan datos esenciales, mostrar un error de configuración; no inventar descriptores.
- Pedir evaluar la progresión de la conducta, sin imponer una cantidad mínima de observaciones ni un ascenso obligatorio.
- Reutilizar `ClienteBedrock.invocar_herramienta` con una herramienta que devuelva `nivel`, `evidencia_suficiente`, `observaciones_citadas`, `conductas_observadas` y `justificacion`.
- Validar tipos y coherencia: nivel entero dentro del rango dinámico, ids citados dentro del conjunto enviado, textos válidos y evidencia citada para una propuesta con nivel. Rechazar ids ajenos y respuestas incoherentes.
- Si no hay observaciones, resolver localmente como evidencia insuficiente sin llamar a Bedrock. Si la respuesta indica insuficiencia, exigir nivel nulo.

Entregable: módulo testeable con cliente falso, incluida una rúbrica de nueve niveles y la reserva de ejemplos de evaluación.

Implementado el punto 3: prompt versionado y módulo puro `registro/ia/propuesta.py`, con contexto oficial/provisorio, envío seudonimizado y validación estricta de respuesta. `preparar_evidencia` captura la entrada desde Django; `generar_propuesta` devuelve resultado, huella, referencia, procedencia y metadatos del cliente sin persistir ni cambiar niveles. La misma captura alimenta la huella, que ahora incluye el archivo de prompt. La llamada se ejecuta fuera de la transacción de captura. El procesamiento y guardado de trabajos siguen en el punto 4.

## 4. Solicitudes y procesamiento en segundo plano

Archivos: `registro/propuestas.py`, `registro/revision.py` y `registro/management/commands/procesar_propuestas.py`.

- Crear la solicitud automática dentro de la misma transacción que acepta la observación. Excluir notas grupales y observaciones sin niño.
- Al aceptar todas, agrupar por niño/núcleo y solicitar una sola vez por combinación afectada. Las observaciones sin núcleo ni OA no generarán una propuesta sin destino.
- Añadir una solicitud manual desde la ficha. Repetir el POST o hacer doble clic no debe crear trabajos simultáneos para la misma combinación.
- Tomar un trabajo mediante actualización condicional `solicitada -> procesando`; comprobar las filas actualizadas. No depender de bloqueos de fila para la exclusión en SQLite.
- Preparar una entrada consistente, liberar la transacción, llamar a Bedrock y guardar el resultado en otra transacción corta. No mantener escrituras bloqueadas durante la llamada de red.
- Si cambia la entrada durante la llamada, descartar la vigencia del resultado y asegurar una solicitud con los datos recientes.
- Guardar modelo real, resultado validado, relaciones de evidencia y errores sin texto sensible. Ofrecer reintento explícito y recuperación acotada de trabajos interrumpidos.
- El comando tendrá modo continuo y `--once` para pruebas y operación local. No agregar Celery ni Redis.

Entregable: aceptación individual y masiva que encolan correctamente; dos procesadores no ejecutan el mismo trabajo y un fallo no deja la propuesta bloqueada indefinidamente.

Implementado el punto 4: aceptación y solicitudes en una misma transacción; agrupación por niño/núcleo; solicitud y reintento POST desde la ficha; comando `procesar_propuestas` continuo o `--once`. Cada intento recibe un token que impide publicar resultados de un intento recuperado. La captura se guarda antes de llamar al modelo y se comprueba su vigencia al finalizar: un resultado desactualizado se retira y genera una nueva solicitud. Se guardan respuesta, evidencia, modelo y métricas sin cambiar niveles. La recuperación revisa hasta 100 trabajos vencidos por ciclo, con caducidad predeterminada de 300 segundos y un máximo de tres intentos por solicitud; luego exige reintento explícito, conservando el historial. La migración `0004_propuesta_procesamiento` añade el token y las métricas.

## 5. Decisión de la educadora y ficha

Archivos: `registro/views_propuestas.py`, `registro/urls.py`, `registro/ficha.py`, `registro/forms.py`, `registro/templates/registro/_propuesta_nivel.html`, `_nucleo_ficha.html` y estilos necesarios.

- Consultar las propuestas de la ficha en bloque para evitar una consulta por núcleo.
- Mostrar los estados pendiente, procesando, lista, insuficiente, error y obsoleta; además del nivel propuesto con su nombre, justificación, conductas y evidencia enlazada.
- Agregar anclas únicas a las observaciones de cada núcleo. Mantener la etiqueta de rúbrica provisoria según la entrada usada al generar la propuesta.
- Añadir solicitar/reintentar, aceptar, fijar otro nivel y rechazar. Las mutaciones serán POST con CSRF y filtros de permisos en servidor; solo la educadora puede ejecutarlas.
- Aceptar una propuesta vigente creará un único `NivelValidado` ligado a ella, con fecha y usuaria de sesión. Hacer atómica e idempotente la resolución para evitar validaciones duplicadas por doble envío.
- Fijar otro nivel desde una propuesta reutilizará la validación del formulario y guardará la relación con la propuesta de origen, distinguiendo que la educadora eligió un nivel diferente. Rechazar no creará `NivelValidado`.
- Conservar el formulario manual independiente y hacer que sus cambios invaliden sugerencias anteriores cuando corresponda.
- Responder con parciales HTMX y ofrecer navegación normal sin JavaScript. Consultar el estado periódicamente solo mientras haya trabajo pendiente, deteniendo la consulta al finalizar.
- No aceptar propuestas insuficientes, obsoletas, resueltas o pertenecientes a otro niño/curso. La actualización de alertas seguirá usando los cálculos existentes al cargar la tabla.

Entregable: flujo completo desde la revisión hasta la decisión en la ficha, con permisos de educadora, asistente, directora y otro curso comprobados.

Implementado el punto 5: panel completo con nivel y nombre, justificación, conductas, evidencia enlazada, procedencia guardada y decisión con usuaria y fecha. Las decisiones POST verifican permisos, estado, huella y pertenencia de las citas. Aceptar o fijar otro nivel crea un único `NivelValidado` por propuesta en una transacción; rechazar no crea niveles. El estado `ajustada` distingue la elección de un nivel diferente y conserva la sugerencia original. La validación manual independiente invalida propuestas listas anteriores. Se consulta la última propuesta de cada núcleo en bloque; el sondeo cada tres segundos reemplaza solo el panel y se detiene al salir de pendiente/procesando. Hay navegación sin JavaScript, errores de formulario conservados y protección CSRF. La migración `0005_propuesta_decision` añade el estado y las restricciones, sin eliminar historial duplicado si lo hubiera.

## 6. Verificación y cierre

- Escribir primero los casos de privacidad, selección de evidencia, rango dinámico, estados y decisiones; implementar por bloques y ejecutar únicamente los tests afectados durante la iteración.
- Probar fallos de Bedrock, respuestas inválidas, ausencia de evidencia, doble aceptación, aceptación masiva, trabajos concurrentes, interrupción del proceso y evidencia nueva durante la generación.
- Comprobar que ni nombres ni alias del curso aparecen en la petición completa enviada al cliente falso y que los ejemplos reservados no aparecen en el prompt.
- Probar HTMX y navegación normal, enlaces a evidencia, etiqueta provisoria y que generar/rechazar no cambia niveles.
- Ejecutar migraciones de prueba, `manage.py check`, comprobación de migraciones pendientes y la suite completa una sola vez al terminar, siguiendo el README.
- Actualizar README con el comando del proceso, variables de Bedrock, estados, reintentos y pasos de demo. La evaluación de calidad a escala permanece en la Task 10.
- Demo: aceptar tres observaciones de Identidad y Autonomía, procesar la propuesta, revisar sus citas y validarla; comprobar el nuevo historial y la tabla del curso. Con cliente falso se comprueba un resultado reproducible, por ejemplo `3 · Desarrollando`; con Bedrock real se evalúa la propuesta sin prometer ese nivel exacto.

## Orden de ejecución

Estado del punto 6 (15-10-2026): verificación local completada con 562 pruebas, comprobaciones de Django y demo en navegador de escritorio y móvil. Se verificaron las tres decisiones y la ausencia de cambios de nivel al generar/rechazar. La auditoría del envío simulado no encontró identidades conocidas ni ejemplos reservados. **Pendiente la generación con Bedrock real por falta de credenciales AWS**; no se hicieron llamadas reales. Procedimiento y resultados en `docs/validacion_task7.md` y `docs/task7.md`. La Task 7 no se marca cerrada hasta comprobar esa integración.

1. Contrato y migración.
2. Sustitución de nombres y tests de privacidad.
3. Preparación de evidencia, prompt y validación con cliente falso.
4. Solicitudes, integración de revisión y proceso de fondo.
5. Decisiones, endpoints y ficha.
6. Regresión, documentación y demo.

La tarea se considera terminada cuando ambos disparadores (automático y manual) generan propuestas revisables, toda llamada usa códigos, las decisiones quedan registradas y ningún nivel cambia sin intervención de la educadora.
