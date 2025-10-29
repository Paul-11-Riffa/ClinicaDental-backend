"""
Tests para el Paso 2: Lógica de negocio del flujo clínico.

Valida:
- Métodos helper de Consulta, Plandetratamiento, Itemplandetratamiento
- Signals de transiciones automáticas
- Validaciones de consistencia de datos
"""
from django.test import TestCase
from django.utils import timezone
from decimal import Decimal

from api.models import (
    Empresa, Tipodeusuario, Usuario, Paciente, Odontologo,
    Estado, Tipodeconsulta, Estadodeconsulta, Horario,
    Consulta, Plandetratamiento, Itemplandetratamiento, Servicio
)


class FlujoPaso2ConsultaTestCase(TestCase):
    """Tests para métodos helper del modelo Consulta"""
    
    def setUp(self):
        # Crear empresa
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test"
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
        
        # Crear usuarios (los signals crean Paciente/Odontologo automáticamente)
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan",
            apellido="Pérez",
            correoelectronico="juan@test.com",
            idtipousuario=self.tipo_paciente,
            empresa=self.empresa
        )
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos",
            apellido="Gómez",
            correoelectronico="carlos@test.com",
            idtipousuario=self.tipo_odontologo,
            empresa=self.empresa
        )
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        # Crear datos de apoyo
        self.estado = Estado.objects.create(estado="Activo", empresa=self.empresa)
        self.tipo_consulta = Tipodeconsulta.objects.create(nombreconsulta="Diagnóstico", empresa=self.empresa)
        self.estado_consulta = Estadodeconsulta.objects.create(estado="Completado", empresa=self.empresa)
        self.horario = Horario.objects.create(
            hora="09:00:00",
            empresa=self.empresa
        )
    
    def test_consulta_es_diagnostico(self):
        """Test: Identificar si una consulta es diagnóstica"""
        consulta_diagnostico = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            plan_tratamiento=None  # Sin plan = diagnóstica
        )
        
        self.assertTrue(consulta_diagnostico.es_consulta_diagnostico())
        print("   ✓ Consulta sin plan identificada como diagnóstica")
    
    def test_consulta_no_es_diagnostico(self):
        """Test: Consulta vinculada a plan no es diagnóstica"""
        # Crear plan
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            empresa=self.empresa
        )
        
        consulta_ejecucion = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            plan_tratamiento=plan  # Vinculada a plan
        )
        
        self.assertFalse(consulta_ejecucion.es_consulta_diagnostico())
        print("   ✓ Consulta vinculada a plan identificada como de ejecución")
    
    def test_consulta_puede_generar_plan(self):
        """Test: Consulta completada puede generar plan"""
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            requiere_pago=False
        )
        
        puede, mensaje = consulta.puede_generar_plan()
        self.assertTrue(puede)
        print(f"   ✓ Consulta puede generar plan: {mensaje}")
    
    def test_consulta_validacion_datos(self):
        """Test: Validación de consistencia de datos"""
        consulta = Consulta.objects.create(
            fecha=timezone.now().date(),
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idhorario=self.horario,
            idtipoconsulta=self.tipo_consulta,
            idestadoconsulta=self.estado_consulta,
            empresa=self.empresa,
            costo_consulta=Decimal('100.00'),
            requiere_pago=True
        )
        
        es_valido, errores = consulta.validar_datos_flujo()
        self.assertTrue(es_valido)
        self.assertEqual(len(errores), 0)
        print("   ✓ Validación de datos correcta")


