# Python-FastAPI Project Documentation Setup

## Overview

This document provides comprehensive project documentation for the Python-FastAPI full-stack application, including development guidelines, usage instructions, and architectural specifications. The project implements a modern frontend-backend separation architecture using Vue.js and FastAPI.

**Project Type**: Full-Stack Application
**Architecture Pattern**: Layered architecture with clear separation between frontend, backend, and database layers
**Target Environment**: Development and production deployment with Docker containerization

## Technology Stack

### Backend Stack
- **Framework**: FastAPI (Python 3.13+)
- **ORM**: SQLAlchemy (Asynchronous)
- **Database**: PostgreSQL 16
- **Package Manager**: uv
- **ASGI Server**: Uvicorn
- **Validation**: Pydantic v2
- **API Documentation**: Swagger/OpenAPI

### Frontend Stack
- **Framework**: Vue 3.4+ + TypeScript 5.3+
- **Build Tool**: Vite 5.x
- **State Management**: Pinia 2.1+
- **HTTP Client**: Axios 1.6+
- **Routing**: Vue Router 4.2+
- **Package Manager**: npm (Node.js 20+)

### Development Tools
- **Containerization**: Docker + Docker Compose
- **IDE**: VS Code with debugging support
- **Code Formatting**: Black (Python), Prettier (JavaScript/TypeScript), ESLint
- **Version Control**: Git
- **Type Checking**: mypy (Python), vue-tsc (TypeScript)

## Architecture

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
    end

    subgraph "Frontend Layer"
        Vue[Vue.js Application<br/>Port: 5173]
        VueRouter[Vue Router]
        Pinia[Pinia State Management]
        Axios[Axios HTTP Client]
    end

    subgraph "Backend Layer"
        FastAPI[FastAPI Application<br/>Port: 8000]
        Middleware[Middleware Pipeline]
        Routers[API Routers]
        Services[Business Logic]
        Repositories[Data Access Layer]
    end

    subgraph "Database Layer"
        PostgreSQL[(PostgreSQL<br/>Port: 5432)]
    end

    Browser --> Vue
    Vue --> VueRouter
    Vue --> Pinia
    Vue --> Axios
    Axios --> FastAPI
    FastAPI --> Middleware
    Middleware --> Routers
    Routers --> Services
    Services --> Repositories
    Repositories --> PostgreSQL
```

### Component Architecture

#### Frontend Component Hierarchy
```mermaid
graph TD
    App[App.vue - Root Component]
    Router[Vue Router]
    Home[Home.vue]
    Users[Users.vue]
    API[API Service]

    App --> Router
    Router --> Home
    Router --> Users
    Home --> API
    Users --> API
```

#### Backend Service Architecture
```mermaid
graph TD
    Main[main.py - Application Entry]
    Config[Configuration System]
    Middleware[Middleware Pipeline]
    Routers[API Routers]
    Models[Data Models]
    Schemas[Pydantic Schemas]
    Database[Database Connection]

    Main --> Config
    Main --> Middleware
    Main --> Routers
    Routers --> Models
    Routers --> Schemas
    Models --> Database
