"""
Servicio de integración con OpenAI Assistant API para el chatbot dental.
"""
import json
import time
from typing import Dict, Optional, List, Tuple
from openai import OpenAI
from django.conf import settings
from django.utils import timezone

from .models import ConversacionChatbot, MensajeChatbot, PreConsulta
from api.models import Empresa, Paciente, Consulta, Odontologo


class OpenAIService:
    """
    Servicio para interactuar con OpenAI Assistant API.
    Maneja la creación de asistentes, threads y mensajes.
    """
    
    def __init__(self):
        """Inicializa el cliente de OpenAI."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY no está configurada en settings")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.assistant_id = settings.OPENAI_ASSISTANT_ID
    
    def crear_o_obtener_asistente(self) -> str:
        """
        Crea un nuevo asistente o retorna el ID del asistente existente.
        
        Returns:
            str: ID del asistente
        """
        # Si ya existe un assistant_id en settings, usarlo
        if self.assistant_id:
            try:
                # Verificar que el asistente existe
                assistant = self.client.beta.assistants.retrieve(self.assistant_id)
                return assistant.id
            except Exception as e:
                print(f"Asistente con ID {self.assistant_id} no encontrado: {e}")
        
        # Crear nuevo asistente
        assistant = self.client.beta.assistants.create(
            name=settings.OPENAI_ASSISTANT_NAME,
            instructions=settings.OPENAI_ASSISTANT_INSTRUCTIONS,
            model=self.model,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "buscar_disponibilidad",
                        "description": "Busca horarios disponibles para agendar citas dentales en una fecha específica",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "fecha": {
                                    "type": "string",
                                    "description": "Fecha en formato YYYY-MM-DD"
                                },
                                "odontologo_id": {
                                    "type": "integer",
                                    "description": "ID del odontólogo (opcional)"
                                }
                            },
                            "required": ["fecha"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "agendar_cita",
                        "description": "Agenda una cita dental con los datos del paciente",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string", "description": "Nombre completo del paciente"},
                                "telefono": {"type": "string", "description": "Teléfono de contacto"},
                                "email": {"type": "string", "description": "Email del paciente"},
                                "fecha": {"type": "string", "description": "Fecha en formato YYYY-MM-DD"},
                                "hora": {"type": "string", "description": "Hora en formato HH:MM"},
                                "motivo": {"type": "string", "description": "Motivo de la consulta"},
                                "odontologo_id": {"type": "integer", "description": "ID del odontólogo"}
                            },
                            "required": ["nombre", "telefono", "fecha", "hora", "motivo"]
                        }
                    }
                }
            ]
        )
        
        print(f"✅ Asistente creado con ID: {assistant.id}")
        print(f"⚠️ IMPORTANTE: Agrega este ID a tu archivo .env:")
        print(f"OPENAI_ASSISTANT_ID={assistant.id}")
        
        return assistant.id
    
    def crear_conversacion(self, empresa: Empresa, paciente: Optional[Paciente] = None) -> ConversacionChatbot:
        """
        Crea una nueva conversación (thread) con OpenAI.
        
        Args:
            empresa: Empresa/clínica a la que pertenece la conversación
            paciente: Paciente (opcional, puede ser anónimo)
        
        Returns:
            ConversacionChatbot: Objeto de conversación creado
        """
        # Crear thread en OpenAI
        thread = self.client.beta.threads.create()
        
        # Obtener o crear asistente
        assistant_id = self.crear_o_obtener_asistente()
        
        # Crear registro en BD
        conversacion = ConversacionChatbot.objects.create(
            paciente=paciente,
            empresa=empresa,
            thread_id=thread.id,
            assistant_id=assistant_id,
            estado='activa'
        )
        
        # Mensaje de bienvenida del sistema
        MensajeChatbot.objects.create(
            conversacion=conversacion,
            role='assistant',
            contenido=f"¡Hola! Soy el asistente virtual de {empresa.nombre}. "
                     "¿En qué puedo ayudarte hoy? Puedo ayudarte a entender tus síntomas "
                     "dentales y agendar una cita si lo necesitas."
        )
        
        return conversacion
    
    def enviar_mensaje(
        self, 
        conversacion: ConversacionChatbot, 
        mensaje_usuario: str
    ) -> Tuple[str, Optional[Dict]]:
        """
        Envía un mensaje al asistente y procesa la respuesta.
        
        Args:
            conversacion: Conversación activa
            mensaje_usuario: Mensaje del usuario
        
        Returns:
            Tuple[str, Optional[Dict]]: (respuesta_asistente, function_call_data)
        """
        # Guardar mensaje del usuario
        MensajeChatbot.objects.create(
            conversacion=conversacion,
            role='user',
            contenido=mensaje_usuario
        )
        
        # Enviar mensaje a OpenAI
        self.client.beta.threads.messages.create(
            thread_id=conversacion.thread_id,
            role="user",
            content=mensaje_usuario
        )
        
        # Ejecutar el asistente
        run = self.client.beta.threads.runs.create(
            thread_id=conversacion.thread_id,
            assistant_id=conversacion.assistant_id
        )
        
        # Esperar a que termine la ejecución
        respuesta_texto, function_call_data = self._esperar_respuesta(
            conversacion.thread_id, 
            run.id,
            conversacion
        )
        
        # Guardar respuesta del asistente
        if respuesta_texto:
            MensajeChatbot.objects.create(
                conversacion=conversacion,
                role='assistant',
                contenido=respuesta_texto,
                metadata=function_call_data if function_call_data else None
            )
        
        return respuesta_texto, function_call_data
    
    def _esperar_respuesta(
        self, 
        thread_id: str, 
        run_id: str,
        conversacion: ConversacionChatbot,
        timeout: int = 30
    ) -> Tuple[str, Optional[Dict]]:
        """
        Espera a que el asistente complete la ejecución y retorna la respuesta.
        
        Args:
            thread_id: ID del thread
            run_id: ID de la ejecución
            conversacion: Conversación activa
            timeout: Tiempo máximo de espera en segundos
        
        Returns:
            Tuple[str, Optional[Dict]]: (respuesta, function_call_data)
        """
        start_time = time.time()
        function_call_data = None
        
        while time.time() - start_time < timeout:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status == 'completed':
                # Obtener mensajes
                messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                # El primer mensaje es el más reciente (respuesta del asistente)
                latest_message = messages.data[0]
                
                if latest_message.content:
                    respuesta = latest_message.content[0].text.value
                    return respuesta, function_call_data
            
            elif run.status == 'requires_action':
                # El asistente quiere llamar a una función
                function_call_data = self._manejar_function_call(
                    thread_id, 
                    run_id, 
                    run,
                    conversacion
                )
                # Continuar esperando la respuesta final
            
            elif run.status in ['failed', 'cancelled', 'expired']:
                error_msg = f"Ejecución falló con estado: {run.status}"
                if hasattr(run, 'last_error') and run.last_error:
                    error_msg += f"\nDetalles: {run.last_error}"
                raise Exception(error_msg)
            
            time.sleep(1)  # Esperar 1 segundo antes de revisar de nuevo
        
        raise TimeoutError("Tiempo de espera agotado para la respuesta del asistente")
    
    def _manejar_function_call(
        self, 
        thread_id: str, 
        run_id: str, 
        run,
        conversacion: ConversacionChatbot
    ) -> Dict:
        """
        Maneja las llamadas a funciones del asistente.
        
        Args:
            thread_id: ID del thread
            run_id: ID de la ejecución
            run: Objeto run con la información de la función
            conversacion: Conversación activa
        
        Returns:
            Dict: Datos de la función llamada
        """
        tool_outputs = []
        function_data = {}
        
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 Function call: {function_name} con args: {function_args}")
            
            # Guardar datos de la función
            function_data = {
                'function': function_name,
                'arguments': function_args
            }
            
            # Ejecutar la función correspondiente
            if function_name == 'buscar_disponibilidad':
                resultado = self._buscar_disponibilidad(
                    conversacion.empresa, 
                    function_args
                )
            elif function_name == 'agendar_cita':
                resultado = self._agendar_cita(
                    conversacion, 
                    function_args
                )
            else:
                resultado = {"error": f"Función {function_name} no implementada"}
            
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(resultado)
            })
        
        # Enviar resultados de las funciones al asistente
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run_id,
            tool_outputs=tool_outputs
        )
        
        return function_data
    
    def _buscar_disponibilidad(self, empresa: Empresa, args: Dict) -> Dict:
        """
        Busca horarios disponibles en la clínica.
        
        Args:
            empresa: Empresa/clínica
            args: Argumentos de la función (fecha, odontologo_id)
        
        Returns:
            Dict: Horarios disponibles
        """
        from datetime import datetime, timedelta
        
        fecha_str = args.get('fecha')
        odontologo_id = args.get('odontologo_id')
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}
        
        # Obtener odontólogos
        odontologos = Odontologo.objects.filter(empresa=empresa)
        if odontologo_id:
            odontologos = odontologos.filter(idusuario=odontologo_id)
        
        if not odontologos.exists():
            return {"error": "No hay odontólogos disponibles"}
        
        # Buscar citas ocupadas en esa fecha
        citas_ocupadas = Consulta.objects.filter(
            empresa=empresa,
            fecha=fecha
        ).values_list('hora', 'odontologo_id')
        
        # Horarios laborales típicos (8:00 - 18:00, cada 30 min)
        hora_inicio = datetime.combine(fecha, datetime.strptime('08:00', '%H:%M').time())
        hora_fin = datetime.combine(fecha, datetime.strptime('18:00', '%H:%M').time())
        
        horarios_disponibles = []
        hora_actual = hora_inicio
        
        while hora_actual < hora_fin:
            hora_str = hora_actual.strftime('%H:%M')
            
            # Verificar si está ocupado
            ocupado = any(
                hora == hora_actual.time() 
                for hora, _ in citas_ocupadas
            )
            
            if not ocupado:
                horarios_disponibles.append(hora_str)
            
            hora_actual += timedelta(minutes=30)
        
        return {
            "fecha": fecha_str,
            "horarios_disponibles": horarios_disponibles[:10],  # Limitar a 10
            "odontologos": [
                {"id": odon.idusuario, "nombre": odon.nombre}
                for odon in odontologos
            ]
        }
    
    def _agendar_cita(self, conversacion: ConversacionChatbot, args: Dict) -> Dict:
        """
        Crea una pre-consulta con los datos recopilados.
        NO crea la cita real, solo guarda los datos para que la recepcionista confirme.
        
        Args:
            conversacion: Conversación activa
            args: Datos del paciente y la cita
        
        Returns:
            Dict: Resultado del agendamiento
        """
        from datetime import datetime
        
        try:
            # Obtener o crear PreConsulta
            pre_consulta, created = PreConsulta.objects.get_or_create(
                conversacion=conversacion,
                defaults={
                    'nombre': args.get('nombre'),
                    'telefono': args.get('telefono'),
                    'email': args.get('email', ''),
                    'sintomas': args.get('motivo', ''),
                    'urgencia': 'media',  # Por defecto
                    'procesada': False
                }
            )
            
            # Actualizar datos si ya existía
            if not created:
                pre_consulta.nombre = args.get('nombre')
                pre_consulta.telefono = args.get('telefono')
                pre_consulta.email = args.get('email', '')
                pre_consulta.sintomas = args.get('motivo', '')
            
            # Guardar preferencias de fecha/hora
            fecha_str = args.get('fecha')
            hora_str = args.get('hora')
            
            if fecha_str:
                try:
                    fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    pre_consulta.fecha_preferida = fecha
                except ValueError:
                    pass
            
            if hora_str:
                pre_consulta.horario_preferido = hora_str
            
            pre_consulta.save()
            
            # Actualizar estado de conversación
            conversacion.estado = 'cita_agendada'
            conversacion.save()
            
            return {
                "success": True,
                "mensaje": f"Hemos registrado tu solicitud de cita para el {fecha_str} a las {hora_str}. "
                          f"Un miembro de nuestro equipo te contactará pronto al {args.get('telefono')} "
                          f"para confirmar tu cita. ¡Gracias!"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error al procesar la cita: {str(e)}"
            }


def evaluar_urgencia(sintomas: str, dolor_nivel: Optional[int] = None) -> str:
    """
    Evalúa el nivel de urgencia basado en síntomas y nivel de dolor.
    
    Args:
        sintomas: Descripción de síntomas
        dolor_nivel: Nivel de dolor 1-10
    
    Returns:
        str: 'alta', 'media', o 'baja'
    """
    sintomas_lower = sintomas.lower()
    
    # Palabras clave de urgencia alta
    urgencia_alta_keywords = [
        'sangrado', 'hemorragia', 'trauma', 'golpe', 'accidente',
        'hinchazón', 'inflamación', 'pus', 'infección', 'fiebre',
        'fractura', 'diente roto', 'insoportable'
    ]
    
    # Palabras clave de urgencia media
    urgencia_media_keywords = [
        'dolor', 'molestia', 'sensibilidad', 'caries', 
        'corona suelta', 'empaste', 'limpieza'
    ]
    
    # Verificar urgencia alta
    if any(keyword in sintomas_lower for keyword in urgencia_alta_keywords):
        return 'alta'
    
    # Verificar por nivel de dolor
    if dolor_nivel and dolor_nivel >= 7:
        return 'alta'
    elif dolor_nivel and dolor_nivel >= 4:
        return 'media'
    
    # Verificar urgencia media
    if any(keyword in sintomas_lower for keyword in urgencia_media_keywords):
        return 'media'
    
    return 'baja'
