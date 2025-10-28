"""
Serializers para Sesiones de Tratamiento
SP3-T008: Registrar procedimiento clínico (web)
"""
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import SesionTratamiento, Itemplandetratamiento, Consulta, Usuario
from .serializers_presupuestos import ItemplandetratamientoSerializer
from .serializers import ConsultaSerializer


class SesionTratamientoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear sesiones de tratamiento."""
    
    class Meta:
        model = SesionTratamiento
        fields = [
            'id',
            'item_plan',
            'consulta',
            'fecha_sesion',
            'hora_inicio',
            'duracion_minutos',
            'progreso_actual',
            'acciones_realizadas',
            'notas_sesion',
            'complicaciones',
            'evidencias',
            'usuario_registro',
            'empresa',
        ]
        read_only_fields = ['id', 'progreso_anterior', 'fecha_registro', 'fecha_modificacion']
    
    def validate(self, attrs):
        """Validaciones de negocio."""
        item_plan = attrs.get('item_plan')
        consulta = attrs.get('consulta')
        progreso_actual = attrs.get('progreso_actual')
        
        # 1. Validar que el ítem no esté cancelado
        if item_plan.esta_cancelado():
            raise serializers.ValidationError({
                'item_plan': 'No se pueden registrar sesiones sobre ítems cancelados.'
            })
        
        # 2. Validar que no exista ya una sesión para esta consulta + item_plan
        if SesionTratamiento.objects.filter(
            consulta=consulta,
            item_plan=item_plan
        ).exists():
            raise serializers.ValidationError({
                'item_plan': 'Ya existe una sesión registrada para este ítem en esta consulta.'
            })
        
        # 3. Validar que el progreso esté en rango válido
        if not (0 <= progreso_actual <= 100):
            raise serializers.ValidationError({
                'progreso_actual': 'El progreso debe estar entre 0 y 100%.'
            })
        
        # 4. Validar que el progreso actual sea mayor o igual al progreso anterior
        sesiones_anteriores = SesionTratamiento.objects.filter(
            item_plan=item_plan
        ).order_by('-fecha_sesion', '-hora_inicio')
        
        if sesiones_anteriores.exists():
            progreso_anterior = sesiones_anteriores.first().progreso_actual
            if progreso_actual < progreso_anterior:
                raise serializers.ValidationError({
                    'progreso_actual': f'El progreso actual ({progreso_actual}%) no puede ser menor al progreso anterior ({progreso_anterior}%).'
                })
        
        # 5. Validar que el ítem y la consulta pertenezcan al mismo paciente
        if item_plan.idplantratamiento.codpaciente_id != consulta.codpaciente_id:
            raise serializers.ValidationError({
                'consulta': 'La consulta y el plan de tratamiento deben pertenecer al mismo paciente.'
            })
        
        # 6. Validar que el ítem pertenezca a un plan aprobado
        if item_plan.idplantratamiento.estado_plan != 'Aprobado':
            raise serializers.ValidationError({
                'item_plan': 'Solo se pueden registrar sesiones sobre planes aprobados.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """Crear sesión con lógica de negocio."""
        item_plan = validated_data['item_plan']
        progreso_actual = validated_data['progreso_actual']
        
        # Si el ítem está pendiente, activarlo automáticamente al crear primera sesión
        if item_plan.estado_item == Itemplandetratamiento.ESTADO_PENDIENTE:
            item_plan.activar()
        
        # Crear la sesión
        sesion = super().create(validated_data)
        
        # Si progreso llega a 100%, marcar ítem como completado
        if progreso_actual >= 100:
            item_plan.completar()
        
        return sesion


class SesionTratamientoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar sesiones de tratamiento."""
    
    class Meta:
        model = SesionTratamiento
        fields = [
            'id',
            'fecha_sesion',
            'hora_inicio',
            'duracion_minutos',
            'progreso_actual',
            'acciones_realizadas',
            'notas_sesion',
            'complicaciones',
            'evidencias',
        ]
        read_only_fields = ['id', 'item_plan', 'consulta', 'progreso_anterior']
    
    def validate_progreso_actual(self, value):
        """Validar que el progreso no retroceda."""
        if not (0 <= value <= 100):
            raise serializers.ValidationError('El progreso debe estar entre 0 y 100%.')
        
        # Obtener progreso anterior de esta sesión
        if self.instance:
            progreso_anterior = self.instance.progreso_anterior
            if value < progreso_anterior:
                raise serializers.ValidationError(
                    f'El progreso no puede ser menor al progreso anterior ({progreso_anterior}%).'
                )
        
        return value
    
    def update(self, instance, validated_data):
        """Actualizar sesión con lógica de negocio."""
        progreso_actual = validated_data.get('progreso_actual', instance.progreso_actual)
        
        # Actualizar la sesión
        sesion = super().update(instance, validated_data)
        
        # Si progreso llega a 100%, marcar ítem como completado
        if progreso_actual >= 100 and instance.item_plan.estado_item != Itemplandetratamiento.ESTADO_COMPLETADO:
            instance.item_plan.completar()
        
        # Recalcular progreso del plan
        sesion.recalcular_progreso_plan()
        
        return sesion


