"""
Serializers para el chatbot dental.
"""
from rest_framework import serializers
from .models import ConversacionChatbot, MensajeChatbot, PreConsulta


class MensajeChatbotSerializer(serializers.ModelSerializer):
    """Serializer para mensajes individuales del chat."""
    
    class Meta:
        model = MensajeChatbot
        fields = [
            'id',
            'role',
            'contenido',
            'metadata',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ConversacionChatbotSerializer(serializers.ModelSerializer):
    """Serializer para conversaciones del chatbot."""
    
    mensajes = MensajeChatbotSerializer(
        source='mensajechatbot_set',
        many=True,
        read_only=True
    )
    paciente_nombre = serializers.CharField(
        source='paciente.nombre',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ConversacionChatbot
        fields = [
            'id',
            'paciente',
            'paciente_nombre',
            'empresa',
            'thread_id',
            'assistant_id',
            'estado',
            'created_at',
            'updated_at',
            'closed_at',
            'mensajes'
        ]
        read_only_fields = [
            'id',
            'thread_id',
            'assistant_id',
            'created_at',
            'updated_at',
            'closed_at'
        ]


class IniciarConversacionSerializer(serializers.Serializer):
    """Serializer para iniciar una nueva conversación."""
    
    paciente_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID del paciente (opcional para conversaciones anónimas)"
    )


class EnviarMensajeSerializer(serializers.Serializer):
    """Serializer para enviar un mensaje en una conversación."""
    
    conversacion_id = serializers.IntegerField(
        help_text="ID de la conversación activa"
    )
    mensaje = serializers.CharField(
        help_text="Contenido del mensaje del usuario"
    )
    
    def validate_mensaje(self, value):
        """Validar que el mensaje no esté vacío."""
        if not value or not value.strip():
            raise serializers.ValidationError("El mensaje no puede estar vacío")
        
        if len(value) > 1000:
            raise serializers.ValidationError(
                "El mensaje es demasiado largo (máximo 1000 caracteres)"
            )
        
        return value.strip()


class PreConsultaSerializer(serializers.ModelSerializer):
    """Serializer para pre-consultas creadas por el chatbot."""
    
    conversacion_id = serializers.IntegerField(
        source='conversacion.id',
        read_only=True
    )
    paciente_nombre = serializers.CharField(
        source='conversacion.paciente.nombre',
        read_only=True,
        allow_null=True
    )
    empresa_nombre = serializers.CharField(
        source='conversacion.empresa.nombre',
        read_only=True
    )
    consulta_id = serializers.IntegerField(
        source='consulta.idconsulta',
        read_only=True,
        allow_null=True
    )
    
    # Campos calculados
    dias_desde_solicitud = serializers.SerializerMethodField()
    
    class Meta:
        model = PreConsulta
        fields = [
            'id',
            'conversacion_id',
            'consulta_id',
            'paciente_nombre',
            'empresa_nombre',
            'nombre',
            'edad',
            'telefono',
            'email',
            'sintomas',
            'dolor_nivel',
            'alergias',
            'condiciones_medicas',
            'urgencia',
            'fecha_preferida',
            'horario_preferido',
            'procesada',
            'notas_recepcion',
            'created_at',
            'dias_desde_solicitud'
        ]
        read_only_fields = [
            'id',
            'conversacion_id',
            'consulta_id',
            'created_at'
        ]
    
    def get_dias_desde_solicitud(self, obj):
        """Calcula cuántos días han pasado desde la solicitud."""
        from django.utils import timezone
        delta = timezone.now() - obj.created_at
        return delta.days


class ProcesarPreConsultaSerializer(serializers.Serializer):
    """Serializer para procesar una pre-consulta y crear la cita real."""
    
    pre_consulta_id = serializers.IntegerField(
        help_text="ID de la pre-consulta a procesar"
    )
    odontologo_id = serializers.IntegerField(
        help_text="ID del odontólogo asignado"
    )
    fecha = serializers.DateField(
        help_text="Fecha de la cita (YYYY-MM-DD)"
    )
    hora = serializers.TimeField(
        help_text="Hora de la cita (HH:MM)"
    )
    notas = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notas adicionales de la recepcionista"
    )
    
    def validate(self, data):
        """Validaciones adicionales."""
        from datetime import datetime, date
        from django.utils import timezone
        
        # Validar que la fecha no sea en el pasado
        if data['fecha'] < date.today():
            raise serializers.ValidationError({
                'fecha': 'La fecha no puede ser en el pasado'
            })
        
        # Validar que la hora esté en horario laboral (8:00 - 18:00)
        hora = data['hora']
        if hora.hour < 8 or hora.hour >= 18:
            raise serializers.ValidationError({
                'hora': 'La hora debe estar entre 08:00 y 18:00'
            })
        
        return data


class EstadisticasChatbotSerializer(serializers.Serializer):
    """Serializer para estadísticas del chatbot."""
    
    total_conversaciones = serializers.IntegerField()
    conversaciones_activas = serializers.IntegerField()
    conversaciones_cerradas = serializers.IntegerField()
    citas_agendadas = serializers.IntegerField()
    pre_consultas_pendientes = serializers.IntegerField()
    pre_consultas_procesadas = serializers.IntegerField()
    urgencia_alta = serializers.IntegerField()
    urgencia_media = serializers.IntegerField()
    urgencia_baja = serializers.IntegerField()
    promedio_mensajes_por_conversacion = serializers.FloatField()
