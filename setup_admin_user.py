"""
Script para resetear contraseñas de SUPERUSERS para Django Admin (/admin)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("🔐 RESETEAR CONTRASEÑAS DE SUPERUSERS PARA /admin")
print("=" * 70)

# Resetear contraseña del superuser principal
try:
    # Usar el primero que encontremos con is_superuser=True
    admin = User.objects.filter(is_superuser=True, is_staff=True).first()
    
    if admin:
        # Resetear contraseña
        admin.set_password('admin')
        admin.username = 'admin'
        admin.email = 'admin@system.com'
        admin.is_active = True
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        
        print("\n✅ SUPERUSER CONFIGURADO:")
        print(f"   ID: {admin.id}")
        print(f"   Username: {admin.username}")
        print(f"   Email: {admin.email}")
        print(f"   Password: admin")
        print(f"   Is Staff: {admin.is_staff}")
        print(f"   Is Superuser: {admin.is_superuser}")
        
    else:
        print("❌ No se encontró ningún superuser")
        print("\nCreando nuevo superuser...")
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@system.com',
            password='admin'
        )
        print(f"\n✅ SUPERUSER CREADO:")
        print(f"   Username: admin")
        print(f"   Email: admin@system.com")
        print(f"   Password: admin")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nIntentando crear superuser nuevo...")
    try:
        # Eliminar duplicados y crear uno nuevo
        User.objects.filter(username='admin').delete()
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@system.com',
            password='admin'
        )
        print(f"\n✅ SUPERUSER CREADO:")
        print(f"   Username: admin")
        print(f"   Email: admin@system.com")
        print(f"   Password: admin")
    except Exception as e2:
        print(f"❌ Error al crear: {e2}")

print("\n" + "=" * 70)
print("🌐 ACCESO AL PANEL DE ADMINISTRACIÓN:")
print("=" * 70)
print("\nURL: http://localhost:8000/admin/")
print("\nCREDENCIALES:")
print("   Username: admin")
print("   Password: admin")
print("\n" + "=" * 70)
