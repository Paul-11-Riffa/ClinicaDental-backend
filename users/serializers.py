from rest_framework import serializers
from api.models import Usuario, Tipodeusuario

class UsuarioSerializer(serializers.ModelSerializer):
    """Serializer para modelo Usuario"""
    class Meta:
        model = Usuario
        fields = '__all__'
        read_only_fields = ['empresa']

class TipodeusuarioSerializer(serializers.ModelSerializer):
    """Serializer para modelo Tipodeusuario"""
    class Meta:
        model = Tipodeusuario
        fields = '__all__'
        read_only_fields = ['empresa']
