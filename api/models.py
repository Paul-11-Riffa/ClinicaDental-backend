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
    
    # NUEVOS CAMPOS: Appointment Lifecycle (Realistic Flow Phase 1 - Optimized)
    # Estado del ciclo de vida de la cita (8 estados - Opción B Realista)
    ESTADOS_CONSULTA = [
        ('pendiente', 'Pendiente'),          # Cita agendada, no confirmada
        ('confirmada', 'Confirmada'),        # Cita confirmada por staff
        ('en_consulta', 'En Consulta'),      # Paciente siendo atendido
        ('diagnosticada', 'Diagnosticada'),  # Diagnóstico completado
        ('con_plan', 'Con Plan'),            # Plan de tratamiento generado
        ('completada', 'Completada'),        # Consulta finalizada
        ('cancelada', 'Cancelada'),          # Cita cancelada
        ('no_asistio', 'No Asistió'),        # Paciente no se presentó
    ]
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS_CONSULTA,
        default='pendiente',
        help_text="Estado del ciclo de vida de la cita"
    )
    
    # Campos de solicitud de cita
    fecha_preferida = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha que el paciente prefiere (antes de confirmar)"
    )
    
    # NUEVO: Horario preferido (franja horaria) - Agendamiento Web
    horario_preferido = models.CharField(
        max_length=20,
        choices=[
            ('mañana', 'Mañana (8am-12pm)'),
            ('tarde', 'Tarde (2pm-6pm)'),
            ('noche', 'Noche (6pm-8pm)'),
            ('cualquiera', 'Cualquier horario'),
        ],
        default='cualquiera',
        db_column='horario_preferido',
        help_text="Horario preferido por el paciente"
    )
    
    # Campos de cita confirmada
    fecha_consulta = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha confirmada de la consulta"
    )
    hora_consulta = models.TimeField(
        null=True,
        blank=True,
        help_text="Hora confirmada de la consulta"
    )
    
    # Timestamps del flujo de la cita
    hora_llegada = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que el paciente llegó (check-in)"
    )
    hora_inicio_consulta = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que comenzó la consulta"
    )
    hora_fin_consulta = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Momento en que terminó la consulta"
    )
    
    # Tipo y metadata de la cita
    TIPOS_CONSULTA = [
        ('primera_vez', 'Primera Vez'),
        ('control', 'Control'),
        ('tratamiento', 'Tratamiento'),
        ('urgencia', 'Urgencia'),
    ]
    tipo_consulta = models.CharField(
        max_length=20,
        choices=TIPOS_CONSULTA,
        null=True,
        blank=True,
        help_text="Tipo de consulta solicitada"
    )
    motivo_consulta = models.TextField(
        null=True,
        blank=True,
        help_text="Razón por la que el paciente solicita la cita"
    )
    notas_recepcion = models.TextField(
        null=True,
        blank=True,
        help_text="Notas de la recepcionista al confirmar/gestionar la cita"
    )
    motivo_cancelacion = models.TextField(
        null=True,
        blank=True,
        help_text="Motivo de cancelación de la cita"
    )
    
    # Duración
    duracion_estimada = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duración estimada en minutos"
    )
    
    # Campos clínicos
    observaciones = models.TextField(
        null=True,
        blank=True,
        help_text="Observaciones generales"
    )
    diagnostico = models.TextField(
        null=True,
        blank=True,
        help_text="Diagnóstico del odontólogo"
    )
    tratamiento = models.TextField(
        null=True,
        blank=True,
        help_text="Tratamiento recomendado"
    )
    
    # NUEVOS CAMPOS: Flujo Clínico (Paso 1)
    costo_consulta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Costo de la consulta (si aplica)"
    )
    requiere_pago = models.BooleanField(
        default=False,
        help_text="Indica si esta consulta requiere pago previo"
    )
    plan_tratamiento = models.ForeignKey(
        'Plandetratamiento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas_ejecucion',
        help_text="Plan al que pertenece esta consulta (si es de ejecución)"
    )
    pago_consulta = models.ForeignKey(
        'PagoEnLinea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consulta_pagada',
        help_text="Pago asociado a esta consulta"
    )
    
    # =========================================
    # NUEVOS CAMPOS: Agendamiento Web (Frontend Request)
    # =========================================
    
    # Campo 1: Indicador de agendamiento web
    agendado_por_web = models.BooleanField(
        default=False,
        db_column='agendado_por_web',
        help_text="¿Esta consulta fue agendada por el paciente desde la web?"
    )
    
    # Campo 2: Nivel de prioridad
    prioridad = models.CharField(
        max_length=20,
        choices=[
            ('normal', 'Normal'),
            ('urgente', 'Urgente'),
        ],
        default='normal',
        db_column='prioridad',
        help_text="Nivel de prioridad de la consulta"
    )
    
    # =========================================
    # CAMPOS: Timestamps (Auditoría)
    # =========================================
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de creación de la consulta"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de última actualización"
    )

    class Meta:
        db_table = 'consulta'
        indexes = [
            models.Index(fields=['plan_tratamiento'], name='idx_consulta_plan'),
        ]
    
    # SP3-T009: Métodos para gestión de pagos de consultas
    def calcular_costo_prepago(self):
        """
        Calcula el costo de prepago de la consulta.
        Basado en el tipo de consulta y tarifas configuradas.
        
        Returns:
            Decimal: Costo de prepago (si aplica)
        """
        from decimal import Decimal
        
        # Si el tipo de consulta tiene costo base, retornarlo
        # De lo contrario, retornar 0 (consulta sin prepago)
        if hasattr(self.idtipoconsulta, 'costo_prepago'):
            return Decimal(str(self.idtipoconsulta.costo_prepago or 0))
        
        return Decimal('0')
    
    def calcular_copago(self):
        """
        Calcula el copago adicional de la consulta.
        Puede incluir servicios adicionales o cargos extras.
        
        Returns:
            Decimal: Monto de copago adicional
        """
        from decimal import Decimal
        
        # Por defecto, retorna 0
        # Puede extenderse para incluir servicios adicionales
        return Decimal('0')
    
    def calcular_saldo_pendiente(self):
        """
        Calcula el saldo pendiente de pago de la consulta.
        Saldo = Costo total - Pagos aprobados
        
        Returns:
            Decimal: Saldo pendiente
        """
        from decimal import Decimal
        
        costo_total = self.calcular_costo_prepago() + self.calcular_copago()
        
        # Sumar pagos aprobados para esta consulta
        pagos_aprobados = self.pagos.filter(
            estado='aprobado',
            origen_tipo='consulta'
        )
        
        total_pagado = sum(
            Decimal(str(pago.monto or 0)) 
            for pago in pagos_aprobados
        )
        
        saldo = costo_total - total_pagado
        return max(saldo, Decimal('0'))  # No puede ser negativo
    
    def esta_pagada(self):
        """
        Verifica si la consulta está completamente pagada.
        
        Returns:
            bool: True si el saldo pendiente es 0
        """
        from decimal import Decimal
        return self.calcular_saldo_pendiente() <= Decimal('0')
    
    def requiere_prepago(self):
        """
        Verifica si la consulta requiere prepago.
        
        Returns:
            bool: True si requiere prepago
        """
        from decimal import Decimal
        return self.calcular_costo_prepago() > Decimal('0')
    
    def puede_pagarse(self):
        """
        Verifica si la consulta puede recibir pagos.
        
        Returns:
            tuple: (puede_pagar: bool, razon: str)
        """
        if self.esta_pagada():
            return False, "La consulta ya está completamente pagada"
        
        return True, "La consulta puede recibir pagos"
    
    # PASO 2: Métodos para Flujo Clínico
    def es_consulta_diagnostico(self):
        """
        Determina si esta consulta es una consulta diagnóstica inicial.
        Una consulta diagnóstica no está vinculada a un plan de tratamiento.
        
        Returns:
            bool: True si es consulta diagnóstica
        """
        return self.plan_tratamiento is None
    
    def puede_generar_plan(self):
        """
        Verifica si esta consulta puede generar un plan de tratamiento.
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # Solo consultas diagnósticas pueden generar planes
        if not self.es_consulta_diagnostico():
            return False, "Esta consulta ya está vinculada a un plan de tratamiento"
        
        # Verificar si ya generó un plan
        if hasattr(self, 'plan_generado') and self.plan_generado.exists():
            return False, "Esta consulta ya generó un plan de tratamiento"
        
        # Verificar que esté completada o en proceso
        if self.idestadoconsulta.estado not in ['Completado', 'En Proceso']:
            return False, f"La consulta debe estar completada o en proceso (estado actual: {self.idestadoconsulta.estado})"
        
        # Si requiere pago, verificar que esté pagada
        if self.requiere_pago and not self.esta_pagada():
            return False, "La consulta requiere pago antes de generar el plan"
        
        return True, "La consulta puede generar un plan de tratamiento"
    
    def vincular_plan(self, plan_tratamiento):
        """
        Vincula esta consulta a un plan de tratamiento generado.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
            
        Returns:
            bool: True si se vinculó exitosamente
            
        Raises:
            ValueError: Si no se puede vincular
        """
        puede, mensaje = self.puede_generar_plan()
        if not puede:
            raise ValueError(f"No se puede vincular plan: {mensaje}")
        
        # Establecer la relación bidireccional
        plan_tratamiento.consulta_diagnostico = self
        plan_tratamiento.save()
        
        return True
    
    def get_plan_asociado(self):
        """
        Obtiene el plan de tratamiento asociado a esta consulta.
        
        Returns:
            Plandetratamiento | None: El plan generado por esta consulta (si existe)
        """
        if self.es_consulta_diagnostico():
            # Esta es una consulta diagnóstica, buscar el plan que generó
            return getattr(self, 'plan_generado', None)
        else:
            # Esta es una consulta de ejecución, retornar el plan al que pertenece
            return self.plan_tratamiento
    
    def validar_datos_flujo(self):
        """
        Valida la consistencia de datos del flujo clínico.
        
        Returns:
            tuple: (es_valido: bool, errores: list[str])
        """
        errores = []
        
        # Validar costo_consulta
        if self.costo_consulta < 0:
            errores.append("El costo de consulta no puede ser negativo")
        
        # Validar consistencia requiere_pago vs costo_consulta
        if self.requiere_pago and self.costo_consulta == 0:
            errores.append("Si requiere pago, debe tener un costo_consulta > 0")
        
        # Validar consistencia pago_consulta
        if self.pago_consulta and not self.requiere_pago:
            errores.append("Tiene pago asociado pero no requiere pago")
        
        return len(errores) == 0, errores

    # PASO 4 (PHASE 2): Métodos para Appointment Lifecycle (Opción B - Realista)
    
    def puede_cambiar_estado(self, nuevo_estado, usuario=None):
        """
        Valida si es posible cambiar al nuevo estado según el flujo realista.
        
        Flujo permitido:
        pendiente → confirmada → en_consulta → diagnosticada → con_plan → completada
                  ↓            ↓
              cancelada    no_asistio
        
        Args:
            nuevo_estado: Estado destino
            usuario: Usuario que realiza el cambio (opcional, para auditoría)
            
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        estado_actual = self.estado or 'pendiente'
        
        # Definir transiciones válidas (Opción B - 8 estados)
        TRANSICIONES_VALIDAS = {
            'pendiente': ['confirmada', 'cancelada'],
            'confirmada': ['en_consulta', 'cancelada', 'no_asistio'],
            'en_consulta': ['diagnosticada', 'cancelada'],
            'diagnosticada': ['con_plan', 'completada', 'cancelada'],
            'con_plan': ['completada', 'cancelada'],
            'completada': [],  # Estado final
            'cancelada': [],   # Estado final
            'no_asistio': [],  # Estado final
        }
        
        # Validar si la transición es permitida
        estados_permitidos = TRANSICIONES_VALIDAS.get(estado_actual, [])
        
        if nuevo_estado not in estados_permitidos:
            return False, f"No se puede cambiar de '{estado_actual}' a '{nuevo_estado}'. Estados permitidos: {estados_permitidos}"
        
        # Validaciones específicas por estado
        # NOTA: fecha_consulta, hora_consulta y diagnostico se asignan en sus respectivos
        # métodos (confirmar_cita, registrar_diagnostico), por lo que no validamos aquí
        
        if nuevo_estado == 'en_consulta':
            if not self.motivo_consulta:
                return False, "Debe registrar el motivo de consulta antes de iniciar"
        
        if nuevo_estado == 'completada':
            # Si requiere pago, validar que esté pagada
            if self.requiere_pago and not self.esta_pagada():
                return False, "La consulta requiere estar pagada antes de completarse"
        
        return True, f"Transición válida: {estado_actual} → {nuevo_estado}"
    
    def confirmar_cita(self, fecha_consulta, hora_consulta, usuario=None, notas=None):
        """
        Confirma una cita pendiente asignando fecha y hora.
        
        Args:
            fecha_consulta: Fecha confirmada (date)
            hora_consulta: Hora confirmada (time)
            usuario: Usuario que confirma (para auditoría)
            notas: Notas de la recepcionista (opcional)
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('confirmada', usuario)
        if not puede:
            return False, mensaje
        
        # Asignar fecha y hora
        self.fecha_consulta = fecha_consulta
        self.hora_consulta = hora_consulta
        
        if notas:
            self.notas_recepcion = notas
        
        # Cambiar estado
        self.estado = 'confirmada'
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="CONFIRMAR_CITA",
            detalles=f"Cita confirmada para {fecha_consulta} a las {hora_consulta}"
        )
        
        return True, f"Cita confirmada exitosamente para {fecha_consulta} {hora_consulta}"
    
    def iniciar_consulta(self, usuario=None):
        """
        Inicia la consulta cuando el odontólogo comienza a atender.
        Registra hora de inicio.
        
        Args:
            usuario: Odontólogo que inicia la consulta
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('en_consulta', usuario)
        if not puede:
            return False, mensaje
        
        # Registrar hora de inicio
        self.hora_inicio_consulta = timezone.now()
        self.estado = 'en_consulta'
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="INICIAR_CONSULTA",
            detalles=f"Consulta iniciada a las {self.hora_inicio_consulta.strftime('%H:%M')}"
        )
        
        return True, "Consulta iniciada exitosamente"
    
    def registrar_diagnostico(self, diagnostico, tratamiento=None, usuario=None):
        """
        Registra el diagnóstico del odontólogo.
        
        Args:
            diagnostico: Texto del diagnóstico
            tratamiento: Tratamiento recomendado (opcional)
            usuario: Odontólogo que diagnostica
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('diagnosticada', usuario)
        if not puede:
            return False, mensaje
        
        # Registrar diagnóstico
        self.diagnostico = diagnostico
        if tratamiento:
            self.tratamiento = tratamiento
        
        self.estado = 'diagnosticada'
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="REGISTRAR_DIAGNOSTICO",
            detalles=f"Diagnóstico: {diagnostico[:100]}..."
        )
        
        return True, "Diagnóstico registrado exitosamente"
    
    def marcar_con_plan(self, plan_tratamiento, usuario=None):
        """
        Marca la consulta como 'con_plan' cuando se genera un plan de tratamiento.
        Este método es llamado automáticamente al generar el plan.
        
        Args:
            plan_tratamiento: Plan generado
            usuario: Usuario que genera el plan
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('con_plan', usuario)
        if not puede:
            return False, mensaje
        
        self.estado = 'con_plan'
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="GENERAR_PLAN",
            detalles=f"Plan de tratamiento #{plan_tratamiento.idplan} generado"
        )
        
        return True, "Plan de tratamiento vinculado exitosamente"
    
    def completar_consulta(self, observaciones=None, usuario=None):
        """
        Completa la consulta finalizando el proceso.
        Registra hora de fin.
        
        Args:
            observaciones: Observaciones finales (opcional)
            usuario: Usuario que completa
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('completada', usuario)
        if not puede:
            return False, mensaje
        
        # Registrar hora de fin
        self.hora_fin_consulta = timezone.now()
        
        if observaciones:
            self.observaciones = observaciones
        
        self.estado = 'completada'
        
        # Actualizar estado FK legacy (para compatibilidad)
        try:
            estado_completado = Estadodeconsulta.objects.get(estado='Completado', empresa=self.empresa)
            self.idestadoconsulta = estado_completado
        except Estadodeconsulta.DoesNotExist:
            pass  # Si no existe el estado FK, solo usar CharField
        
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="COMPLETAR_CONSULTA",
            detalles=f"Consulta completada. Duración: {self.get_duracion_consulta()} min"
        )
        
        return True, "Consulta completada exitosamente"
    
    def cancelar_cita(self, motivo_cancelacion, usuario=None):
        """
        Cancela una cita.
        
        Args:
            motivo_cancelacion: Razón de la cancelación
            usuario: Usuario que cancela
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('cancelada', usuario)
        if not puede:
            return False, mensaje
        
        self.motivo_cancelacion = motivo_cancelacion
        self.estado = 'cancelada'
        
        # Actualizar estado FK legacy
        try:
            estado_cancelado = Estadodeconsulta.objects.get(estado='Cancelado', empresa=self.empresa)
            self.idestadoconsulta = estado_cancelado
        except Estadodeconsulta.DoesNotExist:
            pass
        
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="CANCELAR_CITA",
            detalles=f"Motivo: {motivo_cancelacion}"
        )
        
        return True, "Cita cancelada exitosamente"
    
    def marcar_no_asistio(self, usuario=None):
        """
        Marca al paciente como no asistido (no-show).
        Solo puede hacerse desde estado 'confirmada'.
        
        Args:
            usuario: Usuario que registra el no-show
            
        Returns:
            tuple: (exito: bool, mensaje: str)
        """
        puede, mensaje = self.puede_cambiar_estado('no_asistio', usuario)
        if not puede:
            return False, mensaje
        
        self.estado = 'no_asistio'
        
        # Actualizar estado FK legacy
        try:
            estado_no_asistio = Estadodeconsulta.objects.get(estado='No Asistió', empresa=self.empresa)
            self.idestadoconsulta = estado_no_asistio
        except Estadodeconsulta.DoesNotExist:
            pass
        
        self.save()
        
        # Auditoría
        self._crear_auditoria(
            usuario=usuario,
            accion="MARCAR_NO_ASISTIO",
            detalles="Paciente no se presentó a la cita"
        )
        
        # Aquí se activarán las políticas de no-show automáticamente (signals)
        
        return True, "Paciente marcado como no asistido"
    
    def get_duracion_consulta(self):
        """
        Calcula la duración real de la consulta en minutos.
        
        Returns:
            int | None: Duración en minutos o None si no está completa
        """
        if self.hora_inicio_consulta and self.hora_fin_consulta:
            duracion = self.hora_fin_consulta - self.hora_inicio_consulta
            return int(duracion.total_seconds() / 60)
        return None
    
    def get_tiempo_espera(self):
        """
        Calcula el tiempo de espera del paciente (entre llegada e inicio).
        
        Returns:
            int | None: Tiempo en minutos o None si no aplica
        """
        if self.hora_llegada and self.hora_inicio_consulta:
            espera = self.hora_inicio_consulta - self.hora_llegada
            return int(espera.total_seconds() / 60)
        return None
    
    def _crear_auditoria(self, usuario, accion, detalles):
        """
        Crea un registro en Bitacora para auditoría.
        
        Args:
            usuario: Usuario que realiza la acción
            accion: Tipo de acción
            detalles: Descripción detallada
        """
        try:
            Bitacora.objects.create(
                empresa=self.empresa,
                usuario=usuario,
                accion=accion,
                tabla_afectada='consulta',
                registro_id=self.id,  # Consulta usa 'id' como PK, no 'idconsulta'
                detalles=detalles
            )
        except Exception as e:
            # No fallar la operación principal por error de auditoría
            print(f"⚠️ Error al crear auditoría: {e}")


