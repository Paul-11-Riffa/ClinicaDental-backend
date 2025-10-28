"""
Tests para Sesiones de Tratamiento (SP3-T008)
Verificación completa de funcionalidad de registro de procedimientos clínicos
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from datetime import date, time, timedelta

from .models import (
    Empresa, Usuario, Tipodeusuario, Paciente, Odontologo, Recepcionista,
    Consulta, Horario, Tipodeconsulta, Estadodeconsulta,
    Servicio, Plandetratamiento, Itemplandetratamiento, Estado,
    SesionTratamiento, Historialclinico
)


class SesionTratamientoModelTestCase(TestCase):
    """Tests del modelo SesionTratamiento"""
    
    def setUp(self):
        """Preparar datos de prueba"""
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
        
        # Crear tipo de usuario
        self.tipo_usuario = Tipodeusuario.objects.create(
            rol="Odontologo",
            empresa=self.empresa
        )
        
        # Crear usuario odontólogo
        self.usuario = Usuario.objects.create(
            nombre="Dr. Test",
            apellido="Prueba",
            correoelectronico="test@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Crear usuario paciente
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan",
            apellido="Perez",
            correoelectronico="juan@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        
        # Crear paciente
        self.paciente = Paciente.objects.create(
            codusuario=self.usuario_paciente,
            carnetidentidad="12345678",
            fechanacimiento=date(1990, 1, 1),
            empresa=self.empresa
        )
        
        # Crear odontólogo
        self.odontologo = Odontologo.objects.create(
            codusuario=self.usuario,
            especialidad="General",
            nromatricula="MAT-001",
            empresa=self.empresa
        )
        
        # Crear recepcionista
        self.usuario_recep = Usuario.objects.create(
            nombre="Maria",
            apellido="Lopez",
            correoelectronico="maria@test.com",
            idtipousuario=self.tipo_usuario,
            empresa=self.empresa
        )
        self.recepcionista = Recepcionista.objects.create(
            codusuario=self.usuario_recep,
            empresa=self.empresa
        )
        
        # Crear horario
        self.horario = Horario.objects.create(
            hora=time(10, 0),
            empresa=self.empresa
        )
        
        # Crear tipo de consulta
        self.tipo_consulta = Tipodeconsulta.objects.create(
            nombreconsulta="Limpieza",
            empresa=self.empresa
        )
        
        # Crear estado de consulta
        self.estado_consulta = Estadodeconsulta.objects.create(
            estado="Programada",
            empresa=self.empresa
        )
        
        # Crear consulta
        self.consulta = Consulta.objects.create(
            fecha=date.today(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa
        )
        
        # Crear servicio
        self.servicio = Servicio.objects.create(
            nombre="Endodoncia",
            descripcion="Tratamiento de conducto",
            costobase=Decimal("500.00"),
            duracion=60,
            empresa=self.empresa
        )
        
        # Crear estado
        self.estado = Estado.objects.create(
            estado="Activo",
            empresa=self.empresa
        )
        
        # Crear plan de tratamiento aprobado
        self.plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=date.today(),
            montototal=Decimal("500.00"),
            empresa=self.empresa,
            estado_plan='Aprobado'
        )
        
        # Crear ítem del plan
        self.item_plan = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal("500.00"),
            empresa=self.empresa,
            estado_item='Activo'
        )
    
    def test_crear_sesion_basica(self):
        """Test: Crear sesión de tratamiento básica"""
        sesion = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            hora_inicio=time(10, 0),
            duracion_minutos=45,
            progreso_actual=Decimal("30.00"),
            acciones_realizadas="Se realizó la primera parte del tratamiento",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        self.assertIsNotNone(sesion.id)
        self.assertEqual(sesion.progreso_anterior, Decimal("0.00"))
        self.assertEqual(sesion.progreso_actual, Decimal("30.00"))
        self.assertEqual(sesion.get_incremento_progreso(), 30.0)
        print("✅ Test crear_sesion_basica: PASADO")
    
    def test_prevenir_sesiones_duplicadas(self):
        """Test: No permitir sesiones duplicadas para mismo ítem y consulta"""
        # Crear primera sesión
        SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=45,
            progreso_actual=Decimal("30.00"),
            acciones_realizadas="Primera sesión",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Intentar crear segunda sesión duplicada (debe fallar por UniqueConstraint)
        with self.assertRaises(IntegrityError):
            SesionTratamiento.objects.create(
                item_plan=self.item_plan,
                consulta=self.consulta,
                fecha_sesion=date.today(),
                duracion_minutos=30,
                progreso_actual=Decimal("50.00"),
                acciones_realizadas="Intento duplicado",
                usuario_registro=self.usuario,
                empresa=self.empresa
            )
        
        print("✅ Test prevenir_sesiones_duplicadas: PASADO")
    
    def test_progreso_no_retrocede(self):
        """Test: El progreso no puede ser menor al anterior"""
        # Primera sesión con 30% de progreso
        SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=45,
            progreso_actual=Decimal("30.00"),
            acciones_realizadas="Primera sesión",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Crear segunda consulta
        consulta2 = Consulta.objects.create(
            fecha=date.today() + timedelta(days=7),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa
        )
        
        # Intentar crear sesión con progreso menor (20% < 30%)
        with self.assertRaises(ValidationError):
            sesion2 = SesionTratamiento(
                item_plan=self.item_plan,
                consulta=consulta2,
                fecha_sesion=date.today() + timedelta(days=7),
                duracion_minutos=30,
                progreso_actual=Decimal("20.00"),  # Retroceso!
                acciones_realizadas="Intento retroceso",
                usuario_registro=self.usuario,
                empresa=self.empresa
            )
            sesion2.save()
        
        print("✅ Test progreso_no_retrocede: PASADO")
    
    def test_auto_completar_item_al_100(self):
        """Test: Ítem se completa automáticamente al llegar a 100%"""
        sesion = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=60,
            progreso_actual=Decimal("100.00"),
            acciones_realizadas="Tratamiento completado",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Refrescar el ítem desde la DB
        self.item_plan.refresh_from_db()
        
        self.assertEqual(self.item_plan.estado_item, 'Completado')
        print("✅ Test auto_completar_item_al_100: PASADO")
    
    def test_no_sesiones_en_items_cancelados(self):
        """Test: No se pueden crear sesiones en ítems cancelados"""
        # Cancelar el ítem
        self.item_plan.estado_item = 'Cancelado'
        self.item_plan.save()
        
        # Intentar crear sesión
        with self.assertRaises(ValidationError):
            sesion = SesionTratamiento(
                item_plan=self.item_plan,
                consulta=self.consulta,
                fecha_sesion=date.today(),
                duracion_minutos=30,
                progreso_actual=Decimal("50.00"),
                acciones_realizadas="Intento en item cancelado",
                usuario_registro=self.usuario,
                empresa=self.empresa
            )
            sesion.save()
        
        print("✅ Test no_sesiones_en_items_cancelados: PASADO")
    
    def test_multiples_sesiones_progresivas(self):
        """Test: Crear múltiples sesiones con progreso creciente"""
        # Primera sesión: 30%
        sesion1 = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=45,
            progreso_actual=Decimal("30.00"),
            acciones_realizadas="Primera sesión",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Segunda sesión: 60%
        consulta2 = Consulta.objects.create(
            fecha=date.today() + timedelta(days=7),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa
        )
        sesion2 = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=consulta2,
            fecha_sesion=date.today() + timedelta(days=7),
            duracion_minutos=45,
            progreso_actual=Decimal("60.00"),
            acciones_realizadas="Segunda sesión",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Tercera sesión: 100%
        consulta3 = Consulta.objects.create(
            fecha=date.today() + timedelta(days=14),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa
        )
        sesion3 = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=consulta3,
            fecha_sesion=date.today() + timedelta(days=14),
            duracion_minutos=30,
            progreso_actual=Decimal("100.00"),
            acciones_realizadas="Sesión final",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Verificaciones
        self.assertEqual(sesion1.progreso_anterior, Decimal("0.00"))
        self.assertEqual(sesion2.progreso_anterior, Decimal("30.00"))
        self.assertEqual(sesion3.progreso_anterior, Decimal("60.00"))
        
        # Verificar que el ítem está completado
        self.item_plan.refresh_from_db()
        self.assertEqual(self.item_plan.estado_item, 'Completado')
        
        print("✅ Test multiples_sesiones_progresivas: PASADO")
    
    def test_recalcular_progreso_plan(self):
        """Test: Recalcular progreso general del plan con múltiples ítems"""
        # Crear segundo servicio e ítem
        servicio2 = Servicio.objects.create(
            nombre="Limpieza",
            costobase=Decimal("100.00"),
            duracion=30,
            empresa=self.empresa
        )
        item_plan2 = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=servicio2,
            idestado=self.estado,
            costofinal=Decimal("100.00"),
            empresa=self.empresa,
            estado_item='Activo'
        )
        
        # Crear sesiones
        sesion1 = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=45,
            progreso_actual=Decimal("50.00"),
            acciones_realizadas="Sesión item 1",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        consulta2 = Consulta.objects.create(
            fecha=date.today(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa
        )
        sesion2 = SesionTratamiento.objects.create(
            item_plan=item_plan2,
            consulta=consulta2,
            fecha_sesion=date.today(),
            duracion_minutos=30,
            progreso_actual=Decimal("100.00"),
            acciones_realizadas="Sesión item 2",
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        # Verificar progreso del plan (50% + 100%) / 2 = 75%
        self.plan.refresh_from_db()
        self.assertEqual(self.plan.progreso_general, Decimal("75.00"))
        
        print("✅ Test recalcular_progreso_plan: PASADO")
    
    def test_evidencias_json(self):
        """Test: Guardar evidencias en formato JSON"""
        evidencias = [
            "https://s3.amazonaws.com/foto1.jpg",
            "https://s3.amazonaws.com/radiografia1.jpg"
        ]
        
        sesion = SesionTratamiento.objects.create(
            item_plan=self.item_plan,
            consulta=self.consulta,
            fecha_sesion=date.today(),
            duracion_minutos=45,
            progreso_actual=Decimal("50.00"),
            acciones_realizadas="Sesión con evidencias",
            evidencias=evidencias,
            usuario_registro=self.usuario,
            empresa=self.empresa
        )
        
        self.assertEqual(len(sesion.evidencias), 2)
        self.assertIn("foto1.jpg", sesion.evidencias[0])
        print("✅ Test evidencias_json: PASADO")


def run_tests_with_summary():
    """Ejecutar tests y mostrar resumen"""
    print("\n" + "="*80)
    print("EJECUTANDO TESTS - SP3-T008: SESIONES DE TRATAMIENTO")
    print("="*80 + "\n")
    
    # Importar el test runner
    from django.test.runner import DiscoverRunner
    
    # Ejecutar tests
    runner = DiscoverRunner(verbosity=2, interactive=False, keepdb=True)
    failures = runner.run_tests(['api.tests_sesiones'])
    
    # Mostrar resumen final
    print("\n" + "="*80)
    if failures == 0:
        print("✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("="*80)
        print("\n📋 FUNCIONALIDADES VERIFICADAS:")
        print("  ✓ Crear sesiones básicas")
        print("  ✓ Prevenir sesiones duplicadas (UniqueConstraint)")
        print("  ✓ Progreso no retrocede")
        print("  ✓ Auto-completar ítems al 100%")
        print("  ✓ No permitir sesiones en ítems cancelados")
        print("  ✓ Múltiples sesiones progresivas")
        print("  ✓ Recalcular progreso del plan")
        print("  ✓ Guardar evidencias en JSON")
        print("\n🎯 LA FUNCIONALIDAD SP3-T008 ESTÁ COMPLETAMENTE OPERATIVA")
    else:
        print(f"❌ {failures} TEST(S) FALLARON")
        print("Revisa los detalles arriba para más información.")
    print("="*80 + "\n")
    
    return failures == 0


if __name__ == '__main__':
    run_tests_with_summary()
