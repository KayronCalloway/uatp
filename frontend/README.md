# UATP Capsule Engine Frontend

Modern React/Next.js frontend for the UATP Capsule Engine - civilization-grade AI attribution infrastructure.

## What We've Built

### Core Infrastructure
- **Next.js 15** with TypeScript and Tailwind CSS
- **React Query** for API state management
- **Comprehensive API client** with full UATP backend integration
- **Authentication system** with API key management
- **Responsive design** with modern UI components

### Key Features
- **Login/Authentication**: API key-based authentication with validation
- **Dashboard**: Real-time system health, capsule stats, and trust metrics
- **API Integration**: Full integration with existing UATP backend endpoints
- **Error Handling**: Comprehensive error handling and loading states
- **TypeScript**: Full type safety with backend API schemas

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- UATP Backend API running (see backend setup)

### Installation
```bash
cd frontend
npm install
```

### Environment Setup
```bash
# Copy the example environment file
cp .env.example .env.local

# Edit if needed (defaults work for local development)
```

Required environment variables:
| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_UATP_API_URL` | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_ENABLE_REAL_API` | `true` | Use real backend (vs mock) |
| `NEXT_PUBLIC_ENABLE_MOCK_FALLBACK` | `true` | Fall back to mock if API unavailable |

### Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx         # Root layout with providers
│   │   └── page.tsx           # Main page with auth flow
│   ├── components/
│   │   ├── auth/              # Authentication components
│   │   ├── dashboard/         # Dashboard components
│   │   └── ui/                # Reusable UI components
│   ├── contexts/
│   │   └── auth-context.tsx   # Authentication context
│   ├── lib/
│   │   ├── api-client.ts      # API client with all endpoints
│   │   ├── react-query.tsx    # React Query provider
│   │   └── utils.ts           # Utility functions
│   └── types/
│       └── api.ts             # TypeScript types from backend
```

## API Integration

### Available Endpoints
- **Core**: Health checks, system info
- **Capsules**: CRUD operations, stats, verification
- **Chain**: Sealing, verification, cryptographic operations
- **Trust**: Agent trust scores, policies, violations
- **AI**: Content generation with attribution
- **Reasoning**: Analysis and validation

### API Client Usage
```typescript
import { api } from '@/lib/api-client';

// Get capsule statistics
const stats = await api.getCapsuleStats();

// Create a new capsule
const capsule = await api.createCapsule({
  type: 'chat',
  content: 'Hello world',
  metadata: { source: 'frontend' }
});

// Analyze reasoning
const analysis = await api.analyzeReasoning({
  capsule_id: 'some-id',
  analysis_type: 'comprehensive'
});
```

## UI Components

### Authentication
- **LoginForm**: API key authentication with validation
- **AuthProvider**: Authentication state management

### Dashboard
- **Dashboard**: Main dashboard with system overview
- **Status Cards**: Real-time system health and metrics
- **Quick Actions**: Navigation to key features

### UI Components
- **Button**: Consistent button component with variants
- **Card**: Layout cards for content sections
- **Input**: Form input with validation styles

## State Management

### React Query
- **Automatic caching** with configurable stale time
- **Background refetching** for real-time updates
- **Error handling** with retry logic
- **DevTools** for debugging queries

### Authentication
- **Local storage** for API key persistence
- **Automatic validation** on app startup
- **Context-based** state management

## Next Steps

### Phase 1: Core Features (Current)
- • Authentication system (Complete)
- • Basic dashboard (Complete)
- • API integration (Complete)
- • Capsule list/detail views (In Progress)
- • Trust dashboard (In Progress)

### Phase 2: Advanced Features
- • Universe visualization (port from existing visualizer)
- • Real-time updates with WebSockets
- • Economic attribution dashboard
- • Governance interface

### Phase 3: Civilization Scale
- • Multi-node federation
- • Global universe view
- • Cross-border economic coordination
- • Governance participation

## Backend Integration

### API Configuration
The frontend is configured to connect to the UATP backend at `http://localhost:8000`.

### Authentication
Uses API key authentication. Get your API key from the backend system.

### Error Handling
- Network errors are handled gracefully
- API errors are displayed to the user
- Retry logic for transient failures

## Responsive Design

- **Mobile-first** approach with Tailwind CSS
- **Responsive layout** that works on all screen sizes
- **Touch-friendly** interactions
- **Progressive Web App** ready

## Security

- **API key validation** before requests
- **Secure storage** of authentication tokens
- **HTTPS ready** for production
- **XSS protection** with proper sanitization

## Future Enhancements

### Universe Visualization
- **3D rendering** with Three.js/WebGL
- **Cosmic metaphors** for capsule relationships
- **Real-time collaboration** features
- **Temporal navigation** through capsule history

### Economic Dashboard
- **Real-time attribution** tracking
- **Dividend visualization** and management
- **Multi-currency support** for global coordination
- **Economic analytics** and forecasting

### Governance Interface
- **Proposal creation** and voting
- **Stakeholder representation** with quadratic voting
- **Dispute resolution** interface
- **Constitutional framework** participation

---

Built for civilization-scale AI attribution infrastructure.
