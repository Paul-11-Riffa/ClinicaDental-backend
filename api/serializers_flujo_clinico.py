"""
Serializers para el Flujo Clínico
Paso 3: Endpoints API para gestión de consultas, planes e items con flujo de estados
"""
from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone

from .models import (
    Consulta, Plandetratamiento, Itemplandetratamiento,
    Paciente, Odontologo, Empresa, Servicio, Estado
)


class ConsultaFlujoClincoSerializer(serializers.ModelSerializer):
    """
    Serializer para Consulta con información del flujo clínico.
    Incluye campos calculados y relaciones simplificadas.
    """
    # Campos de solo lectura calculados
    es_diagnostico = serializers.SerializerMethodField()
    puede_generar_plan = serializers.SerializerMethodField()
    plan_asociado = serializers.SerializerMethodField()
    validacion_flujo = serializers.SerializerMethodField()
    
    # Relaciones simplificadas
    paciente_nombre = serializers.CharField(source='codpaciente.nombre', read_only=True)
    odontologo_nombre = serializers.CharField(source='cododontologo.nombre', read_only=True)
    estado_consulta = serializers.CharField(source='idestadoconsulta.estado', read_only=True)
    tipo_consulta = serializers.CharField(source='idtipoconsulta.nombreconsulta', read_only=True)
    
    class Meta:
        model = Consulta
        fields = [
            'id', 'fecha', 'codpaciente', 'cododontologo',
            'paciente_nombre', 'odontologo_nombre',
            'idestadoconsulta', 'estado_consulta',
            'idtipoconsulta', 'tipo_consulta',
            'idhorario',
            'costo_consulta', 'requiere_pago',
            'plan_tratamiento',
            'es_diagnostico', 'puede_generar_plan', 
            'plan_asociado', 'validacion_flujo',
            'empresa'
        ]
        read_only_fields = ['id', 'empresa']
    
    def get_es_diagnostico(self, obj):
        """Indica si es consulta diagnóstica o de ejecución"""
        return obj.es_consulta_diagnostico()
    
    def get_puede_generar_plan(self, obj):
        """Valida si puede generar plan de tratamiento"""
        puede, mensaje = obj.puede_generar_plan()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_plan_asociado(self, obj):
        """Retorna ID del plan asociado si existe"""
        plan = obj.get_plan_asociado()
        if plan:
            return {
                'id': plan.id,
                'estado': plan.estado_tratamiento,
                'notas': plan.notas_plan[:100] if plan.notas_plan else None
            }
        return None
    
    def get_validacion_flujo(self, obj):
        """Validaciones de consistencia de datos"""
        es_valido, errores = obj.validar_datos_flujo()
        return {
            'es_valido': es_valido,
            'errores': errores
        }


class ItemEjecucionSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para items de plan con estado de ejecución.
    """
    servicio_nombre = serializers.CharField(source='idservicio.nombre', read_only=True)
    odontologo_ejecutor_nombre = serializers.CharField(
        source='odontologo_ejecutor.codusuario.nombre', 
        read_only=True
    )
    puede_ejecutarse = serializers.SerializerMethodField()
    esta_ejecutado = serializers.SerializerMethodField()
    puede_reprogramarse = serializers.SerializerMethodField()
    tiempo_desde_ejecucion = serializers.SerializerMethodField()
    
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'id', 'idservicio', 'servicio_nombre',
            'costofinal', 'orden_ejecucion', 'estado_item',
            'fecha_ejecucion', 'odontologo_ejecutor', 'odontologo_ejecutor_nombre',
            'consulta_ejecucion', 'notas_ejecucion',
            'puede_ejecutarse', 'esta_ejecutado', 
            'puede_reprogramarse', 'tiempo_desde_ejecucion'
        ]
        read_only_fields = ['id']
    
    def get_puede_ejecutarse(self, obj):
        """Valida si el item puede ejecutarse ahora"""
        puede, mensaje = obj.puede_ejecutarse()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_esta_ejecutado(self, obj):
        """Indica si ya fue ejecutado"""
        return obj.esta_ejecutado()
    
    def get_puede_reprogramarse(self, obj):
        """Valida si puede cambiar su orden"""
        puede, mensaje = obj.puede_reprogramarse()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_tiempo_desde_ejecucion(self, obj):
        """Tiempo transcurrido desde ejecución"""
        tiempo = obj.get_tiempo_transcurrido_desde_ejecucion()
        if tiempo:
            return {
                'dias': tiempo.days,
                'horas': tiempo.seconds // 3600,
                'minutos': (tiempo.seconds % 3600) // 60
            }
        return None


class PlanTratamientoFlujoClincoSerializer(serializers.ModelSerializer):
    """
    Serializer completo para Plan de Tratamiento con flujo clínico.
    Incluye items, progreso y validaciones de estado.
    """
    # Campos calculados
    progreso_ejecucion = serializers.SerializerMethodField()
    puede_iniciar = serializers.SerializerMethodField()
    puede_completarse = serializers.SerializerMethodField()
    puede_modificar_items = serializers.SerializerMethodField()
    siguiente_item = serializers.SerializerMethodField()
    validacion_consistencia = serializers.SerializerMethodField()
    
    # Relaciones
    paciente_nombre = serializers.CharField(source='codpaciente.nombre', read_only=True)
    odontologo_nombre = serializers.CharField(source='codoontologo.nombre', read_only=True)
    items = ItemEjecucionSerializer(many=True, read_only=True, source='itemplandetratamiento_set')
    
    # Consultas relacionadas
    consulta_diagnostico_fecha = serializers.DateField(
        source='consulta_diagnostico.fecha', 
        read_only=True
    )
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'id', 'fechaplan',
            'codpaciente', 'paciente_nombre',
            'cododontologo', 'odontologo_nombre',
            'idestado', 'montototal', 'descuento',
            'notas_plan',
            # Campos de flujo clínico (Paso 1)
            'estado_tratamiento', 'fecha_inicio_ejecucion', 
            'fecha_finalizacion',
            'consulta_diagnostico', 'consulta_diagnostico_fecha',
            # Campos calculados (Paso 2)
            'progreso_ejecucion', 'puede_iniciar', 'puede_completarse',
            'puede_modificar_items', 'siguiente_item', 'validacion_consistencia',
            # Items
            'items',
            'empresa'
        ]
        read_only_fields = ['id', 'empresa']
    
    def get_progreso_ejecucion(self, obj):
        """Porcentaje de progreso 0-100"""
        return round(obj.calcular_progreso_ejecucion(), 2)
    
    def get_puede_iniciar(self, obj):
        """Valida si puede iniciar ejecución"""
        puede, mensaje = obj.puede_iniciar_ejecucion()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_puede_completarse(self, obj):
        """Valida si puede marcarse como completado"""
        puede, mensaje = obj.puede_completarse()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_puede_modificar_items(self, obj):
        """Valida si pueden agregarse/eliminarse items"""
        puede, mensaje = obj.puede_modificar_items()
        return {
            'puede': puede,
            'mensaje': mensaje
        }
    
    def get_siguiente_item(self, obj):
        """Obtiene el siguiente item por ejecutar"""
        item = obj.get_siguiente_item_por_ejecutar()
        if item:
            return {
                'id': item.id,
                'servicio': item.idservicio.nombre,
                'orden': item.orden_ejecucion,
                'costo': float(item.costofinal) if item.costofinal else 0
            }
        return None
    
    def get_validacion_consistencia(self, obj):
        """Validaciones de consistencia del flujo"""
        es_valido, errores = obj.validar_consistencia_flujo()
        return {
            'es_valido': es_valido,
            'errores': errores
        }


class PlanTratamientoCreateSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para crear planes de tratamiento.
    Usado en la acción generar_plan desde Consulta.
    """
    class Meta:
        model = Plandetratamiento
        fields = [
            'notas_plan', 'codpaciente', 'cododontologo',
            'idestado', 'consulta_diagnostico', 'empresa', 'fechaplan'
        ]
        read_only_fields = ['empresa']
    
    def validate(self, data):
        """Validaciones antes de crear el plan"""
        # Validar que la consulta pueda generar plan
        consulta = data.get('consulta_diagnostico')
        if consulta:
            puede, mensaje = consulta.puede_generar_plan()
            if not puede:
                raise serializers.ValidationError({
                    'consulta_diagnostico': mensaje
                })
        
        return data


class ItemEjecucionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para ejecutar un item en una consulta.
    Usado en la acción ejecutar_en_consulta.
    """
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'consulta_ejecucion', 'odontologo_ejecutor', 'notas_ejecucion'
        ]
    
    def validate(self, data):
        """Validaciones antes de ejecutar"""
        item = self.instance
        if item:
            puede, mensaje = item.puede_ejecutarse()
            if not puede:
                raise serializers.ValidationError({
                    'non_field_errors': [mensaje]
                })
        
        return data


class ItemReprogramarSerializer(serializers.Serializer):
    """
    Serializer para reprogramar el orden de ejecución de un item.
    """
    nuevo_orden = serializers.IntegerField(min_value=1)
    
    def validate_nuevo_orden(self, value):
        """Validar que el nuevo orden sea válido"""
        item = self.context.get('item')
        if item:
            puede, mensaje = item.puede_reprogramarse()
            if not puede:
                raise serializers.ValidationError(mensaje)
        
        return value
