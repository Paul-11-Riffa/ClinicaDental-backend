from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para las URLs de la clínica dental
router = DefaultRouter()
router.register(r"pacientes", views.PacienteViewSet, basename="pacientes")
router.register(r"consultas", views.ConsultaViewSet, basename="consultas")
router.register(r"odontologos", views.OdontologoViewSet, basename="odontologos")
router.register(r"servicios", views.ServicioViewSet, basename="servicios")

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='clinic-health'),
    # URLs específicas para funcionalidades de clínica
]