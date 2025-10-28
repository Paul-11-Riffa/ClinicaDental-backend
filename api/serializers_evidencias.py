"""
Serializers para gestión de evidencias (upload de archivos).

SP3-T008 - FASE 5: Backend Upload de Evidencias
"""
from rest_framework import serializers
from .models import Evidencia


class EvidenciaSerializer(serializers.ModelSerializer):
    """
    Serializer para listar/mostrar evidencias subidas.
    """
    url = serializers.SerializerMethodField()
    tamanio_legible = serializers.SerializerMethodField()
    usuario_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = Evidencia
        fields = [
            'id',
            'url',
            'nombre_original',
            'tipo',
            'mimetype',
            'tamanio',
            'tamanio_legible',
            'usuario',
            'usuario_nombre',
            'fecha_subida',
            'ip_subida',
        ]
        read_only_fields = [
            'id',
            'fecha_subida',
            'usuario',
            'empresa',
            'ip_subida',
        ]
    
    def get_url(self, obj):
        """Retorna URL absoluta del archivo"""
        if obj.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo.url)
            return obj.archivo.url
        return None
    
    def get_tamanio_legible(self, obj):
        """Retorna tamaño en formato legible"""
        return obj.get_tamanio_legible()
    
    def get_usuario_nombre(self, obj):
        """Retorna nombre completo del usuario que subió"""
        if obj.usuario:
            return f"{obj.usuario.nombre} {obj.usuario.apellido}"
        return None


class EvidenciaUploadSerializer(serializers.Serializer):
    """
    Serializer para validar datos de upload.
    No usa ModelSerializer porque el archivo se maneja en la vista.
    """
    file = serializers.FileField(
        required=True,
        help_text="Archivo a subir (imagen o PDF)"
    )
    tipo = serializers.ChoiceField(
        choices=Evidencia.TIPO_CHOICES,
        default='evidencia_sesion',
        required=False,
        help_text="Tipo de evidencia"
    )
    
    def validate_file(self, value):
        """Validación básica del archivo en el serializer"""
        from django.conf import settings
        import os
        
        # Validar que se envió un archivo
        if not value:
            raise serializers.ValidationError("No se proporcionó ningún archivo")
        
        # Validar extensión
        ext = os.path.splitext(value.name)[1].lower().replace('.', '')
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            raise serializers.ValidationError(
                f"Extensión .{ext} no permitida. "
                f"Permitidas: {', '.join(settings.ALLOWED_UPLOAD_EXTENSIONS)}"
            )
        
        # Validar tamaño
        if value.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            max_mb = settings.FILE_UPLOAD_MAX_MEMORY_SIZE / (1024 * 1024)
            raise serializers.ValidationError(
                f"Archivo demasiado grande ({value.size / (1024*1024):.2f}MB). "
                f"Máximo: {max_mb}MB"
            )
        
        return value


class EvidenciaResponseSerializer(serializers.Serializer):
    """
    Serializer para la respuesta del endpoint de upload.
    Formato específico esperado por el frontend.
    """
    url = serializers.URLField(
        help_text="URL pública del archivo subido"
    )
    filename = serializers.CharField(
        help_text="Nombre original del archivo"
    )
    size = serializers.IntegerField(
        help_text="Tamaño en bytes"
    )
    type = serializers.CharField(
        help_text="MIME type del archivo"
    )
    id = serializers.IntegerField(
        help_text="ID de la evidencia en la base de datos"
    )
