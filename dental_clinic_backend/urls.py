"""
URL configuration for dental_clinic_backend project.

Sistema de enrutamiento dinámico para Multi-Tenancy:
- Dominio público: Administración de tenants y landing page
- Subdominios: Aplicación de clínica dental específica por tenant
"""
from django.conf import settings
from django.conf.urls.static import static

# Importar los patrones de URL dinámicos
from .url_patterns import urlpatterns_public, urlpatterns_tenant


def get_urlpatterns(request=None):
    """
    Función para obtener los patrones de URL según el contexto.
    Si hay un tenant, usar patrones de tenant; sino, usar patrones públicos.
    """
    if request and hasattr(request, 'tenant') and request.tenant:
        return urlpatterns_tenant
    else:
        return urlpatterns_public


# Django necesita una variable urlpatterns por defecto
# El middleware TenantRoutingMiddleware se encargará del routing dinámico
urlpatterns = urlpatterns_public  # Por defecto, usar el patrón público

# URLs estáticas en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
