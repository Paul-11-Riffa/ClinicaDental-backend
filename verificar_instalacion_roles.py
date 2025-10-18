"""
Script de verificación final del sistema de gestión de roles

Este script verifica que:
1. Los signals están registrados correctamente
2. No hay errores de importación
3. El sistema está listo para usar

Ejecutar: python verificar_instalacion_roles.py
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

def verificar_instalacion():
    """Verifica que todo esté correctamente instalado"""
    
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE INSTALACIÓN DEL SISTEMA DE GESTIÓN DE ROLES")
    print("=" * 80)
    
    errores = []
    advertencias = []
    
    # 1. Verificar que el módulo de signals existe
    print("\n1️⃣  Verificando módulo de signals...")
    try:
        import api.signals_usuario
        print("   ✅ Módulo api.signals_usuario importado correctamente")
    except ImportError as e:
        errores.append(f"❌ No se pudo importar api.signals_usuario: {e}")
        print(f"   {errores[-1]}")
    
    # 2. Verificar que apps.py tiene el import
    print("\n2️⃣  Verificando registro de signals en apps.py...")
    try:
        from api.apps import ApiConfig
        import inspect
        
        source = inspect.getsource(ApiConfig.ready)
        if 'signals_usuario' in source:
            print("   ✅ Signals registrados en api.apps.ApiConfig.ready()")
        else:
            advertencias.append("⚠️  No se encontró 'signals_usuario' en apps.py")
            print(f"   {advertencias[-1]}")
    except Exception as e:
        advertencias.append(f"⚠️  No se pudo verificar apps.py: {e}")
        print(f"   {advertencias[-1]}")
    
    # 3. Verificar que los modelos existen
    print("\n3️⃣  Verificando modelos...")
    try:
        from api.models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario
        print("   ✅ Todos los modelos importados correctamente")
        print(f"      - Usuario")
        print(f"      - Paciente")
        print(f"      - Odontologo")
        print(f"      - Recepcionista")
        print(f"      - Tipodeusuario")
    except ImportError as e:
        errores.append(f"❌ Error importando modelos: {e}")
        print(f"   {errores[-1]}")
    
    # 4. Verificar que los roles existen en la BD
    print("\n4️⃣  Verificando roles en la base de datos...")
    try:
        from api.models import Tipodeusuario
        
        roles_esperados = {
            1: 'Administrador',
            2: 'Paciente',
            3: 'Odontologo',
            4: 'Recepcionista'
        }
        
        roles_encontrados = {}
        for rol_id, rol_nombre in roles_esperados.items():
            try:
                rol = Tipodeusuario.objects.get(id=rol_id)
                roles_encontrados[rol_id] = rol.rol
                print(f"   ✅ Rol {rol_id}: {rol.rol}")
            except Tipodeusuario.DoesNotExist:
                advertencias.append(f"⚠️  Rol {rol_id} ({rol_nombre}) no encontrado en BD")
                print(f"   {advertencias[-1]}")
        
        if len(roles_encontrados) < 4:
            print("\n   ℹ️  Algunos roles no están en la BD. Ejecuta:")
            print("      python inicializar_datos.py")
    
    except Exception as e:
        errores.append(f"❌ Error verificando roles: {e}")
        print(f"   {errores[-1]}")
    
    # 5. Verificar el management command
    print("\n5️⃣  Verificando management command...")
    try:
        from api.management.commands.reparar_roles_usuarios import Command
        print("   ✅ Management command 'reparar_roles_usuarios' disponible")
    except ImportError as e:
        errores.append(f"❌ Management command no disponible: {e}")
        print(f"   {errores[-1]}")
    
    # 6. Verificar funciones auxiliares
    print("\n6️⃣  Verificando funciones auxiliares...")
    try:
        from api.signals_usuario import (
            _obtener_rol_nombre,
            _eliminar_perfil_antiguo,
            _crear_perfil_nuevo,
            reparar_inconsistencias_roles
        )
        print("   ✅ Todas las funciones auxiliares disponibles")
        print(f"      - _obtener_rol_nombre")
        print(f"      - _eliminar_perfil_antiguo")
        print(f"      - _crear_perfil_nuevo")
        print(f"      - reparar_inconsistencias_roles")
    except ImportError as e:
        errores.append(f"❌ Funciones auxiliares no disponibles: {e}")
        print(f"   {errores[-1]}")
    
    # 7. Verificar scripts de utilidad
    print("\n7️⃣  Verificando scripts de utilidad...")
    scripts = [
        'diagnosticar_roles.py',
        'test_cambio_roles.py',
    ]
    
    for script in scripts:
        if os.path.exists(script):
            print(f"   ✅ {script}")
        else:
            advertencias.append(f"⚠️  {script} no encontrado")
            print(f"   {advertencias[-1]}")
    
    # 8. Verificar documentación
    print("\n8️⃣  Verificando documentación...")
    docs = [
        'GESTION_ROLES_README.md',
        'RESUMEN_GESTION_ROLES.md',
        'GUIA_FRONTEND_CAMBIO_ROLES.md',
        'CHANGELOG_ROLES.md'
    ]
    
    for doc in docs:
        if os.path.exists(doc):
            print(f"   ✅ {doc}")
        else:
            advertencias.append(f"⚠️  {doc} no encontrado")
            print(f"   {advertencias[-1]}")
    
    # RESUMEN
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 80)
    
    if not errores and not advertencias:
        print("\n✅ ¡PERFECTO! El sistema está correctamente instalado y listo para usar.")
        print("\n📝 Próximos pasos:")
        print("   1. Ejecutar diagnóstico: python diagnosticar_roles.py")
        print("   2. Si hay inconsistencias: python manage.py reparar_roles_usuarios")
        print("   3. Ejecutar tests: python test_cambio_roles.py")
        print("   4. Leer documentación: GESTION_ROLES_README.md")
        return True
    
    if errores:
        print(f"\n❌ Se encontraron {len(errores)} ERRORES:")
        for error in errores:
            print(f"   {error}")
        print("\n⚠️  El sistema NO está listo. Corrige los errores antes de continuar.")
        return False
    
    if advertencias:
        print(f"\n⚠️  Se encontraron {len(advertencias)} ADVERTENCIAS:")
        for advertencia in advertencias:
            print(f"   {advertencia}")
        print("\n✅ El sistema está funcional, pero revisa las advertencias.")
        print("\n📝 Próximos pasos:")
        print("   1. Ejecutar diagnóstico: python diagnosticar_roles.py")
        print("   2. Si hay inconsistencias: python manage.py reparar_roles_usuarios")
        print("   3. Ejecutar tests: python test_cambio_roles.py")
        return True


if __name__ == '__main__':
    try:
        exito = verificar_instalacion()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error durante la verificación: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
