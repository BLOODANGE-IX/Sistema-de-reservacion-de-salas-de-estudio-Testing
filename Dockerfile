
FROM debian:bookworm-slim

# Instalar dependencias del sistema para Django y MariaDB
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    libmariadb-dev \
    pkg-config \
    gcc \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Configurar zona horaria
ENV TZ=America/Mexico_City
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias
COPY ./requirements.txt /app/

# Crear entorno virtual
RUN python3 -m venv /env

ENV PATH="/env/bin:$PATH"

# Instalar dependencias
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Puerto de Django
EXPOSE 8000

# Iniciar servidor de desarrollo
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]