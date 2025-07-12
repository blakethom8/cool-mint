# Cool Mint - AI-Enabled CRM for Physician Liaisons

## Overview

Cool Mint is a comprehensive CRM system designed specifically for physician liaisons, built on the GenAI Launchpad framework. It provides powerful tools for managing sales activities, organizing physician contacts, and exploring market territories through an intuitive interface. The system leverages AI capabilities to enhance productivity and provide intelligent insights for healthcare sales teams.

## System Architecture

### Core Components

1. **Backend API (FastAPI)**
   - RESTful API endpoints for activity management
   - Pydantic schemas for data validation
   - PostgreSQL database integration with SQLAlchemy ORM
   - CORS middleware for frontend integration

2. **Frontend Application (React/TypeScript)**
   - Modern React application with TypeScript
   - Responsive activity table with filtering capabilities
   - Multi-select functionality for activity selection
   - Real-time pagination and scrolling

3. **Database Layer**
   - PostgreSQL database with Supabase integration
   - Structured activity data from Salesforce
   - Efficient querying with indexed fields

4. **Infrastructure**
   - Docker containerization for all services
   - Kong API Gateway for routing (bypassed in current setup)
   - Redis for caching and background tasks
   - Celery for asynchronous processing

### Data Flow

```
Frontend (React) → FastAPI Backend → PostgreSQL Database
     ↓                    ↓              ↓
Activity Selection → API Processing → SfActivityStructured Table
```

## Key Features

### Activity Selector
- **Advanced Filtering**: Filter activities by date range, owner, contact types, specialties, and more
- **Multi-Select Interface**: Select individual activities or bulk operations
- **Real-time Search**: Search across activity subjects and descriptions
- **Responsive Design**: Scrollable tables with sticky headers
- **Pagination**: Efficient handling of large datasets
- **Type Safety**: Full TypeScript implementation for reliability

### Bundle Manager
- **Activity Bundling**: Group related activities into manageable bundles
- **AI-Powered Descriptions**: Generate bundle descriptions using Claude AI
- **Bundle Statistics**: View activity counts and date ranges
- **Quick Actions**: Edit, delete, and manage bundles efficiently

### Market Explorer (New)
- **Interactive Map Interface**: Explore physician contacts on a geographic map
- **Smart Markers**: Marker size indicates contact density at each location
- **Comprehensive Filtering**: Filter by specialty, organization, location, and more
- **Split-View Design**: Map view synchronized with scrollable contact list
- **Performance Optimized**: Viewport-based loading for 3000+ contacts
- **Clean Aesthetics**: CARTO Light map theme for professional appearance

## Database Schema

### Activity Data
The system uses the `SfActivityStructured` table which contains:
- Activity metadata (ID, date, subject, description)
- Contact information (names, counts, specialties)
- Owner details (user names, IDs)
- Activity types and statuses
- Structured data for efficient querying

### Contact Data
The `SfContacts` table provides:
- Contact identification (Salesforce ID, name, NPI)
- Geographic data (mailing address, latitude/longitude)
- Professional info (specialty, organization, physician status)
- Activity tracking (last activity date, days since visit)
- Custom fields (geography, panel status, network info)

## API Endpoints

### Activities API (`/api/activities/`)
- `GET /` - List activities with filtering and pagination
- `GET /filter-options` - Get available filter options
- `POST /selection` - Process selected activities

### Bundles API (`/api/bundles/`)
- `GET /` - List all bundles
- `POST /` - Create new bundle
- `PUT /{id}` - Update bundle
- `DELETE /{id}` - Delete bundle
- `POST /generate-description` - AI-powered description generation

### Contacts API (`/api/contacts/`)
- `GET /map-data` - Optimized contact data for map markers
- `GET /` - List contacts with filtering and pagination
- `GET /{id}` - Get detailed contact information
- `GET /filter-options` - Get available filter values

