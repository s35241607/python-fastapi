# Enterprise Ticket Management System - Admin Configuration Guide

## Quick Setup Guide

### 1. Environment Setup

```bash
# Production Environment Variables
APP_NAME="Enterprise Ticket Management System"
ENVIRONMENT="production"
SECRET_KEY="your-256-bit-secret-key"
DATABASE_URL="postgresql://user:password@localhost:5432/ticketsystem"
REDIS_URL="redis://localhost:6379/0"
JWT_SECRET_KEY="your-jwt-secret"
```

### 2. Database Configuration

```sql
-- Create database and optimize
CREATE DATABASE ticketsystem;
CREATE USER ticketadmin WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ticketsystem TO ticketadmin;

-- Performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
SELECT pg_reload_conf();

-- Essential indexes
CREATE INDEX CONCURRENTLY idx_tickets_status ON tickets(status);
CREATE INDEX CONCURRENTLY idx_tickets_priority ON tickets(priority);
CREATE INDEX CONCURRENTLY idx_tickets_assignee_status ON tickets(assigned_to_id, status);
```

### 3. User Management

#### Role Configuration
```python
ROLES = {
    "super_admin": ["*"],  # All permissions
    "admin": ["manage_users", "system_config", "view_all_tickets"],
    "manager": ["approve_requests", "view_team_tickets", "assign_tickets"],
    "user": ["create_tickets", "view_own_tickets", "add_comments"]
}
```

#### LDAP Integration
```python
LDAP_SETTINGS = {
    "server": "ldap://ldap.company.com",
    "base_dn": "dc=company,dc=com",
    "user_dn": "ou=users,dc=company,dc=com",
    "bind_user": "cn=admin,dc=company,dc=com",
    "auto_create_users": True
}
```

### 4. Security Configuration

#### Password Policy
```python
PASSWORD_POLICY = {
    "min_length": 12,
    "require_uppercase": True,
    "require_numbers": True,
    "require_special_chars": True,
    "max_age_days": 90,
    "lockout_threshold": 5
}
```

#### Rate Limiting
```python
RATE_LIMITS = {
    "/auth/login": {"requests_per_minute": 10, "per_ip": True},
    "/tickets/": {"requests_per_minute": 200, "per_user": True},
    "/attachments/upload": {"requests_per_minute": 20, "per_user": True}
}
```

### 5. Department & Workflow Setup

#### Department Configuration
```python
DEPARTMENTS = [
    {
        "name": "IT",
        "manager_email": "it-manager@company.com",
        "sla_hours": 24,
        "escalation_hours": 4,
        "budget_limit": 50000,
        "approval_rules": {
            "budget_threshold": 1000,
            "auto_approve_below": 100
        }
    }
]
```

#### Approval Workflows
```yaml
workflows:
  budget_approval:
    trigger: "budget_amount > 1000"
    steps:
      - manager_approval: {timeout_hours: 48, required: true}
      - finance_approval: {timeout_hours: 72, condition: "budget > 5000"}
  
  system_change:
    trigger: "category == 'change'"
    steps:
      - technical_review: {type: "parallel", approvers: ["tech_lead", "security"]}
      - change_board: {type: "sequential", timeout_hours: 168}
```

### 6. Integration Setup

#### Email Configuration
```python
EMAIL_SETTINGS = {
    "smtp_host": "smtp.office365.com",
    "smtp_port": 587,
    "username": "tickets@company.com",
    "use_tls": True,
    "templates": {
        "ticket_created": "New Ticket: {ticket_number}",
        "approval_request": "Approval Required: {ticket_number}"
    }
}
```

#### Teams Integration
```python
TEAMS_WEBHOOK = "https://outlook.office.com/webhook/your-url"
TEAMS_NOTIFICATIONS = {
    "ticket_created": ["it-support"],
    "critical_tickets": ["it-alerts", "management"],
    "sla_breaches": ["management"]
}
```

