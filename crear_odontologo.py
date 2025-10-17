#!/usr/bin/env python
"""
Script para crear odontólogos en el sistema
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
from django.contrib.auth.hashers import make_password
from api.models import Usuario, Odontologo, Tipodeusuario, Empresa

print("="*80)
print("👨‍⚕️ CREAR ODONTÓLOGO EN EL SISTEMA")
print("="*80)

# Obtener empresa
empresas = Empresa.objects.all()
if not empresas.exists():
    print("\n❌ No hay empresas registradas. Primero registra una empresa.")
    sys.exit(1)

if empresas.count() == 1:
    empresa = empresas.first()
    print(f"\n✅ Usando empresa: {empresa.nombre} ({empresa.subdomain})")
else:
    print("\n📋 Empresas disponibles:")
    for idx, emp in enumerate(empresas, 1):
        print(f"   {idx}. {emp.nombre} ({emp.subdomain})")
    
    opcion = input("\nSelecciona empresa (número): ").strip()
    if opcion.isdigit() and 1 <= int(opcion) <= empresas.count():
        empresa = empresas[int(opcion) - 1]
    else:
        print("❌ Opción inválida")
        sys.exit(1)

# Verificar rol de odontólogo
try:
    rol_odontologo = Tipodeusuario.objects.get(id=3)  # Odontólogo
except Tipodeusuario.DoesNotExist:
    print("\n❌ Rol de Odontólogo no existe. Ejecuta: python inicializar_datos.py")
    sys.exit(1)

print("\n" + "="*80)
print("📝 DATOS DEL ODONTÓLOGO")
print("="*80)

# Solicitar datos
nombre = input("\n👤 Nombre: ").strip()
if not nombre:
    print("❌ El nombre es requerido")
    sys.exit(1)

apellido = input("👤 Apellido: ").strip()
if not apellido:
    print("❌ El apellido es requerido")
    sys.exit(1)

email = input("📧 Email: ").strip().lower()
if not email:
    print("❌ El email es requerido")
    sys.exit(1)

# Verificar si el email ya existe
User = get_user_model()
if User.objects.filter(username=email).exists():
    print(f"\n❌ Ya existe un usuario con el email: {email}")
    sys.exit(1)

if Usuario.objects.filter(correoelectronico=email).exists():
    print(f"\n❌ Ya existe un usuario con el email: {email}")
    sys.exit(1)

telefono = input("📱 Teléfono (opcional): ").strip()

print("\n🧑‍🤝‍🧑 Sexo:")
print("   1. Masculino")
print("   2. Femenino")
print("   3. Otro/Prefiero no decir")
sexo_opcion = input("Selecciona (1-3, Enter para omitir): ").strip()

sexo = None
if sexo_opcion == '1':
    sexo = 'M'
elif sexo_opcion == '2':
    sexo = 'F'
elif sexo_opcion == '3':
    sexo = 'O'

# Datos específicos de odontólogo
print("\n🦷 DATOS PROFESIONALES")
print("-"*80)

especialidad = input("🎓 Especialidad (ej: Ortodoncia, Endodoncia): ").strip()
if not especialidad:
    especialidad = "Odontología General"

nro_matricula = input("📜 Número de Matrícula Profesional: ").strip()

experiencia = input("💼 Experiencia profesional (ej: 5 años en ortodoncia): ").strip()

# Generar contraseña temporal
import secrets
import string

def generar_password():
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(12))

password_temporal = generar_password()

# Resumen
print("\n" + "="*80)
print("📋 RESUMEN")
print("="*80)
print(f"\n👤 Nombre completo: {nombre} {apellido}")
print(f"📧 Email: {email}")
print(f"📱 Teléfono: {telefono or 'N/A'}")
print(f"🧑‍🤝‍🧑 Sexo: {sexo or 'N/A'}")
print(f"🎓 Especialidad: {especialidad}")
print(f"📜 Matrícula: {nro_matricula or 'N/A'}")
print(f"💼 Experiencia: {experiencia or 'N/A'}")
print(f"🏢 Empresa: {empresa.nombre}")
print(f"🔐 Password temporal: {password_temporal}")

confirmar = input("\n⚠️  ¿Crear este odontólogo? (s/n): ").strip().lower()

if confirmar != 's':
    print("❌ Operación cancelada")
    sys.exit(0)

# Crear usuario en Django Auth
try:
    print("\n" + "="*80)
    print("🚀 CREANDO ODONTÓLOGO...")
    print("="*80)
    
    # 1. Usuario de Django (para login)
    django_user = User.objects.create(
        username=email,
        email=email,
        first_name=nombre,
        last_name=apellido,
        is_active=True,
        is_staff=True,  # Para acceso al admin
        password=make_password(password_temporal)
    )
    print(f"\n✅ Usuario Django creado: {django_user.username}")
    
    # 2. Usuario de la aplicación
    usuario = Usuario.objects.create(
        nombre=nombre,
        apellido=apellido,
        correoelectronico=email,
        telefono=telefono,
        sexo=sexo,
        idtipousuario=rol_odontologo,
        empresa=empresa,
        recibir_notificaciones=True,
        notificaciones_email=True,
        notificaciones_push=False
    )
    print(f"✅ Usuario de aplicación creado: ID {usuario.codigo}")
    
    # 3. Odontólogo (datos profesionales)
    odontologo = Odontologo.objects.create(
        codusuario=usuario,
        especialidad=especialidad,
        nromatricula=nro_matricula,
        experienciaprofesional=experiencia,
        empresa=empresa
    )
    print(f"✅ Odontólogo creado: Dr. {usuario.nombre} {usuario.apellido}")
    
    print("\n" + "="*80)
    print("🎉 ¡ODONTÓLOGO CREADO EXITOSAMENTE!")
    print("="*80)
    
    print(f"\n📋 CREDENCIALES DE ACCESO:")
    print(f"   URL: http://{empresa.subdomain}.localhost:5173/login")
    print(f"   Email: {email}")
    print(f"   Password: {password_temporal}")
    
    print(f"\n👨‍⚕️ INFORMACIÓN PROFESIONAL:")
    print(f"   Especialidad: {especialidad}")
    print(f"   Matrícula: {nro_matricula or 'N/A'}")
    print(f"   ID Odontólogo: {odontologo.codusuario_id}")
    
    print(f"\n💡 IMPORTANTE:")
    print(f"   1. Guarda estas credenciales en un lugar seguro")
    print(f"   2. El odontólogo debe cambiar su contraseña al primer login")
    print(f"   3. Puede acceder al panel de administración si es necesario")
    
    print("\n" + "="*80)
    
except Exception as e:
    print(f"\n❌ Error al crear odontólogo: {e}")
    import traceback
    traceback.print_exc()
    
    # Rollback: eliminar datos creados
    try:
        if 'django_user' in locals():
            django_user.delete()
            print("⚠️  Usuario Django eliminado (rollback)")
        if 'usuario' in locals():
            usuario.delete()
            print("⚠️  Usuario de aplicación eliminado (rollback)")
    except:
        pass
    
    sys.exit(1)
