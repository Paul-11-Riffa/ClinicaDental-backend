"""
SP3-T009: Serializers para Sistema de Pagos en Línea
Serializers para PagoEnLinea, DetallePagoItem, ComprobanteDigital
y operaciones de creación/actualización de pagos.
"""

from rest_framework import serializers
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

from .models import (
    PagoEnLinea, DetallePagoItem, ComprobanteDigital,
    Plandetratamiento, Itemplandetratamiento, Consulta,
    Usuario, Empresa
)
from .services.calculador_pagos import CalculadorPagos


# ==================== Serializers de Lectura ====================

class DetallePagoItemSerializer(serializers.ModelSerializer):
    """
    Serializer para leer detalles de pago por item.
    """
    item_plan_id = serializers.IntegerField(source='item_plan.id', read_only=True)
    servicio_nombre = serializers.CharField(
        source='item_plan.idservicio.nombre', 
        read_only=True
    )
    porcentaje_pagado = serializers.SerializerMethodField()
    
    class Meta:
        model = DetallePagoItem
        fields = [
            'id',
            'item_plan_id',
            'servicio_nombre',
            'monto_item_total',
            'monto_pagado_anterior',
            'monto_pagado_ahora',
            'monto_pagado_total',
            'saldo_restante',
            'item_completamente_pagado',
            'porcentaje_pagado'
        ]
        read_only_fields = fields
    
    def get_porcentaje_pagado(self, obj):
        """Calcula el porcentaje pagado del item."""
        if obj.item_plan:
            return float(obj.item_plan.calcular_porcentaje_pagado())
        return 0.0


class ComprobanteDigitalSerializer(serializers.ModelSerializer):
    """
    Serializer para leer comprobantes digitales.
    """
    url_verificacion = serializers.SerializerMethodField()
    puede_anularse = serializers.SerializerMethodField()
    esta_activo = serializers.SerializerMethodField()
    
    class Meta:
        model = ComprobanteDigital
        fields = [
            'id',
            'codigo_comprobante',
            'codigo_verificacion',
            'fecha_emision',
            'archivo_pdf',
            'estado_comprobante',
            'motivo_anulacion',
            'fecha_anulacion',
            'usuario_anula',
            'enviado_email',
            'fecha_envio_email',
            'datos_comprobante',
            'url_verificacion',
            'puede_anularse',
            'esta_activo'
        ]
        read_only_fields = fields
    
    def get_url_verificacion(self, obj):
        """Genera la URL de verificación del comprobante."""
        return obj.get_url_verificacion()
    
    def get_puede_anularse(self, obj):
        """Verifica si el comprobante puede ser anulado."""
        return obj.puede_anularse()
    
    def get_esta_activo(self, obj):
        """Verifica si el comprobante está activo."""
        return obj.esta_activo()


