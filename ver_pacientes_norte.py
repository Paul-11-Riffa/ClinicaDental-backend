"""
Verificar pacientes de Norte
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Paciente, Empresa

norte = Empresa.objects.get(subdomain='norte')
pacientes = Paciente.objects.filter(empresa=norte)

print(f"📋 Pacientes en Norte:")
for p in pacientes:
    print(f"  ID: {p.codusuario_id} - {p.codusuario.nombre} {p.codusuario.apellido}")

print(f"\nTotal: {pacientes.count()}")