class FlujoPaso2PlanTratamientoTestCase(TestCase):
    """Tests para métodos helper del modelo Plandetratamiento"""
    
    def setUp(self):
        # Setup similar al anterior (reutilizar código)
        self.empresa = Empresa.objects.create(
            nombre="Clínica Test Planes"
        )
        self.tipo_paciente = Tipodeusuario.objects.create(rol="Paciente", empresa=self.empresa)
        self.tipo_odontologo = Tipodeusuario.objects.create(rol="Odontologo", empresa=self.empresa)
        
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan", apellido="Pérez", correoelectronico="juan2@test.com",
            idtipousuario=self.tipo_paciente, empresa=self.empresa
        )
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos", apellido="Gómez", correoelectronico="carlos2@test.com",
            idtipousuario=self.tipo_odontologo, empresa=self.empresa
        )
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        self.estado = Estado.objects.create(estado="Activo", empresa=self.empresa)
        self.servicio = Servicio.objects.create(
            nombre="Limpieza",
            costobase=Decimal('50.00'),
            duracion=30,
            empresa=self.empresa
        )
    
    def test_plan_iniciar_ejecucion(self):
        """Test: Iniciar ejecución de un plan Aceptado"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='Aceptado',
            empresa=self.empresa
        )
        
        # Agregar un item
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            empresa=self.empresa
        )
        
        # Iniciar ejecución
        resultado = plan.iniciar_ejecucion()
        
        self.assertTrue(resultado)
        self.assertEqual(plan.estado_tratamiento, 'En Ejecución')
        self.assertIsNotNone(plan.fecha_inicio_ejecucion)
        print("   ✓ Plan iniciado correctamente")
    
    def test_plan_pausar_y_reanudar(self):
        """Test: Pausar y reanudar un plan"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),
            empresa=self.empresa
        )
        
        # Pausar
        plan.pausar(motivo="Paciente solicitó postergar")
        self.assertEqual(plan.estado_tratamiento, 'Pausado')
        print("   ✓ Plan pausado correctamente")
        
        # Reanudar
        plan.reanudar()
        self.assertEqual(plan.estado_tratamiento, 'En Ejecución')
        print("   ✓ Plan reanudado correctamente")
    
    def test_plan_cancelar(self):
        """Test: Cancelar un plan"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='Propuesto',
            empresa=self.empresa
        )
        
        resultado = plan.cancelar(motivo="Paciente no acepta presupuesto")
        
        self.assertTrue(resultado)
        self.assertEqual(plan.estado_tratamiento, 'Cancelado')
        self.assertIn("CANCELADO", plan.notas_plan)
        print("   ✓ Plan cancelado correctamente")
    
    def test_plan_completar(self):
        """Test: Completar un plan cuando todos los items están ejecutados"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),
            empresa=self.empresa
        )
        
        # Agregar item SIN fecha_ejecucion primero
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            empresa=self.empresa
        )
        
        # Ahora marcar como ejecutado - la signal se dispara automáticamente
        item.fecha_ejecucion = timezone.now()
        item.odontologo_ejecutor = self.odontologo
        item.save()
        
        # Recargar plan para ver los cambios de la signal
        plan.refresh_from_db()
        
        # Verificar que la signal completó el plan automáticamente
        self.assertEqual(plan.estado_tratamiento, 'Completado')
        self.assertIsNotNone(plan.fecha_finalizacion)
        print("   ✓ Plan completado correctamente (por signal automática)")
    
    def test_plan_calcular_progreso(self):
        """Test: Calcular progreso de ejecución del plan"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            empresa=self.empresa
        )
        
        # Agregar 3 items, ejecutar 2
        for i in range(3):
            item = Itemplandetratamiento.objects.create(
                idplantratamiento=plan,
                idservicio=self.servicio,
                idestado=self.estado,
                costofinal=Decimal('50.00'),
                estado_item='Activo',
                empresa=self.empresa
            )
            if i < 2:  # Ejecutar los primeros 2
                item.fecha_ejecucion = timezone.now()
                item.odontologo_ejecutor = self.odontologo
                item.save()
        
        progreso = plan.calcular_progreso_ejecucion()
        self.assertAlmostEqual(progreso, 66.67, places=1)
        print(f"   ✓ Progreso calculado correctamente: {progreso:.2f}%")


class FlujoPaso2ItemTestCase(TestCase):
    """Tests para métodos helper del modelo Itemplandetratamiento"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre="Clínica Test")
        self.tipo_paciente = Tipodeusuario.objects.create(rol="Paciente", empresa=self.empresa)
        self.tipo_odontologo = Tipodeusuario.objects.create(rol="Odontologo", empresa=self.empresa)
        
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan", apellido="Pérez", correoelectronico="juan3@test.com",
            idtipousuario=self.tipo_paciente, empresa=self.empresa
        )
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos", apellido="Gómez", correoelectronico="carlos3@test.com",
            idtipousuario=self.tipo_odontologo, empresa=self.empresa
        )
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        self.estado = Estado.objects.create(estado="Activo", empresa=self.empresa)
        self.servicio = Servicio.objects.create(
            nombre="Limpieza", costobase=Decimal('50.00'), duracion=30, empresa=self.empresa
        )
        
        self.plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),
            empresa=self.empresa
        )
    
    def test_item_puede_ejecutarse(self):
        """Test: Verificar si un item puede ejecutarse"""
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            orden_ejecucion=1,
            empresa=self.empresa
        )
        
        puede, mensaje = item.puede_ejecutarse()
        self.assertTrue(puede)
        print(f"   ✓ Item puede ejecutarse: {mensaje}")
    
    def test_item_marcar_ejecutado(self):
        """Test: Marcar un item como ejecutado"""
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            orden_ejecucion=1,
            empresa=self.empresa
        )
        
        resultado = item.marcar_ejecutado(
            odontologo=self.odontologo,
            notas="Procedimiento realizado sin complicaciones"
        )
        
        self.assertTrue(resultado)
        self.assertIsNotNone(item.fecha_ejecucion)
        self.assertEqual(item.odontologo_ejecutor, self.odontologo)
        self.assertIsNotNone(item.notas_ejecucion)
        print("   ✓ Item marcado como ejecutado correctamente")
    
    def test_item_validar_orden_ejecucion(self):
        """Test: No se puede ejecutar si hay items previos pendientes"""
        # Crear item con orden 1 (pendiente)
        item1 = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            orden_ejecucion=1,
            empresa=self.empresa
        )
        
        # Crear item con orden 2
        item2 = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('75.00'),
            estado_item='Activo',
            orden_ejecucion=2,
            empresa=self.empresa
        )
        
        # Intentar ejecutar item2 sin haber ejecutado item1
        puede, mensaje = item2.puede_ejecutarse()
        self.assertFalse(puede)
        self.assertIn("menor orden", mensaje)
        print(f"   ✓ Validación de orden correcta: {mensaje}")
    
    def test_item_reprogramar_orden(self):
        """Test: Reprogramar orden de ejecución de un item"""
        item = Itemplandetratamiento.objects.create(
            idplantratamiento=self.plan,
            idservicio=self.servicio,
            idestado=self.estado,
            costofinal=Decimal('50.00'),
            estado_item='Activo',
            orden_ejecucion=1,
            empresa=self.empresa
        )
        
        resultado = item.reprogramar_orden(nuevo_orden=5)
        
        self.assertTrue(resultado)
        self.assertEqual(item.orden_ejecucion, 5)
        print("   ✓ Item reprogramado correctamente")


