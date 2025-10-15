#!/usr/bin/env python
"""
Script para crear datos de prueba del sistema multi-tenant.
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from tenancy.models import Empresa
from users.models import Usuario, Tipodeusuario

def create_test_data():
    """Crear datos de prueba para el sistema"""
    
    print("🏗️  Creando datos de prueba...")
    
    # 1. Crear empresas de prueba
    empresas_data = [
        {
            'nombre': 'Clínica Dental Norte',
            'subdomain': 'norte',
            'activo': True
        },
        {
            'nombre': 'Sonrisas del Sur',
            'subdomain': 'sur', 
            'activo': True
        },
        {
            'nombre': 'Centro Dental Este',
            'subdomain': 'este',
            'activo': True
        }
    ]
    
    empresas_creadas = []
    for data in empresas_data:
        empresa, created = Empresa.objects.get_or_create(
            subdomain=data['subdomain'],
            defaults=data
        )
        if created:
            print(f"✅ Empresa creada: {empresa.nombre} ({empresa.subdomain})")
        else:
            print(f"📍 Empresa existente: {empresa.nombre} ({empresa.subdomain})")
        empresas_creadas.append(empresa)
    
    # 2. Crear tipos de usuario
    tipos_usuario = [
        {'rol': 'Administrador', 'descripcion': 'Acceso completo al sistema'},
        {'rol': 'Recepcionista', 'descripcion': 'Gestión de citas y pacientes'},
        {'rol': 'Odontólogo', 'descripcion': 'Profesional dental'},
        {'rol': 'Paciente', 'descripcion': 'Usuario final del sistema'},
    ]
    
    for tipo_data in tipos_usuario:
        tipo, created = Tipodeusuario.objects.get_or_create(
            rol=tipo_data['rol'],
            empresa=None,  # Tipos globales
            defaults=tipo_data
        )
        if created:
            print(f"✅ Tipo de usuario creado: {tipo.rol}")
        else:
            print(f"📍 Tipo de usuario existente: {tipo.rol}")
    
    print("\n🎉 Datos de prueba creados exitosamente!")
    print("\n📋 Resumen:")
    print(f"   • Empresas: {Empresa.objects.count()}")
    print(f"   • Tipos de usuario: {Tipodeusuario.objects.count()}")
    
    print("\n🌐 URLs de prueba:")
    for empresa in empresas_creadas:
        print(f"   • {empresa.nombre}: http://{empresa.subdomain}.localhost:8000/")
        print(f"     - Header: X-Tenant-Subdomain: {empresa.subdomain}")
    
    print("\n📝 Para probar multi-tenancy:")
    print("   curl -H 'X-Tenant-Subdomain: norte' http://localhost:8000/")
    print("   curl -H 'X-Tenant-Subdomain: sur' http://localhost:8000/")

if __name__ == "__main__":
    create_test_data()