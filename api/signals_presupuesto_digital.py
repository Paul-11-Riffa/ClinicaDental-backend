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


# ============================================================================
# SIGNALS PARA NOTIFICACIONES - SP3-T003 FASE 5
# ============================================================================
"""
Signals para notificaciones automáticas al aceptar presupuestos digitales.

SP3-T003: Aceptar Presupuesto Digital por Paciente
Fase 5: Signals y Notificaciones

Este módulo maneja el envío automático de notificaciones cuando:
- Un paciente acepta un presupuesto digital
- Se genera el comprobante PDF
"""

import logging
from typing import Optional
from decimal import Decimal

# Importar modelo de aceptación
from .models import AceptacionPresupuestoDigital

# Importar sistema de notificaciones
try:
    from api.notifications_mobile.queue import enqueue_notif_for_user_devices
    from api.notifications_mobile.models import (
        TipoNotificacionMN,
        CanalNotificacionMN,
        HistorialNotificacionMN,
        DispositivoMovilMN
    )
    NOTIFICACIONES_DISPONIBLES = True
except ImportError:
    NOTIFICACIONES_DISPONIBLES = False
    logging.warning("Sistema de notificaciones no disponible")

logger_notif = logging.getLogger("signals_presupuesto_notificaciones")


def _ensure_catalog_safe(nombre_tipo: str, canal_nombre: str = "PUSH_MOBILE"):
    """
    Versión segura de _ensure_catalog que maneja conflictos de ID.
    Usa canales y tipos existentes en vez de intentar crearlos.
    """
    from django.db import connection
    
    #  Primero intentar encontrar existentes (sin transacción)
    tipo = TipoNotificacionMN.objects.filter(nombre=nombre_tipo).first()
    canal = CanalNotificacionMN.objects.filter(nombre=canal_nombre).first()
    
    # Si ya tenemos ambos, retornar
    if tipo and canal:
        return tipo, canal
    
    # Si falta alguno, usar los primeros disponibles como fallback
    if not tipo:
        tipo = TipoNotificacionMN.objects.first()
        if not tipo:
            logger_notif.error("No hay tipos de notificación en la base de datos")
            return None, None
    
    if not canal:
        canal = CanalNotificacionMN.objects.first()
        if not canal:
            logger_notif.error("No hay canales de notificación en la base de datos")
            return None, None
    
    return tipo, canal


def _enqueue_notif_safe(
    usuario_codigo: int,
    titulo: str,
    mensaje: str,
    tipo_nombre: str,
    data: Optional[dict] = None
) -> list:
    """
    Versión segura de enqueue_notif_for_user_devices.
    """
    try:
        tipo, canal = _ensure_catalog_safe(tipo_nombre)
        
        if not tipo or not canal:
            logger_notif.error("No se pudieron obtener/crear tipo y canal de notificación")
            return []
        
        # Buscar dispositivos activos del usuario
        dispositivos = DispositivoMovilMN.objects.filter(
            codusuario=usuario_codigo,
            activo=True
        ).only("id")
        
        rows = []
        now = timezone.now()
        
        for d in dispositivos:
            rows.append(HistorialNotificacionMN(
                titulo=titulo,
                mensaje=mensaje,
                datos_adicionales=dict(data or {}),
                estado="PENDING",
                fecha_creacion=now,
                fecha_envio=None,
                fecha_entrega=None,
                fecha_lectura=None,
                error_mensaje=None,
                intentos=0,
                codusuario=usuario_codigo,
                idtiponotificacion=tipo.id,
                idcanalnotificacion=canal.id,
                iddispositivomovil=d.id,
            ))
        
        if rows:
            HistorialNotificacionMN.objects.bulk_create(rows, batch_size=500)
        
        return rows
        
    except Exception as e:
        logger_notif.error(f"Error encolando notificación: {str(e)}", exc_info=True)
        return []


