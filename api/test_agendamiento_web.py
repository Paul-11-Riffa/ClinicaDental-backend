"""
Tests para Agendamiento Web de Consultas por Pacientes

Valida el flujo completo de agendamiento desde la web:
- Creación de consultas por pacientes
- Validaciones de tipos permitidos
- Límites de consultas pendientes
- Anti-spam (1 consulta por día)
- Asignación automática de prioridad

NOTA: Los tests desactivan señales de notificaciones para evitar errores de cola.
"""

from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, time
from django.utils import timezone
from django.db import connection
from unittest.mock import patch
from django.db.models import signals

from .models import (
    Consulta, Tipodeconsulta, Paciente, Odontologo, Recepcionista,
    Usuario, Tipodeusuario, Empresa, Horario, Estadodeconsulta
)
from .notifications_mobile.models import (
    CanalNotificacionMN, TipoNotificacionMN
)

User = get_user_model()


class BaseAgendamientoWebTest(TransactionTestCase):
    """
    Clase base para tests de agendamiento web.
    
    Usa TransactionTestCase en lugar de TestCase para poder crear
    datos que persistan entre queries (necesario para canales de notificación).
    
    IMPORTANTE: Desactiva señales de notificaciones móviles durante tests.
    """
    
    @classmethod
    def setUpClass(cls):
        """Setup que se ejecuta UNA VEZ para toda la clase"""
        super().setUpClass()
        
        # Mockear la función _enqueue de signals_consulta
        # Esto evita errores cuando las señales intentan encolar notificaciones
        cls.patcher_enqueue = patch('api.notifications_mobile.signals_consulta._enqueue')
        cls.mock_enqueue = cls.patcher_enqueue.start()
        cls.mock_enqueue.return_value = None
        
    @classmethod
    def tearDownClass(cls):
        """Cleanup que se ejecuta UNA VEZ después de todos los tests"""
        # Detener el mock
        cls.patcher_enqueue.stop()
        
        super().tearDownClass()
    
    def _crear_canales_notificacion(self):
        """Crea canales de notificación necesarios"""
        # Crear canales básicos para el sistema de notificaciones móviles
        canales_config = [
            ('PUSH_MOBILE', 'Notificación Push Móvil', True),
            ('email', 'Correo Electrónico', True),
            ('sms', 'SMS', False),
            ('whatsapp', 'WhatsApp', False),
        ]
        
        for nombre, descripcion, activo in canales_config:
            CanalNotificacionMN.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'descripcion': descripcion,
                    'activo': activo
                }
            )


