"""
SP3-T009: Tests de ViewSet - Sistema de Pagos
Tests para PagoEnLineaViewSet y endpoints de pagos.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from unittest.mock import patch, Mock
from decimal import Decimal

from api.models import (
    Empresa, Usuario, Tipodeusuario, Paciente,
    Plandetratamiento, Itemplandetratamiento, Servicio,
    PagoEnLinea, ComprobanteDigital, Consulta, Estadodeconsulta
)


class PagoEnLineaViewSetTestCase(APITestCase):
    """Tests para PagoEnLineaViewSet."""
    
    def setUp(self):
        """Configuración inicial."""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre_empresa="Clínica Test",
            subdomain="test",
            email_empresa="test@clinic.com"
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            nombre="Recepcionista",
            descripcion="Usuario recepcionista"
        )
        
        # Crear user Django y usuario
        self.django_user = User.objects.create_user(
            username='test_user',
            password='test123',
            email='test@test.com'
        )
        
        self.usuario = Usuario.objects.create(
            user=self.django_user,
            empresa=self.empresa,
            idtipodeusuario=self.tipo_usuario,
            nombre="Test",
            apellido="User",
            email="test@test.com"
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
        
        # Crear servicio
        self.servicio = Servicio.objects.create(
            empresa=self.empresa,
            nombre="Limpieza dental",
            precio=Decimal('200.00')
        )
        
        # Crear plan de tratamiento
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            descripcion="Plan de prueba",
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
        
        # Crear item de plan
        self.item = Itemplandetratamiento.objects.create(
            plan=self.plan,
            servicio=self.servicio,
            cantidad=1,
            precio_unitario=Decimal('200.00'),
            subtotal=Decimal('200.00'),
            estado='pendiente'
        )
        
        # Configurar cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.django_user)
        
        # Simular middleware tenant
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'test'
    
    def test_listar_pagos(self):
        """Test listar pagos de la empresa."""
        # Crear pagos
        PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        # Hacer request
        response = self.client.get('/api/pagos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_obtener_detalle_pago(self):
        """Test obtener detalle de un pago."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        response = self.client.get(f'/api/pagos/{pago.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(response.data['monto']), Decimal('500.00'))
        self.assertEqual(response.data['estado'], 'aprobado')
    
    @patch('api.services.stripe_payment_service.StripePaymentService.crear_payment_intent')
    @patch('api.services.stripe_payment_service.StripePaymentService.is_enabled')
    def test_crear_pago_plan_con_tarjeta(self, mock_is_enabled, mock_crear_pi):
        """Test crear pago para plan con método tarjeta."""
        mock_is_enabled.return_value = True
        mock_crear_pi.return_value = (
            True,
            "Payment Intent creado",
            {
                'id': 'pi_test_123',
                'client_secret': 'pi_test_123_secret_abc',
                'amount': 50000,
                'currency': 'bob'
            }
        )
        
        data = {
            'plan_tratamiento_id': self.plan.id,
            'monto': '500.00',
            'metodo_pago': 'tarjeta',
            'descripcion': 'Pago inicial'
        }
        
        response = self.client.post('/api/pagos/crear-pago-plan/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('pago', response.data)
        self.assertIn('stripe', response.data)
        self.assertEqual(response.data['stripe']['payment_intent_id'], 'pi_test_123')
        
        # Verificar que se llamó a crear_payment_intent
        mock_crear_pi.assert_called_once()
    
    def test_crear_pago_plan_con_transferencia(self):
        """Test crear pago para plan con método transferencia."""
        data = {
            'plan_tratamiento_id': self.plan.id,
            'monto': '500.00',
            'metodo_pago': 'transferencia',
            'descripcion': 'Pago por transferencia'
        }
        
        response = self.client.post('/api/pagos/crear-pago-plan/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('pago', response.data)
        self.assertNotIn('stripe', response.data)  # No Stripe para transferencia
    
    def test_crear_pago_plan_con_items_seleccionados(self):
        """Test crear pago para items específicos del plan."""
        data = {
            'plan_tratamiento_id': self.plan.id,
            'monto': '200.00',
            'metodo_pago': 'efectivo',
            'items_seleccionados': [self.item.id]
        }
        
        response = self.client.post('/api/pagos/crear-pago-plan/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que se creó detalle para el item
        pago_id = response.data['pago']['id']
        pago = PagoEnLinea.objects.get(id=pago_id)
        self.assertEqual(pago.detalles_pago.count(), 1)
    
    def test_crear_pago_plan_monto_excede_saldo(self):
        """Test que no se puede crear pago que exceda el saldo pendiente."""
        data = {
            'plan_tratamiento_id': self.plan.id,
            'monto': '2000.00',  # Excede costo_total del plan (1000)
            'metodo_pago': 'efectivo'
        }
        
        response = self.client.post('/api/pagos/crear-pago-plan/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_crear_pago_consulta(self):
        """Test crear pago para consulta."""
        # Crear consulta
        estado = Estadodeconsulta.objects.create(
            empresa=self.empresa,
            nombre="Confirmada"
        )
        
        consulta = Consulta.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            idestadoconsulta=estado,
            costo_consulta=Decimal('150.00')
        )
        
        data = {
            'consulta_id': consulta.id,
            'monto': '150.00',
            'metodo_pago': 'tarjeta',
            'tipo_pago_consulta': 'prepago'
        }
        
        response = self.client.post('/api/pagos/crear-pago-consulta/', data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['pago']['origen_tipo'], 'consulta')
    
    @patch('api.services.stripe_payment_service.StripePaymentService.obtener_payment_intent')
    def test_confirmar_pago_tarjeta(self, mock_obtener_pi):
        """Test confirmar pago con tarjeta verificando con Stripe."""
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
        
        # Mock Stripe
        mock_obtener_pi.return_value = (
            True,
            "OK",
            {'status': 'succeeded', 'id': 'pi_test_123'}
        )
        
        response = self.client.post(f'/api/pagos/{pago.id}/confirmar-pago/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estado actualizado
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'aprobado')
    
    def test_confirmar_pago_transferencia(self):
        """Test confirmar pago con transferencia (sin Stripe)."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='transferencia',
            estado='pendiente',
            usuario=self.usuario
        )
        
        response = self.client.post(f'/api/pagos/{pago.id}/confirmar-pago/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'aprobado')
    
    def test_no_confirmar_pago_ya_aprobado(self):
        """Test que no se puede confirmar pago ya aprobado."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        response = self.client.post(f'/api/pagos/{pago.id}/confirmar-pago/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('api.services.stripe_payment_service.StripePaymentService.cancelar_payment_intent')
    def test_cancelar_pago_pendiente(self, mock_cancelar_pi):
        """Test cancelar pago pendiente."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            metodo_pago='tarjeta',
            estado='pendiente',
            stripe_payment_intent_id='pi_test_123',
            usuario=self.usuario
        )
        
        mock_cancelar_pi.return_value = (True, "Cancelado", {'status': 'canceled'})
        
        response = self.client.post(f'/api/pagos/{pago.id}/cancelar-pago/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'cancelado')
    
    def test_no_cancelar_pago_aprobado(self):
        """Test que no se puede cancelar pago aprobado."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        response = self.client.post(f'/api/pagos/{pago.id}/cancelar-pago/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    @patch('api.services.stripe_payment_service.StripePaymentService.crear_reembolso')
    def test_reembolsar_pago_completo(self, mock_crear_reembolso):
        """Test crear reembolso completo."""
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
        
        mock_crear_reembolso.return_value = (
            True,
            "Reembolso creado",
            {'id': 're_test_123', 'status': 'succeeded'}
        )
        
        data = {'razon': 'Cliente solicitó reembolso'}
        
        response = self.client.post(f'/api/pagos/{pago.id}/reembolsar/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        pago.refresh_from_db()
        self.assertEqual(pago.estado, 'reembolsado')
    
    @patch('api.services.stripe_payment_service.StripePaymentService.crear_reembolso')
    def test_reembolsar_pago_parcial(self, mock_crear_reembolso):
        """Test crear reembolso parcial."""
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
        
        mock_crear_reembolso.return_value = (
            True,
            "Reembolso creado",
            {'id': 're_test_123', 'amount': 25000}
        )
        
        data = {
            'monto': '250.00',
            'razon': 'Reembolso parcial'
        }
        
        response = self.client.post(f'/api/pagos/{pago.id}/reembolsar/', data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_reembolsar_monto_mayor_al_pago(self):
        """Test que no se puede reembolsar más del monto pagado."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        data = {
            'monto': '600.00',
            'razon': 'Test'
        }
        
        response = self.client.post(f'/api/pagos/{pago.id}/reembolsar/', data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_obtener_resumen_plan(self):
        """Test obtener resumen financiero de plan."""
        response = self.client.get(f'/api/pagos/resumen-plan/{self.plan.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('resumen_general', response.data)
        self.assertIn('items', response.data)
        self.assertIn('historial_pagos', response.data)
        
        # Verificar estructura del resumen
        resumen = response.data['resumen_general']
        self.assertIn('costo_total', resumen)
        self.assertIn('total_pagado', resumen)
        self.assertIn('saldo_pendiente', resumen)
    
    def test_obtener_resumen_plan_inexistente(self):
        """Test obtener resumen de plan que no existe."""
        response = self.client.get('/api/pagos/resumen-plan/99999/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_filtrar_pagos_por_estado(self):
        """Test filtrar pagos por estado."""
        PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        # Filtrar solo aprobados
        response = self.client.get('/api/pagos/?estado=aprobado')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Todos los resultados deben ser aprobados
        for pago in response.data['results']:
            self.assertEqual(pago['estado'], 'aprobado')
    
    def test_pagos_aislados_por_empresa(self):
        """Test que solo se ven pagos de la empresa (tenant isolation)."""
        # Crear otra empresa
        otra_empresa = Empresa.objects.create(
            nombre_empresa="Otra Clínica",
            subdomain="otra"
        )
        
        # Crear pago en otra empresa
        PagoEnLinea.objects.create(
            empresa=otra_empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        # Crear pago en empresa actual
        PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        # Listar pagos
        response = self.client.get('/api/pagos/')
        
        # Solo debe ver el pago de su empresa
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['empresa']['subdomain'],
            'test'
        )


class VerificarComprobanteTestCase(APITestCase):
    """Tests para endpoint público de verificación de comprobantes."""
    
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
            apellido="Pérez"
        )
        
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            costo_total=Decimal('1000.00')
        )
        
        self.pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        self.comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        self.client = APIClient()
        # No autenticar - endpoint público
    
    def test_verificar_comprobante_valido(self):
        """Test verificar comprobante válido."""
        url = f'/api/verificar-comprobante-pago/{self.comprobante.codigo_verificacion}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valido'])
        self.assertIn('comprobante', response.data)
        self.assertIn('pago', response.data)
    
    def test_verificar_comprobante_inexistente(self):
        """Test verificar comprobante que no existe."""
        url = '/api/verificar-comprobante-pago/CODIGO_FALSO/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['valido'])
    
    def test_verificar_comprobante_anulado(self):
        """Test verificar comprobante anulado."""
        self.comprobante.anular()
        
        url = f'/api/verificar-comprobante-pago/{self.comprobante.codigo_verificacion}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['valido'])
        self.assertEqual(
            response.data['comprobante']['estado'],
            ComprobanteDigital.ESTADO_ANULADO
        )