class PagoEnLineaSerializer(serializers.ModelSerializer):
    """
    Serializer principal para lectura de pagos en línea.
    Incluye información completa del pago con nested serializers.
    """
    # Información del origen
    plan_tratamiento_id = serializers.IntegerField(
        source='plan_tratamiento.id', 
        read_only=True
    )
    consulta_id = serializers.IntegerField(
        source='consulta.id', 
        read_only=True
    )
    paciente_nombre = serializers.SerializerMethodField()
    
    # Nested serializers
    detalles_items = DetallePagoItemSerializer(
        source='detalles_pago',
        many=True, 
        read_only=True
    )
    comprobante = ComprobanteDigitalSerializer(read_only=True)
    
    # Display fields
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    metodo_pago_display = serializers.CharField(
        source='get_metodo_pago_display',
        read_only=True
    )
    origen_display = serializers.CharField(
        source='get_origen_display',
        read_only=True
    )
    
    # Métodos de estado
    esta_pendiente = serializers.SerializerMethodField()
    esta_aprobado = serializers.SerializerMethodField()
    puede_reintentarse = serializers.SerializerMethodField()
    puede_anularse = serializers.SerializerMethodField()
    puede_reembolsarse = serializers.SerializerMethodField()
    tiene_comprobante = serializers.SerializerMethodField()
    
    class Meta:
        model = PagoEnLinea
        fields = [
            # IDs
            'id',
            'codigo_pago',
            
            # Origen
            'origen_tipo',
            'origen_display',
            'plan_tratamiento_id',
            'consulta_id',
            'paciente_nombre',
            
            # Montos
            'monto',
            'moneda',
            'monto_original',
            'saldo_anterior',
            'saldo_nuevo',
            
            # Estado y método
            'estado',
            'estado_display',
            'metodo_pago',
            'metodo_pago_display',
            'tipo_pago_consulta',
            
            # Stripe
            'stripe_payment_intent_id',
            'stripe_charge_id',
            'stripe_customer_id',
            'stripe_metadata',
            
            # Fechas
            'fecha_creacion',
            'fecha_procesamiento',
            'fecha_aprobacion',
            
            # Detalles
            'descripcion',
            'motivo_rechazo',
            
            # Auditoría
            'usuario',
            'ip_address',
            'user_agent',
            'numero_intentos',
            'ultimo_intento',
            
            # Nested
            'detalles_items',
            'comprobante',
            
            # Métodos
            'esta_pendiente',
            'esta_aprobado',
            'puede_reintentarse',
            'puede_anularse',
            'puede_reembolsarse',
            'tiene_comprobante',
        ]
        read_only_fields = [
            'id', 'codigo_pago', 'fecha_creacion', 'fecha_procesamiento', 'fecha_aprobacion',
            'stripe_payment_intent_id', 'stripe_charge_id',
            'stripe_customer_id', 'numero_intentos', 'ultimo_intento'
        ]
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente según el origen."""
        try:
            if obj.origen_tipo == 'plan_completo' or obj.origen_tipo == 'items_individuales':
                if obj.plan_tratamiento and obj.plan_tratamiento.codpaciente:
                    paciente = obj.plan_tratamiento.codpaciente
                    if paciente.codusuario:
                        return paciente.codusuario.nombre
            elif obj.origen_tipo == 'consulta':
                if obj.consulta and obj.consulta.codpaciente:
                    paciente = obj.consulta.codpaciente
                    if paciente.codusuario:
                        return paciente.codusuario.nombre
        except Exception:
            pass
        return None
    
    def get_esta_pendiente(self, obj):
        return obj.esta_pendiente()
    
    def get_esta_aprobado(self, obj):
        return obj.esta_aprobado()
    
    def get_puede_reintentarse(self, obj):
        return obj.puede_reintentarse()
    
    def get_puede_anularse(self, obj):
        return obj.puede_anularse()
    
    def get_puede_reembolsarse(self, obj):
        return obj.puede_reembolsarse()
    
    def get_tiene_comprobante(self, obj):
        return hasattr(obj, 'comprobante')


class PagoEnLineaListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para listar pagos (sin nested data).
    Optimizado para listados con muchos registros.
    """
    paciente_nombre = serializers.SerializerMethodField()
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    metodo_pago_display = serializers.CharField(source='get_metodo_pago_display', read_only=True)
    tiene_comprobante = serializers.SerializerMethodField()
    
    class Meta:
        model = PagoEnLinea
        fields = [
            'id',
            'codigo_pago',
            'origen_tipo',
            'monto',
            'moneda',
            'estado',
            'estado_display',
            'metodo_pago',
            'metodo_pago_display',
            'fecha_creacion',
            'paciente_nombre',
            'tiene_comprobante',
            'descripcion'
        ]
        read_only_fields = fields
    
    def get_paciente_nombre(self, obj):
        """Obtiene el nombre del paciente según el origen."""
        try:
            if obj.origen_tipo in ['plan_completo', 'items_individuales']:
                if obj.plan_tratamiento and obj.plan_tratamiento.codpaciente:
                    return obj.plan_tratamiento.codpaciente.codusuario.nombre
            elif obj.origen_tipo == 'consulta':
                if obj.consulta and obj.consulta.codpaciente:
                    return obj.consulta.codpaciente.codusuario.nombre
        except Exception:
            pass
        return None
    
    def get_tiene_comprobante(self, obj):
        return hasattr(obj, 'comprobante')


