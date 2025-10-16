#!/usr/bin/env python
"""
Script para crear la base de datos PostgreSQL para el proyecto Django
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('api/.env')

# Configuración de la base de datos
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'ClinicaDental')

def create_database():
    """Crear la base de datos si no existe"""
    try:
        # Conectar a la base de datos por defecto 'postgres'
        print(f"Conectando a PostgreSQL en {DB_HOST}:{DB_PORT}...")
        conn = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Verificar si la base de datos ya existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"✓ La base de datos '{DB_NAME}' ya existe.")
        else:
            # Crear la base de datos
            print(f"Creando base de datos '{DB_NAME}'...")
            cursor.execute(
                sql.SQL("CREATE DATABASE {} WITH ENCODING 'UTF8'").format(
                    sql.Identifier(DB_NAME)
                )
            )
            print(f"✓ Base de datos '{DB_NAME}' creada exitosamente!")

        cursor.close()
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"✗ Error al conectar o crear la base de datos:")
        print(f"  {e}")
        return False
    except Exception as e:
        print(f"✗ Error inesperado: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CREACIÓN DE BASE DE DATOS - CLÍNICA DENTAL")
    print("=" * 60)
    print(f"Base de datos: {DB_NAME}")
    print(f"Usuario: {DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("=" * 60)

    if create_database():
        print("\n✓ Proceso completado exitosamente!")
        print("\nPróximos pasos:")
        print("  1. Ejecutar: python manage.py makemigrations")
        print("  2. Ejecutar: python manage.py migrate")
        print("  3. Crear superusuario: python manage.py createsuperuser")
    else:
        print("\n✗ No se pudo crear la base de datos.")
        print("\nVerifica que:")
        print("  - El servicio PostgreSQL esté iniciado")
        print("  - Las credenciales en api/.env sean correctas")
        print("  - El usuario tenga permisos para crear bases de datos")