"""
Script para crear usuarios administradores para cada clínica.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Tipodeusuario, Empresa
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("👤 CREANDO USUARIOS ADMINISTRADORES PARA CADA CLÍNICA")
print("=" * 70)

# Obtener el tipo de usuario Administrador
admin_tipo = Tipodeusuario.objects.get(id=1, rol='Administrador')
print(f"\n✅ Tipo de usuario: {admin_tipo.rol} (ID: {admin_tipo.id})")

# Obtener todas las clínicas
empresas = Empresa.objects.all()
print(f"\n📊 Total de clínicas: {empresas.count()}\n")

# Datos de administradores a crear
admins_data = [
    {
        'empresa_subdomain': 'norte',
        'nombre': 'Admin',
        'apellido': 'Norte',
        'email': 'admin@norte.com',
        'telefono': '70000000',
        'sexo': 'M',
        'password': 'norte123'
    },
    {
        'empresa_subdomain': 'sur',
        'nombre': 'Admin',
        'apellido': 'Sur',
        'email': 'admin@sur.com',
        'telefono': '71000000',
        'sexo': 'F',
        'password': 'sur123'
    },
    {
        'empresa_subdomain': 'este',
        'nombre': 'Admin',
        'apellido': 'Este',
        'email': 'admin@este.com',
        'telefono': '72000000',
        'sexo': 'M',
        'password': 'este123'
    },
]

for admin_data in admins_data:
    try:
        # Buscar la empresa
        empresa = Empresa.objects.get(subdomain=admin_data['empresa_subdomain'])
        print(f"🏥 {empresa.nombre} ({empresa.subdomain})")
        
        # Verificar si ya existe un administrador
        existing_admin = Usuario.objects.filter(
            empresa=empresa,
            idtipousuario=admin_tipo
        ).first()
        
        if existing_admin:
            print(f"   ⚠️  Ya existe administrador: {existing_admin.correoelectronico}")
            continue
        
        # Verificar si el email ya existe
        if Usuario.objects.filter(correoelectronico=admin_data['email']).exists():
            print(f"   ⚠️  Email {admin_data['email']} ya existe")
            continue
        
        # Crear Usuario (tabla api)
        usuario = Usuario.objects.create(
            nombre=admin_data['nombre'],
            apellido=admin_data['apellido'],
            correoelectronico=admin_data['email'],
            telefono=admin_data['telefono'],
            sexo=admin_data['sexo'],
            idtipousuario=admin_tipo,
            empresa=empresa,
            recibir_notificaciones=True,
            notificaciones_email=True,
            notificaciones_push=False
        )
        print(f"   ✅ Usuario creado: {usuario.correoelectronico} (Código: {usuario.codigo})")
        
        # Crear cuenta de Django Auth
        django_user = User.objects.create_user(
            username=admin_data['email'],
            email=admin_data['email'],
            password=admin_data['password'],
            first_name=admin_data['nombre'],
            last_name=admin_data['apellido'],
            is_active=True,
            is_staff=False,  # No es staff de Django Admin
            is_superuser=False  # No es superuser de Django
        )
        
        # Vincular Usuario con Django User
        django_user.usuario = usuario
        django_user.save()
        
        print(f"   ✅ Cuenta Django Auth creada")
        print(f"   📧 Email: {admin_data['email']}")
        print(f"   🔑 Password: {admin_data['password']}")
        print()
        
    except Empresa.DoesNotExist:
        print(f"   ❌ Empresa '{admin_data['empresa_subdomain']}' no encontrada")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("=" * 70)
print("\n📝 RESUMEN DE ADMINISTRADORES POR CLÍNICA:")
print("=" * 70)

for empresa in empresas:
    admins = Usuario.objects.filter(empresa=empresa, idtipousuario=admin_tipo)
    print(f"\n🏥 {empresa.nombre} ({empresa.subdomain})")
    if admins.count() == 0:
        print("   ⚠️  Sin administrador")
    else:
        for admin in admins:
            print(f"   ✅ {admin.nombre} {admin.apellido} - {admin.correoelectronico}")

print("\n" + "=" * 70)
print("✅ ¡Proceso completado!")
print("\nAhora puedes hacer login como administrador en cada clínica:")
print("\n🏥 Clínica Norte:")
print("   Email: admin@norte.com")
print("   Password: norte123")
print("\n🏥 Clínica Sur:")
print("   Email: admin@sur.com")
print("   Password: sur123")
print("\n🏥 Clínica Este:")
print("   Email: admin@este.com")
print("   Password: este123")
print("\n" + "=" * 70)
