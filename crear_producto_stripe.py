#!/usr/bin/env python
"""
Script para crear automáticamente el producto y precio en Stripe
Ejecutar: python crear_producto_stripe.py
"""

import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

# Cargar variables de entorno
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Importar después de configurar Django
import stripe

def crear_producto_stripe():
    """
    Crea un producto y precio en Stripe para la suscripción mensual
    """
    # Configurar Stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    if not stripe.api_key:
        print("❌ Error: STRIPE_SECRET_KEY no encontrada en .env")
        return None
    
    print("🚀 Creando producto en Stripe...")
    print(f"📍 Usando API key: {stripe.api_key[:20]}...")
    
    try:
        # 1. Crear el producto
        print("\n1️⃣ Creando producto...")
        producto = stripe.Product.create(
            name="Plan Mensual Clínica Dental",
            description="Suscripción mensual para sistema de gestión de clínica dental con todas las funcionalidades incluidas",
            metadata={
                "tipo": "saas_subscription",
                "sistema": "dental_clinic"
            }
        )
        
        print(f"✅ Producto creado: {producto.id}")
        print(f"   Nombre: {producto.name}")
        
        # 2. Crear el precio (mensual)
        print("\n2️⃣ Creando precio mensual...")
        precio = stripe.Price.create(
            product=producto.id,
            unit_amount=9900,  # $99.00 USD (en centavos)
            currency="usd",
            recurring={
                "interval": "month",
                "trial_period_days": 14  # 14 días gratis
            },
            metadata={
                "plan": "completo",
                "features": "all"
            }
        )
        
        print(f"✅ Precio creado: {precio.id}")
        print(f"   Precio: ${precio.unit_amount / 100:.2f} USD/mes")
        print(f"   Trial: {precio.recurring.trial_period_days} días gratis")
        
        # 3. Actualizar .env
        print("\n3️⃣ Actualizando archivo .env...")
        env_path = os.path.join(BASE_DIR, '.env')
        
        with open(env_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Reemplazar STRIPE_PRICE_ID
        if 'STRIPE_PRICE_ID=' in contenido:
            lineas = contenido.split('\n')
            nuevas_lineas = []
            
            for linea in lineas:
                if linea.startswith('STRIPE_PRICE_ID='):
                    nuevas_lineas.append(f'STRIPE_PRICE_ID={precio.id}')
                    print(f"   ✅ Actualizado: STRIPE_PRICE_ID={precio.id}")
                else:
                    nuevas_lineas.append(linea)
            
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(nuevas_lineas))
        else:
            print("   ⚠️  No se encontró STRIPE_PRICE_ID en .env")
        
        # 4. Resumen
        print("\n" + "="*60)
        print("✅ ¡PRODUCTO CREADO EXITOSAMENTE EN STRIPE!")
        print("="*60)
        print(f"\n📦 Producto ID: {producto.id}")
        print(f"💰 Price ID:    {precio.id}")
        print(f"💵 Precio:      ${precio.unit_amount / 100:.2f} USD/mes")
        print(f"🎁 Trial:       {precio.recurring.trial_period_days} días gratis")
        print(f"\n📝 El archivo .env ha sido actualizado automáticamente")
        print(f"\n🔄 PRÓXIMO PASO: Reinicia el servidor Django")
        print(f"   python manage.py runserver")
        print("\n" + "="*60)
        
        return precio.id
        
    except stripe.error.StripeError as e:
        print(f"\n❌ Error de Stripe: {e.user_message}")
        print(f"   Detalles: {str(e)}")
        return None
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def verificar_producto_existente():
    """
    Verifica si ya existe un producto con el mismo nombre
    """
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    
    try:
        productos = stripe.Product.list(limit=10)
        
        for producto in productos.data:
            if "Plan Mensual Clínica Dental" in producto.name:
                print(f"\n⚠️  Ya existe un producto similar:")
                print(f"   ID: {producto.id}")
                print(f"   Nombre: {producto.name}")
                
                # Buscar precios de este producto
                precios = stripe.Price.list(product=producto.id, limit=5)
                if precios.data:
                    for precio in precios.data:
                        if precio.active:
                            print(f"\n💰 Precio activo encontrado: {precio.id}")
                            print(f"   ${precio.unit_amount / 100:.2f} USD/{precio.recurring.interval}")
                            
                            respuesta = input("\n¿Deseas usar este precio existente? (s/n): ")
                            if respuesta.lower() == 's':
                                return precio.id
                
                respuesta = input("\n¿Deseas crear un nuevo producto de todas formas? (s/n): ")
                if respuesta.lower() != 's':
                    return None
        
        return False  # No existe, continuar con creación
        
    except Exception as e:
        print(f"⚠️  Error al verificar productos: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("🛍️  CREAR PRODUCTO EN STRIPE - SISTEMA DENTAL")
    print("="*60)
    
    # Verificar si ya existe
    precio_existente = verificar_producto_existente()
    
    if precio_existente:
        # Actualizar .env con el precio existente
        env_path = os.path.join(BASE_DIR, '.env')
        with open(env_path, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        lineas = contenido.split('\n')
        nuevas_lineas = []
        
        for linea in lineas:
            if linea.startswith('STRIPE_PRICE_ID='):
                nuevas_lineas.append(f'STRIPE_PRICE_ID={precio_existente}')
            else:
                nuevas_lineas.append(linea)
        
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(nuevas_lineas))
        
        print(f"\n✅ .env actualizado con Price ID: {precio_existente}")
        print(f"\n🔄 Reinicia el servidor Django:")
        print(f"   python manage.py runserver")
    
    elif precio_existente is False:
        # No existe, crear nuevo
        precio_id = crear_producto_stripe()
        
        if precio_id:
            print("\n✅ ¡Listo! Ahora puedes probar el registro con pago.")
            print("\n🧪 Tarjeta de prueba:")
            print("   Número: 4242 4242 4242 4242")
            print("   Fecha:  12/25")
            print("   CVC:    123")
    else:
        print("\n❌ Operación cancelada por el usuario")
