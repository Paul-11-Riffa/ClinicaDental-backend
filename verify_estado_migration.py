"""
Verify estado migration - check that all consultas have the new estado field populated
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Consulta

print("\n" + "="*60)
print("VERIFICACIÓN DE MIGRACIÓN DE ESTADOS")
print("="*60 + "\n")

consultas = Consulta.objects.select_related('idestadoconsulta').all()

print(f"Total consultas: {consultas.count()}\n")

for consulta in consultas:
    old_estado = consulta.idestadoconsulta.estado if consulta.idestadoconsulta else "None"
    new_estado = consulta.estado if consulta.estado else "None"
    
    # Color code the result
    if new_estado != "None":
        status = "✅"
    else:
        status = "❌"
    
    print(f"{status} Consulta #{consulta.id}:")
    print(f"   - Old FK estado: {old_estado}")
    print(f"   - New CharField: {new_estado}")
    print(f"   - Fecha: {consulta.fecha}")
    print()

# Check for any nulls
null_count = Consulta.objects.filter(estado__isnull=True).count()
if null_count == 0:
    print("✅ ¡Perfecto! Todas las consultas tienen el nuevo campo 'estado' poblado")
else:
    print(f"⚠️  Advertencia: {null_count} consultas sin estado")

print("\n" + "="*60)
