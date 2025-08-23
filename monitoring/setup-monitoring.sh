#!/bin/bash

# Enterprise Ticket Management System - Monitoring Setup Script
# Sets up comprehensive monitoring and logging for production environment

set -e

echo "🚀 Setting up monitoring and logging for Enterprise Ticket Management System..."

# Configuration
MONITORING_DIR="/opt/enterprise-tickets/monitoring"
LOG_DIR="/var/log/enterprise-tickets"
BACKUP_DIR="/opt/enterprise-tickets/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating monitoring directories..."
    
    mkdir -p $MONITORING_DIR/{prometheus,grafana,elk}
    mkdir -p $LOG_DIR/{fastapi,nginx,postgresql,system}
    mkdir -p $BACKUP_DIR/monitoring
    mkdir -p /etc/prometheus
    mkdir -p /etc/grafana/provisioning/{datasources,dashboards}
    mkdir -p /usr/share/logstash/{pipeline,templates}
    
    log_success "Directories created successfully"
}

# Set up file permissions
setup_permissions() {
    log_info "Setting up file permissions..."
    
    # Prometheus permissions
    chown -R 65534:65534 $MONITORING_DIR/prometheus
    chmod -R 755 $MONITORING_DIR/prometheus
    
    # Grafana permissions  
    chown -R 472:472 $MONITORING_DIR/grafana
    chmod -R 755 $MONITORING_DIR/grafana
    
    # ELK permissions
    chown -R 1000:1000 $MONITORING_DIR/elk
    chmod -R 755 $MONITORING_DIR/elk
    
    # Log directory permissions
    chown -R syslog:adm $LOG_DIR
    chmod -R 750 $LOG_DIR
    
    log_success "Permissions configured successfully"
}

# Install monitoring dependencies
install_dependencies() {
    log_info "Installing monitoring dependencies..."
    
    # Update package list
    apt-get update
    
    # Install required packages
    apt-get install -y \
        curl \
        wget \
        gnupg \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        lsb-release
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        log_info "Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        log_info "Installing Docker Compose..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log_success "Dependencies installed successfully"
}

# Configure system monitoring
configure_system_monitoring() {
    log_info "Configuring system monitoring..."
    
    # Configure log rotation
    cat > /etc/logrotate.d/enterprise-tickets << EOF
$LOG_DIR/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 syslog adm
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
    endscript
}
EOF

    # Configure rsyslog for application logs
    cat > /etc/rsyslog.d/50-enterprise-tickets.conf << EOF
# Enterprise Ticket Management System logging configuration

# FastAPI application logs
:programname, isequal, "enterprise-tickets" $LOG_DIR/fastapi/application.log
& stop

# NGINX access logs
:msg, regex, "enterprise-tickets.*access" $LOG_DIR/nginx/access.log
& stop

# NGINX error logs  
:msg, regex, "enterprise-tickets.*error" $LOG_DIR/nginx/error.log
& stop

# PostgreSQL logs
:programname, isequal, "postgres" $LOG_DIR/postgresql/postgresql.log
& stop
EOF

    # Restart rsyslog
    systemctl restart rsyslog
    
    log_success "System monitoring configured"
}

# Set up health checks
setup_health_checks() {
    log_info "Setting up health check scripts..."
    
    # Create health check script
    cat > /usr/local/bin/enterprise-tickets-health-check << 'EOF'
#!/bin/bash

# Enterprise Ticket Management System Health Check
# Monitors all critical services and sends alerts

SERVICES=("backend" "frontend" "postgres" "redis" "prometheus" "grafana")
ALERT_EMAIL="admin@yourcompany.com"
WEBHOOK_URL="https://hooks.slack.com/your-webhook-url"

check_service() {
    local service=$1
    if docker-compose -f /opt/enterprise-tickets/docker-compose.prod.yml ps $service | grep -q "Up"; then
        echo "✅ $service is healthy"
        return 0
    else
        echo "❌ $service is down"
        return 1
    fi
}

send_alert() {
    local message=$1
    
    # Send email alert
    echo "$message" | mail -s "Enterprise Ticket System Alert" $ALERT_EMAIL
    
    # Send Slack notification
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$message\"}" \
        $WEBHOOK_URL
}

main() {
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        if ! check_service $service; then
            failed_services+=($service)
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        local alert_msg="ALERT: The following services are down: ${failed_services[*]}"
        echo $alert_msg
        send_alert "$alert_msg"
        exit 1
    else
        echo "All services are healthy"
        exit 0
    fi
}

main "$@"
EOF

    chmod +x /usr/local/bin/enterprise-tickets-health-check
    
    # Create cron job for health checks
    cat > /etc/cron.d/enterprise-tickets-health << EOF
# Health check every 5 minutes
*/5 * * * * root /usr/local/bin/enterprise-tickets-health-check >> $LOG_DIR/system/health-check.log 2>&1
EOF

    log_success "Health checks configured"
}

# Configure monitoring alerts
configure_alerts() {
    log_info "Configuring monitoring alerts..."
    
    # Create Alertmanager configuration
    cat > $MONITORING_DIR/prometheus/alertmanager.yml << EOF
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alerts@yourcompany.com'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  email_configs:
  - to: 'admin@yourcompany.com'
    subject: 'Enterprise Ticket System Alert'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}
  slack_configs:
  - api_url: 'https://hooks.slack.com/your-webhook-url'
    channel: '#alerts'
    title: 'Enterprise Ticket System Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
