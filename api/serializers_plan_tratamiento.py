# api/serializers_plan_tratamiento.py
"""
Serializers para la funcionalidad de gestión de planes de tratamiento.
SP3-T001: Crear plan de tratamiento (Web)
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal

from .models import (
    Plandetratamiento,
    Itemplandetratamiento,
    Paciente,
    Odontologo,
    Usuario,
    Estado,
    Servicio,
    Piezadental
)


# ============================================================================
# SERIALIZERS PARA ITEMS
# ============================================================================

class ItemPlanTratamientoSerializer(serializers.ModelSerializer):
    """Serializer completo para ítems del plan de tratamiento."""
    servicio_nombre = serializers.CharField(source='idservicio.nombre', read_only=True)
    servicio_descripcion = serializers.CharField(source='idservicio.descripcion', read_only=True)
    servicio_duracion = serializers.IntegerField(source='idservicio.duracion', read_only=True)
    pieza_dental_nombre = serializers.CharField(source='idpiezadental.nombrepieza', read_only=True, allow_null=True)
    estado_nombre = serializers.CharField(source='idestado.estado', read_only=True)
    
    # Campos calculados
    es_activo = serializers.SerializerMethodField()
    es_cancelado = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'id',
            'idservicio',
            'servicio_nombre',
            'servicio_descripcion',
            'servicio_duracion',
            'idpiezadental',
            'pieza_dental_nombre',
            'idestado',
            'estado_nombre',
            'costofinal',
            'costo_base_servicio',
            'fecha_objetivo',
            'tiempo_estimado',
            'estado_item',
            'notas_item',
            'orden',
            'es_activo',
            'es_cancelado',
            'puede_editarse',
        ]
        read_only_fields = ['id', 'costo_base_servicio']
    
    def get_es_activo(self, obj):
        return obj.esta_activo()
    
    def get_es_cancelado(self, obj):
        return obj.esta_cancelado()
    
    def get_puede_editarse(self, obj):
        return obj.puede_editarse()


class CrearItemPlanSerializer(serializers.ModelSerializer):
    """Serializer para crear/editar un ítem del plan."""
    
    # idestado NO debe ser incluido aquí - los items usan estado_item, no idestado
    # idestado es un campo del modelo pero se asigna automáticamente, no desde el frontend
    
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'idservicio',
            'idpiezadental',
            'costofinal',
            'fecha_objetivo',
            'tiempo_estimado',
            'estado_item',  # Usar estado_item en lugar de idestado
            'notas_item',
            'orden',
        ]
    
    def validate(self, data):
        """Validaciones de negocio."""
        # Validar que el costo sea positivo
        if data.get('costofinal') and data['costofinal'] < 0:
            raise serializers.ValidationError({
                'costofinal': 'El costo final debe ser mayor o igual a cero.'
            })
        
        # Validar tiempo estimado
        if data.get('tiempo_estimado') and data['tiempo_estimado'] <= 0:
            raise serializers.ValidationError({
                'tiempo_estimado': 'El tiempo estimado debe ser mayor a cero.'
            })
        
        # Validar fecha objetivo no esté en el pasado
        fecha_objetivo = data.get('fecha_objetivo')
        if fecha_objetivo and fecha_objetivo < timezone.now().date():
            raise serializers.ValidationError({
                'fecha_objetivo': 'La fecha objetivo no puede ser en el pasado.'
            })
        
        return data
    
    def create(self, validated_data):
        """Crear ítem y capturar costo base del servicio."""
        servicio = validated_data.get('idservicio')
        plan = validated_data.get('idplantratamiento')
        
        # Capturar costo base del servicio
        validated_data['costo_base_servicio'] = servicio.costobase
        
        # Si no se especifica costo final, usar costo base
        if 'costofinal' not in validated_data or validated_data['costofinal'] is None:
            validated_data['costofinal'] = servicio.costobase
        
        # Si no se especifica tiempo estimado, usar duración del servicio
        if 'tiempo_estimado' not in validated_data or validated_data['tiempo_estimado'] is None:
            validated_data['tiempo_estimado'] = servicio.duracion
        
        # Si no se especifica estado_item, usar 'Pendiente'
        if 'estado_item' not in validated_data or not validated_data['estado_item']:
            validated_data['estado_item'] = Itemplandetratamiento.ESTADO_PENDIENTE
        
        # Asignar empresa del plan
        if plan:
            validated_data['empresa'] = plan.empresa
            
            # Asignar idestado automáticamente (required en el modelo)
            # Buscar estado "Pendiente" de la empresa
            try:
                estado_pendiente = Estado.objects.get(
                    empresa=plan.empresa,
                    estado='Pendiente'
                )
                validated_data['idestado'] = estado_pendiente
            except Estado.DoesNotExist:
                # Si no existe, crear el estado Pendiente
                estado_pendiente = Estado.objects.create(
                    empresa=plan.empresa,
                    estado='Pendiente'
                )
                validated_data['idestado'] = estado_pendiente
        
        return super().create(validated_data)


class ItemPlanListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar ítems."""
    servicio_nombre = serializers.CharField(source='idservicio.nombre', read_only=True)
    pieza_dental = serializers.CharField(source='idpiezadental.nombrepieza', read_only=True, allow_null=True)
    
    class Meta:
        model = Itemplandetratamiento
        fields = [
            'id',
            'servicio_nombre',
            'pieza_dental',
            'costofinal',
            'fecha_objetivo',
            'estado_item',
            'orden',
        ]


