"""
Script para gestionar cambios de rol de usuarios con datos relacionados

Este script identifica usuarios que tienen datos relacionados (consultas, planes, etc.)
y proporciona opciones para resolver el problema antes de cambiar el rol.

Ejecutar: python gestionar_cambio_rol_con_datos.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Usuario, Paciente, Odontologo, Recepcionista, Consulta, Plandetratamiento, Recetamedica, Tipodeusuario


def analizar_usuario(usuario):
    """Analiza las relaciones de un usuario"""
    print(f"\n{'='*80}")
    print(f"👤 Usuario: {usuario.nombre} {usuario.apellido} (ID: {usuario.codigo})")
    print(f"📧 Email: {usuario.correoelectronico}")
    print(f"🏢 Empresa: {usuario.empresa.nombre if usuario.empresa else 'Sin empresa'}")
    print(f"👔 Rol actual: {usuario.idtipousuario.rol}")
    print(f"{'='*80}")
    
    relaciones = {
        'paciente': [],
        'odontologo': [],
        'recepcionista': []
    }
    
    # Analizar como Paciente
    try:
        paciente = Paciente.objects.get(codusuario=usuario)
        print(f"\n✅ Tiene perfil de PACIENTE")
        
        consultas = Consulta.objects.filter(codpaciente=paciente)
        if consultas.exists():
            count = consultas.count()
            relaciones['paciente'].append(f"{count} consulta(s)")
            print(f"   - {count} consulta(s) como paciente")
            
            # Mostrar algunas consultas
            for i, consulta in enumerate(consultas[:3], 1):
                print(f"      {i}. Fecha: {consulta.fecha}, Estado: {consulta.idestadoconsulta.estado}")
            if count > 3:
                print(f"      ... y {count - 3} más")
        
        planes = Plandetratamiento.objects.filter(codpaciente=paciente)
        if planes.exists():
            count = planes.count()
            relaciones['paciente'].append(f"{count} plan(es) de tratamiento")
            print(f"   - {count} plan(es) de tratamiento")
        
        recetas = Recetamedica.objects.filter(codpaciente=paciente)
        if recetas.exists():
            count = recetas.count()
            relaciones['paciente'].append(f"{count} receta(s) médica(s)")
            print(f"   - {count} receta(s) médica(s)")
        
        if not relaciones['paciente']:
            print(f"   ✅ Sin datos relacionados como paciente")
    except Paciente.DoesNotExist:
        print(f"\n❌ NO tiene perfil de PACIENTE")
    
    # Analizar como Odontólogo
    try:
        odontologo = Odontologo.objects.get(codusuario=usuario)
        print(f"\n✅ Tiene perfil de ODONTOLOGO")
        print(f"   - Especialidad: {odontologo.especialidad or 'No especificada'}")
        print(f"   - Matrícula: {odontologo.nromatricula or 'No especificada'}")
        
        consultas = Consulta.objects.filter(cododontologo=odontologo)
        if consultas.exists():
            count = consultas.count()
            relaciones['odontologo'].append(f"{count} consulta(s)")
            print(f"   - {count} consulta(s) como odontólogo")
            
            # Mostrar algunas consultas
            for i, consulta in enumerate(consultas[:3], 1):
                paciente_nombre = f"{consulta.codpaciente.codusuario.nombre} {consulta.codpaciente.codusuario.apellido}"
                print(f"      {i}. Paciente: {paciente_nombre}, Fecha: {consulta.fecha}")
            if count > 3:
                print(f"      ... y {count - 3} más")
        
        planes = Plandetratamiento.objects.filter(cododontologo=odontologo)
        if planes.exists():
            count = planes.count()
            relaciones['odontologo'].append(f"{count} plan(es) de tratamiento")
            print(f"   - {count} plan(es) de tratamiento como odontólogo")
        
        recetas = Recetamedica.objects.filter(cododontologo=odontologo)
        if recetas.exists():
            count = recetas.count()
            relaciones['odontologo'].append(f"{count} receta(s)")
            print(f"   - {count} receta(s) como odontólogo")
        
        if not relaciones['odontologo']:
            print(f"   ✅ Sin datos relacionados como odontólogo")
    except Odontologo.DoesNotExist:
        print(f"\n❌ NO tiene perfil de ODONTOLOGO")
    
    # Analizar como Recepcionista
    try:
        recepcionista = Recepcionista.objects.get(codusuario=usuario)
        print(f"\n✅ Tiene perfil de RECEPCIONISTA")
        
        consultas = Consulta.objects.filter(codrecepcionista=recepcionista)
        if consultas.exists():
            count = consultas.count()
            relaciones['recepcionista'].append(f"{count} consulta(s)")
            print(f"   - {count} consulta(s) registradas por esta recepcionista")
        
        if not relaciones['recepcionista']:
            print(f"   ✅ Sin datos relacionados como recepcionista")
    except Recepcionista.DoesNotExist:
        print(f"\n❌ NO tiene perfil de RECEPCIONISTA")
    
    return relaciones


def listar_usuarios_con_datos():
    """Lista todos los usuarios y sus datos relacionados"""
    print("=" * 80)
    print("🔍 USUARIOS CON DATOS RELACIONADOS")
    print("=" * 80)
    
    usuarios = Usuario.objects.select_related('idtipousuario', 'empresa').all()
    
    usuarios_con_problemas = []
    
    for usuario in usuarios:
        relaciones = analizar_usuario(usuario)
        
        # Verificar si tiene relaciones
        tiene_relaciones = any([
            relaciones['paciente'],
            relaciones['odontologo'],
            relaciones['recepcionista']
        ])
        
        if tiene_relaciones:
            usuarios_con_problemas.append((usuario, relaciones))
    
    return usuarios_con_problemas


def mostrar_opciones_resolucion(usuario, relaciones):
    """Muestra opciones para resolver el problema de cambio de rol"""
    print(f"\n{'='*80}")
    print(f"💡 OPCIONES PARA CAMBIAR EL ROL DE: {usuario.nombre} {usuario.apellido}")
    print(f"{'='*80}")
    
    print(f"\n⚠️ PROBLEMA: Este usuario tiene datos relacionados que impiden eliminar su perfil actual.")
    print(f"\n📊 Datos relacionados:")
    for rol, datos in relaciones.items():
        if datos:
            print(f"   - Como {rol}: {', '.join(datos)}")
    
    print(f"\n🔧 OPCIONES DE RESOLUCIÓN:\n")
    
    print("1️⃣ **OPCIÓN 1: Mantener ambos perfiles (RECOMENDADO)**")
    print("   - El usuario tendrá múltiples perfiles simultáneamente")
    print("   - Esto permite mantener el historial completo")
    print("   - El sistema usará el perfil según el contexto")
    print("   - PRO: No se pierde información")
    print("   - CON: Inconsistencia en la BD (pero funcional)")
    
    print("\n2️⃣ **OPCIÓN 2: Reasignar datos a otro usuario**")
    print("   - Reasigna las consultas/planes/recetas a otro profesional")
    print("   - Luego se puede eliminar el perfil antiguo")
    print("   - PRO: Mantiene consistencia en la BD")
    print("   - CON: Requiere trabajo manual, cambia el historial")
    
    print("\n3️⃣ **OPCIÓN 3: Marcar datos como archivados/históricos**")
    print("   - Mantén los datos pero con un estado especial")
    print("   - Luego elimina el perfil (si tu BD lo permite)")
    print("   - PRO: Datos preservados para auditoría")
    print("   - CON: Requiere modificación del esquema")
    
    print("\n4️⃣ **OPCIÓN 4: Crear un usuario nuevo para el nuevo rol**")
    print("   - Mantén el usuario actual con su rol")
    print("   - Crea un nuevo usuario para el nuevo rol")
    print("   - PRO: Sin problemas de integridad")
    print("   - CON: Dos usuarios diferentes (puede ser confuso)")
    
    print(f"\n{'='*80}")
    print("💡 RECOMENDACIÓN:")
    print(f"{'='*80}")
    print("Si solo quieres dar acceso temporal a otro rol → OPCIÓN 1")
    print("Si es un cambio permanente de función → OPCIÓN 2 o 4")
    print(f"{'='*80}")


def script_reasignacion_consultas():
    """Genera un script de ejemplo para reasignar consultas"""
    print("\n" + "="*80)
    print("📝 SCRIPT DE EJEMPLO: Reasignar consultas de un odontólogo a otro")
    print("="*80)
    
    script = """
