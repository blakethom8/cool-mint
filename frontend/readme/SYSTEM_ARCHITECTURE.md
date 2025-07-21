# System Architecture Documentation

## Overview

Cool Mint is a comprehensive sales activity selector system built on a modern, scalable architecture. The system enables sales teams to efficiently browse, filter, and select call logs and activity data for sharing with Large Language Models (LLMs) to generate AI-powered sales insights.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
│   Port 3000     │    │   Port 8080     │    │   Port 5433     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vite Dev      │    │   Kong Gateway  │    │   Supabase      │
│   Server        │    │   (Bypassed)    │    │   Integration   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                    ┌─────────────────┐
                    │   Docker        │
                    │   Container     │
                    │   Orchestration │
                    └─────────────────┘
```

## Component Details

### Frontend Layer (React/TypeScript)

**Technology**: React 18, TypeScript, Vite
**Port**: 3000
**Responsibilities**:
- User interface for activity browsing and selection
- Real-time filtering and search capabilities
- Data visualization with responsive tables
- Multi-select functionality for batch operations
- Client-side state management

**Key Features**:
- Responsive design with mobile support
- Real-time search and filtering
- Pagination with efficient rendering
- Type-safe API integration
- Error handling and loading states

### Backend API Layer (FastAPI)

**Technology**: FastAPI, Python 3.11
**Port**: 8080
**Responsibilities**:
- RESTful API endpoints for data access
- Business logic implementation
- Database query optimization
- Data validation and serialization
- Authentication and authorization

**Key Features**:
- Automatic API documentation (Swagger/ReDoc)
- Pydantic data validation
- Async request handling
- CORS configuration for frontend integration
- Structured error responses

### Database Layer (PostgreSQL)

**Technology**: PostgreSQL 15, Supabase
**Port**: 5433
**Responsibilities**:
- Persistent data storage
- Efficient query processing
- Data integrity and consistency
- Full-text search capabilities
- Analytics and reporting data

**Key Features**:
- ACID compliance
- JSON field support for complex data
- Full-text search indexing
- Efficient pagination queries
- Backup and recovery capabilities

### Infrastructure Layer (Docker)

**Technology**: Docker, Docker Compose
**Responsibilities**:
- Container orchestration
- Service discovery
- Environment isolation
- Development and deployment consistency
- Resource management

**Key Features**:
- Multi-service deployment
- Volume persistence
- Network isolation
- Health checks
- Automatic restarts

## Data Flow Architecture

### Request Flow
```
User Action → Frontend State → API Request → Backend Processing → Database Query → Response
     ↓              ↓              ↓              ↓                ↓              ↓
UI Update ← State Update ← API Response ← Data Processing ← Query Result ← Raw Data
```

### Authentication Flow (Development)
```
Frontend Request → Vite Proxy → Kong Gateway → Basic Auth → FastAPI Backend
                              (Currently Bypassed)
