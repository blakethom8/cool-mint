# Frontend Service Documentation

## Overview

The frontend service is a modern React application built with TypeScript that provides a user-friendly interface for browsing, filtering, and selecting sales activity data. It's designed to work seamlessly with the Cool Mint backend API to facilitate efficient data sharing for AI-powered sales insights.

## Technology Stack

- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Full type safety and enhanced developer experience
- **Vite**: Fast build tool and development server
- **Axios**: HTTP client for API communication
- **CSS3**: Custom styling with responsive design

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ActivityTable.tsx     # Main table component
│   │   ├── ActivityTable.css     # Table styling
│   │   ├── ActivityFilters.tsx   # Filter sidebar
│   │   └── ActivityFilters.css   # Filter styling
│   ├── services/           # API service layer
│   │   └── activityService.ts    # Activity API client
│   ├── types/              # TypeScript type definitions
│   │   └── activity.ts           # Activity-related types
│   ├── App.tsx             # Main application component
│   ├── App.css             # Global application styles
│   └── main.tsx            # Application entry point
├── public/                 # Static assets
├── package.json           # Dependencies and scripts
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite configuration
└── README.md              # Frontend-specific documentation
```

## Key Components

### App.tsx
The main application component that orchestrates:
- State management for activities, filters, and selection
- API calls to fetch data
- Communication between child components
- Error handling and loading states

### ActivityTable.tsx
The primary data display component featuring:
- Responsive table with sticky headers
- Multi-select functionality with checkboxes
- Pagination controls with First/Previous/Next/Last buttons
- Scrollable content area with fixed height
- Activity details display (date, subject, contacts, specialties)

### ActivityFilters.tsx
The filter sidebar component providing:
- Date range selection
- Owner/user filtering
- Activity type and status filters
- Contact specialty filtering
- Search functionality across subjects and descriptions

### activityService.ts
The API service layer that handles:
- HTTP requests to the backend API
- Parameter serialization for complex filters
- Response type validation
- Error handling and retries

## Configuration

### Vite Configuration (vite.config.ts)
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

### TypeScript Configuration
- Strict type checking enabled
- Modern ES2020+ features
- React JSX support
- Path mapping for clean imports

## Data Flow

```
User Interaction → Component State → API Service → Backend API
        ↓              ↓              ↓              ↓
   UI Updates ← State Updates ← Response Data ← Database Query
```

## API Integration

The frontend communicates with the backend through RESTful API calls:

### Activity Listing
- **Endpoint**: `GET /activities/`
- **Parameters**: page, page_size, filters, sort_by, sort_order
- **Response**: Paginated list of activities with metadata

### Filter Options
- **Endpoint**: `GET /activities/filter-options`
- **Response**: Available filter values for dropdowns

### Selection Processing
- **Endpoint**: `POST /activities/selection`
- **Payload**: Array of selected activity IDs
- **Response**: Processing confirmation

## State Management

The application uses React hooks for state management:

```typescript
const [activities, setActivities] = useState<ActivityListItem[]>([]);
const [selectedActivityIds, setSelectedActivityIds] = useState<Set<string>>(new Set());
const [filters, setFilters] = useState<ActivityFilters>({});
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

## Styling Architecture

### CSS Organization
- Component-specific CSS files co-located with components
- Global styles in `App.css`
- Responsive design principles
- Modern CSS Grid and Flexbox layouts

### Key Design Patterns
- Sticky table headers for data navigation
- Responsive table with horizontal scrolling
- Color-coded status indicators
- Consistent spacing and typography
- Loading states and error handling

## Performance Optimizations

### Table Rendering
- Virtualized scrolling for large datasets
- Efficient re-rendering with React keys
- Pagination to limit DOM nodes
- Debounced search and filter updates

### API Optimization
- Request deduplication
- Loading states to prevent multiple requests
- Error boundaries for graceful failures
- Efficient filter parameter serialization

## Development Workflow

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server
- Hot module replacement for instant updates
- Proxy configuration for API calls
- TypeScript compilation on-the-fly
- Source maps for debugging

## Testing Strategy

### Unit Testing
- Component testing with React Testing Library
- Service layer testing with mocked API calls
- Type safety validation
- Error boundary testing

### Integration Testing
- End-to-end user workflows
- API integration testing
- Cross-browser compatibility
- Performance testing

## Deployment

### Production Build
```bash
npm run build
```

### Build Output
- Optimized JavaScript bundles
- CSS minification
- Asset optimization
- Source maps for debugging

### Environment Variables
- API endpoints configuration
- Feature flags
- Analytics tracking IDs

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ JavaScript features
- CSS Grid and Flexbox support
- Responsive design for mobile devices

## Future Enhancements

### Planned Features
- Advanced search with filters
- Export functionality for selected data
- Real-time updates with WebSocket
- Offline support with service workers
- Enhanced mobile experience

### Technical Improvements
- State management with Redux/Zustand
- Component library integration
- Automated testing suite
- Performance monitoring
- Accessibility enhancements

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check backend service is running on port 8080
   - Verify Vite proxy configuration
   - Check CORS settings in backend

2. **Data Loading Issues**
   - Verify database connection
   - Check API endpoint responses
   - Review browser network tab

3. **Build Errors**
   - Check TypeScript compilation
   - Verify all dependencies are installed
   - Review import statements

### Debug Mode
Enable debug logging by setting:
```typescript
const DEBUG = true;
```

## Contributing

### Code Style
- Use TypeScript for all new code
- Follow React functional component patterns
- Maintain consistent naming conventions
- Add proper error handling

### Component Guidelines
- Keep components focused and single-purpose
- Use proper TypeScript interfaces
- Include error boundaries
- Add loading states

### Testing Requirements
- Test all user interactions
- Mock external dependencies
- Verify accessibility standards
- Test responsive behavior

---

*For additional support, refer to the main README.md or create an issue in the repository.*