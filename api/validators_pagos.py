"""
SP3-T009: Validadores Personalizados para Sistema de Pagos
Validadores reutilizables para validaciones complejas de pagos.
"""

from rest_framework import serializers
from decimal import Decimal
from django.utils.translation import gettext_lazy as _

from .models import Plandetratamiento, Itemplandetratamiento, Consulta, PagoEnLinea
from .services.calculador_pagos import CalculadorPagos


def validar_monto_positivo(value):
    """
    Valida que el monto sea mayor a 0.
    """
    if value <= Decimal('0'):
        raise serializers.ValidationError(
            _("El monto debe ser mayor a 0")
        )


def validar_monto_no_excede_saldo(monto, origen, origen_id, empresa):
    """
    Valida que el monto no exceda el saldo pendiente del origen.
    
    Args:
        monto: Decimal - Monto a validar
        origen: str - Tipo de origen ('plan_completo', 'items_individuales', 'consulta')
        origen_id: int - ID del origen (plan o consulta)
        empresa: Empresa - Empresa actual
    
    Returns:
        tuple: (es_valido: bool, mensaje: str, saldo_disponible: Decimal)
    """
    if origen in ['plan_completo', 'items_individuales']:
        try:
            plan = Plandetratamiento.objects.get(id=origen_id, empresa=empresa)
            saldo_pendiente = plan.calcular_saldo_pendiente()
            
            if monto > saldo_pendiente:
                return (
                    False,
                    f"El monto (${monto}) excede el saldo pendiente del plan (${saldo_pendiente})",
                    saldo_pendiente
                )
            
            return True, "Monto válido", saldo_pendiente
            
        except Plandetratamiento.DoesNotExist:
            return False, "Plan de tratamiento no encontrado", Decimal('0')
    
    elif origen == 'consulta':
        try:
            consulta = Consulta.objects.get(id=origen_id, empresa=empresa)
            saldo_pendiente = consulta.calcular_saldo_pendiente()
            
            if monto > saldo_pendiente:
                return (
                    False,
                    f"El monto (${monto}) excede el saldo pendiente de la consulta (${saldo_pendiente})",
                    saldo_pendiente
                )
            
            return True, "Monto válido", saldo_pendiente
            
        except Consulta.DoesNotExist:
            return False, "Consulta no encontrada", Decimal('0')
    
    return False, "Origen de pago no válido", Decimal('0')


def validar_estado_origen(origen, origen_id, empresa):
    """
    Valida que el origen (plan/consulta) esté en estado válido para recibir pagos.
    
    Args:
        origen: str - Tipo de origen
        origen_id: int - ID del origen
        empresa: Empresa - Empresa actual
    
    Returns:
        tuple: (es_valido: bool, mensaje: str, objeto_origen)
    """
    if origen in ['plan_completo', 'items_individuales']:
        try:
            plan = Plandetratamiento.objects.get(id=origen_id, empresa=empresa)
            puede_pagar, razon = plan.puede_pagar_completo()
            
            if not puede_pagar:
                return False, razon, None
            
            return True, "Plan válido para pagos", plan
            
        except Plandetratamiento.DoesNotExist:
            return False, "Plan de tratamiento no encontrado", None
    
    elif origen == 'consulta':
        try:
            consulta = Consulta.objects.get(id=origen_id, empresa=empresa)
            puede_pagar, razon = consulta.puede_pagarse()
            
            if not puede_pagar:
                return False, razon, None
            
            return True, "Consulta válida para pagos", consulta
            
        except Consulta.DoesNotExist:
            return False, "Consulta no encontrada", None
    
    return False, "Origen de pago no válido", None


def validar_items_plan(items_ids, plan_id, empresa):
    """
    Valida que los items existan, pertenezcan al plan y puedan recibir pagos.
    
    Args:
        items_ids: list[int] - IDs de items
        plan_id: int - ID del plan
        empresa: Empresa - Empresa actual
    
    Returns:
        tuple: (es_valido: bool, mensaje: str, items: QuerySet)
    """
    if not items_ids:
        return True, "Sin items seleccionados (pago de plan completo)", None
    
    try:
        plan = Plandetratamiento.objects.get(id=plan_id, empresa=empresa)
    except Plandetratamiento.DoesNotExist:
        return False, "Plan de tratamiento no encontrado", None
    
    # Obtener items
    items = Itemplandetratamiento.objects.filter(
        id__in=items_ids,
        idplantratamiento=plan
    ).exclude(estado_item='Cancelado')
    
    # Verificar que todos los items existen
    if items.count() != len(items_ids):
        items_encontrados = set(items.values_list('id', flat=True))
        items_no_encontrados = set(items_ids) - items_encontrados
        return (
            False,
            f"Items no encontrados o cancelados: {list(items_no_encontrados)}",
            None
        )
    
    # Verificar que cada item puede recibir pagos
    for item in items:
        puede_pagar, razon = item.puede_pagarse()
        if not puede_pagar:
            servicio_nombre = item.idservicio.nombre if item.idservicio else 'Sin nombre'
            return (
                False,
                f"Item {item.id} ({servicio_nombre}): {razon}",
                None
            )
    
    return True, "Items válidos", items


