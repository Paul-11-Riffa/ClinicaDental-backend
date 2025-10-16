"""
Crear estados de consulta GLOBALES (sin empresa específica)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Estadodeconsulta

print("=" * 70)
print("🏥 CREAR ESTADOS DE CONSULTA GLOBALES")
print("=" * 70)

# Estados estándar para una consulta dental
estados = [
    "Programada",      # Estado inicial cuando se agenda
    "Confirmada",      # Paciente confirmó asistencia
    "En Atención",     # Paciente en consultorio
    "Completada",      # Consulta finalizada exitosamente
    "Cancelada",       # Cancelada por paciente o clínica
    "No Show",         # Paciente no asistió
    "Reprogramada",    # Se movió a otra fecha/hora
]

print("\n📌 Creando estados globales (empresa=NULL)...\n")

for estado_nombre in estados:
    # Verificar si ya existe
    existe = Estadodeconsulta.objects.filter(
        estado=estado_nombre
    ).exists()
    
    if existe:
        estado_obj = Estadodeconsulta.objects.get(estado=estado_nombre)
        print(f"   ⚠️  '{estado_nombre}' ya existe (ID: {estado_obj.id}) - omitiendo")
    else:
        estado = Estadodeconsulta.objects.create(
            estado=estado_nombre,
            empresa=None  # Sin empresa específica (global)
        )
        print(f"   ✅ Creado: '{estado_nombre}' (ID: {estado.id})")

print("\n" + "=" * 70)
print("📊 RESUMEN")
print("=" * 70)

todos = Estadodeconsulta.objects.all()
print(f"\nTotal de estados: {todos.count()}\n")

for estado in todos:
    empresa_nombre = estado.empresa.nombre if estado.empresa else "GLOBAL"
    print(f"   ID {estado.id}: {estado.estado} - {empresa_nombre}")

print("\n✅ Estados de consulta creados exitosamente")
print("\n💡 Ahora el frontend puede usar:")
print("   - ID 1: Programada (estado inicial para nueva cita)")
print("   - ID 2: Confirmada")
print("   - ID 3: En Atención")
print("   - ID 4: Completada")
print("   - ID 5: Cancelada")
print("   - ID 6: No Show")
print("   - ID 7: Reprogramada")
