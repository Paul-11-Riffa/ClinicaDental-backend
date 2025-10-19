"""
Filtros personalizados para el módulo de clínica dental.
"""
from django_filters import rest_framework as filters
from api.models import Servicio


class ServicioFilter(filters.FilterSet):
    """Filtros para el catálogo de servicios"""
    
    # Búsqueda por texto en nombre y descripción
    busqueda = filters.CharFilter(method='buscar_texto', label='Búsqueda en nombre y descripción')
    
    # Filtros de rango de precio
    precio_min = filters.NumberFilter(field_name='costobase', lookup_expr='gte', label='Precio mínimo')
    precio_max = filters.NumberFilter(field_name='costobase', lookup_expr='lte', label='Precio máximo')
    
    # Filtro de duración
    duracion_min = filters.NumberFilter(field_name='duracion', lookup_expr='gte', label='Duración mínima (minutos)')
    duracion_max = filters.NumberFilter(field_name='duracion', lookup_expr='lte', label='Duración máxima (minutos)')
    
    # Filtro de estado activo (por defecto solo muestra activos)
    activo = filters.BooleanFilter(field_name='activo', label='Servicios activos')
    
    class Meta:
        model = Servicio
        fields = ['busqueda', 'precio_min', 'precio_max', 'duracion_min', 'duracion_max', 'activo']
    
    def buscar_texto(self, queryset, name, value):
        """Búsqueda de texto en nombre y descripción"""
        if value:
            return queryset.filter(
                nombre__icontains=value
            ) | queryset.filter(
                descripcion__icontains=value
            )
        return queryset
