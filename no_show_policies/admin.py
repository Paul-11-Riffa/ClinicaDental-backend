from django.contrib import admin
from .models import PoliticaNoShow, Multa
from dental_clinic_backend.admin_sites import tenant_admin_site, public_admin_site


@admin.register(PoliticaNoShow, site=tenant_admin_site)
@admin.register(PoliticaNoShow, site=public_admin_site)
class PoliticaNoShowAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "empresa", "estado_consulta", "penalizacion_economica", "bloqueo_temporal", "dias_bloqueo", "activo")
    list_filter = ("empresa", "estado_consulta", "activo", "bloqueo_temporal")
    search_fields = ("nombre",)


@admin.register(Multa, site=tenant_admin_site)
@admin.register(Multa, site=public_admin_site)
class MultaAdmin(admin.ModelAdmin):
    list_display = ("id", "empresa", "usuario", "consulta", "monto", "estado", "creado_en")
    list_filter = ("empresa", "estado", "creado_en")
    search_fields = ("usuario__nombre", "usuario__apellido", "consulta__id", "motivo")