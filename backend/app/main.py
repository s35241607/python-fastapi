import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import Base
from app.routers import items, users

# Create database tables


app = FastAPI(
    title="FastAPI Backend",
    description="A FastAPI backend with SQLAlchemy and PostgreSQL",
    version="1.0.0",
    debug=True,  # Enable debug mode
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vue.js dev server
        "http://127.0.0.1:5173",  # Alternative localhost
        "http://localhost:3000",  # Alternative port
    ],
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
        "message": "FastAPI Backend is running!",
        "debug": True,
        "environment": os.getenv("DATABASE_URL", "Not set")[:20] + "...",
    }


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "healthy", "debug_mode": True}


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    print("🚀 FastAPI application started in DEBUG mode")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    print("🛑 FastAPI application shutdown")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True, debug=True)
