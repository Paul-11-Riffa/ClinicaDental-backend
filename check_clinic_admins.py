"""
Script para verificar usuarios administradores de cada clínica.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Tipodeusuario, Empresa
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 70)
print("📋 USUARIOS ADMINISTRADORES POR CLÍNICA")
print("=" * 70)

# Buscar el tipo de usuario "administrador"
try:
    admin_tipo = Tipodeusuario.objects.get(rol='administrador')
    print(f"\n✅ Tipo de usuario encontrado: {admin_tipo.rol} (ID: {admin_tipo.id})")
except Tipodeusuario.DoesNotExist:
    print("\n❌ No existe el tipo de usuario 'administrador'")
    print("\nTipos de usuario disponibles:")
    for tipo in Tipodeusuario.objects.all():
        print(f"  - {tipo.rol} (ID: {tipo.id}) - Empresa: {tipo.empresa}")
    exit()

# Buscar todos los usuarios administradores
admins = Usuario.objects.filter(idtipousuario=admin_tipo)
print(f"\n📊 Total de administradores de clínicas: {admins.count()}")

if admins.count() == 0:
    print("\n⚠️  NO HAY USUARIOS ADMINISTRADORES CREADOS")
    print("\nVerificando usuarios por clínica:")
    
    empresas = Empresa.objects.all()
    for empresa in empresas:
        print(f"\n🏥 {empresa.nombre} ({empresa.subdomain})")
        usuarios = Usuario.objects.filter(empresa=empresa)
        print(f"   Total usuarios: {usuarios.count()}")
        for u in usuarios:
            print(f"   - {u.nombre} {u.apellido} ({u.correoelectronico})")
            print(f"     Tipo: {u.idtipousuario.rol}")
else:
    # Listar administradores por clínica
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\n{'=' * 70}")
        print(f"🏥 {empresa.nombre.upper()} ({empresa.subdomain})")
        print(f"{'=' * 70}")
        
        empresa_admins = admins.filter(empresa=empresa)
        
        if empresa_admins.count() == 0:
            print("   ⚠️  NO HAY ADMINISTRADORES para esta clínica")
        else:
            for admin in empresa_admins:
                print(f"\n   ✅ Administrador encontrado:")
                print(f"      Nombre: {admin.nombre} {admin.apellido}")
                print(f"      Email: {admin.correoelectronico}")
                print(f"      Teléfono: {admin.telefono}")
                
                # Verificar si tiene cuenta de Django Auth
                try:
                    django_user = User.objects.get(email=admin.correoelectronico)
                    print(f"      Django User ID: {django_user.id}")
                    print(f"      Username: {django_user.username}")
                except User.DoesNotExist:
                    print(f"      ⚠️  No tiene cuenta en Django Auth")
                except User.MultipleObjectsReturned:
                    print(f"      ⚠️  Múltiples cuentas en Django Auth (duplicado)")

print("\n" + "=" * 70)
print("\n📝 RESUMEN:")
print(f"   - Total empresas/clínicas: {Empresa.objects.count()}")
print(f"   - Total usuarios administradores: {admins.count()}")
print(f"   - Total usuarios Django Auth: {User.objects.count()}")
print("\n" + "=" * 70)
