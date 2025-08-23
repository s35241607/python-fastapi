from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import engine
from app.models import Base
from app.routers import items, users

# 創建 FastAPI 應用程式
app = FastAPI(
    title=settings.APP_NAME,
    description="A FastAPI backend with SQLAlchemy and PostgreSQL",
    version=settings.APP_VERSION,
    debug=settings.debug,
    docs_url="/docs" if not settings.is_production else None,  # 生產環境隱藏文檔
    redoc_url="/redoc" if not settings.is_production else None,
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


@app.get("/")
async def root():
    """根路徑 - 用於測試 API 連接"""
    return {
        "message": f"{settings.APP_NAME} is running!",
        "environment": settings.ENVIRONMENT.value,
        "version": settings.APP_VERSION,
        "debug": settings.debug,
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
        f"{env_emoji} {settings.APP_NAME} started in {settings.ENVIRONMENT.value.upper()} mode"
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print(f"🛑 {settings.APP_NAME} shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True, debug=True)
