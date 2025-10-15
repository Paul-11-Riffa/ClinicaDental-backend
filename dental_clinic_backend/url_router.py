"""
Enrutador dinámico para Multi-Tenancy.

Este módulo determina qué conjunto de URLs cargar según si la petición
viene del dominio público o de un subdominio de tenant.
"""

from django.urls import include, path
from django.conf import settings
from django.http import Http404


def dynamic_url_resolver(request):
    """
    Determina qué conjunto de URLs usar basado en el tenant.
    
    Returns:
        tuple: (urlpatterns, prefix)
    """
    from .url_patterns import urlpatterns_public, urlpatterns_tenant
    
    # Obtener el tenant del request (configurado por TenantMiddleware)
    tenant = getattr(request, 'tenant', None)
    
    if tenant:
        # Es un subdominio de tenant -> usar URLs de clínica
        return urlpatterns_tenant, ''
    else:
        # Es el dominio público -> usar URLs de administración
        return urlpatterns_public, ''


class DynamicURLResolver:
    """
    Resolver dinámico de URLs que cambia según el tenant.
    """
    
    def __init__(self):
        pass
    
    def resolve(self, request):
        """
        Resuelve las URLs apropiadas para la petición actual.
        """
        urlpatterns, prefix = dynamic_url_resolver(request)
        return urlpatterns


# Esta será la función que Django llamará
def get_urlpatterns(request=None):
    """
    Función principal que devuelve las URLs correctas.
    
    Si no hay request (durante el startup), devuelve URLs públicas por defecto.
    """
    if request is None:
        # Durante el startup de Django, usar URLs públicas por defecto
        from .url_patterns import urlpatterns_public
        return urlpatterns_public
    
    urlpatterns, prefix = dynamic_url_resolver(request)
    return urlpatterns


# Middleware personalizado para inyectar las URLs correctas
class DynamicURLMiddleware:
    """
    Middleware que actualiza las URLs según el tenant.
    Debe ejecutarse DESPUÉS de TenantMiddleware.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # El TenantMiddleware ya debe haber configurado request.tenant
        urlpatterns = get_urlpatterns(request)
        
        # Guardar las URLs en el request para que Django las use
        request.urlconf = urlpatterns
        
        response = self.get_response(request)
        return response