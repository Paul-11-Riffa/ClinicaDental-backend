from django.db import models
from django.utils import timezone
import uuid


class Paciente(models.Model):
    codusuario = models.OneToOneField('users.Usuario', models.DO_NOTHING, db_column='codusuario', primary_key=True)
    carnetidentidad = models.CharField(unique=True, max_length=50, blank=True, null=True)
    fechanacimiento = models.DateField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='pacientes', null=True, blank=True)

    class Meta:
        db_table = 'paciente'


class Odontologo(models.Model):
    codusuario = models.OneToOneField('users.Usuario', models.DO_NOTHING, db_column='codusuario', primary_key=True)
    especialidad = models.CharField(max_length=255, blank=True, null=True)
    experienciaprofesional = models.TextField(blank=True, null=True)
    nromatricula = models.CharField(unique=True, max_length=100, blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='odontologos', null=True, blank=True)

    class Meta:
        db_table = 'odontologo'


class Recepcionista(models.Model):
    codusuario = models.OneToOneField('users.Usuario', models.DO_NOTHING, db_column='codusuario', primary_key=True)
    habilidadessoftware = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='recepcionistas', null=True, blank=True)

    class Meta:
        db_table = 'recepcionista'


class Horario(models.Model):
    hora = models.TimeField(unique=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='horarios', null=True, blank=True)

    class Meta:
        db_table = 'horario'


class Tipodeconsulta(models.Model):
    nombreconsulta = models.CharField(max_length=255)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='tipos_consulta', null=True, blank=True)

    class Meta:
        db_table = 'tipodeconsulta'


class Estadodeconsulta(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='estados_consulta', null=True, blank=True)

    class Meta:
        db_table = 'estadodeconsulta'


class Consulta(models.Model):
    fecha = models.DateField()
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo', blank=True, null=True)
    codrecepcionista = models.ForeignKey(Recepcionista, models.DO_NOTHING, db_column='codrecepcionista', blank=True, null=True)
    idhorario = models.ForeignKey(Horario, models.DO_NOTHING, db_column='idhorario')
    idtipoconsulta = models.ForeignKey(Tipodeconsulta, models.DO_NOTHING, db_column='idtipoconsulta')
    idestadoconsulta = models.ForeignKey(Estadodeconsulta, models.DO_NOTHING, db_column='idestadoconsulta')
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='consultas', null=True, blank=True)

    class Meta:
        db_table = 'consulta'


class Historialclinico(models.Model):
    """Historia clínica de pacientes."""
    pacientecodigo = models.ForeignKey(
        Paciente,
        on_delete=models.DO_NOTHING,
        db_column='pacientecodigo',
        related_name='historias'
    )
    alergias = models.TextField(blank=True, null=True)
    enfermedades = models.TextField(blank=True, null=True)
    motivoconsulta = models.TextField(blank=True, null=True)
    diagnostico = models.TextField(blank=True, null=True)
    episodio = models.PositiveIntegerField(default=1)
    fecha = models.DateTimeField(auto_now_add=True, null=False)
    updated_at = models.DateTimeField(auto_now=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='historiales', null=True, blank=True)

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
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='servicios', null=True, blank=True)

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
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='insumos', null=True, blank=True)

    class Meta:
        db_table = 'insumo'


class Medicamento(models.Model):
    nombre = models.CharField(max_length=255)
    cantidadmiligramos = models.CharField(max_length=100, blank=True, null=True)
    presentacion = models.CharField(max_length=255, blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='medicamentos', null=True, blank=True)

    class Meta:
        db_table = 'medicamento'


class Recetamedica(models.Model):
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo')
    fechaemision = models.DateField()
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='recetas', null=True, blank=True)

    class Meta:
        db_table = 'recetamedica'


class Imtemreceta(models.Model):
    idreceta = models.ForeignKey(Recetamedica, models.DO_NOTHING, db_column='idreceta')
    idmedicamento = models.ForeignKey(Medicamento, models.DO_NOTHING, db_column='idmedicamento')
    posologia = models.TextField()
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='itemsReceta', null=True, blank=True)

    class Meta:
        db_table = 'itemreceta'


class Estado(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='estados', null=True, blank=True)

    class Meta:
        db_table = 'estado'


class Estadodefactura(models.Model):
    estado = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='estados_factura', null=True, blank=True)

    class Meta:
        db_table = 'estadodefactura'


class Tipopago(models.Model):
    nombrepago = models.CharField(unique=True, max_length=100)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='tipos_pago', null=True, blank=True)

    class Meta:
        db_table = 'tipopago'


