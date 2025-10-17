#!/usr/bin/env python
"""
Script para diagnosticar y reparar perfiles de usuario
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from django.contrib.auth import get_user_model
from api.models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario

print("="*80)
print("🔍 DIAGNÓSTICO DE PERFILES DE USUARIO")
print("="*80)

User = get_user_model()

# Obtener todos los usuarios Django Auth
django_users = User.objects.all()

print(f"\n📊 USUARIOS EN EL SISTEMA:")
print(f"   Django Auth Users: {django_users.count()}")
print(f"   Usuarios de App: {Usuario.objects.count()}")
print(f"   Pacientes: {Paciente.objects.count()}")
print(f"   Odontólogos: {Odontologo.objects.count()}")
print(f"   Recepcionistas: {Recepcionista.objects.count()}")

# Verificar cada usuario
print("\n" + "="*80)
print("🔎 ANÁLISIS DETALLADO DE USUARIOS")
print("="*80)

problemas = []

for django_user in django_users:
    print(f"\n{'='*80}")
    print(f"👤 Usuario: {django_user.username}")
    print(f"   Email: {django_user.email}")
    print(f"   Active: {django_user.is_active}")
    print(f"   Staff: {django_user.is_staff}")
    
    # Buscar en tabla Usuario
    try:
        usuario = Usuario.objects.get(correoelectronico=django_user.username)
        print(f"   ✅ Usuario de App: ID {usuario.codigo}")
        print(f"   Rol: {usuario.idtipousuario.rol}")
        print(f"   Empresa: {usuario.empresa.nombre if usuario.empresa else 'Sin empresa'}")
        
        # Verificar perfil específico según rol
        rol_id = usuario.idtipousuario.id
        
        if rol_id == 2:  # Paciente
            try:
                paciente = Paciente.objects.get(codusuario=usuario)
                print(f"   ✅ Perfil de Paciente: Sí")
                print(f"      CI: {paciente.carnetidentidad or 'N/A'}")
                print(f"      Fecha Nac: {paciente.fechanacimiento or 'N/A'}")
            except Paciente.DoesNotExist:
                print(f"   ❌ Perfil de Paciente: NO EXISTE")
                problemas.append({
                    'tipo': 'paciente_faltante',
                    'django_user': django_user,
                    'usuario': usuario
                })
        
        elif rol_id == 3:  # Odontólogo
            try:
                odontologo = Odontologo.objects.get(codusuario=usuario)
                print(f"   ✅ Perfil de Odontólogo: Sí")
                print(f"      Especialidad: {odontologo.especialidad or 'N/A'}")
                print(f"      Matrícula: {odontologo.nromatricula or 'N/A'}")
            except Odontologo.DoesNotExist:
                print(f"   ❌ Perfil de Odontólogo: NO EXISTE")
                problemas.append({
                    'tipo': 'odontologo_faltante',
                    'django_user': django_user,
                    'usuario': usuario
                })
        
        elif rol_id == 4:  # Recepcionista
            try:
                recep = Recepcionista.objects.get(codusuario=usuario)
                print(f"   ✅ Perfil de Recepcionista: Sí")
            except Recepcionista.DoesNotExist:
                print(f"   ❌ Perfil de Recepcionista: NO EXISTE")
                problemas.append({
                    'tipo': 'recepcionista_faltante',
                    'django_user': django_user,
                    'usuario': usuario
                })
        
        elif rol_id == 1:  # Administrador
            print(f"   ℹ️  Administrador (no requiere perfil adicional)")
    
    except Usuario.DoesNotExist:
        print(f"   ❌ Usuario de App: NO EXISTE")
        problemas.append({
            'tipo': 'usuario_app_faltante',
            'django_user': django_user
        })

# Resumen de problemas
print("\n" + "="*80)
print("⚠️  PROBLEMAS DETECTADOS")
print("="*80)

if not problemas:
    print("\n✅ No se detectaron problemas. Todos los usuarios tienen perfiles completos.")
else:
    print(f"\n❌ Se encontraron {len(problemas)} problema(s):\n")
    
    for idx, problema in enumerate(problemas, 1):
        print(f"{idx}. {problema['tipo'].replace('_', ' ').title()}")
        print(f"   Usuario: {problema['django_user'].username}")
        if 'usuario' in problema:
            print(f"   Rol: {problema['usuario'].idtipousuario.rol}")
        print()

# Ofrecer reparación
if problemas:
    print("="*80)
    print("🔧 REPARACIÓN AUTOMÁTICA")
    print("="*80)
    
    reparar = input("\n¿Deseas reparar estos problemas automáticamente? (s/n): ").strip().lower()
    
    if reparar == 's':
        print("\n🚀 Reparando perfiles...")
        
        for problema in problemas:
            try:
                if problema['tipo'] == 'paciente_faltante':
                    usuario = problema['usuario']
                    empresa = usuario.empresa
                    
                    paciente = Paciente.objects.create(
                        codusuario=usuario,
                        empresa=empresa
                    )
                    print(f"✅ Perfil de Paciente creado para: {usuario.correoelectronico}")
                
                elif problema['tipo'] == 'odontologo_faltante':
                    usuario = problema['usuario']
                    empresa = usuario.empresa
                    
                    odontologo = Odontologo.objects.create(
                        codusuario=usuario,
                        especialidad="Odontología General",
                        empresa=empresa
                    )
                    print(f"✅ Perfil de Odontólogo creado para: {usuario.correoelectronico}")
                
                elif problema['tipo'] == 'recepcionista_faltante':
                    usuario = problema['usuario']
                    empresa = usuario.empresa
                    
                    recep = Recepcionista.objects.create(
                        codusuario=usuario,
                        empresa=empresa
                    )
                    print(f"✅ Perfil de Recepcionista creado para: {usuario.correoelectronico}")
                
                elif problema['tipo'] == 'usuario_app_faltante':
                    django_user = problema['django_user']
                    
                    # Necesitamos saber el rol
                    print(f"\n⚠️  Usuario {django_user.username} no tiene registro en la tabla Usuario")
                    print("   Roles disponibles:")
                    print("   1. Administrador")
                    print("   2. Paciente")
                    print("   3. Odontólogo")
                    print("   4. Recepcionista")
                    
                    rol_opcion = input("   Selecciona rol (1-4): ").strip()
                    
                    if rol_opcion in ['1', '2', '3', '4']:
                        rol = Tipodeusuario.objects.get(id=int(rol_opcion))
                        
                        # Buscar empresa
                        from api.models import Empresa
                        empresa = Empresa.objects.first()
                        
                        usuario = Usuario.objects.create(
                            nombre=django_user.first_name or "Usuario",
                            apellido=django_user.last_name or "Nuevo",
                            correoelectronico=django_user.username,
                            idtipousuario=rol,
                            empresa=empresa
                        )
                        
                        print(f"✅ Usuario de App creado: {usuario.correoelectronico}")
                        
                        # Crear perfil específico si es necesario
                        if int(rol_opcion) == 2:  # Paciente
                            Paciente.objects.create(codusuario=usuario, empresa=empresa)
                            print(f"✅ Perfil de Paciente creado")
                        elif int(rol_opcion) == 3:  # Odontólogo
                            Odontologo.objects.create(codusuario=usuario, empresa=empresa)
                            print(f"✅ Perfil de Odontólogo creado")
                        elif int(rol_opcion) == 4:  # Recepcionista
                            Recepcionista.objects.create(codusuario=usuario, empresa=empresa)
                            print(f"✅ Perfil de Recepcionista creado")
            
            except Exception as e:
                print(f"❌ Error reparando {problema['tipo']}: {e}")
        
        print("\n✅ Reparación completada!")
        print("\n💡 Refresca la página y vuelve a intentar.")
    else:
        print("\n⚠️  Reparación cancelada")

print("\n" + "="*80)
print("📊 RESUMEN FINAL")
print("="*80)
print(f"✅ Usuarios totales: {django_users.count()}")
print(f"✅ Usuarios con perfil de app: {Usuario.objects.count()}")
print(f"✅ Pacientes: {Paciente.objects.count()}")
print(f"✅ Odontólogos: {Odontologo.objects.count()}")
print(f"✅ Recepcionistas: {Recepcionista.objects.count()}")
print("="*80)
