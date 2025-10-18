"""
ViewSet para creación de usuarios con diferentes roles.
Permite a los administradores crear usuarios de tipo Paciente, Odontólogo, Recepcionista o Administrador.
"""

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from django.db import transaction

from .models import Usuario, Tipodeusuario
from .serializers_user_creation import (
    CrearUsuarioRequestSerializer,
    UsuarioCreateResponseSerializer,
    CrearPacienteSerializer,
    CrearOdontologoSerializer,
    CrearRecepcionistaSerializer,
    CrearAdministradorSerializer,
)
from .models import Bitacora


def _es_admin_por_tabla(request):
    """
    Verifica si el usuario autenticado es administrador.
    """
    if not hasattr(request.user, 'email'):
        return False
    try:
        usuario = Usuario.objects.select_related('idtipousuario').get(
            correoelectronico__iexact=request.user.email
        )
        return usuario.idtipousuario_id == 1
    except Usuario.DoesNotExist:
        return False


class CrearUsuarioViewSet(GenericViewSet):
    """
    ViewSet para la creación de usuarios por parte de administradores.
    
    Endpoints:
    - POST /api/crear-usuario/ - Crea un nuevo usuario del tipo especificado
    - GET /api/crear-usuario/tipos-usuario/ - Lista los tipos de usuario disponibles
    - GET /api/crear-usuario/campos-requeridos/?tipo=2 - Obtiene campos requeridos por tipo
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='')
    def crear_usuario(self, request):
        """
        Crea un nuevo usuario según el tipo especificado.
        
        Body esperado:
        {
            "tipo_usuario": 2,  // 1=Admin, 2=Paciente, 3=Odontólogo, 4=Recepcionista
            "datos": {
                // Campos base (todos los tipos)
                "nombre": "Juan",
                "apellido": "Pérez",
                "correoelectronico": "juan@example.com",
                "sexo": "M",  // opcional
                "telefono": "12345678",  // opcional
                
                // Campos específicos según tipo_usuario
                // Para Paciente (tipo_usuario=2):
                "carnetidentidad": "1234567",  // opcional
                "fechanacimiento": "1990-01-01",  // opcional
                "direccion": "Calle 123",  // opcional
                
                // Para Odontólogo (tipo_usuario=3):
                "especialidad": "Ortodoncia",  // opcional
                "experienciaprofesional": "5 años",  // opcional
                "nromatricula": "12345",  // opcional
                
                // Para Recepcionista (tipo_usuario=4):
                "habilidadessoftware": "Office, CRM",  // opcional
                
                // Para Admin (tipo_usuario=1):
                // Solo campos base
            }
        }
        """
        # Verificar que el usuario es administrador
        if not _es_admin_por_tabla(request):
            return Response(
                {"error": "Solo los administradores pueden crear usuarios."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Obtener el tenant (empresa) del request
        empresa = getattr(request, 'tenant', None)
        if not empresa:
            return Response(
                {"error": "No se pudo determinar la empresa del usuario."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validar la solicitud
        serializer = CrearUsuarioRequestSerializer(
            data=request.data,
            context={'empresa': empresa, 'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                {"error": "Datos inválidos", "detalles": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Obtener el serializer específico ya validado
            serializer_especifico = serializer.validated_data['_serializer_validado']
            
            # Crear el usuario
            with transaction.atomic():
                usuario_creado = serializer_especifico.save()
                
                # Obtener usuario actual para bitácora
                try:
                    usuario_actual = Usuario.objects.get(correoelectronico__iexact=request.user.email)
                except Usuario.DoesNotExist:
                    usuario_actual = None
                
                # Obtener IP y User-Agent del request
                ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')
                user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
                
                # Registrar en bitácora
                Bitacora.objects.create(
                    empresa=empresa,
                    usuario=usuario_actual,
                    accion=f"CREAR_USUARIO_{usuario_creado.idtipousuario.rol.upper()}",
                    tabla_afectada="usuario",
                    registro_id=usuario_creado.codigo,
                    valores_nuevos={
                        'codigo': usuario_creado.codigo,
                        'nombre': usuario_creado.nombre,
                        'apellido': usuario_creado.apellido,
                        'correoelectronico': usuario_creado.correoelectronico,
                        'tipo_usuario': usuario_creado.idtipousuario.rol,
                        'telefono': usuario_creado.telefono,
                        'sexo': usuario_creado.sexo,
                    },
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            # Preparar respuesta
            response_serializer = UsuarioCreateResponseSerializer(usuario_creado)
            
            return Response(
                {
                    "mensaje": f"Usuario creado exitosamente como {usuario_creado.idtipousuario.rol}",
                    "usuario": response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error al crear usuario: {type(e).__name__}: {str(e)}", exc_info=True)
            
            return Response(
                {
                    "error": "Error al crear el usuario",
                    "detalles": str(e),
                    "tipo_error": type(e).__name__
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='tipos-usuario')
    def tipos_usuario(self, request):
        """
        Lista los tipos de usuario disponibles.
        
        GET /api/crear-usuario/tipos-usuario/
        
        Respuesta:
        {
            "tipos": [
                {"id": 1, "nombre": "Administrador", "tiene_tabla_adicional": false},
                {"id": 2, "nombre": "Paciente", "tiene_tabla_adicional": true},
                {"id": 3, "nombre": "Odontólogo", "tiene_tabla_adicional": true},
                {"id": 4, "nombre": "Recepcionista", "tiene_tabla_adicional": true}
            ]
        }
        """
        tipos = Tipodeusuario.objects.all().order_by('id')
        
        tipos_data = []
        for tipo in tipos:
            tipos_data.append({
                'id': tipo.id,
                'nombre': tipo.rol,
                'tiene_tabla_adicional': tipo.id in [2, 3, 4],  # Paciente, Odontólogo, Recepcionista
            })
        
        return Response({'tipos': tipos_data})
    
    @action(detail=False, methods=['get'], url_path='campos-requeridos')
    def campos_requeridos(self, request):
        """
        Devuelve la estructura de campos requeridos y opcionales para cada tipo de usuario.
        
        GET /api/crear-usuario/campos-requeridos/?tipo=2
        
        Parámetros:
        - tipo: ID del tipo de usuario (1, 2, 3, 4). Si no se proporciona, devuelve todos.
        
        Respuesta:
        {
            "tipo_usuario": 2,
            "nombre_tipo": "Paciente",
            "campos_base": {
                "nombre": {"tipo": "string", "requerido": true, "max_length": 255},
                "apellido": {"tipo": "string", "requerido": true, "max_length": 255},
                ...
            },
            "campos_adicionales": {
                "carnetidentidad": {"tipo": "string", "requerido": false, "max_length": 50},
                ...
            }
        }
        """
        tipo_id = request.query_params.get('tipo')
        
        # Campos base que todos los usuarios tienen
        campos_base = {
            "nombre": {
                "tipo": "string",
                "requerido": True,
                "max_length": 255,
                "descripcion": "Nombre del usuario"
            },
            "apellido": {
                "tipo": "string",
                "requerido": True,
                "max_length": 255,
                "descripcion": "Apellido del usuario"
            },
            "correoelectronico": {
                "tipo": "email",
                "requerido": True,
                "max_length": 255,
                "descripcion": "Correo electrónico (debe ser único)"
            },
            "sexo": {
                "tipo": "string",
                "requerido": False,
                "max_length": 50,
                "opciones": ["M", "F", "Otro"],
                "descripcion": "Sexo del usuario"
            },
            "telefono": {
                "tipo": "string",
                "requerido": False,
                "max_length": 20,
                "descripcion": "Número de teléfono"
            },
            "recibir_notificaciones": {
                "tipo": "boolean",
                "requerido": False,
                "default": True,
                "descripcion": "Si el usuario desea recibir notificaciones"
            },
            "notificaciones_email": {
                "tipo": "boolean",
                "requerido": False,
                "default": True,
                "descripcion": "Si el usuario desea recibir notificaciones por email"
            },
            "notificaciones_push": {
                "tipo": "boolean",
                "requerido": False,
                "default": False,
                "descripcion": "Si el usuario desea recibir notificaciones push"
            }
        }
        
        # Campos específicos por tipo de usuario
        campos_por_tipo = {
            1: {  # Administrador
                "nombre_tipo": "Administrador",
                "campos_adicionales": {}
            },
            2: {  # Paciente
                "nombre_tipo": "Paciente",
                "campos_adicionales": {
                    "carnetidentidad": {
                        "tipo": "string",
                        "requerido": False,
                        "max_length": 50,
                        "descripcion": "Carnet de identidad (debe ser único si se proporciona)"
                    },
                    "fechanacimiento": {
                        "tipo": "date",
                        "requerido": False,
                        "formato": "YYYY-MM-DD",
                        "descripcion": "Fecha de nacimiento"
                    },
                    "direccion": {
                        "tipo": "text",
                        "requerido": False,
                        "descripcion": "Dirección del paciente"
                    }
                }
            },
            3: {  # Odontólogo
                "nombre_tipo": "Odontólogo",
                "campos_adicionales": {
                    "especialidad": {
                        "tipo": "string",
                        "requerido": False,
                        "max_length": 255,
                        "descripcion": "Especialidad del odontólogo"
                    },
                    "experienciaprofesional": {
                        "tipo": "text",
                        "requerido": False,
                        "descripcion": "Experiencia profesional del odontólogo"
                    },
                    "nromatricula": {
                        "tipo": "string",
                        "requerido": False,
                        "max_length": 100,
                        "descripcion": "Número de matrícula profesional (debe ser único si se proporciona)"
                    }
                }
            },
            4: {  # Recepcionista
                "nombre_tipo": "Recepcionista",
                "campos_adicionales": {
                    "habilidadessoftware": {
                        "tipo": "text",
                        "requerido": False,
                        "descripcion": "Habilidades de software del recepcionista"
                    }
                }
            }
        }
        
        # Si se especificó un tipo, devolver solo ese
        if tipo_id:
            try:
                tipo_id = int(tipo_id)
                if tipo_id not in campos_por_tipo:
                    return Response(
                        {"error": f"Tipo de usuario {tipo_id} no válido. Valores permitidos: 1, 2, 3, 4"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response({
                    "tipo_usuario": tipo_id,
                    "nombre_tipo": campos_por_tipo[tipo_id]["nombre_tipo"],
                    "campos_base": campos_base,
                    "campos_adicionales": campos_por_tipo[tipo_id]["campos_adicionales"]
                })
            except ValueError:
                return Response(
                    {"error": "Parámetro 'tipo' debe ser un número"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Si no se especificó tipo, devolver todos
        todos_los_tipos = []
        for tipo_id, info in campos_por_tipo.items():
            todos_los_tipos.append({
                "tipo_usuario": tipo_id,
                "nombre_tipo": info["nombre_tipo"],
                "campos_base": campos_base,
                "campos_adicionales": info["campos_adicionales"]
            })
        
        return Response({"tipos": todos_los_tipos})
    
    def create(self, request):
        """Redirige a crear_usuario para mantener consistencia."""
        return self.crear_usuario(request)
