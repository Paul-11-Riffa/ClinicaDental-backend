import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from api.models import Usuario, Tipodeusuario, Empresa, Paciente, Odontologo
from django.db import transaction

User = get_user_model()

print("Creando usuarios de pacientes y odontólogos con credenciales conocidas (corregido)...")

# Crear usuarios de ejemplo para cada rol y clínica
usuarios_ejemplo = [
    # Pacientes con contraseñas actualizadas
    {
        'email': 'paciente1@norte.com',
        'password': 'paciente123',
        'nombre': 'Juan',
        'apellido': 'Pérez',
        'empresa_subdomain': 'norte',
        'rol_id': 4,  # Paciente
        'tipo_usuario': 'paciente'
    },
    {
        'email': 'paciente1@sur.com',
        'password': 'paciente123',
        'nombre': 'María',
        'apellido': 'González',
        'empresa_subdomain': 'sur',
        'rol_id': 4,  # Paciente
        'tipo_usuario': 'paciente'
    },
    {
        'email': 'paciente1@este.com',
        'password': 'paciente123',
        'nombre': 'Carlos',
        'apellido': 'Rodríguez',
        'empresa_subdomain': 'este',
        'rol_id': 4,  # Paciente
        'tipo_usuario': 'paciente'
    },
    # Odontólogos
    {
        'email': 'odontologo@norte.com',
        'password': 'odontologo123',
        'nombre': 'Dr. Alberto',
        'apellido': 'Hernández',
        'empresa_subdomain': 'norte',
        'rol_id': 2,  # Odontólogo
        'tipo_usuario': 'odontologo'
    },
    {
        'email': 'odontologo@sur.com',
        'password': 'odontologo123',
        'nombre': 'Dra. Lucía',
        'apellido': 'Martínez',
        'empresa_subdomain': 'sur',
        'rol_id': 2,  # Odontólogo
        'tipo_usuario': 'odontologo'
    },
    {
        'email': 'odontologo@este.com',
        'password': 'odontologo123',
        'nombre': 'Dr. Roberto',
        'apellido': 'López',
        'empresa_subdomain': 'este',
        'rol_id': 2,  # Odontólogo
        'tipo_usuario': 'odontologo'
    },
]

for usr_data in usuarios_ejemplo:
    try:
        # Obtener la empresa
        empresa = Empresa.objects.get(subdomain=usr_data['empresa_subdomain'])
        # Obtener el tipo de usuario
        tipo_usuario = Tipodeusuario.objects.get(id=usr_data['rol_id'])
        
        # Crear usuario de Django
        with transaction.atomic():
            # Verificar si el usuario ya existe
            if User.objects.filter(email=usr_data['email']).exists():
                print(f"[!] Usuario {usr_data['email']} ya existe, actualizando contraseña...")
                user = User.objects.get(email=usr_data['email'])
                user.set_password(usr_data['password'])
                user.save()
            else:
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
                usuario_api = Usuario.objects.create(
                    nombre=usr_data['nombre'],
                    apellido=usr_data['apellido'],
                    correoelectronico=usr_data['email'],
                    telefono='70000000',
                    sexo='M' if usr_data['tipo_usuario'] == 'odontologo' else 'M',
                    idtipousuario=tipo_usuario,
                    empresa=empresa,
                    recibir_notificaciones=True,
                    notificaciones_email=True,
                    notificaciones_push=False
                )
                print(f"[V] Usuario API creado: {usr_data['email']}")
                
                # Asegurarse de que el usuario Django tenga relación con el usuario API
                user.usuario = usuario_api
                user.save()
                
                # Si es un paciente, crear perfil de paciente
                if usr_data['tipo_usuario'] == 'paciente':
                    paciente = Paciente.objects.create(
                        codusuario=usuario_api,
                        empresa=empresa,
                        carnetidentidad='12345678',
                        fechanacimiento='1990-01-01',
                        direccion='Dirección de ejemplo',
                        genero='M',
                        telefono_emergencia='70000000',
                        contacto_emergencia='Contacto Ejemplo',
                        alergias='Ninguna',
                        enfermedades_cronicas='Ninguna',
                        grupo_sanguineo='O+',
                        observaciones='Paciente de ejemplo'
                    )
                    print(f"[V] Perfil de paciente creado para: {usr_data['email']}")
                
                # Si es un odontólogo, crear perfil de odontólogo
                elif usr_data['tipo_usuario'] == 'odontologo':
                    odontologo = Odontologo.objects.create(
                        codusuario=usuario_api,
                        empresa=empresa,
                        especialidad='General',
                        experienciaprofesional='Experiencia clínica en odontología general',
                        nromatricula='12345'
                    )
                    print(f"[V] Perfil de odontólogo creado para: {usr_data['email']}")
            else:
                print(f"[V] Usuario API {usr_data['email']} ya existía")
        
        print(f"[V] Usuario listo: {usr_data['email']} / {usr_data['password']}")
        
    except Exception as e:
        print(f"[X] Error creando usuario {usr_data['email']}: {str(e)}")

print("\nUsuarios de ejemplo creados exitosamente!")
print("\nCredenciales de pacientes:")
print("- paciente1@norte.com / paciente123")
print("- paciente1@sur.com / paciente123")
print("- paciente1@este.com / paciente123")
print("\nCredenciales de odontólogos:")
print("- odontologo@norte.com / odontologo123")
print("- odontologo@sur.com / odontologo123")
print("- odontologo@este.com / odontologo123")