def validar_distribucion_pago(monto, items_ids, plan_id, empresa):
    """
    Valida que el monto pueda distribuirse entre los items seleccionados.
    
    Args:
        monto: Decimal - Monto a distribuir
        items_ids: list[int] - IDs de items (None = plan completo)
        plan_id: int - ID del plan
        empresa: Empresa - Empresa actual
    
    Returns:
        tuple: (es_valido: bool, mensaje: str, distribucion: dict)
    """
    try:
        plan = Plandetratamiento.objects.get(id=plan_id, empresa=empresa)
    except Plandetratamiento.DoesNotExist:
        return False, "Plan de tratamiento no encontrado", None
    
    # Calcular distribución
    distribucion = CalculadorPagos.calcular_distribucion_pago(
        plan,
        monto,
        items_ids
    )
    
    # Verificar que el monto puede distribuirse
    if not distribucion['distribucion']:
        return False, "No hay items disponibles para distribuir el pago", None
    
    monto_distribuido = Decimal(str(distribucion['monto_distribuido']))
    monto_sobrante = Decimal(str(distribucion['monto_sobrante']))
    
    # Advertir si hay monto sobrante
    if monto_sobrante > Decimal('0'):
        return (
            True,
            f"Advertencia: ${monto_sobrante} no se distribuirá (todos los items están pagados)",
            distribucion
        )
    
    return True, f"Distribución válida: ${monto_distribuido} entre {len(distribucion['distribucion'])} items", distribucion


def validar_pago_duplicado(origen, origen_id, monto, empresa, ultimo_minutos=5):
    """
    Valida que no exista un pago pendiente/procesando idéntico reciente.
    Previene pagos duplicados por doble clic.
    
    Args:
        origen: str - Tipo de origen
        origen_id: int - ID del origen
        monto: Decimal - Monto del pago
        empresa: Empresa - Empresa actual
        ultimo_minutos: int - Ventana de tiempo para considerar duplicado
    
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    from django.utils import timezone
    from datetime import timedelta
    
    hace_n_minutos = timezone.now() - timedelta(minutes=ultimo_minutos)
    
    # Buscar pagos similares recientes
    filtros = {
        'empresa': empresa,
        'origen': origen,
        'monto': monto,
        'estado__in': ['pendiente', 'procesando'],
        'fecha_creacion__gte': hace_n_minutos
    }
    
    if origen in ['plan_completo', 'items_individuales']:
        filtros['plan_tratamiento_id'] = origen_id
    elif origen == 'consulta':
        filtros['consulta_id'] = origen_id
    
    pagos_similares = PagoEnLinea.objects.filter(**filtros)
    
    if pagos_similares.exists():
        pago = pagos_similares.first()
        return (
            False,
            f"Ya existe un pago pendiente/procesando similar (#{pago.codigo_pago}) creado hace {(timezone.now() - pago.fecha_creacion).seconds // 60} minutos"
        )
    
    return True, "No hay pagos duplicados"


def validar_metodo_pago_disponible(metodo_pago, empresa):
    """
    Valida que el método de pago esté habilitado para la empresa.
    
    Args:
        metodo_pago: str - Método de pago
        empresa: Empresa - Empresa actual
    
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    # Por ahora, todos los métodos están disponibles
    # En el futuro, esto podría verificar configuración de empresa
    
    metodos_validos = dict(PagoEnLinea.METODO_CHOICES).keys()
    
    if metodo_pago not in metodos_validos:
        return False, f"Método de pago '{metodo_pago}' no es válido"
    
    # Validaciones específicas por método
    if metodo_pago == 'tarjeta_credito' or metodo_pago == 'tarjeta_debito':
        # Verificar que Stripe esté configurado
        from django.conf import settings
        if not hasattr(settings, 'STRIPE_SECRET_KEY') or not settings.STRIPE_SECRET_KEY:
            return False, "Pagos con tarjeta no están configurados para esta clínica"
    
    return True, f"Método de pago '{metodo_pago}' disponible"


def validar_pago_puede_anularse(pago):
    """
    Valida que un pago pueda ser anulado.
    
    Args:
        pago: PagoEnLinea - Instancia del pago
    
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    if not pago.puede_anularse():
        return False, "El pago no puede ser anulado (solo se pueden anular pagos pendientes o rechazados)"
    
    return True, "El pago puede ser anulado"


def validar_pago_puede_reembolsarse(pago):
    """
    Valida que un pago pueda ser reembolsado.
    
    Args:
        pago: PagoEnLinea - Instancia del pago
    
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    if not pago.puede_reembolsarse():
        return (
            False,
            "El pago no puede ser reembolsado (solo se pueden reembolsar pagos aprobados dentro del período permitido)"
        )
    
    return True, "El pago puede ser reembolsado"


