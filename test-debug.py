#!/usr/bin/env python3
"""
測試 Debug 配置腳本
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """測試所有模組是否可以正常導入"""
    try:
        from app.main import app
        print("✅ FastAPI app imported successfully")
        
        from app.database import engine, get_db
        print("✅ Database modules imported successfully")
        
        from app.models import User, Item
        print("✅ Models imported successfully")
        
        from app.routers import users, items
        print("✅ Routers imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_database_connection():
    """測試資料庫連接"""
    try:
        from app.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Debug Configuration...")
    print("-" * 40)
    
    if test_imports():
        print("✅ All imports successful")
    else:
        print("❌ Import test failed")
        sys.exit(1)
    
    if test_database_connection():
        print("✅ Database connection test passed")
    else:
        print("❌ Database connection test failed")
        sys.exit(1)
    
    print("-" * 40)
    print("🎉 All tests passed! Ready for debugging.")
    print("\n📝 Instructions:")
    print("1. 在 VS Code 中打開專案")
    print("2. 按 F5 或選擇 'Python: FastAPI Debug' 配置")
    print("3. 在代碼中設置斷點")
    print("4. 訪問 http://127.0.0.1:8000 測試")