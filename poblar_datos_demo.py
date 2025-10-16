# -*- coding: utf-8 -*-
"""
Script para poblar la base de datos con datos de prueba.
Crea 4 empresas (Norte, Sur, Este, Oeste) con usuarios y datos completos.
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
from decimal import Decimal
import random

# Configurar UTF-8 para la salida de Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# IMPORTANTE: Desactivar señales antes de configurar Django
os.environ['DISABLE_SIGNALS'] = '1'

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

# Importar modelos (todos están en la app 'api')
from api.models import (
    Empresa, Usuario, Tipodeusuario,
    Paciente, Odontologo, Recepcionista, Consulta, Historialclinico,
    Servicio, Insumo, Medicamento, Recetamedica, Imtemreceta,
    Plandetratamiento, Itemplandetratamiento, Factura, Itemdefactura, Pago,
    Piezadental, Registroodontograma, Horario, Estado, Estadodeconsulta,
    Estadodefactura, Tipodeconsulta, Tipopago
)
from no_show_policies.models import PoliticaNoShow, Multa
from django.db.models import signals
from django.db import transaction
from django.contrib.auth import get_user_model

User = get_user_model()


def limpiar_datos():
    """Limpia todos los datos de prueba existentes."""
    print("🗑️  Limpiando datos existentes...")

    # Orden de eliminación por dependencias
    Multa.objects.all().delete()
    PoliticaNoShow.objects.all().delete()
    Pago.objects.all().delete()
    Itemdefactura.objects.all().delete()
    Factura.objects.all().delete()
    Itemplandetratamiento.objects.all().delete()
    Plandetratamiento.objects.all().delete()
    Imtemreceta.objects.all().delete()
    Recetamedica.objects.all().delete()
    Registroodontograma.objects.all().delete()
    Consulta.objects.all().delete()
    Historialclinico.objects.all().delete()

    # Eliminar usuarios específicos por tipo
    Recepcionista.objects.all().delete()
    Odontologo.objects.all().delete()
    Paciente.objects.all().delete()

    # Eliminar datos de catálogo
    Piezadental.objects.all().delete()
    Medicamento.objects.all().delete()
    Insumo.objects.all().delete()
    Servicio.objects.all().delete()
    Horario.objects.all().delete()
    Tipopago.objects.all().delete()
    Estadodefactura.objects.all().delete()
    Estadodeconsulta.objects.all().delete()
    Tipodeconsulta.objects.all().delete()
    Estado.objects.all().delete()

    # Eliminar usuarios y tipos
    Usuario.objects.all().delete()
    Tipodeusuario.objects.all().delete()

    # Eliminar usuarios de Django Auth
    User.objects.all().delete()

    # Eliminar empresas
    Empresa.objects.all().delete()

    print("✅ Datos limpiados exitosamente\n")


def crear_empresas():
    """Crea las 4 empresas."""
    print("🏢 Creando empresas...")

    empresas_data = [
        {"nombre": "Clínica Dental Norte", "subdomain": "norte"},
        {"nombre": "Clínica Dental Sur", "subdomain": "sur"},
        {"nombre": "Clínica Dental Este", "subdomain": "este"},
        {"nombre": "Clínica Dental Oeste", "subdomain": "oeste"},
    ]

    empresas = []
    for data in empresas_data:
        empresa = Empresa.objects.create(**data, activo=True)
        empresas.append(empresa)
        print(f"  ✓ {empresa.nombre} ({empresa.subdomain})")

    print()
    return empresas


def crear_tipos_usuario(empresa):
    """Crea los tipos de usuario para una empresa."""
    tipos_data = [
        {"rol": "Administrador", "descripcion": "Gestión completa de la clínica"},
        {"rol": "Paciente", "descripcion": "Usuario final que recibe atención"},
        {"rol": "Odontólogo", "descripcion": "Profesional que atiende pacientes"},
        {"rol": "Recepcionista", "descripcion": "Personal administrativo"},
    ]

    tipos = {}
    for data in tipos_data:
        tipo = Tipodeusuario.objects.create(empresa=empresa, **data)
        tipos[data["rol"]] = tipo

    return tipos


def crear_usuarios(empresa, tipos_usuario):
    """Crea usuarios para una empresa con diferentes roles."""
    usuarios_creados = {
        "administradores": [],
        "pacientes": [],
        "odontologos": [],
        "recepcionistas": [],
        "credenciales": []  # Para guardar las credenciales
    }

    subdomain = empresa.subdomain
    password_default = "Password123"  # Contraseña por defecto para todos

    # 2 Administradores
    for i in range(1, 3):
        email = f"admin{i}@{subdomain}.com"

        # Crear usuario en Django auth
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password_default,
            first_name=f"Admin{i}",
            last_name=f"{subdomain.capitalize()}"
        )

        # Crear usuario en tabla Usuario
        usuario = Usuario.objects.create(
            nombre=f"Admin{i}",
            apellido=f"{subdomain.capitalize()}",
            correoelectronico=email,
            sexo=random.choice(["Masculino", "Femenino"]),
            telefono=f"555-010{i}",
            idtipousuario=tipos_usuario["Administrador"],
            empresa=empresa
        )
        usuarios_creados["administradores"].append(usuario)
        usuarios_creados["credenciales"].append({
            "rol": "Administrador",
            "email": email,
            "password": password_default,
            "nombre": f"Admin{i} {subdomain.capitalize()}"
        })

    # 4 Odontólogos
    especialidades = ["Ortodoncia", "Endodoncia", "Periodoncia", "Implantología"]
    for i in range(1, 5):
        usuario = Usuario.objects.create(
            nombre=f"Dr. Carlos{i}" if i % 2 == 0 else f"Dra. María{i}",
            apellido=f"Dentista{subdomain.capitalize()}",
            correoelectronico=f"odontologo{i}@{subdomain}.com",
            sexo="Masculino" if i % 2 == 0 else "Femenino",
            telefono=f"555-020{i}",
            idtipousuario=tipos_usuario["Odontólogo"],
            empresa=empresa
        )

        Odontologo.objects.create(
            codusuario=usuario,
            especialidad=especialidades[i-1],
            experienciaprofesional=f"{random.randint(5, 20)} años de experiencia en {especialidades[i-1]}",
            nromatricula=f"MAT-{subdomain.upper()}-{1000+i}",
            empresa=empresa
        )
        usuarios_creados["odontologos"].append(usuario)

    # 2 Recepcionistas
    for i in range(1, 3):
        usuario = Usuario.objects.create(
            nombre=f"Recep{i}",
            apellido=f"{subdomain.capitalize()}",
            correoelectronico=f"recepcion{i}@{subdomain}.com",
            sexo="Femenino",
            telefono=f"555-030{i}",
            idtipousuario=tipos_usuario["Recepcionista"],
            empresa=empresa
        )

        Recepcionista.objects.create(
            codusuario=usuario,
            habilidadessoftware="Microsoft Office, Sistema de Gestión Dental, Atención al Cliente",
            empresa=empresa
        )
        usuarios_creados["recepcionistas"].append(usuario)

    # 15 Pacientes
    nombres = ["Juan", "María", "Pedro", "Ana", "Luis", "Carmen", "José", "Laura", "Miguel", "Sofia",
               "Carlos", "Elena", "Diego", "Isabel", "Fernando"]
    apellidos = ["García", "Rodríguez", "Martínez", "López", "González", "Pérez", "Sánchez", "Ramírez",
                 "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Cruz", "Morales"]

    for i in range(1, 16):
        email = f"paciente{i}@{subdomain}.com"
        nombre = nombres[i-1]
        apellido = apellidos[i-1]

        # Crear usuario en Django auth
        django_user = User.objects.create_user(
            username=email,
            email=email,
            password=password_default,
            first_name=nombre,
            last_name=apellido
        )

        # Crear usuario en tabla Usuario
        usuario = Usuario.objects.create(
            nombre=nombre,
            apellido=apellido,
            correoelectronico=email,
            sexo=random.choice(["Masculino", "Femenino"]),
            telefono=f"555-{1000+i}",
            idtipousuario=tipos_usuario["Paciente"],
            empresa=empresa
        )

        Paciente.objects.create(
            codusuario=usuario,
            carnetidentidad=f"CI-{subdomain.upper()}-{10000+i}",
            fechanacimiento=date(random.randint(1950, 2005), random.randint(1, 12), random.randint(1, 28)),
            direccion=f"Calle {i}, Zona {subdomain.capitalize()}, Ciudad",
            empresa=empresa
        )
        usuarios_creados["pacientes"].append(usuario)

        # Guardar credenciales del primer paciente de cada empresa
        if i == 1:
            usuarios_creados["credenciales"].append({
                "rol": "Paciente",
                "email": email,
                "password": password_default,
                "nombre": f"{nombre} {apellido}"
            })

    return usuarios_creados


def crear_catalogos(empresa):
    """Crea datos de catálogos para la empresa."""
    catalogos = {}

    # Horarios (8:00 AM a 6:00 PM) - usar get_or_create por unique constraint
    horarios = []
    for hora in range(8, 19):
        for minuto in [0, 30]:
            horario, created = Horario.objects.get_or_create(
                hora=f"{hora:02d}:{minuto:02d}:00",
                defaults={"empresa": empresa}
            )
            horarios.append(horario)
    catalogos["horarios"] = horarios

    # Estados - crear con sufijo de empresa para evitar duplicados
    estados_nombres = ["Pendiente", "En Proceso", "Completado", "Cancelado"]
    estados = []
    for nombre in estados_nombres:
        estado, created = Estado.objects.get_or_create(
            estado=f"{nombre}_{empresa.subdomain}",
            defaults={"empresa": empresa}
        )
        estados.append(estado)
    catalogos["estados"] = estados

    # Estados de consulta
    estados_consulta_nombres = ["Programada", "En Atención", "Completada", "Cancelada", "No Show"]
    estados_consulta = []
    for nombre in estados_consulta_nombres:
        estado, created = Estadodeconsulta.objects.get_or_create(
            estado=f"{nombre}_{empresa.subdomain}",
            defaults={"empresa": empresa}
        )
        estados_consulta.append(estado)
    catalogos["estados_consulta"] = estados_consulta

    # Estados de factura
    estados_factura_nombres = ["Pendiente", "Pagada", "Parcial", "Vencida"]
    estados_factura = []
    for nombre in estados_factura_nombres:
        estado, created = Estadodefactura.objects.get_or_create(
            estado=f"{nombre}_{empresa.subdomain}",
            defaults={"empresa": empresa}
        )
        estados_factura.append(estado)
    catalogos["estados_factura"] = estados_factura

    # Tipos de consulta
    tipos_consulta_nombres = ["Primera Vez", "Control", "Emergencia", "Tratamiento"]
    tipos_consulta = []
    for nombre in tipos_consulta_nombres:
        tipo = Tipodeconsulta.objects.create(nombreconsulta=nombre, empresa=empresa)
        tipos_consulta.append(tipo)
    catalogos["tipos_consulta"] = tipos_consulta

    # Tipos de pago
    tipos_pago_nombres = ["Efectivo", "Tarjeta", "Transferencia", "Seguro"]
    tipos_pago = []
    for nombre in tipos_pago_nombres:
        tipo, created = Tipopago.objects.get_or_create(
            nombrepago=f"{nombre}_{empresa.subdomain}",
            defaults={"empresa": empresa}
        )
        tipos_pago.append(tipo)
    catalogos["tipos_pago"] = tipos_pago

    # Servicios dentales
    servicios_data = [
        {"nombre": "Limpieza Dental", "descripcion": "Limpieza profesional completa", "costobase": "150.00"},
        {"nombre": "Extracción Simple", "descripcion": "Extracción de pieza dental", "costobase": "200.00"},
        {"nombre": "Endodoncia", "descripcion": "Tratamiento de conducto", "costobase": "800.00"},
        {"nombre": "Corona Dental", "descripcion": "Prótesis fija", "costobase": "1200.00"},
        {"nombre": "Ortodoncia", "descripcion": "Brackets metálicos", "costobase": "3500.00"},
        {"nombre": "Blanqueamiento", "descripcion": "Blanqueamiento dental profesional", "costobase": "400.00"},
        {"nombre": "Implante Dental", "descripcion": "Implante de titanio", "costobase": "2500.00"},
        {"nombre": "Prótesis Total", "descripcion": "Dentadura completa", "costobase": "1800.00"},
    ]
    servicios = []
    for data in servicios_data:
        servicio = Servicio.objects.create(empresa=empresa, **data)
        servicios.append(servicio)
    catalogos["servicios"] = servicios

    # Medicamentos
    medicamentos_data = [
        {"nombre": "Amoxicilina", "cantidadmiligramos": "500", "presentacion": "Cápsulas"},
        {"nombre": "Ibuprofeno", "cantidadmiligramos": "400", "presentacion": "Tabletas"},
        {"nombre": "Paracetamol", "cantidadmiligramos": "500", "presentacion": "Tabletas"},
        {"nombre": "Clindamicina", "cantidadmiligramos": "300", "presentacion": "Cápsulas"},
        {"nombre": "Diclofenaco", "cantidadmiligramos": "50", "presentacion": "Tabletas"},
    ]
    medicamentos = []
    for data in medicamentos_data:
        medicamento = Medicamento.objects.create(empresa=empresa, **data)
        medicamentos.append(medicamento)
    catalogos["medicamentos"] = medicamentos

    # Insumos
    insumos_data = [
        {"nombre": "Guantes de Látex", "descripcion": "Caja x100", "stock": 50, "unidaddemedida": "Caja"},
        {"nombre": "Mascarillas", "descripcion": "Caja x50", "stock": 100, "unidaddemedida": "Caja"},
        {"nombre": "Anestesia Local", "descripcion": "Lidocaína 2%", "stock": 30, "unidaddemedida": "Unidad"},
        {"nombre": "Algodón", "descripcion": "Rollo estéril", "stock": 75, "unidaddemedida": "Rollo"},
        {"nombre": "Gasas", "descripcion": "Paquete x100", "stock": 40, "unidaddemedida": "Paquete"},
    ]
    insumos = []
    for data in insumos_data:
        insumo = Insumo.objects.create(empresa=empresa, **data)
        insumos.append(insumo)
    catalogos["insumos"] = insumos

    # Piezas dentales (Sistema FDI)
    piezas_data = []
    # Adultos (11-18, 21-28, 31-38, 41-48)
    for cuadrante in [1, 2, 3, 4]:
        for pieza in range(1, 9):
            numero = cuadrante * 10 + pieza
            grupo = "Permanente"
            piezas_data.append({"nombrepieza": str(numero), "grupo": grupo})

    piezas_dentales = []
    for data in piezas_data:
        pieza = Piezadental.objects.create(empresa=empresa, **data)
        piezas_dentales.append(pieza)
    catalogos["piezas_dentales"] = piezas_dentales

    return catalogos


@transaction.atomic
def crear_datos_clinicos(empresa, usuarios, catalogos):
    """Crea datos clínicos: historiales, consultas, tratamientos, etc."""
    pacientes = Paciente.objects.filter(empresa=empresa)
    odontologos = Odontologo.objects.filter(empresa=empresa)
    recepcionistas = Recepcionista.objects.filter(empresa=empresa)

    # Historiales clínicos
    alergias_opciones = ["Ninguna", "Penicilina", "Látex", "Anestesia local"]
    enfermedades_opciones = ["Ninguna", "Diabetes", "Hipertensión", "Cardiopatía"]

    for paciente in pacientes[:10]:  # 10 pacientes con historial
        historial = Historialclinico.objects.create(
            pacientecodigo=paciente,
            alergias=random.choice(alergias_opciones),
            enfermedades=random.choice(enfermedades_opciones),
            motivoconsulta="Dolor en molar",
            diagnostico="Caries dental",
            episodio=1,
            empresa=empresa
        )

        # Registros odontograma (2-3 piezas afectadas)
        for _ in range(random.randint(2, 3)):
            pieza = random.choice(catalogos["piezas_dentales"])
            Registroodontograma.objects.create(
                idhistorialclinico=historial,
                idpiezadental=pieza,
                diagnostico=random.choice(["Caries", "Fractura", "Desgaste"]),
                fecharegistro=date.today() - timedelta(days=random.randint(1, 30)),
                empresa=empresa
            )

    # Consultas (citas) - Crear en lote para mejor rendimiento
    consultas_a_crear = []
    for i in range(30):  # 30 consultas por empresa
        paciente = random.choice(list(pacientes))
        odontologo = random.choice(list(odontologos))
        recepcionista = random.choice(list(recepcionistas))

        fecha_consulta = date.today() - timedelta(days=random.randint(-30, 30))

        consulta = Consulta(
            fecha=fecha_consulta,
            codpaciente=paciente,
            cododontologo=odontologo,
            codrecepcionista=recepcionista,
            idhorario=random.choice(catalogos["horarios"]),
            idtipoconsulta=random.choice(catalogos["tipos_consulta"]),
            idestadoconsulta=random.choice(catalogos["estados_consulta"]),
            empresa=empresa
        )
        consultas_a_crear.append(consulta)

    # Crear todas las consultas en lote (no dispara señales post_save)
    if consultas_a_crear:
        Consulta.objects.bulk_create(consultas_a_crear)

    # Planes de tratamiento
    for i in range(15):  # 15 planes por empresa
        paciente = random.choice(list(pacientes))
        odontologo = random.choice(list(odontologos))

        plan = Plandetratamiento.objects.create(
            codpaciente=paciente,
            cododontologo=odontologo,
            idestado=catalogos["estados"][0],  # Pendiente
            fechaplan=date.today() - timedelta(days=random.randint(1, 60)),
            descuento=Decimal(random.randint(0, 20)),
            montototal=Decimal("0.00"),
            empresa=empresa
        )

        # Items del plan (2-4 servicios)
        total_plan = Decimal("0.00")
        for _ in range(random.randint(2, 4)):
            servicio = random.choice(catalogos["servicios"])
            pieza = random.choice(catalogos["piezas_dentales"]) if random.random() > 0.3 else None

            # Convertir costobase a Decimal si no lo es
            costo_base = Decimal(str(servicio.costobase))
            costo = costo_base * Decimal(str(random.uniform(0.9, 1.1)))
            total_plan += costo

            Itemplandetratamiento.objects.create(
                idplantratamiento=plan,
                idservicio=servicio,
                idpiezadental=pieza,
                idestado=random.choice(catalogos["estados"]),
                costofinal=costo,
                empresa=empresa
            )

        plan.montototal = total_plan
        plan.save()

        # Factura para el plan (70% de probabilidad)
        if random.random() > 0.3:
            factura = Factura.objects.create(
                idplantratamiento=plan,
                idestadofactura=random.choice(catalogos["estados_factura"]),
                fechaemision=plan.fechaplan + timedelta(days=random.randint(1, 7)),
                montototal=total_plan,
                empresa=empresa
            )

            # Items de factura
            Itemdefactura.objects.create(
                idfactura=factura,
                descripcion=f"Plan de tratamiento - {paciente.codusuario.nombre}",
                monto=total_plan,
                empresa=empresa
            )

            # Pagos (50% de facturas tienen pagos)
            if random.random() > 0.5:
                monto_pagado = total_plan * Decimal(random.uniform(0.3, 1.0))
                Pago.objects.create(
                    idfactura=factura,
                    idtipopago=random.choice(catalogos["tipos_pago"]),
                    montopagado=monto_pagado,
                    fechapago=factura.fechaemision + timedelta(days=random.randint(1, 15)),
                    empresa=empresa
                )

    # Recetas médicas
    for i in range(20):  # 20 recetas por empresa
        paciente = random.choice(list(pacientes))
        odontologo = random.choice(list(odontologos))

        receta = Recetamedica.objects.create(
            codpaciente=paciente,
            cododontologo=odontologo,
            fechaemision=date.today() - timedelta(days=random.randint(1, 90)),
            empresa=empresa
        )

        # Items de receta (1-3 medicamentos)
        for _ in range(random.randint(1, 3)):
            medicamento = random.choice(catalogos["medicamentos"])
            posologias = [
                "Tomar 1 cada 8 horas por 7 días",
                "Tomar 1 cada 6 horas después de las comidas",
                "Tomar 1 cada 12 horas por 5 días",
            ]

            Imtemreceta.objects.create(
                idreceta=receta,
                idmedicamento=medicamento,
                posologia=random.choice(posologias),
                empresa=empresa
            )


def crear_politicas_noshow(empresa, catalogos):
    """Crea políticas de no-show para la empresa."""
    # Buscar el estado "No Show"
    estado_noshow = None
    for estado in catalogos["estados_consulta"]:
        if "No Show" in estado.estado:
            estado_noshow = estado
            break

    if not estado_noshow:
        return

    # Crear política básica de no-show
    politica = PoliticaNoShow.objects.create(
        nombre=f"Política No-Show - {empresa.nombre}",
        empresa=empresa,
        estado_consulta=estado_noshow,
        penalizacion_economica=Decimal("100.00"),
        bloqueo_temporal=True,
        dias_bloqueo=7,
        reprogramacion_obligatoria=True,
        alerta_interna=True,
        notificacion_paciente=True,
        notificacion_profesional=False,
        activo=True
    )

    # Crear algunas multas de ejemplo
    consultas_noshow = Consulta.objects.filter(
        empresa=empresa,
        idestadoconsulta=estado_noshow
    )[:3]

    for consulta in consultas_noshow:
        Multa.objects.create(
            empresa=empresa,
            usuario=consulta.codpaciente.codusuario,
            consulta=consulta,
            politica=politica,
            monto=Decimal("100.00"),
            motivo="Inasistencia sin aviso previo",
            estado=random.choice(["pendiente", "pagada"]),
            vencimiento=datetime.now() + timedelta(days=30)
        )


def desactivar_senales():
    """Desactiva temporalmente las señales de Django para evitar errores durante la población."""
    # Desactivar señal específica de notificaciones móviles
    try:
        signals.post_save.disconnect(
            sender=Consulta,
            dispatch_uid="mn_consulta_created_queue_v3"
        )
        print("  ✓ Señales de notificaciones desactivadas temporalmente")
    except Exception as e:
        print(f"  ℹ️  No se pudo desactivar señal específica: {e}")

    # Desactivar otras señales de Consulta
    try:
        # Obtener todos los receptores registrados para Consulta
        from django.db.models.signals import post_save, pre_save
        post_save.disconnect(sender=Consulta)
        pre_save.disconnect(sender=Consulta)
        print("  ✓ Señales generales de Consulta desactivadas")
    except Exception as e:
        print(f"  ℹ️  Error desactivando señales generales: {e}")


def main():
    """Función principal."""
    print("=" * 60)
    print("🦷 SCRIPT DE POBLACIÓN DE DATOS - SISTEMA DENTAL")
    print("=" * 60)
    print()

    # Desactivar señales que causan errores
    try:
        desactivar_senales()
    except Exception as e:
        print(f"  ℹ️  No se pudieron desactivar las señales (puede ser normal): {e}")

    # Limpiar datos existentes
    # respuesta = input("¿Desea limpiar los datos existentes? (s/n): ")
    # if respuesta.lower() == 's':
    #     limpiar_datos()
    limpiar_datos()  # Ejecutar automáticamente

    # Crear empresas
    empresas = crear_empresas()

    # Para cada empresa, crear todos los datos
    for empresa in empresas:
        print(f"📊 Poblando datos para: {empresa.nombre}")
        print("-" * 60)

        # Tipos de usuario
        print("  👥 Creando tipos de usuario...")
        tipos_usuario = crear_tipos_usuario(empresa)

        # Usuarios
        print("  🧑‍⚕️ Creando usuarios...")
        usuarios = crear_usuarios(empresa, tipos_usuario)
        print(f"    ✓ {len(usuarios['administradores'])} Administradores")
        print(f"    ✓ {len(usuarios['odontologos'])} Odontólogos")
        print(f"    ✓ {len(usuarios['recepcionistas'])} Recepcionistas")
        print(f"    ✓ {len(usuarios['pacientes'])} Pacientes")

        # Catálogos
        print("  📋 Creando catálogos...")
        catalogos = crear_catalogos(empresa)
        print(f"    ✓ {len(catalogos['horarios'])} Horarios")
        print(f"    ✓ {len(catalogos['estados'])} Estados")
        print(f"    ✓ {len(catalogos['servicios'])} Servicios")
        print(f"    ✓ {len(catalogos['medicamentos'])} Medicamentos")
        print(f"    ✓ {len(catalogos['insumos'])} Insumos")
        print(f"    ✓ {len(catalogos['piezas_dentales'])} Piezas dentales")

        # Datos clínicos
        print("  🏥 Creando datos clínicos...")
        crear_datos_clinicos(empresa, usuarios, catalogos)
        print(f"    ✓ Historiales clínicos: {Historialclinico.objects.filter(empresa=empresa).count()}")
        print(f"    ✓ Consultas: {Consulta.objects.filter(empresa=empresa).count()}")
        print(f"    ✓ Planes de tratamiento: {Plandetratamiento.objects.filter(empresa=empresa).count()}")
        print(f"    ✓ Facturas: {Factura.objects.filter(empresa=empresa).count()}")
        print(f"    ✓ Recetas: {Recetamedica.objects.filter(empresa=empresa).count()}")

        # Políticas no-show
        print("  ⚠️  Creando políticas de no-show...")
        crear_politicas_noshow(empresa, catalogos)
        print(f"    ✓ Políticas: {PoliticaNoShow.objects.filter(empresa=empresa).count()}")
        print(f"    ✓ Multas: {Multa.objects.filter(empresa=empresa).count()}")

        print()

    print("=" * 60)
    print("✅ POBLACIÓN DE DATOS COMPLETADA EXITOSAMENTE")
    print("=" * 60)
    print()
    print("📊 Resumen general:")
    print(f"  • Empresas creadas: {Empresa.objects.count()}")
    print(f"  • Usuarios totales: {Usuario.objects.count()}")
    print(f"  • Pacientes totales: {Paciente.objects.count()}")
    print(f"  • Odontólogos totales: {Odontologo.objects.count()}")
    print(f"  • Consultas totales: {Consulta.objects.count()}")
    print(f"  • Planes de tratamiento totales: {Plandetratamiento.objects.count()}")
    print()

    # Mostrar credenciales de acceso
    print("=" * 60)
    print("🔑 CREDENCIALES DE ACCESO PARA PRUEBAS")
    print("=" * 60)
    print()

    # Obtener credenciales de cada empresa
    for empresa in empresas:
        print(f"📍 {empresa.nombre} ({empresa.subdomain})")
        print("-" * 60)

        # Buscar credenciales de esta empresa
        admin_email = f"admin1@{empresa.subdomain}.com"
        paciente_email = f"paciente1@{empresa.subdomain}.com"

        print(f"  👤 Administrador:")
        print(f"     Email:    {admin_email}")
        print(f"     Password: Password123")
        print()
        print(f"  👤 Paciente (Cliente):")
        print(f"     Email:    {paciente_email}")
        print(f"     Password: Password123")
        print()

    print("=" * 60)
    print("ℹ️  NOTA: Todos los usuarios tienen la contraseña: Password123")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