# ============================================================================
# SERIALIZERS PARA PLAN DE TRATAMIENTO
# ============================================================================

class PlanTratamientoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de planes."""
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    cantidad_items = serializers.SerializerMethodField()
    items_activos = serializers.SerializerMethodField()
    items_completados = serializers.SerializerMethodField()
    es_borrador = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'id',
            'fechaplan',
            'paciente_nombre',
            'odontologo_nombre',
            'estado_plan',
            'estado_aceptacion',
            'montototal',
            'subtotal_calculado',
            'descuento',
            'cantidad_items',
            'items_activos',
            'items_completados',
            'es_borrador',
            'puede_editarse',
            'fecha_aprobacion',
            'fecha_vigencia',
            'version',
        ]
    
    def get_paciente_nombre(self, obj):
        return f"{obj.codpaciente.codusuario.nombre} {obj.codpaciente.codusuario.apellido}"
    
    def get_odontologo_nombre(self, obj):
        return f"Dr. {obj.cododontologo.codusuario.nombre} {obj.cododontologo.codusuario.apellido}"
    
    def get_cantidad_items(self, obj):
        return obj.itemplandetratamiento_set.count()
    
    def get_items_activos(self, obj):
        return obj.itemplandetratamiento_set.filter(estado_item='Activo').count()
    
    def get_items_completados(self, obj):
        return obj.itemplandetratamiento_set.filter(estado_item='Completado').count()
    
    def get_es_borrador(self, obj):
        return obj.es_borrador()
    
    def get_puede_editarse(self, obj):
        return obj.puede_editarse()


class PlanTratamientoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver un plan específico."""
    paciente = serializers.SerializerMethodField()
    odontologo = serializers.SerializerMethodField()
    items = ItemPlanTratamientoSerializer(source='itemplandetratamiento_set', many=True, read_only=True)
    usuario_aprueba_nombre = serializers.SerializerMethodField()
    usuario_acepta_nombre = serializers.SerializerMethodField()
    
    # Campos calculados
    es_borrador = serializers.SerializerMethodField()
    es_aprobado = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    puede_ser_aceptado = serializers.SerializerMethodField()
    estadisticas = serializers.SerializerMethodField()
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'id',
            'fechaplan',
            'paciente',
            'odontologo',
            'estado_plan',
            'estado_aceptacion',
            'aceptacion_tipo',
            'version',
            'notas_plan',
            'subtotal_calculado',
            'descuento',
            'montototal',
            'items',
            'fecha_aprobacion',
            'usuario_aprueba_nombre',
            'fecha_vigencia',
            'fecha_aceptacion',
            'usuario_acepta_nombre',
            'es_borrador',
            'es_aprobado',
            'puede_editarse',
            'puede_ser_aceptado',
            'es_editable',
            'estadisticas',
        ]
    
    def get_paciente(self, obj):
        return {
            'id': obj.codpaciente.codusuario.codigo,
            'nombre': obj.codpaciente.codusuario.nombre,
            'apellido': obj.codpaciente.codusuario.apellido,
            'email': obj.codpaciente.codusuario.correoelectronico,
        }
    
    def get_odontologo(self, obj):
        return {
            'id': obj.cododontologo.codusuario.codigo,
            'nombre': f"Dr. {obj.cododontologo.codusuario.nombre} {obj.cododontologo.codusuario.apellido}",
            'especialidad': obj.cododontologo.especialidad,
        }
    
    def get_usuario_aprueba_nombre(self, obj):
        if obj.usuario_aprueba:
            return f"{obj.usuario_aprueba.nombre} {obj.usuario_aprueba.apellido}"
        return None
    
    def get_usuario_acepta_nombre(self, obj):
        if obj.usuario_acepta:
            return f"{obj.usuario_acepta.nombre} {obj.usuario_acepta.apellido}"
        return None
    
    def get_es_borrador(self, obj):
        return obj.es_borrador()
    
    def get_es_aprobado(self, obj):
        return obj.es_aprobado()
    
    def get_puede_editarse(self, obj):
        return obj.puede_editarse()
    
    def get_puede_ser_aceptado(self, obj):
        return obj.puede_ser_aceptado()
    
    def get_estadisticas(self, obj):
        """Estadísticas del plan."""
        items = obj.itemplandetratamiento_set.all()
        return {
            'total_items': items.count(),
            'items_pendientes': items.filter(estado_item='Pendiente').count(),
            'items_activos': items.filter(estado_item='Activo').count(),
            'items_cancelados': items.filter(estado_item='Cancelado').count(),
            'items_completados': items.filter(estado_item='Completado').count(),
            'progreso_porcentaje': self._calcular_progreso(items),
        }
    
    def _calcular_progreso(self, items):
        """Calcula el porcentaje de progreso del plan."""
        total = items.exclude(estado_item='Cancelado').count()
        if total == 0:
            return 0
        completados = items.filter(estado_item='Completado').count()
        return round((completados / total) * 100, 2)


