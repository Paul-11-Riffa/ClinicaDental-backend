# api/signals_plan_tratamiento.py
"""
Signals para la funcionalidad de gestión de planes de tratamiento.
SP3-T001: Crear plan de tratamiento (Web)
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import logging

from .models import Itemplandetratamiento, Plandetratamiento

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Itemplandetratamiento)
def recalcular_totales_al_guardar_item(sender, instance, created, **kwargs):
    """
    Recalcula automáticamente los totales del plan cuando se guarda un ítem.
    Esto asegura que el total siempre esté actualizado.
    """
    try:
        plan = instance.idplantratamiento
        
        # Solo recalcular si el plan existe y está en borrador
        if plan and plan.puede_editarse():
            plan.calcular_totales()
            logger.debug(
                f"Totales recalculados para plan #{plan.id} "
                f"tras {'crear' if created else 'actualizar'} ítem #{instance.id}"
            )
    
    except Exception as e:
        logger.error(
            f"Error al recalcular totales para plan tras guardar ítem #{instance.id}: {e}",
            exc_info=True
        )


@receiver(post_delete, sender=Itemplandetratamiento)
def recalcular_totales_al_eliminar_item(sender, instance, **kwargs):
    """
    Recalcula automáticamente los totales del plan cuando se elimina un ítem.
    """
    try:
        plan = instance.idplantratamiento
        
        # Solo recalcular si el plan existe
        if plan:
            plan.calcular_totales()
            logger.debug(
                f"Totales recalculados para plan #{plan.id} "
                f"tras eliminar ítem #{instance.id}"
            )
    
    except Exception as e:
        logger.error(
            f"Error al recalcular totales para plan tras eliminar ítem: {e}",
            exc_info=True
        )


@receiver(post_save, sender=Plandetratamiento)
def notificar_aprobacion_plan(sender, instance, created, update_fields, **kwargs):
    """
    Envía notificación cuando un plan es aprobado.
    """
    if created:
        return  # No notificar en creación
    
    # Verificar si se actualizó el estado_plan a Aprobado
    if update_fields and 'estado_plan' in update_fields:
        if instance.estado_plan == Plandetratamiento.ESTADO_PLAN_APROBADO:
            try:
                # Importar aquí para evitar imports circulares
                from api.notifications_mobile.queue import queue_notification
                
                paciente = instance.codpaciente
                odontologo = instance.cododontologo
                empresa = instance.empresa
                
                # Notificación al paciente
                notif_paciente_data = {
                    'empresa': empresa,
                    'usuario_destino': paciente.codusuario,
                    'titulo': '📋 Plan de Tratamiento Aprobado',
                    'mensaje': (
                        f'Tu plan de tratamiento #{instance.id} ha sido aprobado '
                        f'por Dr. {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}. '
                        f'Total: ${instance.montototal}'
                    ),
                    'tipo': 'plan_aprobado',
                    'datos_extra': {
                        'plan_id': instance.id,
                        'total': str(instance.montototal),
                        'fecha_aprobacion': instance.fecha_aprobacion.isoformat() if instance.fecha_aprobacion else None,
                    }
                }
                
                queue_notification(**notif_paciente_data)
                
                logger.info(
                    f"Notificación enviada para plan aprobado #{instance.id}"
                )
            
            except ImportError:
                logger.warning(
                    "Sistema de notificaciones no disponible. "
                    "No se envió notificación de aprobación de plan."
                )
            except Exception as e:
                logger.error(
                    f"Error al enviar notificación de aprobación de plan #{instance.id}: {e}",
                    exc_info=True
                )
