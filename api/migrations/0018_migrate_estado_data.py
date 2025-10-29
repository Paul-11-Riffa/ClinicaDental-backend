# Generated data migration to map old FK estados to new CharField
# Phase 1.2 Step 2: Migrate existing data

from django.db import migrations


def migrate_estado_data(apps, schema_editor):
    """
    Map existing idestadoconsulta FK values to new estado CharField.
    
    Based on database analysis:
    - Estadodeconsulta ID 1 = "Pendiente" → 'solicitada'
    - Estadodeconsulta ID 2 = "Confirmada" → 'confirmada'  
    - Estadodeconsulta ID 3 = "Completado" → 'completada'
    - Estadodeconsulta ID 4 = "Cancelado" → 'cancelada'
    - Estadodeconsulta ID 5 = "No Asistió" → 'no_asistio'
    - Estadodeconsulta ID 6 = "En Proceso" → 'en_consulta'
    """
    Consulta = apps.get_model('api', 'Consulta')
    Estadodeconsulta = apps.get_model('api', 'Estadodeconsulta')
    
    # Mapping dictionary (estado name → new CharField value)
    estado_mapping = {
        'Pendiente': 'solicitada',
        'Confirmada': 'confirmada',
        'Confirmado': 'confirmada',  # Alternative spelling
        'Completado': 'completada',
        'Completada': 'completada',  # Alternative spelling
        'Cancelado': 'cancelada',
        'Cancelada': 'cancelada',  # Alternative spelling
        'No Asistió': 'no_asistio',
        'No Asistio': 'no_asistio',  # Without accent
        'En Proceso': 'en_consulta',
        'En Consulta': 'en_consulta',
        'Diagnosticada': 'diagnosticada',
        'Con Plan': 'con_plan',
    }
    
    migrated_count = 0
    unmapped_estados = set()
    
    for consulta in Consulta.objects.all():
        if consulta.idestadoconsulta:
            old_estado_name = consulta.idestadoconsulta.estado
            new_estado = estado_mapping.get(old_estado_name)
            
            if new_estado:
                consulta.estado = new_estado
                consulta.save(update_fields=['estado'])
                migrated_count += 1
            else:
                # Track unmapped estados for reporting
                unmapped_estados.add(old_estado_name)
                # Default to 'solicitada' for safety
                consulta.estado = 'solicitada'
                consulta.save(update_fields=['estado'])
                migrated_count += 1
        else:
            # No FK estado - default to 'solicitada'
            consulta.estado = 'solicitada'
            consulta.save(update_fields=['estado'])
            migrated_count += 1
    
    print(f"✅ Migrated {migrated_count} consultas to new estado CharField")
    if unmapped_estados:
        print(f"⚠️  Unmapped estados (defaulted to 'solicitada'): {unmapped_estados}")


def reverse_migration(apps, schema_editor):
    """Reverse is not needed - just clear the estado field"""
    Consulta = apps.get_model('api', 'Consulta')
    Consulta.objects.all().update(estado=None)
    print("🔄 Cleared estado CharField values")


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_add_estado_charfield'),
    ]

    operations = [
        migrations.RunPython(migrate_estado_data, reverse_migration),
    ]
