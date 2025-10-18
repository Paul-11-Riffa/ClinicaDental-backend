"""
Script de prueba para verificar el funcionamiento del sistema de cambio de roles

Este script:
1. Crea un usuario de prueba como Paciente
2. Lo cambia a Odontologo
3. Lo cambia a Recepcionista
4. Lo cambia a Administrador
5. Verifica que en cada paso los perfiles se crean/eliminan correctamente

Ejecutar: python test_cambio_roles.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario, Empresa
from django.db import transaction


def verificar_perfiles(usuario, rol_esperado):
    """Verifica que el usuario tenga solo el perfil correcto"""
    tiene_paciente = Paciente.objects.filter(codusuario=usuario).exists()
    tiene_odontologo = Odontologo.objects.filter(codusuario=usuario).exists()
    tiene_recepcionista = Recepcionista.objects.filter(codusuario=usuario).exists()
    
    print(f"\n   Verificando perfiles:")
    print(f"   - Paciente: {'✅ Sí' if tiene_paciente else '❌ No'}")
    print(f"   - Odontologo: {'✅ Sí' if tiene_odontologo else '❌ No'}")
    print(f"   - Recepcionista: {'✅ Sí' if tiene_recepcionista else '❌ No'}")
    
    # Verificar consistencia
    if rol_esperado == 'paciente':
        return tiene_paciente and not tiene_odontologo and not tiene_recepcionista
    elif rol_esperado == 'odontologo':
        return not tiene_paciente and tiene_odontologo and not tiene_recepcionista
    elif rol_esperado == 'recepcionista':
        return not tiene_paciente and not tiene_odontologo and tiene_recepcionista
    elif rol_esperado == 'administrador':
        return not tiene_paciente and not tiene_odontologo and not tiene_recepcionista
    
    return False


def test_cambio_roles():
    """Prueba el cambio de roles y verifica la consistencia"""
    
    print("=" * 80)
    print("🧪 TEST DE CAMBIO DE ROLES")
    print("=" * 80)
    
    # Obtener o crear empresa de prueba
    empresa, _ = Empresa.objects.get_or_create(
        subdomain='test',
        defaults={'nombre': 'Empresa Test', 'activo': True}
    )
    
    # Obtener tipos de usuario
    tipo_admin = Tipodeusuario.objects.get(id=1)
    tipo_paciente = Tipodeusuario.objects.get(id=2)
    tipo_odontologo = Tipodeusuario.objects.get(id=3)
    tipo_recepcionista = Tipodeusuario.objects.get(id=4)
    
    # Limpiar usuario de prueba anterior si existe
    Usuario.objects.filter(correoelectronico='test.roles@example.com').delete()
    
    try:
        with transaction.atomic():
            # PASO 1: Crear usuario como Paciente
            print("\n" + "=" * 80)
            print("PASO 1: Crear usuario como Paciente")
            print("=" * 80)
            
            usuario = Usuario.objects.create(
                nombre='Test',
                apellido='Roles',
                correoelectronico='test.roles@example.com',
                idtipousuario=tipo_paciente,
                empresa=empresa
            )
            print(f"✅ Usuario creado con ID: {usuario.codigo}")
            
            # Verificar
            es_correcto = verificar_perfiles(usuario, 'paciente')
            if es_correcto:
                print("✅ Perfiles correctos para Paciente")
            else:
                print("❌ ERROR: Perfiles incorrectos para Paciente")
                raise Exception("Perfiles incorrectos en creación")
            
            # PASO 2: Cambiar a Odontologo
            print("\n" + "=" * 80)
            print("PASO 2: Cambiar a Odontologo")
            print("=" * 80)
            
            usuario.idtipousuario = tipo_odontologo
            usuario.save()
            
            # Verificar
            es_correcto = verificar_perfiles(usuario, 'odontologo')
            if es_correcto:
                print("✅ Perfiles correctos para Odontologo")
            else:
                print("❌ ERROR: Perfiles incorrectos para Odontologo")
                raise Exception("Perfiles incorrectos al cambiar a Odontologo")
            
            # PASO 3: Cambiar a Recepcionista
            print("\n" + "=" * 80)
            print("PASO 3: Cambiar a Recepcionista")
            print("=" * 80)
            
            usuario.idtipousuario = tipo_recepcionista
            usuario.save()
            
            # Verificar
            es_correcto = verificar_perfiles(usuario, 'recepcionista')
            if es_correcto:
                print("✅ Perfiles correctos para Recepcionista")
            else:
                print("❌ ERROR: Perfiles incorrectos para Recepcionista")
                raise Exception("Perfiles incorrectos al cambiar a Recepcionista")
            
            # PASO 4: Cambiar a Administrador
            print("\n" + "=" * 80)
            print("PASO 4: Cambiar a Administrador")
            print("=" * 80)
            
            usuario.idtipousuario = tipo_admin
            usuario.save()
            
            # Verificar
            es_correcto = verificar_perfiles(usuario, 'administrador')
            if es_correcto:
                print("✅ Perfiles correctos para Administrador (sin perfil específico)")
            else:
                print("❌ ERROR: Perfiles incorrectos para Administrador")
                raise Exception("Perfiles incorrectos al cambiar a Administrador")
            
            # PASO 5: Volver a Paciente
            print("\n" + "=" * 80)
            print("PASO 5: Volver a Paciente")
            print("=" * 80)
            
            usuario.idtipousuario = tipo_paciente
            usuario.save()
            
            # Verificar
            es_correcto = verificar_perfiles(usuario, 'paciente')
            if es_correcto:
                print("✅ Perfiles correctos para Paciente (de nuevo)")
            else:
                print("❌ ERROR: Perfiles incorrectos al volver a Paciente")
                raise Exception("Perfiles incorrectos al volver a Paciente")
            
            # RESUMEN FINAL
            print("\n" + "=" * 80)
            print("✅ TODOS LOS TESTS PASARON CORRECTAMENTE")
            print("=" * 80)
            print("\n🎉 El sistema de cambio de roles funciona perfectamente!")
            print("\nEl usuario de prueba fue eliminado automáticamente (rollback).")
            
            # Hacer rollback para limpiar
            raise Exception("Test completado - rollback intencional")
    
    except Exception as e:
        if "Test completado" in str(e):
            print("\n✅ Limpieza completada (rollback de transacción de prueba)")
        else:
            print(f"\n❌ ERROR durante el test: {str(e)}")
            raise


if __name__ == '__main__':
    try:
        test_cambio_roles()
    except Exception as e:
        if "Test completado" not in str(e):
            print(f"\n❌ Test falló: {str(e)}")
        else:
            print("\n✅ Test completado exitosamente")
