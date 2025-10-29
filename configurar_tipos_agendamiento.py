#!/usr/bin/env python
"""
Script para configurar tipos de consulta para agendamiento web.

Este script actualiza los tipos de consulta más comunes para permitir
que los pacientes los agenden desde la web.

Uso:
    python configurar_tipos_agendamiento.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models import Tipodeconsulta


def configurar_tipos_agendamiento():
    """
    Configura tipos de consulta para permitir agendamiento web.
    """

    print("\n" + "="*70)
    print("CONFIGURANDO TIPOS DE CONSULTA PARA AGENDAMIENTO WEB")
    print("="*70 + "\n")

    # Tipos que se permitirán agendar por web
    # Estos son los más comunes y seguros para que pacientes agenden
    tipos_permitidos = [
        {
            'nombres': ['Consulta General', 'Primera Consulta', 'Consulta Inicial'],
            'duracion': 30,
            'es_urgencia': False,
            'requiere_aprobacion': False
        },
        {
            'nombres': ['Control', 'Control Post-tratamiento', 'Revisión'],
            'duracion': 20,
            'es_urgencia': False,
            'requiere_aprobacion': False
        },
        {
            'nombres': ['Limpieza Dental', 'Profilaxis', 'Higiene Dental'],
            'duracion': 45,
            'es_urgencia': False,
            'requiere_aprobacion': False
        },
        {
            'nombres': ['Blanqueamiento'],
            'duracion': 60,
            'es_urgencia': False,
            'requiere_aprobacion': True  # Requiere aprobación porque es estético
        },
        {
            'nombres': ['Urgencia', 'Urgencia Dental', 'Emergencia', 'Dolor Agudo'],
            'duracion': 30,
            'es_urgencia': True,
            'requiere_aprobacion': False
        }
    ]

    total_actualizados = 0

    for config in tipos_permitidos:
        nombres = config['nombres']
        duracion = config['duracion']
        es_urgencia = config['es_urgencia']
        requiere_aprobacion = config['requiere_aprobacion']

        for nombre in nombres:
            # Buscar tipos que coincidan (insensible a mayúsculas/minúsculas)
            tipos = Tipodeconsulta.objects.filter(
                nombreconsulta__icontains=nombre
            )

            count = tipos.count()
            if count > 0:
                # Actualizar todos los que coincidan
                tipos.update(
                    permite_agendamiento_web=True,
                    duracion_estimada=duracion,
                    es_urgencia=es_urgencia,
                    requiere_aprobacion=requiere_aprobacion
                )

                total_actualizados += count

                urgencia_text = " [URGENCIA]" if es_urgencia else ""
                aprobacion_text = " [REQUIERE APROBACION]" if requiere_aprobacion else ""

                print(f"[OK] {nombre}: {count} tipo(s) configurado(s) "
                      f"({duracion} min){urgencia_text}{aprobacion_text}")

    print(f"\n{'='*70}")
    print(f"TOTAL: {total_actualizados} tipos de consulta configurados")
    print(f"{'='*70}\n")

    # Mostrar resumen de tipos configurados
    tipos_web = Tipodeconsulta.objects.filter(permite_agendamiento_web=True)

    if tipos_web.exists():
        print("\n[RESUMEN] Tipos disponibles para agendamiento web:")
        print("-" * 70)
        for tipo in tipos_web.order_by('nombreconsulta'):
            urgencia = " [URGENCIA]" if tipo.es_urgencia else ""
            aprobacion = " [APROBACION]" if tipo.requiere_aprobacion else ""
            print(f"  - {tipo.nombreconsulta} ({tipo.duracion_estimada} min){urgencia}{aprobacion}")
        print("-" * 70)
        print(f"Total: {tipos_web.count()} tipos\n")
    else:
        print("\n[WARNING] No se configuraron tipos para agendamiento web")
        print("  Verifica que existan tipos con los nombres especificados\n")

    # Tipos NO configurados (para referencia)
    tipos_no_web = Tipodeconsulta.objects.filter(permite_agendamiento_web=False)

    if tipos_no_web.exists():
        print(f"\n[INFO] Tipos NO disponibles para agendamiento web: {tipos_no_web.count()}")
        print("  (Estos requieren gestión por staff)")
        if tipos_no_web.count() <= 10:
            for tipo in tipos_no_web.order_by('nombreconsulta'):
                print(f"  - {tipo.nombreconsulta}")
        else:
            print("  Use: python manage.py shell")
            print("  > from api.models import Tipodeconsulta")
            print("  > Tipodeconsulta.objects.filter(permite_agendamiento_web=False)")
        print()


def main():
    """Función principal"""
    try:
        configurar_tipos_agendamiento()

        print("[SUCCESS] Configuración completada exitosamente")
        print("\n[NEXT STEPS]")
        print("  1. Reiniciar servidor: python manage.py runserver")
        print("  2. Probar agendamiento web en el frontend")
        print("  3. Verificar que los tipos aparezcan correctamente\n")

    except Exception as e:
        print(f"\n[ERROR] Error al configurar tipos: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
