"""
Kill all connections to test database to allow recreation
"""
import psycopg2
from dental_clinic_backend.settings import DATABASES

# Connect to postgres database (not the target database)
conn = psycopg2.connect(
    host=DATABASES['default']['HOST'],
    port=DATABASES['default']['PORT'],
    database='postgres',  # Connect to postgres, not target
    user=DATABASES['default']['USER'],
    password=DATABASES['default']['PASSWORD']
)
conn.autocommit = True
cursor = conn.cursor()

# Kill all connections to test database
try:
    cursor.execute("""
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = 'test_neondb'
          AND pid <> pg_backend_pid();
    """)
    print("✅ Killed all connections to test_neondb")
except Exception as e:
    print(f"Error: {e}")
finally:
    cursor.close()
    conn.close()
