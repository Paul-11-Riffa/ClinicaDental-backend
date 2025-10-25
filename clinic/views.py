from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework import viewsets, permissions, filters, status
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from api.models import Paciente, Consulta, Odontologo, Servicio, Piezadental
from .serializers import (
    PacienteSerializer, 
    ConsultaSerializer, 
    OdontologoSerializer, 
    ServicioSerializer,
    ServicioListSerializer,
    PiezadentalSerializer
)
from .filters import ServicioFilter


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para listados"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_check(request):
    """Health check para el módulo de clínica - REQUIERE AUTENTICACIÓN"""
    return Response({
        'status': 'healthy',
        'module': 'clinic',
        'tenant': getattr(request, 'tenant', None),
        'user': request.user.username if request.user.is_authenticated else None,
        'message': 'Acceso autorizado a módulo de clínica',
    })

class PacienteViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de pacientes - REQUIERE AUTENTICACIÓN"""
    serializer_class = PacienteSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar pacientes por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Paciente.objects.filter(empresa=self.request.tenant)
        return Paciente.objects.none()

    def perform_create(self, serializer):
        """Crear paciente asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear paciente")

class ConsultaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de consultas - REQUIERE AUTENTICACIÓN"""
    serializer_class = ConsultaSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar consultas por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Consulta.objects.filter(empresa=self.request.tenant)
        return Consulta.objects.none()

    def perform_create(self, serializer):
        """Crear consulta asociada al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear consulta")

class OdontologoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de odontólogos - REQUIERE AUTENTICACIÓN"""
    serializer_class = OdontologoSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar odontólogos por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Odontologo.objects.filter(empresa=self.request.tenant)
        return Odontologo.objects.none()

    def perform_create(self, serializer):
        """Crear odontólogo asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear odontólogo")

class ServicioViewSet(viewsets.ModelViewSet):
    """
    ViewSet para catálogo de servicios - ACCESO PÚBLICO PARA CONSULTA
    
    Permite a pacientes y visitantes consultar el catálogo de servicios sin autenticación.
    Las operaciones de creación, actualización y eliminación requieren autenticación.
    
    Funcionalidades:
    - Búsqueda por texto en nombre y descripción
    - Filtros por rango de precio y duración
    - Ordenamiento por nombre, precio o duración
    - Paginación configurable
    - Solo muestra servicios activos por defecto
    - Vista de detalle con precio vigente
    - Acceso público para lectura (GET)
    - Autenticación requerida para escritura (POST, PUT, PATCH, DELETE)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ServicioFilter
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'costobase', 'duracion', 'fecha_creacion']
    ordering = ['nombre']  # Ordenamiento por defecto

    def get_permissions(self):
        """
        Permisos diferenciados por acción:
        - Lectura (list, retrieve, detalle_completo): Acceso público
        - Escritura (create, update, partial_update, destroy): Requiere autenticación
        """
        if self.action in ['list', 'retrieve', 'detalle_completo']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Filtrar servicios por tenant y mostrar solo activos por defecto.
        Se puede incluir inactivos con el parámetro ?activo=false o sin filtro
        """
        if hasattr(self.request, 'tenant') and self.request.tenant:
            queryset = Servicio.objects.filter(empresa=self.request.tenant)
            
            # Por defecto solo mostrar servicios activos
            # Se puede override con parámetro explícito
            if 'activo' not in self.request.query_params:
                queryset = queryset.filter(activo=True)
            
            return queryset
        return Servicio.objects.none()

    def get_serializer_class(self):
        """Usar serializer diferente para list vs retrieve/create/update"""
        if self.action == 'list':
            return ServicioListSerializer
        return ServicioSerializer

    def perform_create(self, serializer):
        """Crear servicio asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear servicio")
    
    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        """
        Endpoint adicional para obtener detalle completo del servicio
        con información extendida incluyendo precio vigente.
        ACCESO PÚBLICO - No requiere autenticación.
        """
        servicio = self.get_object()
        serializer = ServicioSerializer(servicio)
        return Response(serializer.data)


class PiezadentalViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar catálogo de piezas dentales.
    Solo lectura (GET) - No permite crear/editar/eliminar desde este endpoint.
    """
    serializer_class = PiezadentalSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Filtrar piezas dentales por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Piezadental.objects.filter(empresa=self.request.tenant).order_by('nombrepieza')
        return Piezadental.objects.none()
