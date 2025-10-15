#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from tenancy.models import Empresa

# Crear empresa de prueba
empresa, created = Empresa.objects.get_or_create(
    subdomain='test-clinic',
    defaults={
        'nombre': 'Clínica Dental Test',
        'activo': True
    }
)

if created:
    print(f"Empresa creada: {empresa.nombre} (subdomain: {empresa.subdomain})")
else:
    print(f"Empresa ya existe: {empresa.nombre} (subdomain: {empresa.subdomain})")

print(f"ID de la empresa: {empresa.id}")