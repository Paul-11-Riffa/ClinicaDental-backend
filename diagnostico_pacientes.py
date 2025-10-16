"""
Verificar por qué /pacientes/ retorna 0 resultados
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Paciente, Usuario, Empresa

print("=" * 70)
print("🔍 DIAGNÓSTICO: ENDPOINT /pacientes/")
print("=" * 70)

# 1. Verificar empresa Norte
norte = Empresa.objects.get(subdomain='norte')
print(f"\n✅ Empresa Norte: {norte.nombre}")

# 2. Contar pacientes totales
total_pacientes = Paciente.objects.count()
print(f"\n📊 Total de pacientes en BD: {total_pacientes}")

# 3. Contar pacientes de Norte
pacientes_norte = Paciente.objects.filter(empresa=norte).count()
print(f"📊 Pacientes de Norte: {pacientes_norte}")

# 4. Listar todos los pacientes con detalles
print("\n" + "=" * 70)
print("📋 LISTA DE PACIENTES")
print("=" * 70)

for paciente in Paciente.objects.select_related('codusuario', 'empresa'):
    print(f"\nPaciente PK: {paciente.pk}")
    print(f"  Usuario codigo: {paciente.codusuario.codigo}")
    print(f"  Nombre: {paciente.codusuario.nombre} {paciente.codusuario.apellido}")
    print(f"  Email: {paciente.codusuario.correoelectronico}")
    print(f"  Empresa: {paciente.empresa.nombre if paciente.empresa else 'SIN EMPRESA'}")
    print(f"  Carnet: {paciente.carnetidentidad}")

# 5. Verificar específicamente Juan Pérez
print("\n" + "=" * 70)
print("🔍 VERIFICAR JUAN PÉREZ")
print("=" * 70)

try:
    usuario_juan = Usuario.objects.get(correoelectronico='juan.perez@norte.com')
    print(f"\n✅ Usuario Juan encontrado (codigo: {usuario_juan.codigo})")
    
    try:
        paciente_juan = Paciente.objects.get(codusuario=usuario_juan)
        print(f"✅ Perfil de Paciente existe")
        print(f"   PK: {paciente_juan.pk}")
        print(f"   Empresa: {paciente_juan.empresa.nombre if paciente_juan.empresa else 'NULL'}")
        print(f"   Carnet: {paciente_juan.carnetidentidad}")
        
        # Verificar si está en el filtro de Norte
        if paciente_juan.empresa == norte:
            print(f"\n✅ El paciente SÍ pertenece a empresa Norte")
        else:
            print(f"\n❌ PROBLEMA: El paciente NO pertenece a empresa Norte")
            print(f"   Empresa actual: {paciente_juan.empresa.nombre if paciente_juan.empresa else 'NULL'}")
            
    except Paciente.DoesNotExist:
        print(f"❌ NO existe perfil de Paciente para este usuario")
        
except Usuario.DoesNotExist:
    print(f"❌ Usuario Juan Pérez no encontrado")

print("\n" + "=" * 70)
print("🔧 ANÁLISIS")
print("=" * 70)

if total_pacientes == 0:
    print("\n❌ No hay pacientes en la base de datos")
    print("   Ejecutar: python create_sample_data.py")
elif pacientes_norte == 0:
    print("\n❌ Hay pacientes pero ninguno pertenece a empresa Norte")
    print("   Problema: campo 'empresa' NULL o apuntando a otra empresa")
else:
    print(f"\n✅ Hay {pacientes_norte} paciente(s) de Norte")
    print("   El problema puede estar en el endpoint del backend")