# ==================== Serializers de Creación ====================

class CrearPagoPlanSerializer(serializers.Serializer):
    """
    Serializer para crear un pago de plan completo o items individuales.
    Incluye validaciones complejas de monto, saldo y distribución.
    """
    # Campos requeridos
    plan_tratamiento_id = serializers.IntegerField(required=True)
    monto = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2,
        required=True,
        min_value=Decimal('0.01')
    )
    metodo_pago = serializers.ChoiceField(
        choices=PagoEnLinea.METODO_CHOICES,
        required=True
    )
    
    # Campos opcionales
    items_seleccionados = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="IDs de items específicos a pagar (None = plan completo)"
    )
    descripcion = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    
    # Campos de auditoría (opcionales, llenados automáticamente)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True)
    
    def validate_plan_tratamiento_id(self, value):
        """Valida que el plan exista y pertenezca a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'tenant', None)
        
        try:
            plan = Plandetratamiento.objects.get(id=value, empresa=empresa)
        except Plandetratamiento.DoesNotExist:
            raise serializers.ValidationError(
                "Plan de tratamiento no encontrado o no pertenece a esta empresa"
            )
        
        # Validar que el plan puede recibir pagos
        puede_pagar, razon = plan.puede_pagar_completo()
        if not puede_pagar:
            raise serializers.ValidationError(razon)
        
        # Guardar para uso posterior
        self.context['plan_tratamiento'] = plan
        
        return value
    
    def validate_monto(self, value):
        """Valida que el monto sea positivo."""
        if value <= Decimal('0'):
            raise serializers.ValidationError("El monto debe ser mayor a 0")
        return value
    
    def validate_items_seleccionados(self, value):
        """Valida que los items existan y pertenezcan al plan."""
        if not value:
            return value
        
        plan = self.context.get('plan_tratamiento')
        if not plan:
            return value
        
        # Verificar que todos los items existan y pertenezcan al plan
        items = Itemplandetratamiento.objects.filter(
            id__in=value,
            idplantratamiento=plan
        ).exclude(estado_item='Cancelado')
        
        if items.count() != len(value):
            raise serializers.ValidationError(
                "Algunos items no existen, no pertenecen al plan o están cancelados"
            )
        
        # Verificar que los items pueden recibir pagos
        for item in items:
            puede_pagar, razon = item.puede_pagarse()
            if not puede_pagar:
                raise serializers.ValidationError(
                    f"Item {item.id} ({item.idservicio.nombre}): {razon}"
                )
        
        return value
    
    def validate(self, attrs):
        """Validación a nivel de objeto (relaciones entre campos)."""
        plan = self.context.get('plan_tratamiento')
        monto = attrs.get('monto')
        items_seleccionados = attrs.get('items_seleccionados')
        
        # Determinar origen
        if items_seleccionados:
            origen_tipo = 'items_individuales'
        else:
            origen_tipo = 'plan_completo'
        
        attrs['origen_tipo'] = origen_tipo
        
        # Validar monto vs saldo
        if origen_tipo == 'plan_completo':
            # Validar contra saldo total del plan
            es_valido, mensaje = CalculadorPagos.validar_monto_pago(plan, monto)
            if not es_valido:
                raise serializers.ValidationError({'monto': mensaje})
        else:
            # Validar contra saldo de items seleccionados
            items = Itemplandetratamiento.objects.filter(
                id__in=items_seleccionados,
                idplantratamiento=plan
            )
            
            saldo_total_items = sum(
                item.calcular_saldo_pendiente() for item in items
            )
            
            if monto > saldo_total_items:
                raise serializers.ValidationError({
                    'monto': f"El monto (${monto}) excede el saldo de los items seleccionados (${saldo_total_items})"
                })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """
        Crea el pago y sus detalles por item.
        Calcula automáticamente saldos y distribución.
        """
        request = self.context.get('request')
        empresa = getattr(request, 'tenant', None)
        usuario = getattr(request.user, 'usuario', None) if hasattr(request, 'user') else None
        
        plan = self.context.get('plan_tratamiento')
        monto = validated_data['monto']
        origen_tipo = validated_data['origen_tipo']
        items_seleccionados = validated_data.get('items_seleccionados')
        
        # Calcular saldos
        saldo_anterior = plan.calcular_saldo_pendiente()
        saldo_nuevo = saldo_anterior - monto
        
        # Crear el pago
        pago = PagoEnLinea.objects.create(
            empresa=empresa,
            usuario=usuario,
            plan_tratamiento=plan,
            origen_tipo=origen_tipo,
            monto=monto,
            moneda='BOB',  # Default
            monto_original=plan.montototal,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=max(saldo_nuevo, Decimal('0')),
            estado='pendiente',
            metodo_pago=validated_data['metodo_pago'],
            descripcion=validated_data.get('descripcion', ''),
            ip_address=validated_data.get('ip_address'),
            user_agent=validated_data.get('user_agent'),
            numero_intentos=0
        )
        
        # Calcular distribución del pago entre items
        distribucion = CalculadorPagos.calcular_distribucion_pago(
            plan, 
            monto, 
            items_seleccionados
        )
        
        # Crear detalles por item
        for detalle_dist in distribucion['distribucion']:
            item = Itemplandetratamiento.objects.get(id=detalle_dist['item_id'])
            
            monto_pagado_anterior = item.calcular_monto_pagado()
            monto_pagado_ahora = Decimal(str(detalle_dist['monto_a_pagar']))
            monto_pagado_total = monto_pagado_anterior + monto_pagado_ahora
            saldo_restante = Decimal(str(detalle_dist['saldo_resultante']))
            
            DetallePagoItem.objects.create(
                pago=pago,
                item_plan=item,
                monto_item_total=item.costofinal,
                monto_pagado_anterior=monto_pagado_anterior,
                monto_pagado_ahora=monto_pagado_ahora,
                monto_pagado_total=monto_pagado_total,
                saldo_restante=saldo_restante,
                item_completamente_pagado=(saldo_restante <= Decimal('0'))
            )
        
        return pago


class CrearPagoConsultaSerializer(serializers.Serializer):
    """
    Serializer para crear un pago de consulta (prepago/copago).
    """
    # Campos requeridos
    consulta_id = serializers.IntegerField(required=True)
    monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=Decimal('0.01')
    )
    metodo_pago = serializers.ChoiceField(
        choices=PagoEnLinea.METODO_CHOICES,
        required=True
    )
    tipo_pago_consulta = serializers.ChoiceField(
        choices=PagoEnLinea.TIPO_PAGO_CONSULTA_CHOICES,
        required=False,
        allow_null=True
    )
    
    # Campos opcionales
    descripcion = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True
    )
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True)
    
    def validate_consulta_id(self, value):
        """Valida que la consulta exista y pertenezca a la empresa."""
        request = self.context.get('request')
        empresa = getattr(request, 'tenant', None)
        
        try:
            consulta = Consulta.objects.get(id=value, empresa=empresa)
        except Consulta.DoesNotExist:
            raise serializers.ValidationError(
                "Consulta no encontrada o no pertenece a esta empresa"
            )
        
        # Validar que la consulta puede recibir pagos
        puede_pagar, razon = consulta.puede_pagarse()
        if not puede_pagar:
            raise serializers.ValidationError(razon)
        
        # Guardar para uso posterior
        self.context['consulta'] = consulta
        
        return value
    
    def validate(self, attrs):
        """Validación a nivel de objeto."""
        consulta = self.context.get('consulta')
        monto = attrs.get('monto')
        
        # Validar monto vs saldo de consulta
        es_valido, mensaje = CalculadorPagos.validar_pago_consulta(consulta, monto)
        if not es_valido:
            raise serializers.ValidationError({'monto': mensaje})
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Crea el pago de consulta."""
        request = self.context.get('request')
        empresa = getattr(request, 'tenant', None)
        usuario = getattr(request.user, 'usuario', None) if hasattr(request, 'user') else None
        
        consulta = self.context.get('consulta')
        monto = validated_data['monto']
        
        # Calcular saldos
        costo_total = consulta.calcular_costo_prepago() + consulta.calcular_copago()
        saldo_anterior = consulta.calcular_saldo_pendiente()
        saldo_nuevo = saldo_anterior - monto
        
        # Crear el pago
        pago = PagoEnLinea.objects.create(
            empresa=empresa,
            usuario=usuario,
            consulta=consulta,
            origen_tipo='consulta',
            tipo_pago_consulta=validated_data.get('tipo_pago_consulta'),
            monto=monto,
            moneda='BOB',
            monto_original=costo_total,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=max(saldo_nuevo, Decimal('0')),
            estado='pendiente',
            metodo_pago=validated_data['metodo_pago'],
            descripcion=validated_data.get('descripcion', ''),
            ip_address=validated_data.get('ip_address'),
            user_agent=validated_data.get('user_agent'),
            numero_intentos=0
        )
        
        return pago


