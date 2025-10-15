# dental_clinic_backend/url_router.py

from django.urls import path, include
from django.conf import settings
from .url_patterns import urlpatterns_public, urlpatterns_tenant

def get_urlpatterns():
    """
    Función que devuelve las URLs por defecto.
    """
    # Por defecto, usamos las URLs públicas
    return urlpatterns_public

# Django espera una lista de patrones de URL
urlpatterns = get_urlpatterns()