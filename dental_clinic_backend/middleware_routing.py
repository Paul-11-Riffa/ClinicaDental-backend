# dental_clinic_backend/middleware_routing.py

"""
Middleware para routing dinámico de URLs basado en tenants.
Cambia los patrones de URL según si hay un tenant o no.
"""

from django.urls import set_urlconf
from django.conf import settings
import importlib


class TenantRoutingMiddleware:
    """
    Middleware que cambia dinámicamente las URLs según el tenant.
    
    - Si hay tenant: Usa urlpatterns_tenant
    - Si no hay tenant: Usa urlpatterns_public
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Determinar qué configuración de URLs usar
        if hasattr(request, 'tenant') and request.tenant:
            # Hay un tenant, usar URLs del tenant
            request.urlconf = 'dental_clinic_backend.urlconf_tenant'
        else:
            # No hay tenant, usar URLs públicas  
            request.urlconf = 'dental_clinic_backend.urlconf_public'
        
        response = self.get_response(request)
        
        return response