def validar_saldo_suficiente_reembolso(pago):
    """
    Valida que no se hayan realizado nuevos pagos después del pago a reembolsar.
    Si se reembolsa, el saldo debe ser consistente.
    
    Args:
        pago: PagoEnLinea - Instancia del pago
    
    Returns:
        tuple: (es_valido: bool, mensaje: str)
    """
    # Obtener pagos posteriores aprobados
    if pago.origen in ['plan_completo', 'items_individuales']:
        pagos_posteriores = PagoEnLinea.objects.filter(
            plan_tratamiento=pago.plan_tratamiento,
            estado='aprobado',
            fecha_aprobacion__gt=pago.fecha_aprobacion
        )
    elif pago.origen == 'consulta':
        pagos_posteriores = PagoEnLinea.objects.filter(
            consulta=pago.consulta,
            estado='aprobado',
            fecha_aprobacion__gt=pago.fecha_aprobacion
        )
    else:
        pagos_posteriores = PagoEnLinea.objects.none()
    
    if pagos_posteriores.exists():
        return (
            False,
            "No se puede reembolsar este pago porque existen pagos posteriores aprobados. Reembolse primero los pagos más recientes."
        )
    
    return True, "No hay pagos posteriores, el reembolso es seguro"


class ValidadorComplejoPagos:
    """
    Clase helper para ejecutar múltiples validaciones de forma ordenada.
    """
    
    @staticmethod
    def validar_crear_pago_plan(plan_id, monto, items_ids, metodo_pago, empresa):
        """
        Ejecuta todas las validaciones necesarias para crear un pago de plan.
        
        Returns:
            tuple: (es_valido: bool, errores: dict)
        """
        errores = {}
        
        # 1. Validar monto positivo
        try:
            validar_monto_positivo(monto)
        except serializers.ValidationError as e:
            errores['monto'] = str(e.detail[0])
        
        # 2. Validar estado del origen
        es_valido, mensaje, plan = validar_estado_origen(
            'plan_completo' if not items_ids else 'items_individuales',
            plan_id,
            empresa
        )
        if not es_valido:
            errores['plan_tratamiento_id'] = mensaje
            return False, errores
        
        # 3. Validar items (si aplica)
        if items_ids:
            es_valido, mensaje, items = validar_items_plan(items_ids, plan_id, empresa)
            if not es_valido:
                errores['items_seleccionados'] = mensaje
                return False, errores
        
        # 4. Validar monto vs saldo
        es_valido, mensaje, saldo = validar_monto_no_excede_saldo(
            monto,
            'plan_completo' if not items_ids else 'items_individuales',
            plan_id,
            empresa
        )
        if not es_valido:
            errores['monto'] = mensaje
        
        # 5. Validar distribución
        es_valido, mensaje, distribucion = validar_distribucion_pago(
            monto, items_ids, plan_id, empresa
        )
        if not es_valido:
            errores['general'] = mensaje
        
        # 6. Validar método de pago
        es_valido, mensaje = validar_metodo_pago_disponible(metodo_pago, empresa)
        if not es_valido:
            errores['metodo_pago'] = mensaje
        
        # 7. Validar no duplicado
        es_valido, mensaje = validar_pago_duplicado(
            'plan_completo' if not items_ids else 'items_individuales',
            plan_id,
            monto,
            empresa
        )
        if not es_valido:
            errores['general'] = mensaje
        
        if errores:
            return False, errores
        
        return True, {}
    
    @staticmethod
    def validar_crear_pago_consulta(consulta_id, monto, metodo_pago, empresa):
        """
        Ejecuta todas las validaciones necesarias para crear un pago de consulta.
        
        Returns:
            tuple: (es_valido: bool, errores: dict)
        """
        errores = {}
        
        # 1. Validar monto positivo
        try:
            validar_monto_positivo(monto)
        except serializers.ValidationError as e:
            errores['monto'] = str(e.detail[0])
        
        # 2. Validar estado del origen
        es_valido, mensaje, consulta = validar_estado_origen(
            'consulta',
            consulta_id,
            empresa
        )
        if not es_valido:
            errores['consulta_id'] = mensaje
            return False, errores
        
        # 3. Validar monto vs saldo
        es_valido, mensaje, saldo = validar_monto_no_excede_saldo(
            monto,
            'consulta',
            consulta_id,
            empresa
        )
        if not es_valido:
            errores['monto'] = mensaje
        
        # 4. Validar método de pago
        es_valido, mensaje = validar_metodo_pago_disponible(metodo_pago, empresa)
        if not es_valido:
            errores['metodo_pago'] = mensaje
        
        # 5. Validar no duplicado
        es_valido, mensaje = validar_pago_duplicado(
            'consulta',
            consulta_id,
            monto,
            empresa
        )
        if not es_valido:
            errores['general'] = mensaje
        
        if errores:
            return False, errores
        
        return True, {}
