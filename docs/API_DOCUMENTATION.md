# Enterprise Ticket Management System - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Response Formats](#response-formats)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Code Examples](#code-examples)
9. [SDKs and Libraries](#sdks-and-libraries)
10. [Webhook Integration](#webhook-integration)

## Overview

The Enterprise Ticket Management System API provides comprehensive functionality for managing tickets, approval workflows, user collaboration, and system administration in enterprise environments.

### Key Features

- **🎫 Ticket Management**: Complete CRUD operations with advanced search and filtering
- **🔄 Approval Workflows**: Multi-step approval processes with delegation and escalation
- **👥 User Management**: Role-based access control with granular permissions
- **💬 Collaboration**: Real-time comments, mentions, and notifications
- **📎 File Management**: Secure file upload/download with validation
- **📊 Analytics**: Comprehensive reporting and dashboard metrics
- **🔒 Security**: JWT authentication, audit logging, and data encryption

### API Specifications

- **Base URL**: `https://api.ticketsystem.com`
- **Version**: v1.0.0
- **Protocol**: HTTPS only
- **Format**: JSON
- **Authentication**: JWT Bearer tokens
- **Rate Limit**: 1000 requests/hour per user

## Authentication

### Login

Obtain a JWT token for API access:

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": 1,
      "username": "john.doe",
      "email": "john.doe@company.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "user",
      "permissions": ["view_tickets", "create_tickets", "comment_tickets"]
    }
  },
  "message": "Login successful",
  "timestamp": "2023-12-01T10:00:00Z"
}
```

### Using Authentication

Include the JWT token in the Authorization header:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Refresh

Refresh your access token before it expires:

```http
POST /auth/refresh
Authorization: Bearer your_refresh_token
```

## API Endpoints

### Tickets

#### List Tickets

```http
GET /tickets?page=1&size=20&status=open&priority=high&search=server
Authorization: Bearer token
```

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `size` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (open, in_progress, resolved, closed)
- `priority` (string): Filter by priority (low, medium, high, critical)
- `search` (string): Full-text search query
- `created_by_id` (integer): Filter by creator
- `assigned_to_id` (integer): Filter by assignee
- `department_id` (integer): Filter by department
- `created_after` (datetime): Filter by creation date
- `tags` (string): Comma-separated tags

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 123,
        "ticket_number": "TKT-20231201-001",
        "title": "Server Performance Issue",
        "description": "Database queries are running slowly",
        "status": "open",
        "priority": "high",
        "ticket_type": "incident",
        "created_by_id": 1,
        "assigned_to_id": 5,
        "department_id": 1,
        "tags": ["performance", "database", "urgent"],
        "created_at": "2023-12-01T10:00:00Z",
        "updated_at": "2023-12-01T10:00:00Z",
        "due_date": "2023-12-02T18:00:00Z",
        "sla_breach_time": null,
        "resolution_time": null,
        "created_by": {
          "id": 1,
          "username": "john.doe",
          "first_name": "John",
          "last_name": "Doe"
        },
        "assigned_to": {
          "id": 5,
          "username": "admin",
          "first_name": "System",
          "last_name": "Admin"
        },
        "department": {
          "id": 1,
          "name": "IT Department"
        }
      }
    ],
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8
  }
}
```

#### Create Ticket

```http
POST /tickets
Authorization: Bearer token
Content-Type: application/json

{
  "title": "New System Issue",
  "description": "Detailed description of the issue",
  "priority": "medium",
  "ticket_type": "incident",
  "department_id": 1,
  "assigned_to_id": 5,
  "tags": ["system", "bug"],
  "due_date": "2023-12-05T18:00:00Z",
  "attachments": ["file1.pdf", "screenshot.png"]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 124,
    "ticket_number": "TKT-20231201-002",
    "title": "New System Issue",
    "status": "open",
    "created_at": "2023-12-01T11:00:00Z"
  },
  "message": "Ticket created successfully",
  "timestamp": "2023-12-01T11:00:00Z"
}
```

#### Update Ticket

```http
PATCH /tickets/123
Authorization: Bearer token
Content-Type: application/json

{
  "status": "in_progress",
  "priority": "high",
  "assigned_to_id": 7,
  "internal_notes": "Escalated to senior engineer"
}
```

#### Get Ticket Details

```http
GET /tickets/123
Authorization: Bearer token
```

**Response includes:**
- Complete ticket information
- Comment history
- Attachment list
- Approval workflow status
- Activity timeline
- Related tickets

#### Delete Ticket

```http
DELETE /tickets/123
Authorization: Bearer token
```

### Approvals

#### List Pending Approvals

```http
GET /approvals/pending?department_id=1&priority=high
Authorization: Bearer token
```

#### Process Approval

```http
POST /approvals/45/action
Authorization: Bearer token
Content-Type: application/json

{
  "action": "approve",
  "comments": "Approved with conditions",
  "conditions": ["Budget limit: $5000", "Timeline: 2 weeks"]
}
```

