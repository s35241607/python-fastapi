# Usage Guide

## Quick Start

### Prerequisites Installation

#### 1. Install Node.js 20+
```bash
# Windows (using Chocolatey)
choco install nodejs

# Or download from https://nodejs.org/
# Verify installation
node --version  # Should be 20+
npm --version   # Should be 10+
```

#### 2. Install Python 3.13+
```bash
# Windows (using Chocolatey)
choco install python

# Or download from https://python.org/
# Verify installation
python --version  # Should be 3.13+
```

#### 3. Install uv (Python Package Manager)
```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or using pip
pip install uv

# Verify installation
uv --version
```

#### 4. Install PostgreSQL 16
```bash
# Windows (using Chocolatey)
choco install postgresql16

# Or download from https://www.postgresql.org/download/
# Verify installation
psql --version  # Should show PostgreSQL 16.x
```

#### 5. Install Docker (Optional)
```bash
# Download Docker Desktop from https://www.docker.com/products/docker-desktop/
# Verify installation
docker --version
docker-compose --version
```

### Initial Project Setup

#### 1. Clone and Setup Project
```bash
# Clone the repository
git clone <repository-url>
cd python-fastapi

# Create environment files
cd backend
copy .env.example .env
cd ..
```

#### 2. Configure Environment Variables
Edit `backend/.env` with your settings:
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/myapp
POSTGRES_DB=myapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Application Configuration
SECRET_KEY=your-super-secret-key-here
ENVIRONMENT=development
DEBUG=True

# CORS Configuration
ALLOWED_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

## Development Modes

### Option 1: Docker Development (Recommended)
This is the easiest way to get started as it handles all dependencies automatically.

```bash
# Start all services (PostgreSQL + Backend + Frontend)
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs

# Stop all services
docker-compose down
```

### Option 2: Local Development
Run each component locally for full development control.

#### Backend Setup
```bash
cd backend

# Install dependencies
uv sync

# Start PostgreSQL (if not using Docker)
# Make sure PostgreSQL 16 is running locally

# Run database migrations (if applicable)
# uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Backend will be available at http://localhost:8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies (this will use the updated package.json)
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

### Option 3: VS Code Debugging
Use the integrated VS Code debugging for development.

#### Backend Debug
1. Open VS Code in the project root
2. Press `Ctrl+Shift+P` → "Python: Select Interpreter"
3. Choose the uv virtual environment
4. Press `F5` → Select "Python: FastAPI Debug"
5. Backend starts with debugger attached

#### Frontend Debug
1. Press `F5` → Select "Launch Chrome against localhost"
2. Frontend opens in debug mode
3. Set breakpoints in TypeScript/Vue files

#### Full Stack Debug
1. Press `F5` → Select "Launch Full Stack"
2. Both backend and frontend start with debugging enabled

## API Usage Examples

### Using the Interactive API Documentation

1. Start the backend server
2. Open http://localhost:8000/docs in your browser
3. Use the interactive interface to test API endpoints

### Using curl Commands

#### Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

#### User Management
```bash
# Create a user
curl -X POST "http://localhost:8000/api/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "securepassword123"
  }'

# Get all users
curl -X GET "http://localhost:8000/api/users"

# Get specific user
curl -X GET "http://localhost:8000/api/users/1"

# Update user
curl -X PUT "http://localhost:8000/api/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.updated@example.com",
    "username": "johndoe_updated"
  }'

# Delete user
curl -X DELETE "http://localhost:8000/api/users/1"
```

#### Item Management
```bash
# Create an item
curl -X POST "http://localhost:8000/api/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Item",
    "description": "This is a sample item"
  }'

# Get all items
curl -X GET "http://localhost:8000/api/items"

# Get specific item
curl -X GET "http://localhost:8000/api/items/1"
```

### Using Frontend Application

#### Access the Application
1. Navigate to http://localhost:5173
2. You'll see the main application interface

#### Available Pages
- **Home** (`/`): Landing page with project overview
- **Users** (`/users`): User management interface

#### Frontend Features
```typescript
// Example: Using the API service in a Vue component
import { ref } from 'vue'
import api from '@/services/api'

export default {
  setup() {
    const users = ref([])
    const loading = ref(false)

    const fetchUsers = async () => {
      loading.value = true
      try {
        const response = await api.get('/api/users')
        users.value = response.data
      } catch (error) {
        console.error('Error fetching users:', error)
      } finally {
        loading.value = false
      }
    }

    return {
      users,
      loading,
      fetchUsers
    }
  }
}
```

## Database Management

### Using PostgreSQL with Docker
```bash
# Start PostgreSQL container only
docker-compose up -d postgres

# Connect to database
docker exec -it postgres_db psql -U postgres -d myapp

# Basic PostgreSQL commands
# List tables
\dt

