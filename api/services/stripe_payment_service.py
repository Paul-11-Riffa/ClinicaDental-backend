"""
SP3-T009: Servicio de Integración con Stripe
Gestiona pagos, Payment Intents, confirmaciones y reembolsos con Stripe.
"""

import stripe
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone

from api.models import PagoEnLinea, ComprobanteDigital

logger = logging.getLogger(__name__)

# Configurar Stripe API key
if settings.STRIPE_ENABLED:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """
    Servicio para gestionar pagos con Stripe.
    Maneja Payment Intents, confirmaciones, capturas y reembolsos.
    """
    
    @staticmethod
    def is_enabled() -> bool:
        """Verifica si Stripe está habilitado."""
        return settings.STRIPE_ENABLED
    
    @staticmethod
    def crear_payment_intent(
        pago: PagoEnLinea,
        descripcion: str = None,
        metadata: dict = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Crea un Payment Intent en Stripe para un pago.
        
        Args:
            pago: Instancia de PagoEnLinea
            descripcion: Descripción del pago (opcional)
            metadata: Metadata adicional (opcional)
        
        Returns:
            Tuple (exito: bool, mensaje: str, payment_intent: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        try:
            # Convertir monto a centavos (Stripe usa centavos)
            monto_centavos = int(pago.monto * 100)
            
            # Preparar metadata
            metadata_completo = {
                'pago_id': str(pago.id),
                'codigo_pago': pago.codigo_pago,
                'empresa_id': str(pago.empresa.id) if pago.empresa else None,
                'origen_tipo': pago.origen_tipo,
            }
            
            if pago.plan_tratamiento:
                metadata_completo['plan_tratamiento_id'] = str(pago.plan_tratamiento.id)
                if pago.plan_tratamiento.codpaciente:
                    paciente = pago.plan_tratamiento.codpaciente
                    if paciente.codusuario:
                        metadata_completo['paciente_nombre'] = paciente.codusuario.nombre
                        metadata_completo['paciente_email'] = paciente.codusuario.email
            
            elif pago.consulta:
                metadata_completo['consulta_id'] = str(pago.consulta.id)
                if pago.consulta.codpaciente:
                    paciente = pago.consulta.codpaciente
                    if paciente.codusuario:
                        metadata_completo['paciente_nombre'] = paciente.codusuario.nombre
                        metadata_completo['paciente_email'] = paciente.codusuario.email
            
            # Agregar metadata personalizado
            if metadata:
                metadata_completo.update(metadata)
            
            # Descripción del pago
            if not descripcion:
                if pago.plan_tratamiento:
                    descripcion = f"Pago de Plan de Tratamiento - {pago.codigo_pago}"
                elif pago.consulta:
                    descripcion = f"Pago de Consulta - {pago.codigo_pago}"
                else:
                    descripcion = f"Pago - {pago.codigo_pago}"
            
            # Crear Payment Intent
            payment_intent = stripe.PaymentIntent.create(
                amount=monto_centavos,
                currency=pago.moneda.lower(),
                payment_method_types=settings.STRIPE_PAYMENT_METHOD_TYPES,
                capture_method=settings.STRIPE_CAPTURE_METHOD,
                description=descripcion,
                metadata=metadata_completo,
                # Configuración adicional
                statement_descriptor="CLINICA DENTAL",  # Aparece en el estado de cuenta
                receipt_email=metadata_completo.get('paciente_email'),
            )
            
            # Guardar Payment Intent ID en el pago
            pago.stripe_payment_intent_id = payment_intent['id']
            pago.stripe_metadata = payment_intent.get('metadata', {})
            pago.estado = 'procesando'
            pago.ultimo_intento = timezone.now()
            pago.numero_intentos += 1
            pago.save(update_fields=[
                'stripe_payment_intent_id', 
                'stripe_metadata', 
                'estado',
                'ultimo_intento',
                'numero_intentos'
            ])
            
            logger.info(
                f"Payment Intent creado: {payment_intent['id']} para pago {pago.codigo_pago}"
            )
            
            return True, "Payment Intent creado exitosamente", payment_intent
        
        except stripe.error.CardError as e:
            # Tarjeta rechazada
            error_msg = f"Tarjeta rechazada: {e.user_message}"
            logger.error(f"CardError para pago {pago.codigo_pago}: {error_msg}")
            return False, error_msg, None
        
        except stripe.error.InvalidRequestError as e:
            # Parámetros inválidos
            error_msg = f"Error en parámetros: {str(e)}"
            logger.error(f"InvalidRequestError para pago {pago.codigo_pago}: {error_msg}")
            return False, error_msg, None
        
        except stripe.error.AuthenticationError as e:
            # Error de autenticación con Stripe
            error_msg = "Error de autenticación con Stripe"
            logger.error(f"AuthenticationError: {str(e)}")
            return False, error_msg, None
        
        except stripe.error.APIConnectionError as e:
            # Error de conexión con Stripe
            error_msg = "Error de conexión con la pasarela de pagos"
            logger.error(f"APIConnectionError: {str(e)}")
            return False, error_msg, None
        
        except stripe.error.StripeError as e:
            # Error genérico de Stripe
            error_msg = f"Error en procesamiento: {str(e)}"
            logger.error(f"StripeError para pago {pago.codigo_pago}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            # Error inesperado
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado creando Payment Intent para {pago.codigo_pago}")
            return False, error_msg, None
    
    @staticmethod
    def confirmar_payment_intent(
        payment_intent_id: str,
        payment_method_id: str = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Confirma un Payment Intent.
        
        Args:
            payment_intent_id: ID del Payment Intent
            payment_method_id: ID del método de pago (opcional si ya está adjunto)
        
        Returns:
            Tuple (exito: bool, mensaje: str, payment_intent: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        try:
            params = {}
            if payment_method_id:
                params['payment_method'] = payment_method_id
            
            payment_intent = stripe.PaymentIntent.confirm(
                payment_intent_id,
                **params
            )
            
            logger.info(f"Payment Intent confirmado: {payment_intent_id}")
            
            return True, "Pago confirmado", payment_intent
        
        except stripe.error.StripeError as e:
            error_msg = f"Error confirmando pago: {str(e)}"
            logger.error(f"Error confirmando Payment Intent {payment_intent_id}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado confirmando Payment Intent {payment_intent_id}")
            return False, error_msg, None
    
    @staticmethod
    def capturar_payment_intent(payment_intent_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Captura un Payment Intent (para capture_method='manual').
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            Tuple (exito: bool, mensaje: str, payment_intent: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        try:
            payment_intent = stripe.PaymentIntent.capture(payment_intent_id)
            
            logger.info(f"Payment Intent capturado: {payment_intent_id}")
            
            return True, "Pago capturado", payment_intent
        
        except stripe.error.StripeError as e:
            error_msg = f"Error capturando pago: {str(e)}"
            logger.error(f"Error capturando Payment Intent {payment_intent_id}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado capturando Payment Intent {payment_intent_id}")
            return False, error_msg, None
    
    @staticmethod
    def cancelar_payment_intent(payment_intent_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Cancela un Payment Intent.
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            Tuple (exito: bool, mensaje: str, payment_intent: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        try:
            payment_intent = stripe.PaymentIntent.cancel(payment_intent_id)
            
            logger.info(f"Payment Intent cancelado: {payment_intent_id}")
            
            return True, "Pago cancelado", payment_intent
        
        except stripe.error.StripeError as e:
            error_msg = f"Error cancelando pago: {str(e)}"
            logger.error(f"Error cancelando Payment Intent {payment_intent_id}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado cancelando Payment Intent {payment_intent_id}")
            return False, error_msg, None
    
    @staticmethod
    def crear_reembolso(
        pago: PagoEnLinea,
        monto: Decimal = None,
        razon: str = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Crea un reembolso en Stripe.
        
        Args:
            pago: Instancia de PagoEnLinea
            monto: Monto a reembolsar (None = total)
            razon: Razón del reembolso
        
        Returns:
            Tuple (exito: bool, mensaje: str, refund: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        if not pago.stripe_charge_id and not pago.stripe_payment_intent_id:
            return False, "No hay información de pago en Stripe para reembolsar", None
        
        try:
            params = {}
            
            # Identificar el pago (preferir charge_id, luego payment_intent)
            if pago.stripe_charge_id:
                params['charge'] = pago.stripe_charge_id
            else:
                params['payment_intent'] = pago.stripe_payment_intent_id
            
            # Monto a reembolsar (en centavos)
            if monto:
                params['amount'] = int(monto * 100)
            
            # Razón del reembolso
            if razon:
                params['reason'] = 'requested_by_customer'  # o 'fraudulent', 'duplicate'
                params['metadata'] = {'razon': razon}
            
            # Crear reembolso
            refund = stripe.Refund.create(**params)
            
            logger.info(
                f"Reembolso creado: {refund['id']} para pago {pago.codigo_pago}"
            )
            
            return True, "Reembolso creado exitosamente", refund
        
        except stripe.error.StripeError as e:
            error_msg = f"Error creando reembolso: {str(e)}"
            logger.error(f"Error creando reembolso para pago {pago.codigo_pago}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado creando reembolso para {pago.codigo_pago}")
            return False, error_msg, None
    
    @staticmethod
    def obtener_payment_intent(payment_intent_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Obtiene información de un Payment Intent.
        
        Args:
            payment_intent_id: ID del Payment Intent
        
        Returns:
            Tuple (exito: bool, mensaje: str, payment_intent: dict)
        """
        if not StripePaymentService.is_enabled():
            return False, "Stripe no está configurado", None
        
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            return True, "Payment Intent obtenido", payment_intent
        
        except stripe.error.StripeError as e:
            error_msg = f"Error obteniendo Payment Intent: {str(e)}"
            logger.error(f"Error obteniendo Payment Intent {payment_intent_id}: {error_msg}")
            return False, error_msg, None
        
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.exception(f"Error inesperado obteniendo Payment Intent {payment_intent_id}")
            return False, error_msg, None
    
    @staticmethod
    def procesar_webhook_payment_intent_succeeded(payment_intent_data: dict) -> Tuple[bool, str]:
        """
        Procesa el webhook de payment_intent.succeeded.
        Actualiza el estado del pago a 'aprobado'.
        
        Args:
            payment_intent_data: Datos del Payment Intent desde webhook
        
        Returns:
            Tuple (exito: bool, mensaje: str)
        """
        try:
            payment_intent_id = payment_intent_data['id']
            
            # Buscar el pago
            try:
                pago = PagoEnLinea.objects.get(stripe_payment_intent_id=payment_intent_id)
            except PagoEnLinea.DoesNotExist:
                return False, f"Pago no encontrado para Payment Intent {payment_intent_id}"
            
            # Actualizar estado
            pago.estado = 'aprobado'
            pago.fecha_aprobacion = timezone.now()
            pago.fecha_procesamiento = timezone.now()
            
            # Guardar charge_id si está disponible
            if 'charges' in payment_intent_data and payment_intent_data['charges']['data']:
                charge = payment_intent_data['charges']['data'][0]
                pago.stripe_charge_id = charge['id']
            
            # Actualizar metadata
            if 'metadata' in payment_intent_data:
                pago.stripe_metadata = payment_intent_data['metadata']
            
            pago.save()
            
            # Bloquear items pagados del plan
            if pago.plan_tratamiento:
                pago.plan_tratamiento.bloquear_items_pagados()
            
            # Crear comprobante digital automáticamente
            ComprobanteDigital.crear_comprobante(pago)
            
            logger.info(f"Pago {pago.codigo_pago} aprobado vía webhook")
            
            return True, f"Pago {pago.codigo_pago} aprobado"
        
        except Exception as e:
            error_msg = f"Error procesando webhook payment_intent.succeeded: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
    
    @staticmethod
    def procesar_webhook_payment_intent_failed(payment_intent_data: dict) -> Tuple[bool, str]:
        """
        Procesa el webhook de payment_intent.payment_failed.
        Actualiza el estado del pago a 'rechazado'.
        
        Args:
            payment_intent_data: Datos del Payment Intent desde webhook
        
        Returns:
            Tuple (exito: bool, mensaje: str)
        """
        try:
            payment_intent_id = payment_intent_data['id']
            
            # Buscar el pago
            try:
                pago = PagoEnLinea.objects.get(stripe_payment_intent_id=payment_intent_id)
            except PagoEnLinea.DoesNotExist:
                return False, f"Pago no encontrado para Payment Intent {payment_intent_id}"
            
            # Actualizar estado
            pago.estado = 'rechazado'
            pago.fecha_procesamiento = timezone.now()
            
            # Guardar motivo de rechazo
            if 'last_payment_error' in payment_intent_data:
                error = payment_intent_data['last_payment_error']
                pago.motivo_rechazo = error.get('message', 'Error desconocido')
            else:
                pago.motivo_rechazo = "Pago rechazado por el procesador"
            
            pago.save()
            
            logger.info(f"Pago {pago.codigo_pago} rechazado vía webhook")
            
            return True, f"Pago {pago.codigo_pago} rechazado"
        
        except Exception as e:
            error_msg = f"Error procesando webhook payment_intent.payment_failed: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
    
    @staticmethod
    def procesar_webhook_charge_refunded(charge_data: dict) -> Tuple[bool, str]:
        """
        Procesa el webhook de charge.refunded.
        Actualiza el estado del pago a 'reembolsado'.
        
        Args:
            charge_data: Datos del Charge desde webhook
        
        Returns:
            Tuple (exito: bool, mensaje: str)
        """
        try:
            charge_id = charge_data['id']
            
            # Buscar el pago
            try:
                pago = PagoEnLinea.objects.get(stripe_charge_id=charge_id)
            except PagoEnLinea.DoesNotExist:
                # Intentar buscar por payment_intent_id
                payment_intent_id = charge_data.get('payment_intent')
                if payment_intent_id:
                    try:
                        pago = PagoEnLinea.objects.get(stripe_payment_intent_id=payment_intent_id)
                    except PagoEnLinea.DoesNotExist:
                        return False, f"Pago no encontrado para Charge {charge_id}"
                else:
                    return False, f"Pago no encontrado para Charge {charge_id}"
            
            # Actualizar estado
            pago.estado = 'reembolsado'
            pago.save()
            
            logger.info(f"Pago {pago.codigo_pago} reembolsado vía webhook")
            
            return True, f"Pago {pago.codigo_pago} reembolsado"
        
        except Exception as e:
            error_msg = f"Error procesando webhook charge.refunded: {str(e)}"
            logger.exception(error_msg)
            return False, error_msg
    
    @staticmethod
    def verificar_webhook_signature(payload: bytes, sig_header: str) -> Tuple[bool, str, Optional[dict]]:
        """
        Verifica la firma del webhook de Stripe.
        
        Args:
            payload: Cuerpo del webhook (bytes)
            sig_header: Header Stripe-Signature
        
        Returns:
            Tuple (valido: bool, mensaje: str, event: dict)
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            return False, "Webhook secret no configurado", None
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )
            
            return True, "Firma válida", event
        
        except ValueError as e:
            # Payload inválido
            return False, f"Payload inválido: {str(e)}", None
        
        except stripe.error.SignatureVerificationError as e:
            # Firma inválida
            return False, f"Firma inválida: {str(e)}", None
        
        except Exception as e:
            # Error inesperado
            return False, f"Error verificando firma: {str(e)}", None
