#!/usr/bin/env python
"""
Script para asignar empresa a usuarios sin empresa
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from api.models import Usuario, Paciente, Odontologo, Recepcionista, Empresa

print("="*80)
print("🏢 ASIGNAR EMPRESA A USUARIOS")
print("="*80)

# Obtener empresas disponibles
empresas = Empresa.objects.all()

if not empresas.exists():
    print("\n❌ No hay empresas registradas en el sistema")
    sys.exit(1)

print(f"\n📋 Empresas disponibles:")
for idx, emp in enumerate(empresas, 1):
    usuarios_count = Usuario.objects.filter(empresa=emp).count()
    print(f"   {idx}. {emp.nombre} ({emp.subdomain})")
    print(f"      Usuarios: {usuarios_count}")
    print(f"      Activa: {'✅ Sí' if emp.activo else '❌ No'}")
    print()

# Buscar usuarios sin empresa
usuarios_sin_empresa = Usuario.objects.filter(empresa__isnull=True)

if not usuarios_sin_empresa.exists():
    print("✅ Todos los usuarios tienen empresa asignada")
    sys.exit(0)

print("="*80)
print(f"⚠️  USUARIOS SIN EMPRESA: {usuarios_sin_empresa.count()}")
print("="*80)

for usuario in usuarios_sin_empresa:
    print(f"\n👤 {usuario.nombre} {usuario.apellido}")
    print(f"   Email: {usuario.correoelectronico}")
    print(f"   Rol: {usuario.idtipousuario.rol}")
    print(f"   Empresa actual: Sin empresa")

# Asignar empresa
print("\n" + "="*80)
print("🔧 ASIGNAR EMPRESA")
print("="*80)

if empresas.count() == 1:
    empresa_seleccionada = empresas.first()
    print(f"\n✅ Solo hay una empresa: {empresa_seleccionada.nombre}")
    confirmar = input(f"¿Asignar todos los usuarios a {empresa_seleccionada.nombre}? (s/n): ").strip().lower()
    
    if confirmar == 's':
        for usuario in usuarios_sin_empresa:
            usuario.empresa = empresa_seleccionada
            usuario.save()
            print(f"✅ {usuario.correoelectronico} → {empresa_seleccionada.nombre}")
            
            # Actualizar también el perfil específico (Paciente, Odontólogo, etc.)
            try:
                if usuario.idtipousuario.id == 2:  # Paciente
                    paciente = Paciente.objects.get(codusuario=usuario)
                    paciente.empresa = empresa_seleccionada
                    paciente.save()
                    print(f"   ✅ Perfil de Paciente actualizado")
                elif usuario.idtipousuario.id == 3:  # Odontólogo
                    odontologo = Odontologo.objects.get(codusuario=usuario)
                    odontologo.empresa = empresa_seleccionada
                    odontologo.save()
                    print(f"   ✅ Perfil de Odontólogo actualizado")
                elif usuario.idtipousuario.id == 4:  # Recepcionista
                    recep = Recepcionista.objects.get(codusuario=usuario)
                    recep.empresa = empresa_seleccionada
                    recep.save()
                    print(f"   ✅ Perfil de Recepcionista actualizado")
            except Exception as e:
                print(f"   ⚠️  No se pudo actualizar perfil específico: {e}")
        
        print("\n✅ Todos los usuarios han sido asignados a la empresa")
    else:
        print("❌ Operación cancelada")
else:
    # Múltiples empresas: asignar manualmente
    print("\nAsigna empresa a cada usuario:")
    
    for usuario in usuarios_sin_empresa:
        print(f"\n{'='*80}")
        print(f"👤 Usuario: {usuario.nombre} {usuario.apellido}")
        print(f"   Email: {usuario.correoelectronico}")
        print(f"   Rol: {usuario.idtipousuario.rol}")
        print(f"\n📋 Selecciona empresa:")
        
        for idx, emp in enumerate(empresas, 1):
            print(f"   {idx}. {emp.nombre} ({emp.subdomain})")
        
        print(f"   0. Saltar este usuario")
        
        opcion = input("\nEmpresa (número): ").strip()
        
        if opcion == '0':
            print("⏭️  Usuario omitido")
            continue
        
        if opcion.isdigit() and 1 <= int(opcion) <= empresas.count():
            empresa_seleccionada = empresas[int(opcion) - 1]
            usuario.empresa = empresa_seleccionada
            usuario.save()
            print(f"✅ {usuario.correoelectronico} → {empresa_seleccionada.nombre}")
            
            # Actualizar perfil específico
            try:
                if usuario.idtipousuario.id == 2:  # Paciente
                    paciente = Paciente.objects.get(codusuario=usuario)
                    paciente.empresa = empresa_seleccionada
                    paciente.save()
                    print(f"   ✅ Perfil de Paciente actualizado")
                elif usuario.idtipousuario.id == 3:  # Odontólogo
                    odontologo = Odontologo.objects.get(codusuario=usuario)
                    odontologo.empresa = empresa_seleccionada
                    odontologo.save()
                    print(f"   ✅ Perfil de Odontólogo actualizado")
                elif usuario.idtipousuario.id == 4:  # Recepcionista
                    recep = Recepcionista.objects.get(codusuario=usuario)
                    recep.empresa = empresa_seleccionada
                    recep.save()
                    print(f"   ✅ Perfil de Recepcionista actualizado")
            except Exception as e:
                print(f"   ⚠️  No se pudo actualizar perfil específico: {e}")
        else:
            print("❌ Opción inválida, usuario omitido")

print("\n" + "="*80)
print("📊 RESUMEN FINAL")
print("="*80)

# Verificar usuarios sin empresa
usuarios_sin_empresa = Usuario.objects.filter(empresa__isnull=True).count()

if usuarios_sin_empresa == 0:
    print("✅ Todos los usuarios tienen empresa asignada")
else:
    print(f"⚠️  Aún hay {usuarios_sin_empresa} usuario(s) sin empresa")

for empresa in empresas:
    usuarios_count = Usuario.objects.filter(empresa=empresa).count()
    print(f"   {empresa.nombre}: {usuarios_count} usuarios")

print("="*80)
