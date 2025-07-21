# Activity Selector Frontend

A simple React-based frontend for selecting and filtering sales activity logs to share with a large language model.

## Features

- **Activity Table**: View all activities in a paginated table
- **Filtering**: Filter activities by:
  - Date range
  - Owner/User
  - Text search (subject and description)
  - Contact types (MD, Pharma, etc.)
  - Contact specialties
  - Activity types and subtypes
  - Status
- **Selection**: Select individual activities or all activities on the current page
- **Batch Processing**: Process selected activities for LLM analysis

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on http://localhost:8080

## Installation

```bash
# Install dependencies
npm install
```

## Development

```bash
# Start the development server
npm run dev
```

The application will be available at http://localhost:3000

## Configuration

The frontend is configured to proxy API requests to the backend running on port 8080. If your backend runs on a different port, update the proxy configuration in `vite.config.ts`.

## Project Structure

```
src/
├── components/       # React components
│   ├── ActivityTable.tsx
│   ├── ActivityFilters.tsx
│   └── *.css        # Component styles
├── services/        # API service layer
│   └── activityService.ts
├── types/           # TypeScript type definitions
│   └── activity.ts
├── App.tsx          # Main application component
├── App.css          # Application styles
└── main.tsx         # Application entry point
```

## API Integration

The frontend expects the following API endpoints:

- `GET /api/activities` - List activities with filtering
- `GET /api/activities/filter-options` - Get available filter options
- `POST /api/activities/selection` - Process selected activities

## Future Enhancements

- Real-time activity updates
- Advanced search capabilities
- Activity detail view
- Export functionality
- LLM interaction UI
- User authentication

## Deployment

For production deployment:

```bash
# Build the application
npm run build

# The build output will be in the dist/ directory
```

## Separating into Standalone Repository

This frontend is designed to be easily separated into its own repository. To do so:

1. Copy the entire `frontend/` directory to a new repository
2. Update the API base URL in `vite.config.ts` to point to your production backend
3. Add environment variable support for API configuration
4. Set up CI/CD for the frontend repository