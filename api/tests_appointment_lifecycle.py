"""
Tests para el flujo de Appointment Lifecycle (Opción B - Realista)
Prueba el flujo completo: pendiente → confirmada → en_consulta → diagnosticada → completada
"""
from django.test import TestCase
from django.utils import timezone
from datetime import date, time
from decimal import Decimal

from api.models import (
    Empresa, Usuario, Paciente, Odontologo, Recepcionista,
    Consulta, Estadodeconsulta, Tipodeconsulta, Horario
)


class AppointmentLifecycleTestCase(TestCase):
    """
    Test del ciclo de vida completo de una cita usando los 8 estados de la Opción B.
    """
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        # Crear empresa (tenant)
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test",
            subdomain="test",
            activo=True
        )
        
        # Crear tipo de usuario (necesario para Usuario)
        from api.models import Tipodeusuario
        self.tipo_paciente = Tipodeusuario.objects.create(
            rol="paciente",  # lowercase porque el signal busca lowercase
            descripcion="Tipo de usuario paciente",
            empresa=self.empresa
        )
        
        self.tipo_odontologo = Tipodeusuario.objects.create(
            rol="odontologo",
            descripcion="Tipo de usuario odontólogo",
            empresa=self.empresa
        )
        
        self.tipo_recepcionista = Tipodeusuario.objects.create(
            rol="recepcionista",
            descripcion="Tipo de usuario recepcionista",
            empresa=self.empresa
        )
        
        # Crear usuarios (los signals crean automáticamente los perfiles)
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan",
            apellido="Pérez",
            correoelectronico="juan@test.com",
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dra. María",
            apellido="González",
            correoelectronico="maria@test.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        
        self.usuario_recepcionista = Usuario.objects.create(
            nombre="Ana",
            apellido="López",
            correoelectronico="ana@test.com",
            idtipousuario=self.tipo_recepcionista,
            empresa=self.empresa
        )
        
        # Obtener los perfiles creados automáticamente por signals
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        self.recepcionista = Recepcionista.objects.get(codusuario=self.usuario_recepcionista)
        
        # Crear estado de consulta FK (legacy)
        self.estado_pendiente = Estadodeconsulta.objects.create(
            estado="Pendiente",
            empresa=self.empresa
        )
        
        # Crear tipo de consulta
        self.tipo_consulta = Tipodeconsulta.objects.create(
            nombreconsulta="Revisión General",
            empresa=self.empresa
        )
        
        # Crear horario
        self.horario = Horario.objects.create(
            hora=time(10, 0),
            empresa=self.empresa
        )
    
    def test_flujo_completo_appointment_lifecycle(self):
        """
        Test del flujo completo: pendiente → confirmada → en_consulta → 
        diagnosticada → completada
        """
        # 1. Crear consulta en estado PENDIENTE
        consulta = Consulta.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_pendiente,
            empresa=self.empresa,
            fecha=date.today(),
            estado='pendiente',
            motivo_consulta="Dolor de muela",
            requiere_pago=False
        )
        
        self.assertEqual(consulta.estado, 'pendiente')
        print(f"✅ 1. Consulta creada en estado: {consulta.estado}")
        
        # 2. CONFIRMAR CITA
        exito, mensaje = consulta.confirmar_cita(
            fecha_consulta=date.today(),
            hora_consulta=time(10, 30),
            usuario=self.usuario_recepcionista,
            notas="Paciente confirmó por teléfono"
        )
        
        self.assertTrue(exito, f"Error al confirmar: {mensaje}")
        self.assertEqual(consulta.estado, 'confirmada')
        self.assertEqual(consulta.fecha_consulta, date.today())
        self.assertEqual(consulta.hora_consulta, time(10, 30))
        print(f"✅ 2. Cita confirmada: {consulta.estado} - {mensaje}")
        
        # 3. INICIAR CONSULTA
        exito, mensaje = consulta.iniciar_consulta(usuario=self.usuario_odontologo)
        
        self.assertTrue(exito, f"Error al iniciar: {mensaje}")
        self.assertEqual(consulta.estado, 'en_consulta')
        self.assertIsNotNone(consulta.hora_inicio_consulta)
        print(f"✅ 3. Consulta iniciada: {consulta.estado} - Hora: {consulta.hora_inicio_consulta}")
        
        # 4. REGISTRAR DIAGNÓSTICO
        exito, mensaje = consulta.registrar_diagnostico(
            diagnostico="Caries en molar inferior derecho",
            tratamiento="Obturación",
            usuario=self.usuario_odontologo
        )
        
        self.assertTrue(exito, f"Error al diagnosticar: {mensaje}")
        self.assertEqual(consulta.estado, 'diagnosticada')
        self.assertEqual(consulta.diagnostico, "Caries en molar inferior derecho")
        print(f"✅ 4. Diagnóstico registrado: {consulta.estado}")
        
        # 5. COMPLETAR CONSULTA
        exito, mensaje = consulta.completar_consulta(
            observaciones="Paciente tolera bien el tratamiento",
            usuario=self.usuario_odontologo
        )
        
        self.assertTrue(exito, f"Error al completar: {mensaje}")
        self.assertEqual(consulta.estado, 'completada')
        self.assertIsNotNone(consulta.hora_fin_consulta)
        print(f"✅ 5. Consulta completada: {consulta.estado}")
        
        # Verificar duración
        duracion = consulta.get_duracion_consulta()
        self.assertIsNotNone(duracion)
        self.assertGreaterEqual(duracion, 0)
        print(f"✅ 6. Duración de consulta: {duracion} minutos")
        
        print("\n🎉 FLUJO COMPLETO EXITOSO!")
    
    def test_validacion_transiciones_invalidas(self):
        """
        Test que valida que no se puedan hacer transiciones inválidas
        """
        consulta = Consulta.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_pendiente,
            empresa=self.empresa,
            fecha=date.today(),
            estado='pendiente',
            motivo_consulta="Limpieza dental"
        )
        
        # Intentar completar sin confirmar (DEBE FALLAR)
        puede, mensaje = consulta.puede_cambiar_estado('completada')
        self.assertFalse(puede)
        print(f"✅ Validación correcta: No se puede saltar de 'pendiente' a 'completada'")
        
        # Intentar diagnosticar sin iniciar consulta (DEBE FALLAR)
        puede, mensaje = consulta.puede_cambiar_estado('diagnosticada')
        self.assertFalse(puede)
        print(f"✅ Validación correcta: No se puede diagnosticar sin iniciar consulta")
    
    def test_cancelar_cita(self):
        """
        Test de cancelación de cita
        """
        consulta = Consulta.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_pendiente,
            empresa=self.empresa,
            fecha=date.today(),
            estado='confirmada',  # Ya confirmada
            fecha_consulta=date.today(),
            hora_consulta=time(15, 0),
            motivo_consulta="Control"
        )
        
        # Cancelar cita
        exito, mensaje = consulta.cancelar_cita(
            motivo_cancelacion="Paciente enfermo, solicita reprogramar",
            usuario=self.usuario_recepcionista
        )
        
        self.assertTrue(exito)
        self.assertEqual(consulta.estado, 'cancelada')
        self.assertIsNotNone(consulta.motivo_cancelacion)
        print(f"✅ Cita cancelada correctamente: {consulta.motivo_cancelacion}")
    
    def test_marcar_no_asistio(self):
        """
        Test de marcar paciente como no asistido
        """
        consulta = Consulta.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_pendiente,
            empresa=self.empresa,
            fecha=date.today(),
            estado='confirmada',
            fecha_consulta=date.today(),
            hora_consulta=time(16, 0),
            motivo_consulta="Ortodoncia"
        )
        
        # Marcar no-show
        exito, mensaje = consulta.marcar_no_asistio(usuario=self.usuario_recepcionista)
        
        self.assertTrue(exito)
        self.assertEqual(consulta.estado, 'no_asistio')
        print(f"✅ Paciente marcado como no asistido")
    
    def test_validacion_pago_antes_completar(self):
        """
        Test que valida que si requiere pago, debe estar pagada antes de completar
        """
        consulta = Consulta.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            codrecepcionista=self.recepcionista,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_pendiente,
            empresa=self.empresa,
            fecha=date.today(),
            estado='diagnosticada',  # Ya diagnosticada
            motivo_consulta="Implante",
            diagnostico="Requiere implante dental",
            requiere_pago=True,
            costo_consulta=Decimal('50000.00')
        )
        
        # Intentar completar sin pago (DEBE FALLAR)
        exito, mensaje = consulta.completar_consulta(usuario=self.usuario_odontologo)
        
        self.assertFalse(exito)
        self.assertIn("pag", mensaje.lower())  # Debe mencionar el pago
        print(f"✅ Validación correcta: No se puede completar sin pago - {mensaje}")


if __name__ == '__main__':
    import unittest
    unittest.main()
