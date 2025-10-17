import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

# Verificar si existen los usuarios que se supone deberían existir
emails_a_verificar = [
    'admin@norte.com',
    'admin@sur.com', 
    'admin@este.com',
    'admin1@norte.com',
    'admin2@norte.com',
    'admin1@sur.com',
    'admin2@sur.com',
    'admin1@este.com',
    'admin2@este.com'
]

print("Verificando usuarios existentes:")
for email in emails_a_verificar:
    try:
        user = User.objects.get(email=email)
        print(f"[V] {email} - Existe (activo: {user.is_active})")
    except User.DoesNotExist:
        print(f"[X] {email} - NO existe")

print("\n" + "="*50)

# Verificar todos los usuarios de Django
print("Usuarios en la tabla de Django:")
usuarios_django = User.objects.all()
for user in usuarios_django:
    try:
        usuario_api = user.usuario  # Accede al modelo Usuario relacionado
        print(f"  - {user.email} | (API: {usuario_api.nombre} {usuario_api.apellido}, Empresa: {usuario_api.empresa.nombre})")
    except:
        print(f"  - {user.email} | (Sin relacion API)")