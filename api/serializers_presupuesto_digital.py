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


# =========================================================================
# SERIALIZERS PARA ACEPTACIÓN DE PRESUPUESTOS (SP3-T003)
# =========================================================================

class PresupuestoDigitalParaPacienteSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar presupuestos digitales al paciente.
    Incluye validaciones y metadata útil para la UI de aceptación.
    
    SP3-T003: Aceptar presupuesto digital por paciente
    """
    codigo_corto = serializers.SerializerMethodField()
    dias_para_vencimiento = serializers.SerializerMethodField()
    esta_vigente = serializers.SerializerMethodField()
    puede_ser_aceptado = serializers.SerializerMethodField()
    paciente_info = serializers.SerializerMethodField()
    odontologo_info = serializers.SerializerMethodField()
    items = ItemPresupuestoSerializer(source='items_presupuesto', many=True, read_only=True)
    permite_aceptacion_parcial = serializers.SerializerMethodField()
    estado_aceptacion_display = serializers.CharField(
        source='get_estado_aceptacion_display',
        read_only=True
    )
    
    class Meta:
        model = PresupuestoDigital
        fields = [
            'id',
            'codigo_presupuesto',
            'codigo_corto',
            'fecha_emision',
            'fecha_vigencia',
            'fecha_emitido',
            'dias_para_vencimiento',
            'esta_vigente',
            'estado',
            'estado_aceptacion',
            'estado_aceptacion_display',
            'fecha_aceptacion',
            'tipo_aceptacion',
            'puede_ser_aceptado',
            'es_editable',
            'paciente_info',
            'odontologo_info',
            'subtotal',
            'descuento',
            'total',
            'items',
            'permite_aceptacion_parcial',
            'terminos_condiciones',
            'notas',
            'pdf_url',
            'pdf_generado',
            'comprobante_aceptacion_url',
        ]
        read_only_fields = fields
    
    def get_codigo_corto(self, obj):
        """Código corto de 8 caracteres para mostrar en UI."""
        return obj.codigo_presupuesto.hex[:8].upper()
    
    def get_dias_para_vencimiento(self, obj):
        """Días restantes hasta que caduque el presupuesto."""
        if not obj.fecha_vigencia:
            return None
        delta = obj.fecha_vigencia - timezone.now().date()
        return delta.days
    
    def get_esta_vigente(self, obj):
        """Si el presupuesto está dentro de su vigencia."""
        return obj.esta_vigente()
    
    def get_puede_ser_aceptado(self, obj):
        """Si el presupuesto puede ser aceptado actualmente."""
        return obj.puede_ser_aceptado()
    
    def get_paciente_info(self, obj):
        """Información del paciente."""
        try:
            paciente = obj.plan_tratamiento.codpaciente
            return {
                'id': paciente.codigo,
                'nombre': paciente.codusuario.nombre,
                'apellido': paciente.codusuario.apellido,
                'email': paciente.codusuario.correoelectronico,
                'telefono': paciente.codusuario.telefono
            }
        except AttributeError:
            return None
    
    def get_odontologo_info(self, obj):
        """Información del odontólogo."""
        try:
            odontologo = obj.plan_tratamiento.cododontologo
            return {
                'id': odontologo.codigo,
                'nombre': f"Dr(a). {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}",
                'especialidad': odontologo.especialidad
            }
        except AttributeError:
            return None
    
    def get_permite_aceptacion_parcial(self, obj):
        """Si algún ítem permite pago parcial (aceptación por ítems)."""
        return obj.items_presupuesto.filter(permite_pago_parcial=True).exists()


class AceptarPresupuestoDigitalSerializer(serializers.Serializer):
    """
    Serializer para validar el payload de aceptación de presupuesto.
    
    Valida la firma digital, items aceptados y otros datos necesarios
    para registrar la aceptación del paciente.
    
    SP3-T003: Aceptar presupuesto digital por paciente
    """
    tipo_aceptacion = serializers.ChoiceField(
        choices=['Total', 'Parcial'],
        required=True,
        help_text="Tipo de aceptación: Total (todos los ítems) o Parcial (ítems seleccionados)"
    )
    
    items_aceptados = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=False,
        help_text="Lista de IDs de ItemPresupuestoDigital aceptados (requerido si tipo=Parcial)"
    )
    
    firma_digital = serializers.JSONField(
        required=True,
        help_text="Objeto JSON con datos de firma electrónica del paciente"
    )
    
    notas = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
        help_text="Comentarios o condiciones del paciente al aceptar"
    )
    
    def validate_tipo_aceptacion(self, value):
        """Valida que el tipo de aceptación sea válido."""
        if value not in ['Total', 'Parcial']:
            raise serializers.ValidationError(
                "Tipo de aceptación debe ser 'Total' o 'Parcial'"
            )
        return value
    
    def validate_items_aceptados(self, value):
        """Valida que los IDs de items sean válidos."""
        if value:
            # Verificar que sean enteros positivos
            for item_id in value:
                if not isinstance(item_id, int) or item_id <= 0:
                    raise serializers.ValidationError(
                        f"ID de ítem inválido: {item_id}"
                    )
        return value
    
    def validate_firma_digital(self, value):
        """Valida que la firma digital contenga los campos requeridos."""
        required_fields = ['timestamp', 'user_id', 'consent_text', 'signature_hash']
        
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(
                    f"Firma digital incompleta: falta campo '{field}'"
                )
        
        # Validar timestamp
        timestamp_str = value.get('timestamp')
        try:
            from django.utils.dateparse import parse_datetime
            timestamp = parse_datetime(timestamp_str)
            if not timestamp:
                raise ValueError("Formato inválido")
            
            # No puede ser futuro
            if timestamp > timezone.now():
                raise serializers.ValidationError(
                    "Timestamp de firma no puede ser futuro"
                )
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError(
                f"Timestamp inválido en firma digital: {str(e)}"
            )
        
        # Validar user_id
        if not isinstance(value.get('user_id'), int):
            raise serializers.ValidationError(
                "user_id debe ser un entero"
            )
        
        return value
    
    def validate(self, data):
        """Validaciones cruzadas."""
        tipo = data.get('tipo_aceptacion')
        items = data.get('items_aceptados', [])
        
        # Si es Parcial, debe tener items
        if tipo == 'Parcial':
            if not items or len(items) == 0:
                raise serializers.ValidationError({
                    'items_aceptados': "Aceptación parcial requiere seleccionar al menos un ítem"
                })
        
        # Si es Total, items debe estar vacío o no presente
        if tipo == 'Total' and items:
            raise serializers.ValidationError({
                'items_aceptados': "Aceptación total no debe incluir items_aceptados"
            })
        
        return data


class AceptacionPresupuestoDigitalSerializer(serializers.ModelSerializer):
    """
    Serializer para el modelo de aceptación (registro de auditoría).
    
    Usado para lectura de registros de aceptación y generación de comprobantes.
    
    SP3-T003: Aceptar presupuesto digital por paciente
    """
    comprobante_id_str = serializers.SerializerMethodField()
    presupuesto_codigo = serializers.SerializerMethodField()
    presupuesto_codigo_corto = serializers.SerializerMethodField()
    paciente_nombre_completo = serializers.SerializerMethodField()
    tipo_aceptacion_display = serializers.CharField(
        source='get_tipo_aceptacion_display',
        read_only=True
    )
    items_aceptados_detalle = serializers.SerializerMethodField()
    
    class Meta:
        model = serializers.ModelSerializer.Meta.model if hasattr(serializers.ModelSerializer, 'Meta') else None
        fields = [
            'id',
            'presupuesto_digital',
            'presupuesto_codigo',
            'presupuesto_codigo_corto',
            'usuario_paciente',
            'paciente_nombre_completo',
            'empresa',
            'fecha_aceptacion',
            'tipo_aceptacion',
            'tipo_aceptacion_display',
            'items_aceptados',
            'items_aceptados_detalle',
            'firma_digital',
            'ip_address',
            'user_agent',
            'comprobante_id',
            'comprobante_id_str',
            'comprobante_url',
            'monto_subtotal',
            'monto_descuento',
            'monto_total_aceptado',
            'notas_paciente',
            'listo_para_pago',
        ]
        read_only_fields = [
            'id',
            'fecha_aceptacion',
            'comprobante_id',
            'comprobante_url',
            'ip_address',
            'user_agent',
        ]
    
    def __init__(self, *args, **kwargs):
        """Fix Meta.model dinamically."""
        super().__init__(*args, **kwargs)
        if not self.Meta.model:
            from .models import AceptacionPresupuestoDigital
            self.Meta.model = AceptacionPresupuestoDigital
    
    def get_comprobante_id_str(self, obj):
        """Comprobante ID como string."""
        return str(obj.comprobante_id)
    
    def get_presupuesto_codigo(self, obj):
        """Código completo del presupuesto."""
        return str(obj.presupuesto_digital.codigo_presupuesto)
    
    def get_presupuesto_codigo_corto(self, obj):
        """Código corto del presupuesto (8 caracteres)."""
        return obj.presupuesto_digital.codigo_presupuesto.hex[:8].upper()
    
    def get_paciente_nombre_completo(self, obj):
        """Nombre completo del paciente."""
        return f"{obj.usuario_paciente.nombre} {obj.usuario_paciente.apellido}"
    
    def get_items_aceptados_detalle(self, obj):
        """Detalle de los ítems aceptados (si es aceptación parcial)."""
        if obj.tipo_aceptacion == 'Total' or not obj.items_aceptados:
            return []
        
        from .models import ItemPresupuestoDigital
        items = ItemPresupuestoDigital.objects.filter(
            id__in=obj.items_aceptados
        ).select_related('item_plan__idservicio')
        
        return [
            {
                'id': item.id,
                'servicio': item.item_plan.idservicio.nombre if item.item_plan.idservicio else 'N/A',
                'precio_final': str(item.precio_final),
            }
            for item in items
        ]
