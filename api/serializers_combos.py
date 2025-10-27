"""
Serializers para el módulo de Combos/Paquetes de Servicios.
Permite la gestión completa de combos con precios especiales.
"""
from rest_framework import serializers
from decimal import Decimal
from .models import ComboServicio, ComboServicioDetalle, Servicio


class ComboServicioDetalleSerializer(serializers.ModelSerializer):
    """
    Serializer para detalles de combo (servicios incluidos).
    Muestra información del servicio y calcula subtotales.
    """
    servicio_nombre = serializers.CharField(source='servicio.nombre', read_only=True)
    servicio_precio = serializers.DecimalField(
        source='servicio.costobase',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    servicio_duracion = serializers.IntegerField(source='servicio.duracion', read_only=True)
    subtotal = serializers.SerializerMethodField()
    
    class Meta:
        model = ComboServicioDetalle
        fields = [
            'id',
            'servicio',
            'servicio_nombre',
            'servicio_precio',
            'servicio_duracion',
            'cantidad',
            'orden',
            'subtotal'
        ]
        read_only_fields = ['id']
    
    def get_subtotal(self, obj):
        """Calcula el subtotal de este detalle."""
        return obj.calcular_subtotal()
    
    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva."""
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor a cero."
            )
        return value
    
    def validate_servicio(self, value):
        """Valida que el servicio esté activo y pertenezca al tenant."""
        if not value.activo:
            raise serializers.ValidationError(
                f"El servicio '{value.nombre}' no está activo."
            )
        
        # Validar tenant en el contexto de la request
        request = self.context.get('request')
        if request and hasattr(request, 'tenant') and request.tenant:
            if value.empresa != request.tenant:
                raise serializers.ValidationError(
                    "El servicio no pertenece a su empresa."
                )
        
        return value


class ComboServicioDetalleCreateSerializer(serializers.ModelSerializer):
    """Serializer simplificado para crear detalles de combo."""
    
    class Meta:
        model = ComboServicioDetalle
        fields = ['servicio', 'cantidad', 'orden']
    
    def validate_cantidad(self, value):
        """Valida que la cantidad sea positiva."""
        if value <= 0:
            raise serializers.ValidationError(
                "La cantidad debe ser mayor a cero."
            )
        return value


class ComboServicioSerializer(serializers.ModelSerializer):
    """
    Serializer completo para gestión de combos de servicios.
    Incluye detalles anidados, cálculos de precios y validaciones.
    """
    detalles = ComboServicioDetalleSerializer(many=True, read_only=True)
    precio_total_servicios = serializers.SerializerMethodField()
    precio_final = serializers.SerializerMethodField()
    ahorro = serializers.SerializerMethodField()
    duracion_total = serializers.SerializerMethodField()
    cantidad_servicios = serializers.SerializerMethodField()
    
    class Meta:
        model = ComboServicio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'tipo_precio',
            'valor_precio',
            'activo',
            'fecha_creacion',
            'fecha_modificacion',
            'empresa',
            'detalles',
            'precio_total_servicios',
            'precio_final',
            'ahorro',
            'duracion_total',
            'cantidad_servicios'
        ]
        read_only_fields = ['id', 'empresa', 'fecha_creacion', 'fecha_modificacion']
    
    def get_precio_total_servicios(self, obj):
        """Suma de precios de todos los servicios incluidos."""
        return obj.calcular_precio_total_servicios()
    
    def get_precio_final(self, obj):
        """Precio final del combo según la regla aplicada."""
        try:
            return obj.calcular_precio_final()
        except ValueError as e:
            return None
    
    def get_ahorro(self, obj):
        """Calcula el ahorro comparado con comprar servicios individualmente."""
        precio_servicios = obj.calcular_precio_total_servicios()
        try:
            precio_final = obj.calcular_precio_final()
            ahorro = precio_servicios - precio_final
            return ahorro if ahorro > 0 else Decimal('0.00')
        except ValueError:
            return Decimal('0.00')
    
    def get_duracion_total(self, obj):
        """Duración total estimada del combo en minutos."""
        return obj.calcular_duracion_total()
    
    def get_cantidad_servicios(self, obj):
        """Cantidad total de servicios incluidos en el combo."""
        return obj.detalles.count()
    
    def validate_valor_precio(self, value):
        """Valida que el valor de precio sea válido según el tipo."""
        if value < 0:
            raise serializers.ValidationError(
                "El valor del precio no puede ser negativo."
            )
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto."""
        # Validar que el porcentaje no sea mayor a 100
        if data.get('tipo_precio') == 'PORCENTAJE':
            if data.get('valor_precio', 0) > 100:
                raise serializers.ValidationError({
                    'valor_precio': 'El porcentaje de descuento no puede ser mayor a 100%.'
                })
        
        return data


class ComboServicioCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear y actualizar combos con sus detalles.
    Permite crear/actualizar combo y detalles en una sola operación.
    """
    detalles = ComboServicioDetalleCreateSerializer(many=True)
    
    class Meta:
        model = ComboServicio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'tipo_precio',
            'valor_precio',
            'activo',
            'detalles'
        ]
        read_only_fields = ['id']
    
    def validate_detalles(self, value):
        """Valida que el combo tenga al menos un servicio."""
        if not value:
            raise serializers.ValidationError(
                "El combo debe incluir al menos un servicio."
            )
        
        # Validar que no haya servicios duplicados
        servicios_ids = [detalle['servicio'].id for detalle in value]
        if len(servicios_ids) != len(set(servicios_ids)):
            raise serializers.ValidationError(
                "No puede incluir el mismo servicio más de una vez en el combo."
            )
        
        return value
    
    def validate(self, data):
        """Validaciones a nivel de objeto."""
        # Validar porcentaje
        if data.get('tipo_precio') == 'PORCENTAJE':
            if data.get('valor_precio', 0) > 100:
                raise serializers.ValidationError({
                    'valor_precio': 'El porcentaje de descuento no puede ser mayor a 100%.'
                })
        
        # Validar que el valor de precio sea positivo
        if data.get('valor_precio', 0) < 0:
            raise serializers.ValidationError({
                'valor_precio': 'El valor del precio no puede ser negativo.'
            })
        
        return data
    
    def create(self, validated_data):
        """Crea el combo y sus detalles en una transacción."""
        detalles_data = validated_data.pop('detalles')
        
        # Asignar empresa del tenant
        request = self.context.get('request')
        if request and hasattr(request, 'tenant') and request.tenant:
            validated_data['empresa'] = request.tenant
        
        # Crear combo
        combo = ComboServicio.objects.create(**validated_data)
        
        # Crear detalles
        for detalle_data in detalles_data:
            ComboServicioDetalle.objects.create(
                combo=combo,
                **detalle_data
            )
        
        # Validar precio final no negativo
        try:
            precio_final = combo.calcular_precio_final()
            if precio_final < 0:
                combo.delete()
                raise serializers.ValidationError({
                    'precio_final': 'El precio final del combo no puede ser negativo. Ajuste el tipo o valor de precio.'
                })
        except ValueError as e:
            combo.delete()
            raise serializers.ValidationError({
                'precio_final': str(e)
            })
        
        return combo
    
    def update(self, instance, validated_data):
        """Actualiza el combo y sus detalles."""
        detalles_data = validated_data.pop('detalles', None)
        
        # Actualizar campos del combo
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Si se proporcionan detalles, reemplazar los existentes
        if detalles_data is not None:
            # Eliminar detalles anteriores
            instance.detalles.all().delete()
            
            # Crear nuevos detalles
            for detalle_data in detalles_data:
                ComboServicioDetalle.objects.create(
                    combo=instance,
                    **detalle_data
                )
        
        # Validar precio final no negativo
        try:
            precio_final = instance.calcular_precio_final()
            if precio_final < 0:
                raise serializers.ValidationError({
                    'precio_final': 'El precio final del combo no puede ser negativo. Ajuste el tipo o valor de precio.'
                })
        except ValueError as e:
            raise serializers.ValidationError({
                'precio_final': str(e)
            })
        
        return instance


class ComboServicioListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listado de combos."""
    precio_final = serializers.SerializerMethodField()
    cantidad_servicios = serializers.SerializerMethodField()
    
    class Meta:
        model = ComboServicio
        fields = [
            'id',
            'nombre',
            'descripcion',
            'tipo_precio',
            'precio_final',
            'cantidad_servicios',
            'activo',
            'fecha_creacion'
        ]
    
    def get_precio_final(self, obj):
        """Precio final del combo."""
        try:
            return obj.calcular_precio_final()
        except ValueError:
            return None
    
    def get_cantidad_servicios(self, obj):
        """Cantidad de servicios en el combo."""
        return obj.detalles.count()


class ComboServicioPrevisualizacionSerializer(serializers.Serializer):
    """
    Serializer para previsualizar el precio de un combo antes de guardarlo.
    No crea registros en la base de datos.
    """
    tipo_precio = serializers.ChoiceField(choices=ComboServicio.TIPO_PRECIO_CHOICES)
    valor_precio = serializers.DecimalField(max_digits=10, decimal_places=2)
    servicios = serializers.ListField(
        child=serializers.DictField(child=serializers.IntegerField()),
        help_text="Lista de {servicio_id: cantidad}"
    )
    
    def validate_servicios(self, value):
        """Valida que los servicios existan y estén activos."""
        if not value:
            raise serializers.ValidationError("Debe incluir al menos un servicio.")
        
        for item in value:
            if 'servicio_id' not in item or 'cantidad' not in item:
                raise serializers.ValidationError(
                    "Cada servicio debe tener 'servicio_id' y 'cantidad'."
                )
            
            if item['cantidad'] <= 0:
                raise serializers.ValidationError(
                    "La cantidad debe ser mayor a cero."
                )
        
        return value
    
    def validate_valor_precio(self, value):
        """Valida que el valor sea positivo."""
        if value < 0:
            raise serializers.ValidationError(
                "El valor del precio no puede ser negativo."
            )
        return value
    
    def validate(self, data):
        """Validaciones cruzadas."""
        if data['tipo_precio'] == 'PORCENTAJE' and data['valor_precio'] > 100:
            raise serializers.ValidationError({
                'valor_precio': 'El porcentaje no puede ser mayor a 100%.'
            })
        
        # Obtener tenant del contexto
        request = self.context.get('request')
        tenant = getattr(request, 'tenant', None) if request else None
        
        # Calcular precios
        precio_total_servicios = Decimal('0.00')
        for item in data['servicios']:
            try:
                servicio = Servicio.objects.get(
                    id=item['servicio_id'],
                    empresa=tenant,
                    activo=True
                )
                precio_total_servicios += servicio.costobase * item['cantidad']
            except Servicio.DoesNotExist:
                raise serializers.ValidationError({
                    'servicios': f"Servicio con ID {item['servicio_id']} no encontrado o inactivo."
                })
        
        # Calcular precio final según tipo
        if data['tipo_precio'] == 'PORCENTAJE':
            descuento = precio_total_servicios * (data['valor_precio'] / Decimal('100'))
            precio_final = precio_total_servicios - descuento
        elif data['tipo_precio'] in ['MONTO_FIJO', 'PROMOCION']:
            precio_final = data['valor_precio']
        else:
            precio_final = precio_total_servicios
        
        # Validar precio final no negativo
        if precio_final < 0:
            raise serializers.ValidationError({
                'precio_final': 'El precio final no puede ser negativo. Ajuste los valores.'
            })
        
        # Agregar información calculada
        data['precio_total_servicios'] = precio_total_servicios
        data['precio_final'] = precio_final
        data['ahorro'] = precio_total_servicios - precio_final if precio_final < precio_total_servicios else Decimal('0.00')
        
        return data