class FlujoPaso2SignalsTestCase(TestCase):
    """Tests para signals de transiciones automáticas"""
    
    def setUp(self):
        self.empresa = Empresa.objects.create(nombre="Clínica Test")
        self.tipo_paciente = Tipodeusuario.objects.create(rol="Paciente", empresa=self.empresa)
        self.tipo_odontologo = Tipodeusuario.objects.create(rol="Odontologo", empresa=self.empresa)
        
        self.usuario_paciente = Usuario.objects.create(
            nombre="Juan", apellido="Pérez", correoelectronico="juan4@test.com",
            idtipousuario=self.tipo_paciente, empresa=self.empresa
        )
        self.paciente = Paciente.objects.get(codusuario=self.usuario_paciente)
        
        self.usuario_odontologo = Usuario.objects.create(
            nombre="Dr. Carlos", apellido="Gómez", correoelectronico="carlos4@test.com",
            idtipousuario=self.tipo_odontologo, empresa=self.empresa
        )
        self.odontologo = Odontologo.objects.get(codusuario=self.usuario_odontologo)
        
        self.estado = Estado.objects.create(estado="Activo", empresa=self.empresa)
        self.servicio = Servicio.objects.create(
            nombre="Limpieza", costobase=Decimal('50.00'), duracion=30, empresa=self.empresa
        )
    
    def test_signal_autocompletar_plan(self):
        """Test: El plan se autocompleta cuando todos los items están ejecutados"""
        plan = Plandetratamiento.objects.create(
            codpaciente=self.paciente,
            cododontologo=self.odontologo,
            idestado=self.estado,
            fechaplan=timezone.now().date(),
            estado_tratamiento='En Ejecución',
            fecha_inicio_ejecucion=timezone.now(),
            empresa=self.empresa
        )
        
        # Agregar items
        items = []
        for i in range(2):
            item = Itemplandetratamiento.objects.create(
                idplantratamiento=plan,
                idservicio=self.servicio,
                idestado=self.estado,
                costofinal=Decimal('50.00'),
                estado_item='Activo',
                orden_ejecucion=i+1,
                empresa=self.empresa
            )
            items.append(item)
        
        # Ejecutar el primero
        items[0].marcar_ejecutado(odontologo=self.odontologo)
        plan.refresh_from_db()
        self.assertEqual(plan.estado_tratamiento, 'En Ejecución')  # Aún en ejecución
        
        # Ejecutar el segundo (debería autocompletar el plan)
        items[1].marcar_ejecutado(odontologo=self.odontologo)
        plan.refresh_from_db()
        self.assertEqual(plan.estado_tratamiento, 'Completado')  # Autocompletado por signal!
        self.assertIsNotNone(plan.fecha_finalizacion)
        print("   ✓ Signal autocompletó el plan correctamente")
