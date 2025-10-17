#!/usr/bin/env python
"""
Script para diagnosticar problema con consentimientos
"""
import os
import sys
import django
from pathlib import Path
from datetime import date, datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from api.models import Consulta, Usuario, Paciente, Consentimiento
from django.contrib.auth import get_user_model

User = get_user_model()

print("="*80)
print("🔍 DIAGNÓSTICO DE CONSENTIMIENTOS")
print("="*80)

# Obtener pacientes
pacientes = Paciente.objects.all()

if not pacientes.exists():
    print("\n❌ No hay pacientes en el sistema")
    sys.exit(1)

print(f"\n📊 PACIENTES EN EL SISTEMA: {pacientes.count()}")

for paciente in pacientes:
    usuario = paciente.codusuario
    print(f"\n{'='*80}")
    print(f"👤 Paciente: {usuario.nombre} {usuario.apellido}")
    print(f"   Email: {usuario.correoelectronico}")
    print(f"   ID Paciente: {paciente.codusuario_id}")
    print(f"   Empresa: {usuario.empresa.nombre if usuario.empresa else 'Sin empresa'}")
    
    # Buscar citas del paciente
    citas = Consulta.objects.filter(codpaciente=paciente).order_by('-fecha')
    print(f"\n   📅 CITAS: {citas.count()}")
    
    if citas.exists():
        hoy = date.today()
        
        for cita in citas:
            fecha_cita = cita.fecha
            es_futura = fecha_cita >= hoy
            dias_diff = (fecha_cita - hoy).days
            
            print(f"\n   ---")
            print(f"   Cita ID: {cita.id}")
            print(f"   Fecha: {cita.fecha}")
            print(f"   Hora: {cita.idhorario.hora if cita.idhorario else 'N/A'}")
            print(f"   Tipo: {cita.idtipoconsulta.nombreconsulta if cita.idtipoconsulta else 'N/A'}")
            print(f"   Estado: {cita.idestadoconsulta.estado if cita.idestadoconsulta else 'N/A'}")
            print(f"   Odontólogo: {cita.cododontologo.codusuario.nombre if cita.cododontologo else 'N/A'} {cita.cododontologo.codusuario.apellido if cita.cododontologo else ''}")
            
            # Mostrar si es futura o pasada
            if es_futura:
                if dias_diff == 0:
                    print(f"   ⏰ Estado temporal: HOY")
                else:
                    print(f"   ✅ Estado temporal: FUTURA (en {dias_diff} días)")
                print(f"   ℹ️  Debería aparecer botón de consentimiento")
            else:
                print(f"   ❌ Estado temporal: PASADA (hace {abs(dias_diff)} días)")
                print(f"   ℹ️  NO aparecerá botón de consentimiento")
            
            # Verificar si tiene consentimiento firmado
            try:
                consentimiento = Consentimiento.objects.get(consulta=cita)
                print(f"   ✅ Consentimiento: FIRMADO")
                print(f"      ID: {consentimiento.id}")
                print(f"      Fecha firma: {consentimiento.fecha_firma if hasattr(consentimiento, 'fecha_firma') else 'N/A'}")
                print(f"   ℹ️  NO aparecerá botón (ya está firmado)")
            except Consentimiento.DoesNotExist:
                print(f"   ⚠️  Consentimiento: NO FIRMADO")
                if es_futura:
                    print(f"   ✅ SÍ debería aparecer botón para firmar")
                else:
                    print(f"   ❌ NO aparecerá botón (cita pasada)")
            except Consentimiento.MultipleObjectsReturned:
                consentimientos = Consentimiento.objects.filter(consulta=cita)
                print(f"   ⚠️  ADVERTENCIA: Múltiples consentimientos ({consentimientos.count()})")
                for idx, c in enumerate(consentimientos, 1):
                    print(f"      {idx}. ID: {c.id}")
    else:
        print(f"   ℹ️  Este paciente no tiene citas agendadas")

# Resumen general
print(f"\n{'='*80}")
print("📊 RESUMEN GENERAL")
print("="*80)

total_citas = Consulta.objects.count()
citas_futuras = Consulta.objects.filter(fecha__gte=date.today()).count()
citas_pasadas = Consulta.objects.filter(fecha__lt=date.today()).count()
total_consentimientos = Consentimiento.objects.count()

print(f"\n✅ Total de citas: {total_citas}")
print(f"   - Futuras/Hoy: {citas_futuras}")
print(f"   - Pasadas: {citas_pasadas}")
print(f"\n✅ Consentimientos firmados: {total_consentimientos}")

if citas_futuras > 0:
    citas_futuras_sin_consentimiento = 0
    for cita in Consulta.objects.filter(fecha__gte=date.today()):
        if not Consentimiento.objects.filter(consulta=cita).exists():
            citas_futuras_sin_consentimiento += 1
    
    print(f"\n📝 Citas futuras SIN consentimiento: {citas_futuras_sin_consentimiento}")
    
    if citas_futuras_sin_consentimiento > 0:
        print("\n✅ SOLUCIÓN: En estas citas DEBERÍA aparecer el botón de firmar consentimiento")
    else:
        print("\n✅ Todas las citas futuras tienen consentimiento firmado")

# Problema común
print(f"\n{'='*80}")
print("❓ ¿POR QUÉ NO APARECE EL BOTÓN?")
print("="*80)

print("""
El botón "Firmar Consentimiento" solo aparece si:

1. ✅ La cita es HOY o FUTURA (no pasada)
2. ✅ La cita NO está cancelada ni finalizada
3. ✅ El consentimiento NO ha sido firmado

Si no aparece el botón, verifica:
- ¿La fecha de la cita ya pasó?
- ¿La cita está cancelada o finalizada?
- ¿Ya firmaste el consentimiento para esta cita?

SOLUCIÓN:
- Si la cita es pasada: Agenda una nueva cita
- Si ya está firmado: No necesitas firmarlo de nuevo
- Si es futura y no aparece: Revisa la consola del navegador
""")

print("="*80)
