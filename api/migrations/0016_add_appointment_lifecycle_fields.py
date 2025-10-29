# Generated migration for adding appointment lifecycle fields to Consulta model
# Phase 1.1: Add all new fields (all nullable for backward compatibility)

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_flujo_clinico_paso2_data'),
    ]

    operations = [
        # Appointment request fields
        migrations.AddField(
            model_name='consulta',
            name='fecha_preferida',
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Fecha que el paciente prefiere (antes de confirmar)"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='hora_preferida',
            field=models.CharField(
                max_length=10,
                null=True,
                blank=True,
                help_text="Hora que el paciente prefiere (antes de confirmar)"
            ),
        ),
        
        # Confirmed appointment fields
        migrations.AddField(
            model_name='consulta',
            name='fecha_consulta',
            field=models.DateField(
                null=True,
                blank=True,
                help_text="Fecha confirmada de la consulta"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='hora_consulta',
            field=models.TimeField(
                null=True,
                blank=True,
                help_text="Hora confirmada de la consulta"
            ),
        ),
        
        # Workflow timestamp fields
        migrations.AddField(
            model_name='consulta',
            name='hora_llegada',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Momento en que el paciente llegó (check-in)"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='hora_inicio_consulta',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Momento en que comenzó la consulta"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='hora_fin_consulta',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Momento en que terminó la consulta"
            ),
        ),
        
        # Appointment type and metadata
        migrations.AddField(
            model_name='consulta',
            name='tipo_consulta',
            field=models.CharField(
                max_length=20,
                null=True,  # Nullable for backward compatibility
                blank=True,
                choices=[
                    ('primera_vez', 'Primera Vez'),
                    ('control', 'Control'),
                    ('tratamiento', 'Tratamiento'),
                    ('urgencia', 'Urgencia'),
                ],
                help_text="Tipo de consulta solicitada"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='motivo_consulta',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Razón por la que el paciente solicita la cita"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='notas_recepcion',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Notas de la recepcionista al confirmar/gestionar la cita"
            ),
        ),
        
        # Cancellation
        migrations.AddField(
            model_name='consulta',
            name='motivo_cancelacion',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Motivo de cancelación de la cita"
            ),
        ),
        
        # Duration
        migrations.AddField(
            model_name='consulta',
            name='duracion_estimada',
            field=models.IntegerField(
                null=True,  # Nullable for backward compatibility
                blank=True,
                help_text="Duración estimada en minutos"
            ),
        ),
        
        # Clinical text fields (that should have existed)
        migrations.AddField(
            model_name='consulta',
            name='observaciones',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Observaciones generales"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='diagnostico',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Diagnóstico del odontólogo"
            ),
        ),
        migrations.AddField(
            model_name='consulta',
            name='tratamiento',
            field=models.TextField(
                null=True,
                blank=True,
                help_text="Tratamiento recomendado"
            ),
        ),
    ]
