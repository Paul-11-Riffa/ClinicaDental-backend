from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las URLs de tenancy (gestión de empresas)
router = DefaultRouter()
router.register(r"empresas", views.EmpresaViewSet, basename="empresas")

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='tenancy-health'),
    # URLs específicas para administración de tenants
    # path('register/', views.register_tenant, name='register-tenant'),
    # path('subscribe/', views.stripe_subscription, name='stripe-subscription'),
]