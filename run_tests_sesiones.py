"""
Script para ejecutar tests de SP3-T008 de manera simple
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

# Importar después del setup
from django.test.utils import get_runner
from django.conf import settings

print("\n" + "="*80)
print("EJECT ANDO TESTS - SP3-T008: SESIONES DE TRATAMIENTO")
print("="*80 + "\n")

# Configurar y ejecutar el test runner
TestRunner = get_runner(settings)
test_runner = TestRunner(verbosity=2, interactive=False, keepdb=False)

# Ejecutar solo nuestros tests
failures = test_runner.run_tests(["api.tests_sesiones"])

# Resumen final
print("\n" + "="*80)
if failures == 0:
    print("✅ ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
    print("="*80)
    print("\n📋 FUNCIONALIDADES VERIFICADAS:")
    print("  ✓ Crear sesiones básicas")
    print("  ✓ Prevenir sesiones duplicadas (UniqueConstraint)")
    print("  ✓ Progreso no retrocede")
    print("  ✓ Auto-completar ítems al 100%")
    print("  ✓ No permitir sesiones en ítems cancelados")
    print("  ✓ Múltiples sesiones progresivas")
    print("  ✓ Recalcular progreso del plan")
    print("  ✓ Guardar evidencias en JSON")
    print("\n🎯 LA FUNCIONALIDAD SP3-T008 ESTÁ COMPLETAMENTE OPERATIVA")
else:
    print(f"❌ {failures} TEST(S) FALLARON")
    print("Revisa los detalles arriba para más información.")
print("="*80 + "\n")

sys.exit(0 if failures == 0 else 1)
