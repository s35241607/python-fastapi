# Frontend-Backend Integration Design

## Overview

This document outlines the comprehensive design for integrating the Vue 3 frontend with the FastAPI backend in the Enterprise Ticket Management System. The integration strategy ensures seamless communication between frontend and backend services across different environments (development and production) while maintaining security, performance, and maintainability.

The system implements a RESTful API architecture with JWT-based authentication, comprehensive error handling, and environment-specific configurations to support both local development through Vite proxy and production deployment via Docker containers.

## Technology Stack & Dependencies

### Frontend Technology Stack
- **Vue 3.5.19** - Progressive JavaScript framework
- **TypeScript 5.9.2** - Type-safe JavaScript development
- **Vite 7.1.3** - Fast build tool and development server
- **Axios** - HTTP client for API communication
- **Pinia** - State management library
- **Vue Router** - Client-side routing

### Backend Technology Stack
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - Async ORM for database operations
- **PostgreSQL 16** - Primary database
- **JWT** - Token-based authentication
- **Pydantic** - Data validation and serialization

### Development & Deployment Tools
- **Node.js 22** - JavaScript runtime
- **Python 3.13+** - Backend runtime
- **Docker & Docker Compose** - Containerization
- **Nginx** - Production web server and reverse proxy

## API Architecture Overview

### Backend API Structure

The backend exposes a comprehensive REST API organized into the following modules:

```mermaid
graph TB
    subgraph "FastAPI Backend"
        Auth[Authentication Module<br>/api/v1/auth]
        Tickets[Tickets Module<br>/api/v1/tickets]
        Approvals[Approvals Module<br>/api/v1/approvals]
        Comments[Comments Module<br>/api/v1/comments]
        Attachments[Attachments Module<br>/api/v1/attachments]
        Reports[Reports Module<br>/api/v1/reports]
        Users[Users Module<br>/api/v1/users]
        Items[Items Module<br>/api/v1/items]
    end

    subgraph "Core Services"
        AuthService[Authentication Service]
        TicketService[Ticket Service]
        ApprovalService[Approval Service]
        FileService[File Service]
        NotificationService[Notification Service]
        ReportingService[Reporting Service]
    end

    Auth --> AuthService
    Tickets --> TicketService
    Approvals --> ApprovalService
    Attachments --> FileService
    Reports --> ReportingService
```

### API Endpoint Categories

| Module | Base Path | Key Endpoints | Authentication Required |
|--------|-----------|---------------|------------------------|
| Authentication | `/api/v1/auth` | login, logout, register, refresh, profile | Partial |
| Tickets | `/api/v1/tickets` | CRUD, search, status updates, assignments | Yes |
| Approvals | `/api/v1/approvals` | workflow management, step processing | Yes |
| Comments | `/api/v1/comments` | thread management, updates | Yes |
| Attachments | `/api/v1/attachments` | upload, download, metadata | Yes |
| Reports | `/api/v1/reports` | dashboard, analytics, exports | Yes |
| Users | `/api/v1/users` | profile, management | Yes |
| Items | `/api/v1/items` | general entity management | Yes |

## Frontend API Client Architecture

### Core API Client Implementation

The frontend implements a centralized API client using Axios with comprehensive error handling, automatic token refresh, and request/response interceptors:

```mermaid
graph TD
    subgraph "Frontend API Layer"
        ApiClient[API Client<br>Axios Instance]
        AuthInterceptor[Auth Interceptor<br>Token Management]
        ErrorHandler[Error Handler<br>Response Processing]
        TokenRefresh[Token Refresh<br>Automatic Renewal]
    end

    subgraph "Service Layer"
        TicketAPI[Ticket API Service]
        AuthAPI[Auth API Service]
        ApprovalAPI[Approval API Service]
        CommentsAPI[Comments API Service]
        FileAPI[File Upload Service]
        NotificationAPI[Notification Service]
        SearchAPI[Search Service]
    end

    subgraph "Store Layer"
        AuthStore[Auth Store<br>Pinia]
        TicketStore[Ticket Store]
        ApprovalStore[Approval Store]
        DashboardStore[Dashboard Store]
    end

    ApiClient --> AuthInterceptor
    ApiClient --> ErrorHandler
    ApiClient --> TokenRefresh

    TicketAPI --> ApiClient
    AuthAPI --> ApiClient
    ApprovalAPI --> ApiClient
    CommentsAPI --> ApiClient
    FileAPI --> ApiClient
    NotificationAPI --> ApiClient
    SearchAPI --> ApiClient

    TicketAPI --> TicketStore
    AuthAPI --> AuthStore
    ApprovalAPI --> ApprovalStore
```

