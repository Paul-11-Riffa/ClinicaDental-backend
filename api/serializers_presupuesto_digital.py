# api/serializers_presupuesto_digital.py
"""
Serializers para la funcionalidad de generación de presupuestos digitales.
SP3-T002: Generar presupuesto digital (web)

Permite emitir un presupuesto total o por tramos a partir de un plan aprobado,
seleccionando qué ítems cotizar y habilitando pagos parciales por ítem;
genera PDF trazable con vigencia.
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal

from .models import (
    PresupuestoDigital,
    ItemPresupuestoDigital,
    Plandetratamiento,
    Itemplandetratamiento,
    Usuario,
    Servicio,
)


class ItemPresupuestoSerializer(serializers.ModelSerializer):
    """Serializer para ítems del presupuesto digital."""
    servicio_nombre = serializers.CharField(
        source='item_plan.idservicio.nombre',
        read_only=True
    )
    servicio_descripcion = serializers.CharField(
        source='item_plan.idservicio.descripcion',
        read_only=True
    )
    pieza_dental = serializers.CharField(
        source='item_plan.idpiezadental.nombrepieza',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ItemPresupuestoDigital
        fields = [
            'id',
            'item_plan',
            'servicio_nombre',
            'servicio_descripcion',
            'pieza_dental',
            'precio_unitario',
            'descuento_item',
            'precio_final',
            'permite_pago_parcial',
            'cantidad_cuotas',
            'notas_item',
            'orden',
        ]
        read_only_fields = ['id', 'precio_final']


class ListarPresupuestosSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de presupuestos digitales."""
    paciente_nombre = serializers.SerializerMethodField()
    odontologo_nombre = serializers.SerializerMethodField()
    cantidad_items = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    codigo_corto = serializers.SerializerMethodField()
    
    class Meta:
        model = PresupuestoDigital
        fields = [
            'id',
            'codigo_presupuesto',
            'codigo_corto',
            'plan_tratamiento',
            'paciente_nombre',
            'odontologo_nombre',
            'fecha_emision',
            'fecha_vigencia',
            'fecha_emitido',
            'estado',
            'es_tramo',
            'numero_tramo',
            'subtotal',
            'descuento',
            'total',
            'cantidad_items',
            'esta_vigente',
            'puede_editarse',
            'pdf_generado',
        ]
    
    def get_paciente_nombre(self, obj):
        paciente = obj.plan_tratamiento.codpaciente
        return f"{paciente.codusuario.nombre} {paciente.codusuario.apellido}"
    
    def get_odontologo_nombre(self, obj):
        odontologo = obj.plan_tratamiento.cododontologo
        return f"Dr. {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}"
    
    def get_cantidad_items(self, obj):
        return obj.items_presupuesto.count()
    
    def get_codigo_corto(self, obj):
        """Código corto para display (primeros 8 caracteres)."""
        return obj.codigo_presupuesto.hex[:8].upper()
    
    def get_esta_vigente(self, obj):
        """Indica si el presupuesto está vigente."""
        return obj.esta_vigente()
    
    def get_puede_editarse(self, obj):
        """Indica si el presupuesto puede editarse."""
        return obj.puede_editarse()


class DetallePresupuestoSerializer(serializers.ModelSerializer):
    """Serializer detallado para ver un presupuesto específico."""
    paciente = serializers.SerializerMethodField()
    odontologo = serializers.SerializerMethodField()
    items = ItemPresupuestoSerializer(source='items_presupuesto', many=True, read_only=True)
    esta_vigente = serializers.SerializerMethodField()
    puede_editarse = serializers.SerializerMethodField()
    dias_para_vencimiento = serializers.SerializerMethodField()
    codigo_corto = serializers.SerializerMethodField()
    usuario_emite_nombre = serializers.SerializerMethodField()
    plan_detalle = serializers.SerializerMethodField()
    
    class Meta:
        model = PresupuestoDigital
        fields = [
            'id',
            'codigo_presupuesto',
            'codigo_corto',
            'plan_tratamiento',
            'plan_detalle',
            'paciente',
            'odontologo',
            'fecha_emision',
            'fecha_vigencia',
            'fecha_emitido',
            'usuario_emite',
            'usuario_emite_nombre',
            'estado',
            'es_tramo',
            'numero_tramo',
            'subtotal',
            'descuento',
            'total',
            'terminos_condiciones',
            'notas',
            'pdf_url',
            'pdf_generado',
            'es_editable',
            'items',
            'esta_vigente',
            'puede_editarse',
            'dias_para_vencimiento',
            'fecha_creacion',
            'fecha_actualizacion',
        ]
    
    def get_paciente(self, obj):
        paciente = obj.plan_tratamiento.codpaciente
        return {
            'id': paciente.codusuario.codigo,
            'nombre': paciente.codusuario.nombre,
            'apellido': paciente.codusuario.apellido,
            'correo': paciente.codusuario.correoelectronico,
        }
    
    def get_odontologo(self, obj):
        odontologo = obj.plan_tratamiento.cododontologo
        return {
            'id': odontologo.codusuario.codigo,
            'nombre': odontologo.codusuario.nombre,
            'apellido': odontologo.codusuario.apellido,
            'especialidad': odontologo.especialidad,
        }
    
    def get_dias_para_vencimiento(self, obj):
        """Calcula días restantes hasta el vencimiento."""
        if not obj.fecha_vigencia:
            return None
        delta = obj.fecha_vigencia - timezone.now().date()
        return delta.days
    
    def get_codigo_corto(self, obj):
        return obj.codigo_presupuesto.hex[:8].upper()
    
    def get_usuario_emite_nombre(self, obj):
        if obj.usuario_emite:
            return f"{obj.usuario_emite.nombre} {obj.usuario_emite.apellido}"
        return None
    
    def get_plan_detalle(self, obj):
        """Información resumida del plan de tratamiento original."""
        plan = obj.plan_tratamiento
        return {
            'id': plan.id,
            'fecha': plan.fechaplan,
            'estado_plan': plan.estado_plan,
            'total_items': plan.itemplandetratamiento_set.count(),
        }
    
    def get_esta_vigente(self, obj):
        """Verifica si el presupuesto está vigente."""
        return obj.esta_vigente()
    
    def get_puede_editarse(self, obj):
        """Verifica si el presupuesto puede editarse."""
        return obj.puede_editarse()