**Actions:**
- `approve`: Approve the request
- `reject`: Reject the request
- `delegate`: Delegate to another user
- `request_info`: Request additional information

#### Bulk Approval

```http
POST /approvals/bulk-action
Authorization: Bearer token
Content-Type: application/json

{
  "approval_ids": [45, 46, 47],
  "action": "approve",
  "comments": "Bulk approval for routine requests"
}
```

### Comments

#### Add Comment

```http
POST /comments/ticket/123
Authorization: Bearer token
Content-Type: application/json

{
  "content": "I've investigated this issue and found the root cause.",
  "is_internal": false,
  "mentions": ["@john.doe", "@admin"],
  "attachments": ["investigation_log.txt"]
}
```

#### List Comments

```http
GET /comments/ticket/123?page=1&size=10&include_internal=false
Authorization: Bearer token
```

### File Attachments

#### Upload File

```http
POST /attachments/ticket/123/upload
Authorization: Bearer token
Content-Type: multipart/form-data

file: <binary_data>
description: "Error log file"
is_internal: false
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 789,
    "filename": "error_log.txt",
    "size": 2048,
    "content_type": "text/plain",
    "upload_url": "https://files.ticketsystem.com/789/error_log.txt",
    "virus_scan_status": "clean"
  }
}
```

#### Download File

```http
GET /attachments/789/download
Authorization: Bearer token
```

### Reports and Analytics

#### Dashboard Metrics

```http
GET /reports/dashboard?period=30d&department_id=1
Authorization: Bearer token
```

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "total_tickets": 1250,
      "open_tickets": 89,
      "in_progress_tickets": 45,
      "resolved_tickets": 1100,
      "closed_tickets": 16,
      "avg_resolution_time": 4.2,
      "sla_compliance": 94.5,
      "customer_satisfaction": 4.3
    },
    "trends": {
      "ticket_volume_trend": "+12%",
      "resolution_time_trend": "-8%",
      "satisfaction_trend": "+5%"
    },
    "top_categories": [
      {"name": "Network Issues", "count": 45},
      {"name": "Software Bugs", "count": 32},
      {"name": "Hardware Problems", "count": 28}
    ]
  }
}
```

#### Performance Reports

```http
GET /reports/performance?start_date=2023-11-01&end_date=2023-12-01&format=json
Authorization: Bearer token
```

#### Export Data

```http
GET /reports/export?type=tickets&format=csv&filters={"status":"resolved","created_after":"2023-11-01"}
Authorization: Bearer token
```

### Search

#### Advanced Search

```http
POST /tickets/search
Authorization: Bearer token
Content-Type: application/json

{
  "query": "server performance",
  "filters": {
    "status": ["open", "in_progress"],
    "priority": ["high", "critical"],
    "created_after": "2023-11-01",
    "departments": [1, 2],
    "tags": ["performance", "server"]
  },
  "sort": [
    {"field": "priority", "order": "desc"},
    {"field": "created_at", "order": "desc"}
  ],
  "page": 1,
  "size": 20
}
```

## Data Models

### Ticket Model

```json
{
  "id": "integer (primary key)",
  "ticket_number": "string (unique, auto-generated)",
  "title": "string (required, max 200 chars)",
  "description": "string (required)",
  "status": "enum (open, in_progress, pending_approval, resolved, closed)",
  "priority": "enum (low, medium, high, critical)",
  "ticket_type": "enum (incident, request, problem, change)",
  "created_by_id": "integer (foreign key)",
  "assigned_to_id": "integer (foreign key, nullable)",
  "department_id": "integer (foreign key)",
  "tags": "array of strings",
  "created_at": "datetime (auto)",
  "updated_at": "datetime (auto)",
  "due_date": "datetime (nullable)",
  "resolution_time": "integer (minutes, nullable)",
  "sla_breach_time": "datetime (nullable)",
  "customer_satisfaction_rating": "integer (1-5, nullable)",
  "internal_notes": "string (nullable)",
  "public_notes": "string (nullable)"
}
```

### User Model

```json
{
  "id": "integer (primary key)",
  "username": "string (unique, required)",
  "email": "string (unique, required)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "role": "enum (user, manager, admin, super_admin)",
  "department_id": "integer (foreign key)",
  "is_active": "boolean (default: true)",
  "last_login": "datetime (nullable)",
  "created_at": "datetime (auto)",
  "preferences": "json object",
  "permissions": "array of strings"
}
```

### Comment Model

```json
{
  "id": "integer (primary key)",
  "ticket_id": "integer (foreign key)",
  "user_id": "integer (foreign key)",
  "content": "string (required)",
  "is_internal": "boolean (default: false)",
  "mentions": "array of user IDs",
  "created_at": "datetime (auto)",
  "updated_at": "datetime (auto)",
  "edited": "boolean (default: false)",
  "attachments": "array of attachment IDs"
}
```

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully",
  "timestamp": "2023-12-01T10:00:00Z",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Invalid email format",
      "provided_value": "invalid-email"
    },
    "timestamp": "2023-12-01T10:00:00Z"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Pagination Response

```json
{
  "items": [...],
  "pagination": {
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8,
    "has_next": true,
    "has_prev": false,
    "next_page": 2,
    "prev_page": null
  }
}
```

## Error Handling

### HTTP Status Codes

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation errors)
- **401**: Unauthorized (invalid/expired token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not Found
- **409**: Conflict (duplicate resource)
- **422**: Unprocessable Entity (business logic error)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

### Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_REQUIRED` | Valid token required |
| `PERMISSION_DENIED` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource doesn't exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `BUSINESS_RULE_VIOLATION` | Business logic constraint violated |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | External service unavailable |

