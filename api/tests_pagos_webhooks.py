"""
SP3-T009: Tests de Webhooks - Stripe
Tests para el endpoint de webhooks de Stripe y procesamiento de eventos.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
from decimal import Decimal
import json

from api.models import (
    Empresa, Usuario, Tipodeusuario, Paciente,
    Plandetratamiento, PagoEnLinea, ComprobanteDigital
)


class StripeWebhookTestCase(APITestCase):
    """Tests para el endpoint de webhooks de Stripe."""
    
    def setUp(self):
        """Configuración inicial."""
        self.empresa = Empresa.objects.create(
            nombre_empresa="Clínica Test",
            subdomain="test",
            email_empresa="test@clinic.com"
        )
        
        self.tipo_usuario = Tipodeusuario.objects.create(nombre="Paciente")
        self.django_user = User.objects.create_user(username='test', password='test')
        self.usuario = Usuario.objects.create(
            user=self.django_user,
            empresa=self.empresa,
            idtipodeusuario=self.tipo_usuario,
            nombre="Test",
            apellido="User",
            email="test@test.com"
        )
        
        self.paciente = Paciente.objects.create(
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com"
        )
        
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
        
        # Cliente API sin autenticación (webhook es público)
        self.client = APIClient()
        
        # URL del webhook
        self.webhook_url = '/api/webhook/stripe/'
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    @patch('api.views_pagos.StripePaymentService.procesar_webhook_payment_intent_succeeded')
    def test_webhook_payment_intent_succeeded(self, mock_procesar, mock_verificar):
        """Test webhook de pago exitoso."""
        # Crear pago en procesamiento
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='procesando',
            stripe_payment_intent_id='pi_test_123',
            usuario=self.usuario
        )
        
        # Mock verificación de firma
        event_data = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'status': 'succeeded',
                    'charges': {
                        'data': [{'id': 'ch_test_123'}]
                    }
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        mock_procesar.return_value = (True, "Pago procesado exitosamente")
        
        # Payload simulado
        payload = json.dumps(event_data).encode('utf-8')
        
        # Request
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar que se llamaron los métodos
        mock_verificar.assert_called_once()
        mock_procesar.assert_called_once()
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    @patch('api.views_pagos.StripePaymentService.procesar_webhook_payment_intent_failed')
    def test_webhook_payment_intent_failed(self, mock_procesar, mock_verificar):
        """Test webhook de pago fallido."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='procesando',
            stripe_payment_intent_id='pi_test_123',
            usuario=self.usuario
        )
        
        event_data = {
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'status': 'failed',
                    'last_payment_error': {
                        'message': 'Card declined'
                    }
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        mock_procesar.return_value = (True, "Pago rechazado")
        
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        mock_procesar.assert_called_once()
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    @patch('api.views_pagos.StripePaymentService.procesar_webhook_charge_refunded')
    def test_webhook_charge_refunded(self, mock_procesar, mock_verificar):
        """Test webhook de reembolso."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='aprobado',
            stripe_charge_id='ch_test_123',
            usuario=self.usuario
        )
        
        event_data = {
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'ch_test_123',
                    'refunded': True
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        mock_procesar.return_value = (True, "Reembolso procesado")
        
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        mock_procesar.assert_called_once()
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_webhook_evento_no_manejado(self, mock_verificar):
        """Test webhook con evento no manejado."""
        event_data = {
            'type': 'customer.created',  # Evento no manejado
            'data': {'object': {}}
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Evento no manejado', response.content)
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_webhook_firma_invalida(self, mock_verificar):
        """Test webhook con firma inválida."""
        mock_verificar.return_value = (False, "Firma inválida", None)
        
        event_data = {'type': 'payment_intent.succeeded'}
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_webhook_sin_firma(self):
        """Test webhook sin header Stripe-Signature."""
        event_data = {'type': 'payment_intent.succeeded'}
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json'
            # Sin HTTP_STRIPE_SIGNATURE
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Firma faltante', response.content)
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    @patch('api.views_pagos.StripePaymentService.procesar_webhook_payment_intent_succeeded')
    def test_webhook_procesamiento_falla(self, mock_procesar, mock_verificar):
        """Test webhook cuando el procesamiento falla."""
        event_data = {
            'type': 'payment_intent.succeeded',
            'data': {'object': {'id': 'pi_inexistente'}}
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        mock_procesar.return_value = (False, "Pago no encontrado")
        
        payload = json.dumps(event_data).encode('utf-8')
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 400)
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_webhook_excepcion_inesperada(self, mock_verificar):
        """Test webhook cuando ocurre excepción inesperada."""
        mock_verificar.side_effect = Exception("Error inesperado")
        
        payload = b'{"test": "data"}'
        
        response = self.client.post(
            self.webhook_url,
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 500)


class WebhookIntegrationTestCase(TestCase):
    """Tests de integración para webhooks completos."""
    
    def setUp(self):
        """Configuración inicial."""
        self.empresa = Empresa.objects.create(
            nombre_empresa="Clínica Test",
            subdomain="test"
        )
        
        self.tipo_usuario = Tipodeusuario.objects.create(nombre="Paciente")
        self.django_user = User.objects.create_user(username='test', password='test')
        self.usuario = Usuario.objects.create(
            user=self.django_user,
            empresa=self.empresa,
            idtipodeusuario=self.tipo_usuario,
            nombre="Test",
            email="test@test.com"
        )
        
        self.paciente = Paciente.objects.create(
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com"
        )
        
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_flujo_completo_pago_exitoso_con_webhook(self, mock_verificar):
        """Test flujo completo: crear pago → webhook → comprobante creado."""
        # 1. Crear pago en procesamiento
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='procesando',
            stripe_payment_intent_id='pi_test_123',
            usuario=self.usuario
        )
        
        self.assertEqual(pago.estado, 'procesando')
        self.assertEqual(ComprobanteDigital.objects.filter(pago=pago).count(), 0)
        
        # 2. Simular webhook de Stripe
        event_data = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'status': 'succeeded',
                    'charges': {
                        'data': [{'id': 'ch_test_123'}]
                    }
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        
        client = APIClient()
        payload = json.dumps(event_data).encode('utf-8')
        
        response = client.post(
            '/api/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 3. Verificar que el pago fue actualizado
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'aprobado')
        self.assertEqual(pago.stripe_charge_id, 'ch_test_123')
        self.assertIsNotNone(pago.fecha_aprobacion)
        
        # 4. Verificar que se creó el comprobante
        self.assertEqual(ComprobanteDigital.objects.filter(pago=pago).count(), 1)
        comprobante = ComprobanteDigital.objects.get(pago=pago)
        self.assertIsNotNone(comprobante.codigo_comprobante)
        self.assertIsNotNone(comprobante.codigo_verificacion)
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_flujo_pago_fallido_con_webhook(self, mock_verificar):
        """Test flujo: pago fallido → webhook → estado rechazado."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='procesando',
            stripe_payment_intent_id='pi_test_123',
            usuario=self.usuario
        )
        
        event_data = {
            'type': 'payment_intent.payment_failed',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'status': 'failed',
                    'last_payment_error': {
                        'message': 'Insufficient funds'
                    }
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        
        client = APIClient()
        payload = json.dumps(event_data).encode('utf-8')
        
        response = client.post(
            '/api/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar estado
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'rechazado')
        self.assertIn('Insufficient funds', pago.motivo_rechazo)
        
        # No debe haber comprobante
        self.assertEqual(ComprobanteDigital.objects.filter(pago=pago).count(), 0)
    
    @patch('api.views_pagos.StripePaymentService.verificar_webhook_signature')
    def test_flujo_reembolso_con_webhook(self, mock_verificar):
        """Test flujo: reembolso → webhook → estado reembolsado."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='aprobado',
            stripe_charge_id='ch_test_123',
            usuario=self.usuario
        )
        
        # Crear comprobante
        comprobante = ComprobanteDigital.crear_comprobante(pago)
        
        # Webhook de reembolso
        event_data = {
            'type': 'charge.refunded',
            'data': {
                'object': {
                    'id': 'ch_test_123',
                    'refunded': True
                }
            }
        }
        
        mock_verificar.return_value = (True, "Firma válida", event_data)
        
        client = APIClient()
        payload = json.dumps(event_data).encode('utf-8')
        
        response = client.post(
            '/api/webhook/stripe/',
            data=payload,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='t=123,v1=signature'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar estado
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'reembolsado')


class WebhookSecurityTestCase(TestCase):
    """Tests de seguridad para webhooks."""
    
    def test_webhook_requiere_csrf_exempt(self):
        """Test que el webhook no requiere CSRF token."""
        # El endpoint debe tener @csrf_exempt para que Stripe pueda llamarlo
        client = APIClient()
        client.enforce_csrf_checks = True  # Forzar verificación CSRF
        
        payload = b'{"test": "data"}'
        
        # Esto no debería fallar por CSRF (debe fallar por firma)
        response = client.post(
            '/api/webhook/stripe/',
            data=payload,
            content_type='application/json'
        )
        
        # No debe ser 403 Forbidden (CSRF)
        self.assertNotEqual(response.status_code, 403)
    
    def test_webhook_es_publico(self):
        """Test que el webhook es accesible sin autenticación."""
        client = APIClient()
        # No autenticar
        
        payload = b'{"test": "data"}'
        
        response = client.post(
            '/api/webhook/stripe/',
            data=payload,
            content_type='application/json'
        )
        
        # No debe ser 401 Unauthorized o 403 Forbidden
        self.assertNotIn(response.status_code, [401, 403])
