from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/<int:curso_id>/", views.curso, name="curso"),
    path("cursos/<int:curso_id>/metas/", views.metas, name="metas"),
    path("ninos/<int:nino_id>/", views.ficha, name="ficha"),
    path("ninos/<int:nino_id>/nucleos/<str:sigla>/nivel/", views.fijar_nivel, name="fijar_nivel"),
]
