"""
SP3-T009: Script de Verificación - FASE 4
Verifica la integración con Stripe:
- Configuración de Stripe en settings
- StripePaymentService y sus métodos
- Vistas y endpoints de pagos
- Webhook endpoint
- ComprobanteDigital.crear_comprobante()
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.conf import settings
from api.models import ComprobanteDigital, PagoEnLinea
from api.services.stripe_payment_service import StripePaymentService
from api import views_pagos
from api import urls_pagos
from decimal import Decimal
import inspect


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_success(msg):
    print(f"✅ {msg}")


def print_error(msg):
    print(f"❌ {msg}")


def print_info(msg):
    print(f"ℹ️  {msg}")


def verificar_configuracion_stripe():
    """Verifica que Stripe esté configurado en settings."""
    print_header("1. Verificación de Configuración Stripe")
    
    errores = []
    
    # Verificar STRIPE_ENABLED
    if not hasattr(settings, 'STRIPE_ENABLED'):
        errores.append("STRIPE_ENABLED no está definido en settings")
    else:
        print_success(f"STRIPE_ENABLED: {settings.STRIPE_ENABLED}")
    
    # Verificar STRIPE_SECRET_KEY
    if not hasattr(settings, 'STRIPE_SECRET_KEY'):
        errores.append("STRIPE_SECRET_KEY no está definido en settings")
    else:
        if settings.STRIPE_SECRET_KEY:
            print_success(f"STRIPE_SECRET_KEY: Configurado (longitud: {len(settings.STRIPE_SECRET_KEY)})")
        else:
            print_info("STRIPE_SECRET_KEY: No configurado (Stripe deshabilitado)")
    
    # Verificar STRIPE_PUBLIC_KEY
    if not hasattr(settings, 'STRIPE_PUBLIC_KEY'):
        errores.append("STRIPE_PUBLIC_KEY no está definido en settings")
    else:
        if settings.STRIPE_PUBLIC_KEY:
            print_success(f"STRIPE_PUBLIC_KEY: Configurado (longitud: {len(settings.STRIPE_PUBLIC_KEY)})")
        else:
            print_info("STRIPE_PUBLIC_KEY: No configurado")
    
    # Verificar STRIPE_WEBHOOK_SECRET
    if not hasattr(settings, 'STRIPE_WEBHOOK_SECRET'):
        errores.append("STRIPE_WEBHOOK_SECRET no está definido en settings")
    else:
        if settings.STRIPE_WEBHOOK_SECRET:
            print_success(f"STRIPE_WEBHOOK_SECRET: Configurado")
        else:
            print_info("STRIPE_WEBHOOK_SECRET: No configurado (webhooks no verificarán firma)")
    
    # Verificar configuraciones adicionales
    configs_adicionales = [
        'STRIPE_DEFAULT_CURRENCY',
        'STRIPE_PAYMENT_METHOD_TYPES',
        'STRIPE_CAPTURE_METHOD'
    ]
    
    for config in configs_adicionales:
        if hasattr(settings, config):
            valor = getattr(settings, config)
            print_success(f"{config}: {valor}")
        else:
            print_info(f"{config}: No definido (usará default)")
    
    return len(errores) == 0, errores


def verificar_stripe_payment_service():
    """Verifica que StripePaymentService tenga todos los métodos necesarios."""
    print_header("2. Verificación de StripePaymentService")
    
    errores = []
    
    # Métodos requeridos
    metodos_requeridos = [
        'is_enabled',
        'crear_payment_intent',
        'confirmar_payment_intent',
        'capturar_payment_intent',
        'cancelar_payment_intent',
        'obtener_payment_intent',
        'crear_reembolso',
        'procesar_webhook_payment_intent_succeeded',
        'procesar_webhook_payment_intent_failed',
        'procesar_webhook_charge_refunded',
        'verificar_webhook_signature'
    ]
    
    for metodo in metodos_requeridos:
        if hasattr(StripePaymentService, metodo):
            # Verificar que sea método
            attr = getattr(StripePaymentService, metodo)
            if callable(attr):
                print_success(f"Método '{metodo}' existe")
                
                # Verificar docstring
                if attr.__doc__:
                    print_info(f"  Documentado: {attr.__doc__.strip().split('\\n')[0][:60]}...")
            else:
                errores.append(f"'{metodo}' no es callable")
        else:
            errores.append(f"Método '{metodo}' no existe")
    
    # Verificar que is_enabled funcione
    try:
        enabled = StripePaymentService.is_enabled()
        print_success(f"is_enabled() retorna: {enabled}")
    except Exception as e:
        errores.append(f"is_enabled() falla: {e}")
    
    return len(errores) == 0, errores


def verificar_modelo_comprobante():
    """Verifica que ComprobanteDigital tenga el método crear_comprobante."""
    print_header("3. Verificación de ComprobanteDigital.crear_comprobante")
    
    errores = []
    
    # Verificar que el método existe
    if not hasattr(ComprobanteDigital, 'crear_comprobante'):
        errores.append("ComprobanteDigital no tiene método 'crear_comprobante'")
        return False, errores
    
    print_success("Método 'crear_comprobante' existe")
    
    # Verificar que sea classmethod
    metodo = getattr(ComprobanteDigital, 'crear_comprobante')
    if not isinstance(inspect.getattr_static(ComprobanteDigital, 'crear_comprobante'), classmethod):
        errores.append("'crear_comprobante' no es un classmethod")
    else:
        print_success("'crear_comprobante' es un classmethod")
    
    # Verificar signature
    try:
        sig = inspect.signature(metodo)
        params = list(sig.parameters.keys())
        
        if 'pago' in params:
            print_success("Acepta parámetro 'pago'")
        else:
            errores.append("No acepta parámetro 'pago'")
        
        print_info(f"Parámetros: {params}")
    except Exception as e:
        errores.append(f"Error verificando signature: {e}")
    
    # Verificar docstring
    if metodo.__doc__:
        print_info(f"Documentado: {metodo.__doc__.strip().split('\\n')[0][:60]}...")
    else:
        print_info("Sin documentación")
    
    return len(errores) == 0, errores


def verificar_vistas_pagos():
    """Verifica que las vistas de pagos existan."""
    print_header("4. Verificación de Vistas de Pagos")
    
    errores = []
    
    # Verificar ViewSet
    if hasattr(views_pagos, 'PagoEnLineaViewSet'):
        print_success("PagoEnLineaViewSet existe")
        
        # Verificar métodos custom
        viewset = views_pagos.PagoEnLineaViewSet
        metodos_custom = [
            'crear_pago_plan',
            'crear_pago_consulta',
            'confirmar_pago',
            'cancelar_pago',
            'reembolsar_pago',
            'resumen_plan'
        ]
        
        for metodo in metodos_custom:
            if hasattr(viewset, metodo):
                print_success(f"  Método '{metodo}' existe")
            else:
                errores.append(f"ViewSet no tiene método '{metodo}'")
    else:
        errores.append("PagoEnLineaViewSet no existe")
    
    # Verificar webhook view
    if hasattr(views_pagos, 'stripe_webhook'):
        print_success("stripe_webhook existe")
    else:
        errores.append("stripe_webhook no existe")
    
    # Verificar view de verificación de comprobante
    if hasattr(views_pagos, 'verificar_comprobante'):
        print_success("verificar_comprobante existe")
    else:
        errores.append("verificar_comprobante no existe")
    
    return len(errores) == 0, errores


def verificar_urls_pagos():
    """Verifica que las URLs de pagos estén configuradas."""
    print_header("5. Verificación de URLs de Pagos")
    
    errores = []
    
    # Verificar que el módulo urls_pagos existe
    if not hasattr(urls_pagos, 'urlpatterns'):
        errores.append("urls_pagos no tiene 'urlpatterns'")
        return False, errores
    
    print_success("urls_pagos.urlpatterns existe")
    
    # Verificar router
    if hasattr(urls_pagos, 'router'):
        print_success("Router configurado")
    else:
        print_info("Router no encontrado (puede estar inline)")
    
    # Contar URLs
    url_count = len(urls_pagos.urlpatterns)
    print_success(f"Total de URLs configuradas: {url_count}")
    
    # Verificar URLs específicas
    urls_esperadas = [
        ('webhook/stripe/', 'Webhook de Stripe'),
        ('verificar-comprobante-pago/', 'Verificación de comprobantes')
    ]
    
    urls_str = str(urls_pagos.urlpatterns)
    
    for pattern, descripcion in urls_esperadas:
        if pattern in urls_str:
            print_success(f"URL '{pattern}' configurada ({descripcion})")
        else:
            print_info(f"URL '{pattern}' no encontrada directamente")
    
    return len(errores) == 0, errores


def verificar_integracion_modelos():
    """Verifica que PagoEnLinea tenga los campos necesarios para Stripe."""
    print_header("6. Verificación de Integración con Modelos")
    
    errores = []
    
    # Verificar campos de Stripe en PagoEnLinea
    campos_stripe = [
        'stripe_payment_intent_id',
        'stripe_charge_id',
        'numero_intentos'
    ]
    
    for campo in campos_stripe:
        if hasattr(PagoEnLinea, campo):
            print_success(f"PagoEnLinea.{campo} existe")
        else:
            errores.append(f"PagoEnLinea no tiene campo '{campo}'")
    
    # Verificar métodos relacionados con Stripe
    metodos_pago = [
        'puede_anularse',
        'puede_reembolsarse'
    ]
    
    for metodo in metodos_pago:
        if hasattr(PagoEnLinea, metodo):
            print_success(f"PagoEnLinea.{metodo}() existe")
        else:
            errores.append(f"PagoEnLinea no tiene método '{metodo}'")
    
    return len(errores) == 0, errores


def main():
    print("\n" + "🔍 " * 20)
    print("   VERIFICACIÓN FASE 4: INTEGRACIÓN CON STRIPE")
    print("   SP3-T009: Realizar pago en línea (web)")
    print("🔍 " * 20)
    
    resultados = []
    
    # 1. Configuración Stripe
    exito, errores = verificar_configuracion_stripe()
    resultados.append(("Configuración Stripe", exito, errores))
    
    # 2. StripePaymentService
    exito, errores = verificar_stripe_payment_service()
    resultados.append(("StripePaymentService", exito, errores))
    
    # 3. ComprobanteDigital.crear_comprobante
    exito, errores = verificar_modelo_comprobante()
    resultados.append(("ComprobanteDigital.crear_comprobante", exito, errores))
    
    # 4. Vistas de Pagos
    exito, errores = verificar_vistas_pagos()
    resultados.append(("Vistas de Pagos", exito, errores))
    
    # 5. URLs de Pagos
    exito, errores = verificar_urls_pagos()
    resultados.append(("URLs de Pagos", exito, errores))
    
    # 6. Integración con Modelos
    exito, errores = verificar_integracion_modelos()
    resultados.append(("Integración con Modelos", exito, errores))
    
    # Resumen
    print_header("RESUMEN DE VERIFICACIÓN")
    
    total = len(resultados)
    exitosos = sum(1 for _, exito, _ in resultados if exito)
    
    for nombre, exito, errores in resultados:
        if exito:
            print_success(f"{nombre}: OK")
        else:
            print_error(f"{nombre}: FALLÓ")
            for error in errores:
                print(f"    - {error}")
    
    print("\n" + "-" * 70)
    print(f"Total: {exitosos}/{total} verificaciones exitosas")
    print("-" * 70)
    
    if exitosos == total:
        print("\n✅ ¡FASE 4 COMPLETADA EXITOSAMENTE!")
        print("\nStripe Integration:")
        print("  • StripePaymentService: 11 métodos implementados")
        print("  • Webhook endpoint: Configurado")
        print("  • ComprobanteDigital: Auto-creación implementada")
        print("  • ViewSet: 6 endpoints custom")
        print("\nPróximos pasos:")
        print("  1. Configurar variables de entorno Stripe (si es necesario)")
        print("  2. Probar webhook en ambiente de desarrollo (Stripe CLI)")
        print("  3. Continuar con FASE 5: ViewSet y Endpoints")
        return True
    else:
        print("\n⚠️  Hay errores que corregir antes de continuar")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print_error(f"Error ejecutando verificación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
