"""
Tests para el catálogo de servicios dentales
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from api.models import Empresa, Usuario, Tipodeusuario, Servicio


class ServicioModelTest(TestCase):
    """Tests para el modelo Servicio"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
    
    def test_crear_servicio_completo(self):
        """Verificar que se puede crear un servicio con todos los campos"""
        servicio = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza dental profesional completa",
            costobase=Decimal("150.00"),
            duracion=45,
            activo=True,
            empresa=self.empresa
        )
        
        self.assertEqual(servicio.nombre, "Limpieza Dental")
        self.assertEqual(servicio.costobase, Decimal("150.00"))
        self.assertEqual(servicio.duracion, 45)
        self.assertTrue(servicio.activo)
        self.assertIsNotNone(servicio.fecha_creacion)
        self.assertIsNotNone(servicio.fecha_modificacion)
    
    def test_servicio_activo_por_defecto(self):
        """Verificar que el servicio es activo por defecto"""
        servicio = Servicio.objects.create(
            nombre="Consulta General",
            costobase=Decimal("50.00"),
            empresa=self.empresa
        )
        
        self.assertTrue(servicio.activo)
        self.assertEqual(servicio.duracion, 30)  # Valor por defecto


class ServicioCatalogoAPITest(APITestCase):
    """Tests para el API del catálogo de servicios"""
    
    def setUp(self):
        """Configuración inicial para cada test del API"""
        # Crear empresa/tenant
        self.empresa = Empresa.objects.create(
            nombre="Clínica Norte",
            subdomain="norte",
            activo=True
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            rol="Recepcionista",
            empresa=self.empresa
        )
        
        # Crear usuario de Django
        self.django_user = User.objects.create_user(
            username='testuser@test.com',
            password='testpass123',
            email='testuser@test.com'
        )
        
        # Crear usuario del sistema
        self.usuario = Usuario.objects.create(
            nombre="Test",
            apellido="User",
            correoelectronico="testuser@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.django_user)
        
        # Configurar cliente API
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'norte'
        
        # Crear servicios de prueba
        self.servicio1 = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza profesional completa con ultrasonido",
            costobase=Decimal("150.00"),
            duracion=45,
            activo=True,
            empresa=self.empresa
        )
        
        self.servicio2 = Servicio.objects.create(
            nombre="Endodoncia",
            descripcion="Tratamiento de conducto completo",
            costobase=Decimal("800.00"),
            duracion=90,
            activo=True,
            empresa=self.empresa
        )
        
        self.servicio3 = Servicio.objects.create(
            nombre="Ortodoncia Mensual",
            descripcion="Control mensual de brackets",
            costobase=Decimal("200.00"),
            duracion=30,
            activo=True,
            empresa=self.empresa
        )
        
        self.servicio_inactivo = Servicio.objects.create(
            nombre="Servicio Antiguo",
            descripcion="Este servicio ya no está disponible",
            costobase=Decimal("100.00"),
            duracion=30,
            activo=False,
            empresa=self.empresa
        )
    
    def test_listar_servicios_activos(self):
        """Verificar que solo se listan servicios activos por defecto"""
        url = '/clinic/servicios/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)  # Solo los 3 activos
    
    def test_listar_todos_servicios_con_filtro(self):
        """Verificar que se pueden listar todos los servicios incluyendo inactivos"""
        url = '/clinic/servicios/?activo='
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)  # Todos los servicios
    
    def test_busqueda_por_texto(self):
        """Verificar búsqueda por texto en nombre y descripción"""
        url = '/clinic/servicios/?search=limpieza'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nombre'], "Limpieza Dental")
    
    def test_filtro_rango_precio(self):
        """Verificar filtro por rango de precio"""
        url = '/clinic/servicios/?precio_min=150&precio_max=250'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Limpieza (150) y Ortodoncia (200)
    
    def test_filtro_precio_minimo(self):
        """Verificar filtro por precio mínimo"""
        url = '/clinic/servicios/?precio_min=500'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nombre'], "Endodoncia")
    
    def test_filtro_duracion(self):
        """Verificar filtro por duración"""
        url = '/clinic/servicios/?duracion_min=60'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nombre'], "Endodoncia")
    
    def test_ordenamiento_por_nombre(self):
        """Verificar ordenamiento por nombre"""
        url = '/clinic/servicios/?ordering=nombre'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        nombres = [item['nombre'] for item in response.data['results']]
        self.assertEqual(nombres, sorted(nombres))
    
    def test_ordenamiento_por_precio(self):
        """Verificar ordenamiento por precio"""
        url = '/clinic/servicios/?ordering=costobase'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        precios = [Decimal(item['costobase']) for item in response.data['results']]
        self.assertEqual(precios, sorted(precios))
    
    def test_ordenamiento_por_duracion(self):
        """Verificar ordenamiento por duración"""
        url = '/clinic/servicios/?ordering=duracion'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        duraciones = [item['duracion'] for item in response.data['results']]
        self.assertEqual(duraciones, sorted(duraciones))
    
    def test_paginacion(self):
        """Verificar que la paginación funciona correctamente"""
        # Crear más servicios para probar paginación
        for i in range(15):
            Servicio.objects.create(
                nombre=f"Servicio {i}",
                costobase=Decimal("100.00"),
                duracion=30,
                activo=True,
                empresa=self.empresa
            )
        
        url = '/clinic/servicios/?page_size=5'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
        self.assertIsNotNone(response.data.get('next'))
    
    def test_detalle_servicio(self):
        """Verificar endpoint de detalle de servicio"""
        url = f'/clinic/servicios/{self.servicio1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], "Limpieza Dental")
        self.assertEqual(Decimal(response.data['precio_vigente']), Decimal("150.00"))
        self.assertIn('descripcion', response.data)
        self.assertIn('duracion', response.data)
    
    def test_detalle_completo_servicio(self):
        """Verificar endpoint de detalle completo"""
        url = f'/clinic/servicios/{self.servicio1.id}/detalle_completo/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], "Limpieza Dental")
        self.assertIn('precio_vigente', response.data)
        self.assertIn('fecha_creacion', response.data)
        self.assertIn('fecha_modificacion', response.data)
    
    def test_crear_servicio(self):
        """Verificar creación de nuevo servicio"""
        url = '/clinic/servicios/'
        data = {
            'nombre': 'Blanqueamiento Dental',
            'descripcion': 'Blanqueamiento profesional con gel',
            'costobase': '400.00',
            'duracion': 60,
            'activo': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Servicio.objects.filter(nombre='Blanqueamiento Dental').count(), 1)
    
    def test_actualizar_servicio(self):
        """Verificar actualización de servicio"""
        url = f'/clinic/servicios/{self.servicio1.id}/'
        data = {
            'nombre': 'Limpieza Dental Premium',
            'descripcion': 'Limpieza profesional completa con ultrasonido',
            'costobase': '180.00',
            'duracion': 60,
            'activo': True
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.servicio1.refresh_from_db()
        self.assertEqual(self.servicio1.nombre, 'Limpieza Dental Premium')
        self.assertEqual(self.servicio1.costobase, Decimal('180.00'))
    
    def test_desactivar_servicio(self):
        """Verificar desactivación de servicio"""
        url = f'/clinic/servicios/{self.servicio1.id}/'
        data = {
            'nombre': self.servicio1.nombre,
            'descripcion': self.servicio1.descripcion,
            'costobase': str(self.servicio1.costobase),
            'duracion': self.servicio1.duracion,
            'activo': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.servicio1.refresh_from_db()
        self.assertFalse(self.servicio1.activo)
        
        # Verificar que no aparece en listado por defecto
        url = '/clinic/servicios/'
        response = self.client.get(url)
        nombres = [item['nombre'] for item in response.data['results']]
        self.assertNotIn('Limpieza Dental', nombres)
    
    def test_sin_autenticacion(self):
        """Verificar que NO se requiere autenticación para consultas (acceso público)"""
        self.client.credentials()  # Remover credenciales
        url = '/clinic/servicios/'
        response = self.client.get(url)
        
        # Ahora debe permitir acceso sin autenticación para GET
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_aislamiento_tenant(self):
        """Verificar que solo se ven servicios del tenant actual"""
        # Crear otra empresa
        otra_empresa = Empresa.objects.create(
            nombre="Clínica Sur",
            subdomain="sur",
            activo=True
        )
        
        # Crear servicio en otra empresa
        Servicio.objects.create(
            nombre="Servicio de Otra Clínica",
            costobase=Decimal("100.00"),
            empresa=otra_empresa
        )
        
        url = '/clinic/servicios/'
        response = self.client.get(url)
        
        # Solo debe ver los servicios de su empresa (norte)
        for item in response.data['results']:
            self.assertNotEqual(item['nombre'], "Servicio de Otra Clínica")
    
    def test_crear_sin_autenticacion_falla(self):
        """Verificar que NO se puede crear un servicio sin autenticación"""
        self.client.credentials()  # Remover credenciales
        url = '/clinic/servicios/'
        data = {
            'nombre': 'Servicio sin Auth',
            'descripcion': 'Este intento debe fallar',
            'costobase': '100.00',
            'duracion': 30,
            'activo': True
        }
        response = self.client.post(url, data, format='json')
        
        # Debe rechazar la creación por falta de autenticación
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_acceso_publico_listado(self):
        """Verificar que pacientes sin autenticación pueden ver el listado"""
        self.client.credentials()  # Remover credenciales
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'norte'
        
        url = '/clinic/servicios/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 3)  # Debe ver los servicios activos
    
    def test_acceso_publico_detalle(self):
        """Verificar que pacientes sin autenticación pueden ver el detalle"""
        self.client.credentials()  # Remover credenciales
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'norte'
        
        url = f'/clinic/servicios/{self.servicio1.id}/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nombre'], "Limpieza Dental")
        self.assertIn('precio_vigente', response.data)
