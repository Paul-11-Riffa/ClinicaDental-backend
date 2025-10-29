"""
Script de diagnóstico para agendamiento web

Analiza la estructura de la base de datos y configuración
para identificar problemas y crear datos necesarios.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import connection
from api.models import Consulta, Tipodeconsulta, Horario
from api.models_notifications import CanalNotificacion

def analizar_estructura():
    """Analiza la estructura de tablas relevantes"""
    print("=" * 80)
    print("DIAGNÓSTICO DE AGENDAMIENTO WEB")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        # 1. Analizar tabla Consulta
        print("\n1. ESTRUCTURA DE TABLA 'consulta':")
        print("-" * 80)
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'consulta'
            AND column_name IN (
                'idhorario', 'cododontologo', 'codrecepcionista',
                'horario_preferido', 'agendado_por_web', 'prioridad',
                'created_at', 'updated_at'
            )
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print(f"{'Campo':<25} {'Tipo':<20} {'Nullable':<10} {'Default':<20}")
            print("-" * 80)
            for col in columns:
                print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {str(col[3]):<20}")
        else:
            print("⚠️  No se encontraron los campos esperados")
        
        # 2. Verificar constraints
        print("\n2. CONSTRAINTS DE TABLA 'consulta':")
        print("-" * 80)
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.constraint_type,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            LEFT JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            LEFT JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = 'consulta'
            AND kcu.column_name IN ('idhorario', 'cododontologo', 'codrecepcionista')
            ORDER BY tc.constraint_type, kcu.column_name;
        """)
        
        constraints = cursor.fetchall()
        if constraints:
            print(f"{'Constraint':<40} {'Tipo':<15} {'Columna':<20} {'FK Tabla':<20}")
            print("-" * 80)
            for cons in constraints:
                print(f"{cons[0]:<40} {cons[1]:<15} {cons[2]:<20} {str(cons[3]):<20}")
        
        # 3. Verificar CanalNotificacion
        print("\n3. CANALES DE NOTIFICACIÓN:")
        print("-" * 80)
        canales = CanalNotificacion.objects.all()
        if canales.exists():
            print(f"{'ID':<5} {'Nombre':<20} {'Activo':<10}")
            print("-" * 80)
            for canal in canales:
                print(f"{canal.id:<5} {canal.nombre:<20} {str(canal.activo):<10}")
        else:
            print("⚠️  NO HAY CANALES DE NOTIFICACIÓN EN LA BASE DE DATOS")
            print("   Esto causará errores cuando las señales intenten crear notificaciones")
        
        # 4. Verificar tipos de consulta
        print("\n4. TIPOS DE CONSULTA PERMITIDOS PARA WEB:")
        print("-" * 80)
        tipos = Tipodeconsulta.objects.filter(permite_agendamiento_web=True)
        if tipos.exists():
            print(f"{'ID':<5} {'Nombre':<30} {'Es Urgencia':<15} {'Duración':<10}")
            print("-" * 80)
            for tipo in tipos:
                print(f"{tipo.id:<5} {tipo.nombreconsulta:<30} {str(tipo.es_urgencia):<15} {tipo.duracion_estimada:<10}")
        else:
            print("⚠️  NO HAY TIPOS DE CONSULTA PERMITIDOS PARA AGENDAMIENTO WEB")
        
        # 5. Verificar horarios disponibles
        print("\n5. HORARIOS DISPONIBLES:")
        print("-" * 80)
        horarios = Horario.objects.all()[:5]
        if horarios.exists():
            print(f"Total de horarios: {Horario.objects.count()}")
            print("\nPrimeros 5:")
            for horario in horarios:
                print(f"  - ID {horario.id}: {horario.hora}")
        else:
            print("⚠️  NO HAY HORARIOS EN LA BASE DE DATOS")
        
        # 6. Verificar índices
        print("\n6. ÍNDICES EN TABLA 'consulta':")
        print("-" * 80)
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'consulta'
            AND indexname LIKE '%empresa%' OR indexname LIKE '%agendado%'
            ORDER BY indexname;
        """)
        
        indices = cursor.fetchall()
        if indices:
            for idx in indices:
                print(f"  - {idx[0]}")
        else:
            print("  No hay índices específicos para empresa o agendado_por_web")
            print("  💡 Recomendación: Agregar índices para mejor performance")

def crear_datos_basicos():
    """Crea datos básicos necesarios si no existen"""
    print("\n" + "=" * 80)
    print("CREANDO DATOS BÁSICOS NECESARIOS")
    print("=" * 80)
    
    # 1. Crear canales de notificación
    print("\n1. Canales de Notificación:")
    canales_necesarios = ['email', 'push', 'sms', 'whatsapp']
    for nombre_canal in canales_necesarios:
        canal, created = CanalNotificacion.objects.get_or_create(
            nombre=nombre_canal,
            defaults={
                'descripcion': f'Canal de {nombre_canal}',
                'activo': True
            }
        )
        status = "✅ Creado" if created else "ℹ️  Ya existe"
        print(f"   {status}: {nombre_canal} (ID: {canal.id})")

def verificar_migraciones():
    """Verifica estado de migraciones"""
    print("\n" + "=" * 80)
    print("VERIFICANDO MIGRACIONES")
    print("=" * 80)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT app, name, applied
            FROM django_migrations
            WHERE app = 'api'
            ORDER BY applied DESC
            LIMIT 5;
        """)
        
        migrations = cursor.fetchall()
        print("\nÚltimas 5 migraciones aplicadas:")
        for mig in migrations:
            print(f"  - {mig[1]} ({mig[2]})")
        
        # Verificar migración específica de agendamiento web
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM django_migrations
                WHERE app = 'api' AND name = '0020_agendamiento_web'
            );
        """)
        
        tiene_migracion = cursor.fetchone()[0]
        if tiene_migracion:
            print("\n✅ Migración 0020_agendamiento_web está aplicada")
        else:
            print("\n⚠️  Migración 0020_agendamiento_web NO está aplicada")
            print("   Ejecutar: python manage.py migrate api")

def generar_recomendaciones():
    """Genera recomendaciones basadas en el análisis"""
    print("\n" + "=" * 80)
    print("RECOMENDACIONES")
    print("=" * 80)
    
    recomendaciones = []
    
    # Verificar si existen canales
    if not CanalNotificacion.objects.exists():
        recomendaciones.append({
            'prioridad': '🔴 CRÍTICO',
            'item': 'Crear canales de notificación',
            'accion': 'Ejecutar: crear_datos_basicos() en este script'
        })
    
    # Verificar tipos de consulta
    if not Tipodeconsulta.objects.filter(permite_agendamiento_web=True).exists():
        recomendaciones.append({
            'prioridad': '🔴 CRÍTICO',
            'item': 'Configurar tipos de consulta para web',
            'accion': 'Ejecutar: python scripts/configurar_tipos_web.py'
        })
    
    # Verificar campo created_at
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'consulta' AND column_name = 'created_at'
            );
        """)
        tiene_created_at = cursor.fetchone()[0]
    
    if not tiene_created_at:
        recomendaciones.append({
            'prioridad': '🟡 ALTA',
            'item': 'Agregar campos created_at y updated_at',
            'accion': 'Crear migración 0021 con timestamps'
        })
    
    # Verificar índices
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'consulta' 
                AND indexname LIKE '%empresa%agendado%'
            );
        """)
        tiene_indice = cursor.fetchone()[0]
    
    if not tiene_indice:
        recomendaciones.append({
            'prioridad': '🟢 MEDIA',
            'item': 'Agregar índices para mejor performance',
            'accion': 'CREATE INDEX idx_consulta_web ON consulta(empresa_id, agendado_por_web, estado);'
        })
    
    if recomendaciones:
        for i, rec in enumerate(recomendaciones, 1):
            print(f"\n{i}. {rec['prioridad']} - {rec['item']}")
            print(f"   Acción: {rec['accion']}")
    else:
        print("\n✅ No se encontraron problemas críticos")
        print("   El sistema está correctamente configurado")

if __name__ == '__main__':
    try:
        print("\nIniciando diagnóstico...\n")
        
        # Ejecutar análisis
        analizar_estructura()
        verificar_migraciones()
        crear_datos_basicos()
        generar_recomendaciones()
        
        print("\n" + "=" * 80)
        print("DIAGNÓSTICO COMPLETADO")
        print("=" * 80)
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERROR durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()
