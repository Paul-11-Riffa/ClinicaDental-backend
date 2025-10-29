"""
TEST PASO 1: Verificar nueva estructura del flujo clínico
==========================================================

Este test verifica que:
1. Los modelos se actualizaron correctamente
2. Los nuevos campos existen
3. Las relaciones funcionan
4. Los datos existentes NO se afectaron

Ejecutar: python manage.py test api.tests_flujo_paso1 --verbosity=2
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal

from api.models import (
    Empresa, Usuario, Tipodeusuario,
    Paciente, Odontologo, Consulta, Tipodeconsulta, Estadodeconsulta,
    Plandetratamiento, Itemplandetratamiento, Estado, Servicio,
    PagoEnLinea, Horario
)


class FlujoPaso1ModelsTestCase(TestCase):
    """Test de modelos actualizados - Paso 1"""
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Test Clínica",
            subdomain="test"
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            rol="Paciente",
            descripcion="Tipo de usuario paciente",
            empresa=self.empresa
        )
        
        # Crear tipo de usuario para odontólogo
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol="Odontologo",
            descripcion="Tipo de usuario odontólogo",
            empresa=self.empresa
        )
        
        # Crear usuario (el signal creará automáticamente el Paciente)
        self.usuario = Usuario.objects.create(
            nombre="Juan",
            apellido="Pérez",
            correoelectronico="juan@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Obtener el paciente creado automáticamente por el signal
        self.paciente = Paciente.objects.get(codusuario=self.usuario)
        
        # Actualizar datos del paciente si es necesario
        self.paciente.carnetidentidad = "123456"
        self.paciente.save()
        
        # Crear odontólogo (el signal lo creará automáticamente)
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos",
            apellido="Gómez",
            correoelectronico="carlos@test.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        
        # Obtener el odontólogo creado automáticamente por el signal
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        # Actualizar datos del odontólogo si es necesario
        self.odontologo.especialidad = "Ortodoncia"
        self.odontologo.nromatricula = "12345"
        self.odontologo.save()
        
        # Crear estados y tipos necesarios
        self.estado = Estado.objects.create(
            estado="Activo",
            empresa=self.empresa
        )
        
        self.tipo_consulta = Tipodeconsulta.objects.create(
            nombreconsulta="Diagnóstico",
            empresa=self.empresa
        )
        
        self.estado_consulta = Estadodeconsulta.objects.create(
            estado="Completada",
            empresa=self.empresa
        )
        
        self.horario = Horario.objects.create(
            hora="10:00:00"
        )
        
        # Crear servicio
        self.servicio = Servicio.objects.create(
            nombre="Limpieza Dental",
            descripcion="Limpieza completa",
            costobase=Decimal('100.00'),
            empresa=self.empresa
        )
    
    def test_consulta_tiene_nuevos_campos(self):
        """Verifica que Consulta tenga los nuevos campos"""
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            # Nuevos campos
            costo_consulta=Decimal('150.00'),
            requiere_pago=True
        )
        
        # Verificar que se creó correctamente
        self.assertIsNotNone(consulta.id)
        self.assertEqual(consulta.costo_consulta, Decimal('150.00'))
        self.assertTrue(consulta.requiere_pago)
        self.assertIsNone(consulta.plan_tratamiento)
        self.assertIsNone(consulta.pago_consulta)
        
        print("   ✓ Consulta: nuevos campos funcionan correctamente")
    
    def test_plandetratamiento_tiene_nuevos_campos(self):
        """Verifica que Plandetratamiento tenga los nuevos campos"""
        # Crear consulta de diagnóstico
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            costo_consulta=Decimal('150.00'),
            requiere_pago=True
        )
        
        # Crear plan vinculado a consulta
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            montototal=Decimal('1000.00'),
            empresa=self.empresa,
            # Nuevos campos
            consulta_diagnostico=consulta,
            estado_tratamiento='Propuesto'
        )
        
        # Verificar
        self.assertIsNotNone(plan.id)
        self.assertEqual(plan.consulta_diagnostico.id, consulta.id)
        self.assertEqual(plan.estado_tratamiento, 'Propuesto')
        self.assertIsNone(plan.fecha_inicio_ejecucion)
        self.assertIsNone(plan.fecha_finalizacion)
        
        # Verificar relación inversa
        self.assertEqual(consulta.planes_generados.count(), 1)
        self.assertEqual(consulta.planes_generados.first().id, plan.id)
        
        print("   ✓ Plandetratamiento: nuevos campos y relaciones funcionan")
    
    def test_itemplandetratamiento_tiene_nuevos_campos(self):
        """Verifica que Itemplandetratamiento tenga los nuevos campos"""
        # Crear plan
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            montototal=Decimal('100.00'),
            empresa=self.empresa,
            estado_tratamiento='Aceptado'
        )
        
        # Crear item
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('100.00'),
            empresa=self.empresa,
            estado_item='Pendiente',
            # Nuevos campos
            orden_ejecucion=1
        )
        
        # Verificar
        self.assertIsNotNone(item.id)
        self.assertEqual(item.orden_ejecucion, 1)
        self.assertIsNone(item.consulta_ejecucion)
        self.assertIsNone(item.fecha_ejecucion)
        self.assertIsNone(item.odontologo_ejecutor)
        self.assertIsNone(item.notas_ejecucion)
        
        print("   ✓ Itemplandetratamiento: nuevos campos funcionan")
    
    def test_flujo_completo_consulta_plan_item(self):
        """Test del flujo completo: Consulta → Plan → Item → Consulta Ejecución"""
        # 1. Consulta de diagnóstico
        consulta_diagnostico = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            costo_consulta=Decimal('150.00'),
            requiere_pago=True
        )
        
        # 2. Plan originado por la consulta
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            montototal=Decimal('500.00'),
            empresa=self.empresa,
            consulta_diagnostico=consulta_diagnostico,
            estado_tratamiento='Aceptado',
            fecha_inicio_ejecucion=timezone.now()
        )
        
        # 3. Items del plan
        item1 = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('100.00'),
            empresa=self.empresa,
            estado_item='Pagado',
            orden_ejecucion=1
        )
        
        item2 = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('100.00'),
            empresa=self.empresa,
            estado_item='Pagado',
            orden_ejecucion=2
        )
        
        # 4. Consulta de ejecución
        consulta_ejecucion = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            plan_tratamiento=plan,  # Vinculado al plan
            costo_consulta=Decimal('0.00'),
            requiere_pago=False
        )
        
        # 5. Marcar item como ejecutado
        item1.consulta_ejecucion = consulta_ejecucion
        item1.fecha_ejecucion = timezone.now()
        item1.odontologo_ejecutor = self.odontologo
        item1.estado_item = 'Completado'
        item1.notas_ejecucion = "Limpieza realizada correctamente"
        item1.save()
        
        # Verificar todo el flujo
        self.assertEqual(consulta_diagnostico.planes_generados.count(), 1)
        self.assertEqual(plan.consulta_diagnostico.id, consulta_diagnostico.id)
        self.assertEqual(plan.itemplandetratamiento_set.count(), 2)
        self.assertEqual(consulta_ejecucion.plan_tratamiento.id, plan.id)
        self.assertEqual(consulta_ejecucion.items_ejecutados.count(), 1)
        self.assertEqual(item1.consulta_ejecucion.id, consulta_ejecucion.id)
        self.assertEqual(item1.odontologo_ejecutor.codusuario.nombre, "Dr. Carlos")
        
        print("   ✓ Flujo completo: Consulta → Plan → Item → Ejecución OK")
    
    def test_datos_existentes_no_afectados(self):
        """Verifica que los datos existentes sigan funcionando"""
        # Crear datos al estilo antiguo (sin nuevos campos)
        plan_antiguo = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            montototal=Decimal('200.00'),
            empresa=self.empresa
            # NO usamos nuevos campos
        )
        
        item_antiguo = Itemplandetratamiento.objects.create(
            idplantratamiento=plan_antiguo,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('200.00'),
            empresa=self.empresa,
            estado_item='Activo'
            # NO usamos nuevos campos
        )
        
        # Verificar que se crearon correctamente
        self.assertIsNotNone(plan_antiguo.id)
        self.assertIsNotNone(item_antiguo.id)
        
        # Verificar valores por defecto de nuevos campos
        self.assertIsNone(plan_antiguo.consulta_diagnostico)
        self.assertEqual(plan_antiguo.estado_tratamiento, 'Propuesto')  # Default
        self.assertIsNone(item_antiguo.consulta_ejecucion)
        self.assertEqual(item_antiguo.orden_ejecucion, 1)  # Default
        
        print("   ✓ Datos antiguos: Compatibilidad retroactiva OK")


def print_test_summary():
    """Resumen de lo que se probó"""
    print("\n" + "="*70)
    print("RESUMEN DEL TEST - PASO 1")
    print("="*70)
    print("\n✅ Tests completados:")
    print("   1. Consulta tiene los 4 nuevos campos")
    print("   2. Plandetratamiento tiene los 4 nuevos campos")
    print("   3. Itemplandetratamiento tiene los 5 nuevos campos")
    print("   4. Flujo completo Consulta → Plan → Item → Ejecución funciona")
    print("   5. Datos existentes NO se afectaron (retrocompatibilidad)")
    print("\n" + "="*70 + "\n")


# Ejecutar resumen al final de los tests
import atexit
atexit.register(print_test_summary)
