# Activity Table URL Guide

## Overview

This document explains how the activity table URL routing works in the Cool Mint system, including the proxy configuration and API endpoint structure.

## URL Structure

### Frontend Access
- **Development**: `http://localhost:3000`
- **Production**: `https://your-domain.com`

### API Requests
- **Frontend Route**: `/activities/*`
- **Backend Route**: `/api/activities/*`
- **Direct API**: `http://localhost:8080/api/activities/*`

## Request Flow

```
Frontend (localhost:3000) → Vite Proxy → Backend API (localhost:8080)
        /activities/*           →        /api/activities/*
```

## Vite Proxy Configuration

Located in `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/activities': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/activities/, '/api/activities')
      }
    }
  }
})
```

## API Endpoints

### Main Activity Endpoint
- **Frontend URL**: `GET /activities/`
- **Backend URL**: `GET /api/activities/`
- **Direct URL**: `http://localhost:8080/api/activities/`

### Filter Options
- **Frontend URL**: `GET /activities/filter-options`
- **Backend URL**: `GET /api/activities/filter-options`
- **Direct URL**: `http://localhost:8080/api/activities/filter-options`

### Selection Processing
- **Frontend URL**: `POST /activities/selection`
- **Backend URL**: `POST /api/activities/selection`
- **Direct URL**: `http://localhost:8080/api/activities/selection`

## Authentication Flow

### Development (Current)
1. User visits `http://localhost:3000`
2. Frontend makes request to `/activities/`
3. Vite proxy forwards to `http://localhost:8080/api/activities/`
4. Kong Gateway intercepts request (if enabled)
5. Basic authentication popup appears
6. After authentication, request reaches FastAPI backend

### Direct API Access (Bypassed Kong)
The system currently bypasses Kong Gateway and connects directly to FastAPI:
- No authentication popup
- Direct communication between frontend and backend
- CORS configured in FastAPI to allow `localhost:3000`

## CORS Configuration

In `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Example API Calls

### Get Activities with Filters
```javascript
// Frontend service call
const response = await axios.get('/activities/', {
  params: {
    page: 1,
    page_size: 50,
    search_text: 'meeting',
    start_date: '2024-01-01',
    owner_ids: ['user-123']
  }
});
```

### Process Selected Activities
```javascript
// Frontend service call
const response = await axios.post('/activities/selection', {
  activity_ids: ['activity-1', 'activity-2', 'activity-3']
});
```

## Direct API Testing

You can test the API directly using curl:

```bash
# Get activities
curl "http://localhost:8080/api/activities/?page=1&page_size=10"

# Get filter options
curl "http://localhost:8080/api/activities/filter-options"

# Process selection
curl -X POST "http://localhost:8080/api/activities/selection" \
  -H "Content-Type: application/json" \
  -d '{"activity_ids": ["activity-1", "activity-2"]}'
```

## Kong Gateway Configuration (When Enabled)

In `docker/volumes/api/kong.yml`:
```yaml
services:
- name: custom-activities-api
  url: http://api:8080/api/activities/
  routes:
  - name: activities-route
    paths:
    - /activities/
```

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check FastAPI CORS configuration
   - Verify allowed origins include `localhost:3000`

2. **404 Not Found**
   - Check Vite proxy configuration
   - Verify backend API is running on port 8080

3. **Authentication Popup**
   - Indicates Kong Gateway is enabled
   - Use Supabase credentials or disable Kong

4. **Connection Refused**
   - Backend API not running
   - Check Docker containers: `docker-compose ps`

### Debug Commands
```bash
# Check if backend is running
curl http://localhost:8080/docs

# Check frontend proxy
curl http://localhost:3000/activities/

# Check Docker services
docker-compose ps
```

## URL Patterns

### Development URLs
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080`
- Database: `localhost:5433`
- API Docs: `http://localhost:8080/docs`

### Production URLs
- Frontend: `https://your-domain.com`
- API: `https://your-domain.com/api/`
- Database: Internal network only

---

*This guide covers the URL routing structure for the activity table feature. For more detailed API documentation, see `BACKEND_API.md`.*