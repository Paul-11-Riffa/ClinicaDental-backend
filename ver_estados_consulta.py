"""
Verificar estados de consulta
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Estadodeconsulta, Empresa

print("=" * 70)
print("📋 ESTADOS DE CONSULTA")
print("=" * 70)

norte = Empresa.objects.get(subdomain='norte')

print(f"\n✅ Estados en empresa Norte:")
estados_norte = Estadodeconsulta.objects.filter(empresa=norte)
for e in estados_norte:
    print(f"   ID {e.id}: {e.estado}")

print(f"\nTotal en Norte: {estados_norte.count()}")

print("\n" + "=" * 70)
print("📋 TODOS LOS ESTADOS (sin filtro)")
print("=" * 70)

todos = Estadodeconsulta.objects.all()
for e in todos:
    empresa_nombre = e.empresa.nombre if e.empresa else "NULL"
    print(f"   ID {e.id}: {e.estado} - Empresa: {empresa_nombre}")

print(f"\nTotal global: {todos.count()}")

if todos.count() == 0:
    print("\n❌ NO HAY ESTADOS DE CONSULTA EN LA BASE DE DATOS")
    print("   Necesitas crearlos con el script create_sample_data.py")
