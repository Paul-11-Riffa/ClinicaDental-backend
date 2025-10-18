"""
Serializers para creación de usuarios con roles específicos.
Permite a los administradores crear usuarios de diferentes tipos (Paciente, Odontólogo, Recepcionista, Admin).
"""

from rest_framework import serializers
from django.db import transaction
from .models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario


class BaseUsuarioCreateSerializer(serializers.Serializer):
    """
    Campos base que todos los usuarios deben tener.
    """
    nombre = serializers.CharField(max_length=255)
    apellido = serializers.CharField(max_length=255)
    correoelectronico = serializers.EmailField()
    sexo = serializers.CharField(max_length=50, required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    recibir_notificaciones = serializers.BooleanField(default=True, required=False)
    notificaciones_email = serializers.BooleanField(default=True, required=False)
    notificaciones_push = serializers.BooleanField(default=False, required=False)

    def validate_correoelectronico(self, value):
        """Validar que el email no esté ya registrado."""
        if Usuario.objects.filter(correoelectronico__iexact=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value.lower()


class CrearPacienteSerializer(BaseUsuarioCreateSerializer):
    """
    Serializer para crear un usuario de tipo Paciente.
    Incluye campos específicos de Paciente.
    """
    # Campos específicos de Paciente
    carnetidentidad = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    fechanacimiento = serializers.DateField(required=False, allow_null=True)
    direccion = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_carnetidentidad(self, value):
        """Validar que el CI no esté duplicado (si se proporciona)."""
        if value and Paciente.objects.filter(carnetidentidad=value).exists():
            raise serializers.ValidationError("Este carnet de identidad ya está registrado.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Crear Usuario y Paciente en una transacción."""
        empresa = self.context.get('empresa')
        
        # Obtener tipo de usuario Paciente (id=2)
        tipo_paciente = Tipodeusuario.objects.get(id=2)
        
        # Separar datos de usuario y paciente
        datos_paciente = {
            'carnetidentidad': validated_data.pop('carnetidentidad', None),
            'fechanacimiento': validated_data.pop('fechanacimiento', None),
            'direccion': validated_data.pop('direccion', None),
        }
        
        # Crear Usuario con flag para saltar signals
        usuario = Usuario(
            **validated_data,
            idtipousuario=tipo_paciente,
            empresa=empresa
        )
        usuario._skip_signals = True  # Flag para que el signal no cree el perfil
        usuario.save()
        
        # Crear Paciente manualmente
        paciente = Paciente.objects.create(
            codusuario=usuario,
            empresa=empresa,
            **datos_paciente
        )
        
        return usuario


class CrearOdontologoSerializer(BaseUsuarioCreateSerializer):
    """
    Serializer para crear un usuario de tipo Odontólogo.
    Incluye campos específicos de Odontólogo.
    """
    # Campos específicos de Odontólogo
    especialidad = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    experienciaprofesional = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    nromatricula = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)

    def validate_nromatricula(self, value):
        """Validar que el número de matrícula no esté duplicado (si se proporciona)."""
        if value and Odontologo.objects.filter(nromatricula=value).exists():
            raise serializers.ValidationError("Este número de matrícula ya está registrado.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        """Crear Usuario y Odontólogo en una transacción."""
        empresa = self.context.get('empresa')
        
        # Obtener tipo de usuario Odontólogo (id=3)
        tipo_odontologo = Tipodeusuario.objects.get(id=3)
        
        # Separar datos de usuario y odontólogo
        datos_odontologo = {
            'especialidad': validated_data.pop('especialidad', None),
            'experienciaprofesional': validated_data.pop('experienciaprofesional', None),
            'nromatricula': validated_data.pop('nromatricula', None),
        }
        
        # Crear Usuario con flag para saltar signals
        usuario = Usuario(
            **validated_data,
            idtipousuario=tipo_odontologo,
            empresa=empresa
        )
        usuario._skip_signals = True  # Flag para que el signal no cree el perfil
        usuario.save()
        
        # Crear Odontólogo manualmente
        odontologo = Odontologo.objects.create(
            codusuario=usuario,
            empresa=empresa,
            **datos_odontologo
        )
        
        return usuario


class CrearRecepcionistaSerializer(BaseUsuarioCreateSerializer):
    """
    Serializer para crear un usuario de tipo Recepcionista.
    Incluye campos específicos de Recepcionista.
    """
    # Campos específicos de Recepcionista
    habilidadessoftware = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    @transaction.atomic
    def create(self, validated_data):
        """Crear Usuario y Recepcionista en una transacción."""
        empresa = self.context.get('empresa')
        
        # Obtener tipo de usuario Recepcionista (id=4)
        tipo_recepcionista = Tipodeusuario.objects.get(id=4)
        
        # Separar datos de usuario y recepcionista
        datos_recepcionista = {
            'habilidadessoftware': validated_data.pop('habilidadessoftware', None),
        }
        
        # Crear Usuario con flag para saltar signals
        usuario = Usuario(
            **validated_data,
            idtipousuario=tipo_recepcionista,
            empresa=empresa
        )
        usuario._skip_signals = True  # Flag para que el signal no cree el perfil
        usuario.save()
        
        # Crear Recepcionista manualmente
        recepcionista = Recepcionista.objects.create(
            codusuario=usuario,
            empresa=empresa,
            **datos_recepcionista
        )
        
        return usuario


class CrearAdministradorSerializer(BaseUsuarioCreateSerializer):
    """
    Serializer para crear un usuario de tipo Administrador.
    Los administradores no tienen tabla adicional, solo el registro en Usuario.
    """
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear Usuario con rol de Administrador."""
        empresa = self.context.get('empresa')
        
        # Obtener tipo de usuario Administrador (id=1)
        tipo_admin = Tipodeusuario.objects.get(id=1)
        
        # Crear Usuario con flag para saltar signals
        usuario = Usuario(
            **validated_data,
            idtipousuario=tipo_admin,
            empresa=empresa
        )
        usuario._skip_signals = True  # Flag para que el signal no intente crear perfil
        usuario.save()
        
        return usuario


class UsuarioCreateResponseSerializer(serializers.ModelSerializer):
    """
    Serializer para la respuesta al crear un usuario.
    Devuelve la información completa del usuario creado.
    """
    idtipousuario = serializers.SerializerMethodField()
    tipo_usuario_nombre = serializers.CharField(source='idtipousuario.rol', read_only=True)
    
    # Campos adicionales según el rol
    paciente = serializers.SerializerMethodField()
    odontologo = serializers.SerializerMethodField()
    recepcionista = serializers.SerializerMethodField()
    
    class Meta:
        model = Usuario
        fields = [
            'codigo',
            'nombre',
            'apellido',
            'correoelectronico',
            'sexo',
            'telefono',
            'idtipousuario',
            'tipo_usuario_nombre',
            'recibir_notificaciones',
            'notificaciones_email',
            'notificaciones_push',
            'paciente',
            'odontologo',
            'recepcionista',
        ]
    
    def get_idtipousuario(self, obj):
        return obj.idtipousuario.id if obj.idtipousuario else None
    
    def get_paciente(self, obj):
        """Devuelve datos del perfil de Paciente si existe."""
        try:
            paciente = obj.paciente
            return {
                'carnetidentidad': paciente.carnetidentidad,
                'fechanacimiento': paciente.fechanacimiento,
                'direccion': paciente.direccion,
            }
        except Paciente.DoesNotExist:
            return None
    
    def get_odontologo(self, obj):
        """Devuelve datos del perfil de Odontólogo si existe."""
        try:
            odontologo = obj.odontologo
            return {
                'especialidad': odontologo.especialidad,
                'experienciaprofesional': odontologo.experienciaprofesional,
                'nromatricula': odontologo.nromatricula,
            }
        except Odontologo.DoesNotExist:
            return None
    
    def get_recepcionista(self, obj):
        """Devuelve datos del perfil de Recepcionista si existe."""
        try:
            recepcionista = obj.recepcionista
            return {
                'habilidadessoftware': recepcionista.habilidadessoftware,
            }
        except Recepcionista.DoesNotExist:
            return None


class CrearUsuarioRequestSerializer(serializers.Serializer):
    """
    Serializer que maneja la solicitud de creación de usuario.
    Determina qué serializer específico usar según el tipo de usuario.
    """
    tipo_usuario = serializers.IntegerField(
        help_text="ID del tipo de usuario: 1=Admin, 2=Paciente, 3=Odontólogo, 4=Recepcionista"
    )
    datos = serializers.JSONField(
        help_text="Objeto JSON con los datos del usuario según su tipo"
    )
    
    def validate_tipo_usuario(self, value):
        """Validar que el tipo de usuario existe y es válido."""
        if value not in [1, 2, 3, 4]:
            raise serializers.ValidationError(
                "Tipo de usuario inválido. Valores permitidos: 1=Admin, 2=Paciente, 3=Odontólogo, 4=Recepcionista"
            )
        
        # Verificar que el tipo existe en la BD
        if not Tipodeusuario.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"El tipo de usuario {value} no existe en el sistema.")
        
        return value
    
    def validate(self, attrs):
        """Validar que los datos proporcionados son correctos según el tipo de usuario."""
        tipo_usuario = attrs.get('tipo_usuario')
        datos = attrs.get('datos')
        
        # Seleccionar el serializer correcto según el tipo
        serializer_map = {
            1: CrearAdministradorSerializer,
            2: CrearPacienteSerializer,
            3: CrearOdontologoSerializer,
            4: CrearRecepcionistaSerializer,
        }
        
        serializer_class = serializer_map[tipo_usuario]
        serializer = serializer_class(data=datos, context=self.context)
        
        # Validar los datos con el serializer específico
        if not serializer.is_valid():
            raise serializers.ValidationError({
                'datos': serializer.errors
            })
        
        # Guardar el serializer validado para usarlo en create()
        attrs['_serializer_validado'] = serializer
        
        return attrs
    
    def create(self, validated_data):
        """
        Crear el usuario usando el serializer específico validado.
        """
        serializer = validated_data.get('_serializer_validado')
        if not serializer:
            raise serializers.ValidationError("No se encontró el serializer validado.")
        
        # Crear y devolver el usuario usando el serializer específico
        return serializer.save()
