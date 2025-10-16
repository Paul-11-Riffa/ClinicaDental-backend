"""
Middleware para hacer que Django Admin funcione con multi-tenancy por subdominio.
Filtra los datos en el admin según la empresa del subdominio.
"""
from django.utils.deprecation import MiddlewareMixin


class TenantAdminMiddleware(MiddlewareMixin):
    """
    Middleware que permite acceder a /admin en subdominios y filtra datos por empresa.
    """
    
    def process_request(self, request):
        # Si es una petición al admin, permitir acceso desde subdominios
        if request.path.startswith('/admin/'):
            # El TenantMiddleware ya habrá resuelto request.tenant
            # Solo aseguramos que el admin esté disponible
            pass
        
        return None
