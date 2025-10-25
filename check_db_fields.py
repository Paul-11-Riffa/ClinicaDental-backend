#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import connection

# Check itemplandetratamiento fields
print("=== ITEMPLANDETRATAMIENTO ===")
cursor = connection.cursor()
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='itemplandetratamiento' 
    ORDER BY ordinal_position;
""")
item_columns = [row[0] for row in cursor.fetchall()]
print(f"Columns in DB: {item_columns}")

# Check plandetratamiento fields
print("\n=== PLANDETRATAMIENTO ===")
cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name='plandetratamiento' 
    ORDER BY ordinal_position;
""")
plan_columns = [row[0] for row in cursor.fetchall()]
print(f"Columns in DB: {plan_columns}")

# Compare with model fields
from api.models import Itemplandetratamiento, Plandetratamiento

print("\n=== COMPARISON ITEMPLANDETRATAMIENTO ===")
model_fields = [f.name for f in Itemplandetratamiento._meta.get_fields() if f.concrete]
print(f"Model fields: {model_fields}")

missing_in_db = set(model_fields) - set(item_columns)
print(f"Missing in DB: {missing_in_db}")

extra_in_db = set(item_columns) - set(model_fields)
print(f"Extra in DB: {extra_in_db}")

print("\n=== COMPARISON PLANDETRATAMIENTO ===")
model_fields_plan = [f.name for f in Plandetratamiento._meta.get_fields() if f.concrete]
print(f"Model fields: {model_fields_plan}")

missing_in_db_plan = set(model_fields_plan) - set(plan_columns)
print(f"Missing in DB: {missing_in_db_plan}")

extra_in_db_plan = set(plan_columns) - set(model_fields_plan)
print(f"Extra in DB: {extra_in_db_plan}")
