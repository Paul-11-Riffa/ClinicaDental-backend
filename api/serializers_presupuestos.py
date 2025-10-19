# api/serializers_presupuestos.py
"""
Serializers para la funcionalidad de aceptación de presupuestos/planes de tratamiento.
SP3-T003: Implementar Aceptar presupuesto por parte del paciente (web)
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
import json

from .models import (
    Plandetratamiento,
    Itemplandetratamiento,
    AceptacionPresupuesto,
    Paciente,
    Usuario,
    Estado,
    Servicio
)


class ItemplandetratamientoSerializer(serializers.ModelSerializer):
    """Serializer para items del plan de tratamiento."""
    servicio_nombre = serializers.CharField(source='idservicio.nombre', read_only=True)
    servicio_descripcion = serializers.CharField(source='idservicio.descripcion', read_only=True)
    pieza_dental = serializers.CharField(source='idpiezadental.nombrepieza', read_only=True, allow_null=True)
    estado_nombre = serializers.CharField(source='idestado.nombreestado', read_only=True)
    
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'id',
            'idservicio',
            'servicio_nombre',
            'servicio_descripcion',
            'idpiezadental',
            'pieza_dental',
            'idestado',
            'estado_nombre',
            'costofinal',
        ]
        read_only_fields = ['id']


class PlandetratamientoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de presupuestos."""
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    estado_nombre = serializers.CharField(source='idestado.nombreestado', read_only=True)
    cantidad_items = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    puede_aceptar = serializers.SerializerMethodField()
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'id',
            'fechaplan',
            'paciente_nombre',
            'odontologo_nombre',
            'estado_nombre',
            'montototal',
            'descuento',
            'cantidad_items',
            'estado_aceptacion',
            'aceptacion_tipo',
            'fecha_vigencia',
            'fecha_aceptacion',
            'esta_vigente',
            'puede_aceptar',
        ]
    
    def get_paciente_nombre(self, obj):
        return f"{obj.codpaciente.codusuario.nombre} {obj.codpaciente.codusuario.apellido}"
    
    def get_odontologo_nombre(self, obj):
        return f"Dr. {obj.cododontologo.codusuario.nombre} {obj.cododontologo.codusuario.apellido}"
    
    def get_cantidad_items(self, obj):
        return obj.itemplandetratamiento_set.count()
    
    def get_esta_vigente(self, obj):
        return obj.esta_vigente()
    
    def get_puede_aceptar(self, obj):
        return obj.puede_ser_aceptado()


class PlandetratamientoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver un presupuesto específico."""
    paciente = serializers.SerializerMethodField()
    odontologo = serializers.SerializerMethodField()
    estado_nombre = serializers.CharField(source='idestado.nombreestado', read_only=True)
    items = ItemplandetratamientoSerializer(source='itemplandetratamiento_set', many=True, read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    puede_aceptar = serializers.SerializerMethodField()
    dias_para_vencimiento = serializers.SerializerMethodField()
    usuario_acepta_nombre = serializers.SerializerMethodField()
    aceptaciones_historial = serializers.SerializerMethodField()
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'id',
            'fechaplan',
            'paciente',
            'odontologo',
            'estado_nombre',
            'montototal',
            'descuento',
            'items',
            'estado_aceptacion',
            'aceptacion_tipo',
            'fecha_vigencia',
            'fecha_aceptacion',
            'usuario_acepta_nombre',
            'es_editable',
            'esta_vigente',
            'puede_aceptar',
            'dias_para_vencimiento',
            'aceptaciones_historial',
        ]
    
    def get_paciente(self, obj):
        return {
            'id': obj.codpaciente.id,
            'usuario_id': obj.codpaciente.codusuario.id,
            'nombre': obj.codpaciente.codusuario.nombre,
            'apellido': obj.codpaciente.codusuario.apellido,
            'email': obj.codpaciente.codusuario.email,
        }
    
    def get_odontologo(self, obj):
        return {
            'id': obj.cododontologo.id,
            'usuario_id': obj.cododontologo.codusuario.id,
            'nombre': f"Dr. {obj.cododontologo.codusuario.nombre} {obj.cododontologo.codusuario.apellido}",
        }
    
    def get_esta_vigente(self, obj):
        return obj.esta_vigente()
    
    def get_puede_aceptar(self, obj):
        return obj.puede_ser_aceptado()
    
    def get_dias_para_vencimiento(self, obj):
        if not obj.fecha_vigencia:
            return None
        delta = obj.fecha_vigencia - timezone.now().date()
        return delta.days if delta.days >= 0 else 0
    
    def get_usuario_acepta_nombre(self, obj):
        if obj.usuario_acepta:
            return f"{obj.usuario_acepta.nombre} {obj.usuario_acepta.apellido}"
        return None
    
    def get_aceptaciones_historial(self, obj):
        """Retorna el historial de aceptaciones (si existen)."""
        aceptaciones = obj.aceptaciones.all()[:5]  # Últimas 5
        return [{
            'comprobante_id': str(aceptacion.comprobante_id),
            'fecha': aceptacion.fecha_aceptacion,
            'tipo': aceptacion.tipo_aceptacion,
            'monto': str(aceptacion.monto_total_aceptado),
        } for aceptacion in aceptaciones]


class AceptarPresupuestoSerializer(serializers.Serializer):
    """
    Serializer para validar y procesar la aceptación de un presupuesto.
    
    Payload esperado:
    {
        "tipo_aceptacion": "Total" | "Parcial",
        "items_aceptados": [1, 2, 3],  # IDs de items (opcional si Total)
        "firma_digital": {
            "timestamp": "2025-10-19T10:30:00Z",
            "user_id": 123,
            "signature_hash": "abc123...",
            "metadata": {...}
        },
        "notas": "Comentarios opcionales del paciente"
    }
    """
    tipo_aceptacion = serializers.ChoiceField(
        choices=['Total', 'Parcial'],
        required=True,
        help_text="Tipo de aceptación: Total (todos los ítems) o Parcial (solo algunos)."
    )
    items_aceptados = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Lista de IDs de ítems a aceptar. Requerido si tipo_aceptacion es 'Parcial'."
    )
    firma_digital = serializers.JSONField(
        required=True,
        help_text="Firma digital en formato JSON con timestamp, user_id, hash, etc."
    )
    notas = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text="Notas o comentarios opcionales del paciente."
    )
    
    def validate(self, data):
        """Validaciones cruzadas."""
        tipo = data.get('tipo_aceptacion')
        items = data.get('items_aceptados', [])
        
        # Si es aceptación parcial, debe haber items
        if tipo == 'Parcial' and not items:
            raise serializers.ValidationError({
                'items_aceptados': 'Debe especificar al menos un ítem para aceptación parcial.'
            })
        
        # Validar estructura de firma digital
        firma = data.get('firma_digital', {})
        required_firma_fields = ['timestamp', 'user_id']
        for field in required_firma_fields:
            if field not in firma:
                raise serializers.ValidationError({
                    'firma_digital': f'El campo "{field}" es requerido en la firma digital.'
                })
        
        return data
    
    def validate_items_aceptados(self, value):
        """Valida que los IDs sean únicos y positivos."""
        if value:
            if len(value) != len(set(value)):
                raise serializers.ValidationError('La lista de ítems contiene duplicados.')
            if any(item_id <= 0 for item_id in value):
                raise serializers.ValidationError('Los IDs de ítems deben ser positivos.')
        return value


class AceptacionPresupuestoSerializer(serializers.ModelSerializer):
    """Serializer para crear registros de aceptación."""
    
    class Meta:
        model = AceptacionPresupuesto
        fields = [
            'id',
            'plandetratamiento',
            'usuario_paciente',
            'empresa',
            'fecha_aceptacion',
            'tipo_aceptacion',
            'items_aceptados',
            'firma_digital',
            'ip_address',
            'user_agent',
            'comprobante_id',
            'comprobante_url',
            'monto_total_aceptado',
            'notas',
        ]
        read_only_fields = [
            'id',
            'fecha_aceptacion',
            'comprobante_id',
        ]


class AceptacionPresupuestoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver una aceptación específica."""
    presupuesto = PlandetratamientoDetailSerializer(source='plandetratamiento', read_only=True)
    paciente = serializers.SerializerMethodField()
    items_detalle = serializers.SerializerMethodField()
    url_verificacion = serializers.SerializerMethodField()
    
    class Meta:
        model = AceptacionPresupuesto
        fields = [
            'id',
            'comprobante_id',
            'fecha_aceptacion',
            'tipo_aceptacion',
            'presupuesto',
            'paciente',
            'items_aceptados',
            'items_detalle',
            'firma_digital',
            'ip_address',
            'user_agent',
            'monto_total_aceptado',
            'notas',
            'comprobante_url',
            'url_verificacion',
        ]
    
    def get_paciente(self, obj):
        return {
            'id': obj.usuario_paciente.id,
            'nombre': f"{obj.usuario_paciente.nombre} {obj.usuario_paciente.apellido}",
            'email': obj.usuario_paciente.email,
        }
    
    def get_items_detalle(self, obj):
        """Si fue aceptación parcial, retorna el detalle de los ítems."""
        if obj.tipo_aceptacion == 'Parcial' and obj.items_aceptados:
            items = Itemplandetratamiento.objects.filter(
                id__in=obj.items_aceptados,
                idplantratamiento=obj.plandetratamiento
            )
            return ItemplandetratamientoSerializer(items, many=True).data
        return []
    
    def get_url_verificacion(self, obj):
        return obj.get_comprobante_verificacion_url()


class VerificarComprobanteSerializer(serializers.Serializer):
    """Serializer para verificar un comprobante de aceptación."""
    comprobante_id = serializers.UUIDField(
        required=True,
        help_text="ID del comprobante a verificar."
    )
    
    def validate_comprobante_id(self, value):
        """Verifica que el comprobante existe."""
        if not AceptacionPresupuesto.objects.filter(comprobante_id=value).exists():
            raise serializers.ValidationError('Comprobante no encontrado.')
        return value