class SesionTratamientoListSerializer(serializers.ModelSerializer):
    """Serializer para listar sesiones con información detallada."""
    item_plan = ItemplandetratamientoSerializer(read_only=True)
    consulta = ConsultaSerializer(read_only=True)
    usuario_registro_nombre = serializers.SerializerMethodField()
    incremento_progreso = serializers.SerializerMethodField()
    paciente_nombre = serializers.SerializerMethodField()
    servicio_nombre = serializers.SerializerMethodField()
    
    class Meta:
        model = SesionTratamiento
        fields = [
            'id',
            'item_plan',
            'consulta',
            'fecha_sesion',
            'hora_inicio',
            'duracion_minutos',
            'progreso_anterior',
            'progreso_actual',
            'incremento_progreso',
            'acciones_realizadas',
            'notas_sesion',
            'complicaciones',
            'evidencias',
            'usuario_registro',
            'usuario_registro_nombre',
            'fecha_registro',
            'fecha_modificacion',
            'paciente_nombre',
            'servicio_nombre',
        ]
    
    def get_usuario_registro_nombre(self, obj):
        """Retorna el nombre completo del usuario que registró la sesión."""
        if obj.usuario_registro:
            return f"{obj.usuario_registro.nombre} {obj.usuario_registro.apellido}"
        return None
    
    def get_incremento_progreso(self, obj):
        """Retorna el incremento de progreso en esta sesión."""
        return obj.get_incremento_progreso()
    
    def get_paciente_nombre(self, obj):
        """Retorna el nombre del paciente."""
        if obj.item_plan and obj.item_plan.idplantratamiento:
            paciente = obj.item_plan.idplantratamiento.codpaciente
            return f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"
        return None
    
    def get_servicio_nombre(self, obj):
        """Retorna el nombre del servicio."""
        if obj.item_plan and obj.item_plan.idservicio:
            return obj.item_plan.idservicio.nombre
        return None


class SesionTratamientoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para una sesión específica."""
    item_plan = ItemplandetratamientoSerializer(read_only=True)
    consulta = ConsultaSerializer(read_only=True)
    usuario_registro_info = serializers.SerializerMethodField()
    incremento_progreso = serializers.SerializerMethodField()
    plan_tratamiento_info = serializers.SerializerMethodField()
    estadisticas_item = serializers.SerializerMethodField()
    
    class Meta:
        model = SesionTratamiento
        fields = '__all__'
    
    def get_usuario_registro_info(self, obj):
        """Información completa del usuario que registró."""
        if obj.usuario_registro:
            return {
                'id': obj.usuario_registro.codigo,
                'nombre_completo': f"{obj.usuario_registro.nombre} {obj.usuario_registro.apellido}",
                'email': obj.usuario_registro.correoelectronico,
            }
        return None
    
    def get_incremento_progreso(self, obj):
        """Incremento de progreso en esta sesión."""
        return obj.get_incremento_progreso()
    
    def get_plan_tratamiento_info(self, obj):
        """Información del plan de tratamiento asociado."""
        plan = obj.item_plan.idplantratamiento
        return {
            'id': plan.id,
            'estado_plan': plan.estado_plan,
            'fecha_aprobacion': plan.fecha_aprobacion,
            'total_items': plan.itemplandetratamiento_set.count(),
        }
    
    def get_estadisticas_item(self, obj):
        """Estadísticas del ítem relacionado."""
        item = obj.item_plan
        sesiones = SesionTratamiento.objects.filter(item_plan=item)
        
        return {
            'total_sesiones': sesiones.count(),
            'duracion_total_minutos': sum(s.duracion_minutos for s in sesiones),
            'progreso_actual': float(obj.progreso_actual),
            'estado_item': item.estado_item,
        }


class ProgresoItemSerializer(serializers.Serializer):
    """Serializer para consultar el progreso de un ítem."""
    item_plan_id = serializers.IntegerField()
    progreso_actual = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_sesiones = serializers.IntegerField()
    ultima_sesion_fecha = serializers.DateField(allow_null=True)
    estado_item = serializers.CharField()
    puede_facturar = serializers.BooleanField()


class ProgresoPlanSerializer(serializers.Serializer):
    """Serializer para consultar el progreso general de un plan."""
    plan_id = serializers.IntegerField()
    progreso_general = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_items = serializers.IntegerField()
    items_completados = serializers.IntegerField()
    items_activos = serializers.IntegerField()
    items_pendientes = serializers.IntegerField()
    plan_completado = serializers.BooleanField()
