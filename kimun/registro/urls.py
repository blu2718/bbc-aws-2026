from django.urls import path

from . import views, views_propuestas, views_revision

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/<int:curso_id>/", views.curso, name="curso"),
    path("cursos/<int:curso_id>/metas/", views.metas, name="metas"),
    path("ninos/<int:nino_id>/", views.ficha, name="ficha"),
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
