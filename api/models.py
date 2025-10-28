from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
import uuid


# +++ NUEVO MODELO EMPRESA +++
class Empresa(models.Model):
    """Representa a un cliente (una clínica dental) en el sistema SaaS."""
    nombre = models.CharField(max_length=255, unique=True)
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        null=True,  # Temporalmente nullable para la migración
        blank=True,
        help_text="Subdominio para acceso multi-tenant (ej: clinica1, clinica2)"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(
        default=True,
        help_text="Indica si la empresa está activa en el sistema"
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID del cliente en Stripe"
    )
    stripe_subscription_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID de la suscripción en Stripe"
    )

    class Meta:
        db_table = 'api_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.subdomain})"


class Usuario(models.Model):
    codigo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    apellido = models.CharField(max_length=255)
    correoelectronico = models.CharField(unique=True, max_length=255)
    sexo = models.CharField(max_length=50, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    idtipousuario = models.ForeignKey('Tipodeusuario', models.DO_NOTHING, db_column='idtipousuario')
    recibir_notificaciones = models.BooleanField(default=True)
    notificaciones_email = models.BooleanField(default=True)
    notificaciones_push = models.BooleanField(default=False)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True)

    class Meta:
        db_table = 'usuario'


class Paciente(models.Model):
    codusuario = models.OneToOneField(Usuario, models.DO_NOTHING, db_column='codusuario', primary_key=True)
    carnetidentidad = models.CharField(unique=True, max_length=50, blank=True, null=True)
    fechanacimiento = models.DateField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pacientes', null=True, blank=True)

    class Meta:
        db_table = 'paciente'


class Odontologo(models.Model):
    codusuario = models.OneToOneField(Usuario, models.DO_NOTHING, db_column='codusuario', primary_key=True)
    especialidad = models.CharField(max_length=255, blank=True, null=True)
    experienciaprofesional = models.TextField(blank=True, null=True)
    nromatricula = models.CharField(unique=True, max_length=100, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='odontologos', null=True, blank=True)

    class Meta:
        db_table = 'odontologo'


class Recepcionista(models.Model):
    codusuario = models.OneToOneField(Usuario, models.DO_NOTHING, db_column='codusuario', primary_key=True)
    habilidadessoftware = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='recepcionistas', null=True, blank=True)

    class Meta:
        db_table = 'recepcionista'


class Consulta(models.Model):
    fecha = models.DateField()
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo', blank=True, null=True)
    codrecepcionista = models.ForeignKey(Recepcionista, models.DO_NOTHING, db_column='codrecepcionista', blank=True, null=True)
    idhorario = models.ForeignKey('Horario', models.DO_NOTHING, db_column='idhorario')
    idtipoconsulta = models.ForeignKey('Tipodeconsulta', models.DO_NOTHING, db_column='idtipoconsulta')
    idestadoconsulta = models.ForeignKey('Estadodeconsulta', models.DO_NOTHING, db_column='idestadoconsulta')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='cosultas', null=True, blank=True)

    class Meta:
        db_table = 'consulta'


class Tipodeconsulta(models.Model):
    nombreconsulta = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tipos_consulta', null=True, blank=True)

    class Meta:
        db_table = 'tipodeconsulta'


class Historialclinico(models.Model):
    # Antes era OneToOne; ahora es FK para permitir múltiples episodios por paciente
    pacientecodigo = models.ForeignKey(
        'Paciente',
        on_delete=models.DO_NOTHING,
        db_column='pacientecodigo',
        related_name='historias'
    )

    # Campos clínicos existentes
    alergias = models.TextField(blank=True, null=True)
    enfermedades = models.TextField(blank=True, null=True)
    motivoconsulta = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)

    # NUEVOS (ya creados en la BD con tu script)
    episodio = models.PositiveIntegerField(default=1)  # 1..n por paciente
    fecha = models.DateTimeField(auto_now_add=True, null=False)  # timestamptz DEFAULT now()
    updated_at = models.DateTimeField(auto_now=True)  # timestamptz DEFAULT now()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='historiales', null=True, blank=True)

    class Meta:
        db_table = 'historialclinico'
        constraints = [
            models.UniqueConstraint(
                fields=['pacientecodigo', 'episodio'],
                name='uniq_historial_paciente_episodio'
            )
        ]
        ordering = ['-fecha', '-episodio']

    def __str__(self):
        return f'HCE paciente={self.pacientecodigo_id} episodio={self.episodio}'


class Servicio(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    costobase = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.IntegerField(
        default=30,
        help_text="Duración estimada del servicio en minutos"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el servicio está disponible para ser consultado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_modificacion = models.DateTimeField(auto_now=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='servicios', null=True, blank=True)

    class Meta:
        db_table = 'servicio'
        ordering = ['nombre']
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f"{self.nombre} - ${self.costobase}"


class ComboServicio(models.Model):
    """
    Representa un paquete o combo de servicios dentales con precio especial.
    
    Tipos de regla de precio:
    - PORCENTAJE: Descuento sobre la suma de servicios individuales
    - MONTO_FIJO: Precio fijo del combo (independiente de servicios)
    - PROMOCION: Precio promocional especial
    """
    TIPO_PRECIO_CHOICES = [
        ('PORCENTAJE', 'Descuento Porcentual'),
        ('MONTO_FIJO', 'Monto Fijo'),
        ('PROMOCION', 'Precio Promocional'),
    ]
    
    nombre = models.CharField(
        max_length=255,
        help_text="Nombre del combo (ej: 'Paquete Blanqueamiento Completo')"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        help_text="Descripción detallada del combo"
    )
    tipo_precio = models.CharField(
        max_length=20,
        choices=TIPO_PRECIO_CHOICES,
        default='PORCENTAJE',
        help_text="Tipo de regla de precio aplicada al combo"
    )
    valor_precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor según tipo_precio: % de descuento, monto fijo, o precio promocional"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el combo está disponible para su uso"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='combos_servicios',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'combo_servicio'
        ordering = ['-fecha_creacion']
        verbose_name = 'Combo de Servicios'
        verbose_name_plural = 'Combos de Servicios'
        constraints = [
            models.CheckConstraint(
                check=models.Q(valor_precio__gte=0),
                name='combo_valor_precio_no_negativo'
            )
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.empresa.nombre if self.empresa else 'Sin empresa'})"
    
    def calcular_precio_total_servicios(self):
        """Calcula la suma de los precios de todos los servicios incluidos."""
        from decimal import Decimal
        total = Decimal('0.00')
        for detalle in self.detalles.all():
            total += detalle.servicio.costobase * detalle.cantidad
        return total
    
    def calcular_precio_final(self):
        """
        Calcula el precio final del combo según el tipo de precio.
        
        Returns:
            Decimal: Precio final del combo
        """
        from decimal import Decimal
        
        precio_servicios = self.calcular_precio_total_servicios()
        
        if self.tipo_precio == 'PORCENTAJE':
            # Aplica descuento porcentual sobre el total de servicios
            descuento = precio_servicios * (self.valor_precio / Decimal('100'))
            precio_final = precio_servicios - descuento
        elif self.tipo_precio == 'MONTO_FIJO':
            # Precio fijo del combo
            precio_final = self.valor_precio
        elif self.tipo_precio == 'PROMOCION':
            # Precio promocional especial
            precio_final = self.valor_precio
        else:
            precio_final = precio_servicios
        
        # Validar que el precio final no sea negativo
        if precio_final < 0:
            raise ValueError("El precio final del combo no puede ser negativo")
        
        return precio_final
    
    def calcular_duracion_total(self):
        """Calcula la duración total estimada del combo en minutos."""
        duracion_total = 0
        for detalle in self.detalles.all():
            duracion_total += detalle.servicio.duracion * detalle.cantidad
        return duracion_total


class ComboServicioDetalle(models.Model):
    """
    Representa un servicio individual dentro de un combo.
    Define qué servicios están incluidos y en qué cantidad.
    """
    combo = models.ForeignKey(
        ComboServicio,
        on_delete=models.CASCADE,
        related_name='detalles',
        help_text="Combo al que pertenece este detalle"
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.PROTECT,
        related_name='combos_detalle',
        help_text="Servicio incluido en el combo"
    )
    cantidad = models.PositiveIntegerField(
        default=1,
        help_text="Cantidad de veces que se incluye este servicio en el combo"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de presentación del servicio en el combo"
    )
    
    class Meta:
        db_table = 'combo_servicio_detalle'
        ordering = ['orden', 'id']
        verbose_name = 'Detalle de Combo'
        verbose_name_plural = 'Detalles de Combos'
        constraints = [
            models.UniqueConstraint(
                fields=['combo', 'servicio'],
                name='unique_combo_servicio'
            ),
            models.CheckConstraint(
                check=models.Q(cantidad__gt=0),
                name='combo_detalle_cantidad_positiva'
            )
        ]
    
    def __str__(self):
        return f"{self.servicio.nombre} x{self.cantidad} en {self.combo.nombre}"
    
    def calcular_subtotal(self):
        """Calcula el subtotal de este detalle (precio del servicio * cantidad)."""
        return self.servicio.costobase * self.cantidad


class Insumo(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    stock = models.IntegerField(blank=True, null=True)
    unidaddemedida = models.CharField(max_length=50, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='insumos', null=True, blank=True)

    class Meta:
        db_table = 'insumo'


class Medicamento(models.Model):
    nombre = models.CharField(max_length=255)
    cantidadmiligramos = models.CharField(max_length=100, blank=True, null=True)
    presentacion = models.CharField(max_length=255, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='medicamentos', null=True, blank=True)

    class Meta:
        db_table = 'medicamento'


class Recetamedica(models.Model):
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo')
    fechaemision = models.DateField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='recetas', null=True, blank=True)

    class Meta:
        db_table = 'recetamedica'


class Imtemreceta(models.Model):
    idreceta = models.ForeignKey(Recetamedica, models.DO_NOTHING, db_column='idreceta')
    idmedicamento = models.ForeignKey(Medicamento, models.DO_NOTHING, db_column='idmedicamento')
    posologia = models.TextField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='itemsReceta', null=True, blank=True)

    class Meta:
        db_table = 'itemreceta'


