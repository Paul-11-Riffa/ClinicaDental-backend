from django.contrib import admin
from .models import Empresa
from dental_clinic_backend.admin_sites import public_admin_site
from .utils import PublicAdminMixin

@admin.register(Empresa, site=public_admin_site)
class EmpresaAdmin(PublicAdminMixin, admin.ModelAdmin):
    """
    Admin para gestión de Empresas en el panel público.
    Solo accesible por super-administradores.
    """
    list_display = ('nombre', 'subdomain', 'activo', 'fecha_creacion', 'stripe_customer_id')
    list_filter = ('activo', 'fecha_creacion')
    search_fields = ('nombre', 'subdomain', 'stripe_customer_id')
    ordering = ('-fecha_creacion',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'subdomain', 'activo')
        }),
        ('Integración Stripe', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion',),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('fecha_creacion',)
    
    def get_readonly_fields(self, request, obj=None):
        """
        En edición, el subdominio no debería cambiar para evitar problemas.
        """
        readonly_fields = list(self.readonly_fields)
        if obj:  # Si está editando (no creando)
            readonly_fields.append('subdomain')
        return readonly_fields
