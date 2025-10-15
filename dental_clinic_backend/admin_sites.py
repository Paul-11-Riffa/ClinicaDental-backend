# dental_clinic_backend/admin_sites.py

from django.contrib import admin

class TenantAdminSite(admin.AdminSite):
    """
    Panel de administración para una clínica específica (tenant).
    Solo muestra datos del tenant actual según el subdominio.
    """
    site_header = 'Administración de la Clínica'
    site_title = 'Portal de Administración'
    index_title = 'Bienvenido al Portal de su Clínica'
    
    def has_permission(self, request):
        """
        Verifica que el usuario tenga permisos y que exista un tenant.
        """
        return (
            request.user.is_active and 
            request.user.is_staff and 
            hasattr(request, 'tenant') and 
            request.tenant is not None
        )

class PublicAdminSite(admin.AdminSite):
    """
    Panel de administración para el sitio público (gestión de tenants).
    Solo para super-administradores que gestionan todas las empresas.
    """
    site_header = 'Administración General del SaaS'
    site_title = 'Portal de Administración General'
    index_title = 'Bienvenido, Super Administrador'
    
    def has_permission(self, request):
        """
        Solo super-usuarios pueden acceder al panel público.
        """
        return request.user.is_active and request.user.is_superuser

# Creamos las instancias que usaremos en el resto del proyecto
tenant_admin_site = TenantAdminSite(name='tenant_admin')
public_admin_site = PublicAdminSite(name='public_admin')