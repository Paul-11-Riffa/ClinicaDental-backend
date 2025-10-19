"""
Script para crear servicios de ejemplo en el catálogo
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from decimal import Decimal
from api.models import Empresa, Servicio

def crear_servicios_ejemplo():
    """Crea servicios de ejemplo para la clínica"""
    
    # Obtener la empresa SmileStudio
    try:
        empresa = Empresa.objects.get(subdomain='smilestudio')
        print(f"✅ Empresa encontrada: {empresa.nombre}")
    except Empresa.DoesNotExist:
        print("❌ Error: No se encontró la empresa 'smilestudio'")
        print("Empresas disponibles:")
        for emp in Empresa.objects.all():
            print(f"  - {emp.subdomain}: {emp.nombre}")
        return
    
    # Servicios de ejemplo
    servicios_data = [
        {
            'nombre': 'Limpieza Dental Profesional',
            'descripcion': 'Limpieza dental completa con ultrasonido, incluye pulido, fluorización y revisión de encías. Elimina sarro y placa bacteriana.',
            'costobase': Decimal('150.00'),
            'duracion': 45,
            'activo': True
        },
        {
            'nombre': 'Blanqueamiento Dental',
            'descripcion': 'Blanqueamiento dental profesional con gel de peróxido de hidrógeno. Resultados visibles desde la primera sesión. Incluye protector de encías.',
            'costobase': Decimal('400.00'),
            'duracion': 60,
            'activo': True
        },
        {
            'nombre': 'Consulta General',
            'descripcion': 'Consulta dental general con revisión completa, diagnóstico y plan de tratamiento. Incluye rayos X si es necesario.',
            'costobase': Decimal('50.00'),
            'duracion': 30,
            'activo': True
        },
        {
            'nombre': 'Endodoncia (Tratamiento de Conducto)',
            'descripcion': 'Tratamiento de conducto completo para salvar dientes con infección o daño en la pulpa. Incluye anestesia local y medicación.',
            'costobase': Decimal('800.00'),
            'duracion': 90,
            'activo': True
        },
        {
            'nombre': 'Ortodoncia Mensual',
            'descripcion': 'Control mensual de ortodoncia con brackets metálicos. Incluye ajuste de brackets, cambio de ligas y revisión de progreso.',
            'costobase': Decimal('200.00'),
            'duracion': 30,
            'activo': True
        },
        {
            'nombre': 'Extracción Simple',
            'descripcion': 'Extracción dental simple con anestesia local. Incluye medicación post-operatoria y recomendaciones de cuidado.',
            'costobase': Decimal('150.00'),
            'duracion': 30,
            'activo': True
        },
        {
            'nombre': 'Corona Dental',
            'descripcion': 'Corona de porcelana o metal-porcelana para restaurar dientes dañados. Incluye toma de impresión y colocación.',
            'costobase': Decimal('1200.00'),
            'duracion': 60,
            'activo': True
        },
        {
            'nombre': 'Implante Dental',
            'descripcion': 'Implante de titanio de alta calidad con corona incluida. Solución permanente para reemplazar dientes perdidos.',
            'costobase': Decimal('2500.00'),
            'duracion': 120,
            'activo': True
        }
    ]
    
    print(f"\n{'='*60}")
    print(f"Creando servicios para: {empresa.nombre}")
    print(f"{'='*60}\n")
    
    servicios_creados = 0
    servicios_existentes = 0
    
    for servicio_data in servicios_data:
        # Verificar si ya existe
        existe = Servicio.objects.filter(
            nombre=servicio_data['nombre'],
            empresa=empresa
        ).exists()
        
        if existe:
            print(f"⚠️  Ya existe: {servicio_data['nombre']}")
            servicios_existentes += 1
        else:
            servicio = Servicio.objects.create(
                empresa=empresa,
                **servicio_data
            )
            print(f"✅ Creado: {servicio.nombre} - ${servicio.costobase} ({servicio.duracion} min)")
            servicios_creados += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Resumen:")
    print(f"  ✅ Servicios creados: {servicios_creados}")
    print(f"  ⚠️  Servicios existentes: {servicios_existentes}")
    print(f"  📝 Total de servicios en catálogo: {Servicio.objects.filter(empresa=empresa, activo=True).count()}")
    print(f"{'='*60}\n")
    
    # Mostrar todos los servicios activos
    print("🔍 Servicios activos en el catálogo:\n")
    servicios = Servicio.objects.filter(empresa=empresa, activo=True).order_by('nombre')
    for i, servicio in enumerate(servicios, 1):
        print(f"{i}. {servicio.nombre}")
        print(f"   💰 Precio: ${servicio.costobase}")
        print(f"   ⏱️  Duración: {servicio.duracion} minutos")
        print()

if __name__ == '__main__':
    print("🏥 Script de Creación de Servicios de Ejemplo\n")
    crear_servicios_ejemplo()
    print("✅ Proceso completado!")
