#!/bin/bash

# Enterprise Ticket Management System - Production Deployment Script
# This script sets up the complete production environment with Docker

set -e

echo "🚀 Enterprise Ticket Management System - Production Deployment"
echo "=============================================================="

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "Environment file not found. Creating from template..."
        cp "$PROJECT_ROOT/.env.template" "$ENV_FILE"
        log_error "Please edit $ENV_FILE with your configuration and run this script again."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    # Create Docker volume directories
    sudo mkdir -p /var/lib/docker/volumes/tickets/{postgres,redis,uploads,logs}
    sudo mkdir -p /var/log/tickets
    sudo mkdir -p "$PROJECT_ROOT/ssl"
    sudo mkdir -p "$PROJECT_ROOT/backups"
    
    # Set proper permissions
    sudo chown -R $USER:$USER /var/lib/docker/volumes/tickets
    sudo chown -R $USER:$USER /var/log/tickets
    sudo chown -R $USER:$USER "$PROJECT_ROOT/ssl"
    sudo chown -R $USER:$USER "$PROJECT_ROOT/backups"
    
    log_success "Directories created successfully"
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certificates() {
    log_info "Generating SSL certificates..."
    
    if [ ! -f "$PROJECT_ROOT/ssl/tickets.crt" ]; then
        log_warning "Generating self-signed SSL certificates for development..."
        log_warning "For production, replace with proper certificates from a CA"
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$PROJECT_ROOT/ssl/tickets.key" \
            -out "$PROJECT_ROOT/ssl/tickets.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=tickets.localhost"
        
        chmod 600 "$PROJECT_ROOT/ssl/tickets.key"
        chmod 644 "$PROJECT_ROOT/ssl/tickets.crt"
        
        log_success "Self-signed SSL certificates generated"
    else
        log_success "SSL certificates already exist"
    fi
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Create database initialization script
    cat > "$PROJECT_ROOT/database/init/01-init.sql" << 'EOF'
-- Initialize database for Enterprise Ticket Management System

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create database user if not exists (for additional security)
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'tickets_app') THEN
      CREATE ROLE tickets_app LOGIN PASSWORD 'app_password';
   END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE ticketsystem TO tickets_app;
GRANT USAGE ON SCHEMA public TO tickets_app;
GRANT CREATE ON SCHEMA public TO tickets_app;

-- Create audit function for tracking changes
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (entity_type, entity_id, action, changes, created_by, created_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'created', row_to_json(NEW), NEW.created_by_id, NOW());
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (entity_type, entity_id, action, changes, created_by, created_at)
        VALUES (TG_TABLE_NAME, NEW.id, 'updated', 
                json_build_object('old', row_to_json(OLD), 'new', row_to_json(NEW)), 
                COALESCE(NEW.updated_by_id, NEW.created_by_id), NOW());
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (entity_type, entity_id, action, changes, created_by, created_at)
        VALUES (TG_TABLE_NAME, OLD.id, 'deleted', row_to_json(OLD), OLD.created_by_id, NOW());
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Performance optimization settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
EOF

    log_success "Database initialization script created"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log_info "Building backend image..."
    docker build -f backend/Dockerfile.prod -t tickets/backend:1.0.0 backend/
    
    # Build frontend image
    log_info "Building frontend image..."
    docker build -f frontend/Dockerfile.prod -t tickets/frontend:1.0.0 frontend/
    
    log_success "Docker images built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    # Start core services first
    log_info "Starting database and cache services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres redis
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 30
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d backend frontend
    
    # Wait for application to be ready
    log_info "Waiting for application to be ready..."
    sleep 20
    
    # Start monitoring and logging services
    log_info "Starting monitoring services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d prometheus grafana
    
    # Start logging services
    log_info "Starting logging services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d elasticsearch kibana logstash
    
    # Start additional services
    log_info "Starting additional services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d loadbalancer backup worker
    
    log_success "All services started successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for backend to be fully ready
    sleep 10
    
    # Run migrations inside the backend container
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec backend python -m alembic upgrade head
    
    log_success "Database migrations completed"
}

# Create initial admin user
create_admin_user() {
    log_info "Creating initial admin user..."
    
    # Create admin user script
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec backend python -c "
import asyncio
from app.services.auth_service import AuthService
from app.database import get_db

async def create_admin():
    async for db in get_db():
        auth_service = AuthService(db)
        admin_data = {
            'username': 'admin',
            'email': 'admin@company.com',
            'password': 'ChangeMe123!',
            'first_name': 'System',
            'last_name': 'Administrator',
            'role': 'super_admin',
            'is_active': True
        }
        user = await auth_service.register_user(admin_data)
        print(f'Admin user created with ID: {user.id}')
        break

asyncio.run(create_admin())
"
    
    log_success "Initial admin user created (username: admin, password: ChangeMe123!)"
    log_warning "Please change the admin password after first login!"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check if services are running
    services=(postgres redis backend frontend prometheus grafana)
    
    for service in "${services[@]}"; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "$service.*Up"; then
            log_success "$service is running"
        else
            log_error "$service is not running"
            return 1
        fi
    done
    
    # Check health endpoints
    log_info "Checking health endpoints..."
    
    sleep 10
    
    # Backend health check
    if curl -f http://localhost:8000/health &> /dev/null; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check failed"
    fi
    
    # Frontend health check
    if curl -f http://localhost/health &> /dev/null; then
        log_success "Frontend health check passed"
    else
        log_warning "Frontend health check failed"
    fi
    
    log_success "Deployment verification completed"
}

# Show deployment summary
show_summary() {
    echo
    echo "🎉 Deployment completed successfully!"
    echo "====================================="
    echo
    echo "📋 Service URLs:"
    echo "  • Main Application: http://localhost (Frontend)"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Grafana Monitoring: http://localhost:3000 (admin/admin)"
    echo "  • Kibana Logs: http://localhost:5601"
    echo "  • Prometheus: http://localhost:9090"
    echo "  • HAProxy Stats: http://localhost:8080/stats"
    echo
    echo "🔐 Default Credentials:"
    echo "  • Admin User: admin / ChangeMe123!"
    echo "  • Grafana: admin / admin"
    echo
    echo "📁 Important Directories:"
    echo "  • Data: /var/lib/docker/volumes/tickets/"
    echo "  • Logs: /var/log/tickets/"
    echo "  • Backups: $PROJECT_ROOT/backups/"
    echo "  • SSL: $PROJECT_ROOT/ssl/"
    echo
    echo "🛠️  Management Commands:"
    echo "  • View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f [service]"
    echo "  • Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "  • Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart [service]"
    echo "  • Update services: docker-compose -f $DOCKER_COMPOSE_FILE pull && docker-compose -f $DOCKER_COMPOSE_FILE up -d"
    echo
    echo "⚠️  Next Steps:"
    echo "  1. Change the default admin password"
    echo "  2. Configure proper SSL certificates for production"
    echo "  3. Update environment variables in .env file"
    echo "  4. Set up external backups and monitoring"
    echo "  5. Review and customize configuration files"
    echo
}

# Cleanup function for interrupted deployments
cleanup() {
    log_warning "Deployment interrupted. Cleaning up..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    exit 1
}

# Main deployment process
main() {
    # Set up signal handling
    trap cleanup INT TERM
    
    echo "Starting deployment process..."
    echo
    
    check_prerequisites
    create_directories
    generate_ssl_certificates
    init_database
    build_images
    start_services
    run_migrations
    create_admin_user
    verify_deployment
    show_summary
    
    log_success "Enterprise Ticket Management System deployed successfully!"
}

# Run the deployment
main "$@"