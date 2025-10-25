from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from api.models import Usuario, Tipodeusuario, Odontologo
from api.serializers import OdontologoSerializer
from .serializers import UsuarioSerializer, TipodeusuarioSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_check(request):
    """Health check para el módulo de usuarios - REQUIERE AUTENTICACIÓN"""
    return Response({
        'status': 'healthy',
        'module': 'users',
        'tenant': getattr(request, 'tenant', None),
        'user': request.user.username if request.user.is_authenticated else None,
        'message': 'Acceso autorizado a módulo de usuarios',
    })

class UsuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de usuarios - REQUIERE AUTENTICACIÓN"""
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar usuarios por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Usuario.objects.filter(empresa=self.request.tenant)
        return Usuario.objects.none()

    def perform_create(self, serializer):
        """Crear usuario asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear usuario")

class TipodeusuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de tipos de usuario - REQUIERE AUTENTICACIÓN"""
    serializer_class = TipodeusuarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar tipos de usuario por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Tipodeusuario.objects.filter(empresa=self.request.tenant)
        return Tipodeusuario.objects.none()

    def perform_create(self, serializer):
        """Crear tipo de usuario asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear tipo de usuario")


class OdontologoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar odontólogos.
    Solo lectura (GET) para uso en selects del frontend.
    Acceso permitido sin autenticación (solo lectura, filtrado por tenant).
    """
    serializer_class = OdontologoSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar odontólogos por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return Odontologo.objects.filter(empresa=self.request.tenant).select_related('codusuario')
        return Odontologo.objects.none()