class Plandetratamiento(models.Model):
    """
    Plan de tratamiento / Presupuesto dental.
    
    Un plan de tratamiento es un presupuesto que un odontólogo genera para un paciente,
    especificando los servicios/tratamientos a realizar y sus costos.
    """
    # Estados del plan (SP3-T001: Workflow borrador -> aprobado)
    ESTADO_PLAN_BORRADOR = 'Borrador'
    ESTADO_PLAN_APROBADO = 'Aprobado'
    ESTADO_PLAN_CANCELADO = 'Cancelado'
    
    ESTADOS_PLAN = [
        (ESTADO_PLAN_BORRADOR, 'Borrador (Editable)'),
        (ESTADO_PLAN_APROBADO, 'Aprobado (Inmutable)'),
        (ESTADO_PLAN_CANCELADO, 'Cancelado'),
    ]
    
    # Estados de aceptación (SP3-T003: Aceptación por paciente)
    ESTADO_PENDIENTE = 'Pendiente'
    ESTADO_ACEPTADO = 'Aceptado'
    ESTADO_RECHAZADO = 'Rechazado'
    ESTADO_CADUCADO = 'Caducado'
    ESTADO_PARCIAL = 'Parcial'  # Solo algunos items aceptados
    
    ESTADOS_ACEPTACION = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ACEPTADO, 'Aceptado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
        (ESTADO_CADUCADO, 'Caducado'),
        (ESTADO_PARCIAL, 'Aceptación Parcial'),
    ]
    
    # Tipos de aceptación
    TIPO_TOTAL = 'Total'
    TIPO_PARCIAL = 'Parcial'
    
    TIPOS_ACEPTACION = [
        (TIPO_TOTAL, 'Aceptación Total'),
        (TIPO_PARCIAL, 'Aceptación Parcial'),
    ]
    
    # Campos originales
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo')
    idestado = models.ForeignKey('Estado', models.DO_NOTHING, db_column='idestado')
    fechaplan = models.DateField()
    descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montototal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='planesTratamientos', null=True, blank=True)
    
    # SP3-T001: Campos para gestión de plan de tratamiento
    estado_plan = models.CharField(
        max_length=20,
        choices=ESTADOS_PLAN,
        default=ESTADO_PLAN_BORRADOR,
        help_text="Estado del plan: Borrador (editable) o Aprobado (inmutable)."
    )
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que el plan fue aprobado por el odontólogo."
    )
    usuario_aprueba = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planes_aprobados',
        help_text="Usuario (odontólogo) que aprobó el plan."
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Versión del plan. Se incrementa con cada aprobación de cambios mayores."
    )
    notas_plan = models.TextField(
        blank=True,
        null=True,
        help_text="Notas generales del plan de tratamiento (diagnóstico, observaciones, etc.)."
    )
    subtotal_calculado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Subtotal calculado automáticamente sumando items activos."
    )
    progreso_general = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Progreso general del plan (promedio de progreso de ítems activos). SP3-T008"
    )
    
    # SP3-T003: Campos para aceptación de presupuestos
    fecha_vigencia = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha hasta la cual el presupuesto es válido. Después de esta fecha, caduca automáticamente."
    )
    fecha_aceptacion = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Fecha y hora en que el paciente aceptó el presupuesto."
    )
    usuario_acepta = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_aceptados',
        help_text="Usuario (paciente) que aceptó el presupuesto."
    )
    estado_aceptacion = models.CharField(
        max_length=20,
        choices=ESTADOS_ACEPTACION,
        default=ESTADO_PENDIENTE,
        help_text="Estado de aceptación del presupuesto por parte del paciente."
    )
    aceptacion_tipo = models.CharField(
        max_length=20,
        choices=TIPOS_ACEPTACION,
        null=True,
        blank=True,
        help_text="Tipo de aceptación: Total (todos los ítems) o Parcial (solo algunos ítems)."
    )
    es_editable = models.BooleanField(
        default=True,
        help_text="Indica si el presupuesto puede ser editado. Se bloquea al ser aceptado."
    )
    firma_digital = models.TextField(
        null=True,
        blank=True,
        help_text="Firma digital del paciente en formato JSON. Incluye timestamp, IP, user agent, etc."
    )
    
    class Meta:
        db_table = 'plandetratamiento'
        verbose_name = 'Plan de Tratamiento'
        verbose_name_plural = 'Planes de Tratamiento'
        ordering = ['-fechaplan']
    
    def __str__(self):
        return f"Plan #{self.id} - {self.codpaciente.codusuario.nombre} ({self.estado_plan})"
    
    # SP3-T001: Métodos para gestión de plan
    def es_borrador(self):
        """Verifica si el plan está en estado borrador (editable)."""
        return self.estado_plan == self.ESTADO_PLAN_BORRADOR
    
    def es_aprobado(self):
        """Verifica si el plan fue aprobado (inmutable)."""
        return self.estado_plan == self.ESTADO_PLAN_APROBADO
    
    def puede_editarse(self):
        """
        Verifica si el plan puede ser editado.
        Solo planes en borrador y no aceptados pueden editarse.
        """
        return (
            self.es_borrador() and 
            self.es_editable and 
            self.estado_aceptacion not in [self.ESTADO_ACEPTADO, self.ESTADO_RECHAZADO]
        )
    
    def aprobar_plan(self, usuario):
        """
        Aprueba el plan de tratamiento, bloqueando su edición.
        Crea una versión inmutable del plan.
        """
        if not self.es_borrador():
            raise ValueError("Solo se pueden aprobar planes en estado borrador.")
        
        self.estado_plan = self.ESTADO_PLAN_APROBADO
        self.fecha_aprobacion = timezone.now()
        self.usuario_aprueba = usuario
        self.es_editable = False
        self.save(update_fields=['estado_plan', 'fecha_aprobacion', 'usuario_aprueba', 'es_editable'])
    
    def calcular_totales(self):
        """
        Calcula automáticamente subtotal y total basándose en items activos.
        Solo cuenta items que NO están cancelados.
        """
        from decimal import Decimal
        
        items_activos = self.itemplandetratamiento_set.exclude(
            estado_item__in=['cancelado', 'Cancelado']
        )
        
        subtotal = sum(
            Decimal(str(item.costofinal or 0)) 
            for item in items_activos
        )
        
        descuento_aplicado = Decimal(str(self.descuento or 0))
        total = subtotal - descuento_aplicado
        
        self.subtotal_calculado = subtotal
        self.montototal = total
        self.save(update_fields=['subtotal_calculado', 'montototal'])
        
        return {
            'subtotal': float(subtotal),
            'descuento': float(descuento_aplicado),
            'total': float(total),
            'items_activos': items_activos.count()
        }
    
    # SP3-T003: Métodos para aceptación de presupuestos
    def esta_vigente(self):
        """Verifica si el presupuesto está dentro de su fecha de vigencia."""
        if not self.fecha_vigencia:
            return True  # Sin fecha de vigencia = siempre vigente
        return timezone.now().date() <= self.fecha_vigencia
    
    def esta_caducado(self):
        """Verifica si el presupuesto ha caducado."""
        return not self.esta_vigente()
    
    def puede_ser_aceptado(self):
        """
        Verifica si el presupuesto puede ser aceptado por el paciente.
        Criterios: debe estar aprobado, vigente y no aceptado previamente.
        """
        return (
            self.es_aprobado() and
            self.esta_vigente() and 
            self.estado_aceptacion not in [self.ESTADO_ACEPTADO, self.ESTADO_RECHAZADO]
        )
    
    def marcar_como_caducado(self):
        """Marca el presupuesto como caducado."""
        self.estado_aceptacion = self.ESTADO_CADUCADO
        self.es_editable = False
        self.save(update_fields=['estado_aceptacion', 'es_editable'])