class CrearPlanTratamientoSerializer(serializers.ModelSerializer):
    """Serializer para crear un nuevo plan de tratamiento."""
    items_iniciales = CrearItemPlanSerializer(many=True, required=False, allow_empty=True)
    fechaplan = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'codpaciente',
            'cododontologo',
            'fechaplan',
            'notas_plan',
            'descuento',
            'fecha_vigencia',
            'items_iniciales',
        ]
    
    def validate(self, data):
        """Validaciones de negocio."""
        # Validar que paciente y odontólogo pertenezcan a la misma empresa
        paciente = data.get('codpaciente')
        odontologo = data.get('cododontologo')
        
        if paciente and odontologo:
            if paciente.empresa != odontologo.empresa:
                raise serializers.ValidationError(
                    "El paciente y el odontólogo deben pertenecer a la misma empresa."
                )
        
        # Validar descuento
        descuento = data.get('descuento', 0)
        if descuento and descuento < 0:
            raise serializers.ValidationError({
                'descuento': 'El descuento no puede ser negativo.'
            })
        
        # Validar fecha de vigencia
        fecha_vigencia = data.get('fecha_vigencia')
        if fecha_vigencia and fecha_vigencia < timezone.now().date():
            raise serializers.ValidationError({
                'fecha_vigencia': 'La fecha de vigencia no puede ser en el pasado.'
            })
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear plan con ítems iniciales."""
        items_data = validated_data.pop('items_iniciales', [])
        
        # Obtener empresa del contexto (tenant)
        request = self.context.get('request')
        empresa = getattr(request, 'tenant', None)
        
        # Si no se proporciona fecha del plan, usar la fecha actual
        if 'fechaplan' not in validated_data or validated_data['fechaplan'] is None:
            validated_data['fechaplan'] = timezone.now().date()
        
        # Obtener estado por defecto (primer estado disponible)
        estado = Estado.objects.filter(empresa=empresa).first()
        if not estado:
            # Crear estado por defecto si no existe
            estado = Estado.objects.create(estado='Planificado', empresa=empresa)
        
        # Crear el plan
        plan = Plandetratamiento.objects.create(
            **validated_data,
            empresa=empresa,
            idestado=estado,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
            montototal=Decimal('0.00'),
            subtotal_calculado=Decimal('0.00'),
        )
        
        # Crear ítems iniciales
        for item_data in items_data:
            # Obtener servicio
            servicio = item_data.get('idservicio')
            
            # Asignar estado automáticamente
            try:
                estado_pendiente = Estado.objects.get(
                    empresa=empresa,
                    estado='Pendiente'
                )
            except Estado.DoesNotExist:
                # Crear estado Pendiente si no existe
                estado_pendiente = Estado.objects.create(
                    empresa=empresa,
                    estado='Pendiente'
                )
            
            # Crear el item directamente
            Itemplandetratamiento.objects.create(
                idplantratamiento=plan,
                empresa=empresa,
                idestado=estado_pendiente,
                idservicio=servicio,
                idpiezadental=item_data.get('idpiezadental'),
                costofinal=item_data.get('costofinal') or servicio.costobase,
                costo_base_servicio=servicio.costobase,
                fecha_objetivo=item_data.get('fecha_objetivo'),
                tiempo_estimado=item_data.get('tiempo_estimado') or servicio.duracion,
                estado_item=item_data.get('estado_item', Itemplandetratamiento.ESTADO_PENDIENTE),
                notas_item=item_data.get('notas_item', ''),
                orden=item_data.get('orden', 0),
            )
        
        # Calcular totales iniciales
        plan.calcular_totales()
        
        return plan


class ActualizarPlanTratamientoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar un plan en borrador."""
    
    class Meta:
        model = Plandetratamiento
        fields = [
            'notas_plan',
            'descuento',
            'fecha_vigencia',
        ]
    
    def validate(self, data):
        """Validar que el plan esté en borrador."""
        plan = self.instance
        
        if not plan.puede_editarse():
            raise serializers.ValidationError(
                "Solo se pueden editar planes en estado borrador que no han sido aceptados."
            )
        
        # Validar descuento
        descuento = data.get('descuento')
        if descuento is not None and descuento < 0:
            raise serializers.ValidationError({
                'descuento': 'El descuento no puede ser negativo.'
            })
        
        return data
    
    def update(self, instance, validated_data):
        """Actualizar plan y recalcular totales si cambió el descuento."""
        descuento_cambio = 'descuento' in validated_data
        
        plan = super().update(instance, validated_data)
        
        if descuento_cambio:
            plan.calcular_totales()
        
        return plan


class AprobarPlanSerializer(serializers.Serializer):
    """Serializer para aprobar un plan de tratamiento."""
    confirmar = serializers.BooleanField(
        required=True,
        help_text="Debe ser True para confirmar la aprobación."
    )
    
    def validate_confirmar(self, value):
        """Validar confirmación."""
        if not value:
            raise serializers.ValidationError("Debe confirmar la aprobación del plan.")
        return value
    
    def validate(self, data):
        """Validar que el plan pueda aprobarse."""
        plan = self.context.get('plan')
        
        if not plan:
            raise serializers.ValidationError("Plan no encontrado.")
        
        if not plan.es_borrador():
            raise serializers.ValidationError("Solo se pueden aprobar planes en estado borrador.")
        
        # Validar que tenga al menos un ítem activo
        items_activos = plan.itemplandetratamiento_set.filter(
            estado_item__in=['Activo', 'Pendiente']
        ).count()
        
        if items_activos == 0:
            raise serializers.ValidationError(
                "El plan debe tener al menos un ítem activo o pendiente para ser aprobado."
            )
        
        return data
