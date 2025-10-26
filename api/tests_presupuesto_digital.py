# api/tests_presupuesto_digital.py
"""
Tests para la funcionalidad de presupuestos digitales.
SP3-T002: Generar presupuesto digital (web)

Cobertura de tests:
- Creación de presupuestos desde planes aprobados
- Emisión de presupuestos
- Validación de vigencia
- Desglose por ítems
- Bloqueo después de emisión
- Generación de PDF
- Multi-tenancy
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import (
    PresupuestoDigital,
    ItemPresupuestoDigital,
    Plandetratamiento,
    Itemplandetratamiento,
    Empresa,
    Usuario,
    Paciente,
    Odontologo,
    Tipodeusuario,
    Estado,
    Servicio,
)


class PresupuestoDigitalModelTests(TestCase):
    """Tests unitarios para el modelo PresupuestoDigital."""
    
    def setUp(self):
        """Configuración inicial para tests."""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test"
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            nombretipo="Paciente"
        )
        
        # Crear estados
        self.estado_activo = Estado.objects.create(
            nombreestado="Activo",
            empresa=self.empresa
        )
        
        # Crear usuarios
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan",
            apellido="Pérez",
            correoelectronico="juan@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="María",
            apellido="López",
            correoelectronico="maria@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Crear paciente y odontólogo
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            empresa=self.empresa
        )
        
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario_odontologo,
            especialidad="Ortodoncia",
            empresa=self.empresa
        )
        
        # Crear plan de tratamiento aprobado
        self.plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado_activo,
            fechaplan=timezone.now().date(),
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
            montototal=Decimal('1000.00'),
            empresa=self.empresa
        )
        
        # Crear servicio
        self.servicio = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza profesional",
            costobase=Decimal('100.00'),
            empresa=self.empresa
        )
        
        # Crear items del plan
        self.item_plan = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado_activo,
            costofinal=Decimal('100.00')
        )
    
    def test_crear_presupuesto_digital(self):
        """Test creación básica de presupuesto digital."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30),
            estado=PresupuestoDigital.ESTADO_BORRADOR
        )
        
        self.assertIsNotNone(presupuesto.codigo_presupuesto)
        self.assertEqual(presupuesto.estado, PresupuestoDigital.ESTADO_BORRADOR)
        self.assertTrue(presupuesto.puede_editarse())
    
    def test_presupuesto_vigente(self):
        """Test verificación de vigencia."""
        # Presupuesto vigente
        presupuesto_vigente = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=10),
        )
        self.assertTrue(presupuesto_vigente.esta_vigente())
        
        # Presupuesto caducado
        presupuesto_caducado = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() - timedelta(days=1),
        )
        self.assertFalse(presupuesto_caducado.esta_vigente())
    
    def test_emitir_presupuesto(self):
        """Test emisión de presupuesto."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30),
        )
        
        # Verificar estado inicial
        self.assertEqual(presupuesto.estado, PresupuestoDigital.ESTADO_BORRADOR)
        self.assertTrue(presupuesto.puede_editarse())
        
        # Emitir presupuesto
        presupuesto.emitir(self.usuario_odontologo)
        
        # Verificar cambios
        self.assertEqual(presupuesto.estado, PresupuestoDigital.ESTADO_EMITIDO)
        self.assertFalse(presupuesto.puede_editarse())
        self.assertIsNotNone(presupuesto.fecha_emitido)
        self.assertEqual(presupuesto.usuario_emite, self.usuario_odontologo)
    
    def test_no_puede_emitir_dos_veces(self):
        """Test que no se puede emitir un presupuesto ya emitido."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30),
        )
        
        presupuesto.emitir(self.usuario_odontologo)
        
        # Intentar emitir nuevamente
        with self.assertRaises(ValueError):
            presupuesto.emitir(self.usuario_odontologo)
    
    def test_calcular_totales(self):
        """Test cálculo de totales del presupuesto."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30),
            descuento=Decimal('10.00')
        )
        
        # Agregar items
        ItemPresupuestoDigital.objects.create(
            presupuesto=presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('100.00'),
            descuento_item=Decimal('0.00')
        )
        
        # Calcular totales
        result = presupuesto.calcular_totales()
        
        self.assertEqual(presupuesto.subtotal, Decimal('100.00'))
        self.assertEqual(presupuesto.total, Decimal('90.00'))  # 100 - 10
        self.assertEqual(result['items_count'], 1)
    
    def test_marcar_caducado(self):
        """Test marcado de presupuesto como caducado."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() - timedelta(days=1),
            estado=PresupuestoDigital.ESTADO_EMITIDO
        )
        
        presupuesto.marcar_caducado()
        
        self.assertEqual(presupuesto.estado, PresupuestoDigital.ESTADO_CADUCADO)
        self.assertFalse(presupuesto.esta_vigente())


