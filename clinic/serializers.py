from rest_framework import serializers
from api.models import Paciente, Consulta, Odontologo, Servicio, Piezadental

class PacienteSerializer(serializers.ModelSerializer):
    """Serializer para modelo Paciente con datos del usuario"""
    # Campos del usuario anidados para fácil acceso en frontend
    codigo = serializers.IntegerField(source='codusuario.codigo', read_only=True)
    nombre = serializers.CharField(source='codusuario.nombre', read_only=True)
    apellido = serializers.CharField(source='codusuario.apellido', read_only=True)
    correoelectronico = serializers.CharField(source='codusuario.correoelectronico', read_only=True)
    telefono = serializers.CharField(source='codusuario.telefono', read_only=True)
    sexo = serializers.CharField(source='codusuario.sexo', read_only=True)
    nombre_completo = serializers.SerializerMethodField()
    
    class Meta:
        model = Paciente
        fields = [
            'codigo',
            'nombre',
            'apellido',
            'nombre_completo',
            'correoelectronico',
            'telefono',
            'sexo',
            'carnetidentidad',
            'fechanacimiento',
            'direccion',
            'empresa'
        ]
        read_only_fields = ['empresa', 'codigo']
    
    def get_nombre_completo(self, obj):
        """Devuelve el nombre completo del paciente"""
        return f"{obj.codusuario.nombre} {obj.codusuario.apellido}"

class ConsultaSerializer(serializers.ModelSerializer):
    """Serializer para modelo Consulta"""
    class Meta:
        model = Consulta
        fields = '__all__'
        read_only_fields = ['empresa']

class OdontologoSerializer(serializers.ModelSerializer):
    """Serializer para modelo Odontólogo"""
    class Meta:
        model = Odontologo
        fields = '__all__'
        read_only_fields = ['empresa']

class ServicioSerializer(serializers.ModelSerializer):
    """Serializer para modelo Servicio con campos completos"""
    precio_vigente = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='costobase',
        read_only=True,
        help_text="Precio actual del servicio"
    )
    
    class Meta:
        model = Servicio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'costobase',
            'precio_vigente',
            'duracion',
            'activo',
            'fecha_creacion',
            'fecha_modificacion',
            'empresa'
        ]
        read_only_fields = ['empresa', 'fecha_creacion', 'fecha_modificacion']

class ServicioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de servicios"""
    precio_vigente = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        source='costobase',
        read_only=True
    )
    
    class Meta:
        model = Servicio
        fields = ['id', 'nombre', 'costobase', 'precio_vigente', 'duracion', 'activo']
        read_only_fields = ['id']


class PiezadentalSerializer(serializers.ModelSerializer):
    """Serializer para piezas dentales"""
    class Meta:
        model = Piezadental
        fields = ['id', 'nombrepieza', 'grupo', 'empresa']
        read_only_fields = ['id', 'empresa']
