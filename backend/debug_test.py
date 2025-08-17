#!/usr/bin/env python3
"""
Debug 測試腳本 - 用於測試斷點只停在你的代碼中
"""
import json
from app.database import get_db
from app.models import User

def test_debug_my_code_only():
    """測試函數 - 在這裡設置斷點"""
    print("🔍 開始 debug 測試...")
    
    # 這裡設置斷點 - 應該會停在這裡
    data = {"name": "測試用戶", "email": "test@example.com"}
    
    # 這個 json.dumps 調用不應該進入 json 庫的內部代碼
    json_data = json.dumps(data, ensure_ascii=False)
    
    # 這裡也設置斷點 - 應該會停在這裡
    print(f"✅ JSON 數據: {json_data}")
    
    return json_data

if __name__ == "__main__":
    result = test_debug_my_code_only()
    print(f"🎉 測試完成: {result}")