class Plandetratamiento(models.Model):
    codpaciente = models.ForeignKey(Paciente, models.DO_NOTHING, db_column='codpaciente')
    cododontologo = models.ForeignKey(Odontologo, models.DO_NOTHING, db_column='cododontologo')
    idestado = models.ForeignKey(Estado, models.DO_NOTHING, db_column='idestado')
    fechaplan = models.DateField()
    descuento = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    montototal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='planesTratamientos', null=True, blank=True)

    class Meta:
        db_table = 'plandetratamiento'


class Piezadental(models.Model):
    nombrepieza = models.CharField(max_length=100)
    grupo = models.CharField(max_length=100, blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='piezas_dentales', null=True, blank=True)

    class Meta:
        db_table = 'piezadental'


class Itemplandetratamiento(models.Model):
    idplantratamiento = models.ForeignKey(Plandetratamiento, models.DO_NOTHING, db_column='idplantratamiento')
    idservicio = models.ForeignKey(Servicio, models.DO_NOTHING, db_column='idservicio')
    idpiezadental = models.ForeignKey(Piezadental, models.DO_NOTHING, db_column='idpiezadental', blank=True, null=True)
    idestado = models.ForeignKey(Estado, models.DO_NOTHING, db_column='idestado')
    costofinal = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='itemsPlanesTratamientos', null=True, blank=True)

    class Meta:
        db_table = 'itemplandetratamiento'


class Factura(models.Model):
    idplantratamiento = models.ForeignKey(Plandetratamiento, models.DO_NOTHING, db_column='idplantratamiento')
    idestadofactura = models.ForeignKey(Estadodefactura, models.DO_NOTHING, db_column='idestadofactura')
    fechaemision = models.DateField()
    montototal = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='facturas', null=True, blank=True)

    class Meta:
        db_table = 'factura'


class Itemdefactura(models.Model):
    idfactura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='idfactura')
    descripcion = models.TextField()
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='itemsFacturas', null=True, blank=True)

    class Meta:
        db_table = 'itemdefactura'


class Pago(models.Model):
    idfactura = models.ForeignKey(Factura, models.DO_NOTHING, db_column='idfactura')
    idtipopago = models.ForeignKey(Tipopago, models.DO_NOTHING, db_column='idtipopago')
    montopagado = models.DecimalField(max_digits=10, decimal_places=2)
    fechapago = models.DateField()
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='pagos', null=True, blank=True)

    class Meta:
        db_table = 'pago'


class Documentoadjunto(models.Model):
    idhistorialclinico = models.ForeignKey(Historialclinico, models.DO_NOTHING, db_column='idhistorialclinico')
    nombredocumento = models.CharField(max_length=255)
    rutaarchivo = models.CharField(max_length=512)
    fechacreacion = models.DateField(blank=True, null=True)
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='documentosAdjuntos', null=True, blank=True)

    class Meta:
        db_table = 'documentoadjunto'


class Registroodontograma(models.Model):
    idhistorialclinico = models.ForeignKey(Historialclinico, models.DO_NOTHING, db_column='idhistorialclinico')
    idpiezadental = models.ForeignKey(Piezadental, models.DO_NOTHING, db_column='idpiezadental')
    diagnostico = models.TextField(blank=True, null=True)
    fecharegistro = models.DateField()
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='registrosOdontogramas', null=True, blank=True)

    class Meta:
        db_table = 'registroodontograma'


class Consentimiento(models.Model):
    """Consentimiento informado digital."""
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='consentimientos')
    consulta = models.ForeignKey(Consulta, on_delete=models.SET_NULL, null=True, blank=True, related_name='consentimientos')
    plan_tratamiento = models.ForeignKey(Plandetratamiento, on_delete=models.SET_NULL, null=True, blank=True, related_name='consentimientos')
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='consentimientos')
    
    titulo = models.CharField(max_length=255)
    texto_contenido = models.TextField()
    firma_base64 = models.TextField(help_text="Firma del paciente guardada en formato Base64")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ip_creacion = models.GenericIPAddressField()
    
    pdf_firmado = models.BinaryField(help_text="PDF del consentimiento con firma digital", null=True)
    hash_documento = models.CharField(max_length=64, help_text="Hash SHA-256 del documento firmado", null=True)
    fecha_hora_sello = models.DateTimeField(help_text="Fecha y hora del sellado digital", null=True)
    
    validado_por = models.ForeignKey(
        'users.Usuario',
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


class DocumentoClinico(models.Model):
    """Documentos clínicos almacenados en AWS S3."""
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
        'users.Usuario',
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
        'tenancy.Empresa',
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