class Tipodeconsulta(models.Model):
    nombreconsulta = models.CharField(max_length=255)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='tipos_consulta', null=True, blank=True)
    
    # =========================================
    # NUEVOS CAMPOS: Agendamiento Web (Frontend Request)
    # =========================================
    
    # Campo 1: Control de agendamiento web
    permite_agendamiento_web = models.BooleanField(
        default=False,
        db_column='permite_agendamiento_web',
        help_text="¿Los pacientes pueden agendar este tipo de consulta desde la web?"
    )
    
    # Campo 2: Requiere aprobación de staff
    requiere_aprobacion = models.BooleanField(
        default=False,
        db_column='requiere_aprobacion',
        help_text="¿Requiere aprobación de staff antes de confirmar?"
    )
    
    # Campo 3: Marcador de urgencia
    es_urgencia = models.BooleanField(
        default=False,
        db_column='es_urgencia',
        help_text="¿Es un tipo de consulta urgente? (prioridad alta, notificación inmediata)"
    )
    
    # Campo 4: Duración estimada (para gestión de agenda)
    duracion_estimada = models.IntegerField(
        default=30,
        db_column='duracion_estimada',
        help_text="Duración estimada de la consulta en minutos"
    )

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
    
    # NUEVOS CAMPOS: Flujo Clínico (Paso 1)
    consulta_diagnostico = models.ForeignKey(
        'Consulta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planes_generados',
        help_text="Consulta de diagnóstico que originó este plan"
    )
    estado_tratamiento = models.CharField(
        max_length=20,
        choices=[
            ('Propuesto', 'Propuesto (Pendiente de aceptación)'),
            ('Aceptado', 'Aceptado por paciente'),
            ('En Ejecución', 'En ejecución'),
            ('Completado', 'Completado'),
            ('Cancelado', 'Cancelado'),
            ('Pausado', 'Pausado'),
        ],
        default='Propuesto',
        help_text="Estado actual del plan de tratamiento"
    )
    fecha_inicio_ejecucion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha en que comenzó la ejecución (primer servicio)"
    )
    fecha_finalizacion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha de finalización del plan completo"
    )
    
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
        indexes = [
            models.Index(fields=['consulta_diagnostico'], name='idx_plan_consulta'),
            models.Index(fields=['estado_tratamiento'], name='idx_plan_estado_trat'),
        ]
    
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
    
    # SP3-T009: Métodos para gestión de pagos
    def calcular_total_pagado(self):
        """
        Calcula el total de pagos aprobados realizados para este plan.
        Solo cuenta pagos con estado 'aprobado'.
        
        Returns:
            Decimal: Monto total pagado
        """
        from decimal import Decimal
        
        pagos_aprobados = self.pagos.filter(
            estado='aprobado',
            origen_tipo='plan_completo'
        )
        
        total_pagado = sum(
            Decimal(str(pago.monto or 0)) 
            for pago in pagos_aprobados
        )
        
        return total_pagado
    
    def calcular_saldo_pendiente(self):
        """
        Calcula el saldo pendiente de pago del plan.
        Saldo = Total del plan - Pagos aprobados
        
        Returns:
            Decimal: Saldo pendiente de pago
        """
        from decimal import Decimal
        
        total_plan = Decimal(str(self.montototal or 0))
        total_pagado = self.calcular_total_pagado()
        
        saldo = total_plan - total_pagado
        return max(saldo, Decimal('0'))  # No puede ser negativo
    
    def puede_pagar_completo(self):
        """
        Verifica si el plan puede ser pagado en su totalidad.
        Criterios:
        - Plan debe estar aprobado
        - Debe tener saldo pendiente
        - No debe estar cancelado
        
        Returns:
            tuple: (puede_pagar: bool, razon: str)
        """
        if self.estado_plan != self.ESTADO_PLAN_APROBADO:
            return False, "El plan debe estar aprobado para realizar pagos"
        
        if self.estado_plan == self.ESTADO_PLAN_CANCELADO:
            return False, "No se pueden realizar pagos en un plan cancelado"
        
        saldo = self.calcular_saldo_pendiente()
        if saldo <= 0:
            return False, "El plan ya está completamente pagado"
        
        return True, "El plan puede ser pagado"
    
    def bloquear_items_pagados(self):
        """
        Bloquea la edición/eliminación de items que tienen pagos asociados.
        Se ejecuta automáticamente cuando se aprueba un pago.
        
        Marca items con pagos aprobados como 'bloqueados' para edición.
        """
        from decimal import Decimal
        
        # Obtener items con pagos aprobados
        items_con_pagos = self.itemplandetratamiento_set.filter(
            detalles_pago__pago__estado='aprobado'
        ).distinct()
        
        # Marcar como no editables (via notas_item o campo futuro)
        for item in items_con_pagos:
            monto_pagado = item.calcular_monto_pagado()
            if monto_pagado > Decimal('0'):
                # Actualizar notas para indicar bloqueo por pagos
                nota_bloqueo = f"[BLOQUEADO POR PAGO: ${monto_pagado}]"
                if not item.notas_item:
                    item.notas_item = nota_bloqueo
                elif nota_bloqueo not in item.notas_item:
                    item.notas_item = f"{nota_bloqueo}\n{item.notas_item}"
                item.save(update_fields=['notas_item'])
        
        return items_con_pagos.count()
    
    # PASO 2: Métodos para Flujo Clínico - Gestión de Estado de Tratamiento
    def puede_iniciar_ejecucion(self):
        """
        Verifica si el plan puede iniciar su ejecución.
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # Debe estar en estado Aceptado
        if self.estado_tratamiento != 'Aceptado':
            return False, f"El plan debe estar Aceptado (estado actual: {self.estado_tratamiento})"
        
        # Debe tener items
        if not self.itemplandetratamiento_set.exists():
            return False, "El plan no tiene items para ejecutar"
        
        # Verificar si ya está pagado (si es necesario)
        if hasattr(self, 'requiere_pago_completo') and self.requiere_pago_completo:
            from decimal import Decimal
            if self.calcular_saldo_pendiente() > Decimal('0'):
                return False, "El plan requiere pago completo antes de iniciar"
        
        return True, "El plan puede iniciar su ejecución"
    
    def iniciar_ejecucion(self):
        """
        Inicia la ejecución del plan de tratamiento.
        Cambia el estado a 'En Ejecución' y registra la fecha.
        
        Returns:
            bool: True si se inició exitosamente
            
        Raises:
            ValueError: Si no se puede iniciar
        """
        puede, mensaje = self.puede_iniciar_ejecucion()
        if not puede:
            raise ValueError(f"No se puede iniciar ejecución: {mensaje}")
        
        from django.utils import timezone
        self.estado_tratamiento = 'En Ejecución'
        self.fecha_inicio_ejecucion = timezone.now()
        self.save(update_fields=['estado_tratamiento', 'fecha_inicio_ejecucion'])
        
        return True
    
    def puede_completarse(self):
        """
        Verifica si el plan puede marcarse como completado.
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # Debe estar en ejecución
        if self.estado_tratamiento != 'En Ejecución':
            return False, f"El plan debe estar En Ejecución (estado actual: {self.estado_tratamiento})"
        
        # Todos los items activos deben estar completados
        items_activos = self.itemplandetratamiento_set.filter(estado_item='Activo')
        items_pendientes = items_activos.exclude(fecha_ejecucion__isnull=False)
        
        if items_pendientes.exists():
            count = items_pendientes.count()
            return False, f"Quedan {count} item(s) sin ejecutar"
        
        return True, "Todos los items están completados"
    
    def marcar_completado(self):
        """
        Marca el plan como completado.
        Verifica que todos los items estén ejecutados.
        
        Returns:
            bool: True si se completó exitosamente
            
        Raises:
            ValueError: Si no se puede completar
        """
        puede, mensaje = self.puede_completarse()
        if not puede:
            raise ValueError(f"No se puede completar el plan: {mensaje}")
        
        from django.utils import timezone
        self.estado_tratamiento = 'Completado'
        self.fecha_finalizacion = timezone.now()
        self.save(update_fields=['estado_tratamiento', 'fecha_finalizacion'])
        
        return True
    
    def cancelar(self, motivo=None):
        """
        Cancela el plan de tratamiento.
        
        Args:
            motivo: Motivo de cancelación (opcional)
            
        Returns:
            bool: True si se canceló exitosamente
        """
        # No se puede cancelar si ya está completado
        if self.estado_tratamiento == 'Completado':
            raise ValueError("No se puede cancelar un plan completado")
        
        self.estado_tratamiento = 'Cancelado'
        
        # Registrar motivo en notas
        if motivo:
            from django.utils import timezone
            nota_cancelacion = f"\n[CANCELADO {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {motivo}"
            if self.notas_plan:
                self.notas_plan += nota_cancelacion
            else:
                self.notas_plan = nota_cancelacion
        
        self.save(update_fields=['estado_tratamiento', 'notas_plan'])
        return True
    
    def pausar(self, motivo=None):
        """
        Pausa el plan de tratamiento.
        
        Args:
            motivo: Motivo de pausa (opcional)
            
        Returns:
            bool: True si se pausó exitosamente
        """
        if self.estado_tratamiento != 'En Ejecución':
            raise ValueError("Solo se pueden pausar planes En Ejecución")
        
        self.estado_tratamiento = 'Pausado'
        
        # Registrar motivo en notas
        if motivo:
            from django.utils import timezone
            nota_pausa = f"\n[PAUSADO {timezone.now().strftime('%Y-%m-%d %H:%M')}]: {motivo}"
            if self.notas_plan:
                self.notas_plan += nota_pausa
            else:
                self.notas_plan = nota_pausa
        
        self.save(update_fields=['estado_tratamiento', 'notas_plan'])
        return True
    
    def reanudar(self):
        """
        Reanuda un plan pausado.
        
        Returns:
            bool: True si se reanudó exitosamente
        """
        if self.estado_tratamiento != 'Pausado':
            raise ValueError("Solo se pueden reanudar planes Pausados")
        
        from django.utils import timezone
        self.estado_tratamiento = 'En Ejecución'
        
        # Registrar reanudación en notas
        nota_reanudacion = f"\n[REANUDADO {timezone.now().strftime('%Y-%m-%d %H:%M')}]"
        if self.notas_plan:
            self.notas_plan += nota_reanudacion
        else:
            self.notas_plan = nota_reanudacion
        
        self.save(update_fields=['estado_tratamiento', 'notas_plan'])
        return True
    
    def puede_modificar_items(self):
        """
        Verifica si se pueden agregar/eliminar/modificar items del plan.
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # No se puede modificar si está Completado
        if self.estado_tratamiento == 'Completado':
            return False, "No se pueden modificar items de un plan Completado"
        
        # No se puede modificar si está Cancelado
        if self.estado_tratamiento == 'Cancelado':
            return False, "No se pueden modificar items de un plan Cancelado"
        
        # Durante ejecución, solo se pueden agregar items, no eliminar
        if self.estado_tratamiento == 'En Ejecución':
            return True, "Durante ejecución solo se pueden agregar items (no eliminar)"
        
        return True, "Se pueden modificar items libremente"
    
    def calcular_progreso_ejecucion(self):
        """
        Calcula el progreso de ejecución del plan basado en items ejecutados.
        
        Returns:
            float: Porcentaje de progreso (0-100)
        """
        items_activos = self.itemplandetratamiento_set.filter(estado_item='Activo')
        total_items = items_activos.count()
        
        if total_items == 0:
            return 0.0
        
        items_ejecutados = items_activos.filter(fecha_ejecucion__isnull=False).count()
        
        return (items_ejecutados / total_items) * 100
    
    def get_siguiente_item_por_ejecutar(self):
        """
        Obtiene el siguiente item pendiente según orden_ejecucion.
        
        Returns:
            Itemplandetratamiento | None: Siguiente item o None si no hay pendientes
        """
        return self.itemplandetratamiento_set.filter(
            estado_item='Activo',
            fecha_ejecucion__isnull=True
        ).order_by('orden_ejecucion', 'id').first()
    
    def validar_consistencia_flujo(self):
        """
        Valida la consistencia del estado del plan con sus datos.
        
        Returns:
            tuple: (es_valido: bool, errores: list[str])
        """
        errores = []
        
        # Validar fecha_inicio_ejecucion
        if self.estado_tratamiento in ['En Ejecución', 'Completado', 'Pausado']:
            if not self.fecha_inicio_ejecucion:
                errores.append(f"Plan en estado '{self.estado_tratamiento}' debe tener fecha_inicio_ejecucion")
        
        # Validar fecha_finalizacion
        if self.estado_tratamiento == 'Completado':
            if not self.fecha_finalizacion:
                errores.append("Plan Completado debe tener fecha_finalizacion")
        
        # Validar consulta_diagnostico
        if not self.consulta_diagnostico:
            errores.append("Plan debe tener una consulta_diagnostico asociada")
        
        # Validar que consultas de ejecución estén vinculadas al plan
        consultas_ejecucion = self.consultas_ejecucion.all()
        for consulta in consultas_ejecucion:
            if consulta.plan_tratamiento != self:
                errores.append(f"Consulta {consulta.id} tiene inconsistencia de vinculación")
        
        return len(errores) == 0, errores


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
    
    # NUEVOS CAMPOS: Flujo Clínico (Paso 1)
    consulta_ejecucion = models.ForeignKey(
        'Consulta',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items_ejecutados',
        help_text="Consulta en la que se ejecutó este item"
    )
    fecha_ejecucion = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Fecha y hora en que se ejecutó el servicio"
    )
    odontologo_ejecutor = models.ForeignKey(
        'Odontologo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items_ejecutados',
        help_text="Odontólogo que ejecutó este servicio"
    )
    orden_ejecucion = models.PositiveIntegerField(
        default=1,
        help_text="Orden sugerido de ejecución (1, 2, 3...)"
    )
    notas_ejecucion = models.TextField(
        blank=True,
        null=True,
        help_text="Notas del odontólogo al ejecutar el servicio"
    )
    
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
        indexes = [
            models.Index(fields=['consulta_ejecucion'], name='idx_item_consulta'),
            models.Index(fields=['estado_item'], name='idx_item_estado'),
        ]
    
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
    
    # SP3-T009: Métodos para gestión de pagos de items
    def calcular_monto_pagado(self):
        """
        Calcula el monto total pagado para este item específico.
        Suma todos los pagos aprobados asociados a este item.
        
        Returns:
            Decimal: Monto total pagado para este item
        """
        from decimal import Decimal
        
        detalles_aprobados = self.detalles_pago.filter(
            pago__estado='aprobado'
        )
        
        total_pagado = sum(
            Decimal(str(detalle.monto_pagado_ahora or 0)) 
            for detalle in detalles_aprobados
        )
        
        return total_pagado
    
    def calcular_saldo_pendiente(self):
        """
        Calcula el saldo pendiente de pago para este item.
        Saldo = Costo final del item - Pagos aprobados
        
        Returns:
            Decimal: Saldo pendiente del item
        """
        from decimal import Decimal
        
        costo_total = Decimal(str(self.costofinal or 0))
        monto_pagado = self.calcular_monto_pagado()
        
        saldo = costo_total - monto_pagado
        return max(saldo, Decimal('0'))  # No puede ser negativo
    
    def esta_pagado(self):
        """
        Verifica si el item está completamente pagado.
        
        Returns:
            bool: True si el saldo pendiente es 0
        """
        from decimal import Decimal
        return self.calcular_saldo_pendiente() <= Decimal('0')
    
    def puede_pagarse(self):
        """
        Verifica si el item puede recibir pagos.
        Criterios:
        - Item debe estar activo o completado (no cancelado)
        - Debe tener saldo pendiente
        - El plan padre debe estar aprobado
        
        Returns:
            tuple: (puede_pagar: bool, razon: str)
        """
        if self.esta_cancelado():
            return False, "No se pueden realizar pagos en items cancelados"
        
        if not self.idplantratamiento.es_aprobado():
            return False, "El plan debe estar aprobado para realizar pagos"
        
        if self.esta_pagado():
            return False, "El item ya está completamente pagado"
        
        return True, "El item puede recibir pagos"
    
    def calcular_porcentaje_pagado(self):
        """
        Calcula el porcentaje del item que ha sido pagado.
        
        Returns:
            Decimal: Porcentaje pagado (0-100)
        """
        from decimal import Decimal
        
        costo_total = Decimal(str(self.costofinal or 0))
        if costo_total <= 0:
            return Decimal('0')
        
        monto_pagado = self.calcular_monto_pagado()
        porcentaje = (monto_pagado / costo_total) * Decimal('100')
        
        return min(porcentaje, Decimal('100'))  # Max 100%
    
    # PASO 2: Métodos para Flujo Clínico - Ejecución de Items
    def puede_ejecutarse(self):
        """
        Verifica si este item puede ejecutarse en una consulta.
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # El plan debe estar en ejecución o aceptado
        plan_estado = self.idplantratamiento.estado_tratamiento
        if plan_estado not in ['Aceptado', 'En Ejecución']:
            return False, f"El plan debe estar Aceptado o En Ejecución (estado actual: {plan_estado})"
        
        # El item debe estar activo
        if not self.esta_activo():
            return False, f"El item debe estar Activo (estado actual: {self.estado_item})"
        
        # No debe haber sido ejecutado ya
        if self.fecha_ejecucion is not None:
            return False, "El item ya fue ejecutado"
        
        # Verificar orden de ejecución (opcional - puede flexibilizarse)
        items_previos_pendientes = self.idplantratamiento.itemplandetratamiento_set.filter(
            estado_item='Activo',
            orden_ejecucion__lt=self.orden_ejecucion,
            fecha_ejecucion__isnull=True
        ).exclude(id=self.id)
        
        if items_previos_pendientes.exists():
            count = items_previos_pendientes.count()
            return False, f"Hay {count} item(s) con menor orden de ejecución pendientes"
        
        return True, "El item puede ejecutarse"
    
    def ejecutar_en_consulta(self, consulta, odontologo, notas=None):
        """
        Ejecuta este item en una consulta específica.
        Registra la ejecución con fecha, odontólogo y notas.
        
        Args:
            consulta: Instancia de Consulta donde se ejecuta
            odontologo: Instancia de Odontologo que ejecuta
            notas: Notas de ejecución (opcional)
            
        Returns:
            bool: True si se ejecutó exitosamente
            
        Raises:
            ValueError: Si no se puede ejecutar
        """
        puede, mensaje = self.puede_ejecutarse()
        if not puede:
            raise ValueError(f"No se puede ejecutar el item: {mensaje}")
        
        # Verificar que la consulta pertenece al plan
        if consulta.plan_tratamiento != self.idplantratamiento:
            raise ValueError("La consulta no pertenece al plan de este item")
        
        from django.utils import timezone
        
        # Registrar ejecución
        self.consulta_ejecucion = consulta
        self.fecha_ejecucion = timezone.now()
        self.odontologo_ejecutor = odontologo
        
        if notas:
            self.notas_ejecucion = notas
        
        self.save(update_fields=['consulta_ejecucion', 'fecha_ejecucion', 'odontologo_ejecutor', 'notas_ejecucion'])
        
        # Verificar si el plan debe iniciar ejecución automáticamente
        if self.idplantratamiento.estado_tratamiento == 'Aceptado':
            self.idplantratamiento.iniciar_ejecucion()
        
        return True
    
    def marcar_ejecutado(self, odontologo, notas=None):
        """
        Marca el item como ejecutado sin vincularlo a una consulta específica.
        Útil para casos donde no se registró la consulta previamente.
        
        Args:
            odontologo: Instancia de Odontologo que ejecutó
            notas: Notas de ejecución (opcional)
            
        Returns:
            bool: True si se marcó exitosamente
        """
        # El item debe estar activo
        if not self.esta_activo():
            raise ValueError(f"Solo items Activos pueden marcarse como ejecutados (estado actual: {self.estado_item})")
        
        # No debe haber sido ejecutado ya
        if self.fecha_ejecucion is not None:
            raise ValueError("El item ya fue ejecutado")
        
        from django.utils import timezone
        
        self.fecha_ejecucion = timezone.now()
        self.odontologo_ejecutor = odontologo
        
        if notas:
            self.notas_ejecucion = notas
        
        self.save(update_fields=['fecha_ejecucion', 'odontologo_ejecutor', 'notas_ejecucion'])
        
        # Verificar si el plan debe iniciar ejecución automáticamente
        if self.idplantratamiento.estado_tratamiento == 'Aceptado':
            self.idplantratamiento.iniciar_ejecucion()
        
        return True
    
    def esta_ejecutado(self):
        """
        Verifica si el item ha sido ejecutado.
        
        Returns:
            bool: True si tiene fecha_ejecucion
        """
        return self.fecha_ejecucion is not None
    
    def puede_reprogramarse(self):
        """
        Verifica si el item puede reprogramarse (cambiar su orden_ejecucion).
        
        Returns:
            tuple: (puede: bool, mensaje: str)
        """
        # No se puede reprogramar si ya fue ejecutado
        if self.esta_ejecutado():
            return False, "No se puede reprogramar un item ya ejecutado"
        
        # El plan debe permitir modificaciones
        puede_modificar, msg = self.idplantratamiento.puede_modificar_items()
        if not puede_modificar:
            return False, msg
        
        return True, "El item puede reprogramarse"
    
    def reprogramar_orden(self, nuevo_orden):
        """
        Cambia el orden de ejecución del item.
        
        Args:
            nuevo_orden: Nuevo valor para orden_ejecucion
            
        Returns:
            bool: True si se reprogramó exitosamente
            
        Raises:
            ValueError: Si no se puede reprogramar
        """
        puede, mensaje = self.puede_reprogramarse()
        if not puede:
            raise ValueError(f"No se puede reprogramar: {mensaje}")
        
        if nuevo_orden < 1:
            raise ValueError("El orden debe ser mayor o igual a 1")
        
        self.orden_ejecucion = nuevo_orden
        self.save(update_fields=['orden_ejecucion'])
        
        return True
    
    def validar_datos_ejecucion(self):
        """
        Valida la consistencia de los datos de ejecución.
        
        Returns:
            tuple: (es_valido: bool, errores: list[str])
        """
        errores = []
        
        # Si tiene fecha_ejecucion, debe tener odontologo_ejecutor
        if self.fecha_ejecucion and not self.odontologo_ejecutor:
            errores.append("Item ejecutado debe tener odontólogo ejecutor")
        
        # Si tiene consulta_ejecucion, debe tener fecha_ejecucion
        if self.consulta_ejecucion and not self.fecha_ejecucion:
            errores.append("Item con consulta de ejecución debe tener fecha de ejecución")
        
        # Validar consistencia de consulta_ejecucion con el plan
        if self.consulta_ejecucion:
            if self.consulta_ejecucion.plan_tratamiento != self.idplantratamiento:
                errores.append("La consulta de ejecución no pertenece al plan de este item")
        
        # Validar orden_ejecucion
        if self.orden_ejecucion < 1:
            errores.append("El orden de ejecución debe ser mayor o igual a 1")
        
        return len(errores) == 0, errores
    
    def get_tiempo_transcurrido_desde_ejecucion(self):
        """
        Obtiene el tiempo transcurrido desde la ejecución.
        
        Returns:
            timedelta | None: Tiempo transcurrido o None si no está ejecutado
        """
        if not self.fecha_ejecucion:
            return None
        
        from django.utils import timezone
        return timezone.now() - self.fecha_ejecucion


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


