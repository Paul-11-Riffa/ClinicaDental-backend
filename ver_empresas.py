#!/usr/bin/env python
"""
Script para ver las empresas registradas y sus usuarios admin
"""
import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dental_clinic_backend.settings')

django.setup()

from api.models import Empresa, Usuario

print("="*70)
print("📊 EMPRESAS REGISTRADAS EN EL SISTEMA")
print("="*70)

empresas = Empresa.objects.all().order_by('-id')

if not empresas.exists():
    print("\n❌ No hay empresas registradas")
else:
    for empresa in empresas:
        print(f"\n🏢 EMPRESA #{empresa.id}")
        print(f"   Nombre: {empresa.nombre}")
        print(f"   Subdomain: {empresa.subdomain}")
        print(f"   Activa: {'✅ Sí' if empresa.activo else '❌ No'}")
        print(f"   Stripe Customer: {empresa.stripe_customer_id or 'N/A'}")
        print(f"   Stripe Subscription: {empresa.stripe_subscription_id or 'N/A'}")
        
        # Buscar usuarios admin de esta empresa
        print(f"\n   👥 USUARIOS:")
        usuarios = Usuario.objects.filter(empresa=empresa).order_by('codigo')
        
        if not usuarios.exists():
            print("      ⚠️  No hay usuarios registrados")
        else:
            for usuario in usuarios:
                rol = usuario.idtipousuario.rol if usuario.idtipousuario else 'Sin rol'
                print(f"\n      👤 Usuario #{usuario.codigo}")
                print(f"         Nombre: {usuario.nombre} {usuario.apellido}")
                print(f"         Email: {usuario.correoelectronico}")
                print(f"         Rol: {rol}")
                print(f"         Teléfono: {usuario.telefono or 'N/A'}")
                
                # Intentar obtener el user de Django para ver si tiene password
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    django_user = User.objects.get(username=usuario.correoelectronico)
                    print(f"         Django User: ✅ Existe")
                    print(f"         Password: {'✅ Configurado' if django_user.password else '❌ Sin password'}")
                    print(f"         Staff: {'✅ Sí' if django_user.is_staff else '❌ No'}")
                    print(f"         Active: {'✅ Sí' if django_user.is_active else '❌ No'}")
                except User.DoesNotExist:
                    print(f"         Django User: ❌ No existe")
        
        print(f"\n   🌐 URL DE ACCESO:")
        print(f"      • Producción: https://{empresa.subdomain}.notificct.dpdns.org/login")
        print(f"      • Local: http://{empresa.subdomain}.localhost:5173/login")
        print(f"      • Header: X-Tenant-Subdomain: {empresa.subdomain}")
        print("\n" + "─"*70)

print("\n" + "="*70)
print(f"📈 Total de empresas: {empresas.count()}")
print("="*70)

# Información adicional para acceso local
print("\n💡 CÓMO ACCEDER EN DESARROLLO:")
print("─"*70)
print("1. Frontend debe enviar el header: X-Tenant-Subdomain: smilestudio")
print("2. O configurar wildcard DNS: *.localhost apunta a 127.0.0.1")
print("3. O usar Chrome con extensión ModHeader para agregar el header")
print("─"*70)

print("\n⚠️  NOTA SOBRE PASSWORDS:")
print("Los passwords temporales se generan al registrar pero NO se guardan")
print("en texto plano. Solo se muestra una vez en la respuesta del registro.")
print("Si no lo guardaste, puedes:")
print("  1. Usar 'Olvidé mi contraseña' en el login")
print("  2. O resetear desde Django admin")
print("  3. O crear un nuevo usuario desde el script de gestión")
print("="*70)
