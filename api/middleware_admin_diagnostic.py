"""
Middleware de diagnóstico para verificar tenant en Django Admin
"""
import logging

logger = logging.getLogger(__name__)

class AdminTenantDiagnosticMiddleware:
    """
    Middleware temporal para diagnosticar tenant en Django Admin
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo mostrar diagnóstico en rutas /admin/
        if request.path.startswith('/admin/'):
            domain = request.get_host()
            tenant = getattr(request, 'tenant', None)
            
            print("=" * 70)
            print("🔍 DIAGNÓSTICO ADMIN MIDDLEWARE")
            print("=" * 70)
            print(f"Path: {request.path}")
            print(f"Domain: {domain}")
            print(f"User: {request.user}")
            print(f"Is authenticated: {request.user.is_authenticated}")
            print(f"Is superuser: {request.user.is_superuser if request.user.is_authenticated else False}")
            print(f"Tenant: {tenant}")
            if tenant:
                print(f"Tenant nombre: {tenant.nombre}")
                print(f"Tenant subdomain: {tenant.subdomain}")
            print("=" * 70)
        
        response = self.get_response(request)
        return response
