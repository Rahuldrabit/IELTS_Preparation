from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime, timedelta

import os

from shared.database import get_db
from shared.models.core import User
from shared.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user
)
from services.auth.schemas import UserCreate, UserLogin, GoogleLogin, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

@router.post("/signup", response_model=Token)
async def signup(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    hashed_pwd = get_password_hash(user_in.password)
    
    new_user = User(
        name=user_in.name,
        university_name=user_in.university_name,
        email=user_in.email,
        hashed_password=hashed_pwd,
        is_pro=True,
        pro_valid_until=datetime.utcnow() + timedelta(days=2)
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    access_token = create_access_token(subject=str(new_user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "avatar_url": new_user.avatar_url,
            "current_band": new_user.current_band,
            "target_band": new_user.target_band,
            "is_pro": new_user.is_pro,
            "pro_valid_until": new_user.pro_valid_until.isoformat() if new_user.pro_valid_until else None
        }
    }

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user_in.email))
    user = result.scalars().first()
    
    if not user or not user.hashed_password:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
        
    access_token = create_access_token(subject=str(user.id))
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "avatar_url": user.avatar_url,
            "current_band": user.current_band,
            "target_band": user.target_band,
            "is_pro": user.is_pro,
            "pro_valid_until": user.pro_valid_until.isoformat() if user.pro_valid_until else None
        }
    }

@router.post("/google", response_model=Token)
async def google_auth(payload: GoogleLogin, db: AsyncSession = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            payload.credential, requests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo['email']
        name = idinfo.get('name', '')
        google_id = idinfo['sub']
        avatar_url = idinfo.get('picture', '')
        
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        
        if not user:
            # Create user if doesn't exist
            user = User(
                name=name,
                email=email,
                google_id=google_id,
                avatar_url=avatar_url,
                is_pro=True,
                pro_valid_until=datetime.utcnow() + timedelta(days=2)
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            # Update google_id if not present
            if not user.google_id:
                user.google_id = google_id
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)
            
        access_token = create_access_token(subject=str(user.id))
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "current_band": user.current_band,
                "target_band": user.target_band,
                "is_pro": user.is_pro,
                "pro_valid_until": user.pro_valid_until.isoformat() if user.pro_valid_until else None
            }
        }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "current_band": current_user.current_band,
        "target_band": current_user.target_band,
        "is_pro": current_user.is_pro,
        "pro_valid_until": current_user.pro_valid_until.isoformat() if current_user.pro_valid_until else None
    }