### Authentication Flow

The system implements JWT-based authentication with automatic token refresh:

```mermaid
sequenceDiagram
    participant Frontend
    participant APIClient
    participant Backend
    participant AuthStore

    Frontend->>APIClient: Login Request
    APIClient->>Backend: POST /api/v1/auth/login
    Backend-->>APIClient: Access Token + Refresh Token
    APIClient->>AuthStore: Store Tokens
    AuthStore-->>Frontend: Login Success

    loop API Requests
        Frontend->>APIClient: API Request
        APIClient->>APIClient: Add Bearer Token
        APIClient->>Backend: Authenticated Request
        alt Token Valid
            Backend-->>APIClient: Success Response
        else Token Expired
            Backend-->>APIClient: 401 Unauthorized
            APIClient->>Backend: POST /api/v1/auth/refresh
            Backend-->>APIClient: New Access Token
            APIClient->>APIClient: Retry Original Request
            APIClient->>Backend: Request with New Token
            Backend-->>APIClient: Success Response
        end
        APIClient-->>Frontend: Final Response
    end
```

## Environment Configuration Strategy

### Development Environment Configuration

#### Vite Configuration (`vite.config.ts`)
```typescript
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/auth': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/tickets': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/approvals': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/comments': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/attachments': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      },
      '/reports': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
})
```

#### Environment Variables Structure

**Development (`.env.development`)**
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_BACKEND_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_ENABLE_DEV_TOOLS=true
```

**Production (`.env.production`)**
```env
VITE_API_BASE_URL=http://backend:8000
VITE_BACKEND_URL=http://backend:8000
VITE_ENVIRONMENT=production
VITE_ENABLE_DEV_TOOLS=false
```

**Docker Environment (`.env.docker`)**
```env
VITE_API_BASE_URL=http://backend:8000
VITE_BACKEND_URL=http://backend:8000
VITE_ENVIRONMENT=docker
VITE_ENABLE_DEV_TOOLS=false
```

### Backend CORS Configuration

The backend must be configured to allow requests from all frontend environments:

```python
# backend/app/core/config.py
CORS_ORIGINS = [
    "http://localhost:5173",     # Vite dev server
    "http://127.0.0.1:5173",     # Alternative localhost
    "http://localhost:3000",     # Alternative frontend port
    "http://frontend:5173",      # Docker container name
    "http://vue_frontend:5173",  # Alternative Docker name
    "http://0.0.0.0:5173",       # Bind all interfaces
    "https://your-domain.com"    # Production domain
]
```

## Docker Configuration for Production

### Frontend Dockerfile Enhancement

```dockerfile
# Stage 1: Build environment
FROM node:22-alpine as build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Set environment for Docker build
ENV VITE_API_BASE_URL=http://backend:8000
ENV VITE_ENVIRONMENT=production

# Build the application
RUN npm run build

# Stage 2: Production environment
FROM nginx:alpine as production-stage

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration for Production

```nginx
# nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Proxy authentication endpoints
    location /auth/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Handle static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Error pages
    error_page 404 /index.html;
}
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:80"
    environment:
      - VITE_API_BASE_URL=http://backend:8000
      - VITE_ENVIRONMENT=docker
    depends_on:
      - backend
    networks:
      - frontend_network
      - backend_network
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:password@postgres:5432/ticketdb
      - CORS_ORIGINS=http://localhost:5173,http://frontend:5173,http://vue_frontend:5173
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - postgres
    networks:
      - backend_network
      - database_network
    restart: unless-stopped

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ticketdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - database_network
    restart: unless-stopped

networks:
  frontend_network:
    driver: bridge
  backend_network:
    driver: bridge
  database_network:
    driver: bridge

volumes:
  postgres_data:
```

## API Service Layer Implementation

### Enhanced API Client Service

```typescript
// Enhanced API configuration with environment detection
const getApiBaseUrl = (): string => {
  const isDevelopment = import.meta.env.DEV
  const isDocker = import.meta.env.VITE_ENVIRONMENT === 'docker'

  if (isDevelopment) {
    // In development, use proxy paths
    return ''
  } else if (isDocker) {
    // In Docker, use container communication
    return 'http://backend:8000'
  } else {
    // Production with custom domain
    return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  }
}

class EnhancedApiClient {
  private client: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = getApiBaseUrl()
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  // Environment-aware request handling
  private buildUrl(endpoint: string): string {
    if (import.meta.env.DEV) {
      // In development, use proxy paths
      return endpoint
    }
    return endpoint
  }
}
```

