"""
Signals para el flujo clínico (Paso 2).

Estos signals manejan transiciones automáticas de estado y validaciones
cuando se ejecutan items del plan de tratamiento.
"""
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Itemplandetratamiento, Plandetratamiento, Consulta

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Itemplandetratamiento)
def auto_verificar_completitud_plan(sender, instance, created, **kwargs):
    """
    Signal que verifica automáticamente si el plan debe marcarse como completado
    cuando se ejecuta un item.
    
    Se dispara después de guardar un Itemplandetratamiento.
    Si todos los items activos están ejecutados, intenta completar el plan automáticamente.
    """
    # Solo procesar si el item fue ejecutado (tiene fecha_ejecucion)
    if not instance.fecha_ejecucion:
        return
    
    plan = instance.idplantratamiento
    
    # Solo procesar si el plan está en ejecución
    if plan.estado_tratamiento != 'En Ejecución':
        return
    
    # Verificar si todos los items están ejecutados
    puede_completar, mensaje = plan.puede_completarse()
    
    if puede_completar:
        try:
            plan.marcar_completado()
            logger.info(
                f"✅ Plan #{plan.id} completado automáticamente. "
                f"Todos los items fueron ejecutados."
            )
        except Exception as e:
            logger.error(
                f"❌ Error al completar automáticamente plan #{plan.id}: {e}"
            )


@receiver(post_save, sender=Itemplandetratamiento)
def validar_consistencia_item_ejecutado(sender, instance, created, **kwargs):
    """
    Valida la consistencia de datos cuando se ejecuta un item.
    
    Verifica que:
    - Si tiene fecha_ejecucion, tiene odontologo_ejecutor
    - Si tiene consulta_ejecucion, pertenece al plan correcto
    """
    if not instance.fecha_ejecucion:
        return
    
    es_valido, errores = instance.validar_datos_ejecucion()
    
    if not es_valido:
        logger.warning(
            f"⚠️  Item #{instance.id} tiene inconsistencias: {', '.join(errores)}"
        )


@receiver(pre_save, sender=Plandetratamiento)
def validar_transicion_estado_plan(sender, instance, **kwargs):
    """
    Valida las transiciones de estado del plan antes de guardar.
    
    Evita transiciones inválidas de estado_tratamiento.
    """
    # Si es un objeto nuevo, no validar transición
    if not instance.pk:
        return
    
    try:
        # Obtener el estado anterior
        plan_anterior = Plandetratamiento.objects.get(pk=instance.pk)
        estado_anterior = plan_anterior.estado_tratamiento
        estado_nuevo = instance.estado_tratamiento
        
        # Si no cambió el estado, no validar
        if estado_anterior == estado_nuevo:
            return
        
        # Definir transiciones válidas
        transiciones_validas = {
            'Propuesto': ['Aceptado', 'Cancelado'],
            'Aceptado': ['En Ejecución', 'Cancelado'],
            'En Ejecución': ['Completado', 'Pausado', 'Cancelado'],
            'Pausado': ['En Ejecución', 'Cancelado'],
            'Completado': [],  # No se puede cambiar desde completado
            'Cancelado': [],  # No se puede cambiar desde cancelado
        }
        
        estados_permitidos = transiciones_validas.get(estado_anterior, [])
        
        if estado_nuevo not in estados_permitidos:
            logger.warning(
                f"⚠️  Transición inválida en Plan #{instance.pk}: "
                f"{estado_anterior} → {estado_nuevo}. "
                f"Transiciones válidas: {estados_permitidos}"
            )
    
    except Plandetratamiento.DoesNotExist:
        # El plan no existe aún, es una creación
        pass


@receiver(post_save, sender=Consulta)
def auto_vincular_plan_a_consulta(sender, instance, created, **kwargs):
    """
    Signal que vincula automáticamente un plan a una consulta cuando se crea.
    
    Solo para consultas que son parte de ejecución de un plan (no diagnósticas).
    """
    # Solo procesar consultas nuevas que tengan plan_tratamiento
    if not created or not instance.plan_tratamiento:
        return
    
    plan = instance.plan_tratamiento
    
    # Si el plan está en estado Aceptado y esta es la primera consulta de ejecución,
    # iniciar automáticamente la ejecución del plan
    if plan.estado_tratamiento == 'Aceptado':
        try:
            plan.iniciar_ejecucion()
            logger.info(
                f"✅ Plan #{plan.id} iniciado automáticamente con Consulta #{instance.id}"
            )
        except Exception as e:
            logger.warning(
                f"⚠️  No se pudo iniciar automáticamente plan #{plan.id}: {e}"
            )


@receiver(post_save, sender=Plandetratamiento)
def log_cambio_estado_plan(sender, instance, created, **kwargs):
    """
    Registra en logs los cambios de estado del plan para auditoría.
    """
    if created:
        logger.info(
            f"📋 Nuevo plan de tratamiento #{instance.id} creado. "
            f"Estado inicial: {instance.estado_tratamiento}"
        )
    else:
        # Solo loguear si hay cambio de estado
        try:
            plan_anterior = Plandetratamiento.objects.get(pk=instance.pk)
            if plan_anterior.estado_tratamiento != instance.estado_tratamiento:
                logger.info(
                    f"🔄 Plan #{instance.id} cambió estado: "
                    f"{plan_anterior.estado_tratamiento} → {instance.estado_tratamiento}"
                )
        except Plandetratamiento.DoesNotExist:
            pass


# Registrar que los signals están cargados
logger.info("✅ Signals de flujo clínico registrados")
