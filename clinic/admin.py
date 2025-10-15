from django.contrib import admin
from .models import (
    Paciente, Odontologo, Recepcionista, Horario, Tipodeconsulta, 
    Estadodeconsulta, Consulta, Historialclinico, Servicio, 
    Insumo, Medicamento, Recetamedica, Imtemreceta, Estado, 
    Estadodefactura, Tipopago, Plandetratamiento, Piezadental, 
    Itemplandetratamiento, Factura, Itemdefactura
)
from dental_clinic_backend.admin_sites import tenant_admin_site
from tenancy.utils import TenantAwareAdmin

@admin.register(Paciente, site=tenant_admin_site)
class PacienteAdmin(TenantAwareAdmin):
    """Admin para Pacientes - Solo datos del tenant actual."""
    list_display = ('codusuario', 'carnetidentidad', 'fechanacimiento')
    list_filter = ('fechanacimiento',)
    search_fields = ('carnetidentidad', 'codusuario__nombre', 'codusuario__apellido')
    ordering = ('codusuario',)

@admin.register(Odontologo, site=tenant_admin_site)
class OdontologoAdmin(TenantAwareAdmin):
    """Admin para Odontólogos - Solo datos del tenant actual."""
    list_display = ('codusuario', 'especialidad', 'nromatricula')
    list_filter = ('especialidad',)
    search_fields = ('codusuario__nombre', 'codusuario__apellido', 'nromatricula')

@admin.register(Consulta, site=tenant_admin_site)
class ConsultaAdmin(TenantAwareAdmin):
    """Admin para Consultas - Solo datos del tenant actual."""
    list_display = ('fecha', 'codpaciente', 'cododontologo', 'idtipoconsulta', 'idestadoconsulta')
    list_filter = ('idtipoconsulta', 'idestadoconsulta', 'fecha')
    search_fields = ('codpaciente__codusuario__nombre', 'cododontologo__codusuario__nombre')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

@admin.register(Tipodeconsulta, site=tenant_admin_site)
class TipoConsultaAdmin(TenantAwareAdmin):
    """Admin para Tipos de Consulta - Solo datos del tenant actual."""
    list_display = ('nombreconsulta',)
    search_fields = ('nombreconsulta',)

@admin.register(Estadodeconsulta, site=tenant_admin_site)
class EstadoConsultaAdmin(TenantAwareAdmin):
    """Admin para Estados de Consulta - Solo datos del tenant actual."""
    list_display = ('estado',)
    search_fields = ('estado',)

@admin.register(Historialclinico, site=tenant_admin_site)
class HistorialClinicoAdmin(TenantAwareAdmin):
    """Admin para Historiales Clínicos - Solo datos del tenant actual."""
    list_display = ('pacientecodigo', 'episodio', 'fecha')
    list_filter = ('fecha',)
    search_fields = ('pacientecodigo__codusuario__nombre', 'pacientecodigo__codusuario__apellido')
    ordering = ('-fecha',)
    date_hierarchy = 'fecha'

@admin.register(Servicio, site=tenant_admin_site)
class ServicioAdmin(TenantAwareAdmin):
    """Admin para Servicios - Solo datos del tenant actual."""
    list_display = ('nombre', 'costobase')
    search_fields = ('nombre',)

@admin.register(Insumo, site=tenant_admin_site)
class InsumoAdmin(TenantAwareAdmin):
    """Admin para Insumos - Solo datos del tenant actual."""
    list_display = ('nombre', 'stock', 'unidaddemedida')
    search_fields = ('nombre',)

@admin.register(Medicamento, site=tenant_admin_site)
class MedicamentoAdmin(TenantAwareAdmin):
    """Admin para Medicamentos - Solo datos del tenant actual."""
    list_display = ('nombre', 'cantidadmiligramos', 'presentacion')
    search_fields = ('nombre',)

@admin.register(Recetamedica, site=tenant_admin_site)
class RecetaAdmin(TenantAwareAdmin):
    """Admin para Recetas Médicas - Solo datos del tenant actual."""
    list_display = ('codpaciente', 'cododontologo', 'fechaemision')
    list_filter = ('fechaemision',)
    search_fields = ('codpaciente__codusuario__nombre', 'cododontologo__codusuario__nombre')
    ordering = ('-fechaemision',)
    date_hierarchy = 'fechaemision'

@admin.register(Plandetratamiento, site=tenant_admin_site)
class PlanTratamientoAdmin(TenantAwareAdmin):
    """Admin para Planes de Tratamiento - Solo datos del tenant actual."""
    list_display = ('codpaciente', 'fechaplan', 'montototal')
    list_filter = ('fechaplan',)
    search_fields = ('codpaciente__codusuario__nombre', 'codpaciente__codusuario__apellido')

@admin.register(Factura, site=tenant_admin_site)
class FacturaAdmin(TenantAwareAdmin):
    """Admin para Facturas - Solo datos del tenant actual."""
    list_display = ('idplantratamiento', 'fechaemision', 'montototal', 'idestadofactura')
    list_filter = ('idestadofactura', 'fechaemision')
    ordering = ('-fechaemision',)
    date_hierarchy = 'fechaemision'

# Registrar otros modelos simples
tenant_admin_site.register(Recepcionista, TenantAwareAdmin)
tenant_admin_site.register(Horario, TenantAwareAdmin)
tenant_admin_site.register(Imtemreceta, TenantAwareAdmin)
tenant_admin_site.register(Estado, TenantAwareAdmin)
tenant_admin_site.register(Estadodefactura, TenantAwareAdmin)
tenant_admin_site.register(Tipopago, TenantAwareAdmin)
tenant_admin_site.register(Piezadental, TenantAwareAdmin)
tenant_admin_site.register(Itemplandetratamiento, TenantAwareAdmin)
tenant_admin_site.register(Itemdefactura, TenantAwareAdmin)