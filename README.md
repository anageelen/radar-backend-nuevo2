# RADAR Backend

Backend API para RADAR - Meta-navegador inteligente para búsqueda y análisis web empresarial.

## 🚀 Características

- **FastAPI** con documentación automática
- **PostgreSQL** para persistencia de datos
- **Celery + Redis** para tareas en segundo plano
- **Búsqueda multi-fuente**: Google, Bing, NewsAPI
- **IA integrada**: OpenAI para interpretación de queries y generación de columnas
- **Autenticación simple** basada en email
- **Exportación** a Excel y PDF
- **Automatización** de búsquedas programadas

## 📋 Endpoints Implementados

### Autenticación
- `POST /auth/login` - Login simple con email

### Búsqueda
- `POST /ai-search` - Búsqueda con IA y filtros automáticos
- `GET /search` - Búsqueda estándar con parámetros
- `POST /refine` - Aplicar filtros dinámicos a resultados
- `PUT /items/{id}` - Actualizar campos de resultados

### Columnas Dinámicas
- `POST /columns` - Crear columnas personalizadas con datos generados por IA

### Automatización
- `POST /jobs` - Programar búsquedas automáticas

### Exportación
- `GET /export` - Exportar resultados a Excel/PDF

### Utilidad
- `GET /healthz` - Health check

## 🛠️ Configuración

### 1. Variables de Entorno (Railway)

Configura estas variables en tu proyecto de Railway:

```bash
# Base de datos (Railway PostgreSQL)
DATABASE_URL=postgresql://postgres:password@host:port/database

# APIs externas (REQUERIDAS)
GOOGLE_API_KEY=tu_google_custom_search_api_key
GOOGLE_CX=tu_google_custom_search_engine_id
BING_API_KEY=tu_bing_search_v7_api_key
NEWSAPI_KEY=tu_newsapi_org_api_key
OPENAI_API_KEY=tu_openai_api_key

# Redis para Celery
REDIS_URL=redis://localhost:6379/0

# Configuración de aplicación
SECRET_KEY=tu_clave_secreta_para_jwt
DEBUG=False
ENVIRONMENT=production
FRONTEND_URL=https://tu-frontend.vercel.app
```

### 2. APIs Externas Necesarias

#### Google Custom Search API
1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Habilita "Custom Search API"
3. Crea credenciales (API Key)
4. Configura un Custom Search Engine en [cse.google.com](https://cse.google.com/)

#### Bing Search API
1. Ve a [Azure Portal](https://portal.azure.com/)
2. Crea un recurso "Bing Search v7"
3. Obtén la API Key

#### NewsAPI
1. Regístrate en [newsapi.org](https://newsapi.org/)
2. Obtén tu API Key gratuita

#### OpenAI API
1. Ve a [platform.openai.com](https://platform.openai.com/)
2. Crea una API Key
3. Asegúrate de tener créditos disponibles

### 3. Base de Datos

El backend usa PostgreSQL. Las tablas se crean automáticamente al iniciar:

- `users` - Usuarios del sistema
- `searches` - Búsquedas realizadas
- `results` - Resultados de búsquedas
- `columns` - Columnas personalizadas
- `column_values` - Valores de columnas personalizadas
- `automations` - Automatizaciones programadas

### 4. Redis (para Celery)

Para tareas en segundo plano como automatizaciones:

```bash
# Local development
redis-server

# Production (Railway)
# Añade Redis como servicio en Railway
```

## 🚀 Despliegue en Railway

### 1. Conectar Repositorio
1. Ve a [railway.app](https://railway.app/)
2. Conecta tu repositorio GitHub
3. Selecciona el directorio `radar-backend`

### 2. Configurar PostgreSQL
1. Añade PostgreSQL como servicio
2. Copia la `DATABASE_URL` a las variables de entorno

### 3. Configurar Redis
1. Añade Redis como servicio
2. Copia la `REDIS_URL` a las variables de entorno

### 4. Variables de Entorno
Configura todas las variables listadas arriba en Railway.

### 5. Deploy
Railway desplegará automáticamente. El backend estará disponible en:
`https://tu-proyecto.railway.app`

## 🔧 Desarrollo Local

```bash
# Instalar dependencias
poetry install

# Configurar variables de entorno
cp .env.example .env
# Edita .env con tus claves

# Iniciar servidor de desarrollo
poetry run fastapi dev app/main.py

# Iniciar Celery worker (en otra terminal)
poetry run celery -A app.celery_app worker --loglevel=info

# Iniciar Celery beat (para automatizaciones)
poetry run celery -A app.celery_app beat --loglevel=info
```

## 📚 Documentación API

Una vez desplegado, la documentación interactiva estará disponible en:
- Swagger UI: `https://tu-backend.railway.app/docs`
- ReDoc: `https://tu-backend.railway.app/redoc`

## 🔗 Conexión con Frontend

El frontend en Vercel debe configurar:

```bash
NEXT_PUBLIC_API_URL=https://tu-backend.railway.app
```

## 🧪 Testing

```bash
# Health check
curl https://tu-backend.railway.app/healthz

# Test search
curl -X POST https://tu-backend.railway.app/ai-search \
  -H "Content-Type: application/json" \
  -d '{"query": "startups en España", "create_filters": true}'
```

## 📝 Notas

- El sistema funciona con datos mock si no se configuran las APIs externas
- La autenticación es simple (solo email) para el MVP
- Las automatizaciones requieren Celery + Redis funcionando
- Los exports se generan en memoria (para producción, usar almacenamiento persistente)