# Ejemplo de script para reasignar consultas
# ADVERTENCIA: Ejecuta esto solo si estás seguro

from api.models import Usuario, Odontologo, Consulta

# Usuario que está cambiando de rol
usuario_origen = Usuario.objects.get(codigo=7)  # Cambiar por el ID correcto
odontologo_origen = Odontologo.objects.get(codusuario=usuario_origen)

# Nuevo odontólogo que tomará las consultas
usuario_destino = Usuario.objects.get(codigo=XX)  # Cambiar por el ID del nuevo odontólogo
odontologo_destino = Odontologo.objects.get(codusuario=usuario_destino)

# Reasignar TODAS las consultas
consultas = Consulta.objects.filter(cododontologo=odontologo_origen)
print(f"Reasignando {consultas.count()} consultas...")

for consulta in consultas:
    consulta.cododontologo = odontologo_destino
    consulta.save()
    print(f"✅ Consulta {consulta.id} reasignada")

print("✅ Reasignación completada")

# Ahora puedes cambiar el rol del usuario sin problemas
usuario_origen.idtipousuario_id = 1  # Cambiar a Administrador, por ejemplo
usuario_origen.save()
"""
    
    print(script)
    print("="*80)


if __name__ == '__main__':
    print("\n" + "="*80)
    print("🔧 GESTOR DE CAMBIOS DE ROL CON DATOS RELACIONADOS")
    print("="*80)
    
    usuarios_problematicos = listar_usuarios_con_datos()
    
    if not usuarios_problematicos:
        print("\n✅ ¡Excelente! No hay usuarios con datos relacionados que impidan cambios de rol.")
    else:
        print(f"\n⚠️ Se encontraron {len(usuarios_problematicos)} usuario(s) con datos relacionados:")
        
        for usuario, relaciones in usuarios_problematicos:
            mostrar_opciones_resolucion(usuario, relaciones)
        
        print("\n" + "="*80)
        print("📝 ¿Necesitas reasignar datos? Aquí tienes un script de ejemplo:")
        print("="*80)
        script_reasignacion_consultas()
