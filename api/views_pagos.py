"""
SP3-T009: Views para Sistema de Pagos en Línea
ViewSets y endpoints para gestión de pagos, webhooks de Stripe.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import json
import logging

from .models import PagoEnLinea, DetallePagoItem, ComprobanteDigital
from .serializers_pagos import (
    PagoEnLineaSerializer,
    PagoEnLineaListSerializer,
    CrearPagoPlanSerializer,
    CrearPagoConsultaSerializer,
    ActualizarEstadoPagoSerializer,
    ResumenFinancieroPlanSerializer
)
from .services.stripe_payment_service import StripePaymentService
from .services.calculador_pagos import CalculadorPagos

logger = logging.getLogger(__name__)


class PagoEnLineaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de pagos en línea.
    
    list: Lista todos los pagos de la empresa
    retrieve: Obtiene detalle de un pago
    create: Crea un nuevo pago (plan o consulta)
    update: Actualiza un pago (solo estados permitidos)
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PagoEnLineaListSerializer
        elif self.action in ['crear_pago_plan', 'create']:
            return CrearPagoPlanSerializer
        elif self.action == 'crear_pago_consulta':
            return CrearPagoConsultaSerializer
        elif self.action == 'actualizar_estado':
            return ActualizarEstadoPagoSerializer
        return PagoEnLineaSerializer
    
    def get_queryset(self):
        """Filtra pagos por empresa (tenant)."""
        empresa = getattr(self.request, 'tenant', None)
        if empresa:
            return PagoEnLinea.objects.filter(empresa=empresa).select_related(
                'plan_tratamiento',
                'consulta',
                'usuario',
                'empresa'
            ).prefetch_related(
                'detalles_pago',
                'detalles_pago__item_plan'
            ).order_by('-fecha_creacion')
        return PagoEnLinea.objects.none()
    
    @action(detail=False, methods=['post'], url_path='crear-pago-plan')
    def crear_pago_plan(self, request):
        """
        Crea un pago para un plan de tratamiento.
        
        Body:
            - plan_tratamiento_id (int): ID del plan
            - monto (decimal): Monto a pagar
            - metodo_pago (str): tarjeta, transferencia, qr
            - items_seleccionados (list, opcional): IDs de items específicos
            - descripcion (str, opcional): Descripción del pago
        """
        serializer = CrearPagoPlanSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el pago
        pago = serializer.save()
        
        # Si el método es tarjeta, crear Payment Intent en Stripe
        if pago.metodo_pago == 'tarjeta' and StripePaymentService.is_enabled():
            exito, mensaje, payment_intent = StripePaymentService.crear_payment_intent(pago)
            
            if not exito:
                # Si falla Stripe, marcar como rechazado
                pago.estado = 'rechazado'
                pago.motivo_rechazo = mensaje
                pago.save()
                
                return Response({
                    'error': 'Error creando Payment Intent',
                    'detalle': mensaje,
                    'pago': PagoEnLineaSerializer(pago).data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Retornar con client_secret para frontend
            return Response({
                'pago': PagoEnLineaSerializer(pago).data,
                'stripe': {
                    'client_secret': payment_intent['client_secret'],
                    'payment_intent_id': payment_intent['id']
                },
                'mensaje': 'Pago creado. Completa la transacción con Stripe.'
            }, status=status.HTTP_201_CREATED)
        
        # Para otros métodos de pago, retornar el pago creado
        return Response({
            'pago': PagoEnLineaSerializer(pago).data,
            'mensaje': 'Pago creado exitosamente'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='crear-pago-consulta')
    def crear_pago_consulta(self, request):
        """
        Crea un pago para una consulta.
        
        Body:
            - consulta_id (int): ID de la consulta
            - monto (decimal): Monto a pagar
            - metodo_pago (str): tarjeta, transferencia, qr
            - tipo_pago_consulta (str, opcional): prepago, copago, saldo_pendiente
            - descripcion (str, opcional): Descripción del pago
        """
        serializer = CrearPagoConsultaSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Crear el pago
        pago = serializer.save()
        
        # Si el método es tarjeta, crear Payment Intent en Stripe
        if pago.metodo_pago == 'tarjeta' and StripePaymentService.is_enabled():
            exito, mensaje, payment_intent = StripePaymentService.crear_payment_intent(pago)
            
            if not exito:
                pago.estado = 'rechazado'
                pago.motivo_rechazo = mensaje
                pago.save()
                
                return Response({
                    'error': 'Error creando Payment Intent',
                    'detalle': mensaje,
                    'pago': PagoEnLineaSerializer(pago).data
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'pago': PagoEnLineaSerializer(pago).data,
                'stripe': {
                    'client_secret': payment_intent['client_secret'],
                    'payment_intent_id': payment_intent['id']
                },
                'mensaje': 'Pago creado. Completa la transacción con Stripe.'
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            'pago': PagoEnLineaSerializer(pago).data,
            'mensaje': 'Pago creado exitosamente'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], url_path='confirmar-pago')
    def confirmar_pago(self, request, pk=None):
        """
        Confirma un pago (marca como aprobado).
        Para pagos con tarjeta, verifica estado en Stripe.
        """
        pago = self.get_object()
        
        # Verificar que el pago esté en estado correcto
        if pago.estado not in ['pendiente', 'procesando']:
            return Response({
                'error': 'El pago no puede ser confirmado',
                'estado_actual': pago.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si es pago con tarjeta, verificar con Stripe
        if pago.metodo_pago == 'tarjeta' and pago.stripe_payment_intent_id:
            exito, mensaje, payment_intent = StripePaymentService.obtener_payment_intent(
                pago.stripe_payment_intent_id
            )
            
            if not exito:
                return Response({
                    'error': 'Error verificando pago con Stripe',
                    'detalle': mensaje
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verificar estado del Payment Intent
            if payment_intent['status'] != 'succeeded':
                return Response({
                    'error': 'El pago no ha sido completado en Stripe',
                    'estado_stripe': payment_intent['status']
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirmar pago
        with transaction.atomic():
            pago.estado = 'aprobado'
            pago.fecha_aprobacion = timezone.now()
            pago.fecha_procesamiento = timezone.now()
            pago.save()
            
            # Bloquear items pagados
            if pago.plan_tratamiento:
                pago.plan_tratamiento.bloquear_items_pagados()
            
            # Crear comprobante
            try:
                ComprobanteDigital.crear_comprobante(pago)
            except Exception as e:
                logger.error(f"Error creando comprobante para pago {pago.codigo_pago}: {e}")
        
        return Response({
            'pago': PagoEnLineaSerializer(pago).data,
            'mensaje': 'Pago confirmado exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='cancelar-pago')
    def cancelar_pago(self, request, pk=None):
        """Cancela un pago pendiente."""
        pago = self.get_object()
        
        if not pago.puede_anularse():
            return Response({
                'error': 'El pago no puede ser cancelado',
                'estado_actual': pago.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Si es pago con Stripe, cancelar Payment Intent
        if pago.metodo_pago == 'tarjeta' and pago.stripe_payment_intent_id:
            exito, mensaje, _ = StripePaymentService.cancelar_payment_intent(
                pago.stripe_payment_intent_id
            )
            
            if not exito:
                logger.warning(f"Error cancelando Payment Intent: {mensaje}")
        
        # Cancelar pago
        pago.estado = 'cancelado'
        pago.save()
        
        return Response({
            'pago': PagoEnLineaSerializer(pago).data,
            'mensaje': 'Pago cancelado exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='reembolsar')
    def reembolsar_pago(self, request, pk=None):
        """
        Crea un reembolso para un pago aprobado.
        
        Body:
            - monto (decimal, opcional): Monto a reembolsar (default: total)
            - razon (str): Razón del reembolso
        """
        pago = self.get_object()
        
        if not pago.puede_reembolsarse():
            return Response({
                'error': 'El pago no puede ser reembolsado',
                'estado_actual': pago.estado
            }, status=status.HTTP_400_BAD_REQUEST)
        
        monto = request.data.get('monto')
        razon = request.data.get('razon', 'Reembolso solicitado')
        
        if monto:
            monto = Decimal(str(monto))
            if monto > pago.monto:
                return Response({
                    'error': 'El monto a reembolsar excede el monto del pago'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear reembolso en Stripe si aplica
        if pago.metodo_pago == 'tarjeta':
            exito, mensaje, refund = StripePaymentService.crear_reembolso(
                pago, monto, razon
            )
            
            if not exito:
                return Response({
                    'error': 'Error creando reembolso en Stripe',
                    'detalle': mensaje
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar estado del pago
        pago.estado = 'reembolsado'
        pago.save()
        
        return Response({
            'pago': PagoEnLineaSerializer(pago).data,
            'mensaje': 'Reembolso procesado exitosamente'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='resumen-plan/(?P<plan_id>[^/.]+)')
    def resumen_plan(self, request, plan_id=None):
        """
        Obtiene resumen financiero de un plan de tratamiento.
        """
        from .models import Plandetratamiento
        
        empresa = getattr(request, 'tenant', None)
        
        try:
            plan = Plandetratamiento.objects.get(id=plan_id, empresa=empresa)
        except Plandetratamiento.DoesNotExist:
            return Response({
                'error': 'Plan de tratamiento no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Obtener resumen
        resumen = CalculadorPagos.calcular_resumen_plan(plan)
        resumen['plan_id'] = plan.id
        
        # Obtener resumen de items
        resumen_items = CalculadorPagos.calcular_resumen_items(plan)
        
        # Obtener historial de pagos
        historial = CalculadorPagos.calcular_historial_pagos(plan)
        
        return Response({
            'resumen_general': resumen,
            'items': resumen_items,
            'historial_pagos': historial
        }, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """
    Endpoint para recibir webhooks de Stripe.
    
    Eventos manejados:
    - payment_intent.succeeded: Pago exitoso
    - payment_intent.payment_failed: Pago fallido
    - charge.refunded: Reembolso procesado
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    if not sig_header:
        logger.warning("Webhook sin firma Stripe-Signature")
        return HttpResponse('Firma faltante', status=400)
    
    # Verificar firma
    valido, mensaje, event = StripePaymentService.verificar_webhook_signature(
        payload, sig_header
    )
    
    if not valido:
        logger.warning(f"Webhook con firma inválida: {mensaje}")
        return HttpResponse(mensaje, status=400)
    
    # Procesar evento
    event_type = event['type']
    event_data = event['data']['object']
    
    logger.info(f"Webhook recibido: {event_type} - {event_data.get('id')}")
    
    try:
        if event_type == 'payment_intent.succeeded':
            exito, mensaje = StripePaymentService.procesar_webhook_payment_intent_succeeded(event_data)
            
        elif event_type == 'payment_intent.payment_failed':
            exito, mensaje = StripePaymentService.procesar_webhook_payment_intent_failed(event_data)
            
        elif event_type == 'charge.refunded':
            exito, mensaje = StripePaymentService.procesar_webhook_charge_refunded(event_data)
            
        else:
            logger.info(f"Evento no manejado: {event_type}")
            return HttpResponse('Evento no manejado', status=200)
        
        if exito:
            logger.info(f"Webhook procesado exitosamente: {mensaje}")
            return HttpResponse(mensaje, status=200)
        else:
            logger.error(f"Error procesando webhook: {mensaje}")
            return HttpResponse(mensaje, status=400)
    
    except Exception as e:
        logger.exception(f"Error inesperado procesando webhook {event_type}")
        return HttpResponse(f'Error: {str(e)}', status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def verificar_comprobante(request, codigo_verificacion):
    """
    Endpoint público para verificar un comprobante digital.
    
    GET /api/verificar-comprobante-pago/{codigo_verificacion}/
    """
    try:
        comprobante = ComprobanteDigital.objects.select_related(
            'pago',
            'pago__plan_tratamiento',
            'pago__consulta'
        ).get(codigo_verificacion=codigo_verificacion)
        
        from .serializers_pagos import ComprobanteDigitalSerializer
        
        return Response({
            'comprobante': ComprobanteDigitalSerializer(comprobante).data,
            'pago': PagoEnLineaSerializer(comprobante.pago).data,
            'valido': comprobante.esta_activo()
        }, status=status.HTTP_200_OK)
    
    except ComprobanteDigital.DoesNotExist:
        return Response({
            'error': 'Comprobante no encontrado',
            'valido': False
        }, status=status.HTTP_404_NOT_FOUND)
