from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .admin_sites import tenant_admin_site, public_admin_site

# Health check endpoint
def health_check(request):
    return JsonResponse({'status': 'ok', 'message': 'Dental Clinic API is running'})

# URLs para el dominio público (localhost:8000)
urlpatterns_public = [
    path('', health_check, name='health_check'),  # Root endpoint
    path('health/', health_check, name='health'),
    path('admin/', public_admin_site.urls),
    path('api/', include('api.urls')),  # Todas las rutas públicas y de tenants
]

# URLs para los subdominios (norte.localhost:8000)
urlpatterns_tenant = [
    path('admin/', tenant_admin_site.urls),
    path('api/', include('api.urls')),  # Todas las rutas del API incluyendo auth
]