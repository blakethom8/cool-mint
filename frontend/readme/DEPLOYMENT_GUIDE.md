# Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Cool Mint sales activity selector system in various environments, from local development to production deployment.

## Prerequisites

### System Requirements
- Docker 20.10+ and Docker Compose 2.0+
- Node.js 18+ and npm 8+
- PostgreSQL 15+ (for non-Docker deployments)
- Redis 6+ (for caching and background tasks)
- Git for version control

### Environment Setup
- Minimum 4GB RAM for development
- 8GB+ RAM recommended for production
- 10GB+ disk space for Docker images and data
- SSL certificates for production HTTPS

## Development Deployment

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd cool-mint
   ```

2. **Environment Configuration**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit environment variables
   nano .env
   ```

3. **Required Environment Variables**
   ```bash
   # Project Configuration
   PROJECT_NAME=cool-mint
   
   # Database Configuration
   POSTGRES_HOST=db
   POSTGRES_DB=postgres
   POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password
   POSTGRES_PORT=5432
   
   # API Keys (optional for basic functionality)
   OPENAI_API_KEY=your-openai-key
   ANTHROPIC_API_KEY=your-anthropic-key
   
   # JWT Configuration
   JWT_SECRET=your-jwt-secret-key
   JWT_EXPIRY=3600
   ```

4. **Start Backend Services**
   ```bash
   cd docker
   docker-compose up -d
   
   # Verify services are running
   docker-compose ps
   ```

5. **Database Migration**
   ```bash
   # Run database migrations
   docker exec cool-mint_api alembic upgrade head
   
   # Optional: Seed test data
   docker exec cool-mint_api python seed_data/seed_expanded.py
   ```

6. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

7. **Verify Installation**
   - Backend API: http://localhost:8080/docs
   - Frontend: http://localhost:3000
   - Database: localhost:5433

### Development Workflow

**Starting Services**:
```bash
# Start all services
./start-activity-selector.sh

# Or manually
cd docker && docker-compose up -d
cd frontend && npm run dev
```

**Stopping Services**:
```bash
cd docker
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

**Monitoring Logs**:
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f db
```

## Production Deployment

### Infrastructure Requirements

**Minimum Production Specs**:
- 2 CPU cores, 8GB RAM
- 50GB SSD storage
- Load balancer (Nginx/HAProxy)
- SSL certificate
- Monitoring solution

**Recommended Production Specs**:
- 4+ CPU cores, 16GB+ RAM
- 100GB+ SSD storage
- CDN for static assets
- Database clustering
- Backup and monitoring

### Production Environment Variables

```bash
# Production-specific variables
ENV=production
DEBUG=false
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database (use managed service)
DATABASE_URL=postgresql://user:password@host:5432/database
REDIS_URL=redis://redis-host:6379/0

# Security
SECRET_KEY=your-production-secret-key
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Monitoring
SENTRY_DSN=your-sentry-dsn
OTEL_EXPORTER_OTLP_ENDPOINT=your-otel-endpoint
```

### Docker Production Deployment

1. **Production Docker Compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'
   services:
     api:
       build:
         context: .
         dockerfile: docker/Dockerfile.api
       restart: unless-stopped
       environment:
         - ENV=production
         - DEBUG=false
       depends_on:
         - db
         - redis
       
     nginx:
       image: nginx:alpine
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf
         - ./ssl:/etc/nginx/ssl
       depends_on:
         - api
   ```

2. **Build Production Images**
   ```bash
   # Build API image
   docker build -f docker/Dockerfile.api -t cool-mint-api:prod .
   
   # Build frontend (static files)
   cd frontend
   npm run build
   ```

3. **Deploy Production Stack**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Kubernetes Deployment

1. **Create Kubernetes Manifests**
   ```yaml
   # api-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: cool-mint-api
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: cool-mint-api
     template:
       metadata:
         labels:
           app: cool-mint-api
       spec:
         containers:
         - name: api
           image: cool-mint-api:prod
           ports:
           - containerPort: 8080
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: db-secret
                 key: url
   ```

2. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s/
   kubectl get pods
   kubectl get services
   ```

### Cloud Platform Deployment

#### AWS Deployment

1. **ECS Fargate Setup**
   ```bash
   # Create ECS cluster
   aws ecs create-cluster --cluster-name cool-mint-cluster
   
   # Create task definition
   aws ecs register-task-definition --cli-input-json file://task-definition.json
   
   # Create service
   aws ecs create-service --cluster cool-mint-cluster --service-name cool-mint-api --task-definition cool-mint-api:1 --desired-count 2
   ```

