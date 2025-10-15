from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.conf import settings
import uuid


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
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='usuarios', null=True, blank=True)

    class Meta:
        db_table = 'usuario'


class Tipodeusuario(models.Model):
    rol = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    empresa = models.ForeignKey(
        'tenancy.Empresa', on_delete=models.CASCADE,
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


class BloqueoUsuario(models.Model):
    """Control de acceso: bloqueo de usuarios."""
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


class Bitacora(models.Model):
    """Tabla de auditoría."""
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
    empresa = models.ForeignKey('tenancy.Empresa', on_delete=models.CASCADE, related_name='bitacoras', null=True, blank=True)

    class Meta:
        db_table = 'bitacora'
        verbose_name = 'Bitácora'
        verbose_name_plural = 'Bitácoras'

    def __str__(self):
        usuario_nombre = self.usuario.nombre if self.usuario else "Sistema"
        return f"{usuario_nombre} - {self.accion} - {self.tabla_afectada} - {self.timestamp}"
