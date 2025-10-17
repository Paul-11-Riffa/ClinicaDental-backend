import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Usuario, Tipodeusuario, Empresa

User = get_user_model()

print("Creando usuarios de demostración con credenciales conocidas...")

# Definir usuarios con contraseñas conocidas
usuarios_demo = [
    {
        'email': 'admin@norte.com',
        'password': 'norte123',
        'nombre': 'Admin Norte',
        'apellido': 'Clínica',
        'empresa_subdomain': 'norte',
        'rol_id': 1  # Administrador
    },
    {
        'email': 'admin@sur.com',
        'password': 'sur123',
        'nombre': 'Admin Sur', 
        'apellido': 'Clínica',
        'empresa_subdomain': 'sur',
        'rol_id': 1  # Administrador
    },
    {
        'email': 'admin@este.com',
        'password': 'este123',
        'nombre': 'Admin Este',
        'apellido': 'Clínica',
        'empresa_subdomain': 'este',
        'rol_id': 1  # Administrador
    },
]

for usr_data in usuarios_demo:
    try:
        # Obtener la empresa
        empresa = Empresa.objects.get(subdomain=usr_data['empresa_subdomain'])
        # Obtener el tipo de usuario
        tipo_usuario = Tipodeusuario.objects.get(id=usr_data['rol_id'])
        
        # Verificar si el usuario ya existe
        if User.objects.filter(email=usr_data['email']).exists():
            print(f"[!] Usuario {usr_data['email']} ya existe, actualizando contraseña...")
            user = User.objects.get(email=usr_data['email'])
            user.set_password(usr_data['password'])
            user.save()
        else:
            # Crear usuario de Django
            user = User.objects.create_user(
                username=usr_data['email'],
                email=usr_data['email'],
                password=usr_data['password'],
                first_name=usr_data['nombre'],
                last_name=usr_data['apellido']
            )
            print(f"[V] Usuario Django creado: {usr_data['email']}")
        
        # Verificar si ya existe el usuario en la tabla API
        if not Usuario.objects.filter(correoelectronico=usr_data['email']).exists():
            # Crear usuario en la tabla API
            usuario_api = Usuario.objects.create(
                nombre=usr_data['nombre'],
                apellido=usr_data['apellido'],
                correoelectronico=usr_data['email'],
                telefono='70000000',
                sexo='M',
                idtipousuario=tipo_usuario,
                empresa=empresa,
                recibir_notificaciones=True,
                notificaciones_email=True,
                notificaciones_push=False
            )
            print(f"[V] Usuario API creado: {usr_data['email']}")
        else:
            print(f"[!] Usuario API {usr_data['email']} ya existe")
        
        # Asegurarse de que el usuario Django tenga relación con el usuario API
        if not hasattr(user, 'usuario'):
            usuario_api = Usuario.objects.get(correoelectronico=usr_data['email'])
            user.usuario = usuario_api
            user.save()
        
        print(f"[V] Usuario listo: {usr_data['email']} / {usr_data['password']}")
        
    except Exception as e:
        print(f"[X] Error creando usuario {usr_data['email']}: {str(e)}")

print("\nUsuarios de demostracion creados exitosamente!")
print("\nCredenciales de acceso:")
print("- admin@norte.com / norte123")
print("- admin@sur.com / sur123") 
print("- admin@este.com / este123")