# Verificación de la Task 7 — 15-10-2026

## Resultado

Verificación local completada sobre `task7`, con las correcciones locales de Kiro conservadas. La Task 7 sigue pendiente de una generación con Bedrock real. No se crearon recursos AWS ni se hicieron llamadas reales durante esta revisión: ni el entorno aislado ni el entorno normal de Windows tenían credenciales o perfiles configurados.

## Comprobaciones

- Suite completa: **562 passed in 217.61s** con el comando del README, una sola ejecución de pytest.
- `manage.py check`: sin problemas. `makemigrations --check --dry-run`: sin cambios. `git diff --check`: sin errores.
- Migraciones aplicadas en una base de demo separada; la base habitual no se utilizó para la demo. La suite incluye las pruebas de conservación de datos y restricciones de las migraciones.
- Navegador de escritorio y móvil a 390 × 844 px: formulario legible y operable, sin desbordamiento horizontal de la ficha; consola sin errores observados.
- Aceptar las tres observaciones pendientes de IA desde revisión produjo una sola solicitud. La evidencia incluyó también las dos observaciones aceptadas que ya tenía el niño ficticio.
- Tres generaciones simuladas mediante el cliente existente y auditoría del cuerpo serializado: cinco observaciones, todas con el código propio, seis códigos distintos, cero menciones ambiguas, cero identidades conocidas del curso y cero ejemplos reservados. Las citas guardadas pertenecían al conjunto enviado.
- El sondeo pasó de cola a lista y se detuvo. El enlace de evidencia abrió la observación correspondiente. El enlace de actualización manual recorrió la vista de estado y volvió a la ficha.
- Aceptar la primera propuesta creó una validación de nivel 3 y la tabla mostró `3 · Desarrollando`.
- Solicitar manualmente otra propuesta, ajustar la sugerencia 4 al nivel 5 y guardar un comentario conservó la sugerencia original y registró la decisión de la educadora.
- Rechazar una tercera propuesta (sugerencia 6) conservó el nivel actual 5. Al finalizar había exactamente dos validaciones ligadas a propuestas: aceptada → 3 y ajustada → 5.
- Solicitar CC sin observaciones devolvió evidencia insuficiente localmente, nivel nulo y etiqueta provisoria, sin llamada al modelo ni botón de aceptación. No quedaron solicitudes en cola ni procesándose.
- Navegación normal, HTMX, roles, CSRF, idempotencia, errores, caducidad y concurrencia están cubiertos por la suite. La revisión visual usó JavaScript; el caso sin JavaScript se comprobó mediante las pruebas HTTP existentes.

## Cambios de cierre

Kiro había corregido los alias explícitos de las dos Sofías de la demo, el enlace para actualizar sin JavaScript, la presentación de solicitudes listas y los diagnósticos de error sin mensajes crudos. Sus pruebas adicionales pasaron con la suite completa.

Se completó `scripts/probar_propuesta.py` para limitar la prueba real a un solo intento, impedir su uso sobre la base habitual, exigir como máximo una solicitud pendiente y ejecutar el modo simulado sin buscar credenciales. El procedimiento está en el README.

## Pendiente de AWS

Con credenciales configuradas, preparar una única solicitud en la base aislada y ejecutar el script sin `--sin-red`. Confirmar modelo y región, resultado listo, citas válidas y métricas de uso. Si falla, registrar el código o clase del error y detener la prueba. No repetir para probar las decisiones de interfaz, ya verificadas con simulación. La evaluación de calidad a escala pertenece a la Task 10.
