from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.http import JsonResponse
from .models import Empresa


class EmpresaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de empresas (tenants)."""
    queryset = Empresa.objects.all()
    # serializer_class = EmpresaSerializer  # Crear después
    
    def list(self, request):
        """Listar todas las empresas."""
        return Response({
            "message": "Lista de empresas registradas",
            "count": self.queryset.count(),
            "results": []
        })
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registrar nueva empresa/tenant."""
        return Response({
            "message": "Endpoint para registrar nueva clínica dental",
            "status": "coming_soon"
        })


def health_check(request):
    """Health check para la app tenancy."""
    
    # Obtener información del tenant del middleware
    tenant = getattr(request, 'tenant', None)
    
    # Información del dominio
    domain = request.get_host()
    subdomain_header = request.headers.get('X-Tenant-Subdomain')
    
    response_data = {
        "app": "tenancy",
        "status": "healthy",
        "message": "Gestión de tenants funcionando correctamente",
        "domain": domain,
        "subdomain_header": subdomain_header,
    }
    
    if tenant:
        response_data["tenant"] = {
            "id": tenant.id,
            "nombre": tenant.nombre,
            "subdomain": tenant.subdomain,
            "activo": tenant.activo,
            "fecha_creacion": tenant.fecha_creacion.isoformat(),
        }
        response_data["message"] = f"Conectado a: {tenant.nombre}"
    else:
        response_data["tenant"] = None
        response_data["message"] = "Dominio público (sin tenant específico)"
    
    return JsonResponse(response_data)
