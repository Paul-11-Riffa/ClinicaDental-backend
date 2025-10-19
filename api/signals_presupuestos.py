# api/signals_presupuestos.py
"""
Signals para la funcionalidad de aceptación de presupuestos.
SP3-T003: Implementar Aceptar presupuesto por parte del paciente (web)
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

from .models import AceptacionPresupuesto

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AceptacionPresupuesto)
def notificar_aceptacion_presupuesto(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta después de crear una AceptacionPresupuesto.
    Envía notificaciones al paciente y al odontólogo.
    """
    if not created:
        return  # Solo para nuevas aceptaciones
    
    try:
        # Importar aquí para evitar imports circulares
        from api.notifications_mobile.queue import queue_notification
        
        presupuesto = instance.plandetratamiento
        paciente = presupuesto.codpaciente
        odontologo = presupuesto.cododontologo
        empresa = instance.empresa
        
        # Notificación al paciente (confirmación)
        notif_paciente_data = {
            'empresa': empresa,
            'usuario_destino': paciente.codusuario,
            'titulo': '✅ Presupuesto Aceptado',
            'mensaje': (
                f'Has aceptado el presupuesto #{presupuesto.id} '
                f'({instance.tipo_aceptacion.lower()}). '
                f'Tu comprobante: {instance.comprobante_id}'
            ),
            'tipo': 'presupuesto_aceptado_paciente',
            'datos_extra': {
                'presupuesto_id': presupuesto.id,
                'comprobante_id': str(instance.comprobante_id),
                'tipo_aceptacion': instance.tipo_aceptacion,
                'monto_total': str(instance.monto_total_aceptado),
                'fecha_aceptacion': instance.fecha_aceptacion.isoformat(),
            }
        }
        
        # Notificación al odontólogo (nueva aceptación)
        notif_odontologo_data = {
            'empresa': empresa,
            'usuario_destino': odontologo.codusuario,
            'titulo': '🔔 Presupuesto Aceptado por Paciente',
            'mensaje': (
                f'El paciente {paciente.codusuario.nombre} {paciente.codusuario.apellido} '
                f'ha aceptado el presupuesto #{presupuesto.id} '
                f'({instance.tipo_aceptacion.lower()}).'
            ),
            'tipo': 'presupuesto_aceptado_odontologo',
            'datos_extra': {
                'presupuesto_id': presupuesto.id,
                'paciente_id': paciente.id,
                'paciente_nombre': f'{paciente.codusuario.nombre} {paciente.codusuario.apellido}',
                'comprobante_id': str(instance.comprobante_id),
                'tipo_aceptacion': instance.tipo_aceptacion,
                'monto_total': str(instance.monto_total_aceptado),
            }
        }
        
        # Encolar notificaciones
        queue_notification(**notif_paciente_data)
        queue_notification(**notif_odontologo_data)
        
        logger.info(
            f"Notificaciones encoladas para aceptación {instance.comprobante_id} "
            f"(Presupuesto #{presupuesto.id})"
        )
        
    except ImportError:
        logger.warning(
            "Sistema de notificaciones no disponible. "
            "No se enviaron notificaciones para la aceptación."
        )
    except Exception as e:
        logger.error(
            f"Error al enviar notificaciones para aceptación {instance.comprobante_id}: {e}",
            exc_info=True
        )
