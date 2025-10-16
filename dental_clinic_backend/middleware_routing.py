# dental_clinic_backend/middleware_routing.py

"""
Middleware para routing dinámico de URLs basado en tenants.
Cambia los patrones de URL según si hay un tenant o no.
"""

from django.urls import set_urlconf
from django.conf import settings
import importlib
import logging

logger = logging.getLogger(__name__)


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
        tenant = getattr(request, 'tenant', None)
        
        if tenant:
            # Hay un tenant, usar URLs del tenant
            request.urlconf = 'dental_clinic_backend.urlconf_tenant'
            logger.info(f"[TenantRoutingMiddleware] Tenant detected: {tenant.nombre} -> using urlconf_tenant")
        else:
            # No hay tenant, usar URLs públicas  
            request.urlconf = 'dental_clinic_backend.urlconf_public'
            logger.info(f"[TenantRoutingMiddleware] No tenant -> using urlconf_public")
        
        response = self.get_response(request)
        
        return response