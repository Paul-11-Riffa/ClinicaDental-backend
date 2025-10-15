from rest_framework import serializers
from .models import Paciente, Consulta, Odontologo, Servicio

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
    """Serializer para modelo Servicio"""
    class Meta:
        model = Servicio
        fields = '__all__'
        read_only_fields = ['empresa']