# ==================== Serializers de Actualización ====================

class ActualizarEstadoPagoSerializer(serializers.Serializer):
    """
    Serializer para actualizar el estado de un pago.
    Usado internamente por webhook de Stripe o aprobación manual.
    """
    estado = serializers.ChoiceField(
        choices=['aprobado', 'rechazado', 'cancelado', 'reembolsado'],
        required=True
    )
    motivo_rechazo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Requerido si estado=rechazado"
    )
    stripe_charge_id = serializers.CharField(
        required=False,
        allow_blank=True
    )
    stripe_metadata = serializers.JSONField(required=False)
    
    def validate(self, attrs):
        """Validaciones a nivel de objeto."""
        estado = attrs.get('estado')
        motivo_rechazo = attrs.get('motivo_rechazo')
        
        # Si el estado es rechazado, motivo es requerido
        if estado == 'rechazado' and not motivo_rechazo:
            raise serializers.ValidationError({
                'motivo_rechazo': 'El motivo de rechazo es requerido'
            })
        
        return attrs
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Actualiza el estado del pago."""
        nuevo_estado = validated_data['estado']
        
        # Actualizar campos según el nuevo estado
        instance.estado = nuevo_estado
        
        if nuevo_estado == 'aprobado':
            instance.fecha_aprobacion = timezone.now()
            instance.fecha_procesamiento = timezone.now()
            if validated_data.get('stripe_charge_id'):
                instance.stripe_charge_id = validated_data['stripe_charge_id']
        
        elif nuevo_estado == 'rechazado':
            instance.fecha_procesamiento = timezone.now()
            instance.motivo_rechazo = validated_data.get('motivo_rechazo', '')
        
        if validated_data.get('stripe_metadata'):
            instance.stripe_metadata = validated_data['stripe_metadata']
        
        instance.save()
        
        # Si fue aprobado, bloquear items pagados
        if nuevo_estado == 'aprobado' and instance.plan_tratamiento:
            instance.plan_tratamiento.bloquear_items_pagados()
        
        return instance


# ==================== Serializers de Resumen ====================

class ResumenFinancieroPlanSerializer(serializers.Serializer):
    """
    Serializer para mostrar resumen financiero de un plan.
    """
    plan_id = serializers.IntegerField()
    total_plan = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_pagado = serializers.DecimalField(max_digits=10, decimal_places=2)
    saldo_pendiente = serializers.DecimalField(max_digits=10, decimal_places=2)
    porcentaje_pagado = serializers.DecimalField(max_digits=5, decimal_places=2)
    items_totales = serializers.IntegerField()
    items_pagados = serializers.IntegerField()
    items_pendientes = serializers.IntegerField()
    esta_pagado_completo = serializers.BooleanField()
    
    # Lista de pagos
    historial_pagos = serializers.JSONField()
