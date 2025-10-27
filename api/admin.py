from django.contrib import admin
from django.apps import apps
from .models import (
    Empresa, Usuario, Paciente, Odontologo, Recepcionista,
    Consulta, Historialclinico, Bitacora, ComboServicio, ComboServicioDetalle
)
# Importar los admin sites personalizados
from dental_clinic_backend.admin_sites import tenant_admin_site, public_admin_site


class TenantFilteredAdmin(admin.ModelAdmin):
    """
    Admin base que filtra automáticamente por empresa (tenant).
    """
    
    def has_module_permission(self, request):
        """
        CRÍTICO: Este método determina si el módulo aparece en el admin index.
        Los superusers SIEMPRE deben tener permiso para ver módulos.
        """
        # Superusers siempre tienen permiso
        if request.user.is_superuser:
            return True
        
        # Para usuarios normales, verificar permisos estándar
        return super().has_module_permission(request)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Si el usuario es el superuser GLOBAL (username='admin'), ve todo
        if request.user.is_superuser and request.user.username == 'admin':
            return qs
        
        # Para todos los demás usuarios (incluyendo admin_norte, admin_sur, etc.)
        # filtrar por tenant si existe
        if hasattr(request, 'tenant') and request.tenant:
            # Verificar si el modelo tiene campo 'empresa'
            if hasattr(qs.model, 'empresa'):
                return qs.filter(empresa=request.tenant)
            else:
                # Si el modelo NO tiene campo empresa, mostrar todo
                # (ejemplo: ContentType, Permission, Group)
                return qs
        else:
            # Si NO hay tenant detectado, permitir ver datos sin filtro empresa
            # Esto es importante para usuarios superadmin que acceden sin subdomain
            return qs
        
        return qs
    
    def save_model(self, request, obj, form, change):
        # Auto-asignar empresa al crear
        if not change and hasattr(obj, 'empresa') and hasattr(request, 'tenant'):
            if not obj.empresa:
                obj.empresa = request.tenant
        super().save_model(request, obj, form, change)


# Registrar modelos con filtrado por tenant
# IMPORTANTE: Registrar en tenant_admin_site (para subdominios) Y public_admin_site (para admin general)
@admin.register(Empresa, site=tenant_admin_site)
@admin.register(Empresa, site=public_admin_site)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'subdomain', 'activo', 'fecha_creacion')
    list_filter = ('activo',)
    search_fields = ('nombre', 'subdomain')
    
    def has_module_permission(self, request):
        """Superusers siempre tienen permiso"""
        if request.user.is_superuser:
            return True
        return super().has_module_permission(request)


@admin.register(Usuario, site=tenant_admin_site)
@admin.register(Usuario, site=public_admin_site)
class UsuarioAdmin(TenantFilteredAdmin):
    list_display = ('codigo', 'nombre', 'apellido', 'correoelectronico', 'empresa', 'idtipousuario')
    list_filter = ('idtipousuario', 'empresa')
    search_fields = ('nombre', 'apellido', 'correoelectronico')


@admin.register(Paciente, site=tenant_admin_site)
@admin.register(Paciente, site=public_admin_site)
class PacienteAdmin(TenantFilteredAdmin):
    list_display = ('get_nombre', 'carnetidentidad', 'fechanacimiento', 'empresa')
    search_fields = ('codusuario__nombre', 'codusuario__apellido', 'carnetidentidad')
    
    def get_nombre(self, obj):
        return f"{obj.codusuario.nombre} {obj.codusuario.apellido}"
    get_nombre.short_description = 'Nombre Completo'


@admin.register(Odontologo, site=tenant_admin_site)
@admin.register(Odontologo, site=public_admin_site)
class OdontologoAdmin(TenantFilteredAdmin):
    list_display = ('get_nombre', 'especialidad', 'nromatricula', 'empresa')
    search_fields = ('codusuario__nombre', 'codusuario__apellido', 'nromatricula')
    
    def get_nombre(self, obj):
        return f"Dr. {obj.codusuario.nombre} {obj.codusuario.apellido}"
    get_nombre.short_description = 'Nombre Completo'


@admin.register(Recepcionista, site=tenant_admin_site)
@admin.register(Recepcionista, site=public_admin_site)
class RecepcionistaAdmin(TenantFilteredAdmin):
    list_display = ('get_nombre', 'empresa')
    search_fields = ('codusuario__nombre', 'codusuario__apellido')
    
    def get_nombre(self, obj):
        return f"{obj.codusuario.nombre} {obj.codusuario.apellido}"
    get_nombre.short_description = 'Nombre Completo'


