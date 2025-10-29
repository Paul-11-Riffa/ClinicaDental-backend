"""
Script de prueba completo del chatbot.
Simula una conversación real con el asistente.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from chatbot.services import OpenAIService
from api.models import Empresa, Paciente

def test_chatbot_completo():
    """Prueba completa del flujo del chatbot."""
    
    print("=" * 70)
    print("🧪 PRUEBA COMPLETA DEL CHATBOT ODONTOLÓGICO")
    print("=" * 70)
    print()
    
    # 1. Verificar que existe una empresa
    print("1️⃣ Verificando empresa de prueba...")
    empresa = Empresa.objects.first()
    
    if not empresa:
        print("   ❌ No hay empresas en la base de datos")
        print("   📝 Necesitas crear una empresa primero")
        return False
    
    print(f"   ✅ Usando empresa: {empresa.nombre} (subdomain: {empresa.subdomain})")
    print()
    
    # 2. Inicializar servicio OpenAI
    print("2️⃣ Inicializando servicio OpenAI...")
    try:
        service = OpenAIService()
        print("   ✅ Servicio inicializado")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 3. Crear conversación
    print("3️⃣ Creando nueva conversación...")
    try:
        conversacion = service.crear_conversacion(empresa, paciente=None)
        print(f"   ✅ Conversación creada con ID: {conversacion.id}")
        print(f"   📝 Thread ID: {conversacion.thread_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()
    
    # 4. Obtener mensaje de bienvenida
    print("4️⃣ Mensaje de bienvenida:")
    mensaje_bienvenida = conversacion.mensajes.first()
    if mensaje_bienvenida:
        print(f"   🤖 Asistente: {mensaje_bienvenida.contenido}")
    print()
    
    # 5. Simular conversación
    print("5️⃣ Simulando conversación...")
    print("-" * 70)
    
    mensajes_prueba = [
        "Hola, tengo un dolor de muelas muy fuerte",
        "El dolor es en el lado derecho, nivel 8 de 10",
        "Sí, me gustaría agendar una cita lo antes posible"
    ]
    
    for i, mensaje in enumerate(mensajes_prueba, 1):
        print(f"\n   👤 Usuario: {mensaje}")
        
        try:
            respuesta, function_data = service.enviar_mensaje(conversacion, mensaje)
            print(f"   🤖 Asistente: {respuesta}")
            
            if function_data:
                print(f"   🔧 Function Call: {function_data.get('function')}")
                print(f"      Args: {function_data.get('arguments')}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print()
    print("-" * 70)
    print()
    
    # 6. Verificar si se creó pre-consulta
    print("6️⃣ Verificando pre-consulta...")
    pre_consulta = conversacion.preconsulta if hasattr(conversacion, 'preconsulta') else None
    
    if pre_consulta:
        print("   ✅ Pre-consulta creada:")
        print(f"      - Nombre: {pre_consulta.nombre or 'N/A'}")
        print(f"      - Teléfono: {pre_consulta.telefono or 'N/A'}")
        print(f"      - Síntomas: {pre_consulta.sintomas or 'N/A'}")
        print(f"      - Urgencia: {pre_consulta.urgencia}")
    else:
        print("   ℹ️ No se creó pre-consulta (normal si no se recopiló info completa)")
    print()
    
    # 7. Estadísticas de la conversación
    print("7️⃣ Estadísticas de la conversación:")
    total_mensajes = conversacion.mensajes.count()
    mensajes_usuario = conversacion.mensajes.filter(role='user').count()
    mensajes_asistente = conversacion.mensajes.filter(role='assistant').count()
    
    print(f"   📊 Total mensajes: {total_mensajes}")
    print(f"   👤 Mensajes usuario: {mensajes_usuario}")
    print(f"   🤖 Mensajes asistente: {mensajes_asistente}")
    print()
    
    # 8. Resumen
    print("=" * 70)
    print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print()
    print("🎉 El chatbot está funcionando correctamente!")
    print()
    print("Siguiente paso: Implementar el frontend")
    print("Ver: chatbot/README.md para ejemplos de integración")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_chatbot_completo()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
