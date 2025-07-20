# core/rrhh/management/commands/deploy_setup.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Configuración inicial para deployment'

    def handle(self, *args, **options):
        """
        Comando para ejecutar en Railway después del deployment
        """
        self.stdout.write('🚀 Iniciando configuración de deployment...')
        
        try:
            # Ejecutar migraciones
            self.stdout.write('📦 Aplicando migraciones...')
            call_command('migrate', verbosity=0)
            
            # Crear superusuario si no existe
            self.stdout.write('👤 Configurando usuario administrador...')
            from core.user.models import User
            from django.contrib.auth.models import Group
            
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    username='admin',
                    email='admin@cividata.com',
                    password='CiviData2025!',
                    names='Administrador CiviData'
                )
                self.stdout.write('✅ Superusuario creado: admin / CiviData2025!')
            
            # Ejecutar configuración inicial
            self.stdout.write('⚙️ Ejecutando configuración inicial...')
            call_command('start_installation', verbosity=0)
            
            # Insertar datos de prueba si es desarrollo
            import os
            if os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.settings_production':
                self.stdout.write('📊 Insertando datos de prueba...')
                call_command('insert_test_data', verbosity=0)
            
            self.stdout.write(
                self.style.SUCCESS('🎉 ¡Deployment configurado exitosamente!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en la configuración: {str(e)}')
            )