class AceptacionPresupuesto(models.Model):
    """
    Registro de auditoría para cada aceptación de presupuesto por parte del paciente.
    
    Este modelo mantiene un historial inmutable de todas las aceptaciones,
    incluyendo firma digital, comprobante, y metadata para trazabilidad.
    """
    # Tipos de aceptación
    TIPO_TOTAL = 'Total'
    TIPO_PARCIAL = 'Parcial'
    
    TIPOS_ACEPTACION = [
        (TIPO_TOTAL, 'Aceptación Total'),
        (TIPO_PARCIAL, 'Aceptación Parcial'),
    ]
    
    # Relaciones
    plandetratamiento = models.ForeignKey(
        Plandetratamiento,
        on_delete=models.CASCADE,
        related_name='aceptaciones',
        help_text="Presupuesto/Plan de tratamiento aceptado."
    )
    usuario_paciente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='aceptaciones_realizadas',
        help_text="Usuario (paciente) que realizó la aceptación."
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='aceptaciones_presupuestos',
        null=True,
        blank=True
    )
    
    # Datos de aceptación
    fecha_aceptacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp exacto de la aceptación."
    )
    tipo_aceptacion = models.CharField(
        max_length=20,
        choices=TIPOS_ACEPTACION,
        help_text="Tipo de aceptación: Total o Parcial."
    )
    items_aceptados = models.JSONField(
        default=list,
        help_text="Lista de IDs de items (Itemplandetratamiento) aceptados. Vacío si aceptación total."
    )
    
    # Firma digital y metadata
    firma_digital = models.JSONField(
        help_text="Firma digital en formato JSON: {timestamp, user_id, hash, etc.}"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Dirección IP desde donde se realizó la aceptación."
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User Agent del navegador/app del paciente."
    )
    
    # Comprobante
    comprobante_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="ID único del comprobante de aceptación. Usado para verificación."
    )
    comprobante_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL del PDF del comprobante (si se generó)."
    )
    
    # Metadata adicional
    monto_total_aceptado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total del presupuesto al momento de la aceptación."
    )
    notas = models.TextField(
        null=True,
        blank=True,
        help_text="Notas o comentarios adicionales del paciente."
    )
    
    class Meta:
        db_table = 'aceptacionpresupuesto'
        verbose_name = 'Aceptación de Presupuesto'
        verbose_name_plural = 'Aceptaciones de Presupuestos'
        ordering = ['-fecha_aceptacion']
        indexes = [
            models.Index(fields=['plandetratamiento', 'fecha_aceptacion']),
            models.Index(fields=['usuario_paciente', 'fecha_aceptacion']),
            models.Index(fields=['comprobante_id']),
        ]
    
    def __str__(self):
        return f"Aceptación {self.comprobante_id} - Presupuesto #{self.plandetratamiento.id} ({self.tipo_aceptacion})"
    
    def get_comprobante_verificacion_url(self):
        """Genera URL para verificar el comprobante."""
        # TODO: Implementar endpoint de verificación pública
        return f"/verificar-comprobante/{self.comprobante_id}/"


