from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las URLs de notificaciones
router = DefaultRouter()
router.register(r"tipos", views.TipoNotificacionViewSet, basename="tipos")
router.register(r"canales", views.CanalNotificacionViewSet, basename="canales")
# router.register(r"dispositivos", views.DispositivoMovilViewSet, basename="dispositivos")

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='notifications-health'),
    # URLs específicas para notificaciones
]