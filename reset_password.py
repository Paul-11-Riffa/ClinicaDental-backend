#!/usr/bin/env python
"""
Script para resetear password de un usuario
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

print("="*70)
print("🔑 RESETEAR PASSWORD DE USUARIO")
print("="*70)

User = get_user_model()

# Mostrar usuarios disponibles
print("\n📋 USUARIOS DISPONIBLES:")
print("-"*70)
usuarios = User.objects.all().order_by('username')

if not usuarios.exists():
    print("❌ No hay usuarios registrados")
    sys.exit(1)

for idx, user in enumerate(usuarios, 1):
    print(f"{idx}. {user.username} ({user.first_name} {user.last_name})")

print("-"*70)

# Solicitar email
email = input("\n✏️  Email del usuario (o número): ").strip()

# Si ingresó un número, obtener el email de la lista
if email.isdigit():
    idx = int(email) - 1
    if 0 <= idx < len(usuarios):
        user = usuarios[idx]
        email = user.username
    else:
        print("❌ Número inválido")
        sys.exit(1)
else:
    email = email.lower()

# Solicitar nueva contraseña
new_password = input("🔐 Nueva contraseña: ").strip()

if not new_password or len(new_password) < 6:
    print("❌ La contraseña debe tener al menos 6 caracteres")
    sys.exit(1)

# Confirmar
confirmar = input(f"\n⚠️  ¿Resetear password de '{email}'? (s/n): ").strip().lower()

if confirmar != 's':
    print("❌ Operación cancelada")
    sys.exit(0)

# Resetear password
try:
    user = User.objects.get(username=email)
    user.set_password(new_password)
    user.save()
    
    print("\n" + "="*70)
    print("✅ PASSWORD ACTUALIZADO EXITOSAMENTE")
    print("="*70)
    print(f"\n👤 Usuario:   {user.username}")
    print(f"🔐 Password:  {new_password}")
    print(f"📧 Email:     {user.email}")
    print(f"👔 Nombre:    {user.first_name} {user.last_name}")
    
    # Buscar empresa asociada
    from api.models import Usuario as AppUsuario
    try:
        app_user = AppUsuario.objects.get(correoelectronico=email)
        if app_user.empresa:
            print(f"\n🏢 Empresa:   {app_user.empresa.nombre}")
            print(f"🌐 Subdomain: {app_user.empresa.subdomain}")
            print(f"\n🔗 URL de acceso:")
            print(f"   Localhost:  http://{app_user.empresa.subdomain}.localhost:5173/login")
            print(f"   Producción: https://{app_user.empresa.subdomain}.notificct.dpdns.org/login")
    except AppUsuario.DoesNotExist:
        pass
    
    print("\n" + "="*70)
    print("💡 TIP: Ahora puedes hacer login con estas credenciales")
    print("="*70)
    
except User.DoesNotExist:
    print(f"\n❌ Usuario no encontrado: {email}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
