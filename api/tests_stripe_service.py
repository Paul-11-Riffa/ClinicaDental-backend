"""
SP3-T009: Tests Unitarios - StripePaymentService
Tests para los 11 métodos del servicio de integración con Stripe.
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, Mock
from decimal import Decimal
from datetime import datetime, timedelta
import stripe

from api.models import (
    Empresa, Usuario, Tipodeusuario, Paciente,
    Plandetratamiento, PagoEnLinea, ComprobanteDigital
)
from api.services.stripe_payment_service import StripePaymentService


class StripePaymentServiceTestCase(TestCase):
    """Tests para StripePaymentService."""
    
    def setUp(self):
        """Configuración inicial para tests."""
        # Crear empresa (tenant)
        self.empresa = Empresa.objects.create(
            nombre_empresa="Clínica Test",
            subdomain="test",
            email_empresa="test@clinic.com",
            telefono_empresa="123456789"
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            nombre="Paciente",
            descripcion="Usuario paciente"
        )
        
        # Crear user Django
        self.django_user = User.objects.create_user(
            username='paciente_test',
            password='test123'
        )
        
        # Crear usuario
        self.usuario = Usuario.objects.create(
            user=self.django_user,
            empresa=self.empresa,
            idtipodeusuario=self.tipo_usuario,
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com"
        )
        
        # Crear paciente
        self.paciente = Paciente.objects.create(
            empresa=self.empresa,
            nombre="Juan",
            apellido="Pérez",
            email="juan@test.com",
            telefono="987654321",
            ci="12345678"
        )
        
        # Crear plan de tratamiento
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            descripcion="Plan de prueba",
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
        
        # Crear pago
        self.pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            moneda='BOB',
            metodo_pago='tarjeta',
            estado='pendiente',
            usuario=self.usuario
        )
    
    @override_settings(STRIPE_ENABLED=True)
    def test_is_enabled_true(self):
        """Test que is_enabled retorna True cuando Stripe está habilitado."""
        self.assertTrue(StripePaymentService.is_enabled())
    
    @override_settings(STRIPE_ENABLED=False)
    def test_is_enabled_false(self):
        """Test que is_enabled retorna False cuando Stripe no está habilitado."""
        self.assertFalse(StripePaymentService.is_enabled())
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.create')
    @override_settings(STRIPE_ENABLED=True)
    def test_crear_payment_intent_exitoso(self, mock_create):
        """Test crear Payment Intent exitosamente."""
        # Mock response de Stripe
        mock_payment_intent = {
            'id': 'pi_test_123',
            'client_secret': 'pi_test_123_secret_abc',
            'amount': 50000,  # 500.00 BOB en centavos
            'currency': 'bob',
            'status': 'requires_payment_method'
        }
        mock_create.return_value = mock_payment_intent
        
        # Ejecutar
        exito, mensaje, payment_intent = StripePaymentService.crear_payment_intent(
            pago=self.pago,
            descripcion="Pago de prueba"
        )
        
        # Verificar
        self.assertTrue(exito)
        self.assertIn("Payment Intent creado exitosamente", mensaje)
        self.assertEqual(payment_intent['id'], 'pi_test_123')
        
        # Verificar que el pago fue actualizado
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.stripe_payment_intent_id, 'pi_test_123')
        self.assertEqual(self.pago.estado, 'procesando')
        self.assertEqual(self.pago.numero_intentos, 1)
        
        # Verificar llamada a Stripe API
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['amount'], 50000)
        self.assertEqual(call_kwargs['currency'], 'bob')
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.create')
    @override_settings(STRIPE_ENABLED=True)
    def test_crear_payment_intent_con_metadata(self, mock_create):
        """Test que crear_payment_intent incluye metadata completa."""
        mock_create.return_value = {
            'id': 'pi_test_123',
            'client_secret': 'secret',
            'amount': 50000,
            'currency': 'bob'
        }
        
        StripePaymentService.crear_payment_intent(self.pago)
        
        # Verificar metadata
        call_kwargs = mock_create.call_args[1]
        metadata = call_kwargs['metadata']
        
        self.assertIn('pago_id', metadata)
        self.assertIn('codigo_pago', metadata)
        self.assertIn('empresa_id', metadata)
        self.assertIn('origen_tipo', metadata)
        self.assertEqual(metadata['origen_tipo'], 'plan')
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.create')
    @override_settings(STRIPE_ENABLED=True)
    def test_crear_payment_intent_card_error(self, mock_create):
        """Test manejo de CardError."""
        mock_create.side_effect = stripe.error.CardError(
            message="Card declined",
            param="card",
            code="card_declined"
        )
        
        exito, mensaje, payment_intent = StripePaymentService.crear_payment_intent(self.pago)
        
        self.assertFalse(exito)
        self.assertIn("Error con la tarjeta", mensaje)
        self.assertIsNone(payment_intent)
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.confirm')
    @override_settings(STRIPE_ENABLED=True)
    def test_confirmar_payment_intent_exitoso(self, mock_confirm):
        """Test confirmar Payment Intent exitosamente."""
        mock_confirm.return_value = {
            'id': 'pi_test_123',
            'status': 'succeeded'
        }
        
        exito, mensaje, payment_intent = StripePaymentService.confirmar_payment_intent(
            'pi_test_123',
            'pm_card_visa'
        )
        
        self.assertTrue(exito)
        self.assertIn("confirmado exitosamente", mensaje)
        mock_confirm.assert_called_once_with(
            'pi_test_123',
            payment_method='pm_card_visa'
        )
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.retrieve')
    @override_settings(STRIPE_ENABLED=True)
    def test_capturar_payment_intent_exitoso(self, mock_retrieve):
        """Test capturar Payment Intent (modo manual)."""
        mock_pi = MagicMock()
        mock_pi.capture.return_value = {
            'id': 'pi_test_123',
            'status': 'succeeded'
        }
        mock_retrieve.return_value = mock_pi
        
        exito, mensaje, payment_intent = StripePaymentService.capturar_payment_intent('pi_test_123')
        
        self.assertTrue(exito)
        self.assertIn("capturado exitosamente", mensaje)
        mock_pi.capture.assert_called_once()
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.retrieve')
    @override_settings(STRIPE_ENABLED=True)
    def test_cancelar_payment_intent_exitoso(self, mock_retrieve):
        """Test cancelar Payment Intent."""
        mock_pi = MagicMock()
        mock_pi.cancel.return_value = {
            'id': 'pi_test_123',
            'status': 'canceled'
        }
        mock_retrieve.return_value = mock_pi
        
        exito, mensaje, payment_intent = StripePaymentService.cancelar_payment_intent('pi_test_123')
        
        self.assertTrue(exito)
        self.assertIn("cancelado exitosamente", mensaje)
        mock_pi.cancel.assert_called_once()
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.retrieve')
    @override_settings(STRIPE_ENABLED=True)
    def test_obtener_payment_intent_exitoso(self, mock_retrieve):
        """Test obtener información de Payment Intent."""
        mock_retrieve.return_value = {
            'id': 'pi_test_123',
            'amount': 50000,
            'currency': 'bob',
            'status': 'succeeded'
        }
        
        exito, mensaje, payment_intent = StripePaymentService.obtener_payment_intent('pi_test_123')
        
        self.assertTrue(exito)
        self.assertIsNotNone(payment_intent)
        self.assertEqual(payment_intent['id'], 'pi_test_123')
    
    @patch('api.services.stripe_payment_service.stripe.Refund.create')
    @override_settings(STRIPE_ENABLED=True)
    def test_crear_reembolso_completo(self, mock_create):
        """Test crear reembolso completo."""
        self.pago.estado = 'aprobado'
        self.pago.stripe_charge_id = 'ch_test_123'
        self.pago.save()
        
        mock_create.return_value = {
            'id': 're_test_123',
            'amount': 50000,
            'status': 'succeeded'
        }
        
        exito, mensaje, refund = StripePaymentService.crear_reembolso(
            pago=self.pago,
            razon="Test refund"
        )
        
        self.assertTrue(exito)
        self.assertIn("Reembolso creado exitosamente", mensaje)
        mock_create.assert_called_once()
    
    @patch('api.services.stripe_payment_service.stripe.Refund.create')
    @override_settings(STRIPE_ENABLED=True)
    def test_crear_reembolso_parcial(self, mock_create):
        """Test crear reembolso parcial."""
        self.pago.estado = 'aprobado'
        self.pago.stripe_charge_id = 'ch_test_123'
        self.pago.save()
        
        mock_create.return_value = {
            'id': 're_test_123',
            'amount': 25000,  # 250.00 BOB
            'status': 'succeeded'
        }
        
        exito, mensaje, refund = StripePaymentService.crear_reembolso(
            pago=self.pago,
            monto=Decimal('250.00'),
            razon="Partial refund"
        )
        
        self.assertTrue(exito)
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs['amount'], 25000)
    
    def test_crear_reembolso_pago_no_aprobado(self):
        """Test que crear_reembolso falla si pago no está aprobado."""
        self.pago.estado = 'pendiente'
        self.pago.save()
        
        exito, mensaje, refund = StripePaymentService.crear_reembolso(self.pago)
        
        self.assertFalse(exito)
        self.assertIn("solo puede reembolsarse si está aprobado", mensaje)
    
    @patch('api.services.stripe_payment_service.ComprobanteDigital.crear_comprobante')
    def test_procesar_webhook_payment_intent_succeeded(self, mock_crear_comprobante):
        """Test procesar webhook de pago exitoso."""
        self.pago.stripe_payment_intent_id = 'pi_test_123'
        self.pago.estado = 'procesando'
        self.pago.save()
        
        mock_crear_comprobante.return_value = Mock()
        
        payment_intent_data = {
            'id': 'pi_test_123',
            'status': 'succeeded',
            'charges': {
                'data': [
                    {'id': 'ch_test_123'}
                ]
            }
        }
        
        exito, mensaje = StripePaymentService.procesar_webhook_payment_intent_succeeded(
            payment_intent_data
        )
        
        self.assertTrue(exito)
        
        # Verificar que el pago fue actualizado
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'aprobado')
        self.assertEqual(self.pago.stripe_charge_id, 'ch_test_123')
        self.assertIsNotNone(self.pago.fecha_aprobacion)
        self.assertIsNotNone(self.pago.fecha_procesamiento)
        
        # Verificar que se intentó crear comprobante
        mock_crear_comprobante.assert_called_once_with(self.pago)
    
    def test_procesar_webhook_payment_intent_succeeded_pago_no_encontrado(self):
        """Test webhook succeeded cuando no se encuentra el pago."""
        payment_intent_data = {
            'id': 'pi_inexistente',
            'status': 'succeeded'
        }
        
        exito, mensaje = StripePaymentService.procesar_webhook_payment_intent_succeeded(
            payment_intent_data
        )
        
        self.assertFalse(exito)
        self.assertIn("no encontrado", mensaje)
    
    def test_procesar_webhook_payment_intent_failed(self):
        """Test procesar webhook de pago fallido."""
        self.pago.stripe_payment_intent_id = 'pi_test_123'
        self.pago.estado = 'procesando'
        self.pago.save()
        
        payment_intent_data = {
            'id': 'pi_test_123',
            'status': 'failed',
            'last_payment_error': {
                'message': 'Card declined'
            }
        }
        
        exito, mensaje = StripePaymentService.procesar_webhook_payment_intent_failed(
            payment_intent_data
        )
        
        self.assertTrue(exito)
        
        # Verificar que el pago fue actualizado
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'rechazado')
        self.assertIn('Card declined', self.pago.motivo_rechazo)
    
    def test_procesar_webhook_charge_refunded_por_charge_id(self):
        """Test procesar webhook de reembolso usando charge_id."""
        self.pago.stripe_charge_id = 'ch_test_123'
        self.pago.estado = 'aprobado'
        self.pago.save()
        
        charge_data = {
            'id': 'ch_test_123',
            'refunded': True
        }
        
        exito, mensaje = StripePaymentService.procesar_webhook_charge_refunded(
            charge_data
        )
        
        self.assertTrue(exito)
        
        # Verificar que el pago fue actualizado
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'reembolsado')
    
    def test_procesar_webhook_charge_refunded_por_payment_intent_id(self):
        """Test procesar webhook de reembolso usando payment_intent_id."""
        self.pago.stripe_payment_intent_id = 'pi_test_123'
        self.pago.estado = 'aprobado'
        self.pago.save()
        
        charge_data = {
            'id': 'ch_test_456',
            'payment_intent': 'pi_test_123',
            'refunded': True
        }
        
        exito, mensaje = StripePaymentService.procesar_webhook_charge_refunded(
            charge_data
        )
        
        self.assertTrue(exito)
        
        self.pago.refresh_from_db()
        self.assertEqual(self.pago.estado, 'reembolsado')
    
    @patch('api.services.stripe_payment_service.stripe.Webhook.construct_event')
    @override_settings(
        STRIPE_ENABLED=True,
        STRIPE_WEBHOOK_SECRET='whsec_test_secret'
    )
    def test_verificar_webhook_signature_valida(self, mock_construct):
        """Test verificación de firma válida."""
        mock_event = {
            'id': 'evt_test_123',
            'type': 'payment_intent.succeeded',
            'data': {'object': {}}
        }
        mock_construct.return_value = mock_event
        
        payload = b'{"test": "data"}'
        sig_header = 't=123456789,v1=signature'
        
        valido, mensaje, event = StripePaymentService.verificar_webhook_signature(
            payload, sig_header
        )
        
        self.assertTrue(valido)
        self.assertEqual(event['id'], 'evt_test_123')
        mock_construct.assert_called_once_with(
            payload, sig_header, 'whsec_test_secret'
        )
    
    @patch('api.services.stripe_payment_service.stripe.Webhook.construct_event')
    @override_settings(
        STRIPE_ENABLED=True,
        STRIPE_WEBHOOK_SECRET='whsec_test_secret'
    )
    def test_verificar_webhook_signature_invalida(self, mock_construct):
        """Test verificación de firma inválida."""
        mock_construct.side_effect = stripe.error.SignatureVerificationError(
            'Invalid signature', sig_header='invalid'
        )
        
        payload = b'{"test": "data"}'
        sig_header = 'invalid_signature'
        
        valido, mensaje, event = StripePaymentService.verificar_webhook_signature(
            payload, sig_header
        )
        
        self.assertFalse(valido)
        self.assertIn("Firma inválida", mensaje)
        self.assertIsNone(event)
    
    @override_settings(STRIPE_ENABLED=False)
    def test_crear_payment_intent_stripe_deshabilitado(self):
        """Test que crear_payment_intent falla si Stripe está deshabilitado."""
        exito, mensaje, payment_intent = StripePaymentService.crear_payment_intent(self.pago)
        
        self.assertFalse(exito)
        self.assertIn("Stripe no está habilitado", mensaje)
        self.assertIsNone(payment_intent)


class StripeServiceIntegrationTestCase(TestCase):
    """Tests de integración para flujos completos de Stripe."""
    
    def setUp(self):
        """Setup similar al anterior."""
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
            nombre="Test",
            apellido="Patient",
            email="patient@test.com"
        )
        
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
    
    @patch('api.services.stripe_payment_service.stripe.PaymentIntent.create')
    @patch('api.services.stripe_payment_service.ComprobanteDigital.crear_comprobante')
    @override_settings(STRIPE_ENABLED=True)
    def test_flujo_completo_pago_exitoso(self, mock_comprobante, mock_create):
        """Test del flujo completo: crear pago → Payment Intent → webhook → comprobante."""
        # 1. Crear pago
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            moneda='BOB',
            metodo_pago='tarjeta',
            estado='pendiente',
            usuario=self.usuario
        )
        
        # 2. Crear Payment Intent
        mock_create.return_value = {
            'id': 'pi_test_123',
            'client_secret': 'secret',
            'amount': 50000,
            'currency': 'bob'
        }
        
        exito, _, _ = StripePaymentService.crear_payment_intent(pago)
        self.assertTrue(exito)
        
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'procesando')
        
        # 3. Simular webhook de pago exitoso
        mock_comprobante.return_value = Mock()
        
        payment_intent_data = {
            'id': 'pi_test_123',
            'status': 'succeeded',
            'charges': {'data': [{'id': 'ch_test_123'}]}
        }
        
        exito, _ = StripePaymentService.procesar_webhook_payment_intent_succeeded(
            payment_intent_data
        )
        self.assertTrue(exito)
        
        # 4. Verificar estado final
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'aprobado')
        self.assertEqual(pago.stripe_charge_id, 'ch_test_123')
        
        # 5. Verificar que se intentó crear comprobante
        mock_comprobante.assert_called_once_with(pago)
