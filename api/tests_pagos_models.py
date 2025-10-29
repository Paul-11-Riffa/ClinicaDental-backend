"""
SP3-T009: Tests de Modelos - Sistema de Pagos
Tests para PagoEnLinea, DetallePagoItem, ComprobanteDigital.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta

from api.models import (
    Empresa, Usuario, Tipodeusuario, Paciente,
    Plandetratamiento, Itemplandetratamiento, Consulta,
    PagoEnLinea, DetallePagoItem, ComprobanteDigital,
    Servicio, Estadodeconsulta
)


class PagoEnLineaModelTestCase(TestCase):
    """Tests para el modelo PagoEnLinea."""
    
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
            email="juan@test.com",
            ci="12345678"
        )
        
        self.plan = Plandetratamiento.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
    
    def test_crear_pago_plan_exitoso(self):
        """Test crear pago para plan de tratamiento."""
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
        
        self.assertIsNotNone(pago.id)
        self.assertEqual(pago.monto, Decimal('500.00'))
        self.assertEqual(pago.estado, 'pendiente')
        self.assertIsNotNone(pago.codigo_pago)
        self.assertTrue(pago.codigo_pago.startswith('PAG-'))
    
    def test_generar_codigo_pago_unico(self):
        """Test que codigo_pago es único."""
        pago1 = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            usuario=self.usuario
        )
        
        pago2 = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            usuario=self.usuario
        )
        
        self.assertNotEqual(pago1.codigo_pago, pago2.codigo_pago)
    
    def test_puede_anularse_estado_pendiente(self):
        """Test que pago pendiente puede anularse."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        self.assertTrue(pago.puede_anularse())
    
    def test_puede_anularse_estado_procesando(self):
        """Test que pago en procesamiento puede anularse."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='procesando',
            usuario=self.usuario
        )
        
        self.assertTrue(pago.puede_anularse())
    
    def test_no_puede_anularse_estado_aprobado(self):
        """Test que pago aprobado NO puede anularse."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        self.assertFalse(pago.puede_anularse())
    
    def test_puede_reembolsarse_estado_aprobado(self):
        """Test que pago aprobado puede reembolsarse."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        self.assertTrue(pago.puede_reembolsarse())
    
    def test_no_puede_reembolsarse_estado_pendiente(self):
        """Test que pago pendiente NO puede reembolsarse."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        self.assertFalse(pago.puede_reembolsarse())
    
    def test_str_representation(self):
        """Test representación string del pago."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            usuario=self.usuario
        )
        
        str_repr = str(pago)
        self.assertIn('PAG-', str_repr)
        self.assertIn('500', str_repr)
    
    def test_incrementar_numero_intentos(self):
        """Test que numero_intentos se incrementa correctamente."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            usuario=self.usuario
        )
        
        # Simular incremento
        pago.numero_intentos += 1
        pago.save()
        
        pago.refresh_from_db()
        self.assertEqual(pago.numero_intentos, 1)


class DetallePagoItemTestCase(TestCase):
    """Tests para el modelo DetallePagoItem."""
    
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
            costo_total=Decimal('1000.00'),
            estado='activo'
        )
        
        self.servicio = Servicio.objects.create(
            empresa=self.empresa,
            nombre="Limpieza",
            precio=Decimal('200.00')
        )
        
        self.item = Itemplandetratamiento.objects.create(
            plan=self.plan,
            servicio=self.servicio,
            cantidad=1,
            precio_unitario=Decimal('200.00'),
            subtotal=Decimal('200.00'),
            estado='pendiente'
        )
        
        self.pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('200.00'),
            estado='pendiente',
            usuario=self.usuario
        )
    
    def test_crear_detalle_pago_item(self):
        """Test crear detalle de pago para un item."""
        detalle = DetallePagoItem.objects.create(
            pago=self.pago,
            item_plan=self.item,
            monto_aplicado=Decimal('200.00'),
            porcentaje_cubierto=Decimal('100.00')
        )
        
        self.assertIsNotNone(detalle.id)
        self.assertEqual(detalle.monto_aplicado, Decimal('200.00'))
        self.assertEqual(detalle.porcentaje_cubierto, Decimal('100.00'))
    
    def test_suma_detalles_igual_monto_pago(self):
        """Test que suma de detalles debe igualar monto del pago."""
        # Crear dos items
        item2 = Itemplandetratamiento.objects.create(
            plan=self.plan,
            servicio=self.servicio,
            cantidad=1,
            precio_unitario=Decimal('300.00'),
            subtotal=Decimal('300.00'),
            estado='pendiente'
        )
        
        # Pago total
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        # Detalles
        DetallePagoItem.objects.create(
            pago=pago,
            item_plan=self.item,
            monto_aplicado=Decimal('200.00'),
            porcentaje_cubierto=Decimal('100.00')
        )
        
        DetallePagoItem.objects.create(
            pago=pago,
            item_plan=item2,
            monto_aplicado=Decimal('300.00'),
            porcentaje_cubierto=Decimal('100.00')
        )
        
        # Verificar suma
        suma_detalles = sum(
            d.monto_aplicado 
            for d in DetallePagoItem.objects.filter(pago=pago)
        )
        
        self.assertEqual(suma_detalles, pago.monto)
    
    def test_str_representation(self):
        """Test representación string del detalle."""
        detalle = DetallePagoItem.objects.create(
            pago=self.pago,
            item_plan=self.item,
            monto_aplicado=Decimal('200.00')
        )
        
        str_repr = str(detalle)
        self.assertIn('200', str_repr)


