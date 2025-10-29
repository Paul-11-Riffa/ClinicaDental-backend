import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("""
    SELECT column_name, is_nullable, data_type, column_default 
    FROM information_schema.columns 
    WHERE table_name='consulta' AND column_name='tipo_consulta'
""")

result = cursor.fetchall()
if result:
    col_name, is_nullable, data_type, default = result[0]
    print(f"Column: {col_name}")
    print(f"Nullable: {is_nullable}")
    print(f"Type: {data_type}")
    print(f"Default: {default}")
else:
    print("Column 'tipo_consulta' not found")