class Itemplandetratamiento(models.Model):
    """
    Ítem individual del plan de tratamiento.
    Representa un procedimiento/servicio específico a realizar.
    """
    # Estados del item (SP3-T001)
    ESTADO_PENDIENTE = 'Pendiente'
    ESTADO_ACTIVO = 'Activo'
    ESTADO_CANCELADO = 'Cancelado'
    ESTADO_COMPLETADO = 'Completado'
    
    ESTADOS_ITEM = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_ACTIVO, 'Activo (Habilita agenda)'),
        (ESTADO_CANCELADO, 'Cancelado (No impacta total)'),
        (ESTADO_COMPLETADO, 'Completado'),
    ]
    
    # Campos originales
    idplantratamiento = models.ForeignKey(
        Plandetratamiento, 
        on_delete=models.CASCADE,  # ✅ Elimina ítems automáticamente cuando se elimina el plan
        db_column='idplantratamiento', 
        related_name='itemplandetratamiento_set'
    )
    idservicio = models.ForeignKey(Servicio, models.DO_NOTHING, db_column='idservicio')
    idpiezadental = models.ForeignKey('Piezadental', models.DO_NOTHING, db_column='idpiezadental', blank=True, null=True)
    idestado = models.ForeignKey('Estado', models.DO_NOTHING, db_column='idestado')
    costofinal = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='itemsPlanesTratamientos', null=True, blank=True)
    
    # SP3-T001: Nuevos campos para planificación
    fecha_objetivo = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha objetivo/estimada para realizar este procedimiento."
    )
    tiempo_estimado = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Tiempo estimado en minutos para el procedimiento."
    )
    estado_item = models.CharField(
        max_length=20,
        choices=ESTADOS_ITEM,
        default=ESTADO_PENDIENTE,
        help_text="Estado del item: Pendiente/Activo/Cancelado/Completado."
    )
    notas_item = models.TextField(
        blank=True,
        null=True,
        help_text="Notas específicas del item (observaciones, instrucciones, etc.)."
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de ejecución del item en el plan (0 = sin orden específico)."
    )
    costo_base_servicio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Costo base del servicio al momento de agregar al plan (para histórico)."
    )

    class Meta:
        db_table = 'itemplandetratamiento'
        ordering = ['orden', 'id']
        verbose_name = 'Ítem de Plan de Tratamiento'
        verbose_name_plural = 'Ítems de Planes de Tratamiento'
    
    def __str__(self):
        servicio_nombre = self.idservicio.nombre if self.idservicio else 'Sin servicio'
        return f"Item #{self.id} - {servicio_nombre} ({self.estado_item})"
    
    def esta_activo(self):
        """Verifica si el item está activo (habilita agenda y cuenta para total)."""
        return self.estado_item == self.ESTADO_ACTIVO

    def esta_cancelado(self):
        """Verifica si el item fue cancelado (no impacta total)."""
        return self.estado_item == self.ESTADO_CANCELADO

    def esta_completado(self):
        """Verifica si el item está completado."""
        return self.estado_item == self.ESTADO_COMPLETADO

    def puede_editarse(self):
        """Verifica si el item puede editarse (plan debe estar en borrador)."""
        return self.idplantratamiento.puede_editarse()
    
    def activar(self):
        """Activa el item (habilita para agenda y cálculo de totales)."""
        if self.estado_item == self.ESTADO_CANCELADO:
            raise ValueError("No se puede activar un item cancelado. Créalo nuevamente.")
        self.estado_item = self.ESTADO_ACTIVO
        self.save(update_fields=['estado_item'])
    
    def cancelar(self):
        """Cancela el item (no impacta total ni habilita agenda)."""
        self.estado_item = self.ESTADO_CANCELADO
        self.save(update_fields=['estado_item'])
        # Recalcular totales del plan
        self.idplantratamiento.calcular_totales()
    
    def completar(self):
        """Marca el item como completado."""
        if not self.esta_activo():
            raise ValueError("Solo items activos pueden marcarse como completados.")
        self.estado_item = self.ESTADO_COMPLETADO
        self.save(update_fields=['estado_item'])


class SesionTratamiento(models.Model):
    """
    Sesión de avance/procedimiento clínico realizado sobre un ítem del plan de tratamiento.
    Implementa SP3-T008: Registrar procedimiento clínico (web)
    
    Representa una sesión específica donde se trabaja en un ítem del plan,
    registrando el avance, acciones realizadas, evidencias y notas.
    """
    # Campos principales
    item_plan = models.ForeignKey(
        Itemplandetratamiento,
        on_delete=models.CASCADE,
        related_name='sesiones',
        help_text="Ítem del plan de tratamiento sobre el que se realiza esta sesión"
    )
    consulta = models.ForeignKey(
        'Consulta',
        on_delete=models.CASCADE,
        related_name='sesiones_tratamiento',
        help_text="Consulta en la que se realizó esta sesión"
    )
    fecha_sesion = models.DateField(
        help_text="Fecha en que se realizó la sesión"
    )
    hora_inicio = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora de inicio de la sesión"
    )
    duracion_minutos = models.PositiveIntegerField(
        help_text="Duración de la sesión en minutos"
    )
    
    # Progreso y estado
    progreso_anterior = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Progreso del ítem antes de esta sesión (0-100%)"
    )
    progreso_actual = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Progreso del ítem después de esta sesión (0-100%)"
    )
    
    # Detalles de la sesión
    acciones_realizadas = models.TextField(
        help_text="Descripción detallada de las acciones/procedimientos realizados en esta sesión"
    )
    notas_sesion = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales, observaciones o comentarios sobre la sesión"
    )
    complicaciones = models.TextField(
        blank=True,
        null=True,
        help_text="Registro de complicaciones o situaciones inesperadas durante la sesión"
    )
    
    # Evidencias y documentación
    evidencias = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de URLs de evidencias (fotos, radiografías, etc.) asociadas a esta sesión"
    )
    
    # Control y auditoría
    usuario_registro = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sesiones_registradas',
        help_text="Usuario (odontólogo/recepcionista) que registró esta sesión"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora en que se registró esta sesión en el sistema"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True,
        help_text="Última fecha de modificación de la sesión"
    )
    
    # Multi-tenancy
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='sesiones_tratamiento',
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'sesion_tratamiento'
        ordering = ['-fecha_sesion', '-hora_inicio']
        verbose_name = 'Sesión de Tratamiento'
        verbose_name_plural = 'Sesiones de Tratamiento'
        constraints = [
            models.UniqueConstraint(
                fields=['consulta', 'item_plan'],
                name='unique_sesion_por_consulta_item',
                violation_error_message="Ya existe una sesión registrada para este ítem en esta consulta."
            ),
            models.CheckConstraint(
                check=models.Q(progreso_actual__gte=0) & models.Q(progreso_actual__lte=100),
                name='sesion_progreso_actual_valido',
                violation_error_message="El progreso debe estar entre 0 y 100%."
            ),
            models.CheckConstraint(
                check=models.Q(progreso_anterior__gte=0) & models.Q(progreso_anterior__lte=100),
                name='sesion_progreso_anterior_valido',
                violation_error_message="El progreso anterior debe estar entre 0 y 100%."
            ),
            models.CheckConstraint(
                check=models.Q(duracion_minutos__gt=0),
                name='sesion_duracion_positiva',
                violation_error_message="La duración debe ser mayor a 0 minutos."
            )
        ]
        indexes = [
            models.Index(fields=['item_plan', 'fecha_sesion']),
            models.Index(fields=['consulta']),
            models.Index(fields=['empresa', 'fecha_sesion']),
        ]
    
    def __str__(self):
        return f"Sesión {self.id} - {self.item_plan} ({self.fecha_sesion})"
    
    def clean(self):
        """Validaciones adicionales antes de guardar."""
        from django.core.exceptions import ValidationError
        
        # Validar que el progreso actual sea mayor o igual al anterior
        if self.progreso_actual < self.progreso_anterior:
            raise ValidationError({
                'progreso_actual': 'El progreso actual no puede ser menor al progreso anterior.'
            })
        
        # Validar que el ítem no esté cancelado o completado
        if self.item_plan.esta_cancelado():
            raise ValidationError({
                'item_plan': 'No se pueden registrar sesiones sobre ítems cancelados.'
            })
        
        # Si el progreso es 100%, el ítem debe marcarse como completado
        if self.progreso_actual >= 100 and self.item_plan.estado_item != Itemplandetratamiento.ESTADO_COMPLETADO:
            # Auto-marcar como completado
            self.item_plan.estado_item = Itemplandetratamiento.ESTADO_COMPLETADO
            self.item_plan.save(update_fields=['estado_item'])
    
    def save(self, *args, **kwargs):
        # Ejecutar validaciones
        self.clean()
        
        # Si es nueva sesión, obtener el progreso anterior del ítem
        if not self.pk:
            sesiones_anteriores = SesionTratamiento.objects.filter(
                item_plan=self.item_plan
            ).order_by('-fecha_sesion', '-hora_inicio')
            
            if sesiones_anteriores.exists():
                self.progreso_anterior = sesiones_anteriores.first().progreso_actual
            else:
                self.progreso_anterior = 0
        
        super().save(*args, **kwargs)
        
        # Después de guardar, recalcular el progreso del plan
        self.recalcular_progreso_plan()
    
    def recalcular_progreso_plan(self):
        """
        Recalcula el progreso general del plan de tratamiento.
        El progreso del plan es el promedio del progreso de todos sus ítems activos.
        """
        plan = self.item_plan.idplantratamiento
        items_activos = plan.itemplandetratamiento_set.filter(
            estado_item__in=[
                Itemplandetratamiento.ESTADO_ACTIVO,
                Itemplandetratamiento.ESTADO_COMPLETADO
            ]
        )
        
        if items_activos.count() == 0:
            return
        
        # Calcular progreso promedio
        total_progreso = 0
        for item in items_activos:
            # Obtener última sesión del ítem
            ultima_sesion = SesionTratamiento.objects.filter(
                item_plan=item
            ).order_by('-fecha_sesion', '-hora_inicio').first()
            
            if ultima_sesion:
                total_progreso += float(ultima_sesion.progreso_actual)
            else:
                total_progreso += 0  # Sin sesiones = 0% progreso
        
        progreso_promedio = total_progreso / items_activos.count()
        
        # Actualizar progreso del plan si existe el campo
        if hasattr(plan, 'progreso_general'):
            plan.progreso_general = round(progreso_promedio, 2)
            plan.save(update_fields=['progreso_general'])
        
        # Verificar si todos los ítems están completados
        self.verificar_plan_completado()
    
    def verificar_plan_completado(self):
        """
        Verifica si todos los ítems activos del plan están completados.
        Si es así, crea una entrada automática en el historial clínico.
        """
        plan = self.item_plan.idplantratamiento
        items_activos = plan.itemplandetratamiento_set.filter(
            estado_item__in=[
                Itemplandetratamiento.ESTADO_ACTIVO,
                Itemplandetratamiento.ESTADO_COMPLETADO
            ]
        )
        
        items_completados = items_activos.filter(
            estado_item=Itemplandetratamiento.ESTADO_COMPLETADO
        )
        
        # Si todos los ítems activos están completados
        if items_activos.count() > 0 and items_activos.count() == items_completados.count():
            # Verificar si ya existe una entrada en historial para este plan
            from .models import Historialclinico

            historial_existe = Historialclinico.objects.filter(
                pacientecodigo=plan.codpaciente,
                motivoconsulta__contains=f"Plan de Tratamiento #{plan.id}"
            ).exists()
            
            if not historial_existe:
                # Crear entrada en historial clínico
                servicios_realizados = ", ".join([item.idservicio.nombre for item in items_completados])
                Historialclinico.objects.create(
                    pacientecodigo=plan.codpaciente,
                    motivoconsulta=f"Plan de Tratamiento #{plan.id} - Completado",
                    diagnostico=f"Tratamiento completado exitosamente. Total de procedimientos realizados: {items_completados.count()}. Servicios: {servicios_realizados}",
                    empresa=self.empresa
                )
    
    def get_incremento_progreso(self):
        """Retorna el incremento de progreso en esta sesión."""
        return float(self.progreso_actual - self.progreso_anterior)


