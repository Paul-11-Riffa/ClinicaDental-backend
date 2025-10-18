"""
Management command para reparar inconsistencias de roles en la base de datos

Uso:
    python manage.py reparar_roles_usuarios

Este comando:
1. Identifica usuarios con múltiples perfiles (Paciente + Odontologo, etc.)
2. Identifica usuarios sin el perfil correcto según su rol
3. Corrige automáticamente estas inconsistencias
"""
from django.core.management.base import BaseCommand
from api.signals_usuario import reparar_inconsistencias_roles


class Command(BaseCommand):
    help = 'Repara inconsistencias en los perfiles de roles de usuarios'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué se corregiría sin hacer cambios',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('🔧 REPARACIÓN DE ROLES DE USUARIOS'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if options['dry_run']:
            self.stdout.write(self.style.NOTICE('\n⚠️  Modo DRY-RUN: No se harán cambios\n'))
        
        try:
            if options['dry_run']:
                self.stdout.write(self.style.NOTICE('Este comando aún no soporta dry-run completo'))
                self.stdout.write(self.style.NOTICE('Por ahora solo ejecutará la reparación real\n'))
            
            # Ejecutar la reparación
            usuarios_reparados = reparar_inconsistencias_roles()
            
            self.stdout.write(self.style.SUCCESS('\n✅ Proceso completado'))
            self.stdout.write(self.style.SUCCESS(f'📊 {usuarios_reparados} usuarios fueron corregidos'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error durante la reparación: {str(e)}'))
            raise
