"""
Script para crear los Canales de Notificación necesarios
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from api.models_notifications import CanalNotificacion

def crear_canales():
    """Crea los canales de notificación necesarios"""
    canales = [
        {'id': 1, 'nombre': 'email', 'descripcion': 'Notificaciones por correo electrónico'},
        {'id': 2, 'nombre': 'push', 'descripcion': 'Notificaciones push móviles'},
        {'id': 3, 'nombre': 'sms', 'descripcion': 'Notificaciones por SMS'},
        {'id': 4, 'nombre': 'whatsapp', 'descripcion': 'Notificaciones por WhatsApp'},
    ]
    
    print("🔔 Creando canales de notificación...\n")
    
    for canal_data in canales:
        canal, created = CanalNotificacion.objects.get_or_create(
            id=canal_data['id'],
            defaults={
                'nombre': canal_data['nombre'],
                'descripcion': canal_data['descripcion'],
                'activo': True
            }
        )
        
        if created:
            print(f"✅ Canal creado: {canal.get_nombre_display()} (ID={canal.id})")
        else:
            print(f"ℹ️  Canal existente: {canal.get_nombre_display()} (ID={canal.id})")
    
    print(f"\n📊 Total de canales: {CanalNotificacion.objects.count()}")
    print("\n✅ Proceso completado")

if __name__ == '__main__':
    crear_canales()