class Factura(models.Model):
    idplantratamiento = models.ForeignKey(Plandetratamiento, models.DO_NOTHING, db_column='idplantratamiento')
    idestadofactura = models.ForeignKey('Estadodefactura', models.DO_NOTHING, db_column='idestadofactura')
    fechaemision = models.DateField()
    montototal = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='facturas', null=True, blank=True)

    class Meta:
        db_table = 'factura'


class Itemdefactura(models.Model):
    idfactura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='idfactura')
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='itemsFacturas', null=True, blank=True)

    class Meta:
        db_table = 'itemdefactura'


class Pago(models.Model):
    idfactura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='idfactura')
    idtipopago = models.ForeignKey('Tipopago', models.DO_NOTHING, db_column='idtipopago')
    montopagado = models.DecimalField(max_digits=10, decimal_places=2)
    fechapago = models.DateField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='pagos', null=True, blank=True)

    class Meta:
        db_table = 'pago'


class Documentoadjunto(models.Model):
    idhistorialclinico = models.ForeignKey(Historialclinico, models.DO_NOTHING, db_column='idhistorialclinico')
    nombredocumento = models.CharField(max_length=255)
    rutaarchivo = models.CharField(max_length=512)
    fechacreacion = models.DateField(blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='documentosAdjuntos', null=True, blank=True)

    class Meta:
        db_table = 'documentoadjunto'


class Piezadental(models.Model):
    nombrepieza = models.CharField(max_length=100)
    grupo = models.CharField(max_length=100, blank=True, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='piezas_dentales', null=True, blank=True)

    class Meta:
        db_table = 'piezadental'


class Registroodontograma(models.Model):
    idhistorialclinico = models.ForeignKey(Historialclinico, models.DO_NOTHING, db_column='idhistorialclinico')
    idpiezadental = models.ForeignKey(Piezadental, models.DO_NOTHING, db_column='idpiezadental')
    diagnostico = models.TextField(blank=True, null=True)
    fecharegistro = models.DateField()
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='registrosOdontogramas', null=True, blank=True)

    class Meta:
        db_table = 'registroodontograma'


class Horario(models.Model):
    hora = models.TimeField(unique=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='horarios', null=True, blank=True)

    class Meta:
        db_table = 'horario'