2. **RDS Database Setup**
   ```bash
   # Create RDS PostgreSQL instance
   aws rds create-db-instance \
     --db-instance-identifier cool-mint-db \
     --db-instance-class db.t3.medium \
     --engine postgres \
     --master-username admin \
     --master-user-password your-password \
     --allocated-storage 100
   ```

#### Google Cloud Platform

1. **Cloud Run Deployment**
   ```bash
   # Build and push to Container Registry
   gcloud builds submit --tag gcr.io/PROJECT-ID/cool-mint-api
   
   # Deploy to Cloud Run
   gcloud run deploy cool-mint-api \
     --image gcr.io/PROJECT-ID/cool-mint-api \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

2. **Cloud SQL Setup**
   ```bash
   # Create Cloud SQL instance
   gcloud sql instances create cool-mint-db \
     --database-version POSTGRES_15 \
     --tier db-f1-micro \
     --region us-central1
   ```

#### Azure Deployment

1. **Container Instances Setup**
   ```bash
   # Create resource group
   az group create --name cool-mint-rg --location eastus
   
   # Deploy container
   az container create \
     --resource-group cool-mint-rg \
     --name cool-mint-api \
     --image cool-mint-api:prod \
     --ports 8080 \
     --environment-variables DATABASE_URL=your-db-url
   ```

## Frontend Deployment

### Static Site Deployment

1. **Build Production Assets**
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to CDN**
   ```bash
   # AWS S3 + CloudFront
   aws s3 sync dist/ s3://your-bucket-name
   aws cloudfront create-invalidation --distribution-id YOUR-DISTRIBUTION-ID --paths "/*"
   
   # Vercel
   vercel --prod
   
   # Netlify
   netlify deploy --prod --dir=dist
   ```

### Server-Side Rendering (Future)

1. **Next.js Setup**
   ```bash
   # Convert to Next.js
   npx create-next-app@latest --typescript
   
   # Deploy to Vercel
   vercel --prod
   ```

## Database Deployment

### Production Database Setup

1. **PostgreSQL Configuration**
   ```sql
   -- Create database and user
   CREATE DATABASE cool_mint_prod;
   CREATE USER cool_mint_user WITH ENCRYPTED PASSWORD 'secure-password';
   GRANT ALL PRIVILEGES ON DATABASE cool_mint_prod TO cool_mint_user;
   
   -- Configure connection limits
   ALTER USER cool_mint_user CONNECTION LIMIT 100;
   ```

2. **Database Optimization**
   ```sql
   -- Performance tuning
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ALTER SYSTEM SET work_mem = '4MB';
   ALTER SYSTEM SET maintenance_work_mem = '64MB';
   
   -- Create indexes
   CREATE INDEX idx_activity_date ON sf_activity_structured(activity_date);
   CREATE INDEX idx_user_id ON sf_activity_structured(user_id);
   CREATE INDEX idx_subject_search ON sf_activity_structured USING gin(to_tsvector('english', subject));
   ```

### Database Migration

1. **Backup Current Database**
   ```bash
   pg_dump -h localhost -U postgres -d cool_mint > backup.sql
   ```

2. **Run Migrations**
   ```bash
   # Update to latest schema
   alembic upgrade head
   
   # Verify migration
   alembic current
   alembic history
   ```

3. **Data Migration**
   ```bash
   # Run data migration scripts
   python scripts/migrate_data.py
   ```

## SSL/TLS Configuration

### Nginx SSL Setup

1. **Obtain SSL Certificate**
   ```bash
   # Let's Encrypt with Certbot
   sudo certbot --nginx -d your-domain.com
   
   # Or use existing certificates
   sudo mkdir -p /etc/nginx/ssl
   sudo cp your-cert.pem /etc/nginx/ssl/
   sudo cp your-key.pem /etc/nginx/ssl/
   ```

2. **Nginx Configuration**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name your-domain.com;
       
       ssl_certificate /etc/nginx/ssl/your-cert.pem;
       ssl_certificate_key /etc/nginx/ssl/your-key.pem;
       
       location / {
           proxy_pass http://localhost:3000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /api/ {
           proxy_pass http://localhost:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

## Monitoring and Logging

### Application Monitoring

1. **Prometheus Setup**
   ```yaml
   # prometheus.yml
   global:
     scrape_interval: 15s
   
   scrape_configs:
   - job_name: 'cool-mint-api'
     static_configs:
     - targets: ['localhost:8080']
   ```

2. **Grafana Dashboard**
   ```bash
   # Start Grafana
   docker run -d -p 3000:3000 grafana/grafana
   
   # Import dashboard
   curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
     -H "Content-Type: application/json" \
     -d @dashboard.json
   ```

### Logging Configuration

1. **Structured Logging**
   ```python
   # Configure logging in main.py
   import logging
   import sys
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('app.log'),
           logging.StreamHandler(sys.stdout)
       ]
   )
   ```

2. **Log Aggregation**
   ```bash
   # ELK Stack setup
   docker-compose -f docker-compose.elk.yml up -d
   
   # Fluentd configuration
   docker run -d -p 24224:24224 fluent/fluentd
   ```

## Backup and Recovery

### Database Backup

1. **Automated Backups**
   ```bash
   #!/bin/bash
   # backup.sh
   DATE=$(date +%Y%m%d_%H%M%S)
   pg_dump -h localhost -U postgres cool_mint > backup_$DATE.sql
   
   # Upload to S3
   aws s3 cp backup_$DATE.sql s3://your-backup-bucket/
   
   # Cleanup old backups
   find . -name "backup_*.sql" -mtime +7 -delete
   ```

2. **Restore Process**
   ```bash
   # Restore from backup
   psql -h localhost -U postgres -d cool_mint < backup_20241215_120000.sql
   
   # Verify restoration
   psql -h localhost -U postgres -d cool_mint -c "SELECT COUNT(*) FROM sf_activity_structured;"
   ```

### Application Backup

1. **Code and Configuration**
   ```bash
   # Backup application files
   tar -czf app_backup_$(date +%Y%m%d).tar.gz app/ frontend/ docker/
   
   # Backup environment variables
   cp .env .env.backup.$(date +%Y%m%d)
   ```

## Performance Optimization

### Database Optimization

1. **Query Optimization**
   ```sql
   -- Analyze query performance
   EXPLAIN ANALYZE SELECT * FROM sf_activity_structured WHERE activity_date > '2024-01-01';
   
   -- Create optimal indexes
   CREATE INDEX CONCURRENTLY idx_activity_date_desc ON sf_activity_structured(activity_date DESC);
   ```

2. **Connection Pooling**
   ```python
   # SQLAlchemy connection pool
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_pre_ping=True
   )
   ```

### Application Optimization

1. **Caching Strategy**
   ```python
   # Redis caching
   import redis
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   # Cache filter options
   @lru_cache(maxsize=128)
   def get_filter_options():
       return fetch_filter_options_from_db()
   ```

2. **Frontend Optimization**
   ```javascript
   // Code splitting
   const ActivityTable = lazy(() => import('./components/ActivityTable'));
   
   // Memoization
   const MemoizedActivityTable = memo(ActivityTable);
   ```

## Security Hardening

### Network Security

1. **Firewall Configuration**
   ```bash
   # UFW firewall setup
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw deny 5432/tcp
   sudo ufw enable
   ```

2. **Docker Security**
   ```dockerfile
   # Use non-root user
   USER 1000:1000
   
   # Read-only root filesystem
   RUN chmod -R 755 /app
   ```

### Application Security

1. **Environment Variables**
   ```bash
   # Use secrets management
   kubectl create secret generic db-secret --from-literal=url=postgresql://...
   ```

2. **Input Validation**
   ```python
   # Pydantic validation
   from pydantic import BaseModel, validator
   
   class ActivityFilter(BaseModel):
       page: int = Field(ge=1, le=1000)
       page_size: int = Field(ge=1, le=100)
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker exec cool-mint_api pg_isready -h db -p 5432
   
   # Check logs
   docker logs cool-mint_api
   ```

2. **Memory Issues**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Increase memory limits
   docker run --memory=2g cool-mint-api
   ```

3. **Performance Issues**
   ```bash
   # Check query performance
   docker exec cool-mint_db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
   
   # Monitor API performance
   curl -w "@curl-format.txt" http://localhost:8080/api/activities/
   ```

### Health Checks

1. **API Health Check**
   ```bash
   # Basic health check
   curl -f http://localhost:8080/health || exit 1
   
   # Database health check
   curl -f http://localhost:8080/health/db || exit 1
   ```

2. **Automated Monitoring**
   ```bash
   # Setup monitoring alerts
   docker run -d prom/alertmanager
   ```

## Rollback Procedures

### Application Rollback

1. **Docker Rollback**
   ```bash
   # Tag current version
   docker tag cool-mint-api:latest cool-mint-api:backup
   
   # Deploy previous version
   docker run -d cool-mint-api:previous
   ```

2. **Database Rollback**
   ```bash
   # Rollback migration
   alembic downgrade -1
   
   # Restore from backup
   psql -h localhost -U postgres -d cool_mint < backup_previous.sql
   ```

---

*This deployment guide provides comprehensive instructions for deploying Cool Mint in various environments. For specific cloud platform details, consult the respective cloud provider documentation.*