### Service Module Structure

Each API domain has a dedicated service module that follows consistent patterns:

```typescript
// Example: Enhanced Ticket API Service
export class TicketApiService {
  constructor(private apiClient: ApiClient) {}

  // Ticket CRUD operations
  async createTicket(ticketData: TicketCreate): Promise<TicketDetail> {
    return this.apiClient.post('/api/v1/tickets/', ticketData)
  }

  async getTicket(ticketId: number): Promise<TicketDetail> {
    return this.apiClient.get(`/api/v1/tickets/${ticketId}`)
  }

  async updateTicket(ticketId: number, updates: TicketUpdate): Promise<TicketDetail> {
    return this.apiClient.patch(`/api/v1/tickets/${ticketId}`, updates)
  }

  async deleteTicket(ticketId: number): Promise<void> {
    return this.apiClient.delete(`/api/v1/tickets/${ticketId}`)
  }

  // Advanced search and filtering
  async searchTickets(filters: TicketFilter, pagination: PaginationParams): Promise<PaginatedResponse<TicketSummary>> {
    const params = new URLSearchParams()

    // Build query parameters
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        params.append(key, String(value))
      }
    })

    Object.entries(pagination).forEach(([key, value]) => {
      params.append(key, String(value))
    })

    return this.apiClient.get(`/api/v1/tickets/search?${params.toString()}`)
  }

  // Status management
  async updateTicketStatus(ticketId: number, status: TicketStatusUpdate): Promise<TicketDetail> {
    return this.apiClient.patch(`/api/v1/tickets/${ticketId}/status`, status)
  }

  // Assignment operations
  async assignTicket(ticketId: number, assigneeId: number): Promise<TicketDetail> {
    return this.apiClient.patch(`/api/v1/tickets/${ticketId}/assign`, { assignee_id: assigneeId })
  }
}
```

## Error Handling & Response Processing

### Centralized Error Handling

```typescript
export interface ApiError {
  message: string
  code?: string
  details?: any
  status?: number
  field_errors?: Record<string, string[]>
}

export class ApiErrorHandler {
  static handle(error: any): ApiError {
    if (error.response) {
      const { status, data } = error.response

      // Handle validation errors (422)
      if (status === 422 && data.detail) {
        return {
          message: 'Validation error',
          code: 'VALIDATION_ERROR',
          status,
          field_errors: this.extractFieldErrors(data.detail)
        }
      }

      // Handle authentication errors (401)
      if (status === 401) {
        return {
          message: 'Authentication required',
          code: 'AUTH_ERROR',
          status
        }
      }

      // Handle authorization errors (403)
      if (status === 403) {
        return {
          message: 'Access denied',
          code: 'PERMISSION_ERROR',
          status
        }
      }

      // Handle not found errors (404)
      if (status === 404) {
        return {
          message: 'Resource not found',
          code: 'NOT_FOUND',
          status
        }
      }

      // Handle server errors (5xx)
      if (status >= 500) {
        return {
          message: 'Server error occurred',
          code: 'SERVER_ERROR',
          status
        }
      }

      return {
        message: data?.message || data?.detail || 'Request failed',
        code: data?.code,
        details: data?.details,
        status
      }
    }

    // Network errors
    if (error.request) {
      return {
        message: 'Network error - please check your connection',
        code: 'NETWORK_ERROR'
      }
    }

    // Other errors
    return {
      message: error.message || 'An unexpected error occurred',
      code: 'UNKNOWN_ERROR'
    }
  }

  private static extractFieldErrors(details: any[]): Record<string, string[]> {
    const fieldErrors: Record<string, string[]> = {}

    details.forEach(error => {
      if (error.loc && error.msg) {
        const field = error.loc[error.loc.length - 1]
        if (!fieldErrors[field]) {
          fieldErrors[field] = []
        }
        fieldErrors[field].push(error.msg)
      }
    })

    return fieldErrors
  }
}
```

## State Management Integration

### Pinia Store Integration Pattern

