# Imagen del backend. Sirve para desarrollo y para producción: lo que cambia es el
# comando, que viene de fuera (docker-compose monta el código y añade --reload).
#
# Dos etapas para que la imagen final no cargue con el compilador. `build-essential` y
# `libpq-dev` hacen falta para compilar las ruedas de psycopg2 y cryptography, pero una
# vez instaladas son peso muerto —y superficie de ataque— en un servidor.
FROM python:3.12-slim AS dependencias

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/instalado -r requirements.txt


FROM python:3.12-slim

# libpq5 es la biblioteca en tiempo de ejecución; libpq-dev (las cabeceras) solo hacía
# falta para compilar. curl queda para el healthcheck del proveedor.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=dependencias /instalado /usr/local

WORKDIR /app
COPY . .

# Sin esto el proceso corre como root: si alguien consigue ejecutar algo dentro del
# contenedor, lo hace con todos los permisos. La carpeta de medios se crea aquí porque
# el usuario sin privilegios no podría crearla después en la raíz.
RUN useradd --create-home --uid 1000 ats \
    && mkdir -p /app/media \
    && chown -R ats:ats /app
USER ats

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Las migraciones se aplican al arrancar: en un despliegue continuo, cada versión nueva
# pone la base al día sola. Sin `--reload`: eso vigila el disco y es para desarrollo.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
