"""
URL configuration for dental_clinic_backend project.

Sistema de enrutamiento dinámico para Multi-Tenancy:
- Dominio público: Administración de tenants y landing page
- Subdominios: Aplicación de clínica dental específica por tenant
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static

# Importar los patrones de URL dinámicos
from .url_patterns import urlpatterns_public, urlpatterns_tenant


def api_welcome(request):
    """Vista de bienvenida adaptativa según el contexto."""
    tenant = getattr(request, 'tenant', None)
    
    if tenant:
        # Vista para tenant específico
        return JsonResponse({
            "message": f"🦷 {tenant.nombre} - API Clínica Dental",
            "tenant": tenant.nombre,
            "subdomain": tenant.subdomain,
            "version": "1.0.0",
            "status": "online",
            "endpoints": {
                "pacientes": "/api/clinic/pacientes/",
                "consultas": "/api/clinic/consultas/",
                "usuarios": "/api/users/usuarios/",
                "notificaciones": "/api/notifications/tipos/",
            }
        })
    else:
        # Vista para dominio público
        return JsonResponse({
            "message": "🏢 Dental Clinic SaaS - Portal de Administración",
            "description": "Sistema de gestión multi-tenant para clínicas dentales",
            "version": "1.0.0",
            "status": "online",
            "endpoints": {
                "admin": "/admin/",
                "tenancy": "/api/tenancy/",
                "documentation": "Coming soon"
            }
        })


# Por defecto, incluir todas las apps para desarrollo
# El middleware dinámico se encargará de cambiar esto según el tenant
urlpatterns = [
    path("", api_welcome, name="welcome"),
    path("admin/", admin.site.urls),
    path("api/tenancy/", include("tenancy.urls")),
    path("api/clinic/", include("clinic.urls")),
    path("api/users/", include("users.urls")),
    path("api/notifications/", include("notifications.urls")),
]

# URLs estáticas en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_URL)
