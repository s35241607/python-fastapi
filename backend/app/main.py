from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import engine
from app.models import Base
from app.routers import items, users, auth, tickets, approvals, comments, attachments, reports
from app.api_docs import setup_api_documentation

# 創建 FastAPI 應用程式
app = FastAPI(
    title="Enterprise Ticket Management System",
    description="Comprehensive enterprise-grade ticket management system supporting 1000+ concurrent users",
    version="1.0.0",
    debug=settings.debug,
    docs_url="/docs" if not settings.is_production else None,  # 生產環境隱藏文檔
    redoc_url="/redoc" if not settings.is_production else None,
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "deepLinking": True,
        "displayRequestDuration": True,
        "docExpansion": "none",
        "operationsSorter": "method",
        "filter": True,
        "tryItOutEnabled": True
    }
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(items.router, prefix="/api/v1")

# Enterprise Ticket Management System routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(approvals.router, prefix="/approvals", tags=["Approvals"])
app.include_router(comments.router, prefix="/comments", tags=["Comments"])
app.include_router(attachments.router, prefix="/attachments", tags=["Attachments"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Setup comprehensive API documentation
setup_api_documentation(app)


@app.get("/")
async def root():
    """根路徑 - Enterprise Ticket Management System API"""
    return {
        "message": "Enterprise Ticket Management System API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT.value,
        "features": [
            "Comprehensive ticket management",
            "Advanced approval workflows", 
            "Real-time collaboration",
            "Enterprise security",
            "Performance optimized for 1000+ users"
        ],
        "documentation": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT.value,
        "debug_mode": settings.debug,
    }


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    env_emoji = (
        "🚀" if settings.is_development else "🏭" if settings.is_production else "🧪"
    )
    print(
        f"{env_emoji} Enterprise Ticket Management System started in {settings.ENVIRONMENT.value.upper()} mode"
    )
    print("🎫 Features: Ticket Management, Approval Workflows, Real-time Collaboration")
    print("📊 Performance: Optimized for 1000+ concurrent users")
    print("🔒 Security: JWT Authentication, RBAC, Audit Logging")

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")
        print("📚 API Documentation available at /docs")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print("🛑 Enterprise Ticket Management System shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True, debug=True)
