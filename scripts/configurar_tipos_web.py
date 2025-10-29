#!/usr/bin/env python
"""
Script para configurar tipos de consulta permitidos para agendamiento web

Ejecutar:
    python manage.py shell < scripts/configurar_tipos_web.py
O:
    python scripts/configurar_tipos_web.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from api.models import Tipodeconsulta, Empresa


def configurar_tipos_web():
    """Configura tipos de consulta para agendamiento web"""
    
    print("🔧 Configurando tipos de consulta para agendamiento web...\n")
    
    # ==========================================================================
    # TIPOS PERMITIDOS PARA AGENDAMIENTO WEB
    # ==========================================================================
    
    tipos_permitidos = [
        {
            'nombre': 'Consulta General',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 30
        },
        {
            'nombre': 'Primera Consulta',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 45
        },
        {
            'nombre': 'Urgencia',
            'permite_web': True,
            'es_urgencia': True,
            'requiere_aprobacion': False,
            'duracion': 30
        },
        {
            'nombre': 'Urgencia Dental',
            'permite_web': True,
            'es_urgencia': True,
            'requiere_aprobacion': False,
            'duracion': 30
        },
        {
            'nombre': 'Dolor Agudo',
            'permite_web': True,
            'es_urgencia': True,
            'requiere_aprobacion': False,
            'duracion': 30
        },
        {
            'nombre': 'Limpieza Dental',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 45
        },
        {
            'nombre': 'Control',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 20
        },
        {
            'nombre': 'Control Post-tratamiento',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 20
        },
        {
            'nombre': 'Revisión',
            'permite_web': True,
            'es_urgencia': False,
            'requiere_aprobacion': False,
            'duracion': 30
        },
    ]
    
    # Obtener todas las empresas
    empresas = Empresa.objects.all()
    
    if not empresas.exists():
        print("⚠️  No hay empresas registradas. Creando empresa de ejemplo...")
        empresa = Empresa.objects.create(
            nombre='Clínica Dental',
            subdomain='clinica',
            activo=True
        )
        empresas = [empresa]
    
    for empresa in empresas:
        print(f"\n📋 Configurando empresa: {empresa.nombre} ({empresa.subdomain})")
        print("=" * 60)
        
        for tipo_config in tipos_permitidos:
            try:
                # Intentar actualizar existente
                tipo = Tipodeconsulta.objects.get(
                    nombreconsulta=tipo_config['nombre'],
                    empresa=empresa
                )
                tipo.permite_agendamiento_web = tipo_config['permite_web']
                tipo.es_urgencia = tipo_config['es_urgencia']
                tipo.requiere_aprobacion = tipo_config['requiere_aprobacion']
                tipo.duracion_estimada = tipo_config['duracion']
                tipo.save()
                
                print(f"✅ {tipo_config['nombre']} (actualizado)")
                print(f"   - Agendamiento web: {tipo_config['permite_web']}")
                print(f"   - Urgencia: {tipo_config['es_urgencia']}")
                print(f"   - Duración: {tipo_config['duracion']} min")
                
            except Tipodeconsulta.DoesNotExist:
                # Crear nuevo
                print(f"⚠️  {tipo_config['nombre']} no existe, creando...")
                tipo = Tipodeconsulta.objects.create(
                    nombreconsulta=tipo_config['nombre'],
                    empresa=empresa,
                    permite_agendamiento_web=tipo_config['permite_web'],
                    es_urgencia=tipo_config['es_urgencia'],
                    requiere_aprobacion=tipo_config['requiere_aprobacion'],
                    duracion_estimada=tipo_config['duracion']
                )
                print(f"   ✅ Creado")
        
        # ==========================================================================
        # TIPOS NO PERMITIDOS (asegurar que estén deshabilitados)
        # ==========================================================================
        
        tipos_no_permitidos = [
            'Cirugía',
            'Extracción',
            'Extracción de Muela',
            'Ortodoncia',
            'Endodoncia',
            'Implante',
            'Implantes',
            'Tratamiento Especializado',
            'Blanqueamiento',
            'Carillas',
            'Corona',
            'Puente',
            'Prótesis'
        ]
        
        print("\n🚫 Deshabilitando agendamiento web para tipos especiales...")
        print("=" * 60)
        
        for nombre in tipos_no_permitidos:
            tipos_encontrados = Tipodeconsulta.objects.filter(
                nombreconsulta__icontains=nombre,
                empresa=empresa
            )
            
            for tipo in tipos_encontrados:
                tipo.permite_agendamiento_web = False
                tipo.requiere_aprobacion = True
                tipo.save()
                print(f"✅ {tipo.nombreconsulta} - Web deshabilitado")
    
    print("\n" + "=" * 60)
    print("✅ Configuración completada!")
    print("\nResumen:")
    
    for empresa in empresas:
        total = Tipodeconsulta.objects.filter(empresa=empresa).count()
        permitidos = Tipodeconsulta.objects.filter(
            empresa=empresa,
            permite_agendamiento_web=True
        ).count()
        urgencias = Tipodeconsulta.objects.filter(
            empresa=empresa,
            es_urgencia=True
        ).count()
        
        print(f"\n{empresa.nombre}:")
        print(f"  - Total de tipos: {total}")
        print(f"  - Permitidos para web: {permitidos}")
        print(f"  - Marcados como urgencia: {urgencias}")


if __name__ == '__main__':
    configurar_tipos_web()