```

## Project Structure

```
python-fastapi/
├── backend/                          # FastAPI Backend Application
│   ├── app/                         # Backend Source Code
│   │   ├── core/                    # Core Configuration
│   │   │   ├── config.py           # Application Configuration
│   │   │   ├── logging.py          # Logging Setup
│   │   │   └── middleware.py       # Middleware Components
│   │   ├── repositories/           # Data Access Layer
│   │   │   └── base_repository.py  # Base Repository Pattern
│   │   ├── routers/                # API Route Handlers
│   │   │   ├── items.py           # Item API Endpoints
│   │   │   └── users.py           # User API Endpoints
│   │   ├── database.py             # Database Connection Setup
│   │   ├── main.py                 # FastAPI Application Entry Point
│   │   ├── models.py               # SQLAlchemy Data Models
│   │   └── schemas.py              # Pydantic Request/Response Schemas
│   ├── scripts/                    # Development Scripts
│   │   ├── dev.bat                # Development Startup Script
│   │   ├── prod.bat               # Production Startup Script
│   │   └── test.bat               # Test Execution Script
│   ├── Dockerfile                  # Backend Container Configuration
│   ├── README.md                   # Backend Development Guide
│   ├── init.sql                    # Database Initialization Script
│   └── pyproject.toml              # Python Dependencies and Configuration
├── frontend/                       # Vue.js Frontend Application
│   ├── src/                        # Frontend Source Code
│   │   ├── router/                 # Vue Router Configuration
│   │   │   └── index.ts           # Route Definitions
│   │   ├── services/               # API Service Layer
│   │   │   └── api.ts             # HTTP Client Configuration
│   │   ├── views/                  # Vue Components/Pages
│   │   │   ├── Home.vue           # Home Page Component
│   │   │   └── Users.vue          # Users Page Component
│   │   ├── App.vue                 # Root Vue Component
│   │   ├── env.d.ts               # TypeScript Environment Declarations
│   │   └── main.ts                # Frontend Application Entry Point
│   ├── Dockerfile                  # Frontend Container Configuration
│   ├── README.md                   # Frontend Development Guide
│   ├── index.html                  # HTML Template
│   ├── package.json                # Node.js Dependencies
│   ├── tsconfig.json               # TypeScript Configuration
│   └── vite.config.ts              # Vite Build Configuration
├── .vscode/                        # VS Code IDE Configuration
├── docs/                           # Project Documentation
├── docker-compose.yml              # Docker Orchestration Configuration
├── DEBUG_GUIDE.md                  # Debugging Instructions
├── start-backend-debug.ps1         # Backend Debug Script
├── start-frontend-debug.ps1        # Frontend Debug Script
└── README.md                       # Project Overview
```

## Development Guidelines

### Code Standards

#### Python (Backend) Standards
- **Code Formatter**: Black with 88-character line length
- **Linter**: flake8 for code quality and style
- **Type Checking**: mypy for static type analysis
- **Import Sorting**: isort for consistent import organization
- **Testing Framework**: pytest with pytest-asyncio for async tests

```bash
# Format code
uv run black app/

# Check code quality
uv run flake8 app/

# Type checking
uv run mypy app/

# Sort imports
uv run isort app/

# Run tests
uv run pytest
```

#### TypeScript/JavaScript (Frontend) Standards
- **Code Formatter**: Prettier
- **Linter**: ESLint with Vue and TypeScript integration
- **Type Checking**: vue-tsc for Vue Single File Components
- **Style Guide**: Vue ESLint configuration

```bash
# Format code
npm run format

# Lint code
npm run lint

# Type checking
npm run type-check

# Run tests (if configured)
npm run test
```

### Naming Conventions

#### Backend Naming Conventions
- **Files**: snake_case (e.g., `user_repository.py`)
- **Classes**: PascalCase (e.g., `UserRepository`)
- **Functions/Methods**: snake_case (e.g., `get_user_by_id`)
- **Variables**: snake_case (e.g., `user_data`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DATABASE_URL`)