```

### Data Processing Flow
```
Salesforce Data → ETL Pipeline → SfActivityStructured Table → API Layer → Frontend Display
```

## Service Communication

### Frontend ↔ Backend API

**Protocol**: HTTP/REST
**Format**: JSON
**Authentication**: Kong Basic Auth (bypassed in development)

**Endpoints**:
- `GET /activities/` - List activities with filtering
- `GET /activities/filter-options` - Get filter metadata
- `POST /activities/selection` - Process selected activities
- `GET /activities/{id}` - Get activity details

### Backend API ↔ Database

**Protocol**: SQL over TCP
**ORM**: SQLAlchemy
**Connection**: PostgreSQL native driver

**Optimization Features**:
- Connection pooling
- Query result caching
- Prepared statements
- Index optimization

## Security Architecture

### Current Security Measures

1. **Input Validation**
   - Pydantic model validation
   - SQL injection prevention
   - XSS protection

2. **Network Security**
   - CORS configuration
   - Docker network isolation
   - Port restrictions

3. **Data Protection**
   - Environment variable isolation
   - Secure database connections
   - Structured logging (no sensitive data)

### Future Security Enhancements

1. **Authentication & Authorization**
   - JWT token implementation
   - Role-based access control
   - API key management

2. **Data Encryption**
   - TLS/SSL termination
   - Database encryption at rest
   - Secure session management

3. **Monitoring & Auditing**
   - Access logging
   - Security event monitoring
   - Intrusion detection

## Scalability Considerations

### Horizontal Scaling

**Frontend**:
- CDN deployment for static assets
- Load balancing across multiple instances
- Client-side caching strategies

**Backend**:
- Stateless API design
- Load balancer distribution
- Auto-scaling based on CPU/memory

**Database**:
- Read replicas for query distribution
- Connection pooling optimization
- Query result caching

### Vertical Scaling

**Resource Optimization**:
- Database query optimization
- Memory usage monitoring
- CPU utilization tracking

**Performance Monitoring**:
- Request latency tracking
- Database performance metrics
- Error rate monitoring

## Development Architecture

### Local Development Setup

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Vite Dev      │    │   FastAPI       │    │   PostgreSQL    │
│   Server        │◄──►│   Development   │◄──►│   Container     │
│   localhost:3000│    │   localhost:8080│    │   localhost:5433│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Hot Reload    │    │   Auto Reload   │    │   Volume        │
│   File Watch    │    │   Code Changes  │    │   Persistence   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Development Workflow

1. **Code Changes** → Hot reload in browser
2. **API Changes** → Automatic server restart
3. **Database Changes** → Alembic migrations
4. **Docker Changes** → Container rebuild

## Production Architecture

### Deployment Strategy

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   Kong Gateway  │    │   Database      │
│   (Nginx/HAProxy) │◄──►│   API Gateway   │◄──►│   Cluster       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Backup        │
│   Instances     │    │   Instances     │    │   & Recovery    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Infrastructure Components

1. **Container Orchestration**: Docker Swarm or Kubernetes
2. **Service Discovery**: Consul or etcd
3. **Monitoring**: Prometheus + Grafana
4. **Logging**: ELK Stack or Fluentd
5. **Caching**: Redis Cluster
6. **Database**: PostgreSQL High Availability

## Performance Architecture

### Optimization Strategies

**Frontend Performance**:
- Code splitting and lazy loading
- Virtual scrolling for large datasets
- Memoization for expensive computations
- Efficient state management

**Backend Performance**:
- Async request handling
- Database query optimization
- Response caching
- Connection pooling

**Database Performance**:
- Strategic indexing
- Query plan optimization
- Partitioning for large tables
- Read/write separation

### Monitoring & Metrics

**Key Performance Indicators**:
- Request latency (p95, p99)
- Database query performance
- Memory usage patterns
- Error rates and types

**Monitoring Stack**:
- Application Performance Monitoring (APM)
- Database performance monitoring
- Infrastructure metrics
- User experience monitoring

## Integration Architecture

### External System Integration

**Salesforce Integration**:
- REST API connectivity
- Bulk data synchronization
- Real-time webhook updates
- Data transformation pipeline

**LLM Integration** (Future):
- OpenAI API integration
- Prompt engineering pipeline
- Response processing
- Usage tracking and optimization

### Data Pipeline Architecture

```
Salesforce API → ETL Service → Data Validation → Database Storage → API Layer → Frontend
      ↓              ↓              ↓                ↓              ↓           ↓
  Raw Data → Transformation → Structured Data → Persistence → API Response → UI Display
```

## Disaster Recovery

### Backup Strategy

1. **Database Backups**
   - Daily full backups
   - Point-in-time recovery
   - Cross-region replication

2. **Application Backups**
   - Code repository backups
   - Configuration backups
   - Environment variable backups

3. **Infrastructure Backups**
   - Docker images
   - Configuration files
   - SSL certificates

### Recovery Procedures

1. **Database Recovery**
   - Automatic failover to replica
   - Point-in-time recovery
   - Data consistency verification

2. **Application Recovery**
   - Blue-green deployment
   - Rollback procedures
   - Health check verification

## Future Architecture Enhancements

### Planned Improvements

1. **Microservices Architecture**
   - Service decomposition
   - API Gateway enhancement
   - Service mesh implementation

2. **Event-Driven Architecture**
   - Message queue integration
   - Event sourcing
   - CQRS implementation

3. **Cloud-Native Features**
   - Serverless functions
   - Auto-scaling groups
   - Managed databases

4. **AI/ML Integration**
   - Model serving infrastructure
   - Feature store implementation
   - ML pipeline automation

---

*This architecture documentation serves as a comprehensive guide for understanding, developing, and maintaining the Cool Mint system. For specific implementation details, refer to the service-specific documentation.*