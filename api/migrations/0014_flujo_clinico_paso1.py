"""
PASO 2: Primera Migración Incremental - Flujo Clínico
======================================================

Esta migración agrega los campos necesarios para el flujo clínico correcto
SIN afectar el funcionamiento actual del sistema.

Estrategia:
- Todos los campos son NULLABLE al inicio
- No se modifican campos existentes
- Se mantienen las FK a Estado (por ahora)
- Los datos existentes NO se afectan

Ejecutar:
    python manage.py makemigrations --name flujo_clinico_paso1
    python manage.py migrate

"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_cambio_related_name_pagos'),
    ]

    operations = [
        # ========================================
        # 1. CONSULTA: Agregar campos de flujo
        # ========================================
        
        # Costo de la consulta
        migrations.AddField(
            model_name='consulta',
            name='costo_consulta',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                max_digits=10,
                help_text='Costo de la consulta (si aplica)'
            ),
        ),
        
        # Requiere pago previo
        migrations.AddField(
            model_name='consulta',
            name='requiere_pago',
            field=models.BooleanField(
                default=False,
                help_text='Indica si esta consulta requiere pago previo'
            ),
        ),
        
        # Vinculación con plan (para consultas de ejecución)
        migrations.AddField(
            model_name='consulta',
            name='plan_tratamiento',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='consultas_ejecucion',
                to='api.plandetratamiento',
                help_text='Plan al que pertenece esta consulta (si es de ejecución)'
            ),
        ),
        
        # Pago asociado a la consulta
        migrations.AddField(
            model_name='consulta',
            name='pago_consulta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='consulta_pagada',
                to='api.pagoenlinea',
                help_text='Pago asociado a esta consulta'
            ),
        ),
        
        # ========================================
        # 2. PLANDETRATAMIENTO: Agregar origen
        # ========================================
        
        # Consulta de diagnóstico que originó el plan
        migrations.AddField(
            model_name='plandetratamiento',
            name='consulta_diagnostico',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='planes_generados',
                to='api.consulta',
                help_text='Consulta de diagnóstico que originó este plan'
            ),
        ),
        
        # Estado específico del tratamiento (CharField)
        migrations.AddField(
            model_name='plandetratamiento',
            name='estado_tratamiento',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('Propuesto', 'Propuesto (Pendiente de aceptación)'),
                    ('Aceptado', 'Aceptado por paciente'),
                    ('En Ejecución', 'En ejecución'),
                    ('Completado', 'Completado'),
                    ('Cancelado', 'Cancelado'),
                    ('Pausado', 'Pausado'),
                ],
                default='Propuesto',
                help_text='Estado actual del plan de tratamiento'
            ),
        ),
        
        # Fecha de inicio de ejecución
        migrations.AddField(
            model_name='plandetratamiento',
            name='fecha_inicio_ejecucion',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Fecha en que comenzó la ejecución (primer servicio)'
            ),
        ),
        
        # Fecha de finalización
        migrations.AddField(
            model_name='plandetratamiento',
            name='fecha_finalizacion',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Fecha de finalización del plan completo'
            ),
        ),
        
        # ========================================
        # 3. ITEMPLANDETRATAMIENTO: Agregar ejecución
        # ========================================
        
        # Consulta donde se ejecutó el item
        migrations.AddField(
            model_name='itemplandetratamiento',
            name='consulta_ejecucion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items_ejecutados',
                to='api.consulta',
                help_text='Consulta en la que se ejecutó este item'
            ),
        ),
        
        # Fecha de ejecución
        migrations.AddField(
            model_name='itemplandetratamiento',
            name='fecha_ejecucion',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Fecha y hora en que se ejecutó el servicio'
            ),
        ),
        
        # Odontólogo que ejecutó
        migrations.AddField(
            model_name='itemplandetratamiento',
            name='odontologo_ejecutor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='items_ejecutados',
                to='api.odontologo',
                help_text='Odontólogo que ejecutó este servicio'
            ),
        ),
        
        # Orden de ejecución
        migrations.AddField(
            model_name='itemplandetratamiento',
            name='orden_ejecucion',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Orden sugerido de ejecución (1, 2, 3...)'
            ),
        ),
        
        # Notas de ejecución
        migrations.AddField(
            model_name='itemplandetratamiento',
            name='notas_ejecucion',
            field=models.TextField(
                blank=True,
                null=True,
                help_text='Notas del odontólogo al ejecutar el servicio'
            ),
        ),
        
        # ========================================
        # 4. ÍNDICES para mejorar performance
        # ========================================
        
        migrations.AddIndex(
            model_name='consulta',
            index=models.Index(fields=['plan_tratamiento'], name='idx_consulta_plan'),
        ),
        
        migrations.AddIndex(
            model_name='plandetratamiento',
            index=models.Index(fields=['consulta_diagnostico'], name='idx_plan_consulta'),
        ),
        
        migrations.AddIndex(
            model_name='plandetratamiento',
            index=models.Index(fields=['estado_tratamiento'], name='idx_plan_estado_trat'),
        ),
        
        migrations.AddIndex(
            model_name='itemplandetratamiento',
            index=models.Index(fields=['consulta_ejecucion'], name='idx_item_consulta'),
        ),
        
        migrations.AddIndex(
            model_name='itemplandetratamiento',
            index=models.Index(fields=['estado_item'], name='idx_item_estado'),
        ),
    ]
