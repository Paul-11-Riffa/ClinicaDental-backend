from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .models import TipoNotificacion, CanalNotificacion
from .serializers import TipoNotificacionSerializer, CanalNotificacionSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_check(request):
    """Health check para el módulo de notificaciones - REQUIERE AUTENTICACIÓN"""
    return Response({
        'status': 'healthy',
        'module': 'notifications',
        'tenant': getattr(request, 'tenant', None),
        'user': request.user.username if request.user.is_authenticated else None,
        'message': 'Acceso autorizado a módulo de notificaciones',
    })

class TipoNotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de tipos de notificación - REQUIERE AUTENTICACIÓN"""
    serializer_class = TipoNotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar tipos de notificación por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return TipoNotificacion.objects.filter(empresa=self.request.tenant)
        return TipoNotificacion.objects.none()

    def perform_create(self, serializer):
        """Crear tipo de notificación asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear tipo de notificación")

class CanalNotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de canales de notificación - REQUIERE AUTENTICACIÓN"""
    serializer_class = CanalNotificacionSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def get_queryset(self):
        """Filtrar canales de notificación por tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            return CanalNotificacion.objects.filter(empresa=self.request.tenant)
        return CanalNotificacion.objects.none()

    def perform_create(self, serializer):
        """Crear canal de notificación asociado al tenant"""
        if hasattr(self.request, 'tenant') and self.request.tenant:
            serializer.save(empresa=self.request.tenant)
        else:
            raise PermissionError("Tenant requerido para crear canal de notificación")