class ItemPresupuestoDigitalModelTests(TestCase):
    """Tests para el modelo ItemPresupuestoDigital."""
    
    def setUp(self):
        """Configuración inicial."""
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test"
        )
        
        self.tipo_usuario = Tipodeusuario.objects.create(nombretipo="Paciente")
        self.estado = Estado.objects.create(nombreestado="Activo", empresa=self.empresa)
        
        usuario_paciente = Usuario.objects.create(
            nombre="Test",
            apellido="User",
            correoelectronico="test@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        usuario_odontologo = Usuario.objects.create(
            nombre="Dr",
            apellido="Test",
            correoelectronico="dr@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        self.paciente = Paciente.objects.create(
            codusuario=usuario_paciente,
            empresa=self.empresa
        )
        
        self.odontologo = Odontologo.objects.create(
            codusuario=usuario_odontologo,
            empresa=self.empresa
        )
        
        self.plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
            empresa=self.empresa
        )
        
        self.servicio = Servicio.objects.create(
            nombre="Test Service",
            costobase=Decimal('200.00'),
            empresa=self.empresa
        )
        
        self.item_plan = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('200.00')
        )
        
        self.presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30)
        )
    
    def test_crear_item_presupuesto(self):
        """Test creación de item de presupuesto."""
        item = ItemPresupuestoDigital.objects.create(
            presupuesto=self.presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('200.00'),
            descuento_item=Decimal('20.00')
        )
        
        self.assertEqual(item.precio_final, Decimal('180.00'))
    
    def test_calculo_precio_final_automatico(self):
        """Test que precio_final se calcula automáticamente al guardar."""
        item = ItemPresupuestoDigital(
            presupuesto=self.presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('300.00'),
            descuento_item=Decimal('50.00')
        )
        
        item.save()
        
        self.assertEqual(item.precio_final, Decimal('250.00'))
    
    def test_pago_parcial(self):
        """Test configuración de pagos parciales."""
        item = ItemPresupuestoDigital.objects.create(
            presupuesto=self.presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('600.00'),
            permite_pago_parcial=True,
            cantidad_cuotas=3
        )
        
        self.assertTrue(item.permite_pago_parcial)
        self.assertEqual(item.cantidad_cuotas, 3)


