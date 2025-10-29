# Generated migration for estado optimization (9 -> 8 estados)

from django.db import migrations


def actualizar_estado_solicitada_a_pendiente(apps, schema_editor):
    """
    Migra las consultas con estado='solicitada' a estado='pendiente'
    según la Opción B (Implementación Realista)
    """
    Consulta = apps.get_model('api', 'Consulta')
    
    # Actualizar solicitada -> pendiente
    consultas_solicitadas = Consulta.objects.filter(estado='solicitada')
    count = consultas_solicitadas.count()
    
    if count > 0:
        consultas_solicitadas.update(estado='pendiente')
        print(f"✅ Actualizadas {count} consultas: solicitada → pendiente")
    else:
        print("ℹ️ No hay consultas con estado 'solicitada'")


def revertir_cambios(apps, schema_editor):
    """
    Revierte los cambios (pendiente -> solicitada)
    """
    Consulta = apps.get_model('api', 'Consulta')
    
    # Solo las que no tienen idestadoconsulta FK apuntando a 'Pendiente'
    # serán revertidas a 'solicitada'
    consultas_pendientes = Consulta.objects.filter(estado='pendiente')
    count = consultas_pendientes.count()
    
    if count > 0:
        consultas_pendientes.update(estado='solicitada')
        print(f"🔄 Revertidas {count} consultas: pendiente → solicitada")


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_migrate_estado_data'),
    ]

    operations = [
        migrations.RunPython(
            actualizar_estado_solicitada_a_pendiente,
            reverse_code=revertir_cambios
        ),
    ]
