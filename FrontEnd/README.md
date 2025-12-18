# OneCore Frontend - Módulo de Análisis de Documentos

Frontend React para el módulo de análisis de documentos con IA, integrado con FastAPI backend.

## 🚀 Características

- ✅ **Autenticación JWT** - Login con roles (admin, gestor)
- ✅ **Carga de Documentos** - Drag & drop para PDF, JPG, PNG
- ✅ **Clasificación Automática** - Identifica Facturas e Información
- ✅ **Extracción de Datos** - Muestra datos extraídos según tipo
- ✅ **Historial** - Lista de documentos procesados con filtros
- ✅ **Diseño Responsive** - Funciona en móvil y desktop

## 📋 Requisitos

- Node.js 18+ y npm
- Backend FastAPI corriendo en `http://localhost:8000`

## 🔧 Instalación

1. **Instalar dependencias:**
```bash
cd FrontEnd
npm install
```

2. **Configurar variables de entorno:**
```bash
cp .env.example .env
```

Editar `.env` si el backend está en otra URL:
```
VITE_API_URL=http://localhost:8000
```

3. **Iniciar servidor de desarrollo:**
```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:3000`

## 📁 Estructura del Proyecto

```
FrontEnd/
├── src/
│   ├── components/          # Componentes reutilizables
│   │   ├── Layout.tsx       # Layout principal con navegación
│   │   └── ProtectedRoute.tsx  # Ruta protegida
│   ├── pages/               # Páginas de la aplicación
│   │   ├── Login.tsx        # Página de login
│   │   ├── DocumentUpload.tsx  # Carga de documentos
│   │   ├── DocumentResults.tsx  # Resultados del análisis
│   │   └── DocumentHistory.tsx  # Historial de documentos
│   ├── services/            # Servicios
│   │   └── api.ts           # Cliente API para FastAPI
│   ├── App.tsx              # Componente principal
│   └── main.tsx             # Punto de entrada
├── package.json
├── vite.config.ts           # Configuración de Vite
└── tsconfig.json            # Configuración TypeScript
```

## 🔌 Integración con Backend

El frontend se comunica con el backend FastAPI a través de los siguientes endpoints:

### Autenticación
- `POST /api/v1/auth/login` - Iniciar sesión
- `POST /api/v1/auth/renew` - Renovar token

### Documentos
- `POST /api/v1/documents/upload` - Subir documento
- `GET /api/v1/documents/{id}` - Obtener documento
- `GET /api/v1/documents` - Listar documentos

## 🎨 Tecnologías Utilizadas

- **React 18** - Biblioteca UI
- **TypeScript** - Tipado estático
- **Vite** - Build tool y dev server
- **React Router** - Navegación
- **Axios** - Cliente HTTP
- **React Dropzone** - Drag & drop de archivos
- **React Toastify** - Notificaciones
- **date-fns** - Manejo de fechas

## 📝 Scripts Disponibles

- `npm run dev` - Iniciar servidor de desarrollo
- `npm run build` - Construir para producción
- `npm run preview` - Previsualizar build de producción

## 🔐 Autenticación

El frontend usa JWT tokens almacenados en `localStorage`. El token se envía automáticamente en todas las peticiones al backend.

## 📱 Responsive Design

La aplicación está diseñada para funcionar en:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

## 🚀 Despliegue

Para producción:

1. **Construir la aplicación:**
```bash
npm run build
```

2. **Los archivos estarán en `dist/`**

3. **Servir con cualquier servidor web estático:**
   - Nginx
   - Apache
   - Vercel
   - Netlify
   - etc.

## 📄 Licencia

Proyecto interno de OneCore

