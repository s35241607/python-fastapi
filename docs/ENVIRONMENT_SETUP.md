# Environment Setup and Version Verification Guide

## Version Requirements Summary

This document helps you verify and upgrade all project dependencies to the required versions.

### Required Versions
- **Python**: 3.13+
- **Node.js**: 22+
- **PostgreSQL**: 16+
- **Docker**: 24+ (optional)
- **uv**: 0.4+ (Python package manager)

### Frontend Package Versions (Updated)
- **Vue**: 3.5+
- **TypeScript**: 5.7+
- **Vite**: 7.1+
- **Vue Router**: 4.4+
- **Pinia**: 2.2+
- **Axios**: 1.7+

## Step-by-Step Version Verification

### 1. Python Version Check and Upgrade

#### Check Current Version
```bash
python --version
python -c "import sys; print(f'Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
```

#### Expected Output
```
Python 3.13.0 (or higher)
```

#### Upgrade Python (if needed)
```bash
# Windows - using Chocolatey
choco upgrade python

# Windows - using winget
winget install Python.Python.3.13

# Or download directly from https://www.python.org/downloads/
```

#### Verify Python Configuration
```bash
# Check if Python is in PATH
where python

# Verify pip is available
pip --version

# Check Python installation location
python -c "import sys; print(sys.executable)"
```

### 2. Node.js Version Check and Upgrade

#### Check Current Version
```bash
node --version
npm --version
```

#### Expected Output
```
v22.x.x (or higher)
11.x.x (or higher)
```

#### Upgrade Node.js (if needed)
```bash
# Windows - using Chocolatey
choco upgrade nodejs

# Windows - using winget
winget install OpenJS.NodeJS

# Or download LTS from https://nodejs.org/
```

#### Verify Node.js Configuration
```bash
# Check Node.js installation path
where node
where npm

# Check npm configuration
npm config list
```

### 3. PostgreSQL Version Check and Upgrade

#### Check Current Version
```bash
# If PostgreSQL is installed locally
psql --version

# If using Docker
docker run --rm postgres:16 psql --version
```

#### Expected Output
```
psql (PostgreSQL) 16.x
```

#### Install/Upgrade PostgreSQL

**Option 1: Local Installation**
```bash
# Windows - using Chocolatey
choco install postgresql16

# Windows - using installer
# Download from https://www.postgresql.org/download/windows/
```

**Option 2: Docker (Recommended for Development)**
```bash
# PostgreSQL 16 is already configured in docker-compose.yml
docker-compose up -d postgres

# Verify PostgreSQL version in Docker
docker exec postgres_db psql --version
```

### 4. uv Package Manager Setup

#### Check Current Version
```bash
uv --version
```

#### Expected Output
```
uv 0.4.x (or higher)
```

#### Install/Upgrade uv
```bash
# Windows - PowerShell (recommended)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative - using pip
pip install --upgrade uv

# Verify installation
uv --version
which uv  # or 'where uv' on Windows
```

### 5. Docker Version Check (Optional)

#### Check Current Version
```bash
docker --version
docker-compose --version
```

#### Expected Output
```
Docker version 24.x.x (or higher)
Docker Compose version 2.x.x (or higher)
```

#### Install Docker Desktop
```bash
# Download from https://www.docker.com/products/docker-desktop/
# Install Docker Desktop for Windows
```

## Project Dependency Updates

### Backend Dependencies Verification

#### Check Current Backend Configuration
```bash
cd backend

# Verify pyproject.toml has been updated
cat pyproject.toml | grep "requires-python"
cat pyproject.toml | grep -A 2 "\[tool.black\]"
cat pyproject.toml | grep -A 2 "\[tool.mypy\]"
```

#### Expected Configuration
```toml
requires-python = ">=3.13"

[tool.black]
line-length = 88
target-version = ['py313']

[tool.mypy]
python_version = "3.13"
```

#### Install/Update Backend Dependencies
```bash
cd backend

# Install dependencies with uv
uv sync

# Verify Python environment
uv run python --version

# Test backend dependencies
uv run python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"
uv run python -c "import sqlalchemy; print(f'SQLAlchemy version: {sqlalchemy.__version__}')"
```

### Frontend Dependencies Verification

#### Check Updated Package.json
```bash
cd frontend

# Verify package.json has been updated
cat package.json | grep -A 10 '"dependencies"'
cat package.json | grep -A 15 '"devDependencies"'
```

