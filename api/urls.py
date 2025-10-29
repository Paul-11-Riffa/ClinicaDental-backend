from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter

from . import views, views_auth, views_saas, views_stripe, views_user_creation
from .views import UserProfileView, ping
from no_show_policies.views import PoliticaNoShowViewSet  # App externa

router = DefaultRouter()
router.register(r"pacientes", views.PacienteViewSet, basename="pacientes")
router.register(r"consultas", views.ConsultaViewSet, basename="consultas")
router.register(r"odontologos", views.OdontologoViewSet, basename="odontologos")

router.register(r"politicas-no-show", PoliticaNoShowViewSet, basename="politicas-no-show")
router.register(r"estadodeconsultas", views.EstadodeconsultaViewSet, basename="estadodeconsultas")

router.register(r"horarios", views.HorarioViewSet, basename="horarios")
router.register(r"tipos-consulta", views.TipodeconsultaViewSet, basename="tipos-consulta")

# Admin
router.register(r"tipos-usuario", views.TipodeusuarioViewSet, basename="tipos-usuario")
router.register(r"usuarios", views.UsuarioViewSet, basename="usuarios")
router.register(r"bitacora", views.BitacoraViewSet, basename="bitacora")
router.register(r"reportes", views.ReporteViewSet, basename="reportes")

# Historias Clínicas (HCE)
router.register(r"historias-clinicas", views.HistorialclinicoViewSet, basename="historias-clinicas")

# Consentimiento Digital
router.register(r"consentimientos", views.ConsentimientoViewSet, basename="consentimientos")

# Presupuestos y Aceptaciones (SP3-T003)
from .views_presupuestos import PresupuestoViewSet, AceptacionPresupuestoViewSet
router.register(r"presupuestos", PresupuestoViewSet, basename="presupuestos")
router.register(r"aceptaciones", AceptacionPresupuestoViewSet, basename="aceptaciones")

# Planes de Tratamiento (SP3-T001)
from .views_plan_tratamiento import PlanTratamientoViewSet
router.register(r"planes-tratamiento", PlanTratamientoViewSet, basename="planes-tratamiento")

# Presupuestos Digitales (SP3-T002)
from .views_presupuesto_digital import PresupuestoDigitalViewSet
router.register(r"presupuestos-digitales", PresupuestoDigitalViewSet, basename="presupuestos-digitales")

# Combos de Servicios (SP3-T007)
from .views_combos import ComboServicioViewSet
router.register(r"combos-servicios", ComboServicioViewSet, basename="combos-servicios")

# Sesiones de Tratamiento (SP3-T008)
from .views_sesiones import SesionTratamientoViewSet
router.register(r"sesiones-tratamiento", SesionTratamientoViewSet, basename="sesiones-tratamiento")

# Flujo Clínico (PASO 3 - APIs)
from .views_flujo_clinico import (
    ConsultaFlujoClincoViewSet,
    PlanTratamientoFlujoClincoViewSet,
    ItemPlanTratamientoFlujoClincoViewSet
)
router.register(r"flujo-clinico/consultas", ConsultaFlujoClincoViewSet, basename="flujo-consultas")
router.register(r"flujo-clinico/planes", PlanTratamientoFlujoClincoViewSet, basename="flujo-planes")
router.register(r"flujo-clinico/items", ItemPlanTratamientoFlujoClincoViewSet, basename="flujo-items")

# Upload de Evidencias (SP3-T008 FASE 5)
from .views_evidencias import upload_evidencia, delete_evidencia, listar_evidencias

# Creación de Usuarios (Admin)
router.register(r"crear-usuario", views_user_creation.CrearUsuarioViewSet, basename="crear-usuario")

urlpatterns = [
    # Health/basic
    path("health/", views.health),
    path("db/", views.db_info),
    path("users/count/", views.users_count),
    path("ping/", ping),

    # Público (SaaS)
    path("public/registrar-empresa/", views_saas.registrar_empresa, name="registrar-empresa"),
    path("public/validar-subdomain/", views_saas.validar_subdomain, name="validar-subdomain"),
    path("public/info/", views_saas.info_sistema, name="info-sistema"),
    path("public/empresa/<str:subdomain>/", views_saas.verificar_empresa_por_subdomain, name="verificar-empresa"),

    # Stripe (Pagos)
    path("public/create-payment-intent/", views_stripe.create_payment_intent, name="create-payment-intent"),
    path("public/registrar-empresa-pago/", views_stripe.registrar_empresa_con_pago, name="registrar-empresa-pago"),
    path("public/stripe-webhook/", views_stripe.stripe_webhook, name="stripe-webhook"),

    # Auth
    path("auth/csrf/", views_auth.csrf_token),
    path("auth/register/", csrf_exempt(views_auth.auth_register)),
    path("auth/login/", csrf_exempt(views_auth.auth_login)),
    path("auth/logout/", views_auth.auth_logout),

    # Perfil de usuario (única ruta para evitar conflicto)
    path("auth/user/", UserProfileView.as_view(), name="user-profile"),

    # Perfil legacy (si aún lo usan en frontend)
    path("usuario/me", views_auth.UsuarioMeView.as_view(), name="usuario-me"),

    # Reset de contraseña
    path("auth/password-reset/", views_auth.password_reset_request),
    path("auth/password-reset-confirm/", views_auth.password_reset_confirm),

    # Notificaciones y preferencias
    path("notificaciones/", include("api.urls_notifications")),
    path("auth/user/settings/", views_auth.auth_user_settings_update),
    path("auth/user/notifications/", views_auth.notification_preferences),

    # Upload de Evidencias (SP3-T008 FASE 5)
    path("upload/evidencias/", upload_evidencia, name="upload-evidencia"),
    path("upload/evidencias/<int:evidencia_id>/", delete_evidencia, name="delete-evidencia"),
    path("evidencias/", listar_evidencias, name="listar-evidencias"),
    
    # Pagos en Línea (SP3-T009)
    path("", include("api.urls_pagos")),

    # Rutas de los ViewSets
    path("", include(router.urls)),

    # Clinic app - Alias para /api/clinic/servicios/
    path("clinic/", include("clinic.urls")),

    # Users app - Alias para /api/users/odontologos/
    path("users/", include("users.urls")),

    # Notificaciones mobile
    path("mobile-notif/", include("api.notifications_mobile.urls")),
    
    # Chatbot
    path("chatbot/", include("chatbot.urls")),
]