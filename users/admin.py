from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Usuario, Tipodeusuario, Bitacora
from dental_clinic_backend.admin_sites import tenant_admin_site
from tenancy.utils import TenantAwareAdmin

@admin.register(Usuario, site=tenant_admin_site)
class UsuarioAdmin(TenantAwareAdmin):
    """
    Admin para Usuarios - Solo datos del tenant actual.
    """
    list_display = ('codigo', 'nombre', 'apellido', 'correoelectronico', 'idtipousuario')
    list_filter = ('idtipousuario', 'sexo')
    search_fields = ('nombre', 'apellido', 'correoelectronico')
    ordering = ('codigo',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'correoelectronico', 'sexo', 'telefono')
        }),
        ('Configuración de Cuenta', {
            'fields': ('idtipousuario', 'recibir_notificaciones', 'notificaciones_email', 'notificaciones_push')
        })
    )

@admin.register(Tipodeusuario, site=tenant_admin_site)
class TipodeusuarioAdmin(TenantAwareAdmin):
    """
    Admin para Tipos de Usuario - Solo datos del tenant actual.
    """
    list_display = ('rol', 'descripcion')
    search_fields = ('rol',)
    ordering = ('rol',)

@admin.register(Bitacora, site=tenant_admin_site)
class BitacoraAdmin(TenantAwareAdmin):
    """
    Admin para Bitácora - Solo datos del tenant actual.
    """
    list_display = ('usuario', 'accion', 'tabla_afectada', 'timestamp')
    list_filter = ('accion', 'timestamp')
    search_fields = ('usuario__nombre', 'accion', 'tabla_afectada')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    readonly_fields = ('usuario', 'accion', 'tabla_afectada', 'registro_id', 'valores_anteriores', 'valores_nuevos', 'ip_address', 'user_agent', 'timestamp')
    
    def has_add_permission(self, request):
        """Las entradas de bitácora no se pueden crear manualmente."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Las entradas de bitácora no se pueden modificar."""
        return False