#### Expected Dependencies (Updated)
```json
{
  "dependencies": {
    "vue": "^3.5.19",
    "vue-router": "^4.4.0",
    "pinia": "^2.2.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@vitejs/plugin-vue": "^6.0.1",
    "@vue/eslint-config-prettier": "^10.0.0",
    "@vue/eslint-config-typescript": "^13.0.0",
    "@vue/tsconfig": "^0.5.0",
    "eslint": "^8.57.0",
    "eslint-plugin-vue": "^9.30.0",
    "prettier": "^3.4.0",
    "typescript": "^5.7.0",
    "vite": "^7.1.3",
    "vue-tsc": "^2.2.0"
  }
}
```

#### Install/Update Frontend Dependencies
```bash
cd frontend

# Remove old node_modules to ensure clean install
rm -rf node_modules package-lock.json

# Install updated dependencies
npm install

# Verify key package versions
npm list vue vue-router vite typescript
```

## Environment Configuration

### Create Backend Environment File
```bash
cd backend

# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
# Use your preferred text editor (e.g., code, notepad, vim)
code .env
```

### Sample .env Configuration
```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/myapp
POSTGRES_DB=myapp
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Application Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ENVIRONMENT=development
DEBUG=True

# Server Configuration
HOST=0.0.0.0
PORT=8000

# CORS Configuration (for frontend development)
ALLOWED_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# Logging Configuration
LOG_LEVEL=INFO
```

## Verification Tests

### 1. Backend Verification
```bash
cd backend

# Test Python environment
uv run python --version

# Test dependency imports
uv run python -c "
import asyncio
import fastapi
import sqlalchemy
import pydantic
print('✓ All backend dependencies imported successfully')
"

# Test application startup
uv run uvicorn app.main:app --reload --port 8001 &
sleep 5
curl -s http://localhost:8001/health || echo "❌ Backend health check failed"
pkill -f uvicorn  # Stop the test server
```

### 2. Frontend Verification
```bash
cd frontend

# Test Node.js and npm
node --version
npm --version

# Test TypeScript compilation
npm run type-check

# Test build process
npm run build

# Verify build output
ls -la dist/
```

### 3. Full Stack Verification with Docker
```bash
# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Check service status
docker-compose ps

# Test backend health
curl -s http://localhost:8000/health

# Test frontend availability
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# Clean up
docker-compose down
```

## Troubleshooting Common Issues

### Python Issues

**Issue**: Wrong Python version active
```bash
# Solution: Check Python installation and PATH
python --version
which python  # Linux/Mac
where python   # Windows

# If multiple Python versions, use specific version
python3.13 --version
```

**Issue**: uv not found after installation
```bash
# Solution: Restart terminal or add to PATH
# On Windows, restart PowerShell/Command Prompt
# Or manually add uv to PATH
```

### Node.js Issues

**Issue**: npm install fails with permission errors
```bash
# Solution: Clear npm cache and try again
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

**Issue**: Old package versions after update
```bash
# Solution: Force reinstall packages
npm ci  # Clean install based on package-lock.json
# Or
rm -rf node_modules package-lock.json
npm install
```

### Database Issues

**Issue**: PostgreSQL connection refused
```bash
# Solution 1: Start PostgreSQL service
# Windows Services: Start PostgreSQL service
# Docker: docker-compose up -d postgres

# Solution 2: Check connection settings
psql -h localhost -p 5432 -U postgres -d myapp
```

### Docker Issues

**Issue**: Docker containers won't start
```bash
# Solution: Check Docker daemon and cleanup
docker system info
docker system prune -f
docker-compose down --volumes
docker-compose up -d --build
```

## Quick Verification Script

Create and run this verification script to check all components:

```bash
#!/bin/bash
# save as verify_setup.sh

echo "🔍 Verifying Development Environment Setup"
echo "========================================"

echo "📦 Checking Python..."
python --version || echo "❌ Python not found"

echo "📦 Checking Node.js..."
node --version || echo "❌ Node.js not found"

echo "📦 Checking uv..."
uv --version || echo "❌ uv not found"

echo "📦 Checking Docker..."
docker --version || echo "❌ Docker not found"

echo "📦 Checking PostgreSQL..."
psql --version || echo "❌ PostgreSQL not found"

echo ""
echo "🔧 Checking Project Dependencies..."

cd backend
echo "Backend Python version:"
uv run python --version

cd ../frontend
echo "Frontend Node version:"
node --version

echo ""
echo "✅ Environment verification complete!"
```

Run the script:
```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

This completes the environment setup and version verification. All components are now configured to use the latest stable versions as requested.