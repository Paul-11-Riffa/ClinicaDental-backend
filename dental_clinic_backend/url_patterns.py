from django.urls import path, include
from django.http import JsonResponse
from .admin_sites import tenant_admin_site, public_admin_site


def tenant_welcome(request):
    """Vista de bienvenida para tenants."""
    tenant = getattr(request, 'tenant', None)
    return JsonResponse({
        "message": f"🦷 Bienvenido a {tenant.nombre if tenant else 'Clínica Dental'}",
        "tenant": tenant.nombre if tenant else None,
        "subdomain": tenant.subdomain if tenant else None,
        "endpoints": {
            "admin": "/admin/",  # Admin específico del tenant
            "pacientes": "/api/clinic/pacientes/",
            "consultas": "/api/clinic/consultas/",
            "usuarios": "/api/users/usuarios/",
            "notificaciones": "/api/notifications/tipos/",
        }
    })


def public_welcome(request):
    """Vista de bienvenida para el dominio público."""
    return JsonResponse({
        "message": "🏢 Portal de Administración - Dental Clinic SaaS",
        "description": "Gestión centralizada de clínicas dentales",
        "endpoints": {
            "admin": "/admin/",  # Admin público para super-administradores
            "tenancy": "/api/tenancy/",
            "register": "/api/tenancy/register/",
        }
    })


# URLs para el dominio público (administración de tenants)
urlpatterns_public = [
    path('', public_welcome, name='public-welcome'),
    path('admin/', public_admin_site.urls),  # Admin público para super-administradores
    path('api/tenancy/', include('tenancy.urls')),
]

# URLs para los subdominios de los tenants (la app de la clínica)
urlpatterns_tenant = [
    path('', tenant_welcome, name='tenant-welcome'),
    path('admin/', tenant_admin_site.urls),  # Admin del tenant para datos de la clínica
    path('api/clinic/', include('clinic.urls')),
    path('api/users/', include('users.urls')),
    path('api/notifications/', include('notifications.urls')),
    # path('api/policies/', include('no_show_policies.urls')),  # Agregar cuando migremos
]