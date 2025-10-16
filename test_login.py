#!/usr/bin/env python
"""Script para probar el login de usuarios"""
import requests
import json

# Configuración
BASE_URL = "http://127.0.0.1:8000/api"
LOGIN_URL = f"{BASE_URL}/auth/login/"

# Credenciales de prueba
test_users = [
    {
        "name": "Juan Pérez (Paciente - Norte)",
        "email": "juan.perez@norte.com",
        "password": "norte123",
        "subdomain": "norte"
    },
    {
        "name": "Pedro Martínez (Odontólogo - Norte)",
        "email": "pedro.martinez@norte.com",
        "password": "norte123",
        "subdomain": "norte"
    },
]

print("=" * 70)
print("🧪 PROBANDO LOGIN DE USUARIOS - CLÍNICA NORTE")
print("=" * 70)

for user_data in test_users:
    print(f"\n📝 Probando: {user_data['name']}")
    print(f"   Email: {user_data['email']}")
    print(f"   URL: {LOGIN_URL}")
    print(f"   Subdomain Header: {user_data['subdomain']}")
    
    try:
        # Hacer la petición con header de subdomain (para desarrollo)
        response = requests.post(
            LOGIN_URL,
            json={
                "email": user_data['email'],
                "password": user_data['password']
            },
            headers={
                "Content-Type": "application/json",
                "X-Tenant-Subdomain": user_data['subdomain']  # Header para desarrollo
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ LOGIN EXITOSO!")
            print(f"   Token: {data.get('token', 'N/A')[:50]}...")
            print(f"   Usuario: {data.get('usuario', {}).get('nombre')} {data.get('usuario', {}).get('apellido')}")
            print(f"   Subtipo: {data.get('usuario', {}).get('subtipo')}")
            print(f"   Recibir notificaciones: {data.get('usuario', {}).get('recibir_notificaciones')}")
        else:
            print(f"   ❌ ERROR: {response.status_code}")
            print(f"   Respuesta: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ ERROR: No se pudo conectar al servidor")
        print(f"   ℹ️  Asegúrate de que el servidor esté corriendo: python manage.py runserver 0.0.0.0:8000")
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")

print("\n" + "=" * 70)
print("✅ PRUEBAS COMPLETADAS")
print("=" * 70)
