"""
OpenAPI/Swagger Configuration for Enterprise Ticket Management System
Comprehensive API documentation with detailed schemas and examples
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict, Any


def custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    Generate comprehensive OpenAPI schema with enterprise-level documentation
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Enterprise Ticket Management System API",
        version="1.0.0",
        summary="Comprehensive ticket management system for enterprise environments",
        description="""
# Enterprise Ticket Management System API

A comprehensive, enterprise-grade ticket management system designed to handle 1000+ concurrent users with advanced workflows, approval processes, and real-time collaboration features.

## Features

### 🎫 Core Ticket Management
- **Complete CRUD Operations**: Create, read, update, delete tickets with validation
- **Advanced Search & Filtering**: Full-text search, faceted filtering, saved searches
- **Bulk Operations**: Process multiple tickets simultaneously
- **Status Workflow**: Customizable ticket lifecycle management
- **Priority Management**: Multi-level priority system with escalation

### 👥 User Management & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: 40+ granular permissions
- **Multi-Role Support**: User, Manager, Admin, Super Admin roles
- **Session Management**: Secure session handling with refresh tokens
- **Password Security**: Bcrypt hashing with complexity requirements

### 🔄 Approval Workflows
- **Multi-Step Workflows**: Sequential, parallel, and conditional approval flows
- **Delegation Support**: Approve on behalf of others with audit trail
- **Escalation Rules**: Automatic escalation based on SLA and business rules
- **Bulk Approvals**: Process multiple approvals efficiently
- **Template System**: Reusable workflow templates

### 💬 Communication & Collaboration
- **Discussion Threads**: Nested comments with mention support
- **Real-time Notifications**: WebSocket-based live updates
- **File Attachments**: Secure file upload/download with validation
- **Activity Timeline**: Complete audit trail of all actions
- **Email Integration**: Automated notifications via email, Teams, Slack

### 📊 Analytics & Reporting
- **Real-time Dashboard**: Live metrics and KPI tracking
- **Performance Analytics**: Response times, SLA compliance, trend analysis
- **Custom Reports**: Configurable reports with multiple export formats
- **User Analytics**: Individual and team performance metrics
- **Executive Summaries**: High-level business intelligence

### 🔒 Enterprise Security
- **Data Encryption**: End-to-end encryption for sensitive data
- **Audit Logging**: Comprehensive audit trail for compliance
- **Rate Limiting**: API protection against abuse
- **Input Validation**: Strict validation with sanitization
- **File Security**: Virus scanning and content validation

### 🚀 Performance & Scalability
- **High Performance**: Optimized for 1000+ concurrent users
- **Caching Strategy**: Multi-layer caching for optimal response times
- **Database Optimization**: Indexed queries and connection pooling
- **Load Balancing**: Ready for horizontal scaling
- **Monitoring**: Built-in performance monitoring and alerting

## API Standards

### Response Format
All API responses follow a consistent structure:
```json
{
    "success": true,
    "data": { ... },
    "message": "Operation completed successfully",
    "timestamp": "2023-12-01T10:00:00Z",
    "request_id": "uuid-request-id"
}
```

