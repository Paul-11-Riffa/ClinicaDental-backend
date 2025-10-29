"""
Vistas del API para el chatbot dental.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404

from .models import ConversacionChatbot, MensajeChatbot, PreConsulta
from .serializers import (
    ConversacionChatbotSerializer,
    MensajeChatbotSerializer,
    PreConsultaSerializer,
    IniciarConversacionSerializer,
    EnviarMensajeSerializer,
    ProcesarPreConsultaSerializer,
    EstadisticasChatbotSerializer
)
from .services import OpenAIService, evaluar_urgencia
from api.models import Paciente, Odontologo, Consulta


class ChatbotViewSet(viewsets.ViewSet):
    """
    ViewSet para interactuar con el chatbot.
    
    Endpoints:
    - POST /api/chatbot/iniciar/ - Inicia una nueva conversación
    - POST /api/chatbot/mensaje/ - Envía un mensaje
    - GET /api/chatbot/conversacion/{id}/ - Obtiene una conversación
    - GET /api/chatbot/historial/ - Lista conversaciones del usuario
    """
    
    permission_classes = []  # Permitir acceso público (anónimo)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai_service = None
    
    def get_openai_service(self):
        """Lazy loading del servicio OpenAI."""
        if self.openai_service is None:
            self.openai_service = OpenAIService()
        return self.openai_service
    
    @action(detail=False, methods=['post'])
    def iniciar(self, request):
        """
        Inicia una nueva conversación con el chatbot.
        
        Body:
            {
                "paciente_id": 123  // Opcional
            }
        
        Returns:
            {
                "conversacion_id": 456,
                "thread_id": "thread_abc123",
                "mensaje_bienvenida": "¡Hola! ..."
            }
        """
        serializer = IniciarConversacionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Obtener empresa del request (tenant)
        empresa = getattr(request, 'tenant', None)
        if not empresa:
            return Response(
                {"error": "No se pudo determinar la empresa/clínica"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener paciente si se proporcionó
        paciente = None
        paciente_id = serializer.validated_data.get('paciente_id')
        if paciente_id:
            try:
                paciente = Paciente.objects.get(
                    idusuario=paciente_id,
                    empresa=empresa
                )
            except Paciente.DoesNotExist:
                return Response(
                    {"error": "Paciente no encontrado"},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Crear conversación
        try:
            service = self.get_openai_service()
            conversacion = service.crear_conversacion(empresa, paciente)
            
            # Obtener mensaje de bienvenida
            mensaje_bienvenida = conversacion.mensajechatbot_set.first()
            
            return Response({
                "conversacion_id": conversacion.id,
                "thread_id": conversacion.thread_id,
                "mensaje_bienvenida": mensaje_bienvenida.contenido if mensaje_bienvenida else "",
                "estado": conversacion.estado
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {"error": f"Error al crear conversación: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def mensaje(self, request):
        """
        Envía un mensaje en una conversación existente.
        
        Body:
            {
                "conversacion_id": 456,
                "mensaje": "Tengo dolor de muelas"
            }
        
        Returns:
            {
                "respuesta": "Lamento escuchar eso...",
                "function_call": {...}  // Si el asistente llamó a una función
            }
        """
        serializer = EnviarMensajeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversacion_id = serializer.validated_data['conversacion_id']
        mensaje_texto = serializer.validated_data['mensaje']
        
        # Obtener conversación
        empresa = getattr(request, 'tenant', None)
        try:
            conversacion = ConversacionChatbot.objects.get(
                id=conversacion_id,
                empresa=empresa
            )
        except ConversacionChatbot.DoesNotExist:
            return Response(
                {"error": "Conversación no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verificar que la conversación esté activa
        if conversacion.estado == 'cerrada':
            return Response(
                {"error": "Esta conversación está cerrada"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Enviar mensaje al asistente
        try:
            service = self.get_openai_service()
            respuesta, function_data = service.enviar_mensaje(
                conversacion,
                mensaje_texto
            )
            
            return Response({
                "respuesta": respuesta,
                "function_call": function_data,
                "estado_conversacion": conversacion.estado
            })
        
        except Exception as e:
            return Response(
                {"error": f"Error al procesar mensaje: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def conversacion(self, request, pk=None):
        """
        Obtiene el historial completo de una conversación.
        
        Returns:
            {
                "id": 456,
                "estado": "activa",
                "mensajes": [...]
            }
        """
        empresa = getattr(request, 'tenant', None)
        
        conversacion = get_object_or_404(
            ConversacionChatbot,
            id=pk,
            empresa=empresa
        )
        
        serializer = ConversacionChatbotSerializer(conversacion)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def historial(self, request):
        """
        Lista todas las conversaciones del paciente actual.
        
        Query params:
            - paciente_id: Filtrar por paciente
            - estado: Filtrar por estado (activa, cerrada, etc.)
        """
        empresa = getattr(request, 'tenant', None)
        
        queryset = ConversacionChatbot.objects.filter(empresa=empresa)
        
        # Filtros opcionales
        paciente_id = request.query_params.get('paciente_id')
        if paciente_id:
            queryset = queryset.filter(paciente_id=paciente_id)
        
        estado = request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        queryset = queryset.order_by('-created_at')
        
        serializer = ConversacionChatbotSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Cierra una conversación.
        """
        empresa = getattr(request, 'tenant', None)
        
        conversacion = get_object_or_404(
            ConversacionChatbot,
            id=pk,
            empresa=empresa
        )
        
        conversacion.cerrar()
        
        return Response({
            "mensaje": "Conversación cerrada",
            "estado": conversacion.estado
        })


class PreConsultaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar pre-consultas creadas por el chatbot.
    
    Endpoints:
    - GET /api/chatbot/pre-consultas/ - Lista pre-consultas pendientes
    - GET /api/chatbot/pre-consultas/{id}/ - Detalle de una pre-consulta
    - PATCH /api/chatbot/pre-consultas/{id}/ - Actualizar notas
    - POST /api/chatbot/pre-consultas/procesar/ - Convertir a cita real
    - GET /api/chatbot/pre-consultas/estadisticas/ - Estadísticas
    """
    
    serializer_class = PreConsultaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar por empresa del tenant."""
        empresa = getattr(self.request, 'tenant', None)
        if not empresa:
            return PreConsulta.objects.none()
        
        queryset = PreConsulta.objects.filter(
            conversacion__empresa=empresa
        ).select_related(
            'conversacion',
            'conversacion__paciente',
            'conversacion__empresa',
            'consulta'
        ).order_by('-created_at')
        
        # Filtros
        procesada = self.request.query_params.get('procesada')
        if procesada is not None:
            procesada_bool = procesada.lower() in ['true', '1', 'si', 'yes']
            queryset = queryset.filter(procesada=procesada_bool)
        
        urgencia = self.request.query_params.get('urgencia')
        if urgencia:
            queryset = queryset.filter(urgencia=urgencia)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def procesar(self, request):
        """
        Procesa una pre-consulta y crea la cita real en el sistema.
        
        Body:
            {
                "pre_consulta_id": 123,
                "odontologo_id": 456,
                "fecha": "2024-03-15",
                "hora": "10:30",
                "notas": "Paciente urgente"
            }
        """
        serializer = ProcesarPreConsultaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        empresa = getattr(request, 'tenant', None)
        
        # Obtener pre-consulta
        pre_consulta_id = serializer.validated_data['pre_consulta_id']
        try:
            pre_consulta = PreConsulta.objects.get(
                id=pre_consulta_id,
                conversacion__empresa=empresa
            )
        except PreConsulta.DoesNotExist:
            return Response(
                {"error": "Pre-consulta no encontrada"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if pre_consulta.procesada:
            return Response(
                {"error": "Esta pre-consulta ya fue procesada"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Obtener odontólogo
        odontologo_id = serializer.validated_data['odontologo_id']
        try:
            odontologo = Odontologo.objects.get(
                idusuario=odontologo_id,
                empresa=empresa
            )
        except Odontologo.DoesNotExist:
            return Response(
                {"error": "Odontólogo no encontrado"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener o crear paciente
        paciente = pre_consulta.conversacion.paciente
        if not paciente:
            # Crear paciente a partir de los datos de la pre-consulta
            from api.models import Usuario
            
            # Crear Usuario base
            usuario = Usuario.objects.create(
                nombre=pre_consulta.nombre,
                email=pre_consulta.email,
                telefono=pre_consulta.telefono,
                empresa=empresa,
                rol='paciente'
            )
            
            # Crear Paciente
            paciente = Paciente.objects.create(
                idusuario=usuario.idusuario,
                nombre=pre_consulta.nombre,
                email=pre_consulta.email,
                telefono=pre_consulta.telefono,
                edad=pre_consulta.edad,
                empresa=empresa
            )
        
        # Crear la consulta
        from api.models import EstadoConsulta
        
        try:
            estado_agendada = EstadoConsulta.objects.get(
                nombre='Agendada',
                empresa=empresa
            )
        except EstadoConsulta.DoesNotExist:
            # Crear estado si no existe
            estado_agendada = EstadoConsulta.objects.create(
                nombre='Agendada',
                descripcion='Cita agendada',
                empresa=empresa
            )
        
        consulta = Consulta.objects.create(
            paciente=paciente,
            odontologo=odontologo,
            fecha=serializer.validated_data['fecha'],
            hora=serializer.validated_data['hora'],
            motivo=pre_consulta.sintomas,
            idestadoconsulta=estado_agendada,
            empresa=empresa
        )
        
        # Actualizar pre-consulta
        pre_consulta.consulta = consulta
        pre_consulta.procesada = True
        pre_consulta.notas_recepcion = serializer.validated_data.get('notas', '')
        pre_consulta.save()
        
        return Response({
            "mensaje": "Pre-consulta procesada exitosamente",
            "consulta_id": consulta.idconsulta,
            "paciente_id": paciente.idusuario
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Retorna estadísticas del chatbot.
        """
        empresa = getattr(request, 'tenant', None)
        if not empresa:
            return Response(
                {"error": "No se pudo determinar la empresa"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Conversaciones
        conversaciones = ConversacionChatbot.objects.filter(empresa=empresa)
        total_conversaciones = conversaciones.count()
        conversaciones_activas = conversaciones.filter(estado='activa').count()
        conversaciones_cerradas = conversaciones.filter(estado='cerrada').count()
        citas_agendadas = conversaciones.filter(estado='cita_agendada').count()
        
        # Pre-consultas
        pre_consultas = PreConsulta.objects.filter(conversacion__empresa=empresa)
        pre_consultas_pendientes = pre_consultas.filter(procesada=False).count()
        pre_consultas_procesadas = pre_consultas.filter(procesada=True).count()
        
        # Urgencias
        urgencia_alta = pre_consultas.filter(urgencia='alta').count()
        urgencia_media = pre_consultas.filter(urgencia='media').count()
        urgencia_baja = pre_consultas.filter(urgencia='baja').count()
        
        # Promedio de mensajes
        mensajes_stats = MensajeChatbot.objects.filter(
            conversacion__empresa=empresa
        ).values('conversacion').annotate(
            total=Count('id')
        ).aggregate(
            promedio=Avg('total')
        )
        
        promedio_mensajes = mensajes_stats['promedio'] or 0
        
        data = {
            'total_conversaciones': total_conversaciones,
            'conversaciones_activas': conversaciones_activas,
            'conversaciones_cerradas': conversaciones_cerradas,
            'citas_agendadas': citas_agendadas,
            'pre_consultas_pendientes': pre_consultas_pendientes,
            'pre_consultas_procesadas': pre_consultas_procesadas,
            'urgencia_alta': urgencia_alta,
            'urgencia_media': urgencia_media,
            'urgencia_baja': urgencia_baja,
            'promedio_mensajes_por_conversacion': round(promedio_mensajes, 2)
        }
        
        serializer = EstadisticasChatbotSerializer(data)
        return Response(serializer.data)
