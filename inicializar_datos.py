#!/usr/bin/env python
"""
Script para inicializar datos básicos del sistema
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from api.models import Tipodeusuario, Estadodeconsulta, Tipodeconsulta, Horario, Empresa
from datetime import time

print("="*80)
print("🚀 INICIALIZANDO DATOS BÁSICOS DEL SISTEMA")
print("="*80)

# Obtener o crear la empresa actual
empresa = None
empresas = Empresa.objects.all()
if empresas.exists():
    empresa = empresas.first()
    print(f"\n✅ Usando empresa: {empresa.nombre} ({empresa.subdomain})")
else:
    print("\n⚠️  No hay empresas registradas. Algunos datos se crearán sin empresa.")

# ============================================
# 1. TIPOS DE USUARIO (ROLES) - CRÍTICO
# ============================================
print("\n" + "="*80)
print("1️⃣  CREANDO ROLES (TIPOS DE USUARIO)")
print("="*80)

roles_base = [
    {'id': 1, 'rol': 'Administrador', 'descripcion': 'Administrador del sistema con acceso completo'},
    {'id': 2, 'rol': 'Paciente', 'descripcion': 'Paciente de la clínica'},
    {'id': 3, 'rol': 'Odontologo', 'descripcion': 'Odontólogo profesional'},
    {'id': 4, 'rol': 'Recepcionista', 'descripcion': 'Personal de recepción'},
]

for rol_data in roles_base:
    try:
        rol, created = Tipodeusuario.objects.get_or_create(
            id=rol_data['id'],
            defaults={
                'rol': rol_data['rol'],
                'descripcion': rol_data['descripcion'],
                'empresa': None  # Roles globales
            }
        )
        if created:
            print(f"✅ Creado: {rol.rol} (ID: {rol.id})")
        else:
            print(f"ℹ️  Ya existe: {rol.rol} (ID: {rol.id})")
    except Exception as e:
        print(f"❌ Error creando rol {rol_data['rol']}: {e}")

# ============================================
# 2. ESTADOS DE CONSULTA - CRÍTICO
# ============================================
print("\n" + "="*80)
print("2️⃣  CREANDO ESTADOS DE CONSULTA")
print("="*80)

estados_base = [
    {'estado': 'Pendiente', 'descripcion': 'Consulta agendada, pendiente de confirmación'},
    {'estado': 'Confirmada', 'descripcion': 'Consulta confirmada por el paciente'},
    {'estado': 'En Proceso', 'descripcion': 'Consulta en curso'},
    {'estado': 'Completada', 'descripcion': 'Consulta finalizada exitosamente'},
    {'estado': 'Cancelada', 'descripcion': 'Consulta cancelada'},
    {'estado': 'No Asistió', 'descripcion': 'El paciente no asistió a la consulta'},
]

for estado_data in estados_base:
    try:
        estado, created = Estadodeconsulta.objects.get_or_create(
            estado=estado_data['estado'],
            defaults={
                'empresa': empresa
            }
        )
        if created:
            print(f"✅ Creado: {estado.estado}")
        else:
            print(f"ℹ️  Ya existe: {estado.estado}")
    except Exception as e:
        print(f"❌ Error creando estado {estado_data['estado']}: {e}")

# ============================================
# 3. TIPOS DE CONSULTA
# ============================================
print("\n" + "="*80)
print("3️⃣  CREANDO TIPOS DE CONSULTA")
print("="*80)

tipos_consulta = [
    {'nombre': 'Consulta General'},
    {'nombre': 'Limpieza Dental'},
    {'nombre': 'Extracción'},
    {'nombre': 'Endodoncia'},
    {'nombre': 'Ortodoncia'},
    {'nombre': 'Implante'},
    {'nombre': 'Blanqueamiento'},
    {'nombre': 'Emergencia'},
]

for tipo_data in tipos_consulta:
    try:
        tipo, created = Tipodeconsulta.objects.get_or_create(
            nombreconsulta=tipo_data['nombre'],
            defaults={
                'empresa': empresa
            }
        )
        if created:
            print(f"✅ Creado: {tipo.nombreconsulta}")
        else:
            print(f"ℹ️  Ya existe: {tipo.nombreconsulta}")
    except Exception as e:
        print(f"❌ Error creando tipo {tipo_data['nombre']}: {e}")

# ============================================
# 4. HORARIOS DE ATENCIÓN
# ============================================
print("\n" + "="*80)
print("4️⃣  CREANDO HORARIOS DE ATENCIÓN")
print("="*80)

# Verificar si ya existen horarios
horarios_existentes = Horario.objects.count()
if horarios_existentes > 0:
    print(f"ℹ️  Ya existen {horarios_existentes} horarios. Saltando creación.")
else:
    print("📅 Creando horarios de 8:00 AM a 6:00 PM (cada 30 minutos)...")
    
    # Crear horarios de 8:00 a 18:00 en intervalos de 30 minutos
    horarios_creados = 0
    hora_inicio = 8  # 8 AM
    hora_fin = 18    # 6 PM
    
    for hora in range(hora_inicio, hora_fin):
        for minuto in [0, 30]:
            try:
                horario_time = time(hour=hora, minute=minuto)
                horario, created = Horario.objects.get_or_create(
                    hora=horario_time,
                    defaults={
                        'empresa': empresa
                    }
                )
                if created:
                    horarios_creados += 1
            except Exception as e:
                print(f"❌ Error creando horario {hora}:{minuto:02d}: {e}")
    
    print(f"✅ Creados {horarios_creados} horarios disponibles")

# ============================================
# RESUMEN FINAL
# ============================================
print("\n" + "="*80)
print("📊 RESUMEN DE INICIALIZACIÓN")
print("="*80)

# Contar registros
roles_count = Tipodeusuario.objects.count()
estados_count = Estadodeconsulta.objects.count()
tipos_count = Tipodeconsulta.objects.count()
horarios_count = Horario.objects.count()

print(f"\n✅ Roles creados: {roles_count}")
print(f"✅ Estados creados: {estados_count}")
print(f"✅ Tipos de consulta creados: {tipos_count}")
print(f"✅ Horarios disponibles: {horarios_count}")

# Verificar si todo está correcto
problemas = []

if roles_count < 4:
    problemas.append("⚠️  Faltan roles (esperados: 4)")

if estados_count < 4:
    problemas.append("⚠️  Faltan estados de consulta (esperados: al menos 4)")

if tipos_count < 3:
    problemas.append("⚠️  Faltan tipos de consulta (esperados: al menos 3)")

if horarios_count < 10:
    problemas.append("⚠️  Pocos horarios disponibles (esperados: al menos 10)")

if problemas:
    print("\n⚠️  ADVERTENCIAS:")
    for problema in problemas:
        print(f"   {problema}")
else:
    print("\n✅ ¡SISTEMA INICIALIZADO CORRECTAMENTE!")

print("\n" + "="*80)
print("🎉 PRÓXIMOS PASOS:")
print("="*80)
print("1. ✅ Ya puedes registrar pacientes")
print("2. ✅ Crea odontólogos desde el panel de admin")
print("3. ✅ Agenda citas y gestiona consultas")
print("4. ✅ El sistema está listo para usar")
print("="*80)
