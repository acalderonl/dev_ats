# Imagen de desarrollo: Vite con hot-reload, montado como volumen desde docker-compose.yml
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