```typescript
// Enhanced Auth Store with API integration
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: null as string | null,
    refreshToken: null as string | null,
    isAuthenticated: false,
    loading: false,
    error: null as ApiError | null
  }),

  actions: {
    async login(credentials: LoginRequest): Promise<void> {
      this.loading = true
      this.error = null

      try {
        const response = await authApiService.login(credentials)

        this.setTokens(
          response.access_token,
          response.refresh_token,
          response.expires_in
        )
        this.user = response.user
        this.isAuthenticated = true

        // Store tokens in localStorage for persistence
        localStorage.setItem('access_token', response.access_token)
        localStorage.setItem('refresh_token', response.refresh_token)

      } catch (error) {
        this.error = ApiErrorHandler.handle(error)
        throw this.error
      } finally {
        this.loading = false
      }
    },

    async logout(): Promise<void> {
      try {
        if (this.refreshToken) {
          await authApiService.logout(this.refreshToken)
        }
      } catch (error) {
        console.warn('Logout API call failed:', error)
      } finally {
        this.clearAuthState()
      }
    },

    clearAuthState(): void {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.isAuthenticated = false
      this.error = null

      // Clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },

    setTokens(accessToken: string, refreshToken: string, expiresIn: number): void {
      this.accessToken = accessToken
      this.refreshToken = refreshToken

      // Set token expiration timer
      const expirationTime = Date.now() + (expiresIn * 1000)
      localStorage.setItem('token_expiration', expirationTime.toString())
    }
  }
})
```

## Testing Strategy

### Unit Testing for API Services

```typescript
// Example: Ticket API Service Tests
describe('TicketApiService', () => {
  let ticketService: TicketApiService
  let mockApiClient: jest.Mocked<ApiClient>

  beforeEach(() => {
    mockApiClient = {
      get: jest.fn(),
      post: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
    } as any

    ticketService = new TicketApiService(mockApiClient)
  })

  describe('createTicket', () => {
    it('should create a ticket successfully', async () => {
      const ticketData: TicketCreate = {
        title: 'Test Ticket',
        description: 'Test Description',
        priority: Priority.MEDIUM,
        type: TicketType.ISSUE
      }

      const expectedResponse: TicketDetail = {
        id: 1,
        ...ticketData,
        status: TicketStatus.OPEN,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      mockApiClient.post.mockResolvedValue(expectedResponse)

      const result = await ticketService.createTicket(ticketData)

      expect(mockApiClient.post).toHaveBeenCalledWith('/api/v1/tickets/', ticketData)
      expect(result).toEqual(expectedResponse)
    })

    it('should handle validation errors', async () => {
      const ticketData: TicketCreate = {
        title: '',
        description: 'Test Description',
        priority: Priority.MEDIUM,
        type: TicketType.ISSUE
      }

      const validationError = {
        response: {
          status: 422,
          data: {
            detail: [
              {
                loc: ['body', 'title'],
                msg: 'Title is required',
                type: 'value_error.missing'
              }
            ]
          }
        }
      }

      mockApiClient.post.mockRejectedValue(validationError)

      await expect(ticketService.createTicket(ticketData)).rejects.toThrow()
    })
  })
})
```

### Integration Testing

```typescript
// Example: E2E API Integration Tests
describe('Frontend-Backend Integration', () => {
  beforeEach(async () => {
    // Set up test environment
    await setupTestDatabase()
    await startTestServer()
  })

  afterEach(async () => {
    await cleanupTestDatabase()
    await stopTestServer()
  })

  it('should complete full ticket lifecycle', async () => {
    // 1. Login
    const loginResponse = await authApiService.login({
      email: 'test@example.com',
      password: 'password123'
    })
    expect(loginResponse.access_token).toBeDefined()

    // 2. Create ticket
    const ticketData: TicketCreate = {
      title: 'Integration Test Ticket',
      description: 'Testing full workflow',
      priority: Priority.HIGH,
      type: TicketType.ISSUE
    }

    const ticket = await ticketApiService.createTicket(ticketData)
    expect(ticket.id).toBeDefined()

    // 3. Add comment
    const comment = await commentsApiService.createComment(ticket.id, {
      content: 'Test comment',
      is_internal: false
    })
    expect(comment.id).toBeDefined()

    // 4. Update status
    const updatedTicket = await ticketApiService.updateTicketStatus(ticket.id, {
      status: TicketStatus.IN_PROGRESS
    })
    expect(updatedTicket.status).toBe(TicketStatus.IN_PROGRESS)

    // 5. Close ticket
    const closedTicket = await ticketApiService.updateTicketStatus(ticket.id, {
      status: TicketStatus.RESOLVED
    })
    expect(closedTicket.status).toBe(TicketStatus.RESOLVED)
  })
})
```
