"""
Tests completos para el módulo de Combos/Paquetes de Servicios.
Implementa SP3-T007: Crear paquete o combo de servicios (web)
"""
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status

from api.models import (
    Empresa, Usuario, Tipodeusuario, Servicio,
    ComboServicio, ComboServicioDetalle
)


class ComboServicioModelTest(TestCase):
    """Tests para el modelo ComboServicio"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
        
        # Crear servicios de prueba
        self.servicio1 = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza profesional",
            costobase=Decimal("150.00"),
            duracion=45,
            empresa=self.empresa
        )
        
        self.servicio2 = Servicio.objects.create(
            nombre="Blanqueamiento",
            descripcion="Blanqueamiento dental",
            costobase=Decimal("500.00"),
            duracion=60,
            empresa=self.empresa
        )
        
        self.servicio3 = Servicio.objects.create(
            nombre="Consulta",
            descripcion="Consulta general",
            costobase=Decimal("50.00"),
            duracion=30,
            empresa=self.empresa
        )
    
    def test_crear_combo_porcentaje(self):
        """Verificar creación de combo con descuento porcentual"""
        combo = ComboServicio.objects.create(
            nombre="Paquete Básico",
            descripcion="Limpieza + Consulta",
            tipo_precio='PORCENTAJE',
            valor_precio=Decimal("20.00"),  # 20% descuento
            empresa=self.empresa
        )
        
        # Agregar servicios
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=1
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio3,
            cantidad=1
        )
        
        # Verificar cálculos
        precio_total = combo.calcular_precio_total_servicios()
        self.assertEqual(precio_total, Decimal("200.00"))  # 150 + 50
        
        precio_final = combo.calcular_precio_final()
        self.assertEqual(precio_final, Decimal("160.00"))  # 200 - 20%
        
        duracion = combo.calcular_duracion_total()
        self.assertEqual(duracion, 75)  # 45 + 30
    
    def test_crear_combo_monto_fijo(self):
        """Verificar combo con precio fijo"""
        combo = ComboServicio.objects.create(
            nombre="Paquete Premium",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("500.00"),
            empresa=self.empresa
        )
        
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=2
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio2,
            cantidad=1
        )
        
        # El precio total de servicios es 150*2 + 500 = 800
        # Pero el precio final es fijo en 500
        precio_final = combo.calcular_precio_final()
        self.assertEqual(precio_final, Decimal("500.00"))
    
    def test_crear_combo_promocion(self):
        """Verificar combo con precio promocional"""
        combo = ComboServicio.objects.create(
            nombre="Oferta Especial",
            tipo_precio='PROMOCION',
            valor_precio=Decimal("399.99"),
            empresa=self.empresa
        )
        
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=1
        )
        
        precio_final = combo.calcular_precio_final()
        self.assertEqual(precio_final, Decimal("399.99"))
    
    def test_precio_negativo_rechazado(self):
        """Verificar que se rechaza precio final negativo"""
        combo = ComboServicio.objects.create(
            nombre="Combo Inválido",
            tipo_precio='PORCENTAJE',
            valor_precio=Decimal("150.00"),  # 150% descuento - inválido
            empresa=self.empresa
        )
        
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio3,
            cantidad=1
        )
        
        # Debe lanzar ValueError
        with self.assertRaises(ValueError):
            combo.calcular_precio_final()
    
    def test_combo_sin_servicios(self):
        """Verificar combo sin servicios devuelve cero"""
        combo = ComboServicio.objects.create(
            nombre="Combo Vacío",
            tipo_precio='PORCENTAJE',
            valor_precio=Decimal("10.00"),
            empresa=self.empresa
        )
        
        precio_total = combo.calcular_precio_total_servicios()
        self.assertEqual(precio_total, Decimal("0.00"))
    
    def test_validacion_cantidades(self):
        """Verificar que las cantidades deben ser positivas"""
        combo = ComboServicio.objects.create(
            nombre="Test",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=self.empresa
        )
        
        # Intentar crear detalle con cantidad inválida debe fallar
        # (esto es validado por constraint de BD)
        with self.assertRaises(Exception):
            ComboServicioDetalle.objects.create(
                combo=combo,
                servicio=self.servicio1,
                cantidad=0  # Inválido
            )


class ComboServicioAPITest(APITestCase):
    """Tests para el API de combos de servicios"""
    
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
            rol="Administrador",
            empresa=self.empresa
        )
        
        # Crear usuario de Django
        self.django_user = User.objects.create_user(
            username='admin@test.com',
            password='testpass123',
            email='admin@test.com'
        )
        
        # Crear usuario del sistema
        self.usuario = Usuario.objects.create(
            nombre="Admin",
            apellido="Test",
            correoelectronico="admin@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Vincular usuario Django con usuario del sistema
        self.django_user.usuario = self.usuario
        self.django_user.save()
        
        # Crear token de autenticación
        self.token = Token.objects.create(user=self.django_user)
        
        # Configurar cliente API
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        self.client.defaults['HTTP_X_TENANT_SUBDOMAIN'] = 'norte'
        
        # Crear servicios de prueba
        self.servicio1 = Servicio.objects.create(
            nombre="Limpieza Dental",
            costobase=Decimal("150.00"),
            duracion=45,
            activo=True,
            empresa=self.empresa
        )
        
        self.servicio2 = Servicio.objects.create(
            nombre="Blanqueamiento",
            costobase=Decimal("500.00"),
            duracion=60,
            activo=True,
            empresa=self.empresa
        )
        
        self.servicio3 = Servicio.objects.create(
            nombre="Consulta",
            costobase=Decimal("50.00"),
            duracion=30,
            activo=True,
            empresa=self.empresa
        )
    
    def test_crear_combo_completo(self):
        """Test crear combo con todos sus detalles (SP3-T007.a)"""
        url = '/api/combos-servicios/'
        data = {
            'nombre': 'Paquete Básico',
            'descripcion': 'Limpieza + Consulta con descuento',
            'tipo_precio': 'PORCENTAJE',
            'valor_precio': '20.00',
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio1.id,
                    'cantidad': 1,
                    'orden': 1
                },
                {
                    'servicio': self.servicio3.id,
                    'cantidad': 1,
                    'orden': 2
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['mensaje'], 'Combo creado exitosamente')
        self.assertIn('combo', response.data)
        
        # Verificar que el combo fue creado correctamente
        combo = ComboServicio.objects.get(nombre='Paquete Básico')
        self.assertEqual(combo.detalles.count(), 2)
        self.assertEqual(combo.calcular_precio_final(), Decimal("160.00"))
    
    def test_editar_combo(self):
        """Test editar combo existente (SP3-T007.b)"""
        # Crear combo inicial
        combo = ComboServicio.objects.create(
            nombre="Combo Original",
            tipo_precio='PORCENTAJE',
            valor_precio=Decimal("10.00"),
            empresa=self.empresa
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=1
        )
        
        # Editar combo
        url = f'/api/combos-servicios/{combo.id}/'
        data = {
            'nombre': 'Combo Modificado',
            'descripcion': 'Descripción actualizada',
            'tipo_precio': 'PORCENTAJE',
            'valor_precio': '25.00',
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio1.id,
                    'cantidad': 2,
                    'orden': 1
                },
                {
                    'servicio': self.servicio2.id,
                    'cantidad': 1,
                    'orden': 2
                }
            ]
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar cambios
        combo.refresh_from_db()
        self.assertEqual(combo.nombre, 'Combo Modificado')
        self.assertEqual(combo.valor_precio, Decimal("25.00"))
        self.assertEqual(combo.detalles.count(), 2)
    
    def test_previsualizar_precio(self):
        """Test previsualizar precio sin guardar (SP3-T007.b)"""
        url = '/api/combos-servicios/previsualizar/'
        data = {
            'tipo_precio': 'PORCENTAJE',
            'valor_precio': '30.00',
            'servicios': [
                {'servicio_id': self.servicio1.id, 'cantidad': 1},
                {'servicio_id': self.servicio2.id, 'cantidad': 1}
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 150 + 500 = 650, con 30% descuento = 455
        self.assertEqual(
            Decimal(response.data['precio_total_servicios']),
            Decimal("650.00")
        )
        self.assertEqual(
            Decimal(response.data['precio_final']),
            Decimal("455.00")
        )
        self.assertEqual(
            Decimal(response.data['ahorro']),
            Decimal("195.00")
        )
    
    def test_rechazar_precio_negativo(self):
        """Test rechazar combo con precio final negativo (SP3-T007.b)"""
        url = '/api/combos-servicios/'
        data = {
            'nombre': 'Combo Inválido',
            'tipo_precio': 'PORCENTAJE',
            'valor_precio': '150.00',  # 150% descuento = negativo
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio3.id,
                    'cantidad': 1,
                    'orden': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Verificar que se rechaza por porcentaje inválido (>100%)
        self.assertIn('valor_precio', response.data['detalles'].lower())
    
    def test_desactivar_combo(self):
        """Test desactivar combo (SP3-T007.c)"""
        combo = ComboServicio.objects.create(
            nombre="Combo Activo",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            activo=True,
            empresa=self.empresa
        )
        
        url = f'/api/combos-servicios/{combo.id}/desactivar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('desactivado exitosamente', response.data['mensaje'])
        
        combo.refresh_from_db()
        self.assertFalse(combo.activo)
    
    def test_activar_combo(self):
        """Test activar combo desactivado"""
        combo = ComboServicio.objects.create(
            nombre="Combo Inactivo",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            activo=False,
            empresa=self.empresa
        )
        
        url = f'/api/combos-servicios/{combo.id}/activar/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        combo.refresh_from_db()
        self.assertTrue(combo.activo)
    
    def test_validar_cantidades_invalidas(self):
        """Test validar que no se permitan cantidades inválidas (SP3-T007.d)"""
        url = '/api/combos-servicios/'
        data = {
            'nombre': 'Combo Test',
            'tipo_precio': 'MONTO_FIJO',
            'valor_precio': '100.00',
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio1.id,
                    'cantidad': 0,  # Inválido
                    'orden': 1
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_validar_servicio_duplicado(self):
        """Test validar que no se dupliquen servicios en un combo"""
        url = '/api/combos-servicios/'
        data = {
            'nombre': 'Combo Test',
            'tipo_precio': 'MONTO_FIJO',
            'valor_precio': '100.00',
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio1.id,
                    'cantidad': 1,
                    'orden': 1
                },
                {
                    'servicio': self.servicio1.id,  # Duplicado
                    'cantidad': 2,
                    'orden': 2
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_listar_combos_activos(self):
        """Test listar solo combos activos por defecto"""
        ComboServicio.objects.create(
            nombre="Combo Activo 1",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            activo=True,
            empresa=self.empresa
        )
        ComboServicio.objects.create(
            nombre="Combo Activo 2",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("200.00"),
            activo=True,
            empresa=self.empresa
        )
        ComboServicio.objects.create(
            nombre="Combo Inactivo",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("150.00"),
            activo=False,
            empresa=self.empresa
        )
        
        url = '/api/combos-servicios/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Solo activos
    
    def test_aislamiento_tenant(self):
        """Test verificar aislamiento entre tenants"""
        # Crear otra empresa
        otra_empresa = Empresa.objects.create(
            nombre="Clínica Sur",
            subdomain="sur",
            activo=True
        )
        
        # Crear combo en otra empresa
        ComboServicio.objects.create(
            nombre="Combo de Otra Clínica",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=otra_empresa
        )
        
        # Crear combo en nuestra empresa
        ComboServicio.objects.create(
            nombre="Nuestro Combo",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=self.empresa
        )
        
        url = '/api/combos-servicios/'
        response = self.client.get(url)
        
        # Solo debe ver el combo de su empresa
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nombre'], 'Nuestro Combo')
    
    def test_detalle_completo_combo(self):
        """Test obtener detalle completo con todos los cálculos"""
        combo = ComboServicio.objects.create(
            nombre="Combo Completo",
            descripcion="Test",
            tipo_precio='PORCENTAJE',
            valor_precio=Decimal("20.00"),
            empresa=self.empresa
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=1
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio3,
            cantidad=1
        )
        
        url = f'/api/combos-servicios/{combo.id}/detalle_completo/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('precio_total_servicios', response.data)
        self.assertIn('precio_final', response.data)
        self.assertIn('ahorro', response.data)
        self.assertIn('duracion_total', response.data)
        self.assertIn('detalles', response.data)
        self.assertEqual(len(response.data['detalles']), 2)
    
    def test_guardar_desde_edicion(self):
        """Test guardar combo desde pantalla de edición (SP3-T007.e)"""
        # Crear combo
        combo = ComboServicio.objects.create(
            nombre="Combo Original",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=self.empresa
        )
        ComboServicioDetalle.objects.create(
            combo=combo,
            servicio=self.servicio1,
            cantidad=1
        )
        
        # Modificar desde edición (PUT)
        url = f'/api/combos-servicios/{combo.id}/'
        data = {
            'nombre': 'Combo Editado',
            'descripcion': 'Nueva descripción',
            'tipo_precio': 'PROMOCION',
            'valor_precio': '99.99',
            'activo': True,
            'detalles': [
                {
                    'servicio': self.servicio2.id,
                    'cantidad': 1,
                    'orden': 1
                }
            ]
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['mensaje'], 'Combo actualizado exitosamente')
        
        # Verificar cambios persistidos
        combo.refresh_from_db()
        self.assertEqual(combo.nombre, 'Combo Editado')
        self.assertEqual(combo.tipo_precio, 'PROMOCION')
        self.assertEqual(combo.detalles.count(), 1)
        self.assertEqual(combo.detalles.first().servicio, self.servicio2)
    
    def test_requiere_autenticacion(self):
        """Test verificar que se requiere autenticación"""
        self.client.credentials()  # Remover credenciales
        
        url = '/api/combos-servicios/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_busqueda_por_nombre(self):
        """Test buscar combos por nombre"""
        ComboServicio.objects.create(
            nombre="Paquete Premium",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("500.00"),
            empresa=self.empresa
        )
        ComboServicio.objects.create(
            nombre="Paquete Básico",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=self.empresa
        )
        
        url = '/api/combos-servicios/?search=Premium'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['nombre'], 'Paquete Premium')
    
    def test_ordenamiento_por_fecha(self):
        """Test ordenar combos por fecha de creación"""
        url = '/api/combos-servicios/?ordering=-fecha_creacion'
        
        combo1 = ComboServicio.objects.create(
            nombre="Combo 1",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("100.00"),
            empresa=self.empresa
        )
        combo2 = ComboServicio.objects.create(
            nombre="Combo 2",
            tipo_precio='MONTO_FIJO',
            valor_precio=Decimal("200.00"),
            empresa=self.empresa
        )
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # El más reciente debe ser el primero
        self.assertEqual(response.data['results'][0]['nombre'], 'Combo 2')
