#!/usr/bin/env python
"""
Diagnóstico completo del sistema
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from django.contrib.auth import get_user_model
from api.models import (
    Empresa, Usuario, Paciente, Odontologo, Recepcionista,
    Consulta, Horario, Tipodeconsulta, Estadodeconsulta,
    Tipodeusuario, Historialclinico, Consentimiento
)

print("="*80)
print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA")
print("="*80)

# 1. Empresas
print("\n📊 1. EMPRESAS REGISTRADAS")
print("-"*80)
empresas = Empresa.objects.all()
if empresas.exists():
    for emp in empresas:
        print(f"✅ {emp.nombre} (subdomain: {emp.subdomain})")
        print(f"   Activa: {emp.activo}")
        print(f"   Usuarios: {Usuario.objects.filter(empresa=emp).count()}")
        print(f"   Pacientes: {Paciente.objects.filter(empresa=emp).count()}")
        print(f"   Consultas: {Consulta.objects.filter(empresa=emp).count()}")
else:
    print("❌ No hay empresas registradas")

# 2. Tipos de Usuario (Roles)
print("\n👥 2. ROLES DISPONIBLES")
print("-"*80)
roles = Tipodeusuario.objects.all()
if roles.exists():
    for rol in roles:
        count = Usuario.objects.filter(idtipousuario=rol).count()
        empresa_info = f"(Empresa: {rol.empresa.nombre})" if rol.empresa else "(Global)"
        print(f"✅ {rol.rol} - {count} usuarios {empresa_info}")
else:
    print("❌ No hay roles configurados")
    print("⚠️  PROBLEMA: El sistema necesita roles para funcionar")
    print("   Solución: python manage.py crear_roles")

# 3. Estados de Consulta
print("\n📋 3. ESTADOS DE CONSULTA")
print("-"*80)
estados = Estadodeconsulta.objects.all()
if estados.exists():
    for estado in estados:
        count = Consulta.objects.filter(idestadoconsulta=estado).count()
        print(f"✅ {estado.estado} - {count} consultas")
else:
    print("❌ No hay estados de consulta configurados")
    print("⚠️  PROBLEMA: No se pueden crear consultas sin estados")
    print("   Solución: Crear estados (Pendiente, Confirmada, Completada, Cancelada)")

# 4. Tipos de Consulta
print("\n🦷 4. TIPOS DE CONSULTA")
print("-"*80)
tipos = Tipodeconsulta.objects.all()
if tipos.exists():
    for tipo in tipos:
        count = Consulta.objects.filter(idtipoconsulta=tipo).count()
        print(f"✅ {tipo.nombreconsulta} - ${tipo.precio} - {count} consultas")
else:
    print("❌ No hay tipos de consulta configurados")
    print("⚠️  PROBLEMA: No se pueden agendar citas sin tipos de consulta")
    print("   Solución: Crear tipos (Consulta General, Limpieza, Ortodoncia, etc.)")

# 5. Horarios
print("\n⏰ 5. HORARIOS DISPONIBLES")
print("-"*80)
horarios = Horario.objects.all()
if horarios.exists():
    print(f"✅ Total de horarios configurados: {horarios.count()}")
    print(f"   Horarios disponibles: {Horario.objects.filter(disponible=True).count()}")
    print(f"   Horarios ocupados: {Horario.objects.filter(disponible=False).count()}")
else:
    print("❌ No hay horarios configurados")
    print("⚠️  PROBLEMA: No se pueden agendar citas sin horarios")
    print("   Solución: Crear horarios de atención")

# 6. Odontólogos
print("\n👨‍⚕️ 6. ODONTÓLOGOS")
print("-"*80)
odontologos = Odontologo.objects.all()
if odontologos.exists():
    for odon in odontologos:
        user = odon.codusuario
        consultas = Consulta.objects.filter(cododontologo=odon).count()
        print(f"✅ Dr. {user.nombre} {user.apellido}")
        print(f"   Especialidad: {odon.especialidad or 'General'}")
        print(f"   Matrícula: {odon.nromatricula or 'N/A'}")
        print(f"   Consultas: {consultas}")
else:
    print("❌ No hay odontólogos registrados")
    print("⚠️  PROBLEMA: No se pueden agendar citas sin odontólogos")

# 7. Pacientes
print("\n🧑 7. PACIENTES")
print("-"*80)
pacientes = Paciente.objects.all()
if pacientes.exists():
    print(f"✅ Total de pacientes: {pacientes.count()}")
    for pac in pacientes[:5]:  # Mostrar solo los primeros 5
        user = pac.codusuario
        consultas = Consulta.objects.filter(codpaciente=pac).count()
        print(f"   • {user.nombre} {user.apellido} - CI: {pac.carnetidentidad} - {consultas} consultas")
    if pacientes.count() > 5:
        print(f"   ... y {pacientes.count() - 5} más")
else:
    print("⚠️  No hay pacientes registrados (normal en sistema nuevo)")

# 8. Consultas
print("\n📅 8. CONSULTAS")
print("-"*80)
consultas = Consulta.objects.all()
if consultas.exists():
    print(f"✅ Total de consultas: {consultas.count()}")
    
    # Por estado
    for estado in Estadodeconsulta.objects.all():
        count = consultas.filter(idestadoconsulta=estado).count()
        if count > 0:
            print(f"   {estado.estado}: {count}")
    
    # Últimas 3 consultas
    print(f"\n   📋 Últimas 3 consultas:")
    for consulta in consultas.order_by('-fecha')[:3]:
        pac = consulta.codpaciente.codusuario
        print(f"   • {consulta.fecha} - {pac.nombre} {pac.apellido} - {consulta.idestadoconsulta.estado}")
else:
    print("⚠️  No hay consultas registradas (normal en sistema nuevo)")

# 9. Historias Clínicas
print("\n📋 9. HISTORIAS CLÍNICAS")
print("-"*80)
historias = Historialclinico.objects.all()
if historias.exists():
    print(f"✅ Total de historias: {historias.count()}")
else:
    print("⚠️  No hay historias clínicas (normal en sistema nuevo)")

# 10. Consentimientos
print("\n📝 10. CONSENTIMIENTOS DIGITALES")
print("-"*80)
consentimientos = Consentimiento.objects.all()
if consentimientos.exists():
    print(f"✅ Total de consentimientos: {consentimientos.count()}")
else:
    print("⚠️  No hay consentimientos registrados (normal en sistema nuevo)")

# 11. Usuarios Django Auth
print("\n🔐 11. USUARIOS DE AUTENTICACIÓN")
print("-"*80)
User = get_user_model()
django_users = User.objects.all()
if django_users.exists():
    print(f"✅ Total de usuarios Django: {django_users.count()}")
    for user in django_users:
        print(f"   • {user.username} - Staff: {user.is_staff} - Active: {user.is_active}")
else:
    print("❌ No hay usuarios de autenticación")

# 12. Problemas detectados
print("\n" + "="*80)
print("⚠️  PROBLEMAS DETECTADOS")
print("="*80)

problemas = []

if not empresas.exists():
    problemas.append("❌ No hay empresas registradas")
    
if not roles.exists():
    problemas.append("❌ No hay roles configurados (CRÍTICO)")
    
if not estados.exists():
    problemas.append("❌ No hay estados de consulta (CRÍTICO)")
    
if not tipos.exists():
    problemas.append("❌ No hay tipos de consulta")
    
if not horarios.exists():
    problemas.append("❌ No hay horarios configurados")
    
if not odontologos.exists():
    problemas.append("⚠️  No hay odontólogos registrados")

if problemas:
    for problema in problemas:
        print(problema)
    
    print("\n💡 SOLUCIONES SUGERIDAS:")
    print("-"*80)
    
    if not roles.exists():
        print("1. Crear roles básicos:")
        print("   python manage.py shell")
        print("   from api.models import Tipodeusuario")
        print("   Tipodeusuario.objects.create(id=1, rol='Administrador', descripcion='Admin del sistema')")
        print("   Tipodeusuario.objects.create(id=2, rol='Paciente', descripcion='Paciente')")
        print("   Tipodeusuario.objects.create(id=3, rol='Odontologo', descripcion='Odontólogo')")
        print("   Tipodeusuario.objects.create(id=4, rol='Recepcionista', descripcion='Recepcionista')")
        
    if not estados.exists():
        print("\n2. Crear estados de consulta:")
        print("   from api.models import Estadodeconsulta")
        print("   Estadodeconsulta.objects.create(estado='Pendiente')")
        print("   Estadodeconsulta.objects.create(estado='Confirmada')")
        print("   Estadodeconsulta.objects.create(estado='Completada')")
        print("   Estadodeconsulta.objects.create(estado='Cancelada')")
        
    if not tipos.exists():
        print("\n3. Crear tipos de consulta:")
        print("   from api.models import Tipodeconsulta")
        print("   Tipodeconsulta.objects.create(nombreconsulta='Consulta General', precio=50)")
        print("   Tipodeconsulta.objects.create(nombreconsulta='Limpieza Dental', precio=80)")
        print("   Tipodeconsulta.objects.create(nombreconsulta='Ortodoncia', precio=150)")
else:
    print("✅ No se detectaron problemas críticos")

print("\n" + "="*80)
print("📊 RESUMEN FINAL")
print("="*80)
print(f"✅ Empresas: {empresas.count()}")
print(f"✅ Usuarios totales: {Usuario.objects.count()}")
print(f"✅ Pacientes: {pacientes.count()}")
print(f"✅ Odontólogos: {odontologos.count()}")
print(f"✅ Consultas: {consultas.count()}")
print(f"✅ Roles: {roles.count()}")
print(f"✅ Estados: {estados.count()}")
print(f"✅ Tipos de consulta: {tipos.count()}")
print(f"✅ Horarios: {horarios.count()}")
print("="*80)
