from django.db import models
from django.utils import timezone


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
    is_public = models.BooleanField(
        default=False,
        help_text="Indica si es el dominio público para administración"
    )

    class Meta:
        db_table = 'api_empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.subdomain})"
