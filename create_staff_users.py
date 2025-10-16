"""
Script para crear usuarios STAFF (admin de Django) por cada clínica.
Estos usuarios podrán acceder a /admin en su subdominio.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Empresa, Usuario, Tipodeusuario

User = get_user_model()

print("=" * 70)
print("👤 CREAR USUARIOS STAFF PARA /admin POR CLÍNICA")
print("=" * 70)

# Obtener tipo de usuario Administrador
admin_tipo = Tipodeusuario.objects.get(id=1, rol='Administrador')

# Usuarios staff a crear (para acceso a /admin en cada subdominio)
staff_users = [
    {
        'empresa_subdomain': 'norte',
        'username': 'admin_norte',
        'email': 'admin_norte@system.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'Norte'
    },
    {
        'empresa_subdomain': 'sur',
        'username': 'admin_sur',
        'email': 'admin_sur@system.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'Sur'
    },
    {
        'empresa_subdomain': 'este',
        'username': 'admin_este',
        'email': 'admin_este@system.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'Este'
    },
]

print("\n📋 Creando usuarios STAFF para cada clínica...\n")

for staff_data in staff_users:
    try:
        empresa = Empresa.objects.get(subdomain=staff_data['empresa_subdomain'])
        print(f"🏥 {empresa.nombre} ({empresa.subdomain})")
        
        # Verificar si ya existe
        if User.objects.filter(username=staff_data['username']).exists():
            user = User.objects.get(username=staff_data['username'])
            user.set_password(staff_data['password'])
            user.is_staff = True
            user.is_active = True
            user.email = staff_data['email']
            user.save()
            print(f"   ✅ Usuario actualizado: {staff_data['username']}")
        else:
            # Crear usuario Django
            user = User.objects.create_user(
                username=staff_data['username'],
                email=staff_data['email'],
                password=staff_data['password'],
                first_name=staff_data['first_name'],
                last_name=staff_data['last_name'],
                is_staff=True,  # ← Puede acceder a /admin
                is_active=True,
                is_superuser=False  # No es superuser global
            )
            print(f"   ✅ Usuario creado: {staff_data['username']}")
        
        # Buscar o crear Usuario en tabla api
        usuario_exists = Usuario.objects.filter(
            correoelectronico=staff_data['email']
        ).exists()
        
        if not usuario_exists:
            usuario = Usuario.objects.create(
                nombre=staff_data['first_name'],
                apellido=staff_data['last_name'],
                correoelectronico=staff_data['email'],
                telefono='70000000',
                sexo='M',
                idtipousuario=admin_tipo,
                empresa=empresa,
                recibir_notificaciones=True
            )
            # Vincular
            user.usuario = usuario
            user.save()
            print(f"   ✅ Usuario vinculado con tabla api")
        
        print(f"   📧 Email: {staff_data['email']}")
        print(f"   🔑 Password: {staff_data['password']}")
        print(f"   🌐 URL: http://{empresa.subdomain}.localhost:8000/admin/")
        print()
        
    except Empresa.DoesNotExist:
        print(f"   ❌ Empresa '{staff_data['empresa_subdomain']}' no encontrada\n")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}\n")

print("=" * 70)
print("✅ USUARIOS STAFF CREADOS EXITOSAMENTE")
print("=" * 70)

print("\n🌐 ACCESO A DJANGO ADMIN POR CLÍNICA:")
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

print("\n💡 NOTA: Estos usuarios pueden acceder a /admin en su subdominio.")
print("   Solo verán los datos de su clínica (multi-tenancy).")
print("\n" + "=" * 70)