class ComprobanteDigitalModelTestCase(TestCase):
    """Tests para el modelo ComprobanteDigital."""
    
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
        
        self.pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('500.00'),
            estado='aprobado',
            usuario=self.usuario
        )
    
    def test_crear_comprobante_pago_aprobado(self):
        """Test crear comprobante para pago aprobado."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        self.assertIsNotNone(comprobante)
        self.assertIsNotNone(comprobante.codigo_comprobante)
        self.assertIsNotNone(comprobante.codigo_verificacion)
        self.assertEqual(comprobante.pago, self.pago)
        self.assertEqual(comprobante.estado, ComprobanteDigital.ESTADO_ACTIVO)
    
    def test_no_crear_comprobante_pago_pendiente(self):
        """Test que no se crea comprobante para pago pendiente."""
        pago_pendiente = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        with self.assertRaises(ValueError) as context:
            ComprobanteDigital.crear_comprobante(pago_pendiente)
        
        self.assertIn("aprobado", str(context.exception))
    
    def test_no_crear_comprobante_duplicado(self):
        """Test que no se crean comprobantes duplicados."""
        # Crear primer comprobante
        ComprobanteDigital.crear_comprobante(self.pago)
        
        # Intentar crear segundo comprobante
        with self.assertRaises(ValueError) as context:
            ComprobanteDigital.crear_comprobante(self.pago)
        
        self.assertIn("ya tiene un comprobante", str(context.exception))
    
    def test_generar_codigo_comprobante_unico(self):
        """Test que codigo_comprobante es único."""
        pago2 = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        comp1 = ComprobanteDigital.crear_comprobante(self.pago)
        comp2 = ComprobanteDigital.crear_comprobante(pago2)
        
        self.assertNotEqual(comp1.codigo_comprobante, comp2.codigo_comprobante)
    
    def test_generar_codigo_verificacion_unico(self):
        """Test que codigo_verificacion es único."""
        pago2 = PagoEnLinea.objects.create(
            empresa=self.empresa,
            plan_tratamiento=self.plan,
            origen_tipo='plan',
            monto=Decimal('300.00'),
            estado='aprobado',
            usuario=self.usuario
        )
        
        comp1 = ComprobanteDigital.crear_comprobante(self.pago)
        comp2 = ComprobanteDigital.crear_comprobante(pago2)
        
        self.assertNotEqual(comp1.codigo_verificacion, comp2.codigo_verificacion)
    
    def test_esta_activo_estado_activo(self):
        """Test que esta_activo retorna True para comprobante activo."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        self.assertTrue(comprobante.esta_activo())
    
    def test_esta_activo_estado_anulado(self):
        """Test que esta_activo retorna False para comprobante anulado."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        comprobante.anular()
        
        self.assertFalse(comprobante.esta_activo())
    
    def test_puede_anularse(self):
        """Test que comprobante puede anularse."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        self.assertTrue(comprobante.puede_anularse())
    
    def test_anular_comprobante(self):
        """Test anular comprobante."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        comprobante.anular()
        
        comprobante.refresh_from_db()
        self.assertEqual(comprobante.estado, ComprobanteDigital.ESTADO_ANULADO)
        self.assertIsNotNone(comprobante.fecha_anulacion)
    
    def test_no_puede_anular_ya_anulado(self):
        """Test que no se puede anular comprobante ya anulado."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        comprobante.anular()
        
        self.assertFalse(comprobante.puede_anularse())
    
    def test_datos_comprobante_contiene_info_pago(self):
        """Test que datos_comprobante contiene información del pago."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        datos = comprobante.datos_comprobante
        
        self.assertIn('pago_id', datos)
        self.assertIn('codigo_pago', datos)
        self.assertIn('monto', datos)
        self.assertIn('moneda', datos)
        self.assertEqual(datos['pago_id'], self.pago.id)
    
    def test_datos_comprobante_contiene_info_paciente(self):
        """Test que datos_comprobante contiene información del paciente."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        datos = comprobante.datos_comprobante
        
        self.assertIn('paciente', datos)
        self.assertIn('nombre_completo', datos['paciente'])
        self.assertIn('email', datos['paciente'])
    
    def test_str_representation(self):
        """Test representación string del comprobante."""
        comprobante = ComprobanteDigital.crear_comprobante(self.pago)
        
        str_repr = str(comprobante)
        self.assertIn('COMP-', str_repr)


class PagoConsultaTestCase(TestCase):
    """Tests específicos para pagos de consultas."""
    
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
        
        self.estado_consulta = Estadodeconsulta.objects.create(
            empresa=self.empresa,
            nombre="Confirmada"
        )
        
        self.consulta = Consulta.objects.create(
            empresa=self.empresa,
            paciente=self.paciente,
            idestadoconsulta=self.estado_consulta,
            costo_consulta=Decimal('150.00')
        )
    
    def test_crear_pago_consulta(self):
        """Test crear pago para consulta."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            consulta=self.consulta,
            origen_tipo='consulta',
            monto=Decimal('150.00'),
            tipo_pago_consulta='prepago',
            estado='pendiente',
            usuario=self.usuario
        )
        
        self.assertIsNotNone(pago.id)
        self.assertEqual(pago.origen_tipo, 'consulta')
        self.assertEqual(pago.tipo_pago_consulta, 'prepago')
    
    def test_pago_consulta_sin_plan(self):
        """Test que pago de consulta no requiere plan."""
        pago = PagoEnLinea.objects.create(
            empresa=self.empresa,
            consulta=self.consulta,
            origen_tipo='consulta',
            monto=Decimal('150.00'),
            estado='pendiente',
            usuario=self.usuario
        )
        
        self.assertIsNone(pago.plan_tratamiento)
        self.assertIsNotNone(pago.consulta)
