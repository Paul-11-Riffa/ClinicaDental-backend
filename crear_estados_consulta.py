"""
Crear estados de consulta para todas las empresas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Estadodeconsulta, Empresa

print("=" * 70)
print("🏥 CREAR ESTADOS DE CONSULTA")
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

# Crear estados para cada empresa
empresas = Empresa.objects.all()

for empresa in empresas:
    print(f"\n📌 Empresa: {empresa.nombre}")
    
    for estado_nombre in estados:
        # Verificar si ya existe
        existe = Estadodeconsulta.objects.filter(
            estado=estado_nombre,
            empresa=empresa
        ).exists()
        
        if existe:
            print(f"   ⚠️  '{estado_nombre}' ya existe - omitiendo")
        else:
            estado = Estadodeconsulta.objects.create(
                estado=estado_nombre,
                empresa=empresa
            )
            print(f"   ✅ Creado: '{estado_nombre}' (ID: {estado.id})")

print("\n" + "=" * 70)
print("📊 RESUMEN")
print("=" * 70)

for empresa in empresas:
    count = Estadodeconsulta.objects.filter(empresa=empresa).count()
    print(f"{empresa.nombre}: {count} estados")

print("\n✅ Estados de consulta creados exitosamente")
print("\nAhora intenta agendar una cita nuevamente desde el frontend")
