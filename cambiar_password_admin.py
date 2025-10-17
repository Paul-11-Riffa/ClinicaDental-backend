#!/usr/bin/env python
"""
Script para cambiar contraseña de usuarios admin
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

User = get_user_model()

print("="*80)
print("🔐 CAMBIAR CONTRASEÑA DE USUARIO ADMIN")
print("="*80)

# Listar usuarios staff
staff_users = User.objects.filter(is_staff=True)

if not staff_users.exists():
    print("\n❌ No hay usuarios con permisos de staff")
    print("\nCrea un superusuario con:")
    print("   python manage.py createsuperuser")
    sys.exit(1)

print(f"\n👥 USUARIOS CON ACCESO AL ADMIN: {staff_users.count()}")
print()

for idx, user in enumerate(staff_users, 1):
    print(f"{idx}. {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Superusuario: {'✅ Sí' if user.is_superuser else '❌ No'}")
    print(f"   Activo: {'✅ Sí' if user.is_active else '❌ No'}")
    print()

print("="*80)
print("🔧 CAMBIAR CONTRASEÑA")
print("="*80)

# Seleccionar usuario
if staff_users.count() == 1:
    user_selected = staff_users.first()
    print(f"\n✅ Usuario seleccionado: {user_selected.username}")
else:
    print("\n¿Qué usuario deseas modificar?")
    opcion = input(f"Selecciona (1-{staff_users.count()}): ").strip()
    
    if not opcion.isdigit() or int(opcion) < 1 or int(opcion) > staff_users.count():
        print("❌ Opción inválida")
        sys.exit(1)
    
    user_selected = list(staff_users)[int(opcion) - 1]
    print(f"\n✅ Usuario seleccionado: {user_selected.username}")

# Ingresar nueva contraseña
print("\n" + "="*80)
nueva_password = input("Nueva contraseña (mínimo 8 caracteres): ").strip()

if len(nueva_password) < 8:
    print("❌ La contraseña debe tener al menos 8 caracteres")
    sys.exit(1)

confirmar_password = input("Confirma la contraseña: ").strip()

if nueva_password != confirmar_password:
    print("❌ Las contraseñas no coinciden")
    sys.exit(1)

# Cambiar contraseña
user_selected.set_password(nueva_password)
user_selected.save()

print("\n" + "="*80)
print("✅ CONTRASEÑA CAMBIADA EXITOSAMENTE")
print("="*80)
print(f"\n👤 Usuario: {user_selected.username}")
print(f"📧 Email: {user_selected.email}")
print(f"🔐 Nueva contraseña: {nueva_password}")
print()
print("🚀 Accede al admin en:")
print("   http://localhost:8000/admin/")
print()
print(f"   Usuario: {user_selected.username}")
print(f"   Contraseña: {nueva_password}")
print("="*80)
