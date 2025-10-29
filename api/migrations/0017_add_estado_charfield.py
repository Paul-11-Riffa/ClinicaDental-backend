# Generated migration for adding estado CharField alongside existing FK
# Phase 1.2 Step 1: Add new estado field (temporary nullable)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_add_appointment_lifecycle_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='consulta',
            name='estado',
            field=models.CharField(
                max_length=20,
                null=True,  # Temporary - will remove after data migration
                blank=True,
                choices=[
                    ('solicitada', 'Solicitada'),
                    ('confirmada', 'Confirmada'),
                    ('paciente_presente', 'Paciente Presente'),
                    ('en_consulta', 'En Consulta'),
                    ('diagnosticada', 'Diagnosticada'),
                    ('con_plan', 'Con Plan'),
                    ('completada', 'Completada'),
                    ('cancelada', 'Cancelada'),
                    ('no_asistio', 'No Asistió'),
                ],
                help_text="Estado del ciclo de vida de la cita"
            ),
        ),
    ]