class Estado(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estados', null=True, blank=True)

    class Meta:
        db_table = 'estado'


class Estadodeconsulta(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estados_consulta', null=True, blank=True)

    class Meta:
        db_table = 'estadodeconsulta'


class Estadodefactura(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estados_factura', null=True, blank=True)

    class Meta:
        db_table = 'estadodefactura'


class Tipodeusuario(models.Model):
    rol = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(
        Empresa, on_delete=models.CASCADE,
        related_name='tipos_usuario', null=True, blank=True
    )

    class Meta:
        db_table = 'tipodeusuario'
        constraints = [
            models.UniqueConstraint(
                fields=['empresa', 'rol'],
                name='uq_tipousuario_empresa_rol'
            )
        ]


class Tipopago(models.Model):
    nombrepago = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tipos_pago', null=True, blank=True)

    class Meta:
        db_table = 'tipopago'


# TEMPORALMENTE COMENTADO - La tabla 'vista' no existe en la BD
# class Vista(models.Model):
#     ...


# ============================================================================
# MODELO DE CONSENTIMIENTO DIGITAL
# ============================================================================
class Consentimiento(models.Model):
    """
    Almacena el registro de un consentimiento informado firmado por un paciente.
    """
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consentimientos')
    # Opcional, para vincular el consentimiento a una cita o plan específico
    consulta = models.ForeignKey(Consulta, on_delete=models.SET_NULL, null=True, blank=True, related_name='consentimientos')
    plan_tratamiento = models.ForeignKey(Plandetratamiento, on_delete=models.SET_NULL, null=True, blank=True, related_name='consentimientos')

    # Datos del tenant
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='consentimientos')

    # Contenido del consentimiento en el momento de la firma (para registro histórico)
    titulo = models.CharField(max_length=255)
    texto_contenido = models.TextField()

    # Datos de la firma
    firma_base64 = models.TextField(help_text="Firma del paciente guardada en formato Base64")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ip_creacion = models.GenericIPAddressField()

    # Datos del documento sellado
    pdf_firmado = models.BinaryField(help_text="PDF del consentimiento con firma digital", null=True)
    hash_documento = models.CharField(max_length=64, help_text="Hash SHA-256 del documento firmado", null=True)
    fecha_hora_sello = models.DateTimeField(help_text="Fecha y hora del sellado digital", null=True)

    # Datos de validación
    validado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='consentimientos_validados',
        help_text="Usuario que validó el consentimiento"
    )
    fecha_validacion = models.DateTimeField(help_text="Fecha y hora de validación", null=True)

    class Meta:
        db_table = 'api_consentimiento'
        verbose_name = 'Consentimiento'
        verbose_name_plural = 'Consentimientos'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Consentimiento de {self.paciente} ({self.fecha_creacion.strftime('%Y-%m-%d')})"


# ============================================================================
# TABLA DE AUDITORÍA
# ============================================================================
class Bitacora(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, db_column='codusuario', null=True, blank=True)
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=100, null=True, blank=True)
    registro_id = models.IntegerField(null=True, blank=True)
    valores_anteriores = models.JSONField(null=True, blank=True)
    valores_nuevos = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='bitacoras', null=True, blank=True)

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'

    def __str__(self):
        usuario_nombre = self.usuario.nombre if self.usuario else "Sistema"
        return f"{usuario_nombre} - {self.accion} - {self.tabla_afectada} - {self.timestamp}"


# ============================================================================
# CONTROL DE ACCESO: BLOQUEO DE USUARIOS
# ============================================================================
class BloqueoUsuario(models.Model):
    usuario = models.ForeignKey("Usuario", on_delete=models.CASCADE, related_name="bloqueos")
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    motivo = models.CharField(max_length=255, blank=True, default="")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "Bloqueo de Usuario"
        verbose_name_plural = "Bloqueos de Usuarios"
        db_table = "bloqueousuario"

    def esta_vigente(self):
        return self.activo and (self.fecha_fin is None or self.fecha_fin > timezone.now())

    def __str__(self):
        return f"Bloqueo {self.usuario} desde {self.fecha_inicio} hasta {self.fecha_fin or 'indefinido'}"


