"""
Test para verificar permisos de admin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.admin.sites import site

print("=" * 70)
print("🔍 VERIFICACIÓN DE ADMIN SITE")
print("=" * 70)

# Obtener usuario
user = User.objects.get(username='admin_norte')
print(f"\n✅ Usuario: {user.username}")
print(f"   is_superuser: {user.is_superuser}")
print(f"   is_staff: {user.is_staff}")
print(f"   is_active: {user.is_active}")

# Verificar modelos registrados en admin
print("\n" + "=" * 70)
print("📋 MODELOS REGISTRADOS EN ADMIN")
print("=" * 70)

registered = site._registry
print(f"\nTotal de modelos registrados: {len(registered)}\n")

for model, model_admin in registered.items():
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    verbose_name = model._meta.verbose_name
    
    print(f"📦 {app_label}.{model_name}")
    print(f"   Nombre: {verbose_name}")
    print(f"   Admin Class: {model_admin.__class__.__name__}")
    
    # Verificar has_module_permission
    class FakeRequest:
        def __init__(self, user):
            self.user = user
    
    fake_request = FakeRequest(user)
    has_perm = model_admin.has_module_permission(fake_request)
    
    print(f"   has_module_permission: {has_perm}")
    print()

print("=" * 70)
print("🔍 ANÁLISIS")
print("=" * 70)

# Contar cuántos tienen permiso
total = len(registered)
with_permission = sum(
    1 for model, model_admin in registered.items() 
    if model_admin.has_module_permission(FakeRequest(user))
)

print(f"\nModelos con permiso: {with_permission}/{total}")

if with_permission == 0:
    print("\n❌ PROBLEMA: Ningún modelo tiene permiso")
    print("   Esto indica que has_module_permission está retornando False")
elif with_permission < total:
    print(f"\n⚠️  ADVERTENCIA: Solo {with_permission} de {total} modelos tienen permiso")
else:
    print(f"\n✅ CORRECTO: Todos los modelos tienen permiso")