#### Frontend Naming Conventions
- **Files**: kebab-case for components (e.g., `user-list.vue`)
- **Classes**: PascalCase (e.g., `UserService`)
- **Functions/Methods**: camelCase (e.g., `getUserById`)
- **Variables**: camelCase (e.g., `userData`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

### Git Workflow

#### Branch Naming
- **Feature**: `feature/description` (e.g., `feature/user-authentication`)
- **Bugfix**: `bugfix/description` (e.g., `bugfix/login-error`)
- **Hotfix**: `hotfix/description` (e.g., `hotfix/security-patch`)

#### Commit Message Format
```
type(scope): brief description

Detailed explanation of the change (optional)

- List of changes (optional)
- Breaking changes (if any)
```

**Types**: feat, fix, docs, style, refactor, test, chore

Example:
```
feat(auth): add JWT token authentication

- Implement JWT token generation and validation
- Add middleware for protected routes
- Update user model with authentication fields
```

## Development Environment Setup

### Prerequisites
- **Node.js** 20+ (LTS recommended for frontend development)
- **Python** 3.13+ (for backend development)
- **PostgreSQL** 16+ (database)
- **uv** 0.4+ (Python package manager)
- **VS Code** (recommended IDE)
- **Docker** 24+ (optional, for containerized development)

### Initial Setup

#### Version Verification and Upgrades

Before starting development, ensure all components are using the latest recommended versions:

**Backend Version Updates:**
```bash
# Check current Python version
python --version  # Should be 3.13+

# Update pyproject.toml Python version requirements
# Current: requires-python = ">=3.13" ✓ (Already correct)
# Update tool configurations to match:
[tool.black]
target-version = ['py313']

[tool.mypy]
python_version = "3.13"
```

**Frontend Version Updates:**
```bash
# Check current Node.js version
node --version  # Should be 20+
npm --version   # Should be 10+

# Update package.json dependencies to latest versions:
cd frontend

# Update Vue ecosystem to latest versions
npm update vue@^3.4.0
npm update vue-router@^4.2.0
npm update pinia@^2.1.0
npm update @vitejs/plugin-vue@^5.0.0
npm update vite@^5.0.0
npm update typescript@^5.3.0
npm update axios@^1.6.0

# Or use npm-check-updates for automated updates
npx npm-check-updates -u
npm install
```

**Database Version Verification:**
```bash
# PostgreSQL 16 is already correctly configured in docker-compose.yml
# Current: image: postgres:16 ✓ (Already correct)

# For local PostgreSQL installation, verify version:
psql --version  # Should show PostgreSQL 16.x
```

#### 1. Clone Repository
```bash
git clone <repository-url>
cd python-fastapi
```

#### 2. Backend Environment Setup
```bash
cd backend

# Verify Python version compatibility
python --version  # Should be 3.13+

# Install Python dependencies
uv sync

# Fix version inconsistencies in pyproject.toml
# Update the following sections to match Python 3.13:
# [tool.black]
# target-version = ['py313']
#
# [tool.mypy]
# python_version = "3.13"

# Copy environment template
copy .env.example .env

# Edit .env file with your database configuration
# Example .env content:
# DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/dbname
# SECRET_KEY=your-secret-key-here
# ENVIRONMENT=development

# Initialize database (if needed)
# Run init.sql script in your PostgreSQL instance

# Start development server
uv run uvicorn app.main:app --reload
```

#### 3. Frontend Environment Setup
```bash
cd frontend

# Install Node.js dependencies with latest versions
npm install

# Recommended package.json updates for latest versions:
# {
#   "dependencies": {
#     "vue": "^3.4.0",
#     "vue-router": "^4.2.0",
#     "pinia": "^2.1.0",
#     "axios": "^1.6.0"
#   },
#   "devDependencies": {
#     "@types/node": "^20.10.0",
#     "@vitejs/plugin-vue": "^5.0.0",
#     "@vue/eslint-config-prettier": "^9.0.0",
#     "@vue/eslint-config-typescript": "^12.0.0",
#     "@vue/tsconfig": "^0.5.0",
#     "eslint": "^8.56.0",
#     "eslint-plugin-vue": "^9.19.0",
#     "prettier": "^3.1.0",
#     "typescript": "^5.3.0",
#     "vite": "^5.0.0",
#     "vue-tsc": "^1.8.0"
#   }
# }

# Start development server
npm run dev
```

### Development Workflow

#### Daily Development Process

1. **Start Development Environment**
   ```bash
   # Terminal 1: Backend
   cd backend
   uv run uvicorn app.main:app --reload

   # Terminal 2: Frontend
   cd frontend
   npm run dev
   ```

2. **Code Quality Checks**
   ```bash
   # Backend formatting and linting
   cd backend
   uv run black app/
   uv run flake8 app/
   uv run mypy app/

   # Frontend formatting and linting
   cd frontend
   npm run lint
   npm run format
   ```

3. **Testing**
   ```bash
   # Backend tests
   cd backend
   uv run pytest

   # Frontend tests (if configured)
   cd frontend
   npm run test
   ```

#### VS Code Debugging Setup

The project includes VS Code debugging configurations for both frontend and backend:

**Available Debug Configurations:**
- `Python: FastAPI Debug` - Backend debugging with hot reload
- `Vue.js: Debug` - Frontend debugging with source maps
- `Launch Full Stack` - Simultaneous frontend and backend debugging

**To start debugging:**
1. Open the project in VS Code
2. Install recommended extensions
3. Press F5 and select the desired configuration
4. Set breakpoints in your code
5. Debug with full IDE support

#### Docker Development Environment

```bash
# Start all services (frontend + backend + database)
docker-compose up -d

# View service status
docker-compose ps

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and restart services
docker-compose up -d --build
```

## API Reference

### Base Configuration
- **Backend URL**: `http://localhost:8000`
- **Frontend URL**: `http://localhost:5173`
- **API Documentation**: `http://localhost:8000/docs` (Swagger UI)
- **Alternative API Docs**: `http://localhost:8000/redoc` (ReDoc)

### Authentication Flow
```mermaid
sequenceDiagram
    participant Client as Frontend Client
    participant API as FastAPI Backend
    participant DB as PostgreSQL Database

    Client->>API: POST /auth/login
    API->>DB: Validate credentials
    DB-->>API: User data
    API-->>Client: JWT token

    Client->>API: GET /protected-endpoint
    Note over Client,API: Authorization: Bearer <token>
    API->>API: Validate JWT token
    API->>DB: Fetch data
    DB-->>API: Response data
    API-->>Client: Protected data
```

### Core API Endpoints

#### User Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/users` | List all users | Yes |
| GET | `/api/users/{user_id}` | Get user by ID | Yes |
| POST | `/api/users` | Create new user | Yes |
| PUT | `/api/users/{user_id}` | Update user | Yes |
| DELETE | `/api/users/{user_id}` | Delete user | Yes |

#### Item Management
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/items` | List all items | Yes |
| GET | `/api/items/{item_id}` | Get item by ID | Yes |
| POST | `/api/items` | Create new item | Yes |
| PUT | `/api/items/{item_id}` | Update item | Yes |
| DELETE | `/api/items/{item_id}` | Delete item | Yes |

#### Health Check
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Service health status | No |

## Data Models

### User Model Schema
```mermaid
erDiagram
    User {
        int id PK
        string email UK
        string username UK
        string hashed_password
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    Item {
        int id PK
        string title
        string description
        int owner_id FK
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    User ||--o{ Item : owns
```

### Request/Response Schemas

#### User Schemas
```python
# User Creation Request
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str

# User Response
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime
```

#### Item Schemas
```python
# Item Creation Request
class ItemCreate(BaseModel):
    title: str
    description: str

# Item Response
class ItemResponse(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    is_active: bool
    created_at: datetime
```

## Testing Strategy

### Backend Testing

#### Unit Testing with Pytest
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_users.py

# Run with verbose output
uv run pytest -v
```

#### Test Structure
```
backend/tests/
├── __init__.py
├── conftest.py                  # Pytest configuration and fixtures
├── test_auth.py                 # Authentication tests
├── test_users.py               # User API tests
├── test_items.py               # Item API tests
├── test_database.py            # Database operation tests
└── test_repositories.py       # Repository layer tests
```

#### Example Test Case
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123"
    }
    response = await client.post("/api/users", json=user_data)
    assert response.status_code == 201
    assert response.json()["email"] == user_data["email"]
```

### Frontend Testing

#### Testing Framework Options
- **Unit Testing**: Vitest (recommended for Vite projects)
- **Component Testing**: Vue Test Utils
- **E2E Testing**: Cypress or Playwright

#### Test Configuration (if implemented)
```bash
# Unit tests
npm run test:unit

# E2E tests
npm run test:e2e

# All tests
npm run test
```

## Deployment Configuration

### Environment Variables

#### Backend Environment Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Security
SECRET_KEY=your-super-secure-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "https://yourdomain.com"]
```

#### Frontend Environment Variables
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Application Settings
VITE_APP_TITLE=Python FastAPI App
VITE_APP_VERSION=1.0.0
```

### Docker Deployment

#### Production Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/production_db
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - db
    restart: unless-stopped

  frontend:
    build: ./frontend
    environment:
      - VITE_API_BASE_URL=http://backend:8000
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=production_db
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  postgres_data:
```

### Production Deployment Checklist

#### Security Hardening
- [ ] Use strong, randomly generated SECRET_KEY
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS with SSL certificates
- [ ] Use environment variables for all secrets
- [ ] Implement rate limiting
- [ ] Add security headers middleware

#### Performance Optimization
- [ ] Use production ASGI server (e.g., Gunicorn with Uvicorn workers)
- [ ] Configure database connection pooling
- [ ] Enable frontend asset minification and compression
- [ ] Implement caching strategies (Redis)
- [ ] Configure CDN for static assets

#### Monitoring and Logging
- [ ] Configure structured logging
- [ ] Set up health check endpoints
- [ ] Implement application monitoring (APM)
- [ ] Configure log aggregation
- [ ] Set up alerting for critical errors

## Troubleshooting Guide

### Common Development Issues

#### Version-Related Issues

**Issue**: Python version inconsistency in pyproject.toml
```bash
# Current issue: requires-python = ">=3.13" but tools configured for 3.11
# Solution: Update tool configurations in pyproject.toml:

[tool.black]
target-version = ['py313']  # Changed from py311

[tool.mypy]
python_version = "3.13"     # Changed from 3.11

# Then sync dependencies
uv sync
```

**Issue**: Outdated frontend dependencies
```bash
# Check for outdated packages
cd frontend
npm outdated

# Update to latest compatible versions
npm update

# Or use npm-check-updates for major version updates
npx npm-check-updates -u
npm install

# Verify Vite compatibility
npm ls vite
```

**Issue**: Node.js version compatibility
```bash
# Check current Node.js version
node --version

# If below 20, update Node.js:
# - Use Node Version Manager (nvm) for easy switching
# - Download from https://nodejs.org (LTS version)
# - Update npm after Node.js update
npm install -g npm@latest
```

#### Backend Issues

**Issue**: Cannot connect to database
```bash
# Check PostgreSQL service status
systemctl status postgresql

# Verify database connection
uv run python -c "from app.database import engine; print('Connection successful')"

# Check environment variables
echo $DATABASE_URL
```

**Issue**: Import errors or dependency conflicts
```bash
# Sync dependencies
uv sync

# Clean and reinstall
rm -rf .venv
uv sync

# Check Python version
python --version
```

#### Frontend Issues

**Issue**: Cannot connect to backend API
```bash
# Check backend server status
curl http://localhost:8000/health

# Verify API configuration
cat src/services/api.ts

# Check browser console for CORS errors
# Open Developer Tools > Console
```

**Issue**: TypeScript compilation errors
```bash
# Check TypeScript configuration
npm run type-check

# Update type definitions
npm update @types/*

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

#### Docker Issues

**Issue**: Container build failures
```bash
# Check Docker daemon
docker info

# Build with verbose output
docker-compose build --no-cache --progress=plain

# Check container logs
docker-compose logs backend
docker-compose logs frontend
```

### Performance Optimization

#### Backend Performance
- Use async/await for all I/O operations
- Implement database connection pooling
- Add caching for frequently accessed data
- Optimize database queries with proper indexing
- Use background tasks for time-consuming operations

#### Frontend Performance
- Implement code splitting with dynamic imports
- Optimize bundle size with tree shaking
- Use lazy loading for routes and components
- Implement service worker for caching
- Optimize API calls with request deduplication

### Security Best Practices

#### Backend Security
- Validate all input data using Pydantic models
- Implement proper error handling without information leakage
- Use parameterized queries to prevent SQL injection
- Implement rate limiting for API endpoints
- Regular security audits of dependencies

#### Frontend Security
- Sanitize user input to prevent XSS attacks
- Implement Content Security Policy (CSP)
- Use HTTPS for all communications
- Validate data from API responses
- Implement proper session management
