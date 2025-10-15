# tenancy/utils.py

from django.contrib import admin
from django.core.exceptions import PermissionDenied

class TenantAwareAdmin(admin.ModelAdmin):
    """
    Una clase ModelAdmin base que automáticamente filtra los datos
    por el tenant actual y asocia nuevos objetos al tenant.
    
    Todos los admin de modelos con campo 'empresa' deben heredar de esta clase
    para garantizar el aislamiento de datos por tenant.
    """
    
    def get_queryset(self, request):
        """
        Filtra el listado de objetos para mostrar solo los del tenant actual.
        """
        queryset = super().get_queryset(request)
        
        # Verificar que existe un tenant en la request
        if not hasattr(request, 'tenant') or not request.tenant:
            # Si no hay tenant, no mostrar ningún dato
            return queryset.none()
        
        # Filtrar solo los objetos del tenant actual
        if hasattr(queryset.model, 'empresa'):
            return queryset.filter(empresa=request.tenant)
        
        # Si el modelo no tiene campo empresa, retornar queryset vacío por seguridad
        return queryset.none()
    
    def save_model(self, request, obj, form, change):
        """
        Al guardar un objeto, lo asocia automáticamente al tenant actual.
        """
        # Verificar que existe un tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied("No se puede guardar sin un tenant válido")
        
        # Solo asignar empresa si el objeto no tiene una ya asignada (nuevo objeto)
        if hasattr(obj, 'empresa') and not change:
            obj.empresa = request.tenant
        elif hasattr(obj, 'empresa') and change:
            # En caso de edición, verificar que el objeto pertenece al tenant actual
            if obj.empresa != request.tenant:
                raise PermissionDenied("No tiene permisos para editar este objeto")
        
        super().save_model(request, obj, form, change)
    
    def get_form(self, request, obj=None, **kwargs):
        """
        Personaliza el formulario para ocultar el campo empresa del admin del tenant.
        """
        form = super().get_form(request, obj, **kwargs)
        
        # Ocultar el campo empresa del formulario ya que se asigna automáticamente
        if 'empresa' in form.base_fields:
            form.base_fields['empresa'].widget = admin.widgets.HiddenInput()
            form.base_fields['empresa'].required = False
        
        return form
    
    def has_view_permission(self, request, obj=None):
        """
        Verifica permisos de visualización considerando el tenant.
        """
        if not super().has_view_permission(request, obj):
            return False
        
        # Si es un objeto específico, verificar que pertenece al tenant
        if obj and hasattr(obj, 'empresa'):
            return obj.empresa == getattr(request, 'tenant', None)
        
        return True
    
    def has_change_permission(self, request, obj=None):
        """
        Verifica permisos de edición considerando el tenant.
        """
        if not super().has_change_permission(request, obj):
            return False
        
        # Si es un objeto específico, verificar que pertenece al tenant
        if obj and hasattr(obj, 'empresa'):
            return obj.empresa == getattr(request, 'tenant', None)
        
        return True
    
    def has_delete_permission(self, request, obj=None):
        """
        Verifica permisos de eliminación considerando el tenant.
        """
        if not super().has_delete_permission(request, obj):
            return False
        
        # Si es un objeto específico, verificar que pertenece al tenant
        if obj and hasattr(obj, 'empresa'):
            return obj.empresa == getattr(request, 'tenant', None)
        
        return True


class PublicAdminMixin(admin.ModelAdmin):
    """
    Mixin para modelos que solo deben ser accesibles desde el admin público.
    Usado principalmente para gestión de Empresas por super-administradores.
    """
    
    def has_module_permission(self, request):
        """
        Solo super-usuarios pueden ver estos módulos.
        """
        return request.user.is_superuser
    
    def has_view_permission(self, request, obj=None):
        """
        Solo super-usuarios pueden ver estos objetos.
        """
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """
        Solo super-usuarios pueden agregar estos objetos.
        """
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """
        Solo super-usuarios pueden editar estos objetos.
        """
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """
        Solo super-usuarios pueden eliminar estos objetos.
        """
        return request.user.is_superuser