class CrearPresupuestoSerializer(serializers.Serializer):
    """
    Serializer para crear un presupuesto digital desde un plan aprobado.
    
    Permite seleccionar qué ítems incluir (total o parcial/tramo).
    """
    plan_tratamiento_id = serializers.IntegerField(
        write_only=True,
        help_text="ID del plan de tratamiento aprobado desde el cual generar el presupuesto."
    )
    items_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        help_text="Lista de IDs de items (Itemplandetratamiento) a incluir. Si vacío, incluye todos."
    )
    fecha_vigencia = serializers.DateField(
        required=False,
        write_only=True,
        help_text="Fecha de vigencia del presupuesto. Por defecto: 30 días desde hoy."
    )
    es_tramo = serializers.BooleanField(
        default=False,
        write_only=True,
        help_text="Indica si es un presupuesto parcial (tramo) o total."
    )
    numero_tramo = serializers.IntegerField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Número de tramo si es presupuesto parcial."
    )
    descuento = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        write_only=True,
        help_text="Descuento global aplicado al presupuesto."
    )
    terminos_condiciones = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Términos y condiciones específicos del presupuesto."
    )
    notas = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text="Notas adicionales del presupuesto."
    )
    
    # Configuración de items
    items_config = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text="Configuración personalizada por ítem (descuentos, pagos parciales)."
    )
    
    def to_representation(self, instance):
        """Usa el serializer de lectura para la respuesta."""
        return DetallePresupuestoSerializer(instance).data
    
    def validate_plan_tratamiento_id(self, value):
        """Valida que el plan exista y esté aprobado."""
        try:
            plan = Plandetratamiento.objects.get(id=value)
        except Plandetratamiento.DoesNotExist:
            raise serializers.ValidationError("El plan de tratamiento no existe.")
        
        if not plan.es_aprobado():
            raise serializers.ValidationError(
                "Solo se pueden generar presupuestos desde planes aprobados."
            )
        
        return value
    
    def validate_items_ids(self, value):
        """Valida que los items existan y pertenezcan al plan."""
        if not value:
            return value
        
        items = Itemplandetratamiento.objects.filter(id__in=value)
        if items.count() != len(value):
            raise serializers.ValidationError(
                "Algunos items especificados no existen."
            )
        
        return value
    
    def validate(self, data):
        """Validaciones cruzadas."""
        # Si es tramo, debe tener número de tramo
        if data.get('es_tramo') and not data.get('numero_tramo'):
            raise serializers.ValidationError({
                'numero_tramo': 'Los presupuestos parciales deben tener número de tramo.'
            })
        
        # Validar que los items pertenezcan al plan
        plan_id = data['plan_tratamiento_id']
        items_ids = data['items_ids']
        
        if items_ids:
            items = Itemplandetratamiento.objects.filter(
                id__in=items_ids,
                idplantratamiento_id=plan_id
            )
            if items.count() != len(items_ids):
                raise serializers.ValidationError({
                    'items_ids': 'Algunos items no pertenecen al plan especificado.'
                })
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Crea el presupuesto digital con sus items."""
        request = self.context.get('request')
        empresa = request.tenant
        usuario = getattr(request.user, 'usuario', None)
        
        # Obtener datos
        plan = Plandetratamiento.objects.get(id=validated_data['plan_tratamiento_id'])
        items_ids = validated_data['items_ids']
        
        # Si no se especifican items, incluir todos los del plan
        if not items_ids:
            items_ids = list(
                plan.itemplandetratamiento_set.exclude(
                    estado_item__in=['cancelado', 'Cancelado']
                ).values_list('id', flat=True)
            )
        
        # Fecha de vigencia por defecto: 30 días
        fecha_vigencia = validated_data.get('fecha_vigencia')
        if not fecha_vigencia:
            fecha_vigencia = timezone.now().date() + timedelta(days=30)
        
        # Crear presupuesto
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=plan,
            empresa=empresa,
            fecha_vigencia=fecha_vigencia,
            es_tramo=validated_data.get('es_tramo', False),
            numero_tramo=validated_data.get('numero_tramo'),
            descuento=validated_data.get('descuento', 0),
            terminos_condiciones=validated_data.get('terminos_condiciones', ''),
            notas=validated_data.get('notas', ''),
        )
        
        # Crear items del presupuesto
        items_config = validated_data.get('items_config', [])
        items_config_dict = {item['item_id']: item for item in items_config}
        
        items_plan = Itemplandetratamiento.objects.filter(id__in=items_ids)
        for orden, item_plan in enumerate(items_plan, start=1):
            config = items_config_dict.get(item_plan.id, {})
            
            ItemPresupuestoDigital.objects.create(
                presupuesto=presupuesto,
                item_plan=item_plan,
                precio_unitario=item_plan.costofinal,
                descuento_item=config.get('descuento_item', 0),
                permite_pago_parcial=config.get('permite_pago_parcial', False),
                cantidad_cuotas=config.get('cantidad_cuotas'),
                notas_item=config.get('notas_item', ''),
                orden=orden,
            )
        
        # Calcular totales
        presupuesto.calcular_totales()
        
        # Registrar en bitácora
        from .models import Bitacora
        Bitacora.objects.create(
            empresa=empresa,
            usuario=usuario,
            accion="PRESUPUESTO_DIGITAL_CREADO",
            tabla_afectada="presupuesto_digital",
            registro_id=presupuesto.id,
            valores_nuevos={
                'codigo_presupuesto': presupuesto.codigo_presupuesto.hex[:8],
                'plan_tratamiento_id': plan.id,
                'items_count': len(items_ids),
                'total': str(presupuesto.total)
            },
            ip_address='127.0.0.1',
            user_agent='API'
        )
        
        return presupuesto


class EmitirPresupuestoSerializer(serializers.Serializer):
    """
    Serializer para emitir oficialmente un presupuesto.
    
    Cambia el estado a 'Emitido' y bloquea la edición.
    """
    confirmar = serializers.BooleanField(
        required=True,
        help_text="Confirmar emisión del presupuesto. Debe ser True."
    )
    
    def validate_confirmar(self, value):
        if not value:
            raise serializers.ValidationError("Debe confirmar la emisión del presupuesto.")
        return value
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Emite el presupuesto."""
        request = self.context.get('request')
        usuario = getattr(request.user, 'usuario', None)
        
        # Emitir presupuesto
        instance.emitir(usuario)
        
        # Registrar en bitácora
        from .models import Bitacora
        Bitacora.objects.create(
            empresa=request.tenant,
            usuario=usuario,
            accion="PRESUPUESTO_DIGITAL_EMITIDO",
            tabla_afectada="presupuesto_digital",
            registro_id=instance.id,
            valores_nuevos={
                'codigo_presupuesto': instance.codigo_presupuesto.hex[:8],
                'fecha_emitido': str(instance.fecha_emitido),
                'estado': instance.estado
            },
            ip_address='127.0.0.1',
            user_agent='API'
        )
        
        return instance


class ActualizarPresupuestoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar presupuestos en borrador."""
    
    class Meta:
        model = PresupuestoDigital
        fields = [
            'fecha_vigencia',
            'descuento',
            'terminos_condiciones',
            'notas',
        ]
    
    def validate(self, data):
        """Solo permite actualizar presupuestos en borrador."""
        if not self.instance.puede_editarse():
            raise serializers.ValidationError(
                "Solo se pueden editar presupuestos en estado borrador."
            )
        return data
    
    def update(self, instance, validated_data):
        """Actualiza y recalcula totales."""
        instance = super().update(instance, validated_data)
        instance.calcular_totales()
        
        # Bitácora
        request = self.context.get('request')
        if request:
            from .models import Bitacora
            usuario = getattr(request.user, 'usuario', None)
            Bitacora.objects.create(
                empresa=request.tenant,
                usuario=usuario,
                accion="PRESUPUESTO_DIGITAL_ACTUALIZADO",
                tabla_afectada="presupuesto_digital",
                registro_id=instance.id,
                valores_nuevos={
                    'codigo_presupuesto': instance.codigo_presupuesto.hex[:8],
                    'subtotal': str(instance.subtotal),
                    'total': str(instance.total)
                },
                ip_address='127.0.0.1',
                user_agent='API'
            )
        
        return instance
