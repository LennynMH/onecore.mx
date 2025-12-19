# Dockerfile para OneCore Frontend - Desarrollo
# Usa Node.js para desarrollo con hot reload

FROM node:18-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package.json package-lock.json* ./

# Instalar dependencias
RUN npm install

# Copiar código fuente
COPY . .

# Exponer puerto de Vite
EXPOSE 3000

# Comando para desarrollo (con hot reload)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