def _get_usuario_codigo(usuario) -> Optional[int]:
    """
    Extrae el código del usuario de forma segura.
    """
    if usuario is None:
        return None
    
    # Si es un ID directo
    if isinstance(usuario, int):
        return usuario
    
    # Si tiene atributo codigo (Usuario model)
    if hasattr(usuario, 'codigo'):
        return int(usuario.codigo)
    
    # Si tiene atributo id
    if hasattr(usuario, 'id'):
        return int(usuario.id)
    
    # Si tiene atributo pk
    if hasattr(usuario, 'pk'):
        return int(usuario.pk)
    
    return None


def _format_currency(amount: Decimal) -> str:
    """
    Formatea un monto decimal a string con formato boliviano.
    Ejemplo: 1234.50 -> "Bs. 1,234.50"
    """
    if amount is None:
        return "Bs. 0.00"
    
    try:
        # Convertir a float para formateo
        value = float(amount)
        # Formatear con separador de miles y 2 decimales
        formatted = f"{value:,.2f}"
        return f"Bs. {formatted}"
    except (ValueError, TypeError):
        return f"Bs. {amount}"


@receiver(post_save, sender=AceptacionPresupuestoDigital)
def notificar_aceptacion_presupuesto(sender, instance: AceptacionPresupuestoDigital, created, **kwargs):
    """
    Signal post_save para AceptacionPresupuestoDigital.
    
    Cuando se crea una nueva aceptación:
    1. Notifica al PACIENTE (confirmación de aceptación)
    2. Notifica al ODONTÓLOGO (alerta de aceptación)
    
    Args:
        sender: Modelo AceptacionPresupuestoDigital
        instance: Instancia de la aceptación creada
        created: True si es creación, False si es actualización
        **kwargs: Argumentos adicionales del signal
    """
    # Solo procesar cuando se CREA una nueva aceptación
    if not created:
        logger_notif.debug(f"Aceptación {instance.id} actualizada, no se envían notificaciones")
        return
    
    # Verificar que el sistema de notificaciones está disponible
    if not NOTIFICACIONES_DISPONIBLES:
        logger_notif.warning("Sistema de notificaciones no disponible, saltando envío")
        return
    
    logger_notif.info(f"📧 Procesando notificaciones para aceptación ID {instance.id}")
    
    try:
        # Obtener datos relacionados
        presupuesto = instance.presupuesto_digital
        usuario_paciente = instance.usuario_paciente
        plan_tratamiento = presupuesto.plan_tratamiento if presupuesto else None
        
        # Validar que tengamos los datos necesarios
        if not presupuesto or not usuario_paciente:
            logger_notif.warning(f"Aceptación {instance.id} sin presupuesto o usuario válido")
            return
        
        # 1. NOTIFICACIÓN AL PACIENTE
        _notificar_paciente_aceptacion(instance, presupuesto, usuario_paciente)
        
        # 2. NOTIFICACIÓN AL ODONTÓLOGO
        if plan_tratamiento and hasattr(plan_tratamiento, 'cododontologo'):
            odontologo = plan_tratamiento.cododontologo
            if odontologo and hasattr(odontologo, 'codusuario'):
                _notificar_odontologo_aceptacion(instance, presupuesto, usuario_paciente, odontologo.codusuario)
        
        logger_notif.info(f"✅ Notificaciones procesadas exitosamente para aceptación {instance.id}")
        
    except Exception as e:
        # Log del error pero no fallar el guardado
        logger_notif.error(f"❌ Error enviando notificaciones para aceptación {instance.id}: {str(e)}", exc_info=True)


