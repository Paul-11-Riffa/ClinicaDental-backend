"""
Script para configurar contraseñas de prueba para todos los usuarios
Ejecutar: python setup_passwords.py
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

try:
    django.setup()
except Exception as e:
    print(f"Error configurando Django: {e}")
    sys.exit(1)

from django.contrib.auth.models import User
from api.models import Usuario

def setup_passwords():
    """Configurar contraseñas para usuarios de prueba"""
    
    # Lista de usuarios y contraseñas
    users_data = [
        # Clínica Norte
        ("juan.perez@norte.com", "norte123", "Juan", "Pérez García"),
        ("maria.gonzalez@norte.com", "norte123", "María", "González"),
        ("pedro.martinez@norte.com", "norte123", "Dr. Pedro", "Martínez"),
        ("laura.fernandez@norte.com", "norte123", "Laura", "Fernández"),
        
        # Clínica Sur
        ("roberto.sanchez@sur.com", "sur123", "Roberto", "Sánchez"),
        ("miguel.vargas@sur.com", "sur123", "Dr. Miguel", "Vargas"),
        ("sofia.morales@sur.com", "sur123", "Sofia", "Morales"),
        
        # Clínica Este
        ("luis.ramirez@este.com", "este123", "Luis", "Ramírez"),
        ("isabel.castro@este.com", "este123", "Dra. Isabel", "Castro"),
        ("andrea.mendez@este.com", "este123", "Andrea", "Méndez"),
    ]
    
    print("=" * 60)
    print("CONFIGURANDO CONTRASEÑAS DE PRUEBA")
    print("=" * 60)
    print()
    
    success_count = 0
    error_count = 0
    
    for email, password, first_name, last_name in users_data:
        try:
            # Buscar usuario en la base de datos
            usuario = Usuario.objects.get(correoelectronico=email)
            
            # Crear o actualizar usuario Django Auth
            django_user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                }
            )
            
            # Establecer contraseña
            django_user.set_password(password)
            django_user.save()
            
            action = "Creado" if created else "Actualizado"
            print(f"✓ {action}: {email}")
            print(f"  Nombre: {first_name} {last_name}")
            print(f"  Contraseña: {password}")
            print()
            
            success_count += 1
            
        except Usuario.DoesNotExist:
            print(f"✗ Error: Usuario no encontrado en BD: {email}")
            print()
            error_count += 1
            
        except Exception as e:
            print(f"✗ Error configurando {email}: {e}")
            print()
            error_count += 1
    
    print("=" * 60)
    print(f"✓ Exitosos: {success_count}")
    print(f"✗ Errores: {error_count}")
    print("=" * 60)
    print()
    
    if success_count > 0:
        print("🎉 ¡Contraseñas configuradas!")
        print()
        print("Ahora puedes hacer login con:")
        print()
        print("📍 Clínica Norte:")
        print("   Email: juan.perez@norte.com")
        print("   Password: norte123")
        print()
        print("📍 Clínica Sur:")
        print("   Email: roberto.sanchez@sur.com")
        print("   Password: sur123")
        print()
        print("📍 Clínica Este:")
        print("   Email: luis.ramirez@este.com")
        print("   Password: este123")
        print()
        print("🚀 Inicia el servidor y prueba el login:")
        print("   python manage.py runserver 0.0.0.0:8000")
        print()

if __name__ == '__main__':
    setup_passwords()
