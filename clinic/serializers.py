from rest_framework import serializers
from api.models import Paciente, Consulta, Odontologo, Servicio

class PacienteSerializer(serializers.ModelSerializer):
    """Serializer para modelo Paciente"""
    class Meta:
        model = Paciente
        fields = '__all__'
        read_only_fields = ['empresa']

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