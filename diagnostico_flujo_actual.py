"""
Script de Diagnóstico del Flujo Clínico Actual
==============================================

Este script analiza el estado actual de la base de datos y el código
para entender exactamente qué está implementado y qué falta.

Ejecutar: python diagnostico_flujo_actual.py
"""

import os
import django
import sys
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')
django.setup()

from django.db import connection
from api.models import (
    Paciente, Odontologo, Consulta, Tipodeconsulta, Estadodeconsulta,
    Plandetratamiento, Itemplandetratamiento, Estado, Servicio,
    PagoEnLinea, PresupuestoDigital, Empresa
)


class FlujoDiagnostico:
    """Diagnóstico completo del flujo clínico"""
    
    def __init__(self):
        self.resultados = {
            'estructura_bd': {},
            'datos_existentes': {},
            'relaciones': {},
            'problemas': [],
            'recomendaciones': []
        }
    
    def ejecutar_diagnostico_completo(self):
        """Ejecuta todos los diagnósticos"""
        print("\n" + "="*70)
        print("🔍 DIAGNÓSTICO DEL FLUJO CLÍNICO ACTUAL")
        print("="*70 + "\n")
        
        self.verificar_estructura_bd()
        self.verificar_datos_existentes()
        self.verificar_relaciones()
        self.analizar_flujo_actual()
        self.generar_reporte()
        
        return self.resultados
    
    def verificar_estructura_bd(self):
        """Verifica la estructura de la base de datos"""
        print("📊 1. VERIFICANDO ESTRUCTURA DE BASE DE DATOS\n")
        
        tablas_core = {
            'consulta': self._get_table_structure('consulta'),
            'plandetratamiento': self._get_table_structure('plandetratamiento'),
            'itemplandetratamiento': self._get_table_structure('itemplandetratamiento'),
            'pago_en_linea': self._get_table_structure('pago_en_linea'),
            'presupuesto_digital': self._get_table_structure('presupuesto_digital'),
        }
        
        self.resultados['estructura_bd'] = tablas_core
        
        # Verificar campos críticos
        print("   Tabla 'consulta':")
        campos_consulta = [col['name'] for col in tablas_core['consulta']]
        self._check_campo('consulta', 'plan_tratamiento_id', campos_consulta)
        self._check_campo('consulta', 'costo_consulta', campos_consulta)
        self._check_campo('consulta', 'requiere_pago', campos_consulta)
        
        print("\n   Tabla 'plandetratamiento':")
        campos_plan = [col['name'] for col in tablas_core['plandetratamiento']]
        self._check_campo('plandetratamiento', 'consulta_diagnostico_id', campos_plan)
        self._check_campo('plandetratamiento', 'estado_tratamiento', campos_plan)
        self._check_campo('plandetratamiento', 'fecha_aceptacion', campos_plan)
        
        print("\n   Tabla 'itemplandetratamiento':")
        campos_item = [col['name'] for col in tablas_core['itemplandetratamiento']]
        self._check_campo('itemplandetratamiento', 'consulta_ejecucion_id', campos_item)
        self._check_campo('itemplandetratamiento', 'estado_item', campos_item)
        self._check_campo('itemplandetratamiento', 'fecha_ejecucion', campos_item)
        
        print("\n")
    
    def verificar_datos_existentes(self):
        """Verifica qué datos existen actualmente"""
        print("📈 2. VERIFICANDO DATOS EXISTENTES\n")
        
        try:
            # Contar registros
            count_pacientes = Paciente.objects.count()
            count_odontologos = Odontologo.objects.count()
            count_consultas = Consulta.objects.count()
            count_planes = Plandetratamiento.objects.count()
            count_items = Itemplandetratamiento.objects.count()
            count_pagos = PagoEnLinea.objects.count()
            count_presupuestos = PresupuestoDigital.objects.count()
            
            print(f"   ✓ Pacientes: {count_pacientes}")
            print(f"   ✓ Odontólogos: {count_odontologos}")
            print(f"   ✓ Consultas: {count_consultas}")
            print(f"   ✓ Planes de Tratamiento: {count_planes}")
            print(f"   ✓ Items de Planes: {count_items}")
            print(f"   ✓ Pagos en Línea: {count_pagos}")
            print(f"   ✓ Presupuestos Digitales: {count_presupuestos}")
            
            self.resultados['datos_existentes'] = {
                'pacientes': count_pacientes,
                'odontologos': count_odontologos,
                'consultas': count_consultas,
                'planes': count_planes,
                'items': count_items,
                'pagos': count_pagos,
                'presupuestos': count_presupuestos,
            }
            
            # Verificar tipos de consulta
            print("\n   Tipos de Consulta existentes:")
            tipos_consulta = Tipodeconsulta.objects.all()[:10]
            for tipo in tipos_consulta:
                print(f"      - {tipo.nombreconsulta}")
            
            # Verificar estados
            print("\n   Estados existentes:")
            estados = Estado.objects.all()[:10]
            for estado in estados:
                print(f"      - {estado.estado}")
            
            print("\n")
            
        except Exception as e:
            print(f"   ❌ Error al verificar datos: {e}\n")
            self.resultados['problemas'].append(f"Error verificando datos: {e}")
    
    def verificar_relaciones(self):
        """Verifica las relaciones entre modelos"""
        print("🔗 3. VERIFICANDO RELACIONES ENTRE MODELOS\n")
        
        try:
            # Verificar si hay planes vinculados a consultas
            planes_con_consulta = Plandetratamiento.objects.filter(
                consentimientos__consulta__isnull=False
            ).count()
            print(f"   Planes vinculados a consultas (via consentimiento): {planes_con_consulta}")
            
            # Verificar pagos de planes
            pagos_plan = PagoEnLinea.objects.filter(
                plan_tratamiento__isnull=False
            ).count()
            print(f"   Pagos vinculados a planes: {pagos_plan}")
            
            # Verificar pagos de consultas
            pagos_consulta = PagoEnLinea.objects.filter(
                consulta__isnull=False
            ).count()
            print(f"   Pagos vinculados a consultas: {pagos_consulta}")
            
            # Verificar presupuestos de planes
            presupuestos_plan = PresupuestoDigital.objects.filter(
                plan_tratamiento__isnull=False
            ).count()
            print(f"   Presupuestos vinculados a planes: {presupuestos_plan}")
            
            self.resultados['relaciones'] = {
                'planes_con_consulta': planes_con_consulta,
                'pagos_plan': pagos_plan,
                'pagos_consulta': pagos_consulta,
                'presupuestos_plan': presupuestos_plan,
            }
            
            print("\n")
            
        except Exception as e:
            print(f"   ❌ Error al verificar relaciones: {e}\n")
            self.resultados['problemas'].append(f"Error verificando relaciones: {e}")
    
    def analizar_flujo_actual(self):
        """Analiza el flujo actual y detecta problemas"""
        print("🔍 4. ANALIZANDO FLUJO CLÍNICO ACTUAL\n")
        
        problemas = []
        recomendaciones = []
        
        # Problema 1: Falta vinculación consulta → plan
        if 'consulta_diagnostico_id' not in str(self.resultados.get('estructura_bd', {}).get('plandetratamiento', [])):
            problemas.append("❌ CRÍTICO: Plandetratamiento NO tiene campo 'consulta_diagnostico_id'")
            recomendaciones.append("Agregar FK: Plandetratamiento.consulta_diagnostico → Consulta")
        
        # Problema 2: Falta estados específicos en items
        if 'estado_item' not in str(self.resultados.get('estructura_bd', {}).get('itemplandetratamiento', [])):
            problemas.append("❌ CRÍTICO: Itemplandetratamiento NO tiene campo 'estado_item'")
            recomendaciones.append("Agregar campo estado_item con choices: Pendiente, Pagado, Completado, etc.")
        
        # Problema 3: Falta vinculación item → consulta ejecución
        if 'consulta_ejecucion_id' not in str(self.resultados.get('estructura_bd', {}).get('itemplandetratamiento', [])):
            problemas.append("❌ CRÍTICO: Itemplandetratamiento NO tiene campo 'consulta_ejecucion_id'")
            recomendaciones.append("Agregar FK: Itemplandetratamiento.consulta_ejecucion → Consulta")
        
        # Problema 4: Falta control de pagos en consultas
        if 'costo_consulta' not in str(self.resultados.get('estructura_bd', {}).get('consulta', [])):
            problemas.append("⚠️  Consulta NO tiene campo 'costo_consulta'")
            recomendaciones.append("Agregar campos: costo_consulta, requiere_pago, pago_consulta_id")
        
        # Problema 5: Estados genéricos
        problemas.append("⚠️  Se usan Estados genéricos en lugar de estados específicos por modelo")
        recomendaciones.append("Migrar de FK(Estado) a CharField con choices específicos")
        
        self.resultados['problemas'] = problemas
        self.resultados['recomendaciones'] = recomendaciones
        
        for problema in problemas:
            print(f"   {problema}")
        
        print("\n")
    
    def generar_reporte(self):
        """Genera reporte final"""
        print("="*70)
        print("📋 RESUMEN DEL DIAGNÓSTICO")
        print("="*70 + "\n")
        
        print(f"✅ Datos Existentes:")
        for key, value in self.resultados['datos_existentes'].items():
            print(f"   - {key.capitalize()}: {value}")
        
        print(f"\n⚠️  Problemas Detectados: {len(self.resultados['problemas'])}")
        for i, problema in enumerate(self.resultados['problemas'], 1):
            print(f"   {i}. {problema}")
        
        print(f"\n💡 Recomendaciones: {len(self.resultados['recomendaciones'])}")
        for i, rec in enumerate(self.resultados['recomendaciones'], 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "="*70)
        print("✅ DIAGNÓSTICO COMPLETADO")
        print("="*70 + "\n")
    
    # Métodos auxiliares
    def _get_table_structure(self, table_name):
        """Obtiene la estructura de una tabla"""
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT 
                    column_name as name,
                    data_type as type,
                    is_nullable as nullable,
                    column_default as default_value
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            return [
                {
                    'name': col[0],
                    'type': col[1],
                    'nullable': col[2],
                    'default': col[3]
                }
                for col in columns
            ]
    
    def _check_campo(self, tabla, campo, lista_campos):
        """Verifica si un campo existe"""
        if campo in lista_campos:
            print(f"      ✅ {campo}: Existe")
        else:
            print(f"      ❌ {campo}: NO existe")
            self.resultados['problemas'].append(f"Falta campo '{campo}' en tabla '{tabla}'")


def main():
    """Función principal"""
    try:
        diagnostico = FlujoDiagnostico()
        resultados = diagnostico.ejecutar_diagnostico_completo()
        
        # Guardar resultados en JSON (opcional)
        import json
        with open('diagnostico_resultados.json', 'w', encoding='utf-8') as f:
            # Convertir estructura_bd a formato serializable
            resultados_serializables = {
                'datos_existentes': resultados['datos_existentes'],
                'relaciones': resultados['relaciones'],
                'problemas': resultados['problemas'],
                'recomendaciones': resultados['recomendaciones'],
            }
            json.dump(resultados_serializables, f, indent=2, ensure_ascii=False)
        
        print("\n💾 Resultados guardados en: diagnostico_resultados.json\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
