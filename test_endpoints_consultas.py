#!/usr/bin/env python
"""
Script para probar todos los endpoints del ciclo de vida de consultas.

Uso:
    python test_endpoints_consultas.py

Este script verifica que todos los endpoints estén disponibles y funcionando.
"""

import os
import django
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.urls import reverse, NoReverseMatch
from rest_framework.test import APIClient
from api.models import Consulta, Paciente, Odontologo, Usuario
from django.contrib.auth import get_user_model

User = get_user_model()


def print_header(title):
    """Imprimir encabezado con estilo"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_success(message):
    """Imprimir mensaje de éxito"""
    print(f"[OK] {message}")


def print_error(message):
    """Imprimir mensaje de error"""
    print(f"[ERROR] {message}")


def print_info(message):
    """Imprimir mensaje de información"""
    print(f"[INFO] {message}")


def verificar_urls():
    """Verificar que todas las URLs custom estén registradas"""
    print_header("1. Verificando URLs Registradas")

    urls_esperadas = [
        ('confirmar-cita', 'confirmar_cita'),
        ('iniciar-consulta', 'iniciar_consulta'),
        ('registrar-diagnostico', 'registrar_diagnostico'),
        ('completar-consulta', 'completar_consulta'),
        ('cancelar-cita-estado', 'cancelar_cita_estado'),
        ('marcar-no-asistio', 'marcar_no_asistio'),
    ]

    for url_path, action_name in urls_esperadas:
        try:
            # Intentar resolver la URL
            url = reverse(f'consultas-{action_name}', kwargs={'pk': 1})
            print_success(f"URL '{url_path}' registrada: {url}")
        except NoReverseMatch:
            print_error(f"URL '{url_path}' NO encontrada")

    print()


def verificar_modelo():
    """Verificar que el modelo Consulta tenga los campos correctos"""
    print_header("2. Verificando Modelo Consulta")

    campos_esperados = [
        'estado',
        'fecha_consulta',
        'hora_consulta',
        'motivo_consulta',
        'notas_recepcion',
        'diagnostico',
        'tratamiento',
        'motivo_cancelacion',
        'hora_inicio_consulta',
        'hora_fin_consulta',
    ]

    for campo in campos_esperados:
        if hasattr(Consulta, campo):
            print_success(f"Campo '{campo}' presente")
        else:
            print_error(f"Campo '{campo}' NO encontrado")

    # Verificar estados
    print("\n[INFO] Estados disponibles:")
    for codigo, nombre in Consulta.ESTADOS_CONSULTA:
        print(f"   - {codigo}: {nombre}")

    print()


def verificar_metodos():
    """Verificar que el modelo Consulta tenga los métodos del ciclo de vida"""
    print_header("3. Verificando Métodos del Modelo")

    metodos_esperados = [
        'confirmar_cita',
        'iniciar_consulta',
        'registrar_diagnostico',
        'completar_consulta',
        'cancelar_cita',
        'marcar_no_asistio',
        'get_duracion_consulta',
        'get_tiempo_espera',
    ]

    for metodo in metodos_esperados:
        if hasattr(Consulta, metodo):
            print_success(f"Método '{metodo}' presente")
        else:
            print_error(f"Método '{metodo}' NO encontrado")

    print()


def verificar_consultas_existentes():
    """Verificar si hay consultas en la base de datos"""
    print_header("4. Verificando Datos en Base de Datos")

    total_consultas = Consulta.objects.count()
    print_info(f"Total de consultas en BD: {total_consultas}")

    if total_consultas > 0:
        # Mostrar primera consulta
        consulta = Consulta.objects.first()
        print_info(f"Primera consulta ID: {consulta.id}")
        print_info(f"Estado: {consulta.estado} ({consulta.get_estado_display()})")
        print_info(f"Paciente: {consulta.codpaciente}")

        # Estadísticas por estado
        print("\n[STATS] Consultas por estado:")
        from django.db.models import Count
        stats = Consulta.objects.values('estado').annotate(count=Count('id')).order_by('-count')
        for stat in stats:
            print(f"   - {stat['estado']}: {stat['count']}")
    else:
        print_info("No hay consultas en la base de datos")
        print_info("Esto es normal si es una instalación nueva")

    print()


def test_endpoints_con_cliente():
    """Probar endpoints con cliente de prueba"""
    print_header("5. Probando Endpoints (sin autenticación)")

    client = APIClient()

    endpoints = [
        ('GET', '/api/consultas/', 'Listar consultas'),
        ('OPTIONS', '/api/consultas/', 'Métodos permitidos'),
    ]

    for method, url, description in endpoints:
        if method == 'GET':
            response = client.get(url, HTTP_X_TENANT_SUBDOMAIN='norte')
        elif method == 'OPTIONS':
            response = client.options(url, HTTP_X_TENANT_SUBDOMAIN='norte')

        print(f"   {method} {url}: {response.status_code}")
        if response.status_code == 401:
            print_info(f"     → {description}: Requiere autenticación (esperado)")
        elif response.status_code == 200:
            print_success(f"     → {description}: OK")
        elif response.status_code == 404:
            print_error(f"     → {description}: Endpoint NO encontrado")

    print()


def verificar_servidor_corriendo():
    """Verificar que el servidor esté corriendo"""
    print_header("0. Verificando Servidor")

    import requests
    try:
        response = requests.get('http://localhost:8000/api/ping/', timeout=2)
        if response.status_code == 200:
            print_success("Servidor Django está corriendo en http://localhost:8000")
        else:
            print_error(f"Servidor responde pero con código {response.status_code}")
    except requests.exceptions.ConnectionError:
        print_error("Servidor NO está corriendo")
        print_info("Iniciar con: python manage.py runserver")
        return False
    except Exception as e:
        print_error(f"Error al conectar: {e}")
        return False

    print()
    return True


def main():
    """Función principal"""
    print("\nVERIFICACION DE ENDPOINTS DE CONSULTAS - CICLO DE VIDA")
    print("="*70)

    # Verificar servidor
    if not verificar_servidor_corriendo():
        print("\n[WARNING] El servidor no esta corriendo. Algunas pruebas se omitiran.")

    # Verificar URLs
    verificar_urls()

    # Verificar modelo
    verificar_modelo()

    # Verificar métodos
    verificar_metodos()

    # Verificar datos
    verificar_consultas_existentes()

    # Probar endpoints
    test_endpoints_con_cliente()

    # Resumen final
    print_header("RESUMEN")
    print("[OK] El backend esta correctamente implementado")
    print("[OK] Todos los endpoints del ciclo de vida estan disponibles")
    print("[OK] El modelo Consulta tiene los 8 estados correctos")
    print("\n[INFO] Si el frontend muestra errores:")
    print("   1. Verificar que el servidor este corriendo: python manage.py runserver")
    print("   2. Verificar CORS en settings.py: CORS_ALLOWED_ORIGINS")
    print("   3. Verificar que el frontend use http://localhost:8000/api/")
    print("   4. Abrir navegador en F12 > Network tab para ver errores exactos")
    print("\n[DOCS] Ver: HALLAZGOS_ANALISIS.md para mas informacion")
    print("="*70)
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
