"""
Script de prueba para el sistema de creación de usuarios con diferentes roles.
Prueba la creación de Pacientes, Odontólogos, Recepcionistas y Administradores.
"""

import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import transaction
from api.models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario, Empresa
from api.serializers_user_creation import (
    CrearPacienteSerializer,
    CrearOdontologoSerializer,
    CrearRecepcionistaSerializer,
    CrearAdministradorSerializer,
)


def limpiar_usuarios_de_prueba():
    """Elimina usuarios de prueba previos."""
    emails_prueba = [
        'paciente.prueba@test.com',
        'odontologo.prueba@test.com',
        'recepcionista.prueba@test.com',
        'admin.prueba@test.com',
    ]
    
    print("\n🧹 Limpiando usuarios de prueba anteriores...")
    for email in emails_prueba:
        try:
            usuario = Usuario.objects.get(correoelectronico=email)
            # Eliminar perfiles relacionados primero
            try:
                if hasattr(usuario, 'paciente'):
                    usuario.paciente.delete()
            except:
                pass
            
            try:
                if hasattr(usuario, 'odontologo'):
                    usuario.odontologo.delete()
            except:
                pass
            
            try:
                if hasattr(usuario, 'recepcionista'):
                    usuario.recepcionista.delete()
            except:
                pass
            
            usuario.delete()
            print(f"   ✓ Eliminado: {email}")
        except Usuario.DoesNotExist:
            pass


def verificar_empresa():
    """Verifica que existe al menos una empresa para las pruebas."""
    empresa = Empresa.objects.first()
    if not empresa:
        print("❌ ERROR: No hay empresas en el sistema. Crea una empresa primero.")
        sys.exit(1)
    print(f"✓ Usando empresa: {empresa.nombre} (subdomain: {empresa.subdomain})")
    return empresa


