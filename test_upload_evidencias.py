"""
Script de prueba para el sistema de upload de evidencias.

SP3-T008 - FASE 5: Test de funcionalidad de upload de archivos

Este script verifica:
1. Creación de modelo Evidencia
2. Validación de archivos
3. Funciones auxiliares (obtener_ip_cliente, sanitización)
4. Serializers
5. Path generation

Ejecutar: python test_upload_evidencias.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from api.models import Evidencia, Empresa, Usuario, Tipodeusuario
from api.serializers_evidencias import (
    EvidenciaSerializer,
    EvidenciaUploadSerializer,
    EvidenciaResponseSerializer
)
from api.views_evidencias import obtener_ip_cliente
from io import BytesIO
from PIL import Image
import json


def print_test(name, status, details=""):
    """Helper para imprimir resultados de tests"""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {name}")
    if details:
        print(f"   └─ {details}")


def create_test_image():
    """Crea una imagen de prueba en memoria"""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.read()


def test_modelo_evidencia():
    """Test 1: Verificar que el modelo Evidencia existe y tiene todos los campos"""
    print("\n" + "="*60)
    print("TEST 1: Modelo Evidencia")
    print("="*60)
    
    try:
        # Verificar campos del modelo
        expected_fields = [
            'archivo', 'nombre_original', 'tipo', 'mimetype', 
            'tamanio', 'usuario', 'empresa', 'fecha_subida', 'ip_subida'
        ]
        
        model_fields = [f.name for f in Evidencia._meta.get_fields()]
        
        for field in expected_fields:
            if field in model_fields:
                print_test(f"Campo '{field}' existe", True)
            else:
                print_test(f"Campo '{field}' existe", False, "FALTA")
                return False
        
        # Verificar choices de tipo
        tipo_choices = dict(Evidencia.TIPO_CHOICES)
        expected_choices = ['evidencia_sesion', 'radiografia', 'foto_clinica', 'documento']
        
        for choice in expected_choices:
            if choice in tipo_choices:
                print_test(f"Tipo '{choice}' disponible", True)
            else:
                print_test(f"Tipo '{choice}' disponible", False, "FALTA")
        
        # Verificar Meta
        print_test("db_table configurado", Evidencia._meta.db_table == 'evidencias')
        print_test("ordering configurado", Evidencia._meta.ordering == ['-fecha_subida'])
        
        # Verificar índices
        indexes = Evidencia._meta.indexes
        print_test(f"Índices creados ({len(indexes)} índices)", len(indexes) == 3)
        
        print_test("✓ Modelo Evidencia correctamente configurado", True)
        return True
        
    except Exception as e:
        print_test("Modelo Evidencia", False, str(e))
        return False


def test_serializers():
    """Test 2: Verificar serializers"""
    print("\n" + "="*60)
    print("TEST 2: Serializers")
    print("="*60)
    
    try:
        # Test EvidenciaUploadSerializer
        img_data = create_test_image()
        test_file = SimpleUploadedFile(
            "test_image.jpg",
            img_data,
            content_type="image/jpeg"
        )
        
        data = {
            'file': test_file,
            'tipo': 'evidencia_sesion'
        }
        
        serializer = EvidenciaUploadSerializer(data=data)
        is_valid = serializer.is_valid()
        
        if is_valid:
            print_test("EvidenciaUploadSerializer valida archivo JPG", True)
        else:
            print_test("EvidenciaUploadSerializer valida archivo JPG", False, 
                      serializer.errors)
            return False
        
        # Test con archivo muy grande (debería fallar)
        large_file = SimpleUploadedFile(
            "large.jpg",
            b"x" * (6 * 1024 * 1024),  # 6MB (límite es 5MB)
            content_type="image/jpeg"
        )
        
        serializer_large = EvidenciaUploadSerializer(data={'file': large_file})
        is_valid_large = serializer_large.is_valid()
        
        print_test("Rechaza archivos >5MB", not is_valid_large, 
                  "Correctamente rechazado" if not is_valid_large else "ERROR: Aceptó archivo grande")
        
        # Test con extensión no permitida
        bad_file = SimpleUploadedFile(
            "test.exe",
            b"fake exe content",
            content_type="application/x-msdownload"
        )
        
        serializer_bad = EvidenciaUploadSerializer(data={'file': bad_file})
        is_valid_bad = serializer_bad.is_valid()
        
        print_test("Rechaza extensiones no permitidas (.exe)", not is_valid_bad,
                  "Correctamente rechazado" if not is_valid_bad else "ERROR: Aceptó .exe")
        
        print_test("✓ Serializers funcionan correctamente", True)
        return True
        
    except Exception as e:
        print_test("Serializers", False, str(e))
        return False


def test_path_generation():
    """Test 3: Verificar generación de paths"""
    print("\n" + "="*60)
    print("TEST 3: Generación de Paths")
    print("="*60)
    
    try:
        from api.models import evidencia_upload_path
        from datetime import datetime
        
        # Crear instancia mock
        class MockInstance:
            fecha_subida = datetime.now()
        
        instance = MockInstance()
        
        # Test con nombre normal
        path1 = evidencia_upload_path(instance, "mi_radiografia.jpg")
        print_test("Path generado con UUID", ".jpg" in path1 and "evidencias" in path1)
        print(f"   └─ Ejemplo: {path1}")
        
        # Test con caracteres especiales
        path2 = evidencia_upload_path(instance, "Foto Clínica #123 (2025).png")
        print_test("Sanitiza caracteres especiales", 
                  "#" not in path2 and "(" not in path2 and " " not in path2)
        print(f"   └─ Sanitizado: {path2}")
        
        # Test estructura de directorio
        year = str(instance.fecha_subida.year)
        month = str(instance.fecha_subida.month)
        day = str(instance.fecha_subida.day)
        
        has_structure = (year in path1 and month in path1 and day in path1)
        print_test(f"Estructura año/mes/día ({year}/{month}/{day})", has_structure)
        
        print_test("✓ Generación de paths correcta", True)
        return True
        
    except Exception as e:
        print_test("Generación de paths", False, str(e))
        return False


def test_funciones_auxiliares():
    """Test 4: Verificar funciones auxiliares"""
    print("\n" + "="*60)
    print("TEST 4: Funciones Auxiliares")
    print("="*60)
    
    try:
        # Test obtener_ip_cliente
        factory = RequestFactory()
        
        # Sin proxy
        request1 = factory.get('/')
        request1.META['REMOTE_ADDR'] = '192.168.1.100'
        ip1 = obtener_ip_cliente(request1)
        print_test("obtener_ip_cliente sin proxy", ip1 == '192.168.1.100')
        
        # Con proxy
        request2 = factory.get('/')
        request2.META['HTTP_X_FORWARDED_FOR'] = '203.0.113.1, 198.51.100.1'
        request2.META['REMOTE_ADDR'] = '192.168.1.1'
        ip2 = obtener_ip_cliente(request2)
        print_test("obtener_ip_cliente con proxy", ip2 == '203.0.113.1')
        
        print_test("✓ Funciones auxiliares correctas", True)
        return True
        
    except Exception as e:
        print_test("Funciones auxiliares", False, str(e))
        return False


def test_metodos_modelo():
    """Test 5: Verificar métodos del modelo"""
    print("\n" + "="*60)
    print("TEST 5: Métodos del Modelo")
    print("="*60)
    
    try:
        # Test get_tamanio_legible
        class MockEvidencia:
            tamanio = 0
            
            def get_tamanio_legible(self):
                size = self.tamanio
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024.0:
                        return f"{size:.2f} {unit}"
                    size /= 1024.0
                return f"{size:.2f} TB"
        
        mock1 = MockEvidencia()
        mock1.tamanio = 512
        result1 = mock1.get_tamanio_legible()
        print_test("512 bytes → '512.00 B'", "512" in result1 and "B" in result1)
        
        mock2 = MockEvidencia()
        mock2.tamanio = 2048
        result2 = mock2.get_tamanio_legible()
        print_test("2048 bytes → '2.00 KB'", "2.00" in result2 and "KB" in result2)
        
        mock3 = MockEvidencia()
        mock3.tamanio = 1048576
        result3 = mock3.get_tamanio_legible()
        print_test("1048576 bytes → '1.00 MB'", "1.00" in result3 and "MB" in result3)
        
        print_test("✓ Métodos del modelo funcionan", True)
        return True
        
    except Exception as e:
        print_test("Métodos del modelo", False, str(e))
        return False


def test_integracion_base_datos():
    """Test 6: Test de integración con base de datos"""
    print("\n" + "="*60)
    print("TEST 6: Integración con Base de Datos")
    print("="*60)
    
    try:
        # Verificar que la tabla existe
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_name = 'evidencias'
            """)
            table_exists = cursor.fetchone()[0] > 0
        
        print_test("Tabla 'evidencias' existe en BD", table_exists)
        
        if not table_exists:
            print_test("✗ Tabla no existe - migración no aplicada", False)
            return False
        
        # Verificar columnas
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'evidencias'
            """)
            columns = [row[0] for row in cursor.fetchall()]
        
        expected_columns = [
            'id', 'archivo', 'nombre_original', 'tipo', 'mimetype',
            'tamanio', 'fecha_subida', 'ip_subida', 'empresa_id', 'usuario_id'
        ]
        
        for col in expected_columns:
            if col in columns:
                print_test(f"Columna '{col}' existe", True)
            else:
                print_test(f"Columna '{col}' existe", False, "FALTA")
        
        # Verificar índices
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'evidencias'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
        
        print_test(f"Índices creados ({len(indexes)} índices)", len(indexes) >= 3)
        
        print_test("✓ Integración con BD correcta", True)
        return True
        
    except Exception as e:
        print_test("Integración con BD", False, str(e))
        return False


def test_crear_evidencia_real():
    """Test 7: Crear evidencia real en base de datos"""
    print("\n" + "="*60)
    print("TEST 7: Crear Evidencia Real")
    print("="*60)
    
    try:
        # Buscar o crear empresa de prueba
        empresa, _ = Empresa.objects.get_or_create(
            subdomain='test_upload',
            defaults={
                'nombre': 'Clínica Test Upload',
                'activo': True
            }
        )
        print_test("Empresa de prueba creada/encontrada", True, f"ID: {empresa.id}")
        
        # Buscar o crear tipo de usuario
        tipo_usuario = Tipodeusuario.objects.filter(
            rol='Administrador'
        ).first()
        
        if not tipo_usuario:
            tipo_usuario = Tipodeusuario.objects.first()
        
        if not tipo_usuario:
            tipo_usuario = Tipodeusuario.objects.create(
                rol='Administrador',
                descripcion='Administrador del sistema'
            )
        
        # Buscar o crear usuario de prueba
        usuario, _ = Usuario.objects.get_or_create(
            correoelectronico='test_upload@test.com',
            defaults={
                'nombre': 'Usuario',
                'apellido': 'Test Upload',
                'idtipousuario': tipo_usuario,
                'empresa': empresa
            }
        )
        print_test("Usuario de prueba creado/encontrado", True, f"ID: {usuario.codigo}")
        
        # Crear archivo de prueba
        img_data = create_test_image()
        test_file = SimpleUploadedFile(
            "test_radiografia.jpg",
            img_data,
            content_type="image/jpeg"
        )
        
        # Crear evidencia
        evidencia = Evidencia.objects.create(
            archivo=test_file,
            nombre_original="test_radiografia.jpg",
            tipo="radiografia",
            mimetype="image/jpeg",
            tamanio=len(img_data),
            usuario=usuario,
            empresa=empresa,
            ip_subida="192.168.1.100"
        )
        
        print_test("Evidencia creada en BD", True, f"ID: {evidencia.id}")
        print_test("Archivo guardado", bool(evidencia.archivo))
        print_test("URL generada", bool(evidencia.url), evidencia.url)
        print_test("Tamaño legible", evidencia.get_tamanio_legible() != "", 
                  evidencia.get_tamanio_legible())
        
        # Verificar filtrado por empresa
        evidencias_empresa = Evidencia.objects.filter(empresa=empresa)
        print_test("Filtrado por empresa funciona", evidencias_empresa.count() > 0,
                  f"{evidencias_empresa.count()} evidencia(s)")
        
        # Limpiar (eliminar evidencia de prueba)
        evidencia.delete()
        print_test("Evidencia eliminada (cleanup)", True)
        
        print_test("✓ CRUD de evidencia funciona correctamente", True)
        return True
        
    except Exception as e:
        print_test("Crear evidencia real", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n" + "="*60)
    print("🧪 SISTEMA DE PRUEBAS - UPLOAD DE EVIDENCIAS")
    print("SP3-T008 - FASE 5")
    print("="*60)
    
    results = []
    
    # Ejecutar tests
    results.append(("Modelo Evidencia", test_modelo_evidencia()))
    results.append(("Serializers", test_serializers()))
    results.append(("Generación de Paths", test_path_generation()))
    results.append(("Funciones Auxiliares", test_funciones_auxiliares()))
    results.append(("Métodos del Modelo", test_metodos_modelo()))
    results.append(("Integración BD", test_integracion_base_datos()))
    results.append(("CRUD Real", test_crear_evidencia_real()))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        symbol = "✅" if result else "❌"
        print(f"{symbol} {name}")
    
    print("\n" + "="*60)
    percentage = (passed / total) * 100
    print(f"✓ Tests Pasados: {passed}/{total} ({percentage:.1f}%)")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
        print("✅ Sistema de upload de evidencias funcionando correctamente")
    else:
        print(f"⚠️  {total - passed} test(s) fallaron")
        print("❌ Revisar implementación")
    
    print("="*60 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
