"""
Script para diagnosticar inconsistencias en roles de usuarios
Ejecutar: python diagnosticar_roles.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Paciente, Odontologo, Recepcionista, Tipodeusuario


def diagnosticar_roles():
    """Diagnostica el estado de los roles de usuarios"""
    
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE ROLES Y PERFILES DE USUARIOS")
    print("=" * 80)
    
    # Obtener todos los usuarios
    usuarios = Usuario.objects.select_related('idtipousuario', 'empresa').all()
    
    print(f"\n📊 Total de usuarios: {usuarios.count()}")
    
    # Contadores
    consistentes = 0
    inconsistentes = 0
    problemas = []
    
    print("\n" + "=" * 80)
    print("ANÁLISIS DETALLADO")
    print("=" * 80)
    
    for usuario in usuarios:
        # Obtener rol
        rol = usuario.idtipousuario.rol if usuario.idtipousuario else "Sin rol"
        rol_lower = rol.lower().strip()
        
        # Verificar perfiles existentes
        tiene_paciente = Paciente.objects.filter(codusuario=usuario).exists()
        tiene_odontologo = Odontologo.objects.filter(codusuario=usuario).exists()
        tiene_recepcionista = Recepcionista.objects.filter(codusuario=usuario).exists()
        
        perfiles_actuales = []
        if tiene_paciente:
            perfiles_actuales.append("Paciente")
        if tiene_odontologo:
            perfiles_actuales.append("Odontologo")
        if tiene_recepcionista:
            perfiles_actuales.append("Recepcionista")
        
        # Determinar el perfil esperado
        perfil_esperado = None
        if 'paciente' in rol_lower:
            perfil_esperado = "Paciente"
        elif 'odontologo' in rol_lower or 'odontólogo' in rol_lower:
            perfil_esperado = "Odontologo"
        elif 'recepcionista' in rol_lower:
            perfil_esperado = "Recepcionista"
        elif 'admin' in rol_lower:
            perfil_esperado = None  # Admin no tiene perfil específico
        
        # Verificar consistencia
        es_consistente = True
        problema_desc = None
        
        # Caso 1: Tiene múltiples perfiles
        if len(perfiles_actuales) > 1:
            es_consistente = False
            problema_desc = f"❌ MÚLTIPLES PERFILES: {', '.join(perfiles_actuales)}"
        
        # Caso 2: Falta el perfil esperado
        elif perfil_esperado and perfil_esperado not in perfiles_actuales:
            es_consistente = False
            problema_desc = f"❌ FALTA PERFIL: Esperado {perfil_esperado}, tiene {perfiles_actuales or 'ninguno'}"
        
        # Caso 3: Tiene perfil pero no debería (es admin)
        elif perfil_esperado is None and len(perfiles_actuales) > 0:
            es_consistente = False
            problema_desc = f"❌ PERFIL INNECESARIO: Es {rol} pero tiene {', '.join(perfiles_actuales)}"
        
        # Caso 4: Tiene perfil que no corresponde
        elif perfil_esperado and perfiles_actuales and perfil_esperado not in perfiles_actuales:
            es_consistente = False
            problema_desc = f"❌ PERFIL INCORRECTO: Esperado {perfil_esperado}, tiene {', '.join(perfiles_actuales)}"
        
        # Mostrar resultado
        if es_consistente:
            consistentes += 1
            print(f"\n✅ Usuario #{usuario.codigo} - {usuario.nombre} {usuario.apellido}")
            print(f"   Email: {usuario.correoelectronico}")
            print(f"   Empresa: {usuario.empresa.nombre if usuario.empresa else 'Sin empresa'}")
            print(f"   Rol: {rol}")
            print(f"   Perfil: {perfiles_actuales[0] if perfiles_actuales else 'Ninguno (correcto para admin)'}")
        else:
            inconsistentes += 1
            print(f"\n❌ Usuario #{usuario.codigo} - {usuario.nombre} {usuario.apellido}")
            print(f"   Email: {usuario.correoelectronico}")
            print(f"   Empresa: {usuario.empresa.nombre if usuario.empresa else 'Sin empresa'}")
            print(f"   Rol: {rol}")
            print(f"   {problema_desc}")
            
            problemas.append({
                'usuario': usuario,
                'rol': rol,
                'perfiles_actuales': perfiles_actuales,
                'perfil_esperado': perfil_esperado,
                'descripcion': problema_desc
            })
    
    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    print(f"✅ Usuarios consistentes: {consistentes}")
    print(f"❌ Usuarios con problemas: {inconsistentes}")
    
    if problemas:
        print("\n" + "=" * 80)
        print("⚠️  ACCIONES RECOMENDADAS")
        print("=" * 80)
        print("\nSe detectaron inconsistencias. Para corregirlas automáticamente, ejecuta:")
        print("\n   python manage.py reparar_roles_usuarios")
        print("\nO ejecuta el script:")
        print("\n   python manage.py shell < api/signals_usuario.py")
        print("   >>> from api.signals_usuario import reparar_inconsistencias_roles")
        print("   >>> reparar_inconsistencias_roles()")
        
        print("\n" + "=" * 80)
        print("DETALLE DE PROBLEMAS")
        print("=" * 80)
        for p in problemas:
            print(f"\n👤 {p['usuario'].correoelectronico}")
            print(f"   Rol actual: {p['rol']}")
            print(f"   Perfil esperado: {p['perfil_esperado'] or 'Ninguno'}")
            print(f"   Perfiles actuales: {', '.join(p['perfiles_actuales']) or 'Ninguno'}")
    else:
        print("\n✅ ¡Excelente! Todos los usuarios tienen perfiles consistentes.")
    
    return consistentes, inconsistentes


if __name__ == '__main__':
    diagnosticar_roles()