# ============================================================================
# DOCUMENTOS CLÍNICOS EN S3
# ============================================================================
class DocumentoClinico(models.Model):
    """
    Modelo para gestionar documentos clínicos almacenados en AWS S3.
    Vincula archivos médicos (radiografías, PDF, imágenes) a pacientes, consultas e historiales.
    """
    TIPO_CHOICES = [
        ('radiografia', 'Radiografía'),
        ('examen_laboratorio', 'Examen de Laboratorio'),
        ('imagen_diagnostico', 'Imagen de Diagnóstico'),
        ('consentimiento', 'Consentimiento Informado'),
        ('receta', 'Receta Médica'),
        ('foto_clinica', 'Foto Clínica'),
        ('otro', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codpaciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        db_column='codpaciente',
        related_name='documentos_clinicos'
    )
    idconsulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        db_column='idconsulta',
        null=True,
        blank=True,
        related_name='documentos'
    )
    idhistorialclinico = models.ForeignKey(
        Historialclinico,
        on_delete=models.SET_NULL,
        db_column='idhistorialclinico',
        null=True,
        blank=True,
        related_name='documentos_s3'
    )

    tipo_documento = models.CharField(max_length=50, choices=TIPO_CHOICES)
    nombre_archivo = models.CharField(max_length=255)
    url_s3 = models.CharField(max_length=500)
    s3_key = models.CharField(max_length=500)
    tamanio_bytes = models.PositiveIntegerField()
    extension = models.CharField(max_length=10)

    profesional_carga = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        db_column='profesional_carga',
        null=True,
        related_name='documentos_cargados'
    )
    fecha_documento = models.DateField(help_text="Fecha del documento médico")
    notas = models.TextField(blank=True, null=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='documentos_clinicos',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'documento_clinico'
        ordering = ['-fecha_creacion']
        verbose_name = 'Documento Clínico'
        verbose_name_plural = 'Documentos Clínicos'

    def __str__(self):
        return f"{self.tipo_documento} - {self.nombre_archivo} - Paciente: {self.codpaciente}"


# +++ SP3-T002: Presupuesto Digital +++
class PresupuestoDigital(models.Model):
    """
    Presupuesto digital generado a partir de un Plan de Tratamiento aprobado.
    
    Permite generar presupuestos totales o parciales (por tramos) seleccionando
    qué ítems del plan incluir, con gestión de vigencia y estados.
    
    SP3-T002: Generar presupuesto digital (web)
    """
    # Estados del presupuesto
    ESTADO_BORRADOR = 'Borrador'
    ESTADO_EMITIDO = 'Emitido'
    ESTADO_CADUCADO = 'Caducado'
    ESTADO_ANULADO = 'Anulado'
    
    ESTADOS_CHOICES = [
        (ESTADO_BORRADOR, 'Borrador (Editable)'),
        (ESTADO_EMITIDO, 'Emitido (Inmutable)'),
        (ESTADO_CADUCADO, 'Caducado'),
        (ESTADO_ANULADO, 'Anulado'),
    ]
    
    # Relaciones
    plan_tratamiento = models.ForeignKey(
        Plandetratamiento,
        on_delete=models.CASCADE,
        related_name='presupuestos_digitales',
        help_text="Plan de tratamiento aprobado del cual se generó este presupuesto."
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='presupuestos_digitales',
        null=True,
        blank=True
    )
    
    # Identificación única
    codigo_presupuesto = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Código único de trazabilidad del presupuesto."
    )
    
    # Fechas
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación del presupuesto."
    )
    fecha_vigencia = models.DateField(
        help_text="Fecha límite de validez del presupuesto. Después caduca."
    )
    fecha_emitido = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que el presupuesto fue oficialmente emitido."
    )
    
    # Usuario que emite
    usuario_emite = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_emitidos',
        help_text="Usuario (odontólogo/admin) que emitió el presupuesto."
    )
    
    # Estado y tipo
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CHOICES,
        default=ESTADO_BORRADOR,
        help_text="Estado actual del presupuesto."
    )
    es_tramo = models.BooleanField(
        default=False,
        help_text="Indica si es un presupuesto parcial (tramo) o total."
    )
    numero_tramo = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número de tramo si es presupuesto parcial (1, 2, 3...)."
    )
    
    # Montos
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Suma de todos los items incluidos antes de descuentos."
    )
    descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Descuento aplicado al presupuesto completo."
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto total del presupuesto (subtotal - descuento)."
    )
    
    # Términos y condiciones
    terminos_condiciones = models.TextField(
        blank=True,
        null=True,
        help_text="Términos y condiciones específicos de este presupuesto."
    )
    notas = models.TextField(
        blank=True,
        null=True,
        help_text="Notas adicionales o aclaraciones del presupuesto."
    )
    
    # PDF generado
    pdf_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL del PDF generado del presupuesto (S3 o storage)."
    )
    pdf_generado = models.BooleanField(
        default=False,
        help_text="Indica si se generó el PDF del presupuesto."
    )
    
    # Control de edición
    es_editable = models.BooleanField(
        default=True,
        help_text="Indica si el presupuesto puede editarse. Se bloquea al emitir."
    )
    
    # ===== CAMPOS DE ACEPTACIÓN (SP3-T003) =====
    # Estados de aceptación del presupuesto por el paciente
    ESTADO_ACEPTACION_PENDIENTE = 'Pendiente'
    ESTADO_ACEPTACION_ACEPTADO = 'Aceptado'
    ESTADO_ACEPTACION_RECHAZADO = 'Rechazado'
    ESTADO_ACEPTACION_PARCIAL = 'Parcial'
    
    ESTADOS_ACEPTACION_CHOICES = [
        (ESTADO_ACEPTACION_PENDIENTE, 'Pendiente de aceptación'),
        (ESTADO_ACEPTACION_ACEPTADO, 'Aceptado por paciente'),
        (ESTADO_ACEPTACION_RECHAZADO, 'Rechazado por paciente'),
        (ESTADO_ACEPTACION_PARCIAL, 'Aceptación parcial (por ítems)'),
    ]
    
    estado_aceptacion = models.CharField(
        max_length=20,
        choices=ESTADOS_ACEPTACION_CHOICES,
        default=ESTADO_ACEPTACION_PENDIENTE,
        help_text="Estado de aceptación del presupuesto por el paciente."
    )
    
    fecha_aceptacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que el paciente aceptó el presupuesto."
    )
    
    usuario_acepta = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_digitales_aceptados',
        help_text="Usuario (paciente) que aceptó el presupuesto."
    )
    
    tipo_aceptacion = models.CharField(
        max_length=20,
        choices=[('Total', 'Total'), ('Parcial', 'Parcial')],
        null=True,
        blank=True,
        help_text="Tipo de aceptación: Total o Parcial (por ítems)."
    )
    
    comprobante_aceptacion_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL del PDF del comprobante de aceptación."
    )
    
    # Timestamps
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'presupuesto_digital'
        verbose_name = 'Presupuesto Digital'
        verbose_name_plural = 'Presupuestos Digitales'
        ordering = ['-fecha_emision']
        indexes = [
            models.Index(fields=['plan_tratamiento', 'estado']),
            models.Index(fields=['empresa', 'fecha_emision']),
            models.Index(fields=['codigo_presupuesto']),
        ]
    
    def __str__(self):
        tipo = "Tramo" if self.es_tramo else "Total"
        return f"Presupuesto {tipo} #{self.codigo_presupuesto.hex[:8]} - {self.estado}"
    
    def esta_vigente(self):
        """Verifica si el presupuesto está dentro de su fecha de vigencia."""
        if self.estado == self.ESTADO_CADUCADO:
            return False
        return timezone.now().date() <= self.fecha_vigencia
    
    def puede_editarse(self):
        """Solo presupuestos en borrador pueden editarse."""
        return self.estado == self.ESTADO_BORRADOR and self.es_editable
    
    def emitir(self, usuario):
        """
        Emite el presupuesto oficialmente, bloqueando su edición.
        """
        if self.estado != self.ESTADO_BORRADOR:
            raise ValueError("Solo presupuestos en borrador pueden ser emitidos.")
        
        self.estado = self.ESTADO_EMITIDO
        self.fecha_emitido = timezone.now()
        self.usuario_emite = usuario
        self.es_editable = False
        self.save(update_fields=['estado', 'fecha_emitido', 'usuario_emite', 'es_editable'])
    
    def marcar_caducado(self):
        """Marca el presupuesto como caducado si venció su vigencia."""
        if not self.esta_vigente() and self.estado == self.ESTADO_EMITIDO:
            self.estado = self.ESTADO_CADUCADO
            self.save(update_fields=['estado'])
    
    def puede_ser_aceptado(self):
        """
        Verifica si el presupuesto puede ser aceptado por el paciente.
        
        Returns:
            bool: True si puede aceptarse, False en caso contrario.
        """
        # Debe estar emitido
        if self.estado != self.ESTADO_EMITIDO:
            return False
        
        # No debe estar caducado
        if not self.esta_vigente():
            return False
        
        # No debe estar ya aceptado completamente
        if self.estado_aceptacion == self.ESTADO_ACEPTACION_ACEPTADO:
            return False
        
        # No debe estar rechazado
        if self.estado_aceptacion == self.ESTADO_ACEPTACION_RECHAZADO:
            return False
        
        return True
    
    def calcular_totales(self):
        """
        Recalcula subtotal y total basándose en los items incluidos.
        """
        from decimal import Decimal
        
        items = self.items_presupuesto.all()
        
        subtotal = sum(
            Decimal(str(item.precio_unitario or 0)) 
            for item in items
        )
        
        descuento_aplicado = Decimal(str(self.descuento or 0))
        total = subtotal - descuento_aplicado
        
        self.subtotal = subtotal
        self.total = total
        self.save(update_fields=['subtotal', 'total'])
        
        return {
            'subtotal': float(subtotal),
            'descuento': float(descuento_aplicado),
            'total': float(total),
            'items_count': items.count()
        }


class ItemPresupuestoDigital(models.Model):
    """
    Ítem individual dentro de un presupuesto digital.
    
    Representa cada servicio/tratamiento incluido en el presupuesto,
    con su precio, descuentos y opciones de pago.
    """
    presupuesto = models.ForeignKey(
        PresupuestoDigital,
        on_delete=models.CASCADE,
        related_name='items_presupuesto',
        help_text="Presupuesto al que pertenece este ítem."
    )
    item_plan = models.ForeignKey(
        Itemplandetratamiento,
        on_delete=models.CASCADE,
        related_name='items_en_presupuestos',
        help_text="Ítem del plan de tratamiento que representa este presupuesto."
    )
    
    # Pricing
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio del servicio para este presupuesto."
    )
    descuento_item = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Descuento aplicado específicamente a este ítem."
    )
    precio_final = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio final después de descuentos (precio_unitario - descuento_item)."
    )
    
    # Pagos parciales
    permite_pago_parcial = models.BooleanField(
        default=False,
        help_text="Indica si este ítem acepta pagos fraccionados."
    )
    cantidad_cuotas = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Número de cuotas disponibles si permite pago parcial."
    )
    
    # Notas específicas del ítem
    notas_item = models.TextField(
        blank=True,
        null=True,
        help_text="Notas o aclaraciones específicas de este ítem."
    )
    
    # Orden en el presupuesto
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización del ítem en el presupuesto."
    )
    
    class Meta:
        db_table = 'item_presupuesto_digital'
        verbose_name = 'Ítem de Presupuesto'
        verbose_name_plural = 'Ítems de Presupuesto'
        ordering = ['presupuesto', 'orden']
        unique_together = [['presupuesto', 'item_plan']]
    
    def __str__(self):
        servicio = self.item_plan.idservicio.nombre if self.item_plan and self.item_plan.idservicio else "Sin servicio"
        return f"{servicio} - ${self.precio_final}"
    
    def save(self, *args, **kwargs):
        """Calcula precio_final automáticamente antes de guardar."""
        from decimal import Decimal
        self.precio_final = Decimal(str(self.precio_unitario)) - Decimal(str(self.descuento_item or 0))
        super().save(*args, **kwargs)

