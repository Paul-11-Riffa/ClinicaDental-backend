"""
Verificar tipos de usuario
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Tipodeusuario, Usuario

print("=" * 70)
print("📋 TIPOS DE USUARIO")
print("=" * 70)

for tipo in Tipodeusuario.objects.all():
    print(f"ID: {tipo.pk} - {tipo.tipousuario}")

print("\n" + "=" * 70)
print("🔍 VERIFICAR JUAN PÉREZ")
print("=" * 70)

juan = Usuario.objects.get(correoelectronico='juan.perez@norte.com')
print(f"\nJuan Pérez:")
print(f"  Usuario codigo: {juan.codigo}")
print(f"  idtipousuario FK: {juan.idtipousuario.pk}")
print(f"  Tipo: {juan.idtipousuario.tipousuario}")