def probar_crear_paciente(empresa):
    """Prueba la creación de un paciente."""
    print("\n" + "="*60)
    print("📋 PRUEBA 1: Crear Paciente")
    print("="*60)
    
    datos = {
        'nombre': 'María',
        'apellido': 'González',
        'correoelectronico': 'paciente.prueba@test.com',
        'sexo': 'F',
        'telefono': '71234567',
        'carnetidentidad': 'TEST-12345678',
        'fechanacimiento': '1995-03-15',
        'direccion': 'Av. Principal 123, La Paz',
    }
    
    print(f"\n📤 Datos enviados:")
    for key, value in datos.items():
        print(f"   {key}: {value}")
    
    serializer = CrearPacienteSerializer(
        data=datos,
        context={'empresa': empresa}
    )
    
    if serializer.is_valid():
        usuario = serializer.save()  # La transacción ya está en el serializer
        
        print(f"\n✅ Paciente creado exitosamente!")
        print(f"   ID Usuario: {usuario.codigo}")
        print(f"   Nombre completo: {usuario.nombre} {usuario.apellido}")
        print(f"   Email: {usuario.correoelectronico}")
        print(f"   Tipo de usuario: {usuario.idtipousuario.rol} (ID: {usuario.idtipousuario.id})")
        
        # Verificar perfil de paciente
        try:
            paciente = usuario.paciente
            print(f"\n📋 Perfil de Paciente:")
            print(f"   CI: {paciente.carnetidentidad}")
            print(f"   Fecha nacimiento: {paciente.fechanacimiento}")
            print(f"   Dirección: {paciente.direccion}")
            print(f"   Empresa: {paciente.empresa.nombre}")
        except Exception as e:
            print(f"\n❌ Error al obtener perfil de paciente: {e}")
            return False
        
        return True
    else:
        print(f"\n❌ Error en validación:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
        return False


def probar_crear_odontologo(empresa):
    """Prueba la creación de un odontólogo."""
    print("\n" + "="*60)
    print("🦷 PRUEBA 2: Crear Odontólogo")
    print("="*60)
    
    datos = {
        'nombre': 'Dr. Carlos',
        'apellido': 'Rodríguez',
        'correoelectronico': 'odontologo.prueba@test.com',
        'sexo': 'M',
        'telefono': '72345678',
        'especialidad': 'Ortodoncia',
        'experienciaprofesional': '10 años de experiencia en ortodoncia y estética dental',
        'nromatricula': 'TEST-OD-12345',
    }
    
    print(f"\n📤 Datos enviados:")
    for key, value in datos.items():
        print(f"   {key}: {value}")
    
    serializer = CrearOdontologoSerializer(
        data=datos,
        context={'empresa': empresa}
    )
    
    if serializer.is_valid():
        usuario = serializer.save()  # La transacción ya está en el serializer
        
        print(f"\n✅ Odontólogo creado exitosamente!")
        print(f"   ID Usuario: {usuario.codigo}")
        print(f"   Nombre completo: {usuario.nombre} {usuario.apellido}")
        print(f"   Email: {usuario.correoelectronico}")
        print(f"   Tipo de usuario: {usuario.idtipousuario.rol} (ID: {usuario.idtipousuario.id})")
        
        # Verificar perfil de odontólogo
        try:
            odontologo = usuario.odontologo
            print(f"\n🦷 Perfil de Odontólogo:")
            print(f"   Especialidad: {odontologo.especialidad}")
            print(f"   Experiencia: {odontologo.experienciaprofesional}")
            print(f"   Nro. Matrícula: {odontologo.nromatricula}")
            print(f"   Empresa: {odontologo.empresa.nombre}")
        except Exception as e:
            print(f"\n❌ Error al obtener perfil de odontólogo: {e}")
            return False
        
        return True
    else:
        print(f"\n❌ Error en validación:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
        return False


def probar_crear_recepcionista(empresa):
    """Prueba la creación de un recepcionista."""
    print("\n" + "="*60)
    print("📞 PRUEBA 3: Crear Recepcionista")
    print("="*60)
    
    datos = {
        'nombre': 'Ana',
        'apellido': 'Martínez',
        'correoelectronico': 'recepcionista.prueba@test.com',
        'sexo': 'F',
        'telefono': '73456789',
        'habilidadessoftware': 'Microsoft Office, Agenda Digital, Sistemas de Gestión de Clínicas',
    }
    
    print(f"\n📤 Datos enviados:")
    for key, value in datos.items():
        print(f"   {key}: {value}")
    
    serializer = CrearRecepcionistaSerializer(
        data=datos,
        context={'empresa': empresa}
    )
    
    if serializer.is_valid():
        usuario = serializer.save()  # La transacción ya está en el serializer
        
        print(f"\n✅ Recepcionista creado exitosamente!")
        print(f"   ID Usuario: {usuario.codigo}")
        print(f"   Nombre completo: {usuario.nombre} {usuario.apellido}")
        print(f"   Email: {usuario.correoelectronico}")
        print(f"   Tipo de usuario: {usuario.idtipousuario.rol} (ID: {usuario.idtipousuario.id})")
        
        # Verificar perfil de recepcionista
        try:
            recepcionista = usuario.recepcionista
            print(f"\n📞 Perfil de Recepcionista:")
            print(f"   Habilidades Software: {recepcionista.habilidadessoftware}")
            print(f"   Empresa: {recepcionista.empresa.nombre}")
        except Exception as e:
            print(f"\n❌ Error al obtener perfil de recepcionista: {e}")
            return False
        
        return True
    else:
        print(f"\n❌ Error en validación:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
        return False


def probar_crear_administrador(empresa):
    """Prueba la creación de un administrador."""
    print("\n" + "="*60)
    print("👑 PRUEBA 4: Crear Administrador")
    print("="*60)
    
    datos = {
        'nombre': 'Luis',
        'apellido': 'Fernández',
        'correoelectronico': 'admin.prueba@test.com',
        'sexo': 'M',
        'telefono': '74567890',
    }
    
    print(f"\n📤 Datos enviados:")
    for key, value in datos.items():
        print(f"   {key}: {value}")
    
    serializer = CrearAdministradorSerializer(
        data=datos,
        context={'empresa': empresa}
    )
    
    if serializer.is_valid():
        usuario = serializer.save()  # La transacción ya está en el serializer
        
        print(f"\n✅ Administrador creado exitosamente!")
        print(f"   ID Usuario: {usuario.codigo}")
        print(f"   Nombre completo: {usuario.nombre} {usuario.apellido}")
        print(f"   Email: {usuario.correoelectronico}")
        print(f"   Tipo de usuario: {usuario.idtipousuario.rol} (ID: {usuario.idtipousuario.id})")
        print(f"   Empresa: {usuario.empresa.nombre}")
        
        # Verificar que NO tiene perfil adicional (los admins no tienen tabla adicional)
        tiene_perfil_adicional = False
        try:
            if hasattr(usuario, 'paciente'):
                tiene_perfil_adicional = True
                print(f"\n⚠️  ADVERTENCIA: Admin tiene perfil de Paciente (no debería)")
        except:
            pass
        
        try:
            if hasattr(usuario, 'odontologo'):
                tiene_perfil_adicional = True
                print(f"\n⚠️  ADVERTENCIA: Admin tiene perfil de Odontólogo (no debería)")
        except:
            pass
        
        try:
            if hasattr(usuario, 'recepcionista'):
                tiene_perfil_adicional = True
                print(f"\n⚠️  ADVERTENCIA: Admin tiene perfil de Recepcionista (no debería)")
        except:
            pass
        
        if not tiene_perfil_adicional:
            print(f"\n✓ Correcto: El administrador NO tiene tabla adicional")
        
        return True
    else:
        print(f"\n❌ Error en validación:")
        for field, errors in serializer.errors.items():
            print(f"   {field}: {errors}")
        return False


def probar_validaciones():
    """Prueba las validaciones del sistema."""
    print("\n" + "="*60)
    print("🔍 PRUEBA 5: Validaciones")
    print("="*60)
    
    empresa = Empresa.objects.first()
    
    # Prueba 1: Email duplicado
    print("\n📋 Test 5.1: Email duplicado")
    datos = {
        'nombre': 'Test',
        'apellido': 'Duplicado',
        'correoelectronico': 'paciente.prueba@test.com',  # Ya existe
    }
    
    serializer = CrearPacienteSerializer(data=datos, context={'empresa': empresa})
    if not serializer.is_valid():
        if 'correoelectronico' in serializer.errors:
            print("   ✅ Validación correcta: Email duplicado detectado")
        else:
            print(f"   ❌ Error inesperado: {serializer.errors}")
    else:
        print("   ❌ ERROR: No detectó email duplicado")
    
    # Prueba 2: CI duplicado
    print("\n📋 Test 5.2: CI duplicado")
    datos = {
        'nombre': 'Test',
        'apellido': 'CI Duplicado',
        'correoelectronico': 'nuevo@test.com',
        'carnetidentidad': 'TEST-12345678',  # Ya existe
    }
    
    serializer = CrearPacienteSerializer(data=datos, context={'empresa': empresa})
    if not serializer.is_valid():
        if 'carnetidentidad' in serializer.errors:
            print("   ✅ Validación correcta: CI duplicado detectado")
        else:
            print(f"   ❌ Error inesperado: {serializer.errors}")
    else:
        print("   ❌ ERROR: No detectó CI duplicado")
    
    # Prueba 3: Matrícula duplicada
    print("\n📋 Test 5.3: Matrícula duplicada")
    datos = {
        'nombre': 'Test',
        'apellido': 'Matrícula Duplicada',
        'correoelectronico': 'nuevo2@test.com',
        'nromatricula': 'TEST-OD-12345',  # Ya existe
    }
    
    serializer = CrearOdontologoSerializer(data=datos, context={'empresa': empresa})
    if not serializer.is_valid():
        if 'nromatricula' in serializer.errors:
            print("   ✅ Validación correcta: Matrícula duplicada detectada")
        else:
            print(f"   ❌ Error inesperado: {serializer.errors}")
    else:
        print("   ❌ ERROR: No detectó matrícula duplicada")


def mostrar_resumen():
    """Muestra un resumen de todos los usuarios creados."""
    print("\n" + "="*60)
    print("📊 RESUMEN FINAL")
    print("="*60)
    
    print("\n👥 Usuarios creados en esta prueba:\n")
    
    usuarios = Usuario.objects.filter(
        correoelectronico__in=[
            'paciente.prueba@test.com',
            'odontologo.prueba@test.com',
            'recepcionista.prueba@test.com',
            'admin.prueba@test.com',
        ]
    ).select_related('idtipousuario', 'empresa')
    
    for usuario in usuarios:
        print(f"   • {usuario.nombre} {usuario.apellido}")
        print(f"     - Email: {usuario.correoelectronico}")
        print(f"     - Tipo: {usuario.idtipousuario.rol}")
        print(f"     - Empresa: {usuario.empresa.nombre if usuario.empresa else 'N/A'}")
        
        # Mostrar datos específicos del rol
        try:
            if hasattr(usuario, 'paciente'):
                p = usuario.paciente
                print(f"     - CI: {p.carnetidentidad}, Nacimiento: {p.fechanacimiento}")
        except:
            pass
        
        try:
            if hasattr(usuario, 'odontologo'):
                o = usuario.odontologo
                print(f"     - Especialidad: {o.especialidad}, Matrícula: {o.nromatricula}")
        except:
            pass
        
        try:
            if hasattr(usuario, 'recepcionista'):
                r = usuario.recepcionista
                print(f"     - Habilidades: {r.habilidadessoftware}")
        except:
            pass
        
        print()


def main():
    """Función principal."""
    print("\n" + "🧪 "*30)
    print("  PRUEBAS DE CREACIÓN DE USUARIOS CON ROLES")
    print("🧪 "*30)
    
    # Limpiar usuarios previos
    limpiar_usuarios_de_prueba()
    
    # Verificar empresa
    empresa = verificar_empresa()
    
    # Ejecutar pruebas
    resultados = []
    
    resultados.append(("Crear Paciente", probar_crear_paciente(empresa)))
    resultados.append(("Crear Odontólogo", probar_crear_odontologo(empresa)))
    resultados.append(("Crear Recepcionista", probar_crear_recepcionista(empresa)))
    resultados.append(("Crear Administrador", probar_crear_administrador(empresa)))
    
    # Pruebas de validación
    probar_validaciones()
    
    # Mostrar resumen
    mostrar_resumen()
    
    # Mostrar resultados finales
    print("\n" + "="*60)
    print("📈 RESULTADOS DE LAS PRUEBAS")
    print("="*60)
    
    exitosas = sum(1 for _, resultado in resultados if resultado)
    total = len(resultados)
    
    for nombre, resultado in resultados:
        estado = "✅ EXITOSA" if resultado else "❌ FALLIDA"
        print(f"   {nombre}: {estado}")
    
    print(f"\n   Total: {exitosas}/{total} pruebas exitosas")
    
    if exitosas == total:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print(f"\n⚠️  {total - exitosas} prueba(s) fallaron")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
