"""
Script para limpiar completamente la base de datos RDS y aplicar nuevas migraciones.
ADVERTENCIA: Esto eliminará TODOS los datos de forma permanente.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def reset_database():
    """Elimina todas las tablas y recrea el schema."""

    # Configuración de la base de datos desde .env
    db_config = {
        'dbname': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432')
    }

    print("=" * 60)
    print("ADVERTENCIA: Este script eliminará TODOS los datos")
    print("=" * 60)
    print(f"Base de datos: {db_config['dbname']}")
    print(f"Host: {db_config['host']}")
    print("=" * 60)

    # Pedir confirmación
    confirmacion = input("\n¿Estás SEGURO de que deseas continuar? (escribe 'SI ELIMINAR TODO'): ")

    if confirmacion != "SI ELIMINAR TODO":
        print("\nOperación cancelada.")
        sys.exit(0)

    try:
        # Conectar a la base de datos
        print("\n1. Conectando a la base de datos...")
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        # Eliminar el schema public y recrearlo
        print("2. Eliminando todas las tablas...")
        cursor.execute("DROP SCHEMA public CASCADE;")
        print("   ✓ Schema 'public' eliminado")

        print("3. Recreando schema 'public'...")
        cursor.execute("CREATE SCHEMA public;")
        print("   ✓ Schema 'public' recreado")

        # Otorgar permisos
        print("4. Configurando permisos...")
        cursor.execute("GRANT ALL ON SCHEMA public TO postgres;")
        cursor.execute("GRANT ALL ON SCHEMA public TO public;")
        print("   ✓ Permisos configurados")

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print("✓ Base de datos limpiada exitosamente")
        print("=" * 60)
        print("\nAhora ejecuta:")
        print("1. python manage.py migrate")
        print("2. python manage.py createsuperuser (para crear usuario admin)")

    except psycopg2.Error as e:
        print(f"\n✗ Error al limpiar la base de datos: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_database()