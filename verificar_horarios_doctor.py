"""
Verificar horarios del Dr. Pedro Martínez en Clínica Norte
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Odontologo, Usuario, Empresa, Horario
from datetime import datetime, time

print("=" * 70)
print("🔍 VERIFICAR DR. PEDRO MARTÍNEZ - CLÍNICA NORTE")
print("=" * 70)

# 1. Buscar empresa Norte
try:
    norte = Empresa.objects.get(subdomain='norte')
    print(f"\n✅ Empresa: {norte.nombre}")
except Empresa.DoesNotExist:
    print("\n❌ Empresa Norte no encontrada")
    exit(1)

# 2. Buscar al Dr. Pedro Martínez
print("\n" + "=" * 70)
print("👨‍⚕️ BUSCAR ODONTÓLOGO")
print("=" * 70)

try:
    # Buscar por nombre en Usuario
    usuario = Usuario.objects.filter(
        nombre__icontains='Pedro',
        apellido__icontains='Martínez',
        empresa=norte
    ).first()
    
    if not usuario:
        print("\n❌ No se encontró usuario 'Pedro Martínez' en Norte")
        print("\nOdontólogos disponibles en Norte:")
        for odontologo in Odontologo.objects.filter(empresa=norte).select_related('codusuario'):
            print(f"  - {odontologo.codusuario.nombre} {odontologo.codusuario.apellido}")
        exit(1)
    
    print(f"\n✅ Usuario encontrado:")
    print(f"   Nombre: {usuario.nombre} {usuario.apellido}")
    print(f"   Email: {usuario.correoelectronico}")
    print(f"   Código: {usuario.codigo}")
    
    # Verificar si tiene perfil de Odontólogo
    try:
        odontologo = Odontologo.objects.get(codusuario=usuario)
        print(f"✅ Perfil de Odontólogo encontrado")
        print(f"   Especialidad: {odontologo.especialidad or 'No especificada'}")
        print(f"   Matrícula: {odontologo.nromatricula or 'No especificada'}")
    except Odontologo.DoesNotExist:
        print(f"❌ No tiene perfil de Odontólogo")
        exit(1)
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    exit(1)

# 3. Verificar horarios
print("\n" + "=" * 70)
print("📅 HORARIOS DISPONIBLES")
print("=" * 70)

horarios = Horario.objects.filter(
    cododontologo=odontologo,
    empresa=norte
).order_by('diasemana', 'horainicio')

if not horarios.exists():
    print("\n❌ No tiene horarios configurados")
else:
    print(f"\n✅ Tiene {horarios.count()} horarios configurados:\n")
    
    dias = {
        0: 'Lunes',
        1: 'Martes', 
        2: 'Miércoles',
        3: 'Jueves',
        4: 'Viernes',
        5: 'Sábado',
        6: 'Domingo'
    }
    
    for horario in horarios:
        dia_nombre = dias.get(horario.diasemana, f'Día {horario.diasemana}')
        print(f"  📌 {dia_nombre}")
        print(f"     Horario: {horario.horainicio.strftime('%H:%M')} - {horario.horafin.strftime('%H:%M')}")
        print(f"     ID: {horario.idhorario}")
        print()

# 4. Verificar consultas agendadas
from api.models import Consulta
from datetime import date, timedelta

print("=" * 70)
print("📋 CONSULTAS PRÓXIMAS (Próximos 7 días)")
print("=" * 70)

hoy = date.today()
fecha_limite = hoy + timedelta(days=7)

consultas = Consulta.objects.filter(
    cododontologo=odontologo,
    fecha__gte=hoy,
    fecha__lte=fecha_limite
).order_by('fecha', 'idhorario')

if not consultas.exists():
    print(f"\n✅ NO tiene consultas agendadas para los próximos 7 días")
    print(f"   Todas sus franjas horarias están LIBRES")
else:
    print(f"\n⚠️  Tiene {consultas.count()} consulta(s) agendada(s):\n")
    
    for consulta in consultas:
        print(f"  📅 {consulta.fecha}")
        print(f"     Horario: {consulta.idhorario}")
        print(f"     Paciente: {consulta.codpaciente.codusuario.nombre}")
        print(f"     Estado: {consulta.idestadoconsulta}")
        print()

print("=" * 70)
print("📊 RESUMEN")
print("=" * 70)

print(f"\n✅ Dr. {usuario.nombre} {usuario.apellido}")
print(f"   Horarios configurados: {horarios.count()}")
print(f"   Consultas próximas: {consultas.count()}")

if horarios.exists():
    if consultas.count() == 0:
        print(f"\n✅ DISPONIBILIDAD: ALTA - Todos los horarios están libres")
    elif consultas.count() < horarios.count():
        print(f"\n✅ DISPONIBILIDAD: MEDIA - Algunos horarios ocupados")
    else:
        print(f"\n⚠️  DISPONIBILIDAD: BAJA - Muchas consultas agendadas")
else:
    print(f"\n❌ No se puede agendar - No tiene horarios configurados")
