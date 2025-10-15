# dental_clinic_backend/urlconf_public.py

"""
Configuración de URLs para el dominio público.
Solo incluye administración de tenants y endpoints públicos.
"""

from django.conf import settings
from django.conf.urls.static import static
from .url_patterns import urlpatterns_public

# URLs para el dominio público
urlpatterns = urlpatterns_public

# URLs estáticas en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)