### 7. Performance Optimization

#### Database Connection Pool
```python
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

#### Redis Caching
```python
CACHE_SETTINGS = {
    "default_timeout": 3600,
    "user_permissions": 1800,
    "dashboard_metrics": 300,
    "search_results": 600
}
```

#### Load Balancing (HAProxy)
```
backend ticket_backend
    balance roundrobin
    option httpchk GET /health
    server web1 127.0.0.1:8001 check
    server web2 127.0.0.1:8002 check
```

### 8. Monitoring & Maintenance

#### Health Checks
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": await check_database(),
        "redis": await check_redis(),
        "disk_space": check_disk_space()
    }
```

#### Backup Script
```bash
#!/bin/bash
# Daily backup
pg_dump -h localhost -U ticketadmin ticketsystem \
    --format=custom --compress=9 \
    --file="/backups/tickets_$(date +%Y%m%d).backup"

# Upload to cloud
aws s3 cp "/backups/tickets_$(date +%Y%m%d).backup" s3://backups/

# Clean old backups (30 days)
find /backups -name "*.backup" -mtime +30 -delete
```

#### Log Configuration
```python
LOGGING = {
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/tickets/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10
        }
    },
    'root': {'level': 'INFO', 'handlers': ['file']}
}
```

### 9. Common Maintenance Tasks

#### Weekly Maintenance
```bash
# Database cleanup
psql -d ticketsystem -c "VACUUM ANALYZE;"
psql -d ticketsystem -c "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"

# Clear expired sessions
psql -d ticketsystem -c "DELETE FROM user_sessions WHERE expires_at < NOW();"

# Restart services
systemctl restart tickets-app
systemctl restart redis
```

#### Performance Monitoring
```sql
-- Find slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;

-- Check database size
SELECT pg_size_pretty(pg_database_size('ticketsystem'));
```

### 10. Troubleshooting

#### Common Issues

**High CPU Usage**
```bash
# Check processes
top -p $(pgrep -f "ticket")
# Check database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

**Memory Leaks**
```bash
# Monitor memory
free -h
ps aux --sort=-%mem | head -10
```

**Connection Pool Exhausted**
```python
# Monitor pool status
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
```

### 11. API Management

#### API Key Generation
```python
import secrets
def generate_api_key():
    return f"tks_{secrets.token_urlsafe(32)}"
```

#### Rate Limiting Implementation
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/tickets/")
@limiter.limit("100/minute")
async def create_ticket(request: Request):
    pass
```

### 12. Security Best Practices

#### SSL Configuration (NGINX)
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/tickets.crt;
    ssl_certificate_key /etc/ssl/private/tickets.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000";
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

#### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 22   # SSH
ufw allow 80   # HTTP
ufw allow 443  # HTTPS
ufw deny 8000  # Block direct app access
ufw enable
```

## Emergency Procedures

### System Recovery
1. Check system status: `systemctl status tickets-app`
2. Review logs: `tail -f /var/log/tickets/app.log`
3. Restart services: `systemctl restart tickets-app redis postgresql`
4. Restore from backup if needed: `pg_restore -d ticketsystem backup.sql`

### Performance Issues
1. Monitor resources: `htop`, `iotop`, `nethogs`
2. Check database: `SELECT * FROM pg_stat_activity;`
3. Clear cache: `redis-cli FLUSHALL`
4. Scale horizontally if needed

### Security Incidents
1. Check access logs: `grep "ERROR\|WARN" /var/log/tickets/app.log`
2. Review failed logins: `SELECT * FROM audit_logs WHERE action='login_failed';`
3. Block suspicious IPs: `ufw deny from <IP>`
4. Reset passwords for affected users

## Support Contacts

- **Technical Support**: support@company.com
- **Security Issues**: security@company.com  
- **Emergency Escalation**: +1-800-EMERGENCY

---

*Admin Guide v1.0 - December 2023*