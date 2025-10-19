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
    # Estados de aceptación
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
    
    # Nuevos campos para aceptación de presupuestos (SP3-T003)
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
        return f"Presupuesto #{self.id} - {self.codpaciente.codusuario.nombre} ({self.estado_aceptacion})"
    
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
        Criterios: debe estar vigente y no haber sido aceptado previamente.
        """
        return (
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
    idplantratamiento = models.ForeignKey(Plandetratamiento, models.DO_NOTHING, db_column='idplantratamiento')
    idservicio = models.ForeignKey(Servicio, models.DO_NOTHING, db_column='idservicio')
    idpiezadental = models.ForeignKey('Piezadental', models.DO_NOTHING, db_column='idpiezadental', blank=True, null=True)
    idestado = models.ForeignKey('Estado', models.DO_NOTHING, db_column='idestado')
    costofinal = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='itemsPlanesTratamientos', null=True, blank=True)

    class Meta:
        db_table = 'itemplandetratamiento'


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