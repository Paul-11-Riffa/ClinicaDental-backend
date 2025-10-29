"""
SP3-T009: Servicio de Cálculo de Pagos
Calculador centralizado para operaciones de pagos en planes de tratamiento,
items individuales y consultas.

Este servicio proporciona métodos reutilizables para cálculos de pagos,
validaciones y generación de resúmenes financieros.
"""

from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from django.db.models import Sum, Q, F
from django.utils import timezone


class CalculadorPagos:
    """
    Servicio centralizado para cálculos de pagos y validaciones financieras.
    """
    
    @staticmethod
    def calcular_resumen_plan(plan_tratamiento) -> Dict:
        """
        Genera un resumen financiero completo del plan de tratamiento.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
        
        Returns:
            Dict con:
            - total_plan: Monto total del plan
            - total_pagado: Suma de pagos aprobados
            - saldo_pendiente: Saldo restante
            - porcentaje_pagado: % del plan pagado
            - items_pagados: Cantidad de items completamente pagados
            - items_pendientes: Cantidad de items con saldo
        """
        from api.models import PagoEnLinea
        
        total_plan = Decimal(str(plan_tratamiento.montototal or 0))
        
        # Calcular total pagado (solo pagos aprobados)
        total_pagado = PagoEnLinea.objects.filter(
            plan_tratamiento=plan_tratamiento,
            estado='aprobado',
            origen_tipo='plan_completo'
        ).aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        saldo_pendiente = max(total_plan - total_pagado, Decimal('0'))
        
        # Calcular porcentaje pagado
        if total_plan > 0:
            porcentaje_pagado = (total_pagado / total_plan) * Decimal('100')
        else:
            porcentaje_pagado = Decimal('0')
        
        # Contar items por estado de pago
        items = plan_tratamiento.itemplandetratamiento_set.exclude(
            estado_item='Cancelado'
        )
        
        items_pagados = sum(1 for item in items if item.esta_pagado())
        items_pendientes = items.count() - items_pagados
        
        return {
            'total_plan': float(total_plan),
            'total_pagado': float(total_pagado),
            'saldo_pendiente': float(saldo_pendiente),
            'porcentaje_pagado': float(porcentaje_pagado),
            'items_totales': items.count(),
            'items_pagados': items_pagados,
            'items_pendientes': items_pendientes,
            'esta_pagado_completo': saldo_pendiente <= Decimal('0')
        }
    
    @staticmethod
    def calcular_resumen_items(plan_tratamiento) -> List[Dict]:
        """
        Genera resumen de pagos por item del plan.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
        
        Returns:
            Lista de diccionarios con info de pago por item
        """
        items = plan_tratamiento.itemplandetratamiento_set.exclude(
            estado_item='Cancelado'
        )
        
        resumen = []
        for item in items:
            costo_total = Decimal(str(item.costofinal or 0))
            monto_pagado = item.calcular_monto_pagado()
            saldo_pendiente = item.calcular_saldo_pendiente()
            porcentaje_pagado = item.calcular_porcentaje_pagado()
            
            resumen.append({
                'item_id': item.id,
                'servicio_nombre': item.idservicio.nombre if item.idservicio else 'Sin servicio',
                'costo_total': float(costo_total),
                'monto_pagado': float(monto_pagado),
                'saldo_pendiente': float(saldo_pendiente),
                'porcentaje_pagado': float(porcentaje_pagado),
                'esta_pagado': item.esta_pagado(),
                'puede_pagarse': item.puede_pagarse()[0]
            })
        
        return resumen
    
    @staticmethod
    def validar_monto_pago(plan_tratamiento, monto_pago: Decimal) -> Tuple[bool, str]:
        """
        Valida si un monto de pago es válido para el plan.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
            monto_pago: Monto a validar
        
        Returns:
            Tuple (es_valido: bool, mensaje: str)
        """
        if monto_pago <= Decimal('0'):
            return False, "El monto del pago debe ser mayor a 0"
        
        saldo_pendiente = plan_tratamiento.calcular_saldo_pendiente()
        
        if monto_pago > saldo_pendiente:
            return False, f"El monto del pago (${monto_pago}) excede el saldo pendiente (${saldo_pendiente})"
        
        return True, "Monto válido"
    
    @staticmethod
    def calcular_distribucion_pago(plan_tratamiento, monto_pago: Decimal, 
                                   items_seleccionados: Optional[List[int]] = None) -> Dict:
        """
        Calcula cómo distribuir un pago entre los items del plan.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
            monto_pago: Monto total a distribuir
            items_seleccionados: Lista de IDs de items (None = todos los items)
        
        Returns:
            Dict con distribución del pago por item
        """
        from decimal import ROUND_HALF_UP
        
        # Obtener items a pagar
        if items_seleccionados:
            items = plan_tratamiento.itemplandetratamiento_set.filter(
                id__in=items_seleccionados
            ).exclude(estado_item='Cancelado')
        else:
            items = plan_tratamiento.itemplandetratamiento_set.exclude(
                estado_item='Cancelado'
            )
        
        # Filtrar items que pueden recibir pagos
        items_pendientes = [item for item in items if item.calcular_saldo_pendiente() > 0]
        
        if not items_pendientes:
            return {
                'distribucion': [],
                'monto_distribuido': 0,
                'monto_sobrante': float(monto_pago)
            }
        
        # Calcular saldo total de items pendientes
        saldo_total = sum(item.calcular_saldo_pendiente() for item in items_pendientes)
        
        # Si el pago es menor al saldo total, distribuir proporcionalmente
        if monto_pago < saldo_total:
            distribucion = []
            monto_restante = monto_pago
            
            for i, item in enumerate(items_pendientes):
                saldo_item = item.calcular_saldo_pendiente()
                
                # Calcular proporción
                if i < len(items_pendientes) - 1:
                    # Para todos excepto el último, calcular proporción
                    proporcion = saldo_item / saldo_total
                    monto_item = (monto_pago * proporcion).quantize(
                        Decimal('0.01'), 
                        rounding=ROUND_HALF_UP
                    )
                else:
                    # El último item recibe el resto (evita errores de redondeo)
                    monto_item = monto_restante
                
                # Asegurar que no excede el saldo del item
                monto_item = min(monto_item, saldo_item)
                
                distribucion.append({
                    'item_id': item.id,
                    'servicio_nombre': item.idservicio.nombre if item.idservicio else 'Sin servicio',
                    'saldo_pendiente': float(saldo_item),
                    'monto_a_pagar': float(monto_item),
                    'saldo_resultante': float(saldo_item - monto_item)
                })
                
                monto_restante -= monto_item
            
            return {
                'distribucion': distribucion,
                'monto_distribuido': float(monto_pago),
                'monto_sobrante': 0
            }
        
        # Si el pago cubre todo, pagar el saldo de cada item
        else:
            distribucion = []
            monto_usado = Decimal('0')
            
            for item in items_pendientes:
                saldo_item = item.calcular_saldo_pendiente()
                
                distribucion.append({
                    'item_id': item.id,
                    'servicio_nombre': item.idservicio.nombre if item.idservicio else 'Sin servicio',
                    'saldo_pendiente': float(saldo_item),
                    'monto_a_pagar': float(saldo_item),
                    'saldo_resultante': 0.0
                })
                
                monto_usado += saldo_item
            
            return {
                'distribucion': distribucion,
                'monto_distribuido': float(monto_usado),
                'monto_sobrante': float(monto_pago - monto_usado)
            }
    
    @staticmethod
    def calcular_historial_pagos(plan_tratamiento) -> List[Dict]:
        """
        Genera historial completo de pagos del plan.
        
        Args:
            plan_tratamiento: Instancia de Plandetratamiento
        
        Returns:
            Lista de pagos con sus detalles
        """
        from api.models import PagoEnLinea
        
        pagos = PagoEnLinea.objects.filter(
            plan_tratamiento=plan_tratamiento
        ).order_by('-fecha_creacion')
        
        historial = []
        for pago in pagos:
            historial.append({
                'id': pago.id,
                'codigo_pago': pago.codigo_pago,
                'fecha': pago.fecha_creacion.isoformat() if pago.fecha_creacion else None,
                'monto': float(pago.monto),
                'estado': pago.estado,
                'estado_display': pago.get_estado_display(),
                'metodo_pago': pago.metodo_pago,
                'metodo_display': pago.get_metodo_pago_display(),
                'origen': pago.origen,
                'descripcion': pago.descripcion,
                'tiene_comprobante': hasattr(pago, 'comprobante'),
                'puede_reintentarse': pago.puede_reintentarse(),
                'puede_anularse': pago.puede_anularse(),
                'puede_reembolsarse': pago.puede_reembolsarse()
            })
        
        return historial
    
    @staticmethod
    def validar_pago_item_individual(item, monto_pago: Decimal) -> Tuple[bool, str]:
        """
        Valida un pago para un item individual.
        
        Args:
            item: Instancia de Itemplandetratamiento
            monto_pago: Monto a validar
        
        Returns:
            Tuple (es_valido: bool, mensaje: str)
        """
        puede_pagar, razon = item.puede_pagarse()
        
        if not puede_pagar:
            return False, razon
        
        if monto_pago <= Decimal('0'):
            return False, "El monto del pago debe ser mayor a 0"
        
        saldo_pendiente = item.calcular_saldo_pendiente()
        
        if monto_pago > saldo_pendiente:
            return False, f"El monto del pago (${monto_pago}) excede el saldo del item (${saldo_pendiente})"
        
        return True, "Monto válido"
    
    @staticmethod
    def validar_pago_consulta(consulta, monto_pago: Decimal) -> Tuple[bool, str]:
        """
        Valida un pago para una consulta.
        
        Args:
            consulta: Instancia de Consulta
            monto_pago: Monto a validar
        
        Returns:
            Tuple (es_valido: bool, mensaje: str)
        """
        puede_pagar, razon = consulta.puede_pagarse()
        
        if not puede_pagar:
            return False, razon
        
        if monto_pago <= Decimal('0'):
            return False, "El monto del pago debe ser mayor a 0"
        
        saldo_pendiente = consulta.calcular_saldo_pendiente()
        
        if saldo_pendiente <= Decimal('0'):
            return False, "La consulta no tiene saldo pendiente"
        
        if monto_pago > saldo_pendiente:
            return False, f"El monto del pago (${monto_pago}) excede el saldo de la consulta (${saldo_pendiente})"
        
        return True, "Monto válido"
    
    @staticmethod
    def obtener_estadisticas_empresa(empresa) -> Dict:
        """
        Genera estadísticas de pagos para toda la empresa.
        
        Args:
            empresa: Instancia de Empresa
        
        Returns:
            Dict con estadísticas generales
        """
        from api.models import PagoEnLinea
        
        # Pagos aprobados
        pagos_aprobados = PagoEnLinea.objects.filter(
            empresa=empresa,
            estado='aprobado'
        )
        
        total_recaudado = pagos_aprobados.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        # Contar pagos por estado
        from django.db.models import Count
        pagos_por_estado = PagoEnLinea.objects.filter(
            empresa=empresa
        ).values('estado').annotate(
            cantidad=Count('id')
        )
        
        # Pagos pendientes
        planes_con_saldo = 0
        saldo_total_pendiente = Decimal('0')
        
        from api.models import Plandetratamiento
        planes_aprobados = Plandetratamiento.objects.filter(
            empresa=empresa,
            estado_plan='Aprobado'
        )
        
        for plan in planes_aprobados:
            saldo = plan.calcular_saldo_pendiente()
            if saldo > 0:
                planes_con_saldo += 1
                saldo_total_pendiente += saldo
        
        return {
            'total_recaudado': float(total_recaudado),
            'cantidad_pagos_aprobados': pagos_aprobados.count(),
            'pagos_por_estado': {p['estado']: p['cantidad'] for p in pagos_por_estado},
            'planes_con_saldo_pendiente': planes_con_saldo,
            'saldo_total_pendiente': float(saldo_total_pendiente)
        }
