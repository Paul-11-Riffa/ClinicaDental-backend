from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from .admin_sites import tenant_admin_site, public_admin_site

# URLs para el dominio público (localhost:8000)
urlpatterns_public = [
    path('admin/', public_admin_site.urls),
    path('api/', include('api.urls')),  # Todas las rutas públicas y de tenants
]

# URLs para los subdominios (norte.localhost:8000)
urlpatterns_tenant = [
    path('admin/', tenant_admin_site.urls),
    path('api/', include('api.urls')),  # Todas las rutas del API incluyendo auth
]