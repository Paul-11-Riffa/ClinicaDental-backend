"""
Script para dar TODOS los permisos a los usuarios staff de cada clínica.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

print("=" * 70)
print("🔐 ASIGNAR PERMISOS A USUARIOS STAFF")
print("=" * 70)

staff_usernames = ['admin_norte', 'admin_sur', 'admin_este']

for username in staff_usernames:
    try:
        user = User.objects.get(username=username)
        
        print(f"\n👤 Usuario: {username}")
        print(f"   Email: {user.email}")
        print(f"   is_staff: {user.is_staff}")
        print(f"   is_superuser: {user.is_superuser}")
        
        # Opción 1: Hacer superuser (acceso total)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
        
        print(f"   ✅ Convertido a SUPERUSER")
        print(f"   ✅ Ahora tiene acceso completo a /admin")
        
    except User.DoesNotExist:
        print(f"❌ Usuario {username} no encontrado")

print("\n" + "=" * 70)
print("✅ PERMISOS ASIGNADOS EXITOSAMENTE")
print("=" * 70)

print("\n🌐 Ahora puedes acceder con permisos completos:")
print("\n🏥 Clínica Norte:")
print("   URL: http://norte.localhost:8000/admin/")
print("   Username: admin_norte")
print("   Password: admin123")

print("\n🏥 Clínica Sur:")
print("   URL: http://sur.localhost:8000/admin/")
print("   Username: admin_sur")
print("   Password: admin123")

print("\n🏥 Clínica Este:")
print("   URL: http://este.localhost:8000/admin/")
print("   Username: admin_este")
print("   Password: admin123")

print("\n💡 NOTA: Ahora son superusers y tienen acceso completo.")
print("   Pero el filtrado multi-tenant sigue activo (solo ven su clínica).")
print("\n" + "=" * 70)
