#!/bin/bash

# Script de inicio para Railway
echo "🚀 Iniciando CiviData en Railway..."

# Esperar a que la base de datos esté disponible
echo "📦 Esperando conexión a PostgreSQL..."
python -c "
import os
import time
import psycopg2
from psycopg2 import OperationalError

max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(
            dbname=os.environ.get('PGDATABASE'),
            user=os.environ.get('PGUSER'),
            password=os.environ.get('PGPASSWORD'),
            host=os.environ.get('PGHOST'),
            port=os.environ.get('PGPORT', '5432')
        )
        conn.close()
        print('✅ Conexión a PostgreSQL exitosa')
        break
    except OperationalError:
        retry_count += 1
        print(f'⏳ Reintento {retry_count}/{max_retries}...')
        time.sleep(2)
else:
    print('❌ No se pudo conectar a PostgreSQL')
    exit(1)
"

# Ejecutar migraciones y configuración
echo "⚙️ Configurando aplicación..."
python manage.py deploy_setup

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Iniciar servidor
echo "🌟 Iniciando servidor CiviData..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 3 \
    --worker-class gthread \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout 30 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile -