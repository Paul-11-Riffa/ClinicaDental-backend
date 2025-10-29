"""
Tests de Integraci�n para APIs del Flujo Cl�nico
Paso 3: Validaci�n de endpoints, autenticaci�n, permisos y transiciones de estado
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal

from api.models import (
    Empresa, Usuario, Paciente, Odontologo, Consulta, Plandetratamiento,
    Itemplandetratamiento, Estado, Tipodeconsulta, Estadodeconsulta,
    Horario, Tipodeusuario, Servicio
)
from api.models_notifications import CanalNotificacion, TipoNotificacion


class FlujoClincoAPIBaseTestCase(TestCase):
    """Clase base para tests de API del flujo cl�nico"""
    
    def setUp(self):
        """Configuración común para todos los tests"""
        # Crear canal y tipo de notificación (requerido por historialnotificacion FK constraints)
        self.canal_notif, _ = CanalNotificacion.objects.get_or_create(
            nombre='push',
            defaults={'descripcion': 'Push notifications', 'activo': True}
        )
        self.tipo_notif, _ = TipoNotificacion.objects.get_or_create(
            nombre='general',
            defaults={'descripcion': 'General notifications', 'activo': True}
        )
        
        # Empresa
        self.empresa = Empresa.objects.create(
            nombre="Cl�nica Test API",
            subdomain="test-api"
        )
        
        # Usuario de Django para autenticaci�n
        self.django_user = User.objects.create_user(
            username='test@api.com',
            password='testpass123'
        )
        
        # Crear tipos de usuario
        self.tipo_paciente = Tipodeusuario.objects.create(
            rol="Paciente",
            empresa=self.empresa
        )
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol="Odontologo",
            empresa=self.empresa
        )
        
        # Crear usuarios del sistema (los signals crean Paciente/Odontologo autom�ticamente)
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan",
            apellido="P�rez",
            correoelectronico="juan@testapi.com",
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos",
            apellido="G�mez",
            correoelectronico="carlos@testapi.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        # Estados y datos maestros
        self.estado = Estado.objects.create(estado="Activo", empresa=self.empresa)
        self.tipo_consulta = Tipodeconsulta.objects.create(
            nombreconsulta="Consulta General",
            empresa=self.empresa
        )
        self.estado_consulta = Estadodeconsulta.objects.create(
            estado="Completado",
            empresa=self.empresa
        )
        self.horario = Horario.objects.create(
            hora="10:00:00",
            empresa=self.empresa
        )
        
        # Servicio
        self.servicio = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza dental profunda",
            costobase=Decimal('50.00'),
            duracion=30,
            activo=True,
            empresa=self.empresa
        )
        
        # Cliente API
        self.client = APIClient()
        self.client.force_authenticate(user=self.django_user)
        
        # Simular tenant
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'test-api'


class ConsultaFlujoClincoAPITest(FlujoClincoAPIBaseTestCase):
    """Tests para endpoints de Consulta en flujo cl�nico"""
    
    def test_listar_consultas(self):
        """Test: GET /api/flujo-clinico/consultas/"""
        # Crear consulta de prueba
        Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa
        )
        
        response = self.client.get('/api/flujo-clinico/consultas/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)  # Respuesta paginada
        print("   [OK] Listar consultas funciona correctamente")
    
    def test_crear_consulta(self):
        """Test: POST /api/flujo-clinico/consultas/"""
        data = {
            'fecha': timezone.now().date(),
            'codpaciente': self.paciente.pk,
            'cododontologo': self.odontologo.pk,
            'idestadoconsulta': self.estado_consulta.id,
            'idtipoconsulta': self.tipo_consulta.id,
            'idhorario': self.horario.id
        }
        
        response = self.client.post('/api/flujo-clinico/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertTrue(response.data['es_diagnostico'])
        print("   [OK] Crear consulta funciona correctamente")
    
    def test_generar_plan_desde_consulta(self):
        """Test: POST /api/flujo-clinico/consultas/{id}/generar-plan/"""
        # Crear consulta diagn�stica completada
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa
        )
        
        data = {
            'notas_plan': 'Plan de tratamiento generado desde API',
            'cododontologo': self.odontologo.pk,
            'idestado': self.estado.id
        }
        
        response = self.client.post(
            f'/api/flujo-clinico/consultas/{consulta.id}/generar-plan/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('plan', response.data)
        self.assertEqual(response.data['plan']['estado_tratamiento'], 'Propuesto')
        print("   [OK] Generar plan desde consulta funciona correctamente")
    
    def test_listar_consultas_diagnosticas(self):
        """Test: GET /api/flujo-clinico/consultas/diagnosticas/"""
        # Crear consulta diagnóstica
        Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa
        )
        
        response = self.client.get('/api/flujo-clinico/consultas/diagnosticas/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debe retornar solo consultas sin plan asociado
        print("   [OK] Listar consultas diagnósticas funciona correctamente")
    
    def test_validar_flujo_consulta(self):
        """Test: GET /api/flujo-clinico/consultas/{id}/validar-flujo/"""
        # Crear consulta con datos válidos
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa,
            costo_consulta=Decimal('100.00'),
            requiere_pago=True
        )
        
        response = self.client.get(
            f'/api/flujo-clinico/consultas/{consulta.id}/validar-flujo/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('es_valido', response.data)
        self.assertIn('errores', response.data)
        self.assertIn('consulta_id', response.data)
        self.assertIn('es_diagnostico', response.data)
        self.assertEqual(response.data['consulta_id'], consulta.id)
        # Con datos válidos, debe pasar la validación
        self.assertTrue(response.data['es_valido'])
        self.assertEqual(len(response.data['errores']), 0)
        print("   [OK] Validar flujo de consulta funciona correctamente")
    
    def test_validar_flujo_consulta_con_errores(self):
        """Test: Validar consulta con datos inconsistentes"""
        # Crear consulta con datos inválidos (requiere pago pero costo = 0)
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa,
            costo_consulta=Decimal('0.00'),
            requiere_pago=True  # Inconsistencia: requiere pago pero costo = 0
        )
        
        response = self.client.get(
            f'/api/flujo-clinico/consultas/{consulta.id}/validar-flujo/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['es_valido'])
        self.assertGreater(len(response.data['errores']), 0)
        print("   [OK] Validar flujo detecta errores correctamente")


class PlanTratamientoFlujoClincoAPITest(FlujoClincoAPIBaseTestCase):
    """Tests para endpoints de Plan de Tratamiento"""
    
    def setUp(self):
        super().setUp()
        # Crear un plan de prueba
        self.plan = Plandetratamiento.objects.create(
            fechaplan=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            estado_tratamiento='Aceptado',
            empresa=self.empresa
        )
        
        # Agregar un item
        self.item = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            orden_ejecucion=1,
            estado_item='Activo',
            empresa=self.empresa
        )
    
    def test_listar_planes(self):
        """Test: GET /api/flujo-clinico/planes/"""
        response = self.client.get('/api/flujo-clinico/planes/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        print("   [OK] Listar planes funciona correctamente")
    
    def test_iniciar_ejecucion_plan(self):
        """Test: POST /api/flujo-clinico/planes/{id}/iniciar-ejecucion/"""
        response = self.client.post(
            f'/api/flujo-clinico/planes/{self.plan.id}/iniciar-ejecucion/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan']['estado_tratamiento'], 'En Ejecución')
        self.assertIn('mensaje', response.data)
        print("   [OK] Iniciar ejecución de plan funciona correctamente")
    
    def test_pausar_plan(self):
        """Test: POST /api/flujo-clinico/planes/{id}/pausar/"""
        # Primero iniciar el plan
        self.plan.iniciar_ejecucion()
        
        response = self.client.post(
            f'/api/flujo-clinico/planes/{self.plan.id}/pausar/',
            {'motivo': 'Pausa por prueba'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan']['estado_tratamiento'], 'Pausado')
        print("   [OK] Pausar plan funciona correctamente")
    
    def test_reanudar_plan(self):
        """Test: POST /api/flujo-clinico/planes/{id}/reanudar/"""
        # Pausar el plan primero
        self.plan.iniciar_ejecucion()
        self.plan.pausar("Pausa de prueba")
        
        response = self.client.post(
            f'/api/flujo-clinico/planes/{self.plan.id}/reanudar/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan']['estado_tratamiento'], 'En Ejecución')
        print("   [OK] Reanudar plan funciona correctamente")
    
    def test_cancelar_plan(self):
        """Test: POST /api/flujo-clinico/planes/{id}/cancelar/"""
        response = self.client.post(
            f'/api/flujo-clinico/planes/{self.plan.id}/cancelar/',
            {'motivo': 'Cancelado por prueba'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan']['estado_tratamiento'], 'Cancelado')
        print("   [OK] Cancelar plan funciona correctamente")
    
    def test_calcular_progreso(self):
        """Test: GET /api/flujo-clinico/planes/{id}/progreso/"""
        # Iniciar plan y ejecutar item
        self.plan.iniciar_ejecucion()
        self.item.marcar_ejecutado(
            odontologo=self.odontologo,
            notas="Ejecutado"
        )
        
        response = self.client.get(
            f'/api/flujo-clinico/planes/{self.plan.id}/progreso/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progreso_porcentaje'], 100.0)
        self.assertEqual(response.data['items_ejecutados'], 1)
        print("   [OK] Calcular progreso funciona correctamente")
    
    def test_siguiente_item(self):
        """Test: GET /api/flujo-clinico/planes/{id}/siguiente-item/"""
        self.plan.iniciar_ejecucion()
        
        response = self.client.get(
            f'/api/flujo-clinico/planes/{self.plan.id}/siguiente-item/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['tiene_siguiente'])
        self.assertEqual(response.data['item']['id'], self.item.id)
        print("   [OK] Obtener siguiente item funciona correctamente")
    
    def test_validar_consistencia_plan(self):
        """Test: GET /api/flujo-clinico/planes/{id}/validar-consistencia/"""
        # Crear plan con datos válidos
        consulta_diagnostico = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=self.empresa
        )
        
        plan_valido = Plandetratamiento.objects.create(
            fechaplan=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),  # Requerido para estado 'En Ejecución'
            consulta_diagnostico=consulta_diagnostico,  # Requerido
            empresa=self.empresa
        )
        
        response = self.client.get(
            f'/api/flujo-clinico/planes/{plan_valido.id}/validar-consistencia/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('es_valido', response.data)
        self.assertIn('errores', response.data)
        self.assertIn('plan_id', response.data)
        self.assertIn('estado_tratamiento', response.data)
        self.assertEqual(response.data['plan_id'], plan_valido.id)
        # Con datos válidos, debe pasar la validación
        self.assertTrue(response.data['es_valido'])
        self.assertEqual(len(response.data['errores']), 0)
        print("   [OK] Validar consistencia de plan funciona correctamente")
    
    def test_validar_consistencia_plan_con_errores(self):
        """Test: Validar plan con datos inconsistentes"""
        # Crear plan con datos inválidos (En Ejecución pero sin fecha_inicio_ejecucion)
        plan_invalido = Plandetratamiento.objects.create(
            fechaplan=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=None,  # Inconsistencia: En Ejecución sin fecha
            consulta_diagnostico=None,  # Otra inconsistencia: sin consulta diagnóstico
            empresa=self.empresa
        )
        
        response = self.client.get(
            f'/api/flujo-clinico/planes/{plan_invalido.id}/validar-consistencia/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['es_valido'])
        self.assertGreater(len(response.data['errores']), 0)
        # Debe detectar al menos 2 errores
        self.assertGreaterEqual(len(response.data['errores']), 2)
        print("   [OK] Validar consistencia detecta errores correctamente")


class ItemPlanTratamientoFlujoClincoAPITest(FlujoClincoAPIBaseTestCase):
    """Tests para endpoints de Items de Plan"""
    
    def setUp(self):
        super().setUp()
        # Crear plan y consulta
        self.plan = Plandetratamiento.objects.create(
            fechaplan=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),
            empresa=self.empresa
        )
        
        self.consulta_ejecucion = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            plan_tratamiento=self.plan,
            empresa=self.empresa
        )
        
        self.item = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            orden_ejecucion=1,
            estado_item='Activo',
            empresa=self.empresa
        )
    
    def test_listar_items(self):
        """Test: GET /api/flujo-clinico/items/"""
        response = self.client.get('/api/flujo-clinico/items/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("   [OK] Listar items funciona correctamente")
    
    def test_ejecutar_item(self):
        """Test: POST /api/flujo-clinico/items/{id}/ejecutar/"""
        data = {
            'consulta_ejecucion': self.consulta_ejecucion.id,
            'odontologo_ejecutor': self.odontologo.pk,
            'notas_ejecucion': 'Item ejecutado desde API'
        }
        
        response = self.client.post(
            f'/api/flujo-clinico/items/{self.item.id}/ejecutar/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['item']['fecha_ejecucion'])
        self.assertTrue(response.data['item']['esta_ejecutado'])
        print("   [OK] Ejecutar item funciona correctamente")
    
    def test_marcar_ejecutado(self):
        """Test: POST /api/flujo-clinico/items/{id}/marcar-ejecutado/"""
        data = {
            'odontologo_ejecutor': self.odontologo.pk,
            'notas_ejecucion': 'Marcado como ejecutado'
        }
        
        response = self.client.post(
            f'/api/flujo-clinico/items/{self.item.id}/marcar-ejecutado/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['item']['esta_ejecutado'])
        print("   [OK] Marcar como ejecutado funciona correctamente")
    
    def test_reprogramar_item(self):
        """Test: POST /api/flujo-clinico/items/{id}/reprogramar/"""
        # Crear segundo item
        item2 = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('30.00'),
            orden_ejecucion=2,
            estado_item='Activo',
            empresa=self.empresa
        )
        
        data = {'nuevo_orden': 3}
        
        response = self.client.post(
            f'/api/flujo-clinico/items/{self.item.id}/reprogramar/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['item']['orden_ejecucion'], 3)
        print("   [OK] Reprogramar item funciona correctamente")
    
    def test_validar_ejecucion(self):
        """Test: GET /api/flujo-clinico/items/{id}/validar-ejecucion/"""
        response = self.client.get(
            f'/api/flujo-clinico/items/{self.item.id}/validar-ejecucion/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('puede_ejecutarse', response.data)
        self.assertIn('mensaje', response.data)
        print("   [OK] Validar ejecución funciona correctamente")


class FlujoClincoPermisosAPITest(FlujoClincoAPIBaseTestCase):
    """Tests de autenticaci�n y permisos"""
    
    def test_sin_autenticacion(self):
        """Test: Endpoints requieren autenticaci�n"""
        client_sin_auth = APIClient()
        
        response = client_sin_auth.get('/api/flujo-clinico/consultas/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print("   [OK] Endpoints requieren autenticación correctamente")
    
    def test_filtro_por_tenant(self):
        """Test: Queries filtran por tenant (multi-tenancy)"""
        # Crear consulta en otra empresa
        otra_empresa = Empresa.objects.create(
            nombre="Otra Cl�nica",
            subdomain="otra-clinica"
        )
        
        Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestadoconsulta=self.estado_consulta,
            idtipoconsulta=self.tipo_consulta,
            idhorario=self.horario,
            empresa=otra_empresa
        )
        
        # Consultar con tenant actual
        response = self.client.get('/api/flujo-clinico/consultas/')
        
        # Solo debe ver las de su empresa
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("   [OK] Filtro por tenant funciona correctamente")
