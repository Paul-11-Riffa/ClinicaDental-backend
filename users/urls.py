from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las URLs de usuarios
router = DefaultRouter()
router.register(r"usuarios", views.UsuarioViewSet, basename="usuarios")
router.register(r"tipos-usuario", views.TipodeusuarioViewSet, basename="tipos-usuario")

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='users-health'),
    # URLs específicas para autenticación
    # path('auth/', include('users.auth_urls')),
]