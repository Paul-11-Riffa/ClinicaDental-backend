"""
Script de prueba para verificar la configuración de OpenAI.

Ejecutar con:
    python test_openai_config.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.conf import settings
from chatbot.services import OpenAIService


def test_openai_config():
    """Prueba la configuración de OpenAI."""
    
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN DE OPENAI")
    print("=" * 60)
    print()
    
    # 1. Verificar API Key
    print("1️⃣ Verificando API Key...")
    if not settings.OPENAI_API_KEY:
        print("   ❌ ERROR: OPENAI_API_KEY no está configurada")
        print("   📝 Solución: Agrega la siguiente línea a tu archivo .env:")
        print("      OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXX")
        print()
        return False
    
    key_preview = settings.OPENAI_API_KEY[:10] + "..." + settings.OPENAI_API_KEY[-4:]
    print(f"   ✅ API Key encontrada: {key_preview}")
    print()
    
    # 2. Verificar modelo
    print("2️⃣ Verificando modelo...")
    print(f"   ✅ Modelo configurado: {settings.OPENAI_MODEL}")
    print()
    
    # 3. Verificar Assistant ID
    print("3️⃣ Verificando Assistant ID...")
    if settings.OPENAI_ASSISTANT_ID:
        print(f"   ✅ Assistant ID: {settings.OPENAI_ASSISTANT_ID}")
    else:
        print("   ⚠️ Assistant ID no configurado (se creará automáticamente)")
    print()
    
    # 4. Probar conexión con OpenAI
    print("4️⃣ Probando conexión con OpenAI...")
    try:
        service = OpenAIService()
        print("   ✅ Cliente OpenAI inicializado correctamente")
        print()
        
        # 5. Crear o verificar asistente
        print("5️⃣ Creando/verificando asistente...")
        assistant_id = service.crear_o_obtener_asistente()
        print(f"   ✅ Asistente listo: {assistant_id}")
        
        if not settings.OPENAI_ASSISTANT_ID:
            print()
            print("   ⚠️ IMPORTANTE: Agrega esta línea a tu .env:")
            print(f"      OPENAI_ASSISTANT_ID={assistant_id}")
        print()
        
        # 6. Resumen
        print("=" * 60)
        print("✅ CONFIGURACIÓN COMPLETADA")
        print("=" * 60)
        print()
        print("El chatbot está listo para usar. Próximos pasos:")
        print()
        print("1. Si mostramos un OPENAI_ASSISTANT_ID arriba, agrégalo al .env")
        print("2. Implementa el frontend según chatbot/README.md")
        print("3. Prueba los endpoints con Postman o cURL")
        print()
        print("Endpoints disponibles:")
        print("  POST /api/chatbot/chatbot/iniciar/")
        print("  POST /api/chatbot/chatbot/mensaje/")
        print("  GET  /api/chatbot/chatbot/historial/")
        print("  GET  /api/chatbot/pre-consultas/")
        print()
        
        return True
        
    except ValueError as e:
        print(f"   ❌ ERROR: {e}")
        print()
        return False
    except Exception as e:
        print(f"   ❌ ERROR al conectar con OpenAI: {e}")
        print()
        print("   Posibles causas:")
        print("   - API Key inválida")
        print("   - Sin conexión a internet")
        print("   - Sin créditos en la cuenta de OpenAI")
        print()
        return False


if __name__ == "__main__":
    success = test_openai_config()
    sys.exit(0 if success else 1)