def _notificar_paciente_aceptacion(
    aceptacion: AceptacionPresupuestoDigital,
    presupuesto,
    usuario_paciente
) -> None:
    """
    Envía notificación de confirmación al paciente.
    """
    try:
        # Obtener código del usuario
        codigo_usuario = _get_usuario_codigo(usuario_paciente)
        if not codigo_usuario:
            logger_notif.warning(f"No se pudo obtener código de usuario del paciente")
            return
        
        # Formatear monto
        monto_str = _format_currency(aceptacion.monto_total_aceptado)
        
        # Construir título y mensaje
        titulo = "✅ Presupuesto Aceptado"
        
        if aceptacion.tipo_aceptacion == 'Total':
            mensaje = (
                f"Has aceptado tu presupuesto por {monto_str}. "
                f"Puedes descargar tu comprobante desde la aplicación."
            )
        else:
            items_count = len(aceptacion.items_aceptados) if aceptacion.items_aceptados else 0
            mensaje = (
                f"Has aceptado {items_count} tratamiento(s) de tu presupuesto por {monto_str}. "
                f"Comprobante disponible en la app."
            )
        
        # Datos adicionales para la notificación
        data = {
            'tipo': 'PRESUPUESTO_ACEPTADO',
            'aceptacion_id': str(aceptacion.id),
            'presupuesto_id': str(presupuesto.codigo_presupuesto),
            'comprobante_id': str(aceptacion.comprobante_id),
            'tipo_aceptacion': aceptacion.tipo_aceptacion,
            'monto_total': str(aceptacion.monto_total_aceptado),
            'comprobante_url': aceptacion.comprobante_url or '',
            'fecha_aceptacion': aceptacion.fecha_aceptacion.isoformat() if aceptacion.fecha_aceptacion else '',
        }
        
        # Encolar notificación
        notificaciones = _enqueue_notif_safe(
            usuario_codigo=codigo_usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo_nombre="PRESUPUESTO_ACEPTADO_PACIENTE",
            data=data
        )
        
        logger_notif.info(
            f"📱 Notificación al paciente encolada: {len(notificaciones)} dispositivo(s) "
            f"(Usuario: {codigo_usuario})"
        )
        
    except Exception as e:
        logger_notif.error(f"Error notificando a paciente: {str(e)}", exc_info=True)


def _notificar_odontologo_aceptacion(
    aceptacion: AceptacionPresupuestoDigital,
    presupuesto,
    usuario_paciente,
    usuario_odontologo
) -> None:
    """
    Envía notificación al odontólogo informando de la aceptación.
    """
    try:
        # Obtener código del odontólogo
        codigo_odontologo = _get_usuario_codigo(usuario_odontologo)
        if not codigo_odontologo:
            logger_notif.warning(f"No se pudo obtener código de usuario del odontólogo")
            return
        
        # Nombre del paciente
        nombre_paciente = f"{usuario_paciente.nombre} {usuario_paciente.apellido}".strip()
        if not nombre_paciente:
            nombre_paciente = "Un paciente"
        
        # Formatear monto
        monto_str = _format_currency(aceptacion.monto_total_aceptado)
        
        # Construir título y mensaje
        titulo = "💼 Presupuesto Aceptado"
        
        if aceptacion.tipo_aceptacion == 'Total':
            mensaje = (
                f"{nombre_paciente} ha aceptado su presupuesto completo por {monto_str}."
            )
        else:
            items_count = len(aceptacion.items_aceptados) if aceptacion.items_aceptados else 0
            mensaje = (
                f"{nombre_paciente} ha aceptado {items_count} tratamiento(s) "
                f"de su presupuesto por {monto_str}."
            )
        
        # Datos adicionales
        data = {
            'tipo': 'PRESUPUESTO_ACEPTADO_ODONTOLOGO',
            'aceptacion_id': str(aceptacion.id),
            'presupuesto_id': str(presupuesto.codigo_presupuesto),
            'paciente_nombre': nombre_paciente,
            'paciente_id': str(usuario_paciente.codigo),
            'tipo_aceptacion': aceptacion.tipo_aceptacion,
            'monto_total': str(aceptacion.monto_total_aceptado),
            'fecha_aceptacion': aceptacion.fecha_aceptacion.isoformat() if aceptacion.fecha_aceptacion else '',
        }
        
        # Encolar notificación
        notificaciones = _enqueue_notif_safe(
            usuario_codigo=codigo_odontologo,
            titulo=titulo,
            mensaje=mensaje,
            tipo_nombre="PRESUPUESTO_ACEPTADO_ODONTOLOGO",
            data=data
        )
        
        logger_notif.info(
            f"👨‍⚕️ Notificación al odontólogo encolada: {len(notificaciones)} dispositivo(s) "
            f"(Usuario: {codigo_odontologo})"
        )
        
    except Exception as e:
        logger_notif.error(f"Error notificando a odontólogo: {str(e)}", exc_info=True)


logger_notif.info("✅ Signals de notificaciones de presupuesto digital registrados")
