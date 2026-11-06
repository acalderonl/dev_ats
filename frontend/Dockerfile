# Imagen de producción del frontend: compila con Vite y sirve los estáticos con nginx.
#
# Para desarrollo NO se usa esta imagen tal cual: docker-compose.yml sobreescribe el
# comando por `npm run dev` y monta el código, para tener recarga en caliente.
FROM node:20-alpine AS compilacion

WORKDIR /app

# `npm ci` y no `npm install`: instala exactamente lo del lock. Dos despliegues del
# mismo commit tienen que dar el mismo resultado.
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# Vite **incrusta** las variables VITE_* al compilar. Por eso aquí se deja una ruta
# RELATIVA: nginx hace de proxy hacia el backend (ver nginx.conf.template), así que la
# imagen no necesita saber en qué dominio vivirá la API y vale para cualquier entorno.
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build


FROM nginx:1.27-alpine

COPY --from=compilacion /app/dist /usr/share/nginx/html
# La imagen de nginx procesa las plantillas de esta carpeta al arrancar, sustituyendo
# las variables de entorno. Así el puerto lo decide el proveedor (Render y Railway
# inyectan PORT) sin reconstruir la imagen.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

# API_URL es la dirección interna del backend a la que nginx reenvía /api. En Render y
# Railway los servicios se ven entre sí por su nombre dentro de la red privada.
ENV PORT=8080 \
    API_URL=http://localhost:8000

EXPOSE 8080
