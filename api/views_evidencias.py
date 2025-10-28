"""
Vistas para gestión de evidencias (upload de archivos).

SP3-T008 - FASE 5: Backend Upload de Evidencias

Endpoints:
- POST /api/upload/evidencias/ - Subir archivo
- DELETE /api/upload/evidencias/<id>/ - Eliminar evidencia
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from .models import Evidencia, Bitacora
from .serializers_evidencias import (
    EvidenciaSerializer,
    EvidenciaUploadSerializer,
    EvidenciaResponseSerializer
)
import os


def obtener_ip_cliente(request):
    """
    Obtiene la IP real del cliente, considerando proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def validar_archivo_avanzado(file: UploadedFile) -> tuple[bool, str]:
    """
    Validación avanzada del archivo con python-magic.
    Valida el MIME type real del archivo (no solo la extensión).
    
    Returns:
        (es_valido, mensaje_error)
    """
    try:
        import magic
        
        # Validar MIME type real del archivo
        file.seek(0)
        mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)  # Resetear puntero
        
        if mime not in settings.ALLOWED_UPLOAD_MIMETYPES:
            return False, (
                f"Tipo de archivo no permitido: {mime}. "
                f"Permitidos: {', '.join(settings.ALLOWED_UPLOAD_MIMETYPES)}"
            )
        
        return True, ""
    
    except ImportError:
        # Si python-magic no está instalado, solo validar extensión
        # (ya validado en el serializer)
        return True, ""
    
    except Exception as e:
        # Si falla la validación, rechazar por seguridad
        return False, f"Error al validar archivo: {str(e)}"


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_evidencia(request):
    """
    Endpoint para subir evidencias de sesiones.
    
    POST /api/upload/evidencias/
    
    Body (multipart/form-data):
        - file: archivo a subir (requerido)
        - tipo: tipo de evidencia (opcional, default: 'evidencia_sesion')
    
    Response Success (201):
        {
            "url": "http://...",
            "filename": "imagen.jpg",
            "size": 1048576,
            "type": "image/jpeg",
            "id": 1
        }
    
    Response Error (400):
        {
            "error": "Mensaje de error",
            "detail": "Detalles adicionales"
        }
    """
    # Validar que existe tenant
    if not hasattr(request, 'tenant') or not request.tenant:
        return Response(
            {'error': 'No se pudo identificar la empresa (tenant)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que existe usuario asociado
    try:
        usuario = request.user.usuario
    except AttributeError:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar datos con serializer
    upload_serializer = EvidenciaUploadSerializer(data=request.data)
    if not upload_serializer.is_valid():
        return Response(
            upload_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file = upload_serializer.validated_data['file']
    tipo = upload_serializer.validated_data.get('tipo', 'evidencia_sesion')
    
    # Validación avanzada con python-magic
    es_valido, mensaje_error = validar_archivo_avanzado(file)
    if not es_valido:
        return Response(
            {'error': mensaje_error},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Crear registro de evidencia
        evidencia = Evidencia.objects.create(
            archivo=file,
            nombre_original=file.name,
            tipo=tipo,
            mimetype=file.content_type,
            tamanio=file.size,
            usuario=usuario,
            empresa=request.tenant,
            ip_subida=obtener_ip_cliente(request)
        )
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="SUBIR_EVIDENCIA",
            tabla_afectada="evidencias",
            registro_id=evidencia.id,
            valores_nuevos={'mensaje': f"Archivo: {file.name} ({file.size} bytes, {file.content_type})"},
            ip_address=obtener_ip_cliente(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Serializar evidencia completa
        evidencia_serializer = EvidenciaSerializer(
            evidencia,
            context={'request': request}
        )
        
        # Formato de respuesta esperado por el frontend
        response_data = {
            'url': evidencia_serializer.data['url'],
            'filename': evidencia.nombre_original,
            'size': evidencia.tamanio,
            'type': evidencia.mimetype,
            'id': evidencia.id,
        }
        
        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )
        
    except Exception as e:
        return Response(
            {
                'error': 'Error al guardar archivo',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_evidencia(request, evidencia_id):
    """
    Endpoint para eliminar evidencia.
    
    DELETE /api/upload/evidencias/<id>/
    
    Restricciones:
    - Solo el usuario que subió la evidencia puede eliminarla
    - O usuarios administradores
    - Debe pertenecer a la misma empresa (tenant)
    
    Response Success (204): No Content
    Response Error (403): Forbidden
    Response Error (404): Not Found
    """
    # Validar que existe tenant
    if not hasattr(request, 'tenant') or not request.tenant:
        return Response(
            {'error': 'No se pudo identificar la empresa (tenant)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validar que existe usuario asociado
    try:
        usuario = request.user.usuario
    except AttributeError:
        return Response(
            {'error': 'Usuario no encontrado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Buscar evidencia con tenant filtering
        evidencia = Evidencia.objects.get(
            id=evidencia_id,
            empresa=request.tenant
        )
        
        # Verificar permisos (solo el que subió o admin)
        es_admin = usuario.idtipousuario.rol in ['Administrador', 'SuperAdmin']
        es_propietario = evidencia.usuario == usuario
        
        if not (es_propietario or es_admin):
            return Response(
                {'error': 'No tienes permiso para eliminar esta evidencia'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Guardar info para bitácora antes de eliminar
        nombre_archivo = evidencia.nombre_original
        
        # Eliminar evidencia (esto también elimina el archivo físico)
        evidencia.delete()
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="ELIMINAR_EVIDENCIA",
            tabla_afectada="evidencias",
            registro_id=evidencia_id,
            valores_anteriores={'mensaje': f"Archivo eliminado: {nombre_archivo} (ID: {evidencia_id})"},
            ip_address=obtener_ip_cliente(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
        
    except Evidencia.DoesNotExist:
        return Response(
            {'error': 'Evidencia no encontrada'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {
                'error': 'Error al eliminar evidencia',
                'detail': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_evidencias(request):
    """
    Endpoint para listar evidencias de la empresa.
    
    GET /api/upload/evidencias/
    
    Query Parameters:
        - tipo: Filtrar por tipo (evidencia_sesion, radiografia, foto_clinica, documento)
        - fecha_desde: Filtrar desde fecha (YYYY-MM-DD)
        - fecha_hasta: Filtrar hasta fecha (YYYY-MM-DD)
    """
    # Validar que existe tenant
    if not hasattr(request, 'tenant') or not request.tenant:
        return Response(
            {'error': 'No se pudo identificar la empresa (tenant)'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Queryset base con tenant filtering
    queryset = Evidencia.objects.filter(empresa=request.tenant)
    
    # Filtros opcionales
    tipo = request.query_params.get('tipo')
    if tipo:
        queryset = queryset.filter(tipo=tipo)
    
    fecha_desde = request.query_params.get('fecha_desde')
    if fecha_desde:
        queryset = queryset.filter(fecha_subida__date__gte=fecha_desde)
    
    fecha_hasta = request.query_params.get('fecha_hasta')
    if fecha_hasta:
        queryset = queryset.filter(fecha_subida__date__lte=fecha_hasta)
    
    # Serializar
    serializer = EvidenciaSerializer(
        queryset,
        many=True,
        context={'request': request}
    )
    
    return Response(serializer.data, status=status.HTTP_200_OK)
