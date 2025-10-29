"""
Script to analyze current database structure for Consulta and Estadodeconsulta
This will help us understand the data before migration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import connection
from api.models import Consulta, Estadodeconsulta, Empresa
from django.db.models import Count

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def analyze_estadodeconsulta_table():
    """Analyze the Estadodeconsulta table structure and data"""
    print_section("1. ESTADODECONSULTA TABLE ANALYSIS")
    
    # Get all estados
    estados = Estadodeconsulta.objects.all()
    print(f"Total estados in table: {estados.count()}\n")
    
    print("Current estados:")
    print("-" * 60)
    for estado in estados:
        # Count consultas using this estado
        consulta_count = Consulta.objects.filter(idestadoconsulta=estado).count()
        print(f"ID: {estado.id:3d} | Estado: {estado.estado:30s} | Used by {consulta_count:4d} consultas")
    
    return estados

def analyze_consulta_table():
    """Analyze Consulta table structure"""
    print_section("2. CONSULTA TABLE ANALYSIS")
    
    total_consultas = Consulta.objects.count()
    print(f"Total consultas in database: {total_consultas}\n")
    
    if total_consultas == 0:
        print("⚠️  No consultas found in database - safe to add new fields\n")
        return
    
    # Group by estado
    print("Consultas by estado:")
    print("-" * 60)
    estado_counts = Consulta.objects.values(
        'idestadoconsulta__estado'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    for item in estado_counts:
        estado_name = item['idestadoconsulta__estado'] or 'NULL'
        count = item['count']
        print(f"{estado_name:30s} : {count:4d} consultas")
    
    print()

def analyze_consulta_fields():
    """Check which fields are currently populated"""
    print_section("3. CONSULTA FIELD POPULATION ANALYSIS")
    
    total = Consulta.objects.count()
    if total == 0:
        print("No consultas to analyze\n")
        return
    
    # Check key fields
    fields_to_check = [
        'fecha',
        'codpaciente',
        'cododontologo',
        'idestadoconsulta',
        'idtipoconsulta',
        'motivoconsulta',
        'diagnostico',
        'tratamiento',
        'observaciones',
        'costo_consulta',
        'requiere_pago',
        'plan_tratamiento',
        'pago_consulta',
    ]
    
    print("Field population rates:")
    print("-" * 60)
    for field in fields_to_check:
        try:
            # Count non-null values
            if field in ['codpaciente', 'cododontologo', 'idestadoconsulta', 
                         'idtipoconsulta', 'plan_tratamiento', 'pago_consulta']:
                # FK fields
                count = Consulta.objects.filter(**{f'{field}__isnull': False}).count()
            elif field == 'requiere_pago':
                # Boolean field
                count = total  # Always populated
            else:
                # Text/Decimal fields
                count = Consulta.objects.exclude(**{field: ''}).exclude(**{f'{field}__isnull': True}).count()
            
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{field:25s} : {count:4d}/{total:4d} ({percentage:5.1f}%)")
        except Exception as e:
            print(f"{field:25s} : Error - {str(e)}")
    
    print()

def check_database_schema():
    """Check actual database schema using raw SQL"""
    print_section("4. DATABASE SCHEMA CHECK (Consulta table)")
    
    with connection.cursor() as cursor:
        # Get table columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'consulta'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("Current columns in 'consulta' table:")
        print("-" * 80)
        print(f"{'Column Name':<30} {'Type':<20} {'Nullable':<10} {'Default'}")
        print("-" * 80)
        
        for col in columns:
            col_name, data_type, is_nullable, default = col
            default_str = str(default)[:20] if default else ''
            print(f"{col_name:<30} {data_type:<20} {is_nullable:<10} {default_str}")
    
    print()

def analyze_empresas():
    """Check how many empresas we have"""
    print_section("5. TENANT (EMPRESA) ANALYSIS")
    
    empresas = Empresa.objects.all()
    print(f"Total empresas (tenants): {empresas.count()}\n")
    
    for empresa in empresas:
        consulta_count = Consulta.objects.filter(empresa=empresa).count()
        print(f"Empresa: {empresa.nombre:30s} | Consultas: {consulta_count:4d}")
    
    print()

def mapping_recommendations():
    """Provide recommendations for estado mapping"""
    print_section("6. ESTADO MAPPING RECOMMENDATIONS")
    
    print("Recommended mapping from current estados to new CharField:\n")
    print("-" * 80)
    
    # Get all current estados
    estados = Estadodeconsulta.objects.all()
    
    # Define mapping rules (you can adjust these)
    mapping_rules = {
        'completado': 'completada',
        'completada': 'completada',
        'en proceso': 'en_consulta',
        'en_proceso': 'en_consulta',
        'pendiente': 'solicitada',
        'cancelado': 'cancelada',
        'cancelada': 'cancelada',
        'confirmado': 'confirmada',
        'confirmada': 'confirmada',
        'diagnosticado': 'diagnosticada',
        'diagnosticada': 'diagnosticada',
    }
    
    for estado in estados:
        estado_lower = estado.estado.lower().strip()
        new_estado = mapping_rules.get(estado_lower, 'solicitada')  # Default
        consulta_count = Consulta.objects.filter(idestadoconsulta=estado).count()
        
        status_icon = "✓" if estado_lower in mapping_rules else "?"
        print(f"{status_icon} '{estado.estado}' -> '{new_estado}' ({consulta_count} consultas)")
    
    print("\nNotes:")
    print("- Estados with '?' need manual review")
    print("- Default mapping is 'solicitada' for unknown estados")
    print("- You can adjust these mappings in the migration script")
    print()

def check_for_conflicts():
    """Check for potential migration conflicts"""
    print_section("7. POTENTIAL MIGRATION CONFLICTS")
    
    issues = []
    
    # Check if 'estado' field already exists
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns
            WHERE table_name = 'consulta' 
            AND column_name = 'estado'
        """)
        if cursor.fetchone():
            issues.append("⚠️  'estado' CharField already exists in Consulta table")
    
    # Check for consultas without idestadoconsulta
    null_estado_count = Consulta.objects.filter(idestadoconsulta__isnull=True).count()
    if null_estado_count > 0:
        issues.append(f"⚠️  {null_estado_count} consultas have NULL idestadoconsulta")
    
    # Check for consultas with plan_tratamiento but no proper estado
    consultas_with_plan = Consulta.objects.filter(plan_tratamiento__isnull=False).count()
    if consultas_with_plan > 0:
        print(f"ℹ️  {consultas_with_plan} consultas already have linked plan_tratamiento")
    
    if issues:
        print("Issues found:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("✓ No conflicts detected - safe to proceed with migration")
    
    print()

def main():
    """Run all analyses"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  DATABASE STRUCTURE ANALYSIS - Realistic Flow Migration".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        analyze_estadodeconsulta_table()
        analyze_consulta_table()
        analyze_consulta_fields()
        check_database_schema()
        analyze_empresas()
        mapping_recommendations()
        check_for_conflicts()
        
        print_section("ANALYSIS COMPLETE")
        print("✓ Database analysis completed successfully")
        print("✓ Review the output above before proceeding with migrations")
        print("✓ Next step: Create migration files based on this analysis\n")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
