"""
Diagnóstico: Verificar relación entre usuario Django y tenant
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Empresa, Usuario

print("=" * 70)
print("🔍 DIAGNÓSTICO: TENANT Y USUARIO ADMIN")
print("=" * 70)

# 1. Verificar usuario Django
username = "admin_norte"
try:
    django_user = User.objects.get(username=username)
    print(f"\n✅ Usuario Django encontrado: {django_user.username}")
    print(f"   Email: {django_user.email}")
    print(f"   is_staff: {django_user.is_staff}")
    print(f"   is_superuser: {django_user.is_superuser}")
except User.DoesNotExist:
    print(f"\n❌ Usuario Django '{username}' NO encontrado")
    exit(1)

# 2. Verificar si tiene Usuario (modelo de api)
try:
    usuario_api = Usuario.objects.get(user=django_user)
    print(f"\n✅ Usuario API encontrado:")
    print(f"   Nombre: {usuario_api.nombre}")
    print(f"   Email: {usuario_api.email}")
    print(f"   Empresa: {usuario_api.empresa.nombre if usuario_api.empresa else 'SIN EMPRESA'}")
    print(f"   Tipo Usuario: {usuario_api.idtipousuario}")
except Usuario.DoesNotExist:
    print(f"\n⚠️  Usuario API NO encontrado (esto puede ser el problema)")
    print(f"   El usuario Django '{username}' NO tiene relación con ninguna Empresa")
    usuario_api = None

# 3. Verificar empresa Norte
print("\n" + "=" * 70)
print("🏥 VERIFICAR EMPRESA NORTE")
print("=" * 70)
try:
    norte = Empresa.objects.get(subdomain='norte')
    print(f"\n✅ Empresa encontrada: {norte.nombre}")
    print(f"   Subdomain: {norte.subdomain}")
    print(f"   Activo: {norte.activo}")
except Empresa.DoesNotExist:
    print("\n❌ Empresa 'norte' NO encontrada")
    norte = None

# 4. Análisis del problema
print("\n" + "=" * 70)
print("📊 ANÁLISIS")
print("=" * 70)

if usuario_api:
    if usuario_api.empresa:
        print(f"\n✅ El usuario '{username}' ESTÁ vinculado a empresa: {usuario_api.empresa.nombre}")
        if norte and usuario_api.empresa.id == norte.id:
            print("✅ La empresa coincide con Norte - CORRECTO")
        else:
            print("⚠️  La empresa NO es Norte - PROBLEMA")
    else:
        print(f"\n❌ El usuario '{username}' NO tiene empresa asignada")
        print("   SOLUCIÓN: Asignar empresa Norte al Usuario API")
else:
    print(f"\n❌ El usuario '{username}' NO tiene registro en Usuario (tabla api_usuario)")
    print("   SOLUCIÓN: Crear Usuario API vinculado a este User y a empresa Norte")

print("\n" + "=" * 70)
print("🔧 SOLUCIÓN PROPUESTA")
print("=" * 70)

if not usuario_api:
    print("\nEjecutar:")
    print(f"""
from django.contrib.auth.models import User
from api.models import Usuario, Empresa

django_user = User.objects.get(username='{username}')
norte = Empresa.objects.get(subdomain='norte')

usuario = Usuario.objects.create(
    user=django_user,
    empresa=norte,
    nombre='Administrador Norte',
    email=django_user.email,
    telefono='',
    idtipousuario=1  # Administrador
)
print(f"✅ Usuario API creado: {{usuario}}")
    """)
elif usuario_api and not usuario_api.empresa:
    print("\nEjecutar:")
    print(f"""
from api.models import Usuario, Empresa

usuario = Usuario.objects.get(user__username='{username}')
norte = Empresa.objects.get(subdomain='norte')
usuario.empresa = norte
usuario.save()
print(f"✅ Empresa asignada a usuario")
    """)
else:
    print("\n✅ No se requiere acción - La configuración es correcta")
    print("   El problema puede estar en otro lugar (middleware, permisos)")

print("\n" + "=" * 70)
