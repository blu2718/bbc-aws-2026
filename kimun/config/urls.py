from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

# MEDIA_URL no se sirve, ni siquiera en desarrollo: las fotos subidas no se muestran
# y se borran apenas se leen (Task 8).
urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("registro.urls")),
]