### Error Handling
Standardized error responses with detailed information:
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": { ... },
        "timestamp": "2023-12-01T10:00:00Z"
    }
}
```

### Pagination
Consistent pagination for list endpoints:
```json
{
    "items": [...],
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8
}
```

### Authentication
Bearer token authentication required for all protected endpoints:
```
Authorization: Bearer <jwt_token>
```

## Rate Limiting

API rate limits to ensure fair usage:
- **Authenticated Users**: 1000 requests/hour
- **Administrative Operations**: 500 requests/hour
- **File Uploads**: 100 requests/hour
- **Search Operations**: 200 requests/hour

## Versioning

API versioning through URL path:
- Current Version: `/api/v1/`
- Future versions will maintain backward compatibility

## Support & Contact

For API support and technical questions:
- **Documentation**: This interactive documentation
- **Support Team**: api-support@company.com
- **Status Page**: https://status.ticketsystem.com
- **GitHub**: https://github.com/company/ticket-system
        """,
        routes=app.routes,
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api-staging.ticketsystem.com",
                "description": "Staging server"
            },
            {
                "url": "https://api.ticketsystem.com",
                "description": "Production server"
            }
        ],
        contact={
            "name": "Enterprise Ticket System API Support",
            "url": "https://support.ticketsystem.com",
            "email": "api-support@company.com"
        },
        license_info={
            "name": "Enterprise License",
            "url": "https://ticketsystem.com/license"
        }
    )

    # Add additional schema information
    openapi_schema["info"]["x-logo"] = {
        "url": "https://ticketsystem.com/logo.png",
        "altText": "Enterprise Ticket Management System"
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token obtained from /auth/login endpoint"
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for service-to-service authentication"
        }
    }

    # Add global security
    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"ApiKeyAuth": []}
    ]

    # Add tags for organization
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication and session management",
            "externalDocs": {
                "description": "Authentication Guide",
                "url": "https://docs.ticketsystem.com/auth"
            }
        },
        {
            "name": "Tickets",
            "description": "Core ticket management operations",
            "externalDocs": {
                "description": "Ticket Management Guide",
                "url": "https://docs.ticketsystem.com/tickets"
            }
        },
        {
            "name": "Approvals",
            "description": "Approval workflow management",
            "externalDocs": {
                "description": "Approval Workflows Guide",
                "url": "https://docs.ticketsystem.com/approvals"
            }
        },
        {
            "name": "Comments",
            "description": "Ticket discussion and collaboration",
            "externalDocs": {
                "description": "Collaboration Guide",
                "url": "https://docs.ticketsystem.com/collaboration"
            }
        },
        {
            "name": "Attachments",
            "description": "File upload and management",
            "externalDocs": {
                "description": "File Management Guide",
                "url": "https://docs.ticketsystem.com/files"
            }
        },
        {
            "name": "Reports",
            "description": "Analytics and reporting",
            "externalDocs": {
                "description": "Reporting Guide",
                "url": "https://docs.ticketsystem.com/reports"
            }
        },
        {
            "name": "Search",
            "description": "Advanced search and filtering",
            "externalDocs": {
                "description": "Search Guide",
                "url": "https://docs.ticketsystem.com/search"
            }
        },
        {
            "name": "Administration",
            "description": "System administration and configuration",
            "externalDocs": {
                "description": "Admin Guide",
                "url": "https://docs.ticketsystem.com/admin"
            }
        }
    ]

    # Add response examples
    openapi_schema["components"]["examples"] = {
        "SuccessResponse": {
            "summary": "Successful operation",
            "value": {
                "success": True,
                "data": {},
                "message": "Operation completed successfully",
                "timestamp": "2023-12-01T10:00:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "ErrorResponse": {
            "summary": "Error response",
            "value": {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid input data",
                    "details": {
                        "field": "email",
                        "reason": "Invalid email format"
                    },
                    "timestamp": "2023-12-01T10:00:00Z"
                },
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        },
        "PaginatedResponse": {
            "summary": "Paginated list response",
            "value": {
                "items": [
                    {
                        "id": 1,
                        "title": "Sample Ticket",
                        "status": "open",
                        "priority": "medium"
                    }
                ],
                "total": 150,
                "page": 1,
                "size": 20,
                "pages": 8
            }
        },
        "TicketCreateRequest": {
            "summary": "Create ticket request",
            "value": {
                "title": "System Performance Issue",
                "description": "The dashboard is loading slowly for all users",
                "priority": "high",
                "ticket_type": "incident",
                "department_id": 1,
                "assigned_to_id": 5,
                "tags": ["performance", "dashboard", "urgent"]
            }
        },
        "TicketResponse": {
            "summary": "Ticket response",
            "value": {
                "id": 123,
                "ticket_number": "TKT-20231201-001",
                "title": "System Performance Issue",
                "description": "The dashboard is loading slowly for all users",
                "status": "open",
                "priority": "high",
                "ticket_type": "incident",
                "created_by_id": 1,
                "assigned_to_id": 5,
                "department_id": 1,
                "tags": ["performance", "dashboard", "urgent"],
                "created_at": "2023-12-01T10:00:00Z",
                "updated_at": "2023-12-01T10:00:00Z",
                "due_date": "2023-12-02T18:00:00Z",
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
        }
    }

    # Add custom extensions
    openapi_schema["x-codeSamples"] = [
        {
            "lang": "curl",
            "source": """
# Login to get authentication token
curl -X POST "http://localhost:8000/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"username": "your_username", "password": "your_password"}'

# Use the token to create a ticket
curl -X POST "http://localhost:8000/tickets/" \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"title": "New Issue", "description": "Description here", "priority": "medium"}'
            """
        },
        {
            "lang": "python",
            "source": """
import requests

# Login
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "your_username", "password": "your_password"}
)
token = login_response.json()["access_token"]

# Create ticket
headers = {"Authorization": f"Bearer {token}"}
ticket_data = {
    "title": "New Issue",
    "description": "Description here",
    "priority": "medium"
}
response = requests.post(
    "http://localhost:8000/tickets/",
    headers=headers,
    json=ticket_data
)
            """
        },
        {
            "lang": "javascript",
            "source": """
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'your_username', password: 'your_password' })
});
const { access_token } = await loginResponse.json();

// Create ticket
const ticketResponse = await fetch('http://localhost:8000/tickets/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'New Issue',
    description: 'Description here',
    priority: 'medium'
  })
});
            """
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_api_documentation(app: FastAPI) -> None:
    """
    Configure comprehensive API documentation for the FastAPI application
    """
    
    # Set custom OpenAPI schema
    app.openapi = lambda: custom_openapi_schema(app)
    
    # Configure Swagger UI
    app.swagger_ui_parameters = {
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "method",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "displayOperationId": True,
        "tryItOutEnabled": True
    }
    
    print("✅ API Documentation configured successfully")
    print("📚 Swagger UI available at: /docs")
    print("📖 ReDoc available at: /redoc")
    print("🔗 OpenAPI JSON available at: /openapi.json")