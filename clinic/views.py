from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .models import Paciente, Consulta, Odontologo, Servicio
from .serializers import PacienteSerializer, ConsultaSerializer, OdontologoSerializer, ServicioSerializer

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
    """ViewSet para gestión de servicios - REQUIERE AUTENTICACIÓN"""
    serializer_class = ServicioSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar servicios por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Servicio.objects.filter(empresa=self.request.tenant)
        return Servicio.objects.none()

    def perform_create(self, serializer):
        """Crear servicio asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear servicio")
