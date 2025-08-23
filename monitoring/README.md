# Enterprise Ticket Management System - Monitoring & Logging

## 🎯 Overview

Comprehensive monitoring and logging solution for the Enterprise Ticket Management System, designed to provide full observability across all components in a production environment supporting 1000+ concurrent users.

## 📋 Architecture

### Monitoring Stack
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **Alertmanager**: Alert routing and notifications
- **Node Exporter**: System metrics
- **PostgreSQL Exporter**: Database metrics
- **Redis Exporter**: Cache metrics

### Logging Stack (ELK)
- **Elasticsearch**: Log storage and indexing
- **Logstash**: Log processing and enrichment
- **Kibana**: Log visualization and analysis
- **Filebeat**: Log shipping

## 🚀 Quick Start

### 1. Setup Monitoring Infrastructure

```bash
# Run the automated setup script
sudo chmod +x monitoring/setup-monitoring.sh
sudo ./monitoring/setup-monitoring.sh
```

### 2. Deploy with Docker Compose

```bash
# Start all monitoring services
docker-compose -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose -f docker-compose.prod.yml ps
```

### 3. Access Monitoring Dashboards

```bash
# Display all monitoring URLs
/usr/local/bin/monitoring-urls
```

## 📊 Monitoring Components

### Prometheus Configuration

**Location**: `monitoring/prometheus/prometheus.yml`

**Key Features**:
- ✅ 15-second scrape intervals for real-time monitoring
- ✅ Monitors FastAPI, PostgreSQL, Redis, NGINX, HAProxy
- ✅ System metrics via Node Exporter
- ✅ Container metrics via cAdvisor
- ✅ 30-day data retention

**Targets Monitored**:
```yaml
- FastAPI Backend: :8000/metrics
- PostgreSQL: postgres-exporter:9187
- Redis: redis-exporter:9121
- NGINX: nginx-exporter:9113
- HAProxy: haproxy-exporter:9101
- System: node-exporter:9100
```

### Alert Rules

**Location**: `monitoring/prometheus/alert_rules.yml`

**Alert Categories**:
- 🚨 **System Alerts**: CPU, Memory, Disk usage
- 🚨 **Application Alerts**: Response time, error rate, throughput
- 🚨 **Database Alerts**: Connection usage, slow queries
- 🚨 **Business Alerts**: High ticket creation, approval backlogs
- 🚨 **Security Alerts**: Authentication failures, suspicious activity

**Critical Thresholds**:
```yaml
CPU Usage: > 80% for 5 minutes
Memory Usage: > 85% for 5 minutes
Disk Space: < 20% available
Response Time: > 2 seconds (95th percentile)
Error Rate: > 5% for 5 minutes
```

### Grafana Dashboards

**Location**: `monitoring/grafana/dashboards/`

**Available Dashboards**:
1. **Enterprise Overview**: System health, request rates, response times
2. **Application Performance**: Detailed FastAPI metrics
3. **Database Performance**: PostgreSQL monitoring
4. **Infrastructure**: System resources and container metrics
5. **Business Intelligence**: Ticket creation, user activity, SLA compliance

**Default Credentials**:
- Username: `admin`
- Password: `secure_grafana_password` (set in .env)

### Log Processing (ELK Stack)

**Logstash Pipeline**: `monitoring/elk/logstash/pipeline/logstash.conf`

**Log Sources**:
- FastAPI application logs (JSON format)
- NGINX access and error logs
- PostgreSQL query logs
- Docker container logs
- System logs (syslog)

**Log Processing Features**:
- ✅ JSON parsing and field extraction
- ✅ Geographic IP location enrichment
- ✅ Sensitive data anonymization
- ✅ Performance metrics extraction
- ✅ Error categorization and tagging

**Index Templates**: `monitoring/elk/elasticsearch/templates/`
- Optimized for time-series log data
- 30-day retention policy
- Automatic field mapping

## 🔧 Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# Monitoring Configuration
GRAFANA_USER=admin
GRAFANA_PASSWORD=secure_grafana_password
PROMETHEUS_RETENTION_DAYS=30

# Alert Configuration
ALERT_EMAIL=admin@yourcompany.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/your-webhook

