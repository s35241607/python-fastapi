# Python-FastAPI Project Documentation

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
- **Framework**: Vue 3.5+ + TypeScript 5.7+
- **Build Tool**: Vite 7.1+
- **State Management**: Pinia 2.2+
- **HTTP Client**: Axios 1.7+
- **Routing**: Vue Router 4.4+
- **Package Manager**: npm (Node.js 22+)

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

## Development Environment Setup

### Prerequisites
- **Node.js** 22+ (LTS recommended for frontend development)
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

## Troubleshooting

### Common Issues

#### Backend Issues
1. **Database Connection Errors**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database exists

2. **Import Errors**
   - Run `uv sync` to install dependencies
   - Check Python version compatibility

#### Frontend Issues
1. **Build Errors**
   - Run `npm install` to update dependencies
   - Clear node_modules and reinstall if needed

2. **API Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS configuration

#### Docker Issues
1. **Container Start Failures**
   - Check port conflicts
   - Verify Docker daemon is running
   - Review docker-compose logs

For more detailed troubleshooting, see the DEBUG_GUIDE.md file.