class PresupuestoDigitalAPITests(APITestCase):
    """Tests de integración para el API de presupuestos digitales."""
    
    def setUp(self):
        """Configuración inicial para tests de API."""
        self.client = APIClient()
        
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="SmileStudio",
            subdomain="smilestudio"
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            nombretipo="Odontólogo"
        )
        
        # Crear estado
        self.estado = Estado.objects.create(
            nombreestado="Pendiente",
            empresa=self.empresa
        )
        
        # Crear usuario odontólogo
        self.usuario = Usuario.objects.create(
            nombre="Carlos",
            apellido="Dentista",
            correoelectronico="carlos@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Crear usuario paciente
        self.usuario_paciente = Usuario.objects.create(
            nombre="Ana",
            apellido="Paciente",
            correoelectronico="ana@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            empresa=self.empresa
        )
        
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario,
            empresa=self.empresa
        )
        
        # Crear plan aprobado
        self.plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
            montototal=Decimal('500.00'),
            empresa=self.empresa
        )
        
        # Crear servicio
        self.servicio = Servicio.objects.create(
            nombre="Ortodoncia",
            costobase=Decimal('500.00'),
            empresa=self.empresa
        )
        
        # Crear item
        self.item_plan = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('500.00')
        )
        
        # Simular tenant middleware
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'smilestudio'
    
    def test_listar_presupuestos(self):
        """Test listar presupuestos digitales."""
        # Crear presupuesto
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30)
        )
        
        response = self.client.get('/api/presupuestos-digitales/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_crear_presupuesto_desde_plan(self):
        """Test crear presupuesto digital desde plan aprobado."""
        data = {
            'plan_tratamiento_id': self.plan.id,
            'items_ids': [self.item_plan.id],
            'es_tramo': False,
            'descuento': '0.00'
        }
        
        response = self.client.post('/api/presupuestos-digitales/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        # Verificar presupuesto creado
        presupuesto = PresupuestoDigital.objects.get(id=response.data['id'])
        self.assertEqual(presupuesto.plan_tratamiento, self.plan)
        self.assertEqual(presupuesto.items_presupuesto.count(), 1)
    
    def test_no_crear_presupuesto_plan_no_aprobado(self):
        """Test que no se puede crear presupuesto desde plan no aprobado."""
        # Crear plan en borrador
        plan_borrador = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
            empresa=self.empresa
        )
        
        data = {
            'plan_tratamiento_id': plan_borrador.id,
            'items_ids': [],
        }
        
        response = self.client.post('/api/presupuestos-digitales/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_emitir_presupuesto(self):
        """Test emitir presupuesto digital."""
        # Crear presupuesto
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30)
        )
        
        ItemPresupuestoDigital.objects.create(
            presupuesto=presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('500.00')
        )
        
        data = {'confirmar': True}
        response = self.client.post(
            f'/api/presupuestos-digitales/{presupuesto.id}/emitir/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estado
        presupuesto.refresh_from_db()
        self.assertEqual(presupuesto.estado, PresupuestoDigital.ESTADO_EMITIDO)
        self.assertFalse(presupuesto.puede_editarse())
    
    def test_verificar_vigencia(self):
        """Test verificar vigencia del presupuesto."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=15)
        )
        
        response = self.client.get(
            f'/api/presupuestos-digitales/{presupuesto.id}/vigencia/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['esta_vigente'])
        self.assertGreater(response.data['dias_restantes'], 0)
    
    def test_generar_pdf(self):
        """Test generar PDF del presupuesto."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30)
        )
        
        response = self.client.post(
            f'/api/presupuestos-digitales/{presupuesto.id}/generar-pdf/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('pdf_url', response.data)
        
        # Verificar que se marcó como generado
        presupuesto.refresh_from_db()
        self.assertTrue(presupuesto.pdf_generado)
    
    def test_desglose_detallado(self):
        """Test obtener desglose detallado del presupuesto."""
        presupuesto = PresupuestoDigital.objects.create(
            plan_tratamiento=self.plan,
            empresa=self.empresa,
            fecha_vigencia=timezone.now().date() + timedelta(days=30),
            descuento=Decimal('50.00')
        )
        
        ItemPresupuestoDigital.objects.create(
            presupuesto=presupuesto,
            item_plan=self.item_plan,
            precio_unitario=Decimal('500.00'),
            descuento_item=Decimal('0.00')
        )
        
        presupuesto.calcular_totales()
        
        response = self.client.get(
            f'/api/presupuestos-digitales/{presupuesto.id}/desglose/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['subtotal'], 500.00)
        self.assertEqual(response.data['descuento_global'], 50.00)
        self.assertEqual(response.data['total'], 450.00)
        self.assertEqual(len(response.data['items']), 1)