# Log Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
ELASTICSEARCH_HEAP_SIZE=1g
```

### Customizing Alerts

1. **Edit Alert Rules**: Modify `monitoring/prometheus/alert_rules.yml`
2. **Configure Recipients**: Update `monitoring/prometheus/alertmanager.yml`
3. **Reload Configuration**: 
   ```bash
   docker-compose exec prometheus kill -HUP 1
   ```

### Adding Custom Metrics

1. **Add Prometheus Scrape Target**:
   ```yaml
   - job_name: 'custom-app'
     static_configs:
       - targets: ['custom-app:9090']
   ```

2. **Create Grafana Dashboard**: Import JSON configuration
3. **Set Up Alerts**: Define alert rules for new metrics

## 📈 Performance Monitoring

### Key Performance Indicators (KPIs)

#### Application Performance
- **Response Time**: < 1 second (target), < 2 seconds (acceptable)
- **Throughput**: > 200 RPS (target), > 100 RPS (minimum)
- **Error Rate**: < 0.5% (target), < 1% (acceptable)
- **Availability**: 99.9% uptime

#### System Performance
- **CPU Usage**: < 70% average, < 80% peak
- **Memory Usage**: < 80% average, < 85% peak
- **Disk I/O**: < 80% utilization
- **Network**: < 70% bandwidth utilization

#### Database Performance
- **Connection Usage**: < 80% of max connections
- **Query Time**: < 100ms average, < 1000ms 95th percentile
- **Lock Wait Time**: < 10ms average
- **Cache Hit Ratio**: > 95%

### Performance Alerts

Critical performance alerts configured:

```yaml
FastAPIHighResponseTime: 95th percentile > 2 seconds
FastAPIHighErrorRate: Error rate > 5%
PostgreSQLSlowQueries: Query duration > 5 minutes
HighCPUUsage: CPU > 80% for 5 minutes
HighMemoryUsage: Memory > 85% for 5 minutes
```

## 🔍 Log Analysis

### Log Categories

#### Application Logs
- **Request/Response**: HTTP transactions
- **Business Logic**: Ticket operations, approvals
- **Security**: Authentication, authorization
- **Performance**: Slow operations, resource usage

#### System Logs
- **Access Logs**: NGINX request logs
- **Error Logs**: Application and system errors
- **Security Logs**: Failed logins, suspicious activity
- **Audit Logs**: Administrative actions

### Kibana Dashboards

**Location**: `monitoring/elk/kibana/dashboard/`

**Available Dashboards**:
1. **Log Overview**: Real-time log analysis
2. **Error Analysis**: Error tracking and trends
3. **Security Monitor**: Authentication and access patterns
4. **Performance Logs**: Slow requests and operations
5. **Business Analytics**: User behavior and system usage

### Common Log Queries

#### Find Errors
```
level:ERROR OR severity:error
```

#### Authentication Failures
```
path:"/auth/login" AND status:401
```

#### Slow Requests
```
response_time:>2000
```

#### Security Events
```
tags:authentication OR tags:security
```

## 🚨 Alerting

### Alert Channels

#### Email Alerts
- **Critical**: Immediate email notification
- **Warning**: Hourly digest
- **Info**: Daily summary

#### Slack Integration
- **#alerts**: Critical and warning alerts
- **#monitoring**: System status updates
- **#ops**: Operational notifications

#### Teams Integration
- **Operations Team**: Infrastructure alerts
- **Development Team**: Application alerts
- **Management**: SLA and business metric alerts

### Alert Escalation

```
Level 1 (0-15 min): Team leads
Level 2 (15-30 min): Department managers
Level 3 (30+ min): Executive team
```

### On-Call Procedures

1. **Acknowledge Alert**: Confirm receipt within 5 minutes
2. **Initial Assessment**: Determine severity and impact
3. **Escalate if Needed**: Follow escalation matrix
4. **Document Response**: Log actions taken
5. **Post-Incident Review**: Analyze and improve

## 🛠️ Maintenance

### Daily Tasks

- ✅ Review overnight alerts
- ✅ Check system health dashboard
- ✅ Verify backup completion
- ✅ Monitor disk usage trends

### Weekly Tasks

- ✅ Review performance trends
- ✅ Update alert thresholds if needed
- ✅ Clean up old logs (if not automated)
- ✅ Review capacity planning metrics

### Monthly Tasks

- ✅ Performance trend analysis
- ✅ Alert effectiveness review
- ✅ Dashboard optimization
- ✅ Capacity planning review

### Backup and Recovery

#### Monitoring Data Backup
```bash
# Backup Prometheus data
docker exec prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus/data

# Backup Grafana configuration
docker exec grafana tar -czf /tmp/grafana-backup.tar.gz /etc/grafana /var/lib/grafana
```

#### Log Retention
- **Application Logs**: 30 days
- **System Logs**: 90 days
- **Audit Logs**: 1 year
- **Performance Metrics**: 30 days

## 🔧 Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check container memory usage
docker stats

# Increase Elasticsearch heap size
export ELASTICSEARCH_HEAP_SIZE=2g
```

#### Missing Metrics
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Restart monitoring services
docker-compose restart prometheus grafana
```

#### Log Processing Delays
```bash
# Check Logstash pipeline
docker logs logstash

# Increase Logstash workers
# Edit logstash.conf: pipeline.workers: 4
```

### Health Checks

Run comprehensive health check:
```bash
/usr/local/bin/enterprise-tickets-health-check
```

Check individual services:
```bash
# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health

# Elasticsearch
curl http://localhost:9200/_cluster/health
```

## 📞 Support

### Emergency Contacts
- **Operations Team**: ops@yourcompany.com
- **Development Team**: dev@yourcompany.com
- **Infrastructure Team**: infra@yourcompany.com

### Documentation
- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **ELK Stack**: https://www.elastic.co/guide/

### Internal Resources
- **Admin Guide**: `docs/ADMIN_GUIDE.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Deployment Guide**: `README.md`

---

**Version**: 1.0  
**Last Updated**: December 2023  
**Maintained By**: Enterprise IT Team