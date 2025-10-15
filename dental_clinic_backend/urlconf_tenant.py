# dental_clinic_backend/urlconf_tenant.py

"""
Configuración de URLs para subdominios de tenants.
Solo incluye funcionalidad específica de la clínica dental.
"""

from django.conf import settings
from django.conf.urls.static import static
from .url_patterns import urlpatterns_tenant

# URLs para subdominios de tenants
urlpatterns = urlpatterns_tenant

# URLs estáticas en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)