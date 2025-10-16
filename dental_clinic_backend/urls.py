"""
URL configuration for dental_clinic_backend project.

Sistema de enrutamiento dinámico para Multi-Tenancy:
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .url_patterns import urlpatterns_public, urlpatterns_tenant

# Django no soporta lambda en path, así que usamos el middleware para cambiar ROOT_URLCONF
# Por defecto, cargamos las URLs públicas
urlpatterns = urlpatterns_public

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
