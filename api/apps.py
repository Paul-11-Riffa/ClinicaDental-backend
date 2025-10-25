from django.apps import AppConfig

class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        # importa y registra los signals del módulo notifications_mobile
        import api.notifications_mobile.signals_consulta  # noqa: F401
        # importa y registra los signals de gestión de roles de usuario
        import api.signals_usuario  # noqa: F401
        # importa y registra los signals de aceptación de presupuestos
        import api.signals_presupuestos  # noqa: F401
        # importa y registra los signals de gestión de planes de tratamiento (SP3-T001)
        import api.signals_plan_tratamiento  # noqa: F401