class AgendamientoWebTestCase(BaseAgendamientoWebTest):
    """Tests para agendamiento web por pacientes"""
    
    def setUp(self):
        """Setup que se ejecuta ANTES de CADA test"""
        
        # PRIMERO: Crear canales de notificación
        self._crear_canales_notificacion()
        
        # Crear empresa (tenant)
        self.empresa = Empresa.objects.create(
            nombre='Clínica Test',
            subdomain='test',
            activo=True
        )
        
        # Crear tipos de usuario
        self.tipo_paciente = Tipodeusuario.objects.create(
            rol='Paciente',
            empresa=self.empresa
        )
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol='Odontologo',
            empresa=self.empresa
        )
        self.tipo_recepcionista = Tipodeusuario.objects.create(
            rol='Recepcionista',
            empresa=self.empresa
        )
        
        # Crear usuario paciente
        self.usuario_paciente = Usuario.objects.create(
            nombre='Juan',
            apellido='Pérez',
            correoelectronico='juan@test.com',
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        
        # El signal crea automáticamente el paciente, lo recuperamos
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        # Actualizar datos del paciente
        self.paciente.carnetidentidad = '12345678'
        self.paciente.fechanacimiento = '1990-01-01'
        self.paciente.direccion = 'Calle Test 123'
        self.paciente.save()
        
        # Crear usuario odontólogo
        self.usuario_odontologo = Usuario.objects.create(
            nombre='Dr. María',
            apellido='González',
            correoelectronico='maria@test.com',
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        
        # El signal crea automáticamente el odontólogo, lo recuperamos
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        # Actualizar datos del odontólogo
        self.odontologo.especialidad = 'Odontología General'
        self.odontologo.nromatricula = 'MAT-001'
        self.odontologo.save()
        
        # Crear usuario recepcionista
        self.usuario_recepcionista = Usuario.objects.create(
            nombre='Ana',
            apellido='Martínez',
            correoelectronico='ana@test.com',
            idtipousuario=self.tipo_recepcionista,
            empresa=self.empresa
        )
        
        # El signal crea automáticamente el recepcionista, lo recuperamos
        self.recepcionista = Recepcionista.objects.get(codusuario=self.usuario_recepcionista)
        
        # Crear horario
        self.horario = Horario.objects.create(
            hora=time(10, 0, 0),
            empresa=self.empresa
        )
        
        # Crear estado de consulta
        self.estado_pendiente = Estadodeconsulta.objects.create(
            estado='Pendiente',
            empresa=self.empresa
        )
        
        # Crear tipos de consulta
        self.tipo_permitido = Tipodeconsulta.objects.create(
            nombreconsulta='Consulta General',
            empresa=self.empresa,
            permite_agendamiento_web=True,
            es_urgencia=False,
            duracion_estimada=30
        )
        
        self.tipo_urgencia = Tipodeconsulta.objects.create(
            nombreconsulta='Urgencia Dental',
            empresa=self.empresa,
            permite_agendamiento_web=True,
            es_urgencia=True,
            duracion_estimada=30
        )
        
        self.tipo_no_permitido = Tipodeconsulta.objects.create(
            nombreconsulta='Cirugía',
            empresa=self.empresa,
            permite_agendamiento_web=False,
            es_urgencia=False,
            duracion_estimada=60
        )
        
        # Crear User de Django para autenticación
        self.django_user = User.objects.create_user(
            username=self.usuario_paciente.correoelectronico,
            email=self.usuario_paciente.correoelectronico,
            password='testpass123'
        )
        # Vincular con Usuario
        self.usuario_paciente.user = self.django_user
        
        # API Client
        self.client = APIClient()
    
    def test_crear_consulta_web_exitosa(self):
        """Test: Paciente puede crear consulta con tipo permitido"""
        self.client.force_authenticate(user=self.django_user)
        
        data = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Dolor en muela superior derecha hace 3 días, me molesta al masticar',
            'fecha_preferida': '2025-11-10',
            'horario_preferido': 'tarde',
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,  # Requerido por el modelo
            'idestadoconsulta': self.estado_pendiente.id,
            # cododontologo y codrecepcionista son opcionales para agendamiento web
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        # Debug: imprimir respuesta si falla
        if response.status_code != status.HTTP_201_CREATED:
            print(f"\nERROR {response.status_code}: {response.data}")
        
        # Verificar respuesta
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, 
                        f"Expected 201, got {response.status_code}: {response.data}")
        
        # Verificar que se creó en BD
        consulta_id = response.data.get('id')
        self.assertIsNotNone(consulta_id, "La respuesta debe incluir el ID de la consulta")
        
        consulta = Consulta.objects.get(id=consulta_id)
        self.assertEqual(consulta.codpaciente, self.paciente)
        self.assertTrue(consulta.agendado_por_web)
        self.assertEqual(consulta.prioridad, 'normal')
        self.assertEqual(consulta.horario_preferido, 'tarde')
    
    def test_crear_consulta_urgencia_asigna_prioridad(self):
        """Test: Consulta de urgencia automáticamente tiene prioridad urgente"""
        self.client.force_authenticate(user=self.django_user)
        
        data = {
            'idtipoconsulta': self.tipo_urgencia.id,
            'motivo_consulta': 'Dolor muy intenso, no puedo dormir, necesito atención urgente',
            'fecha_preferida': '2025-11-10',
            'horario_preferido': 'cualquiera',
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['prioridad'], 'urgente')
        
        # Verificar en BD
        consulta = Consulta.objects.get(id=response.data['id'])
        self.assertEqual(consulta.prioridad, 'urgente')
    
    def test_crear_consulta_tipo_no_permitido(self):
        """Test: Paciente NO puede crear consulta con tipo no permitido"""
        self.client.force_authenticate(user=self.django_user)
        
        data = {
            'idtipoconsulta': self.tipo_no_permitido.id,
            'motivo_consulta': 'Necesito cirugía de muela del juicio',
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no puede agendarse por web', response.data['error'])
    
    def test_limite_consultas_pendientes(self):
        """Test: Paciente no puede tener más de 3 consultas pendientes"""
        self.client.force_authenticate(user=self.django_user)
        
        # Crear 3 consultas pendientes manualmente
        for i in range(3):
            Consulta.objects.create(
                codpaciente=self.paciente,
                idtipoconsulta=self.tipo_permitido,
                estado='pendiente',
                motivo_consulta=f'Motivo de consulta número {i+1} con texto suficiente',
                agendado_por_web=True,
                fecha=date.today(),
                idhorario=self.horario,
                idestadoconsulta=self.estado_pendiente,
                empresa=self.empresa
            )
        
        # Intentar crear la 4ta
        data = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Cuarta consulta que debería fallar por límite',
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Límite de consultas pendientes', response.data['error'])
        self.assertIn('3', response.data['detalle'])
    
    def test_anti_spam_una_consulta_por_dia(self):
        """Test: Paciente no puede crear más de 1 consulta por día"""
        self.client.force_authenticate(user=self.django_user)
        
        # Crear 1 consulta hoy via API
        hoy = timezone.now().date()
        data_primera = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Primera consulta del día con texto suficiente para validar',
            'agendado_por_web': True,
            'fecha': hoy.strftime('%Y-%m-%d'),
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response1 = self.client.post('/api/consultas/', data_primera, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Intentar crear otra el mismo día
        data_segunda = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Segunda consulta del día que debería fallar por anti-spam',
            'agendado_por_web': True,
            'fecha': hoy.strftime('%Y-%m-%d'),
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response2 = self.client.post('/api/consultas/', data_segunda, format='json')
        
        # Debug: Ver qué retorna
        if response2.status_code != status.HTTP_429_TOO_MANY_REQUESTS:
            print(f"\nDEBUG Anti-spam:")
            print(f"Status: {response2.status_code}")
            print(f"Response: {response2.data}")
            # Verificar cuántas consultas hay en DB
            count = Consulta.objects.filter(
                codpaciente=self.paciente,
                agendado_por_web=True,
                empresa=self.empresa
            ).count()
            print(f"Consultas en DB: {count}")
        
        self.assertEqual(response2.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('Límite', response2.data.get('error', ''))
    
    def test_motivo_muy_corto(self):
        """Test: Motivo debe tener al menos 10 caracteres"""
        self.client.force_authenticate(user=self.django_user)
        
        data = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Corto',  # Solo 5 caracteres
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('muy corto', response.data['error'])
    
    def test_motivo_requerido(self):
        """Test: Motivo de consulta es requerido"""
        self.client.force_authenticate(user=self.django_user)
        
        data = {
            'idtipoconsulta': self.tipo_permitido.id,
            'agendado_por_web': True,
            'fecha': '2025-11-10',
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
            # No incluimos motivo_consulta
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('motivo', response.data['error'].lower())
    
    def test_usuario_no_autenticado(self):
        """Test: Usuario no autenticado no puede agendar"""
        # No autenticar
        
        data = {
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Dolor de muela con texto suficiente para validación',
            'agendado_por_web': True
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_horarios_preferidos_validos(self):
        """Test: Horarios preferidos válidos son aceptados"""
        self.client.force_authenticate(user=self.django_user)
        
        horarios = ['mañana', 'tarde', 'noche', 'cualquiera']
        
        for horario in horarios:
            with self.subTest(horario=horario):
                data = {
                    'idtipoconsulta': self.tipo_permitido.id,
                    'motivo_consulta': f'Consulta para horario {horario} con texto suficiente',
                    'fecha_preferida': '2025-11-10',
                    'horario_preferido': horario,
                    'agendado_por_web': True,
                    'fecha': '2025-11-10',
                    'idhorario': self.horario.id,
                    'idestadoconsulta': self.estado_pendiente.id
                }
                
                response = self.client.post('/api/consultas/', data, format='json')
                
                if response.status_code != status.HTTP_201_CREATED:
                    print(f"Error para horario '{horario}': {response.data}")
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertEqual(response.data['horario_preferido'], horario)
    
    def test_consulta_desde_staff_no_requiere_validaciones(self):
        """Test: Consultas creadas por staff (no web) no tienen límites"""
        self.client.force_authenticate(user=self.django_user)
        
        # Crear 3 consultas pendientes
        for i in range(3):
            Consulta.objects.create(
                codpaciente=self.paciente,
                idtipoconsulta=self.tipo_permitido,
                estado='pendiente',
                motivo_consulta=f'Consulta pendiente {i+1}',
                agendado_por_web=True,
                fecha=date.today(),
                idhorario=self.horario,
                idestadoconsulta=self.estado_pendiente,
                empresa=self.empresa
            )
        
        # Staff puede crear otra sin límite (agendado_por_web=False)
        data = {
            'codpaciente': self.paciente.codusuario.codigo,
            'idtipoconsulta': self.tipo_permitido.id,
            'motivo_consulta': 'Consulta creada por staff sin límite de validaciones',
            'agendado_por_web': False,  # KEY: No es web
            'fecha': date.today().strftime('%Y-%m-%d'),
            'idhorario': self.horario.id,
            'idestadoconsulta': self.estado_pendiente.id
        }
        
        response = self.client.post('/api/consultas/', data, format='json')
        
        # Debería funcionar porque agendado_por_web=False
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ConfiguracionTiposConsultaTestCase(BaseAgendamientoWebTest):
    """Tests para verificar configuración de tipos de consulta"""
    
    def setUp(self):
        # Crear canales de notificación primero
        self._crear_canales_notificacion()
        
        self.empresa = Empresa.objects.create(
            nombre='Clínica Test',
            subdomain='test',
            activo=True
        )
    
    def test_tipo_consulta_tiene_campos_web(self):
        """Test: Modelo TipoDeConsulta tiene campos de agendamiento web"""
        tipo = Tipodeconsulta.objects.create(
            nombreconsulta='Test',
            empresa=self.empresa,
            permite_agendamiento_web=True,
            es_urgencia=False,
            requiere_aprobacion=False,
            duracion_estimada=30
        )
        
        self.assertTrue(hasattr(tipo, 'permite_agendamiento_web'))
        self.assertTrue(hasattr(tipo, 'es_urgencia'))
        self.assertTrue(hasattr(tipo, 'requiere_aprobacion'))
        self.assertTrue(hasattr(tipo, 'duracion_estimada'))
        
        self.assertTrue(tipo.permite_agendamiento_web)
        self.assertFalse(tipo.es_urgencia)
        self.assertEqual(tipo.duracion_estimada, 30)
    
    def test_consulta_tiene_campos_web(self):
        """Test: Modelo Consulta tiene campos de agendamiento web"""
        # Solo verificamos que los campos existan
        tipo = Tipodeconsulta.objects.create(
            nombreconsulta='Test',
            empresa=self.empresa
        )
        
        tipo_usuario = Tipodeusuario.objects.create(
            rol='Paciente', 
            empresa=self.empresa
        )
        
        paciente_usuario = Usuario.objects.create(
            nombre='Test',
            apellido='User',
            correoelectronico='test@test.com',
            idtipousuario=tipo_usuario,
            empresa=self.empresa
        )
        
        # El signal crea el paciente automáticamente
        paciente = Paciente.objects.get(codusuario=paciente_usuario)
        
        horario = Horario.objects.create(
            hora=time(10, 0),
            empresa=self.empresa
        )
        
        estado = Estadodeconsulta.objects.create(
            estado='Test',
            empresa=self.empresa
        )
        
        consulta = Consulta.objects.create(
            codpaciente=paciente,
            idtipoconsulta=tipo,
            fecha=date.today(),
            idhorario=horario,
            idestadoconsulta=estado,
            agendado_por_web=True,
            prioridad='normal',
            horario_preferido='tarde',
            empresa=self.empresa
        )
        
        # Verificar que los campos existen y tienen los valores correctos
        self.assertTrue(hasattr(consulta, 'agendado_por_web'))
        self.assertTrue(hasattr(consulta, 'prioridad'))
        self.assertTrue(hasattr(consulta, 'horario_preferido'))
        self.assertTrue(hasattr(consulta, 'fecha_preferida'))
        self.assertTrue(hasattr(consulta, 'created_at'))  # ✅ Nuevo campo
        self.assertTrue(hasattr(consulta, 'updated_at'))  # ✅ Nuevo campo
        
        self.assertTrue(consulta.agendado_por_web)
        self.assertEqual(consulta.prioridad, 'normal')
        self.assertEqual(consulta.horario_preferido, 'tarde')
