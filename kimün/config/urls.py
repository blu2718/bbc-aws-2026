from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("registro.urls")),
]

if settings.DEBUG:
    # Solo en desarrollo. En producción los originales se sirven con URLs
    # prefirmadas de S3 después de verificar permisos (Task 8).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
