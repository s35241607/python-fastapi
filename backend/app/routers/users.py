from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models
from app.database import get_db

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 🔍 Debug point: 檢查輸入資料
    print(f"🔍 Creating user: {user.username}, {user.email}")
    
    # 檢查用戶是否已存在
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        print(f"❌ User already exists: {user.email}")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # 🔍 Debug point: 在這裡設置斷點來檢查密碼處理
    fake_hashed_password = user.password + "notreallyhashed"
    print(f"🔍 Hashed password length: {len(fake_hashed_password)}")
    
    # 創建新用戶
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=fake_hashed_password
    )
    
    # 🔍 Debug point: 資料庫操作
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    print(f"✅ User created successfully: ID {db_user.id}")
    return db_user

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # 🔍 Debug point: 查詢參數
    print(f"🔍 Fetching users: skip={skip}, limit={limit}")
    
    users = db.query(models.User).offset(skip).limit(limit).all()
    
    # 🔍 Debug point: 查詢結果
    print(f"🔍 Found {len(users)} users")
    
    return users

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user