import requests
import json

# Test login para administradores de cada clínica
admins = [
    {'email': 'admin@norte.com', 'password': 'norte123', 'subdomain': 'norte'},
    {'email': 'admin@sur.com', 'password': 'sur123', 'subdomain': 'sur'},
    {'email': 'admin@este.com', 'password': 'este123', 'subdomain': 'este'},
]

print("=" * 70)
print("🔐 TESTING LOGIN PARA ADMINISTRADORES DE CLÍNICAS")
print("=" * 70)

for admin in admins:
    print(f"\n🏥 Clínica: {admin['subdomain'].upper()}")
    print(f"   Email: {admin['email']}")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/auth/login/',
            json={
                'email': admin['email'],
                'password': admin['password']
            },
            headers={
                'Content-Type': 'application/json',
                'X-Tenant-Subdomain': admin['subdomain']
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Login exitoso!")
            print(f"   Token: {data['token'][:30]}...")
            print(f"   Usuario: {data['usuario']['nombre']} {data['usuario']['apellido']}")
            print(f"   Rol: {data['usuario']['subtipo']} (ID Tipo: {data['usuario']['idtipousuario']})")
        else:
            print(f"   ❌ Error {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

print("\n" + "=" * 70)
