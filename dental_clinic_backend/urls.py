"""
URL configuration for dental_clinic_backend project.

Sistema de enrutamiento dinámico para Multi-Tenancy:
- ROOT_URLCONF simplificado que delega todo al url_router.py
"""
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # La única línea importante: delega TODO el enrutamiento al router.
    path('', include('dental_clinic_backend.url_router')),
]

# Mantén esto para servir archivos de medios en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