# ============================================================================
# SISTEMA DE PAGOS EN LÍNEA - SP3-T009
# ============================================================================

class PagoEnLinea(models.Model):
    """
    Modelo para gestionar pagos en línea de tratamientos y consultas.
    Integra con pasarela de pagos (Stripe) y gestiona estados de transacción.
    
    SP3-T009: Realizar pago en línea (web)
    """
    
    # Tipos de origen del pago
    ORIGEN_PLAN_COMPLETO = 'plan_completo'
    ORIGEN_ITEMS_INDIVIDUALES = 'items_individuales'
    ORIGEN_CONSULTA = 'consulta'
    
    ORIGEN_CHOICES = [
        (ORIGEN_PLAN_COMPLETO, 'Plan de Tratamiento Completo'),
        (ORIGEN_ITEMS_INDIVIDUALES, 'Ítems Individuales del Plan'),
        (ORIGEN_CONSULTA, 'Consulta/Cita'),
    ]
    
    # Tipos de pago para consultas
    TIPO_PAGO_CONSULTA_PREPAGO = 'prepago'
    TIPO_PAGO_CONSULTA_COPAGO = 'copago'
    TIPO_PAGO_CONSULTA_SALDO = 'saldo_pendiente'
    
    TIPO_PAGO_CONSULTA_CHOICES = [
        (TIPO_PAGO_CONSULTA_PREPAGO, 'Prepago (Adelanto)'),
        (TIPO_PAGO_CONSULTA_COPAGO, 'Copago (Pago Parcial)'),
        (TIPO_PAGO_CONSULTA_SALDO, 'Saldo Pendiente'),
    ]
    
    # Estados del pago
    ESTADO_PENDIENTE = 'pendiente'
    ESTADO_PROCESANDO = 'procesando'
    ESTADO_APROBADO = 'aprobado'
    ESTADO_RECHAZADO = 'rechazado'
    ESTADO_CANCELADO = 'cancelado'
    ESTADO_REEMBOLSADO = 'reembolsado'
    ESTADO_ANULADO = 'anulado'
    
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_PROCESANDO, 'Procesando'),
        (ESTADO_APROBADO, 'Aprobado'),
        (ESTADO_RECHAZADO, 'Rechazado'),
        (ESTADO_CANCELADO, 'Cancelado'),
        (ESTADO_REEMBOLSADO, 'Reembolsado'),
        (ESTADO_ANULADO, 'Anulado'),
    ]
    
    # Métodos de pago
    METODO_TARJETA = 'tarjeta'
    METODO_TRANSFERENCIA = 'transferencia'
    METODO_QR = 'qr'
    
    METODO_CHOICES = [
        (METODO_TARJETA, 'Tarjeta de Crédito/Débito'),
        (METODO_TRANSFERENCIA, 'Transferencia Bancaria'),
        (METODO_QR, 'Código QR'),
    ]
    
    # ========== Información del Pago ==========
    codigo_pago = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único del pago (ej: PAY-2025-001234)"
    )
    
    # Origen del pago
    origen_tipo = models.CharField(
        max_length=30,
        choices=ORIGEN_CHOICES,
        help_text="Tipo de origen: plan completo, ítems o consulta"
    )
    tipo_pago_consulta = models.CharField(
        max_length=20,
        choices=TIPO_PAGO_CONSULTA_CHOICES,
        null=True,
        blank=True,
        help_text="Tipo específico de pago para consultas"
    )
    
    # Relaciones con orígenes
    plan_tratamiento = models.ForeignKey(
        Plandetratamiento,
        on_delete=models.PROTECT,
        related_name='pagos',
        null=True,
        blank=True,
        help_text="Plan de tratamiento si el origen es plan"
    )
    consulta = models.ForeignKey(
        'Consulta',
        on_delete=models.PROTECT,
        related_name='pagos',
        null=True,
        blank=True,
        help_text="Consulta si el origen es cita"
    )
    
    # ========== Montos ==========
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total del pago"
    )
    moneda = models.CharField(
        max_length=3,
        default='BOB',
        help_text="Código de moneda (BOB, USD, etc.)"
    )
    monto_original = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto original del origen (para cálculo de saldo)"
    )
    saldo_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Saldo pendiente antes de este pago"
    )
    saldo_nuevo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Saldo pendiente después de este pago"
    )
    
    # ========== Estado y Método ==========
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_PENDIENTE,
        help_text="Estado actual del pago"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODO_CHOICES,
        default=METODO_TARJETA,
        help_text="Método de pago utilizado"
    )
    
    # ========== Integración con Stripe ==========
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        unique=True,
        help_text="ID del Payment Intent en Stripe"
    )
    stripe_charge_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID del Charge en Stripe"
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID del Customer en Stripe"
    )
    stripe_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Metadata adicional de Stripe"
    )
    
    # ========== Detalles de Transacción ==========
    descripcion = models.TextField(
        help_text="Descripción del pago"
    )
    motivo_rechazo = models.TextField(
        null=True,
        blank=True,
        help_text="Motivo de rechazo si el pago falla"
    )
    numero_intentos = models.IntegerField(
        default=0,
        help_text="Número de intentos de pago realizados"
    )
    ultimo_intento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora del último intento"
    )
    
    # ========== Datos de Auditoría ==========
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP desde donde se realizó el pago"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        help_text="User agent del navegador"
    )
    
    # ========== Relaciones ==========
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='pagos_realizados',
        help_text="Usuario que realizó el pago (paciente)"
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='pagos_en_linea',
        help_text="Empresa (tenant) dueña del pago"
    )
    factura = models.ForeignKey(
        Factura,
        on_delete=models.SET_NULL,
        related_name='pagos_en_linea',
        null=True,
        blank=True,
        help_text="Factura generada tras el pago (si aplica)"
    )
    
    # ========== Timestamps ==========
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de creación del registro de pago"
    )
    fecha_procesamiento = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se procesó el pago"
    )
    fecha_aprobacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha en que se aprobó el pago"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Última actualización del registro"
    )
    
    class Meta:
        db_table = 'pago_en_linea'
        ordering = ['-fecha_creacion']
        verbose_name = 'Pago en Línea'
        verbose_name_plural = 'Pagos en Línea'
        indexes = [
            models.Index(fields=['empresa', '-fecha_creacion']),
            models.Index(fields=['estado', '-fecha_creacion']),
            models.Index(fields=['usuario', '-fecha_creacion']),
            models.Index(fields=['plan_tratamiento']),
            models.Index(fields=['consulta']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(monto__gt=0),
                name='pago_monto_positivo',
                violation_error_message="El monto debe ser mayor a 0"
            ),
            models.CheckConstraint(
                check=models.Q(saldo_nuevo__gte=0),
                name='pago_saldo_no_negativo',
                violation_error_message="El saldo nuevo no puede ser negativo"
            ),
        ]
    
    def __str__(self):
        return f"{self.codigo_pago} - {self.get_origen_tipo_display()} - {self.monto} {self.moneda} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        """Generar código único si no existe"""
        if not self.codigo_pago:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            # Contar pagos del día para el sufijo
            count = PagoEnLinea.objects.filter(
                fecha_creacion__date=datetime.now().date()
            ).count() + 1
            self.codigo_pago = f"PAY-{timestamp}-{count:04d}"
        
        super().save(*args, **kwargs)
    
    def esta_pendiente(self):
        """Verifica si el pago está pendiente"""
        return self.estado == self.ESTADO_PENDIENTE
    
    def esta_aprobado(self):
        """Verifica si el pago fue aprobado"""
        return self.estado == self.ESTADO_APROBADO
    
    def puede_reintentarse(self):
        """Verifica si se puede reintentar el pago"""
        return self.estado in [self.ESTADO_RECHAZADO, self.ESTADO_CANCELADO] and self.numero_intentos < 3
    
    def puede_anularse(self):
        """Verifica si el pago puede anularse"""
        return self.estado in [self.ESTADO_PENDIENTE, self.ESTADO_PROCESANDO]
    
    def puede_reembolsarse(self):
        """Verifica si el pago puede reembolsarse"""
        return self.estado == self.ESTADO_APROBADO


class DetallePagoItem(models.Model):
    """
    Desglose de pago por ítem individual cuando se paga parcialmente un plan.
    Permite rastrear qué ítems fueron pagados y cuánto se pagó de cada uno.
    
    SP3-T009: Detalle de pagos por ítem
    """
    
    pago = models.ForeignKey(
        PagoEnLinea,
        on_delete=models.CASCADE,
        related_name='detalles_items',
        help_text="Pago al que pertenece este detalle"
    )
    item_plan = models.ForeignKey(
        Itemplandetratamiento,
        on_delete=models.PROTECT,
        related_name='detalles_pago',
        help_text="Ítem del plan de tratamiento"
    )
    
    # Montos
    monto_item_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Costo total del ítem"
    )
    monto_pagado_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monto pagado del ítem antes de este pago"
    )
    monto_pagado_ahora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto pagado del ítem en este pago"
    )
    monto_pagado_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monto total pagado del ítem tras este pago"
    )
    saldo_restante = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Saldo pendiente del ítem tras este pago"
    )
    
    # Estado
    item_completamente_pagado = models.BooleanField(
        default=False,
        help_text="Indica si el ítem quedó completamente pagado"
    )
    
    # Auditoría
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de registro del detalle"
    )
    
    class Meta:
        db_table = 'detalle_pago_item'
        ordering = ['pago', 'item_plan']
        verbose_name = 'Detalle de Pago por Ítem'
        verbose_name_plural = 'Detalles de Pago por Ítem'
        indexes = [
            models.Index(fields=['pago']),
            models.Index(fields=['item_plan']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['pago', 'item_plan'],
                name='unique_pago_item',
                violation_error_message="Ya existe un detalle para este ítem en este pago"
            ),
            models.CheckConstraint(
                check=models.Q(monto_pagado_ahora__gt=0),
                name='detalle_monto_positivo',
                violation_error_message="El monto pagado debe ser mayor a 0"
            ),
            models.CheckConstraint(
                check=models.Q(saldo_restante__gte=0),
                name='detalle_saldo_no_negativo',
                violation_error_message="El saldo restante no puede ser negativo"
            ),
        ]
    
    def __str__(self):
        servicio = self.item_plan.idservicio.nombre if self.item_plan.idservicio else "N/A"
        return f"{self.pago.codigo_pago} - {servicio} - {self.monto_pagado_ahora}"
    
    def calcular_porcentaje_pagado(self):
        """Calcula el porcentaje pagado del ítem"""
        if self.monto_item_total > 0:
            return (float(self.monto_pagado_total) / float(self.monto_item_total)) * 100
        return 0


class ComprobanteDigital(models.Model):
    """
    Comprobante digital de pago.
    Se genera automáticamente tras la aprobación de un pago.
    
    SP3-T009: Comprobantes digitales de pago
    """
    
    # Estados del comprobante
    ESTADO_ACTIVO = 'activo'
    ESTADO_ANULADO = 'anulado'
    
    ESTADO_CHOICES = [
        (ESTADO_ACTIVO, 'Activo'),
        (ESTADO_ANULADO, 'Anulado'),
    ]
    
    pago = models.OneToOneField(
        PagoEnLinea,
        on_delete=models.CASCADE,
        related_name='comprobante',
        help_text="Pago asociado a este comprobante"
    )
    
    # Identificación
    codigo_comprobante = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único del comprobante (ej: COMP-2025-001234)"
    )
    codigo_verificacion = models.CharField(
        max_length=64,
        unique=True,
        help_text="Código de verificación (hash SHA256)"
    )
    
    # Archivo PDF
    archivo_pdf = models.FileField(
        upload_to='comprobantes/pagos/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text="Archivo PDF del comprobante"
    )
    url_publica = models.URLField(
        max_length=500,
        null=True,
        blank=True,
        help_text="URL pública para acceder al comprobante"
    )
    
    # Estado y vigencia
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default=ESTADO_ACTIVO,
        help_text="Estado del comprobante"
    )
    fecha_emision = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha de emisión del comprobante"
    )
    fecha_anulacion = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de anulación (si aplica)"
    )
    motivo_anulacion = models.TextField(
        null=True,
        blank=True,
        help_text="Motivo de anulación"
    )
    
    # Datos adicionales del comprobante (JSON)
    datos_comprobante = models.JSONField(
        default=dict,
        help_text="Datos adicionales del comprobante (paciente, detalles, etc.)"
    )
    
    # Auditoría
    enviado_email = models.BooleanField(
        default=False,
        help_text="Indica si se envió por email"
    )
    fecha_envio_email = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de envío por email"
    )
    
    # Multi-tenancy
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='comprobantes_pago',
        help_text="Empresa emisora del comprobante"
    )
    
    class Meta:
        db_table = 'comprobante_digital_pago'
        ordering = ['-fecha_emision']
        verbose_name = 'Comprobante Digital de Pago'
        verbose_name_plural = 'Comprobantes Digitales de Pago'
        indexes = [
            models.Index(fields=['codigo_comprobante']),
            models.Index(fields=['codigo_verificacion']),
            models.Index(fields=['empresa', '-fecha_emision']),
            models.Index(fields=['estado']),
        ]
    
    def __str__(self):
        return f"{self.codigo_comprobante} - {self.pago.codigo_pago} ({self.get_estado_display()})"
    
    def save(self, *args, **kwargs):
        """Generar códigos únicos si no existen"""
        if not self.codigo_comprobante:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            count = ComprobanteDigital.objects.filter(
                fecha_emision__date=datetime.now().date()
            ).count() + 1
            self.codigo_comprobante = f"COMP-{timestamp}-{count:04d}"
        
        if not self.codigo_verificacion:
            import hashlib
            import uuid
            data = f"{self.codigo_comprobante}{self.pago.codigo_pago}{uuid.uuid4()}"
            self.codigo_verificacion = hashlib.sha256(data.encode()).hexdigest()
        
        super().save(*args, **kwargs)
    
    def esta_activo(self):
        """Verifica si el comprobante está activo"""
        return self.estado == self.ESTADO_ACTIVO
    
    def puede_anularse(self):
        """Verifica si el comprobante puede anularse"""
        return self.estado == self.ESTADO_ACTIVO and self.pago.puede_anularse()
    
    def anular(self, motivo):
        """Anula el comprobante"""
        from django.utils import timezone
        if not self.puede_anularse():
            raise ValueError("El comprobante no puede anularse en su estado actual")
        
        self.estado = self.ESTADO_ANULADO
        self.fecha_anulacion = timezone.now()
        self.motivo_anulacion = motivo
        self.save(update_fields=['estado', 'fecha_anulacion', 'motivo_anulacion'])
    
    def get_url_verificacion(self):
        """Retorna URL pública para verificar el comprobante"""
        return f"/api/verificar-comprobante-pago/{self.codigo_verificacion}/"
    
    @classmethod
    def crear_comprobante(cls, pago):
        """
        Crea un comprobante digital para un pago aprobado.
        
        Args:
            pago: Instancia de PagoEnLinea (debe estar aprobado)
        
        Returns:
            ComprobanteDigital: Instancia creada
        
        Raises:
            ValueError: Si el pago no está aprobado o ya tiene comprobante
        """
        if pago.estado != 'aprobado':
            raise ValueError("Solo se pueden crear comprobantes para pagos aprobados")
        
        if hasattr(pago, 'comprobante'):
            raise ValueError("El pago ya tiene un comprobante asociado")
        
        # Crear datos del comprobante
        datos_comprobante = {
            'pago_id': pago.id,
            'codigo_pago': pago.codigo_pago,
            'monto': float(pago.monto),
            'moneda': pago.moneda,
            'fecha_pago': pago.fecha_aprobacion.isoformat() if pago.fecha_aprobacion else None,
            'metodo_pago': pago.get_metodo_pago_display(),
            'origen': pago.get_origen_tipo_display(),
        }
        
        # Agregar información del paciente
        paciente_info = None
        if pago.origen_tipo in ['plan_completo', 'items_individuales'] and pago.plan_tratamiento:
            if pago.plan_tratamiento.codpaciente and pago.plan_tratamiento.codpaciente.codusuario:
                usuario = pago.plan_tratamiento.codpaciente.codusuario
                paciente_info = {
                    'nombre': usuario.nombre,
                    'email': usuario.email,
                    'telefono': usuario.telefono
                }
        elif pago.origen_tipo == 'consulta' and pago.consulta:
            if pago.consulta.codpaciente and pago.consulta.codpaciente.codusuario:
                usuario = pago.consulta.codpaciente.codusuario
                paciente_info = {
                    'nombre': usuario.nombre,
                    'email': usuario.email,
                    'telefono': usuario.telefono
                }
        
        if paciente_info:
            datos_comprobante['paciente'] = paciente_info
        
        # Crear comprobante
        comprobante = cls.objects.create(
            pago=pago,
            estado=cls.ESTADO_ACTIVO,
            datos_comprobante=datos_comprobante
        )
        
        return comprobante
