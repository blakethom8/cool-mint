# Activity Selector Setup Guide

This guide explains how to set up and run the Activity Selector frontend with your existing Docker architecture and Kong API gateway.

## 🏗️ Architecture Overview

Your current setup uses:
- **Kong API Gateway** (port 8000) - Routes all traffic
- **FastAPI Backend** (port 8080) - Your activity API
- **Supabase Stack** - Database, auth, storage, etc.
- **React Frontend** (port 3000) - New activity selector UI

## 🚀 Quick Start

### 1. Start Your Existing Backend Services

```bash
# From the docker/ directory
cd docker
./start.sh
```

This starts:
- Kong API Gateway at `http://localhost:8000`
- FastAPI API at `http://localhost:8080` (internal)
- PostgreSQL database
- Redis
- Supabase services

### 2. Set Up the Frontend

```bash
# From the frontend/ directory
cd frontend
npm install
npm run dev
```

The frontend will start at `http://localhost:3000`

## 🔀 Routing Architecture

### Current Routing Flow

```
User Request → Kong (8000) → Backend Services
                ↓
            Kong Routes:
            /auth/v1/*    → GoTrue Auth
            /rest/v1/*    → PostgREST
            /storage/v1/* → Storage
            /functions/v1/* → Edge Functions
            /*            → Supabase Studio
```

### New Activity Selector Flow

```
Frontend (3000) → Kong (8000) → FastAPI (8080)
                                    ↓
                            /api/activities/*
```

## 🛠️ Integration Options

You have **3 options** for integrating the frontend:

### Option 1: Development Mode (Recommended for testing)
- Frontend runs on port 3000
- Uses Vite proxy to route `/api/*` requests to Kong (8000)
- **Pro**: Easy development, hot reloading
- **Con**: Two separate servers

### Option 2: Kong Integration (Recommended for production)
- Add frontend as a service in Kong
- All traffic goes through Kong
- **Pro**: Single entry point, consistent routing
- **Con**: More complex setup

### Option 3: Direct Backend Connection
- Frontend connects directly to FastAPI (8080)
- Bypasses Kong entirely
- **Pro**: Simple setup
- **Con**: Bypasses your API gateway

## 🔧 Detailed Setup Instructions

### Current Working Setup (Option 1)

Your frontend is already configured to work with Option 1:

1. **Start backend services**:
   ```bash
   cd docker && ./start.sh
   ```

2. **Start frontend**:
   ```bash
   cd frontend && npm run dev
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000 (through Kong)

### Frontend Configuration

The frontend `vite.config.ts` is configured to proxy API requests:

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8080',  // Direct to FastAPI
      changeOrigin: true,
    }
  }
}
```

### Adding Kong Route (Option 2)

To integrate with Kong, add this to `docker/volumes/api/kong.yml`:

```yaml
  ## Custom API routes
  - name: custom-api
    _comment: 'Custom API: /api/* -> http://api:8080/*'
    url: http://api:8080/
    routes:
      - name: custom-api-all
        strip_path: false
        paths:
          - /api/
    plugins:
      - name: cors
```

Then update frontend to use Kong:

```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',  // Through Kong
    changeOrigin: true,
  }
}
```

## 🌐 Network Configuration

Your services communicate on the Docker network: `${PROJECT_NAME}_network`

### Service Discovery
- **Kong**: `kong:8000` (internal), `localhost:8000` (external)
- **FastAPI**: `api:8080` (internal), `localhost:8080` (external)
- **Database**: `db:5432` (internal), `localhost:5433` (external)
- **Frontend**: `localhost:3000` (external only)

## 🔍 Testing the Setup

### 1. Verify Backend Services
```bash
# Check Kong is running
curl http://localhost:8000/health

# Check FastAPI directly
curl http://localhost:8080/api/activities/

# Check through Kong (if configured)
curl http://localhost:8000/api/activities/
```

### 2. Verify Frontend
```bash
# Open browser to
http://localhost:3000

# Check network tab for API calls to
http://localhost:3000/api/activities/
```

## 📝 Environment Variables

### Backend (.env in docker/)
```bash
PROJECT_NAME=launchpad
KONG_HTTP_PORT=8000
POSTGRES_HOST=db
POSTGRES_PORT=5432
# ... other vars
```

### Frontend (.env in frontend/)
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 🚨 Common Issues

### 1. CORS Issues
If you get CORS errors:
- Check Kong CORS plugin is enabled
- Verify frontend proxy configuration
- Ensure API responses include CORS headers

### 2. Network Connectivity
```bash
# Check Docker network
docker network ls | grep launchpad

# Check service connectivity
docker exec launchpad_api curl http://kong:8000/health
```

### 3. API Route Not Found
- Verify `/api/activities` route is registered in FastAPI
- Check Kong configuration includes your API routes
- Ensure database has activity data

## 📋 Next Steps

1. **Test the current setup** with Option 1
2. **Add Kong integration** (Option 2) for production
3. **Configure authentication** if needed
4. **Add the frontend to Docker** for full containerization

## 🐳 Dockerizing the Frontend (Future)

To fully integrate with your Docker setup:

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

Add to `docker-compose.launchpad.yml`:
```yaml
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: "${PROJECT_NAME}_frontend"
    ports:
      - "3000:3000"
    depends_on:
      - kong
```

This setup gives you a professional, scalable architecture that's ready for production deployment!