#!/usr/bin/env python
"""
Script para eliminar la base de datos de test antes de ejecutar tests
"""
import os
import sys
import django
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.conf import settings

def eliminar_test_db():
    """Elimina la base de datos de test si existe"""
    db_settings = settings.DATABASES['default']
    
    # Nombre de la BD de test (Django agrega 'test_' al nombre)
    test_db_name = f"test_{db_settings['NAME']}"
    
    print(f"🗑️  Intentando eliminar base de datos de test: {test_db_name}")
    
    try:
        # Conectar a la BD por defecto (postgres) para poder eliminar la BD de test
        conn = psycopg2.connect(
            dbname='postgres',  # Conectar a la BD por defecto
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            host=db_settings['HOST'],
            port=db_settings['PORT'],
            sslmode=db_settings['OPTIONS']['sslmode']
        )
        
        # Necesario para ejecutar DROP DATABASE
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Terminar todas las conexiones activas a la BD de test
        cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{test_db_name}'
            AND pid <> pg_backend_pid();
        """)
        
        # Eliminar la BD de test
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name};")
        
        print(f"✅ Base de datos de test eliminada exitosamente")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error al eliminar BD de test: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

if __name__ == '__main__':
    success = eliminar_test_db()
    sys.exit(0 if success else 1)
