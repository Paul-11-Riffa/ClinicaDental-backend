"""
Crear el perfil de Paciente para Juan Pérez
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Paciente, Empresa
from datetime import date

print("=" * 70)
print("🏥 CREAR PERFIL DE PACIENTE PARA JUAN PÉREZ")
print("=" * 70)

# 1. Obtener el Usuario Juan Pérez
try:
    usuario_juan = Usuario.objects.get(correoelectronico='juan.perez@norte.com')
    print(f"\n✅ Usuario encontrado:")
    print(f"   Codigo: {usuario_juan.codigo}")
    print(f"   Nombre: {usuario_juan.nombre} {usuario_juan.apellido}")
    print(f"   Email: {usuario_juan.correoelectronico}")
    print(f"   Empresa: {usuario_juan.empresa.nombre}")
except Usuario.DoesNotExist:
    print("\n❌ Usuario Juan Pérez no encontrado")
    exit(1)

# 2. Verificar si ya tiene perfil de Paciente
try:
    paciente_existente = Paciente.objects.get(codusuario=usuario_juan)
    print(f"\n⚠️  Ya existe un perfil de Paciente para este usuario:")
    print(f"   Paciente ID: {paciente_existente.codigo}")
    print(f"   Carnet: {paciente_existente.carnetidentidad}")
    print(f"\n   No se requiere acción.")
    exit(0)
except Paciente.DoesNotExist:
    print("\n✅ No existe perfil de Paciente - Procediendo a crear...")

# 3. Crear el perfil de Paciente
paciente = Paciente.objects.create(
    codusuario=usuario_juan,
    empresa=usuario_juan.empresa,
    carnetidentidad='12345678',  # CI de ejemplo
    fechanacimiento=date(1990, 5, 15),  # Fecha de ejemplo
    direccion='Av. Principal #123, Norte',
    genero='M',  # M = Masculino
    telefono_emergencia='555-5678',
    contacto_emergencia='María Pérez (hermana)',
    alergias='Ninguna',
    enfermedades_cronicas='Ninguna',
    grupo_sanguineo='O+',
    observaciones='Paciente creado automáticamente para testing'
)

print("\n" + "=" * 70)
print("✅ PACIENTE CREADO EXITOSAMENTE")
print("=" * 70)
print(f"Paciente ID: {paciente.codigo}")
print(f"Nombre: {usuario_juan.nombre} {usuario_juan.apellido}")
print(f"Carnet: {paciente.carnetidentidad}")
print(f"Fecha Nac: {paciente.fechanacimiento}")
print(f"Empresa: {paciente.empresa.nombre}")
print(f"Teléfono emergencia: {paciente.telefono_emergencia}")
print(f"Contacto emergencia: {paciente.contacto_emergencia}")

print("\n" + "=" * 70)
print("🎯 SIGUIENTE PASO")
print("=" * 70)
print("Refresca el frontend (F5) y el error debería desaparecer.")
print("El usuario Juan Pérez ahora tiene perfil completo de paciente.")
