"""
Script de diagnóstico para verificar permisos de admin_norte
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("🔍 DIAGNÓSTICO DE PERMISOS - admin_norte")
print("=" * 70)

try:
    user = User.objects.get(username='admin_norte')
    
    print(f"\n✅ Usuario encontrado:")
    print(f"   Username: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   is_active: {user.is_active}")
    print(f"   is_staff: {user.is_staff}")
    print(f"   is_superuser: {user.is_superuser}")
    
    print(f"\n📊 Total de permisos: {user.get_all_permissions().__len__()}")
    
    # Verificar permisos específicos importantes
    important_perms = [
        'clinic.view_paciente',
        'clinic.add_paciente',
        'clinic.change_paciente',
        'clinic.delete_paciente',
        'clinic.view_consulta',
        'clinic.add_consulta',
    ]
    
    print(f"\n🔑 Permisos importantes:")
    for perm in important_perms:
        has_perm = user.has_perm(perm)
        status = "✅" if has_perm else "❌"
        print(f"   {status} {perm}")
    
    print(f"\n📝 RESULTADO:")
    if user.is_superuser and user.is_staff and user.is_active:
        print("   ✅ El usuario tiene TODOS los permisos necesarios")
        print("   ✅ Debería poder acceder al admin sin problemas")
        print("\n💡 Si aún ves 'No cuenta con permiso...':")
        print("   1. Cierra sesión en el navegador")
        print("   2. Borra cookies (Ctrl + Shift + Delete)")
        print("   3. Abre modo incógnito (Ctrl + Shift + N)")
        print("   4. Ve a http://norte.localhost:8000/admin/")
        print("   5. Login con admin_norte / admin123")
    else:
        print("   ❌ Faltan permisos. Ejecuta:")
        print("   python fix_admin_permissions.py")
        
except User.DoesNotExist:
    print("❌ Usuario 'admin_norte' no encontrado")
    print("\n💡 Crea el usuario con:")
    print("   python create_staff_users.py")

print("\n" + "=" * 70)