### Authentication
Currently bypassing Kong authentication for development. The system connects directly to FastAPI backend running on port 8080.

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Node.js and npm (for frontend development)
- PostgreSQL with Salesforce data

### Environment Setup

1. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```
   PROJECT_NAME=cool-mint
   POSTGRES_HOST=db
   POSTGRES_DB=postgres
   POSTGRES_PASSWORD=your-super-secret-and-long-postgres-password
   POSTGRES_PORT=5432
   # Add other required environment variables
   ```

2. **Database Setup**
   Ensure your PostgreSQL database contains the `SfActivityStructured` table with proper Salesforce data.

### Starting the System

#### Backend Services
```bash
# Start Docker containers
cd docker
docker-compose up -d

# Verify services are running
docker-compose ps
```

The backend API will be available at `http://localhost:8080`

#### Frontend Application
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Alternative Quick Start
Use the provided startup script:
```bash
./start-activity-selector.sh
```

## Development Notes

### Direct FastAPI Connection
**Important**: The current setup bypasses Kong API Gateway and connects directly to FastAPI for development purposes. This approach:
- Simplifies authentication during development
- Avoids Kong routing conflicts with Supabase Studio
- Provides direct access to FastAPI at `localhost:8080`
- Uses Vite proxy configuration for CORS handling

### Frontend-Backend Communication
- Frontend proxy configuration routes `/activities/*` to backend
- CORS middleware configured in FastAPI to allow `localhost:3000`
- Authentication handled through Kong's basic auth (username/password popup)

### Key Configuration Files
- `app/main.py` - FastAPI application with CORS configuration
- `frontend/vite.config.ts` - Vite proxy configuration
- `docker/volumes/api/kong.yml` - Kong routing configuration
- `app/api/activities.py` - Activity API endpoints

## Testing

### Backend Testing
```bash
# Test API endpoints
./test-activity-api.sh

# Test complete setup
./test-complete-setup.sh
```

### Frontend Testing
```bash
cd frontend
npm run build  # Test build process
npm run preview  # Preview production build
```

## Deployment Considerations

### Production Deployment
1. **Authentication**: Implement proper authentication system
2. **HTTPS**: Configure SSL certificates for production
3. **Database**: Use production-grade PostgreSQL setup
4. **Monitoring**: Add logging and monitoring solutions
5. **Scaling**: Consider load balancing for high traffic

### Kong Gateway Integration
For production deployment, re-enable Kong API Gateway:
1. Update Kong configuration in `docker/volumes/api/kong.yml`
2. Implement proper authentication plugins
3. Configure rate limiting and security policies

## Service Documentation

Detailed documentation for individual services can be found in:
- `frontend/readme/` - Frontend service documentation
- `app/api/README.md` - Backend API documentation
- `app/services/README.md` - Business logic documentation
- `MARKET_EXPLORER_TODO.md` - Market Explorer planning document
- `MARKET_EXPLORER_IMPLEMENTATION.md` - Detailed implementation guide

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation
- **PostgreSQL**: Database
- **Redis**: Caching and task queue
- **Celery**: Background task processing

### Frontend
- **React 18**: User interface framework
- **TypeScript**: Type safety
- **Vite**: Build tool and development server
- **Axios**: HTTP client
- **React Leaflet**: Interactive mapping
- **Leaflet**: Map rendering engine
- **CSS3**: Styling

### Infrastructure
- **Docker**: Containerization
- **Kong**: API Gateway (bypassed in development)
- **Supabase**: Database and auth services

## Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new features
3. Update documentation for API changes
4. Test both frontend and backend components
5. Ensure Docker containers build successfully

## License

This project is licensed under the DATALUMINA License. See the [LICENSE](/LICENSE) file for details.

## Support

For support and questions:
- Create issues in the GitHub repository
- Check the service-specific documentation in `frontend/readme/`
- Review the GenAI Launchpad documentation

---

*Built with ❤️ using the GenAI Launchpad framework*