# api/tests_presupuestos.py
"""
Tests para la funcionalidad de aceptación de presupuestos.
SP3-T003: Implementar Aceptar presupuesto por parte del paciente (web)
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from datetime import date, timedelta
from decimal import Decimal
import uuid

from .models import (
    Empresa,
    Usuario,
    Paciente,
    Odontologo,
    Plandetratamiento,
    Itemplandetratamiento,
    AceptacionPresupuesto,
    Estado,
    Servicio,
    Bitacora,
    Tipodeusuario,
)


class PresupuestoAcceptanceTests(APITestCase):
    """Tests para la aceptación de presupuestos por pacientes."""
    
    def setUp(self):
        """Setup inicial para todos los tests."""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
        
        # Crear tipos de usuario
        self.tipo_paciente = Tipodeusuario.objects.create(rol="Paciente")
        self.tipo_odontologo = Tipodeusuario.objects.create(rol="Odontologo")
        
        # Crear estados
        self.estado_pendiente = Estado.objects.create(
            nombreestado="Pendiente",
            empresa=self.empresa
        )
        self.estado_completado = Estado.objects.create(
            nombreestado="Completado",
            empresa=self.empresa
        )
        
        # Crear servicios
        self.servicio1 = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza completa",
            costobase=Decimal("150.00"),
            duracion=30,
            activo=True,
            empresa=self.empresa
        )
        self.servicio2 = Servicio.objects.create(
            nombre="Endodoncia",
            descripcion="Tratamiento de conducto",
            costobase=Decimal("800.00"),
            duracion=90,
            activo=True,
            empresa=self.empresa
        )
        
        # Crear usuario paciente
        self.usuario_paciente = Usuario.objects.create_user(
            email="paciente@test.com",
            password="test123",
            nombre="Juan",
            apellido="Pérez",
            empresa=self.empresa,
            idtipousuario=self.tipo_paciente
        )
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            empresa=self.empresa
        )
        
        # Crear usuario odontólogo
        self.usuario_odontologo = Usuario.objects.create_user(
            email="odontologo@test.com",
            password="test123",
            nombre="Dr. María",
            apellido="González",
            empresa=self.empresa,
            idtipousuario=self.tipo_odontologo
        )
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario_odontologo,
            empresa=self.empresa
        )
        
        # Crear otro paciente (para tests de autorización)
        self.usuario_otro_paciente = Usuario.objects.create_user(
            email="otro.paciente@test.com",
            password="test123",
            nombre="Pedro",
            apellido="López",
            empresa=self.empresa,
            idtipousuario=self.tipo_paciente
        )
        self.otro_paciente = Paciente.objects.create(
            codusuario=self.usuario_otro_paciente,
            empresa=self.empresa
        )
        
        # Crear token para paciente
        self.token_paciente = Token.objects.create(user=self.usuario_paciente)
        
        # Cliente API
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token_paciente.key}')
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN='test')
    
    def crear_presupuesto(self, fecha_vigencia=None, estado_aceptacion='Pendiente'):
        """Helper para crear un presupuesto con items."""
        if fecha_vigencia is None:
            fecha_vigencia = date.today() + timedelta(days=30)
        
        presupuesto = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado_pendiente,
            fechaplan=date.today(),
            montototal=Decimal("950.00"),
            descuento=Decimal("0.00"),
            empresa=self.empresa,
            fecha_vigencia=fecha_vigencia,
            estado_aceptacion=estado_aceptacion,
            es_editable=True
        )
        
        # Crear items
        item1 = Itemplandetratamiento.objects.create(
            idplantratamiento=presupuesto,
            idservicio=self.servicio1,
            idestado=self.estado_pendiente,
            costofinal=Decimal("150.00"),
            empresa=self.empresa
        )
        item2 = Itemplandetratamiento.objects.create(
            idplantratamiento=presupuesto,
            idservicio=self.servicio2,
            idestado=self.estado_pendiente,
            costofinal=Decimal("800.00"),
            empresa=self.empresa
        )
        
        return presupuesto, [item1, item2]
    
    # ========== TESTS DE CONSULTA ==========
    
    def test_listar_presupuestos_paciente(self):
        """Test: El paciente puede listar sus presupuestos."""
        presupuesto, _ = self.crear_presupuesto()
        
        response = self.client.get('/api/presupuestos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], presupuesto.id)
    
    def test_paciente_no_ve_presupuestos_de_otros(self):
        """Test: El paciente solo ve sus propios presupuestos."""
        # Presupuesto del paciente actual
        presupuesto_propio, _ = self.crear_presupuesto()
        
        # Presupuesto de otro paciente
        presupuesto_otro = Plandetratamiento.objects.create(
            codpaciente=self.otro_paciente,
            cododontologo=self.odontologo,
            idestado=self.estado_pendiente,
            fechaplan=date.today(),
            montototal=Decimal("500.00"),
            empresa=self.empresa
        )
        
        response = self.client.get('/api/presupuestos/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], presupuesto_propio.id)
    
    def test_detalle_presupuesto(self):
        """Test: Ver detalle de un presupuesto con todos sus campos."""
        presupuesto, items = self.crear_presupuesto()
        
        response = self.client.get(f'/api/presupuestos/{presupuesto.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data['id'], presupuesto.id)
        self.assertEqual(len(data['items']), 2)
        self.assertTrue(data['puede_aceptar'])
        self.assertTrue(data['esta_vigente'])
        self.assertIn('dias_para_vencimiento', data)
    
    # ========== TESTS DE ACEPTACIÓN EXITOSA ==========
    
    def test_aceptacion_total_exitosa(self):
        """Test: Aceptar presupuesto de forma total exitosamente."""
        presupuesto, items = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
                'signature_hash': 'abc123'
            },
            'notas': 'Todo se ve bien'
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('comprobante_id', response.data['aceptacion'])
        
        # Verificar cambios en DB
        presupuesto.refresh_from_db()
        self.assertEqual(presupuesto.estado_aceptacion, 'Aceptado')
        self.assertFalse(presupuesto.es_editable)
        self.assertIsNotNone(presupuesto.fecha_aceptacion)
        self.assertEqual(presupuesto.usuario_acepta, self.usuario_paciente)
        
        # Verificar registro de aceptación
        self.assertTrue(
            AceptacionPresupuesto.objects.filter(
                plandetratamiento=presupuesto,
                tipo_aceptacion='Total'
            ).exists()
        )
        
        # Verificar bitácora
        self.assertTrue(
            Bitacora.objects.filter(
                accion='ACEPTACION_PRESUPUESTO',
                usuario=self.usuario_paciente
            ).exists()
        )
    
    def test_aceptacion_parcial_exitosa(self):
        """Test: Aceptar solo algunos items del presupuesto."""
        presupuesto, items = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Parcial',
            'items_aceptados': [items[0].id],  # Solo el primer item
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
                'signature_hash': 'xyz789'
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        presupuesto.refresh_from_db()
        self.assertEqual(presupuesto.estado_aceptacion, 'Parcial')
        
        # Verificar que se guardaron los items aceptados
        aceptacion = AceptacionPresupuesto.objects.get(plandetratamiento=presupuesto)
        self.assertEqual(aceptacion.tipo_aceptacion, 'Parcial')
        self.assertEqual(aceptacion.items_aceptados, [items[0].id])
    
    # ========== TESTS DE VALIDACIONES ==========
    
    def test_rechazo_presupuesto_caducado(self):
        """Test: No se puede aceptar un presupuesto caducado."""
        fecha_caducada = date.today() - timedelta(days=1)
        presupuesto, _ = self.crear_presupuesto(fecha_vigencia=fecha_caducada)
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('caducado', response.data['error'].lower())
    
    def test_rechazo_presupuesto_ya_aceptado(self):
        """Test: No se puede aceptar un presupuesto ya aceptado."""
        presupuesto, _ = self.crear_presupuesto(estado_aceptacion='Aceptado')
        presupuesto.fecha_aceptacion = timezone.now()
        presupuesto.save()
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('ya aceptado', response.data['error'].lower())
    
    def test_rechazo_usuario_no_autorizado(self):
        """Test: Un paciente no puede aceptar el presupuesto de otro."""
        # Crear presupuesto para otro paciente
        presupuesto_otro = Plandetratamiento.objects.create(
            codpaciente=self.otro_paciente,
            cododontologo=self.odontologo,
            idestado=self.estado_pendiente,
            fechaplan=date.today(),
            montototal=Decimal("500.00"),
            empresa=self.empresa,
            fecha_vigencia=date.today() + timedelta(days=30),
            estado_aceptacion='Pendiente'
        )
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto_otro.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('autorizado', response.data['error'].lower())
    
    def test_validacion_items_invalidos(self):
        """Test: Rechazar aceptación parcial con items que no existen."""
        presupuesto, items = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Parcial',
            'items_aceptados': [9999, 8888],  # IDs inexistentes
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('inválidos', response.data['error'].lower())
    
    def test_validacion_aceptacion_parcial_sin_items(self):
        """Test: Aceptación parcial requiere especificar items."""
        presupuesto, _ = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Parcial',
            'items_aceptados': [],  # Vacío
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_validacion_firma_digital_incompleta(self):
        """Test: La firma digital debe tener campos requeridos."""
        presupuesto, _ = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                # Falta user_id
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('user_id', str(response.data))
    
    # ========== TESTS DE FUNCIONALIDAD AUXILIAR ==========
    
    def test_verificar_puede_aceptar(self):
        """Test: Endpoint para verificar si se puede aceptar."""
        presupuesto, _ = self.crear_presupuesto()
        
        response = self.client.get(f'/api/presupuestos/{presupuesto.id}/puede-aceptar/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['puede_aceptar'])
        self.assertEqual(len(response.data['razones']), 0)
    
    def test_verificar_no_puede_aceptar_caducado(self):
        """Test: Verificar retorna false si está caducado."""
        fecha_caducada = date.today() - timedelta(days=1)
        presupuesto, _ = self.crear_presupuesto(fecha_vigencia=fecha_caducada)
        
        response = self.client.get(f'/api/presupuestos/{presupuesto.id}/puede-aceptar/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['puede_aceptar'])
        self.assertGreater(len(response.data['razones']), 0)
    
    def test_listar_comprobantes(self):
        """Test: Listar comprobantes de aceptación de un presupuesto."""
        presupuesto, _ = self.crear_presupuesto()
        
        # Crear aceptación
        AceptacionPresupuesto.objects.create(
            plandetratamiento=presupuesto,
            usuario_paciente=self.usuario_paciente,
            empresa=self.empresa,
            tipo_aceptacion='Total',
            firma_digital={'timestamp': timezone.now().isoformat(), 'user_id': 1},
            monto_total_aceptado=presupuesto.montototal
        )
        
        response = self.client.get(f'/api/presupuestos/{presupuesto.id}/comprobantes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['cantidad'], 1)
        self.assertEqual(len(response.data['comprobantes']), 1)
    
    def test_verificar_comprobante_valido(self):
        """Test: Verificar un comprobante existente."""
        presupuesto, _ = self.crear_presupuesto()
        
        aceptacion = AceptacionPresupuesto.objects.create(
            plandetratamiento=presupuesto,
            usuario_paciente=self.usuario_paciente,
            empresa=self.empresa,
            tipo_aceptacion='Total',
            firma_digital={'timestamp': timezone.now().isoformat(), 'user_id': 1},
            monto_total_aceptado=presupuesto.montototal
        )
        
        payload = {'comprobante_id': str(aceptacion.comprobante_id)}
        
        response = self.client.post('/api/aceptaciones/verificar/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valido'])
    
    def test_verificar_comprobante_invalido(self):
        """Test: Verificar un comprobante inexistente."""
        payload = {'comprobante_id': str(uuid.uuid4())}
        
        response = self.client.post('/api/aceptaciones/verificar/', payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['valido'])
    
    # ========== TESTS DE MODELO ==========
    
    def test_modelo_esta_vigente(self):
        """Test: Método esta_vigente() del modelo."""
        # Vigente
        presupuesto, _ = self.crear_presupuesto(fecha_vigencia=date.today() + timedelta(days=10))
        self.assertTrue(presupuesto.esta_vigente())
        
        # Caducado
        presupuesto_caducado, _ = self.crear_presupuesto(fecha_vigencia=date.today() - timedelta(days=1))
        self.assertFalse(presupuesto_caducado.esta_vigente())
        
        # Sin fecha de vigencia (siempre vigente)
        presupuesto_sin_fecha, _ = self.crear_presupuesto(fecha_vigencia=None)
        self.assertTrue(presupuesto_sin_fecha.esta_vigente())
    
    def test_modelo_puede_ser_aceptado(self):
        """Test: Método puede_ser_aceptado() del modelo."""
        # Puede ser aceptado
        presupuesto, _ = self.crear_presupuesto()
        self.assertTrue(presupuesto.puede_ser_aceptado())
        
        # Ya aceptado
        presupuesto_aceptado, _ = self.crear_presupuesto(estado_aceptacion='Aceptado')
        self.assertFalse(presupuesto_aceptado.puede_ser_aceptado())
        
        # Caducado
        presupuesto_caducado, _ = self.crear_presupuesto(
            fecha_vigencia=date.today() - timedelta(days=1)
        )
        self.assertFalse(presupuesto_caducado.puede_ser_aceptado())
    
    def test_modelo_marcar_como_caducado(self):
        """Test: Método marcar_como_caducado() del modelo."""
        presupuesto, _ = self.crear_presupuesto()
        
        presupuesto.marcar_como_caducado()
        
        self.assertEqual(presupuesto.estado_aceptacion, 'Caducado')
        self.assertFalse(presupuesto.es_editable)
    
    # ========== TESTS DE METADATOS ==========
    
    def test_captura_ip_y_user_agent(self):
        """Test: Se captura IP y User Agent del cliente."""
        presupuesto, _ = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Total',
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        aceptacion = AceptacionPresupuesto.objects.get(plandetratamiento=presupuesto)
        self.assertIsNotNone(aceptacion.ip_address)
        self.assertIsNotNone(aceptacion.user_agent)
    
    def test_registro_bitacora_completo(self):
        """Test: La bitácora registra toda la información necesaria."""
        presupuesto, items = self.crear_presupuesto()
        
        payload = {
            'tipo_aceptacion': 'Parcial',
            'items_aceptados': [items[0].id],
            'firma_digital': {
                'timestamp': timezone.now().isoformat(),
                'user_id': self.usuario_paciente.id,
            }
        }
        
        response = self.client.post(
            f'/api/presupuestos/{presupuesto.id}/aceptar/',
            payload,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        bitacora = Bitacora.objects.filter(
            accion='ACEPTACION_PRESUPUESTO',
            usuario=self.usuario_paciente
        ).first()
        
        self.assertIsNotNone(bitacora)
        self.assertIn('presupuesto_id', bitacora.detalles)
        self.assertIn('tipo_aceptacion', bitacora.detalles)
        self.assertIn('comprobante_id', bitacora.detalles)


class AceptacionPresupuestoModelTests(TestCase):
    """Tests unitarios para el modelo AceptacionPresupuesto."""
    
    def setUp(self):
        """Setup mínimo para tests de modelo."""
        self.empresa = Empresa.objects.create(
            nombre="Test Clinic",
            subdomain="test",
            activo=True
        )
        
        tipo_paciente = Tipodeusuario.objects.create(rol="Paciente")
        tipo_odontologo = Tipodeusuario.objects.create(rol="Odontologo")
        
        self.usuario = Usuario.objects.create_user(
            email="test@test.com",
            password="test",
            nombre="Test",
            apellido="User",
            empresa=self.empresa,
            idtipousuario=tipo_paciente
        )
        
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario,
            empresa=self.empresa
        )
        
        usuario_odontologo = Usuario.objects.create_user(
            email="doc@test.com",
            password="test",
            nombre="Doc",
            apellido="Test",
            empresa=self.empresa,
            idtipousuario=tipo_odontologo
        )
        
        self.odontologo = Odontologo.objects.create(
            codusuario=usuario_odontologo,
            empresa=self.empresa
        )
        
        estado = Estado.objects.create(nombreestado="Pendiente", empresa=self.empresa)
        
        self.presupuesto = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=estado,
            fechaplan=date.today(),
            montototal=Decimal("1000.00"),
            empresa=self.empresa
        )
    
    def test_crear_aceptacion_presupuesto(self):
        """Test: Crear registro de aceptación."""
        aceptacion = AceptacionPresupuesto.objects.create(
            plandetratamiento=self.presupuesto,
            usuario_paciente=self.usuario,
            empresa=self.empresa,
            tipo_aceptacion='Total',
            firma_digital={'timestamp': timezone.now().isoformat(), 'user_id': 1},
            monto_total_aceptado=Decimal("1000.00")
        )
        
        self.assertIsNotNone(aceptacion.id)
        self.assertIsNotNone(aceptacion.comprobante_id)
        self.assertIsNotNone(aceptacion.fecha_aceptacion)
    
    def test_comprobante_id_unico(self):
        """Test: El comprobante_id es único."""
        aceptacion1 = AceptacionPresupuesto.objects.create(
            plandetratamiento=self.presupuesto,
            usuario_paciente=self.usuario,
            empresa=self.empresa,
            tipo_aceptacion='Total',
            firma_digital={},
            monto_total_aceptado=Decimal("1000.00")
        )
        
        aceptacion2 = AceptacionPresupuesto.objects.create(
            plandetratamiento=self.presupuesto,
            usuario_paciente=self.usuario,
            empresa=self.empresa,
            tipo_aceptacion='Parcial',
            firma_digital={},
            monto_total_aceptado=Decimal("500.00")
        )
        
        self.assertNotEqual(aceptacion1.comprobante_id, aceptacion2.comprobante_id)
    
    def test_url_verificacion_comprobante(self):
        """Test: Generación de URL de verificación."""
        aceptacion = AceptacionPresupuesto.objects.create(
            plandetratamiento=self.presupuesto,
            usuario_paciente=self.usuario,
            empresa=self.empresa,
            tipo_aceptacion='Total',
            firma_digital={},
            monto_total_aceptado=Decimal("1000.00")
        )
        
        url = aceptacion.get_comprobante_verificacion_url()
        self.assertIn(str(aceptacion.comprobante_id), url)