class AceptacionPresupuestoDigital(models.Model):
    """
    Registro de auditoría inmutable para aceptación de presupuestos digitales.
    
    Cada vez que un paciente acepta un presupuesto digital (total o parcialmente),
    se crea un registro en esta tabla con toda la información de trazabilidad.
    
    SP3-T003: Aceptar presupuesto digital por paciente
    """
    # Tipos de aceptación
    TIPO_TOTAL = 'Total'
    TIPO_PARCIAL = 'Parcial'
    
    TIPOS_ACEPTACION = [
        (TIPO_TOTAL, 'Aceptación Total'),
        (TIPO_PARCIAL, 'Aceptación Parcial por Ítems'),
    ]
    
    # Relaciones principales
    presupuesto_digital = models.ForeignKey(
        PresupuestoDigital,
        on_delete=models.CASCADE,
        related_name='aceptaciones',
        help_text="Presupuesto digital aceptado por el paciente."
    )
    
    usuario_paciente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='aceptaciones_presupuestos_digitales',
        help_text="Paciente que realizó la aceptación."
    )
    
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='aceptaciones_presupuestos_digitales',
        null=True,
        blank=True,
        help_text="Empresa (clínica) asociada al presupuesto."
    )
    
    # Datos de la aceptación
    fecha_aceptacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp exacto de la aceptación (sello de tiempo)."
    )
    
    tipo_aceptacion = models.CharField(
        max_length=20,
        choices=TIPOS_ACEPTACION,
        help_text="Tipo de aceptación: Total o Parcial."
    )
    
    items_aceptados = models.JSONField(
        default=list,
        help_text="Lista de IDs de ItemPresupuestoDigital aceptados. Vacío si Total."
    )
    
    # Firma digital electrónica simple
    firma_digital = models.JSONField(
        help_text="""
        Firma digital del paciente en formato JSON:
        {
            'timestamp': '2025-10-25T10:30:00Z',
            'user_id': 123,
            'signature_hash': 'abc123...',
            'consent_text': 'Acepto los términos...',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0...'
        }
        """
    )
    
    # Metadata de trazabilidad
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se realizó la aceptación."
    )
    
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User Agent del navegador/dispositivo del paciente."
    )
    
    # Comprobante de aceptación
    comprobante_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="ID único del comprobante para verificación."
    )
    
    comprobante_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL del PDF del comprobante de aceptación."
    )
    
    # Montos al momento de la aceptación (snapshot inmutable)
    monto_subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Subtotal del presupuesto al momento de la aceptación."
    )
    
    monto_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Descuento del presupuesto al momento de la aceptación."
    )
    
    monto_total_aceptado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total aceptado (snapshot inmutable)."
    )
    
    # Notas del paciente
    notas_paciente = models.TextField(
        null=True,
        blank=True,
        help_text="Comentarios o condiciones del paciente al aceptar."
    )
    
    # Estado de pago (para futuro SP3-T004)
    listo_para_pago = models.BooleanField(
        default=True,
        help_text="Indica si está listo para procesar pago."
    )
    
    class Meta:
        db_table = 'aceptacion_presupuesto_digital'
        verbose_name = 'Aceptación de Presupuesto Digital'
        verbose_name_plural = 'Aceptaciones de Presupuestos Digitales'
        ordering = ['-fecha_aceptacion']
        indexes = [
            models.Index(fields=['presupuesto_digital', 'fecha_aceptacion']),
            models.Index(fields=['usuario_paciente', 'fecha_aceptacion']),
            models.Index(fields=['comprobante_id']),
            models.Index(fields=['empresa', 'fecha_aceptacion']),
        ]
    
    def __str__(self):
        return f"Aceptación {self.comprobante_id} - Presup. #{self.presupuesto_digital.codigo_presupuesto.hex[:8]}"
    
    def get_comprobante_url_publica(self):
        """URL pública para verificar el comprobante."""
        return f"/api/verificar-comprobante/{self.comprobante_id}/"


# +++ MODELO EVIDENCIA (SP3-T008 FASE 5) +++
def evidencia_upload_path(instance, filename):
    """
    Genera ruta única para evidencias:
    evidencias/2025/10/27/<uuid>_<filename>
    """
    import os
    from django.utils.text import slugify
    from datetime import datetime
    
    ext = filename.split('.')[-1]
    name = os.path.splitext(filename)[0]
    name = slugify(name)[:50]  # Sanitizar nombre
    filename_safe = f"{uuid.uuid4().hex[:8]}_{name}.{ext.lower()}"
    
    # Usar la fecha actual si fecha_subida no está disponible
    fecha = instance.fecha_subida if hasattr(instance, 'fecha_subida') and instance.fecha_subida else datetime.now()
    
    return os.path.join(
        'evidencias',
        str(fecha.year),
        str(fecha.month),
        str(fecha.day),
        filename_safe
    )


class Evidencia(models.Model):
    """
    Modelo para gestionar evidencias (fotos, radiografías, PDFs) 
    subidas en las sesiones de tratamiento.
    
    Multi-tenancy: Filtrado por empresa.
    """
    TIPO_CHOICES = [
        ('evidencia_sesion', 'Evidencia de Sesión'),
        ('radiografia', 'Radiografía'),
        ('foto_clinica', 'Foto Clínica'),
        ('documento', 'Documento'),
    ]
    
    # Archivo
    archivo = models.FileField(
        upload_to=evidencia_upload_path,
        max_length=500,
        help_text="Archivo subido (imagen o PDF)"
    )
    nombre_original = models.CharField(
        max_length=255,
        help_text="Nombre original del archivo"
    )
    tipo = models.CharField(
        max_length=50,
        default='evidencia_sesion',
        choices=TIPO_CHOICES,
        help_text="Tipo de evidencia"
    )
    
    # Metadatos del archivo
    mimetype = models.CharField(
        max_length=100,
        help_text="MIME type del archivo (ej: image/jpeg)"
    )
    tamanio = models.IntegerField(
        help_text='Tamaño en bytes'
    )
    
    # Relaciones (Multi-tenancy)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evidencias_subidas',
        db_column='usuario_id',
        help_text="Usuario que subió la evidencia"
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='evidencias',
        help_text="Empresa (tenant) dueña de la evidencia"
    )
    
    # Metadatos de auditoría
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de subida"
    )
    ip_subida = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se subió el archivo"
    )
    
    class Meta:
        db_table = 'evidencias'
        verbose_name = 'Evidencia'
        verbose_name_plural = 'Evidencias'
        ordering = ['-fecha_subida']
        indexes = [
            models.Index(fields=['empresa', '-fecha_subida']),
            models.Index(fields=['usuario', '-fecha_subida']),
            models.Index(fields=['tipo', '-fecha_subida']),
        ]
    
    def __str__(self):
        return f"{self.nombre_original} - {self.fecha_subida.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def url(self):
        """Retorna URL completa del archivo"""
        if self.archivo:
            return self.archivo.url
        return None
    
    def delete(self, *args, **kwargs):
        """Eliminar archivo físico al borrar registro"""
        if self.archivo:
            # Eliminar archivo físico del storage
            self.archivo.delete(save=False)
        super().delete(*args, **kwargs)
    
    def get_tamanio_legible(self):
        """Retorna tamaño en formato legible (KB, MB)"""
        size = self.tamanio
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
