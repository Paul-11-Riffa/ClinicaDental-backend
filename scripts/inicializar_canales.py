"""
Script para inicializar canales de notificación básicos

Este script debe ejecutarse ANTES de correr tests o en el setUp de los tests
para asegurar que los canales necesarios existen en la BD.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models_notifications import CanalNotificacion

def inicializar_canales():
    """
    Crea los canales de notificación básicos si no existen.
    
    Retorna:
        dict: Diccionario con los canales creados/existentes
    """
    canales = {}
    canales_config = [
        ('email', 'Correo Electrónico', True),
        ('push', 'Notificación Push', True),
        ('sms', 'SMS', False),
        ('whatsapp', 'WhatsApp', False),
    ]
    
    print("Inicializando canales de notificación...")
    
    for nombre, descripcion, activo in canales_config:
        canal, created = CanalNotificacion.objects.get_or_create(
            nombre=nombre,
            defaults={
                'descripcion': descripcion,
                'activo': activo
            }
        )
        canales[nombre] = canal
        status = "✅ Creado" if created else "ℹ️  Ya existe"
        print(f"  {status}: {nombre} (ID: {canal.id})")
    
    return canales

if __name__ == '__main__':
    try:
        canales = inicializar_canales()
        print(f"\n✅ {len(canales)} canales de notificación disponibles")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