# Describe table structure
\d users

# Query data
SELECT * FROM users;

# Exit PostgreSQL
\q
```

### Using Local PostgreSQL
```bash
# Connect to local database
psql -U postgres -d myapp

# Create database (if needed)
createdb -U postgres myapp

# Run initialization script
psql -U postgres -d myapp -f backend/init.sql
```

### Database Migrations (If using Alembic)
```bash
cd backend

# Generate migration
uv run alembic revision --autogenerate -m "Add user table"

# Apply migrations
uv run alembic upgrade head

# Check migration history
uv run alembic history

# Rollback migration
uv run alembic downgrade -1
```

## Testing

### Backend Testing
```bash
cd backend

# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_users.py

# Run tests with verbose output
uv run pytest -v

# Run tests in watch mode (requires pytest-watch)
uv run ptw
```

### Frontend Testing
```bash
cd frontend

# Run unit tests (if configured)
npm run test

# Run tests in watch mode
npm run test:watch

# Run end-to-end tests (if configured)
npm run test:e2e
```

## Code Quality and Formatting

### Backend Code Quality
```bash
cd backend

# Format code with Black
uv run black app/

# Sort imports
uv run isort app/

# Lint code with flake8
uv run flake8 app/

# Type checking with mypy
uv run mypy app/

# Run all quality checks
uv run black app/ && uv run isort app/ && uv run flake8 app/ && uv run mypy app/
```

### Frontend Code Quality
```bash
cd frontend

# Lint and fix code
npm run lint

# Format code with Prettier
npm run format

# Type checking
npm run type-check

# Run all quality checks
npm run lint && npm run format && npm run type-check
```

## Building for Production

### Backend Production Build
```bash
cd backend

# Install production dependencies only
uv sync --no-dev

# Build package (if needed)
uv build

# Start production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Production Build
```bash
cd frontend

# Build for production
npm run build

# Preview production build
npm run preview

# The built files will be in the 'dist' directory
```

### Docker Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production services
docker-compose -f docker-compose.prod.yml up -d

# Check production logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Monitoring and Logs

### Viewing Application Logs

#### Docker Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# View logs with timestamps
docker-compose logs -f -t
```

#### Local Development Logs
```bash
# Backend logs (FastAPI/Uvicorn)
# Logs appear in the terminal where you started the server

# Database logs
# Check PostgreSQL log files or use pgAdmin
```

### Health Checks
```bash
# Check application health
curl http://localhost:8000/health

# Check database connectivity
curl http://localhost:8000/health/db

# Check all service status with Docker
docker-compose ps
```

## Troubleshooting

### Common Issues and Solutions

#### Backend Issues

**Problem**: `ImportError: No module named 'app'`
```bash
# Solution: Ensure you're in the backend directory and uv sync was run
cd backend
uv sync
```

**Problem**: Database connection errors
```bash
# Solution: Check if PostgreSQL is running and credentials are correct
# For Docker:
docker-compose up -d postgres
# Check DATABASE_URL in .env file
```

**Problem**: Port 8000 already in use
```bash
# Solution: Kill the process or use a different port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or start on different port:
uv run uvicorn app.main:app --port 8001
```

#### Frontend Issues

**Problem**: `npm install` fails
```bash
# Solution: Clear npm cache and try again
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Vue compilation errors
```bash
# Solution: Check TypeScript configuration and dependencies
npm run type-check
# Fix any TypeScript errors shown
```

**Problem**: API connection errors
```bash
# Solution: Verify backend is running and CORS is configured
# Check backend logs for CORS errors
# Verify API_BASE_URL in frontend configuration
```

#### Docker Issues

**Problem**: Docker containers won't start
```bash
# Solution: Check Docker daemon and port conflicts
docker system prune
docker-compose down
docker-compose up -d --build
```

**Problem**: Database data not persisting
```bash
# Solution: Check volume mounts in docker-compose.yml
docker-compose down -v  # This will remove volumes
docker-compose up -d
```

### Getting Help

1. **Check the logs** first for error messages
2. **Review the documentation** in the docs/ directory
3. **Check the API documentation** at http://localhost:8000/docs
4. **Verify environment configuration** in .env files
5. **Ensure all services are running** with `docker-compose ps`

### Useful Commands Reference

```bash
# Project setup
git clone <repo> && cd python-fastapi

# Quick start with Docker
docker-compose up -d

# Development mode
# Terminal 1: cd backend && uv run uvicorn app.main:app --reload
# Terminal 2: cd frontend && npm run dev

# Code quality
cd backend && uv run black app/ && uv run flake8 app/
cd frontend && npm run lint && npm run format

# Testing
cd backend && uv run pytest
cd frontend && npm run test

# Production build
cd backend && uv build
cd frontend && npm run build

# Stop everything
docker-compose down
```