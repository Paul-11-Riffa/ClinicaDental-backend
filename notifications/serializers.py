from rest_framework import serializers
from .models import TipoNotificacion, CanalNotificacion

class TipoNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para modelo TipoNotificacion"""
    class Meta:
        model = TipoNotificacion
        fields = '__all__'
        read_only_fields = ['empresa', 'fechacreacion']

class CanalNotificacionSerializer(serializers.ModelSerializer):
    """Serializer para modelo CanalNotificacion"""
    class Meta:
        model = CanalNotificacion
        fields = '__all__'
        read_only_fields = ['empresa', 'fechacreacion']