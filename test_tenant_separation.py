#!/usr/bin/env python
"""
Script para probar la separación de URLs entre dominio público y subdominios de tenant.
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(url, headers=None, description=""):
    """Prueba un endpoint y muestra el resultado."""
    print(f"\n{'='*70}")
    print(f"🧪 PRUEBA: {description}")
    print(f"📍 URL: {url}")
    if headers:
        print(f"📋 Headers: {headers}")
    print(f"{'='*70}")
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📦 Response (JSON):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except:
                print(f"📄 Response (Text):")
                print(response.text[:500])
        elif response.status_code == 404:
            print(f"❌ Endpoint NO encontrado (404) - Esto es ESPERADO para URLs que no existen en este contexto")
        else:
            print(f"⚠️  Response:")
            print(response.text[:300])
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: No se pudo conectar al servidor. ¿Está corriendo en {BASE_URL}?")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {str(e)}")

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                   TEST DE SEPARACIÓN MULTI-TENANT                    ║
║                                                                      ║
║  Objetivo: Verificar que las URLs están correctamente separadas     ║
║  entre dominio público y subdominios de tenant                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")

# ========================================================================
# PARTE 1: DOMINIO PÚBLICO (Sin Tenant)
# ========================================================================
print("\n" + "🏢 " * 35)
print("PARTE 1: DOMINIO PÚBLICO (127.0.0.1:8000)")
print("🏢 " * 35)

# Endpoint raíz público
test_endpoint(
    f"{BASE_URL}/",
    description="Endpoint raíz del dominio público"
)

# Admin público (debería existir)
test_endpoint(
    f"{BASE_URL}/admin/",
    description="Panel de admin PÚBLICO (super-administradores)"
)

# Endpoint de tenancy (debería existir)
test_endpoint(
    f"{BASE_URL}/api/tenancy/",
    description="API de gestión de empresas/tenants"
)

# Endpoints de clínica (NO deberían existir en dominio público)
test_endpoint(
    f"{BASE_URL}/api/clinic/",
    description="API de clínica (NO debería existir en público)"
)

test_endpoint(
    f"{BASE_URL}/api/users/",
    description="API de usuarios (NO debería existir en público)"
)

test_endpoint(
    f"{BASE_URL}/api/users/login/",
    description="Login de usuarios (NO debería existir en público)"
)

# ========================================================================
# PARTE 2: SUBDOMINIO DE TENANT (Con Header)
# ========================================================================
print("\n\n" + "🦷 " * 35)
print("PARTE 2: SUBDOMINIO DE TENANT (norte)")
print("🦷 " * 35)

tenant_headers = {"X-Tenant-Subdomain": "norte"}

# Endpoint raíz de tenant
test_endpoint(
    f"{BASE_URL}/",
    headers=tenant_headers,
    description="Endpoint raíz del subdominio 'norte'"
)

# Admin de tenant (debería existir)
test_endpoint(
    f"{BASE_URL}/admin/",
    headers=tenant_headers,
    description="Panel de admin del TENANT (datos filtrados)"
)

# Endpoints de clínica (DEBERÍAN existir en tenant)
test_endpoint(
    f"{BASE_URL}/api/clinic/",
    headers=tenant_headers,
    description="API de clínica (DEBERÍA existir en tenant)"
)

test_endpoint(
    f"{BASE_URL}/api/users/",
    headers=tenant_headers,
    description="API de usuarios (DEBERÍA existir en tenant)"
)

test_endpoint(
    f"{BASE_URL}/api/users/login/",
    headers=tenant_headers,
    description="Login de usuarios (DEBERÍA existir en tenant)"
)

# Endpoint de tenancy (NO debería existir en subdominios)
test_endpoint(
    f"{BASE_URL}/api/tenancy/",
    headers=tenant_headers,
    description="API de tenancy (NO debería existir en tenant)"
)

# ========================================================================
# RESUMEN
# ========================================================================
print("\n\n" + "="*70)
print("📊 RESUMEN ESPERADO")
print("="*70)
print("""
✅ DOMINIO PÚBLICO (127.0.0.1:8000):
   - / → 200 (mensaje de bienvenida público)
   - /admin/ → 200 o 302 (admin público)
   - /api/tenancy/ → 200 (gestión de empresas)
   - /api/clinic/ → 404 ❌
   - /api/users/ → 404 ❌
   - /api/users/login/ → 404 ❌

✅ SUBDOMINIO TENANT (norte):
   - / → 200 (mensaje de bienvenida de clínica)
   - /admin/ → 200 o 302 (admin del tenant)
   - /api/clinic/ → 200 (API de clínica)
   - /api/users/ → 200 (API de usuarios)
   - /api/users/login/ → 200 o 405 (login de usuarios)
   - /api/tenancy/ → 404 ❌
""")

print("\n" + "="*70)
print("✨ Test completado!")
print("="*70 + "\n")
