from django.urls import path

from . import views, views_captura, views_revision

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/<int:curso_id>/", views.curso, name="curso"),
    # Registro de notas escritas (Task 5)
    path("cursos/<int:curso_id>/capturar/", views_captura.capturar, name="capturar"),
    path("cursos/<int:curso_id>/capturar/recientes/", views_captura.capturas_recientes, name="capturas_recientes"),
    path("capturas/<int:captura_id>/reintentar/", views_captura.reintentar_captura, name="captura_reintentar"),
    path("cursos/<int:curso_id>/metas/", views.metas, name="metas"),
    path("ninos/<int:nino_id>/", views.ficha, name="ficha"),
    path("ninos/<int:nino_id>/nucleos/<str:sigla>/nivel/", views.fijar_nivel, name="fijar_nivel"),
    # Revisión de observaciones (Task 6)
    path("cursos/<int:curso_id>/revision/", views_revision.revision, name="revision"),
    path("observaciones/<int:obs_id>/", views_revision.observacion, name="observacion"),
    path("observaciones/<int:obs_id>/editar/", views_revision.editar, name="observacion_editar"),
    path("observaciones/<int:obs_id>/asignar/", views_revision.asignar, name="observacion_asignar"),
    path("observaciones/<int:obs_id>/aceptar/", views_revision.aceptar_observacion, name="observacion_aceptar"),
    path("observaciones/<int:obs_id>/descartar/", views_revision.descartar_observacion, name="observacion_descartar"),
    path("capturas/<int:captura_id>/aceptar-todas/", views_revision.aceptar_todas_captura, name="captura_aceptar_todas"),
]
