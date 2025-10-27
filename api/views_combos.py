"""
ViewSet para gestión de Combos/Paquetes de Servicios Dentales.
Implementa SP3-T007: Crear paquete o combo de servicios (web)
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction, models
from decimal import Decimal

from .models import ComboServicio, ComboServicioDetalle, Bitacora
from .serializers_combos import (
    ComboServicioSerializer,
    ComboServicioCreateUpdateSerializer,
    ComboServicioListSerializer,
    ComboServicioPrevisualizacionSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para listados"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class ComboServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión completa de combos de servicios.
    
    Funcionalidades (SP3-T007):
    a) Crear combo con nombre, descripción, servicios, cantidades y regla de precio
    b) Editar datos y componentes, previsualizar precio final, rechazar totales negativos
    c) Desactivar para bloquear uso futuro
    d) Validar consistencia: sin cantidades inválidas
    e) Guardar desde pantalla de edición
    
    Endpoints:
    - GET /combos/ - Listar combos activos (por defecto)
    - GET /combos/{id}/ - Detalle de combo con precios calculados
    - POST /combos/ - Crear nuevo combo
    - PUT/PATCH /combos/{id}/ - Actualizar combo
    - DELETE /combos/{id}/ - Eliminar combo (soft delete recomendado)
    - POST /combos/previsualizar/ - Previsualizar precio sin guardar
    - POST /combos/{id}/activar/ - Activar combo
    - POST /combos/{id}/desactivar/ - Desactivar combo
    """
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'fecha_creacion', 'precio_final']
    ordering = ['-fecha_creacion']
    filterset_fields = ['activo', 'tipo_precio']
    
    def get_queryset(self):
        """
        Filtrar combos por tenant.
        Por defecto solo muestra combos activos (a menos que se especifique activo=false).
        """
        if hasattr(self.request, 'tenant') and self.request.tenant:
            queryset = ComboServicio.objects.filter(
                empresa=self.request.tenant
            ).prefetch_related('detalles__servicio')
            
            # Por defecto solo mostrar combos activos
            if 'activo' not in self.request.query_params:
                queryset = queryset.filter(activo=True)
            
            return queryset
        return ComboServicio.objects.none()
    
    def get_serializer_class(self):
        """Usar serializer diferente según la acción."""
        if self.action == 'list':
            return ComboServicioListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ComboServicioCreateUpdateSerializer
        elif self.action == 'previsualizar':
            return ComboServicioPrevisualizacionSerializer
        return ComboServicioSerializer
    
    def perform_create(self, serializer):
        """
        Crear combo asociado al tenant con registro en bitácora.
        """
        combo = serializer.save()
        
        # Registrar en bitácora
        usuario = getattr(self.request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion="CREAR_COMBO",
            tabla_afectada="combo_servicio",
            valores_nuevos={"mensaje": f"Creado combo '{combo.nombre}' con {combo.detalles.count()} servicios. Precio final: ${combo.calcular_precio_final()}"},
            ip_address="127.0.0.1",
            user_agent="API"
        )
    
    def perform_update(self, serializer):
        """
        Actualizar combo con registro en bitácora.
        """
        combo = serializer.save()
        
        # Registrar en bitácora
        usuario = getattr(self.request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion="ACTUALIZAR_COMBO",
            tabla_afectada="combo_servicio",
            valores_nuevos={"mensaje": f"Actualizado combo '{combo.nombre}'. Precio final: ${combo.calcular_precio_final()}"},
            ip_address="127.0.0.1",
            user_agent="API"
        )
    
    def perform_destroy(self, instance):
        """
        Eliminar combo con registro en bitácora.
        Nota: Considerar usar soft delete (desactivar) en lugar de eliminación física.
        """
        nombre_combo = instance.nombre
        
        # Registrar en bitácora antes de eliminar
        usuario = getattr(self.request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=self.request.tenant,
            usuario=usuario,
            accion="ELIMINAR_COMBO",
            tabla_afectada="combo_servicio",
            valores_nuevos={"mensaje": f"Eliminado combo '{nombre_combo}'"},
            ip_address="127.0.0.1",
            user_agent="API"
        )
        
        instance.delete()
    
    @action(detail=False, methods=['post'])
    def previsualizar(self, request):
        """
        Previsualiza el precio de un combo sin guardarlo en la base de datos.
        
        Request body:
        {
            "tipo_precio": "PORCENTAJE",
            "valor_precio": 20.00,
            "servicios": [
                {"servicio_id": 1, "cantidad": 1},
                {"servicio_id": 2, "cantidad": 2}
            ]
        }
        
        Response:
        {
            "precio_total_servicios": 500.00,
            "precio_final": 400.00,
            "ahorro": 100.00,
            "detalles": [...]
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'precio_total_servicios': serializer.validated_data['precio_total_servicios'],
            'precio_final': serializer.validated_data['precio_final'],
            'ahorro': serializer.validated_data['ahorro'],
            'tipo_precio': serializer.validated_data['tipo_precio'],
            'valor_precio': serializer.validated_data['valor_precio'],
            'mensaje': 'Previsualización calculada exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        """
        Activa un combo desactivado.
        
        Response:
        {
            "mensaje": "Combo activado exitosamente",
            "combo": {...}
        }
        """
        # Obtener el combo sin filtro de activo
        try:
            combo = ComboServicio.objects.get(pk=pk, empresa=request.tenant)
        except ComboServicio.DoesNotExist:
            return Response({
                'error': 'Combo no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if combo.activo:
            return Response({
                'mensaje': 'El combo ya está activo'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        combo.activo = True
        combo.save()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="ACTIVAR_COMBO",
            tabla_afectada="combo_servicio",
            valores_nuevos={"mensaje": f"Activado combo '{combo.nombre}'"},
            ip_address="127.0.0.1",
            user_agent="API"
        )
        
        serializer = ComboServicioSerializer(combo, context={'request': request})
        return Response({
            'mensaje': 'Combo activado exitosamente',
            'combo': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def desactivar(self, request, pk=None):
        """
        Desactiva un combo para bloquear su uso futuro (SP3-T007.c).
        El combo no se elimina, solo se marca como inactivo.
        
        Response:
        {
            "mensaje": "Combo desactivado exitosamente",
            "combo": {...}
        }
        """
        combo = self.get_object()
        
        if not combo.activo:
            return Response({
                'mensaje': 'El combo ya está desactivado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        combo.activo = False
        combo.save()
        
        # Registrar en bitácora
        usuario = getattr(request.user, 'usuario', None)
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="DESACTIVAR_COMBO",
            tabla_afectada="combo_servicio",
            valores_nuevos={"mensaje": f"Desactivado combo '{combo.nombre}'"},
            ip_address="127.0.0.1",
            user_agent="API"
        )
        
        serializer = ComboServicioSerializer(combo, context={'request': request})
        return Response({
            'mensaje': 'Combo desactivado exitosamente. Ya no estará disponible para nuevas ventas.',
            'combo': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        """
        Obtiene el detalle completo del combo con todos los cálculos.
        Incluye: precio total servicios, precio final, ahorro, duración total.
        """
        combo = self.get_object()
        serializer = ComboServicioSerializer(combo, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtiene estadísticas generales de los combos del tenant.
        
        Response:
        {
            "total_combos": 10,
            "combos_activos": 8,
            "combos_inactivos": 2,
            "combo_mas_economico": {...},
            "combo_mas_completo": {...}
        }
        """
        queryset = self.get_queryset()
        
        # Estadísticas básicas
        total_combos = queryset.count()
        combos_activos = queryset.filter(activo=True).count()
        combos_inactivos = queryset.filter(activo=False).count()
        
        # Combo más económico
        combo_economico = None
        if combos_activos > 0:
            combos_con_precio = []
            for combo in queryset.filter(activo=True):
                try:
                    precio = combo.calcular_precio_final()
                    combos_con_precio.append((combo, precio))
                except:
                    pass
            
            if combos_con_precio:
                combo_min = min(combos_con_precio, key=lambda x: x[1])
                combo_economico = {
                    'id': combo_min[0].id,
                    'nombre': combo_min[0].nombre,
                    'precio_final': combo_min[1]
                }
        
        # Combo más completo (con más servicios)
        combo_completo = None
        if combos_activos > 0:
            combo_max = queryset.filter(activo=True).annotate(
                cantidad=models.Count('detalles')
            ).order_by('-cantidad').first()
            
            if combo_max:
                combo_completo = {
                    'id': combo_max.id,
                    'nombre': combo_max.nombre,
                    'cantidad_servicios': combo_max.detalles.count()
                }
        
        return Response({
            'total_combos': total_combos,
            'combos_activos': combos_activos,
            'combos_inactivos': combos_inactivos,
            'combo_mas_economico': combo_economico,
            'combo_mas_completo': combo_completo
        })
    
    def create(self, request, *args, **kwargs):
        """
        Override para agregar validación adicional y mensajes personalizados.
        """
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            
            # Obtener el combo completo con todos los cálculos
            combo = ComboServicio.objects.get(id=serializer.data['id'])
            response_serializer = ComboServicioSerializer(combo, context={'request': request})
            
            return Response({
                'mensaje': 'Combo creado exitosamente',
                'combo': response_serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
            
        except Exception as e:
            return Response({
                'error': 'Error al crear el combo',
                'detalles': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, *args, **kwargs):
        """
        Override para agregar validación adicional y mensajes personalizados.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            # Obtener el combo completo con todos los cálculos
            combo = ComboServicio.objects.get(id=instance.id)
            response_serializer = ComboServicioSerializer(combo, context={'request': request})
            
            return Response({
                'mensaje': 'Combo actualizado exitosamente',
                'combo': response_serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': 'Error al actualizar el combo',
                'detalles': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
