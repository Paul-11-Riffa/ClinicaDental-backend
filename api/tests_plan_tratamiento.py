# api/tests_plan_tratamiento.py
"""
Tests unitarios para la funcionalidad de gestión de planes de tratamiento.
SP3-T001: Crear plan de tratamiento (Web)
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Empresa,
    Usuario,
    Tipodeusuario,
    Paciente,
    Odontologo,
    Servicio,
    Piezadental,
    Estado,
    Plandetratamiento,
    Itemplandetratamiento,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class PlanTratamientoTestCase(TestCase):
    """Tests para la gestión de planes de tratamiento."""
    
    def setUp(self):
        """Configuración inicial para todos los tests."""
        # Crear empresa (tenant)
        self.empresa = Empresa.objects.create(
            nombre="Clínica Norte",
            subdomain="norte",
            activo=True
        )
        
        # Crear tipos de usuario
        self.tipo_admin = Tipodeusuario.objects.create(
            rol="Administrador",
            descripcion="Administrador del sistema",
            empresa=self.empresa
        )
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol="Odontólogo",
            descripcion="Profesional dental",
            empresa=self.empresa
        )
        self.tipo_paciente = Tipodeusuario.objects.create(
            rol="Paciente",
            descripcion="Paciente de la clínica",
            empresa=self.empresa
        )
        
        # Crear usuarios Django
        self.user_admin = User.objects.create_user(
            username="admin@norte.com",
            email="admin@norte.com",
            password="admin123"
        )
        self.user_odontologo = User.objects.create_user(
            username="dr.lopez@norte.com",
            email="dr.lopez@norte.com",
            password="doctor123"
        )
        self.user_paciente = User.objects.create_user(
            username="paciente@norte.com",
            email="paciente@norte.com",
            password="paciente123"
        )
        
        # Crear usuarios de negocio
        self.usuario_admin = Usuario.objects.create(
            nombre="Admin",
            apellido="Sistema",
            correoelectronico="admin@norte.com",
            idtipousuario=self.tipo_admin,
            empresa=self.empresa
        )
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Juan",
            apellido="López",
            correoelectronico="dr.lopez@norte.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        self.usuario_paciente = Usuario.objects.create(
            nombre="María",
            apellido="González",
            correoelectronico="paciente@norte.com",
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        
        # Crear odontólogo
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario_odontologo,
            especialidad="Odontología General",
            nromatricula="12345",
            empresa=self.empresa
        )
        
        # Crear paciente (eliminar primero si existe por alguna razón)
        Paciente.objects.filter(codusuario=self.usuario_paciente).delete()
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            carnetidentidad="1234567",
            fechanacimiento=date(1990, 5, 15),
            empresa=self.empresa
        )
        
        # Crear servicios
        self.servicio_limpieza = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza profunda con ultrasonido",
            costobase=Decimal("150.00"),
            duracion=45,
            activo=True,
            empresa=self.empresa
        )
        self.servicio_endodoncia = Servicio.objects.create(
            nombre="Endodoncia",
            descripcion="Tratamiento de conducto",
            costobase=Decimal("800.00"),
            duracion=90,
            activo=True,
            empresa=self.empresa
        )
        
        # Crear piezas dentales
        self.pieza_molar6 = Piezadental.objects.create(
            nombrepieza="Molar 6",
            grupo="Molares",
            empresa=self.empresa
        )
        
        # Crear estado
        self.estado = Estado.objects.create(
            estado="Planificado",
            empresa=self.empresa
        )
        
        # Cliente API
        self.client = APIClient()
    
    # ========================================================================
    # TESTS DE CREACIÓN DE PLAN
    # ========================================================================
    
    def test_crear_plan_exitoso(self):
        """Test: Crear un plan de tratamiento básico."""
        self.client.force_authenticate(user=self.user_odontologo)
        
        data = {
            "codpaciente": self.paciente.codusuario.codigo,
            "cododontologo": self.odontologo.codusuario.codigo,
            "fechaplan": str(date.today()),
            "notas_plan": "Plan inicial de tratamiento",
            "descuento": "0.00",
        }
        
        # Simular tenant
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        response = self.client.post('/api/planes-tratamiento/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar plan creado
        plan = Plandetratamiento.objects.get(id=response.data['id'])
        self.assertEqual(plan.estado_plan, Plandetratamiento.ESTADO_PLAN_BORRADOR)
        self.assertTrue(plan.puede_editarse())
        self.assertEqual(plan.empresa, self.empresa)
    
    def test_crear_plan_con_items_iniciales(self):
        """Test: Crear plan con ítems desde el inicio."""
        self.client.force_authenticate(user=self.user_odontologo)
        
        data = {
            "codpaciente": self.paciente.codusuario.codigo,
            "cododontologo": self.odontologo.codusuario.codigo,
            "fechaplan": str(date.today()),
            "notas_plan": "Plan con items",
            "items_iniciales": [
                {
                    "idservicio": self.servicio_limpieza.id,
                    "idestado": self.estado.id,
                    "costofinal": "150.00",
                    "notas_item": "Limpieza de rutina",
                },
                {
                    "idservicio": self.servicio_endodoncia.id,
                    "idpiezadental": self.pieza_molar6.id,
                    "idestado": self.estado.id,
                    "costofinal": "800.00",
                    "notas_item": "Endodoncia en molar 6",
                }
            ]
        }
        
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        response = self.client.post('/api/planes-tratamiento/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        plan = Plandetratamiento.objects.get(id=response.data['id'])
        self.assertEqual(plan.itemplandetratamiento_set.count(), 2)
        self.assertEqual(plan.subtotal_calculado, Decimal("950.00"))
        self.assertEqual(plan.montototal, Decimal("950.00"))
    
    def test_crear_plan_sin_autenticacion(self):
        """Test: Intentar crear plan sin autenticación debe fallar."""
        data = {
            "codpaciente": self.paciente.codusuario.codigo,
            "cododontologo": self.odontologo.codusuario.codigo,
            "fechaplan": str(date.today()),
        }
        
        response = self.client.post('/api/planes-tratamiento/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    # ========================================================================
    # TESTS DE AGREGAR ITEMS
    # ========================================================================
    
    def test_agregar_item_a_plan_borrador(self):
        """Test: Agregar un ítem a un plan en borrador."""
        # Crear plan
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
        )
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {
            "idservicio": self.servicio_limpieza.id,
            "idestado": self.estado.id,
            "costofinal": "150.00",
            "notas_item": "Limpieza dental",
        }
        
        response = self.client.post(
            f'/api/planes-tratamiento/{plan.id}/items/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(plan.itemplandetratamiento_set.count(), 1)
        
        # Verificar totales recalculados
        plan.refresh_from_db()
        self.assertEqual(plan.subtotal_calculado, Decimal("150.00"))
    
    def test_agregar_item_a_plan_aprobado_falla(self):
        """Test: No se puede agregar ítem a plan aprobado."""
        # Crear plan aprobado
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
            es_editable=False,
        )
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {
            "idservicio": self.servicio_limpieza.id,
            "idestado": self.estado.id,
            "costofinal": "150.00",
        }
        
        response = self.client.post(
            f'/api/planes-tratamiento/{plan.id}/items/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('no editable', response.data['detalle'].lower())
    
    # ========================================================================
    # TESTS DE EDITAR ITEMS
    # ========================================================================
    
    def test_editar_item_de_plan_borrador(self):
        """Test: Editar un ítem de un plan en borrador."""
        # Crear plan con ítem
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
        )
        
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            empresa=self.empresa,
        )
        
        plan.calcular_totales()
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        # Editar costo
        data = {
            "costofinal": "180.00",
            "notas_item": "Limpieza con descuento",
        }
        
        response = self.client.patch(
            f'/api/planes-tratamiento/{plan.id}/items/{item.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        item.refresh_from_db()
        self.assertEqual(item.costofinal, Decimal("180.00"))
        self.assertEqual(item.notas_item, "Limpieza con descuento")
        
        # Verificar totales recalculados
        plan.refresh_from_db()
        self.assertEqual(plan.subtotal_calculado, Decimal("180.00"))
    
    # ========================================================================
    # TESTS DE ELIMINAR ITEMS
    # ========================================================================
    
    def test_eliminar_item_de_plan_borrador(self):
        """Test: Eliminar un ítem de un plan en borrador."""
        # Crear plan con ítem
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
        )
        
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            empresa=self.empresa,
        )
        
        plan.calcular_totales()
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        response = self.client.delete(
            f'/api/planes-tratamiento/{plan.id}/items/{item.id}/eliminar/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(plan.itemplandetratamiento_set.count(), 0)
        
        # Verificar totales recalculados a cero
        plan.refresh_from_db()
        self.assertEqual(plan.subtotal_calculado, Decimal("0.00"))
    
    # ========================================================================
    # TESTS DE APROBAR PLAN
    # ========================================================================
    
    def test_aprobar_plan_exitoso(self):
        """Test: Aprobar un plan con ítems."""
        # Crear plan con ítem
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
        )
        
        Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            estado_item='Activo',
            empresa=self.empresa,
        )
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {"confirmar": True}
        
        response = self.client.post(
            f'/api/planes-tratamiento/{plan.id}/aprobar/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        plan.refresh_from_db()
        self.assertEqual(plan.estado_plan, Plandetratamiento.ESTADO_PLAN_APROBADO)
        self.assertFalse(plan.puede_editarse())
        self.assertIsNotNone(plan.fecha_aprobacion)
        self.assertEqual(plan.usuario_aprueba, self.usuario_odontologo)
    
    def test_aprobar_plan_sin_items_falla(self):
        """Test: No se puede aprobar plan sin ítems activos."""
        # Crear plan SIN ítems
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_BORRADOR,
        )
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {"confirmar": True}
        
        response = self.client.post(
            f'/api/planes-tratamiento/{plan.id}/aprobar/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('al menos un ítem', str(response.data).lower())
    
    def test_aprobar_plan_ya_aprobado_falla(self):
        """Test: No se puede aprobar un plan ya aprobado."""
        # Crear plan ya aprobado
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
        )
        
        self.client.force_authenticate(user=self.user_odontologo)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {"confirmar": True}
        
        response = self.client.post(
            f'/api/planes-tratamiento/{plan.id}/aprobar/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # ========================================================================
    # TESTS DE CÁLCULO DE TOTALES
    # ========================================================================
    
    def test_calcular_totales_con_descuento(self):
        """Test: Calcular totales con descuento aplicado."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            descuento=Decimal("50.00"),  # Descuento de $50
        )
        
        Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            estado_item='Activo',
            empresa=self.empresa,
        )
        
        Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_endodoncia,
            idestado=self.estado,
            costofinal=Decimal("800.00"),
            estado_item='Activo',
            empresa=self.empresa,
        )
        
        resultado = plan.calcular_totales()
        
        self.assertEqual(resultado['subtotal'], 950.00)
        self.assertEqual(resultado['descuento'], 50.00)
        self.assertEqual(resultado['total'], 900.00)
        self.assertEqual(plan.montototal, Decimal("900.00"))
    
    def test_items_cancelados_no_impactan_total(self):
        """Test: Items cancelados no se cuentan en el total."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
        )
        
        # Item activo
        Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            estado_item='Activo',
            empresa=self.empresa,
        )
        
        # Item cancelado
        Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_endodoncia,
            idestado=self.estado,
            costofinal=Decimal("800.00"),
            estado_item='Cancelado',  # Este NO debe contar
            empresa=self.empresa,
        )
        
        resultado = plan.calcular_totales()
        
        # Solo debe contar el item activo
        self.assertEqual(resultado['subtotal'], 150.00)
        self.assertEqual(resultado['total'], 150.00)
        self.assertEqual(resultado['items_activos'], 1)
    
    # ========================================================================
    # TESTS DE ACTIVAR/CANCELAR ITEMS
    # ========================================================================
    
    def test_cancelar_item_recalcula_totales(self):
        """Test: Cancelar un ítem recalcula automáticamente los totales."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
        )
        
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio_limpieza,
            idestado=self.estado,
            costofinal=Decimal("150.00"),
            estado_item='Activo',
            empresa=self.empresa,
        )
        
        plan.calcular_totales()
        self.assertEqual(plan.montototal, Decimal("150.00"))
        
        # Cancelar item
        item.cancelar()
        
        plan.refresh_from_db()
        self.assertEqual(plan.montototal, Decimal("0.00"))
    
    # ========================================================================
    # TESTS DE PERMISOS
    # ========================================================================
    
    def test_paciente_puede_ver_sus_planes(self):
        """Test: Paciente puede ver sus propios planes."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
        )
        
        self.client.force_authenticate(user=self.user_paciente)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        response = self.client.get(f'/api/planes-tratamiento/{plan.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_paciente_no_puede_crear_planes(self):
        """Test: Paciente no puede crear planes (solo odontólogos)."""
        self.client.force_authenticate(user=self.user_paciente)
        self.client.credentials(HTTP_X_TENANT_SUBDOMAIN="norte")
        
        data = {
            "codpaciente": self.paciente.codusuario.codigo,
            "cododontologo": self.odontologo.codusuario.codigo,
            "fechaplan": str(date.today()),
        }
        
        response = self.client.post('/api/planes-tratamiento/', data, format='json')
        
        # Puede que falle por falta de permisos o validación
        # (depende de la implementación de permisos personalizados)
        # Por ahora verificamos que no se cree exitosamente
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


# ============================================================================
# TESTS DE MODELOS
# ============================================================================

class PlanTratamientoModelTestCase(TestCase):
    """Tests unitarios para los modelos de Plan de Tratamiento."""
    
    def setUp(self):
        """Configuración inicial."""
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
        
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol="Odontólogo",
            empresa=self.empresa
        )
        self.tipo_paciente = Tipodeusuario.objects.create(
            rol="Paciente",
            empresa=self.empresa
        )
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Test",
            apellido="Doctor",
            correoelectronico="doctor@test.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        self.usuario_paciente = Usuario.objects.create(
            nombre="Test",
            apellido="Paciente",
            correoelectronico="paciente@test.com",
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario_odontologo,
            empresa=self.empresa
        )
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            empresa=self.empresa
        )
        
        self.estado = Estado.objects.create(
            estado="Test",
            empresa=self.empresa
        )
    
    def test_plan_es_borrador_por_defecto(self):
        """Test: Plan se crea como borrador por defecto."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
        )
        
        self.assertTrue(plan.es_borrador())
        self.assertTrue(plan.puede_editarse())
    
    def test_aprobar_plan_cambia_estado(self):
        """Test: Aprobar plan cambia su estado a aprobado."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
        )
        
        plan.aprobar_plan(self.usuario_odontologo)
        
        self.assertTrue(plan.es_aprobado())
        self.assertFalse(plan.puede_editarse())
    
    def test_no_puede_aprobar_plan_ya_aprobado(self):
        """Test: No se puede aprobar un plan ya aprobado."""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            empresa=self.empresa,
            estado_plan=Plandetratamiento.ESTADO_PLAN_APROBADO,
        )
        
        with self.assertRaises(ValueError):
            plan.aprobar_plan(self.usuario_odontologo)
