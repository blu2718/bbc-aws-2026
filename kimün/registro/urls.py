from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("cursos/<int:curso_id>/", views.curso, name="curso"),
]
