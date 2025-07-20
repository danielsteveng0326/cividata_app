# Usar Python 3.11 como imagen base
FROM python:3.11-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para PostgreSQL y weasyprint
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar dependencias de Python
COPY deploy/txt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar gunicorn para production
RUN pip install gunicorn psycopg2-binary

# Copiar el código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p staticfiles media logs

# Recopilar archivos estáticos
RUN python manage.py collectstatic --noinput

# Exponer el puerto
EXPOSE $PORT

# Comando para ejecutar la aplicación
CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3