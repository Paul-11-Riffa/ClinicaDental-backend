# chatbot/models.py
"""
Modelos para el Chatbot Odontológico con OpenAI
"""
from django.db import models
from django.utils import timezone
from api.models import Paciente, Consulta, Empresa, Usuario


class ConversacionChatbot(models.Model):
    """
    Representa una conversación del chatbot con un paciente.
    Cada conversación tiene un thread_id único de OpenAI.
    """
    ESTADO_CHOICES = [
        ('activa', 'Activa'),
        ('cerrada', 'Cerrada'),
        ('cita_agendada', 'Cita Agendada'),
        ('derivada_humano', 'Derivada a Humano'),
    ]
    
    # Relaciones
    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversaciones_chatbot',
        help_text="Paciente asociado (null si no está registrado aún)"
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='conversaciones_chatbot',
        help_text="Empresa/clínica a la que pertenece la conversación"
    )
    
    # OpenAI
    thread_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="ID del thread en OpenAI"
    )
    assistant_id = models.CharField(
        max_length=100,
        help_text="ID del asistente de OpenAI utilizado"
    )
    
    # Estado
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='activa'
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP del usuario que inició la conversación"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent del navegador"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora de cierre de la conversación"
    )
    
    class Meta:
        db_table = 'chatbot_conversacion'
        ordering = ['-created_at']
        verbose_name = 'Conversación del Chatbot'
        verbose_name_plural = 'Conversaciones del Chatbot'
        indexes = [
            models.Index(fields=['thread_id'], name='idx_chatbot_thread'),
            models.Index(fields=['paciente'], name='idx_chatbot_paciente'),
            models.Index(fields=['empresa'], name='idx_chatbot_empresa'),
            models.Index(fields=['estado'], name='idx_chatbot_estado'),
        ]
    
    def __str__(self):
        paciente_nombre = self.paciente.codusuario.nombre if self.paciente else "Anónimo"
        return f"Conversación #{self.id} - {paciente_nombre} ({self.estado})"
    
    def cerrar(self):
        """Cierra la conversación"""
        self.estado = 'cerrada'
        self.closed_at = timezone.now()
        self.save(update_fields=['estado', 'closed_at', 'updated_at'])
    
    def marcar_cita_agendada(self):
        """Marca que se agendó una cita exitosamente"""
        self.estado = 'cita_agendada'
        self.save(update_fields=['estado', 'updated_at'])
    
    def derivar_humano(self):
        """Marca que fue derivada a un humano"""
        self.estado = 'derivada_humano'
        self.save(update_fields=['estado', 'updated_at'])


class MensajeChatbot(models.Model):
    """
    Representa un mensaje individual dentro de una conversación.
    """
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
        ('system', 'Sistema'),
    ]
    
    conversacion = models.ForeignKey(
        ConversacionChatbot,
        on_delete=models.CASCADE,
        related_name='mensajes'
    )
    
    # OpenAI
    message_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="ID del mensaje en OpenAI"
    )
    
    # Contenido
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="Rol del autor del mensaje"
    )
    contenido = models.TextField(
        help_text="Contenido del mensaje"
    )
    
    # Metadata
    metadata = models.JSONField(
        null=True,
        blank=True,
        help_text="Metadata adicional (function calls, etc.)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chatbot_mensaje'
        ordering = ['created_at']
        verbose_name = 'Mensaje del Chatbot'
        verbose_name_plural = 'Mensajes del Chatbot'
        indexes = [
            models.Index(fields=['conversacion'], name='idx_mensaje_conv'),
            models.Index(fields=['role'], name='idx_mensaje_role'),
        ]
    
    def __str__(self):
        return f"{self.role}: {self.contenido[:50]}..."


class PreConsulta(models.Model):
    """
    Información preliminar recopilada por el chatbot antes de agendar cita.
    """
    URGENCIA_CHOICES = [
        ('alta', 'Alta - Requiere atención inmediata'),
        ('media', 'Media - Agendar pronto'),
        ('baja', 'Baja - Programar normal'),
    ]
    
    # Relaciones
    conversacion = models.OneToOneField(
        ConversacionChatbot,
        on_delete=models.CASCADE,
        related_name='pre_consulta'
    )
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pre_consulta',
        help_text="Consulta creada a partir de esta pre-consulta"
    )
    
    # Información del Paciente
    nombre = models.CharField(
        max_length=200,
        help_text="Nombre del paciente"
    )
    edad = models.IntegerField(
        null=True,
        blank=True,
        help_text="Edad del paciente"
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Teléfono de contacto"
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email de contacto"
    )
    
    # Información Clínica
    sintomas = models.TextField(
        help_text="Descripción de síntomas reportados"
    )
    dolor_nivel = models.IntegerField(
        null=True,
        blank=True,
        help_text="Nivel de dolor (1-10)"
    )
    cuando_comenzo = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Cuándo comenzaron los síntomas"
    )
    alergias = models.TextField(
        null=True,
        blank=True,
        help_text="Alergias reportadas"
    )
    condiciones_medicas = models.TextField(
        null=True,
        blank=True,
        help_text="Condiciones médicas previas"
    )
    
    # Clasificación
    urgencia = models.CharField(
        max_length=10,
        choices=URGENCIA_CHOICES,
        default='media',
        help_text="Nivel de urgencia determinado por el chatbot"
    )
    posible_diagnostico = models.TextField(
        null=True,
        blank=True,
        help_text="Posible condición identificada por el chatbot (orientativo)"
    )
    
    # Preferencias de Agendamiento
    fecha_preferida = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha preferida por el paciente"
    )
    horario_preferido = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('mañana', 'Mañana (8am-12pm)'),
            ('tarde', 'Tarde (2pm-6pm)'),
            ('noche', 'Noche (6pm-8pm)'),
            ('cualquiera', 'Cualquier horario'),
        ],
        default='cualquiera'
    )
    
    # Estado
    procesada = models.BooleanField(
        default=False,
        help_text="¿Ya fue revisada por recepcionista?"
    )
    notas_recepcionista = models.TextField(
        null=True,
        blank=True,
        help_text="Notas de la recepcionista al procesar"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'chatbot_pre_consulta'
        ordering = ['-created_at']
        verbose_name = 'Pre-Consulta'
        verbose_name_plural = 'Pre-Consultas'
        indexes = [
            models.Index(fields=['urgencia'], name='idx_preconsulta_urgencia'),
            models.Index(fields=['procesada'], name='idx_preconsulta_procesada'),
        ]
    
    def __str__(self):
        return f"Pre-consulta: {self.nombre} - {self.urgencia} ({self.created_at.date()})"
    
    def marcar_procesada(self, notas=None):
        """Marca la pre-consulta como procesada"""
        self.procesada = True
        if notas:
            self.notas_recepcionista = notas
        self.save(update_fields=['procesada', 'notas_recepcionista', 'updated_at'])