@admin.register(Consulta, site=tenant_admin_site)
@admin.register(Consulta, site=public_admin_site)
class ConsultaAdmin(TenantFilteredAdmin):
    list_display = ('id', 'fecha', 'get_paciente', 'get_odontologo', 'idestadoconsulta', 'empresa')
    list_filter = ('fecha', 'idestadoconsulta', 'empresa')
    search_fields = ('codpaciente__codusuario__nombre', 'codpaciente__codusuario__apellido')
    
    def get_paciente(self, obj):
        return f"{obj.codpaciente.codusuario.nombre} {obj.codpaciente.codusuario.apellido}"
    get_paciente.short_description = 'Paciente'
    
    def get_odontologo(self, obj):
        if obj.cododontologo:
            return f"Dr. {obj.cododontologo.codusuario.nombre}"
        return '-'
    get_odontologo.short_description = 'Odontólogo'


@admin.register(Historialclinico, site=tenant_admin_site)
@admin.register(Historialclinico, site=public_admin_site)
class HistorialclinicoAdmin(TenantFilteredAdmin):
    list_display = ('id', 'get_paciente', 'episodio', 'fecha', 'empresa')
    list_filter = ('fecha', 'empresa')
    search_fields = ('pacientecodigo__codusuario__nombre',)
    
    def get_paciente(self, obj):
        return f"{obj.pacientecodigo.codusuario.nombre} {obj.pacientecodigo.codusuario.apellido}"
    get_paciente.short_description = 'Paciente'


@admin.register(Bitacora, site=tenant_admin_site)
@admin.register(Bitacora, site=public_admin_site)
class BitacoraAdmin(TenantFilteredAdmin):
    list_display = ('id', 'get_usuario', 'accion', 'tabla_afectada', 'timestamp', 'empresa')
    list_filter = ('accion', 'timestamp', 'empresa')
    readonly_fields = ('usuario', 'accion', 'tabla_afectada', 'timestamp', 'ip_address', 'user_agent')
    
    def get_usuario(self, obj):
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return 'Sistema'
    get_usuario.short_description = 'Usuario'


# ===== COMBOS DE SERVICIOS =====

class ComboServicioDetalleInline(admin.TabularInline):
    """Inline para mostrar servicios dentro del combo"""
    model = ComboServicioDetalle
    extra = 1
    fields = ('servicio', 'cantidad', 'orden', 'get_subtotal')
    readonly_fields = ('get_subtotal',)
    
    def get_subtotal(self, obj):
        if obj.id:
            return f"${obj.calcular_subtotal()}"
        return "-"
    get_subtotal.short_description = 'Subtotal'


@admin.register(ComboServicio, site=tenant_admin_site)
@admin.register(ComboServicio, site=public_admin_site)
class ComboServicioAdmin(TenantFilteredAdmin):
    list_display = ('id', 'nombre', 'tipo_precio', 'valor_precio', 'get_precio_final', 
                    'get_cantidad_servicios', 'activo', 'empresa', 'fecha_creacion')
    list_filter = ('activo', 'tipo_precio', 'fecha_creacion', 'empresa')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('get_precio_total_servicios', 'get_precio_final', 'get_ahorro', 
                       'get_duracion_total', 'fecha_creacion', 'fecha_modificacion')
    inlines = [ComboServicioDetalleInline]
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Configuración de Precio', {
            'fields': ('tipo_precio', 'valor_precio')
        }),
        ('Cálculos', {
            'fields': ('get_precio_total_servicios', 'get_precio_final', 'get_ahorro', 'get_duracion_total'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_modificacion', 'empresa'),
            'classes': ('collapse',)
        })
    )
    
    def get_precio_final(self, obj):
        try:
            return f"${obj.calcular_precio_final()}"
        except ValueError as e:
            return f"Error: {e}"
    get_precio_final.short_description = 'Precio Final'
    
    def get_precio_total_servicios(self, obj):
        return f"${obj.calcular_precio_total_servicios()}"
    get_precio_total_servicios.short_description = 'Precio Total Servicios'
    
    def get_ahorro(self, obj):
        try:
            precio_servicios = obj.calcular_precio_total_servicios()
            precio_final = obj.calcular_precio_final()
            ahorro = precio_servicios - precio_final
            return f"${ahorro}" if ahorro > 0 else "$0.00"
        except:
            return "$0.00"
    get_ahorro.short_description = 'Ahorro'
    
    def get_duracion_total(self, obj):
        return f"{obj.calcular_duracion_total()} min"
    get_duracion_total.short_description = 'Duración Total'
    
    def get_cantidad_servicios(self, obj):
        return obj.detalles.count()
    get_cantidad_servicios.short_description = 'Servicios'


# Registrar el resto de modelos automáticamente
app_config = apps.get_app_config("api")

for model in app_config.get_models():
    # Saltar los que ya registramos manualmente
    if model in [Empresa, Usuario, Paciente, Odontologo, Recepcionista, 
                 Consulta, Historialclinico, Bitacora, ComboServicio, ComboServicioDetalle]:
        continue
    
    try:
        # Registrar en AMBOS admin sites
        if hasattr(model, 'empresa'):
            tenant_admin_site.register(model, TenantFilteredAdmin)
            public_admin_site.register(model, TenantFilteredAdmin)
        else:
            tenant_admin_site.register(model)
            public_admin_site.register(model)
    except admin.sites.AlreadyRegistered:
        pass