EOF

    log_success "Monitoring alerts configured"
}

# Set up backup monitoring
setup_backup_monitoring() {
    log_info "Setting up backup monitoring..."
    
    # Create backup monitoring script
    cat > /usr/local/bin/backup-monitor << 'EOF'
#!/bin/bash

# Backup Monitoring Script
# Ensures backups are running and alerts on failures

BACKUP_DIR="/opt/enterprise-tickets/backups"
MAX_AGE_HOURS=25  # Alert if backup is older than 25 hours

check_backup_age() {
    local backup_file="$BACKUP_DIR/latest/database.sql"
    
    if [ ! -f "$backup_file" ]; then
        echo "❌ No backup file found"
        return 1
    fi
    
    local backup_age=$((($(date +%s) - $(stat -c %Y "$backup_file")) / 3600))
    
    if [ $backup_age -gt $MAX_AGE_HOURS ]; then
        echo "❌ Backup is $backup_age hours old (max: $MAX_AGE_HOURS)"
        return 1
    else
        echo "✅ Backup is $backup_age hours old"
        return 0
    fi
}

main() {
    echo "Checking backup status..."
    
    if ! check_backup_age; then
        local alert_msg="BACKUP ALERT: Database backup is missing or too old"
        echo "$alert_msg"
        
        # Send alert
        echo "$alert_msg" | mail -s "Backup Alert - Enterprise Ticket System" admin@yourcompany.com
        
        exit 1
    else
        echo "Backup monitoring: All good"
        exit 0
    fi
}

main "$@"
EOF

    chmod +x /usr/local/bin/backup-monitor
    
    # Add backup monitoring to cron
    cat > /etc/cron.d/backup-monitor << EOF
# Check backup status every hour
0 * * * * root /usr/local/bin/backup-monitor >> $LOG_DIR/system/backup-monitor.log 2>&1
EOF

    log_success "Backup monitoring configured"
}

# Create monitoring dashboard URL generator
create_dashboard_urls() {
    log_info "Creating monitoring dashboard shortcuts..."
    
    cat > /usr/local/bin/monitoring-urls << 'EOF'
#!/bin/bash

echo "📊 Enterprise Ticket Management System - Monitoring URLs"
echo "======================================================="
echo "🖥️  Application: https://tickets.yourcompany.com"
echo "📈 Prometheus: http://localhost:9090"
echo "📊 Grafana: http://localhost:3000"
echo "🔍 Kibana: http://localhost:5601"
echo "⚡ Alerts: http://localhost:9093"
echo "🏥 Health: http://localhost:8000/health"
echo "======================================================="
EOF

    chmod +x /usr/local/bin/monitoring-urls
    
    log_success "Dashboard URLs created"
}

# Validate monitoring setup
validate_setup() {
    log_info "Validating monitoring setup..."
    
    local validation_errors=0
    
    # Check if all configuration files exist
    local config_files=(
        "$MONITORING_DIR/prometheus/prometheus.yml"
        "$MONITORING_DIR/prometheus/alert_rules.yml"
        "$MONITORING_DIR/grafana/provisioning/datasources/datasources.yml"
        "/etc/logrotate.d/enterprise-tickets"
        "/usr/local/bin/enterprise-tickets-health-check"
    )
    
    for file in "${config_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Missing configuration file: $file"
            ((validation_errors++))
        fi
    done
    
    # Check if directories exist with correct permissions
    local directories=(
        "$MONITORING_DIR"
        "$LOG_DIR"
        "$BACKUP_DIR"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "Missing directory: $dir"
            ((validation_errors++))
        fi
    done
    
    if [ $validation_errors -eq 0 ]; then
        log_success "Monitoring setup validation passed"
        return 0
    else
        log_error "Monitoring setup validation failed with $validation_errors errors"
        return 1
    fi
}

# Main execution
main() {
    echo "🎯 Enterprise Ticket Management System - Monitoring Setup"
    echo "========================================================="
    
    check_root
    create_directories
    setup_permissions
    install_dependencies
    configure_system_monitoring
    setup_health_checks
    configure_alerts
    setup_backup_monitoring
    create_dashboard_urls
    
    if validate_setup; then
        log_success "✅ Monitoring and logging setup completed successfully!"
        echo ""
        echo "🎉 Next Steps:"
        echo "1. Copy monitoring configuration files to their respective directories"
        echo "2. Start monitoring services: docker-compose -f docker-compose.prod.yml up -d"
        echo "3. Access dashboards using: /usr/local/bin/monitoring-urls"
        echo "4. Configure email and Slack webhooks in alert configurations"
        echo ""
        echo "📚 Documentation:"
        echo "- Monitoring Guide: docs/ADMIN_GUIDE.md"
        echo "- Troubleshooting: docs/USER_MANUAL.md#troubleshooting"
    else
        log_error "❌ Setup completed with errors. Please check the logs above."
        exit 1
    fi
}

# Run main function
main "$@"