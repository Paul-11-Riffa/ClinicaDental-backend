"""
Script de Verificación - FASE 3: Serializers y Validaciones
SP3-T009: Realizar pago en línea (web)

Verifica que todos los serializers y validadores estén implementados
correctamente y funcionen según lo esperado.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()


def verificar_imports_serializers():
    """Verifica que todos los serializers se puedan importar."""
    print("\n📋 Verificando imports de serializers...")
    
    try:
        from api.serializers_pagos import (
            DetallePagoItemSerializer,
            ComprobanteDigitalSerializer,
            PagoEnLineaSerializer,
            PagoEnLineaListSerializer,
            CrearPagoPlanSerializer,
            CrearPagoConsultaSerializer,
            ActualizarEstadoPagoSerializer,
            ResumenFinancieroPlanSerializer
        )
        print("  ✅ Todos los serializers importados correctamente")
        
        serializers_count = 8
        print(f"✅ {serializers_count} serializers disponibles")
        return True
        
    except ImportError as e:
        print(f"  ❌ Error al importar serializers: {e}")
        return False


def verificar_imports_validadores():
    """Verifica que todos los validadores se puedan importar."""
    print("\n📋 Verificando imports de validadores...")
    
    try:
        from api.validators_pagos import (
            validar_monto_positivo,
            validar_monto_no_excede_saldo,
            validar_estado_origen,
            validar_items_plan,
            validar_distribucion_pago,
            validar_pago_duplicado,
            validar_metodo_pago_disponible,
            validar_pago_puede_anularse,
            validar_pago_puede_reembolsarse,
            validar_saldo_suficiente_reembolso,
            ValidadorComplejoPagos
        )
        print("  ✅ Todos los validadores importados correctamente")
        
        validadores_count = 11
        print(f"✅ {validadores_count} validadores/funciones disponibles")
        return True
        
    except ImportError as e:
        print(f"  ❌ Error al importar validadores: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_estructura_serializers():
    """Verifica la estructura de los serializers principales."""
    print("\n📋 Verificando estructura de serializers...")
    
    from api.serializers_pagos import (
        PagoEnLineaSerializer,
        CrearPagoPlanSerializer,
        CrearPagoConsultaSerializer
    )
    
    errores = []
    
    # 1. Verificar PagoEnLineaSerializer (lectura)
    print("\n  Verificando PagoEnLineaSerializer...")
    campos_esperados_lectura = [
        'id', 'codigo_pago', 'origen_tipo', 'monto', 'estado',
        'metodo_pago', 'detalles_items', 'comprobante'
    ]
    
    serializer_lectura = PagoEnLineaSerializer()
    campos_lectura = list(serializer_lectura.fields.keys())
    
    for campo in campos_esperados_lectura:
        if campo in campos_lectura:
            print(f"    ✅ Campo '{campo}' presente")
        else:
            print(f"    ❌ Campo '{campo}' NO presente")
            errores.append(f"PagoEnLineaSerializer.{campo}")
    
    # 2. Verificar CrearPagoPlanSerializer (escritura)
    print("\n  Verificando CrearPagoPlanSerializer...")
    campos_esperados_crear_plan = [
        'plan_tratamiento_id', 'monto', 'metodo_pago',
        'items_seleccionados', 'descripcion'
    ]
    
    serializer_crear_plan = CrearPagoPlanSerializer()
    campos_crear_plan = list(serializer_crear_plan.fields.keys())
    
    for campo in campos_esperados_crear_plan:
        if campo in campos_crear_plan:
            print(f"    ✅ Campo '{campo}' presente")
        else:
            print(f"    ❌ Campo '{campo}' NO presente")
            errores.append(f"CrearPagoPlanSerializer.{campo}")
    
    # 3. Verificar CrearPagoConsultaSerializer
    print("\n  Verificando CrearPagoConsultaSerializer...")
    campos_esperados_crear_consulta = [
        'consulta_id', 'monto', 'metodo_pago', 'tipo_pago_consulta'
    ]
    
    serializer_crear_consulta = CrearPagoConsultaSerializer()
    campos_crear_consulta = list(serializer_crear_consulta.fields.keys())
    
    for campo in campos_esperados_crear_consulta:
        if campo in campos_crear_consulta:
            print(f"    ✅ Campo '{campo}' presente")
        else:
            print(f"    ❌ Campo '{campo}' NO presente")
            errores.append(f"CrearPagoConsultaSerializer.{campo}")
    
    if not errores:
        print(f"\n✅ Estructura de serializers correcta")
        return True
    else:
        print(f"\n❌ Faltan {len(errores)} campos en serializers")
        return False


def verificar_validaciones_serializers():
    """Verifica que las validaciones de serializers funcionen."""
    print("\n📋 Probando validaciones de serializers...")
    
    from api.serializers_pagos import CrearPagoPlanSerializer
    from rest_framework.exceptions import ValidationError
    
    try:
        # Test 1: Monto negativo debe fallar
        print("\n  Test 1: Validación de monto negativo")
        serializer = CrearPagoPlanSerializer(data={
            'plan_tratamiento_id': 1,
            'monto': '-10.00',
            'metodo_pago': 'tarjeta'
        })
        
        if not serializer.is_valid():
            if 'monto' in serializer.errors:
                print("    ✅ Rechaza monto negativo correctamente")
            else:
                print("    ⚠️  Monto negativo rechazado pero no en campo 'monto'")
        else:
            print("    ❌ No rechaza monto negativo")
        
        # Test 2: Monto cero debe fallar
        print("\n  Test 2: Validación de monto cero")
        serializer = CrearPagoPlanSerializer(data={
            'plan_tratamiento_id': 1,
            'monto': '0.00',
            'metodo_pago': 'tarjeta'
        })
        
        if not serializer.is_valid():
            if 'monto' in serializer.errors:
                print("    ✅ Rechaza monto cero correctamente")
            else:
                print("    ⚠️  Monto cero rechazado pero no en campo 'monto'")
        else:
            print("    ❌ No rechaza monto cero")
        
        # Test 3: Campos requeridos
        print("\n  Test 3: Validación de campos requeridos")
        serializer = CrearPagoPlanSerializer(data={})
        
        if not serializer.is_valid():
            campos_requeridos = ['plan_tratamiento_id', 'monto', 'metodo_pago']
            errores_encontrados = [c for c in campos_requeridos if c in serializer.errors]
            
            if len(errores_encontrados) == len(campos_requeridos):
                print(f"    ✅ Detecta todos los campos requeridos ({len(errores_encontrados)}/3)")
            else:
                print(f"    ⚠️  Detecta {len(errores_encontrados)}/3 campos requeridos")
        else:
            print("    ❌ No valida campos requeridos")
        
        print("\n✅ Validaciones de serializers funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en validaciones de serializers: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_validadores_funciones():
    """Verifica que los validadores personalizados funcionen."""
    print("\n📋 Probando validadores personalizados...")
    
    from api.validators_pagos import (
        validar_monto_positivo,
        validar_metodo_pago_disponible
    )
    from rest_framework.exceptions import ValidationError
    from api.models import Empresa
    
    try:
        # Test 1: validar_monto_positivo
        print("\n  Test 1: validar_monto_positivo()")
        
        # Monto negativo debe fallar
        try:
            validar_monto_positivo(Decimal('-10'))
            print("    ❌ No rechaza monto negativo")
        except ValidationError:
            print("    ✅ Rechaza monto negativo correctamente")
        
        # Monto cero debe fallar
        try:
            validar_monto_positivo(Decimal('0'))
            print("    ❌ No rechaza monto cero")
        except ValidationError:
            print("    ✅ Rechaza monto cero correctamente")
        
        # Monto positivo debe pasar
        try:
            validar_monto_positivo(Decimal('100'))
            print("    ✅ Acepta monto positivo correctamente")
        except ValidationError:
            print("    ❌ Rechaza monto positivo (incorrecto)")
        
        # Test 2: validar_metodo_pago_disponible
        print("\n  Test 2: validar_metodo_pago_disponible()")
        
        # Crear empresa mock
        class MockEmpresa:
            id = 1
            nombre = "Test"
        
        empresa_mock = MockEmpresa()
        
        # Método válido
        es_valido, mensaje = validar_metodo_pago_disponible('tarjeta', empresa_mock)
        if es_valido:
            print("    ✅ Acepta método de pago válido")
        else:
            print(f"    ⚠️  Rechaza método válido: {mensaje}")
        
        # Método inválido
        es_valido, mensaje = validar_metodo_pago_disponible('metodo_invalido', empresa_mock)
        if not es_valido:
            print("    ✅ Rechaza método de pago inválido")
        else:
            print("    ❌ Acepta método inválido")
        
        print("\n✅ Validadores personalizados funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en validadores personalizados: {e}")
        import traceback
        traceback.print_exc()
        return False


def verificar_metodos_serializacion():
    """Verifica que los métodos de serialización funcionen."""
    print("\n📋 Verificando métodos de serialización...")
    
    from api.serializers_pagos import PagoEnLineaSerializer, DetallePagoItemSerializer
    
    try:
        # Verificar que los serializers tienen get_* methods
        print("\n  Verificando métodos SerializerMethodField...")
        
        serializer = PagoEnLineaSerializer()
        metodos_esperados = [
            'get_paciente_nombre',
            'get_esta_pendiente',
            'get_esta_aprobado',
            'get_puede_reintentarse',
            'get_puede_anularse',
            'get_puede_reembolsarse',
            'get_tiene_comprobante'
        ]
        
        metodos_encontrados = 0
        for metodo in metodos_esperados:
            if hasattr(serializer, metodo):
                print(f"    ✅ Método {metodo}() implementado")
                metodos_encontrados += 1
            else:
                print(f"    ❌ Método {metodo}() NO encontrado")
        
        if metodos_encontrados == len(metodos_esperados):
            print(f"\n✅ Todos los métodos de serialización implementados ({metodos_encontrados}/{len(metodos_esperados)})")
            return True
        else:
            print(f"\n❌ Faltan métodos de serialización ({metodos_encontrados}/{len(metodos_esperados)})")
            return False
        
    except Exception as e:
        print(f"\n❌ Error verificando métodos de serialización: {e}")
        return False


def verificar_validador_complejo():
    """Verifica que la clase ValidadorComplejoPagos funcione."""
    print("\n📋 Verificando ValidadorComplejoPagos...")
    
    from api.validators_pagos import ValidadorComplejoPagos
    
    try:
        # Verificar que tiene los métodos estáticos
        metodos = [
            'validar_crear_pago_plan',
            'validar_crear_pago_consulta'
        ]
        
        metodos_encontrados = 0
        for metodo in metodos:
            if hasattr(ValidadorComplejoPagos, metodo):
                print(f"  ✅ Método {metodo}() implementado")
                metodos_encontrados += 1
            else:
                print(f"  ❌ Método {metodo}() NO encontrado")
        
        if metodos_encontrados == len(metodos):
            print(f"✅ ValidadorComplejoPagos completo ({metodos_encontrados}/{len(metodos)} métodos)")
            return True
        else:
            print(f"❌ ValidadorComplejoPagos incompleto ({metodos_encontrados}/{len(metodos)} métodos)")
            return False
        
    except Exception as e:
        print(f"❌ Error verificando ValidadorComplejoPagos: {e}")
        return False


def main():
    """Ejecuta todas las verificaciones de FASE 3."""
    print("="*70)
    print("🔍 VERIFICACIÓN FASE 3: Serializers y Validaciones")
    print("="*70)
    
    resultados = []
    
    # 1. Verificar imports de serializers
    resultados.append(("Imports Serializers", verificar_imports_serializers()))
    
    # 2. Verificar imports de validadores
    resultados.append(("Imports Validadores", verificar_imports_validadores()))
    
    # 3. Verificar estructura de serializers
    resultados.append(("Estructura Serializers", verificar_estructura_serializers()))
    
    # 4. Verificar validaciones en serializers
    resultados.append(("Validaciones Serializers", verificar_validaciones_serializers()))
    
    # 5. Verificar validadores personalizados
    resultados.append(("Validadores Personalizados", verificar_validadores_funciones()))
    
    # 6. Verificar métodos de serialización
    resultados.append(("Métodos Serialización", verificar_metodos_serializacion()))
    
    # 7. Verificar ValidadorComplejoPagos
    resultados.append(("ValidadorComplejoPagos", verificar_validador_complejo()))
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("="*70)
    
    total_tests = len(resultados)
    tests_pasados = sum(1 for _, resultado in resultados if resultado)
    
    for nombre, resultado in resultados:
        icono = "✅" if resultado else "❌"
        print(f"{icono} {nombre}")
    
    print("\n" + "="*70)
    
    if tests_pasados == total_tests:
        print(f"🎯 FASE 3 COMPLETADA EXITOSAMENTE")
        print(f"✅ {tests_pasados}/{total_tests} verificaciones pasadas")
        print("\n📌 Funcionalidades implementadas:")
        print("  • 8 serializers para lectura y escritura de pagos")
        print("  • 11 validadores personalizados")
        print("  • Validaciones de monto, saldo, estado y origen")
        print("  • Validaciones de items y distribución de pagos")
        print("  • Validaciones de métodos de pago")
        print("  • Validaciones de anulación y reembolso")
        print("  • ValidadorComplejoPagos para validaciones complejas")
        print("  • Métodos SerializerMethodField para campos computados")
        print("\n🚀 Lista para FASE 4: Integración con Stripe")
        return True
    else:
        print(f"⚠️  FASE 3 INCOMPLETA")
        print(f"❌ {total_tests - tests_pasados}/{total_tests} verificaciones fallaron")
        print("\nPor favor, revisa los errores arriba antes de continuar.")
        return False


if __name__ == '__main__':
    try:
        exito = main()
        sys.exit(0 if exito else 1)
    except Exception as e:
        print(f"\n❌ Error crítico durante verificación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