## Rate Limiting

Rate limits are applied per user and endpoint category:

| Category | Limit | Window |
|----------|-------|--------|
| Authentication | 10 requests | 1 minute |
| General API | 1000 requests | 1 hour |
| File Upload | 100 requests | 1 hour |
| Search | 200 requests | 1 hour |
| Reports | 50 requests | 1 hour |

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1638360000
```

## Code Examples

### Python SDK

```python
from ticket_system_sdk import TicketSystemClient

# Initialize client
client = TicketSystemClient(
    base_url="https://api.ticketsystem.com",
    api_key="your_api_key"
)

# Login
auth = client.auth.login("username", "password")
client.set_token(auth.access_token)

# Create ticket
ticket = client.tickets.create({
    "title": "Server Issue",
    "description": "Server is responding slowly",
    "priority": "high",
    "department_id": 1
})

# List tickets
tickets = client.tickets.list(
    status="open",
    priority="high",
    page=1,
    size=20
)

# Add comment
comment = client.comments.create(
    ticket_id=ticket.id,
    content="I'm investigating this issue",
    is_internal=False
)
```

### JavaScript SDK

```javascript
import { TicketSystemAPI } from '@company/ticket-system-sdk';

// Initialize API client
const api = new TicketSystemAPI({
  baseURL: 'https://api.ticketsystem.com',
  apiKey: 'your_api_key'
});

// Login
const auth = await api.auth.login('username', 'password');
api.setToken(auth.access_token);

// Create ticket
const ticket = await api.tickets.create({
  title: 'Frontend Bug',
  description: 'Button not responding to clicks',
  priority: 'medium',
  department_id: 2
});

// Upload attachment
const attachment = await api.attachments.upload(ticket.id, {
  file: fileBlob,
  description: 'Screenshot of the bug'
});
```

### cURL Examples

```bash
# Login
curl -X POST "https://api.ticketsystem.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe", "password": "password123"}'

# Create ticket
curl -X POST "https://api.ticketsystem.com/tickets" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Network Connectivity Issue",
    "description": "Users unable to access shared drives",
    "priority": "high",
    "ticket_type": "incident",
    "department_id": 1
  }'

# Upload file
curl -X POST "https://api.ticketsystem.com/attachments/ticket/123/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@network_logs.txt" \
  -F "description=Network diagnostic logs"
```

## Webhook Integration

Configure webhooks to receive real-time notifications:

### Webhook Events

- `ticket.created`
- `ticket.updated`
- `ticket.status_changed`
- `ticket.assigned`
- `comment.added`
- `approval.requested`
- `approval.processed`
- `file.uploaded`

### Webhook Payload

```json
{
  "event": "ticket.created",
  "timestamp": "2023-12-01T10:00:00Z",
  "data": {
    "ticket": {
      "id": 123,
      "ticket_number": "TKT-20231201-001",
      "title": "New Issue",
      "status": "open",
      "created_by": {
        "id": 1,
        "username": "john.doe"
      }
    }
  },
  "webhook_id": "wh_123456789"
}
```

### Webhook Configuration

```http
POST /webhooks
Authorization: Bearer token
Content-Type: application/json

{
  "url": "https://your-app.com/webhooks/tickets",
  "events": ["ticket.created", "ticket.updated"],
  "secret": "your_webhook_secret",
  "active": true
}
```

## SDKs and Libraries

Official SDKs are available for:

- **Python**: `pip install ticket-system-sdk`
- **JavaScript/Node.js**: `npm install @company/ticket-system-sdk`
- **PHP**: `composer require company/ticket-system-sdk`
- **Java**: Maven/Gradle dependency available
- **C#/.NET**: NuGet package available

## Support and Resources

- **API Documentation**: [https://docs.ticketsystem.com](https://docs.ticketsystem.com)
- **Interactive API Explorer**: [https://api.ticketsystem.com/docs](https://api.ticketsystem.com/docs)
- **Status Page**: [https://status.ticketsystem.com](https://status.ticketsystem.com)
- **Support**: [api-support@company.com](mailto:api-support@company.com)
- **GitHub**: [https://github.com/company/ticket-system](https://github.com/company/ticket-system)

---

*Last updated: December 1, 2023*
*API Version: 1.0.0*