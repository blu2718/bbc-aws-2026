from django.urls import path

from . import views, views_captura, views_propuestas, views_registro, views_revision

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/<int:curso_id>/", views.curso, name="curso"),
    # Resumen del jardín para la directora (Task 12)
    path("jardines/<int:jardin_id>/", views.jardin, name="jardin"),
    # Registrar un suceso y ver cómo quedó ordenado (pantallas I y II de diseno-interfaz.jpg)
    path("cursos/<int:curso_id>/registrar/", views_registro.registrar, name="registrar"),
    path("capturas/<int:captura_id>/", views_registro.captura, name="captura"),
    path("capturas/<int:captura_id>/estado/", views_registro.estado, name="captura_estado"),
    path("capturas/<int:captura_id>/procesar/reintentar/", views_registro.reintentar, name="captura_reintentar_suceso"),
    path("capturas/<int:captura_id>/contexto/", views_registro.agregar_contexto, name="captura_contexto"),
    # Registro de capturas: nota escrita (Task 5), foto (Task 8) y audio (Task 9).
    # Las fotos y los audios no se sirven: se borran apenas se leen.
    path("cursos/<int:curso_id>/capturar/", views_captura.capturar, name="capturar"),
    path("cursos/<int:curso_id>/capturar/foto/", views_captura.capturar_foto, name="capturar_foto"),
    path("cursos/<int:curso_id>/capturar/audio/", views_captura.capturar_audio, name="capturar_audio"),
    path("cursos/<int:curso_id>/capturar/recientes/", views_captura.capturas_recientes, name="capturas_recientes"),
    path("capturas/<int:captura_id>/reintentar/", views_captura.reintentar_captura, name="captura_reintentar"),
    path("cursos/<int:curso_id>/metas/", views.metas, name="metas"),
    path("ninos/<int:nino_id>/", views.ficha, name="ficha"),
    # Informe imprimible para la familia: solo la educadora del curso.
    path("ninos/<int:nino_id>/informe/", views.informe_familia, name="informe_familia"),
    path("ninos/<int:nino_id>/nucleos/<str:sigla>/nivel/", views.fijar_nivel, name="fijar_nivel"),
    path("ninos/<int:nino_id>/nucleos/<str:sigla>/propuesta/", views_propuestas.solicitar_propuesta, name="solicitar_propuesta"),
    path("propuestas/<int:propuesta_id>/reintentar/", views_propuestas.reintentar_propuesta, name="reintentar_propuesta"),
    path("ninos/<int:nino_id>/nucleos/<str:sigla>/propuesta/estado/", views_propuestas.estado_propuesta, name="estado_propuesta"),
    path("propuestas/<int:propuesta_id>/aceptar/", views_propuestas.aceptar_propuesta, name="aceptar_propuesta"),
    path("propuestas/<int:propuesta_id>/ajustar/", views_propuestas.ajustar_propuesta, name="ajustar_propuesta"),
    path("propuestas/<int:propuesta_id>/rechazar/", views_propuestas.rechazar_propuesta, name="rechazar_propuesta"),
    # Revisión de observaciones (Task 6)
    path("cursos/<int:curso_id>/revision/", views_revision.revision, name="revision"),
    path("observaciones/<int:obs_id>/", views_revision.observacion, name="observacion"),
    path("observaciones/<int:obs_id>/editar/", views_revision.editar, name="observacion_editar"),
    path("observaciones/<int:obs_id>/asignar/", views_revision.asignar, name="observacion_asignar"),
    path("observaciones/<int:obs_id>/aceptar/", views_revision.aceptar_observacion, name="observacion_aceptar"),
    path("observaciones/<int:obs_id>/descartar/", views_revision.descartar_observacion, name="observacion_descartar"),
    path("capturas/<int:captura_id>/aceptar-todas/", views_revision.aceptar_todas_captura, name="captura_aceptar_todas"),
]
