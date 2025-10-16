"""
Script para resetear contraseñas de administradores del panel Django Admin.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Resetear contraseñas de los administradores
admins = [
    {'email': 'admin@gmail.com', 'password': 'admin123'},
    {'email': 'admin2@gmail.com', 'password': 'admin123'},
]

print("🔐 Reseteando contraseñas de administradores...\n")

for admin_data in admins:
    try:
        user = User.objects.get(email=admin_data['email'])
        user.set_password(admin_data['password'])
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        print(f"✅ {admin_data['email']}")
        print(f"   Contraseña: {admin_data['password']}")
        print(f"   Staff: {user.is_staff} | Superuser: {user.is_superuser}\n")
    except User.DoesNotExist:
        print(f"❌ Usuario {admin_data['email']} no existe\n")

print("\n✅ Proceso completado!")
print("\n🌐 Ahora puedes acceder al admin en:")
print("   http://localhost:8000/admin/")
print("\nCredenciales:")
print("   Email: admin@gmail.com")
print("   Password: admin123")
