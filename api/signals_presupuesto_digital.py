# api/signals_presupuesto_digital.py
"""
Signals para la gestión automática de presupuestos digitales.
SP3-T002: Generar presupuesto digital (web)

Incluye:
- Recálculo automático de totales al modificar items
- Marcado automático de presupuestos caducados
- Registro de auditoría en bitácora
- Validaciones de negocio
"""
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from decimal import Decimal

from .models import (
    PresupuestoDigital,
    ItemPresupuestoDigital,
    Bitacora,
)


@receiver(post_save, sender=ItemPresupuestoDigital)
def recalcular_totales_presupuesto(sender, instance, created, **kwargs):
    """
    Recalcula automáticamente los totales del presupuesto cuando
    se crea o modifica un item.
    """
    presupuesto = instance.presupuesto
    
    # Solo recalcular si el presupuesto es editable
    if presupuesto.puede_editarse():
        presupuesto.calcular_totales()


@receiver(post_delete, sender=ItemPresupuestoDigital)
def recalcular_totales_al_eliminar_item(sender, instance, **kwargs):
    """
    Recalcula totales cuando se elimina un item del presupuesto.
    """
    presupuesto = instance.presupuesto
    
    # Solo recalcular si el presupuesto es editable
    if presupuesto.puede_editarse():
        presupuesto.calcular_totales()


@receiver(pre_save, sender=PresupuestoDigital)
def validar_cambio_estado(sender, instance, **kwargs):
    """
    Valida las transiciones de estado del presupuesto.
    
    Reglas:
    - De Borrador puede pasar a Emitido o Anulado
    - De Emitido puede pasar a Caducado o Anulado
    - Caducado y Anulado son estados finales
    """
    if instance.pk:  # Si ya existe
        try:
            presupuesto_actual = PresupuestoDigital.objects.get(pk=instance.pk)
            estado_anterior = presupuesto_actual.estado
            estado_nuevo = instance.estado
            
            # Validar transiciones inválidas
            if estado_anterior == PresupuestoDigital.ESTADO_CADUCADO:
                if estado_nuevo != estado_anterior:
                    raise ValueError("Los presupuestos caducados no pueden cambiar de estado.")
            
            if estado_anterior == PresupuestoDigital.ESTADO_ANULADO:
                if estado_nuevo != estado_anterior:
                    raise ValueError("Los presupuestos anulados no pueden cambiar de estado.")
            
        except PresupuestoDigital.DoesNotExist:
            pass


@receiver(post_save, sender=PresupuestoDigital)
def registrar_cambio_estado_bitacora(sender, instance, created, **kwargs):
    """
    Registra en la bitácora los cambios de estado del presupuesto.
    """
    if created:
        # Ya se registra en el serializer al crear
        return
    
    # Detectar cambio de estado
    if instance.pk:
        try:
            presupuesto_anterior = PresupuestoDigital.objects.get(pk=instance.pk)
            if presupuesto_anterior.estado != instance.estado:
                # Registrar cambio de estado
                Bitacora.objects.create(
                    empresa=instance.empresa,
                    usuario=instance.usuario_emite,
                    accion="PRESUPUESTO_CAMBIO_ESTADO",
                    tabla_afectada="presupuesto_digital",
                    registro_id=instance.id,
                    valores_anteriores={'estado': presupuesto_anterior.estado},
                    valores_nuevos={
                        'estado': instance.estado,
                        'codigo_presupuesto': instance.codigo_presupuesto.hex[:8]
                    },
                    ip_address='127.0.0.1',
                    user_agent='Signal'
                )
        except PresupuestoDigital.DoesNotExist:
            pass


def marcar_presupuestos_caducados():
    """
    Tarea periódica para marcar como caducados los presupuestos
    emitidos cuya fecha de vigencia ha expirado.
    
    Esta función debe ser llamada por un cron job o tarea programada
    (ej: Celery, Django-Q).
    
    Uso:
        # En un management command o tarea programada
        from api.signals_presupuesto_digital import marcar_presupuestos_caducados
        marcar_presupuestos_caducados()
    """
    presupuestos_vencidos = PresupuestoDigital.objects.filter(
        estado=PresupuestoDigital.ESTADO_EMITIDO,
        fecha_vigencia__lt=timezone.now().date()
    )
    
    count = 0
    for presupuesto in presupuestos_vencidos:
        presupuesto.marcar_caducado()
        count += 1
        
        # Registrar en bitácora
        Bitacora.objects.create(
            empresa=presupuesto.empresa,
            usuario=None,
            accion="PRESUPUESTO_CADUCADO_AUTO",
            tabla_afectada="presupuesto_digital",
            registro_id=presupuesto.id,
            valores_nuevos={
                'codigo_presupuesto': presupuesto.codigo_presupuesto.hex[:8],
                'estado': presupuesto.estado,
                'fecha_caducidad': str(presupuesto.fecha_vencimiento)
            },
            ip_address='127.0.0.1',
            user_agent='Scheduled Task'
        )
    
    return count


def validar_items_presupuesto(presupuesto):
    """
    Valida que todos los items del presupuesto pertenezcan al plan
    de tratamiento asociado y estén en estado válido.
    
    Args:
        presupuesto: Instancia de PresupuestoDigital
    
    Returns:
        dict: {
            'valido': bool,
            'errores': list,
            'items_invalidos': list
        }
    """
    plan = presupuesto.plan_tratamiento
    errores = []
    items_invalidos = []
    
    for item in presupuesto.items_presupuesto.all():
        # Validar que el item pertenece al plan
        if item.item_plan.idplantratamiento != plan:
            errores.append(f"Item {item.id} no pertenece al plan de tratamiento.")
            items_invalidos.append(item.id)
        
        # Validar que el item no está cancelado
        if item.item_plan.estado_item in ['cancelado', 'Cancelado']:
            errores.append(f"Item {item.id} está cancelado en el plan.")
            items_invalidos.append(item.id)
    
    return {
        'valido': len(errores) == 0,
        'errores': errores,
        'items_invalidos': items_invalidos
    }


# Conectar signals al app ready
def conectar_signals():
    """
    Función para conectar todos los signals.
    Debe ser llamada en apps.py en el método ready().
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Presupuestos Digitales: señales conectadas.")
