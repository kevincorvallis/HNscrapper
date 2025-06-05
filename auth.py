#!/usr/bin/env python3
"""
Firebase Authentication Module for FastAPI
Handles user authentication, token verification, and session management
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', './firebase-service-account.json')
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', 'hnsummary-8edb0')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.getenv('JWT_EXPIRE_MINUTES', '1440'))  # 24 hours

# Pydantic models
class User(BaseModel):
    uid: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    phone_number: Optional[str] = None
    provider_id: str
    email_verified: bool = False
    created_at: datetime
    last_login: datetime

class TokenData(BaseModel):
    uid: Optional[str] = None
    email: Optional[str] = None

class LoginRequest(BaseModel):
    firebase_token: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class FirebaseAuth:
    def __init__(self):
        self.firebase_app = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                if os.path.exists(FIREBASE_SERVICE_ACCOUNT_PATH):
                    cred = credentials.Certificate(FIREBASE_SERVICE_ACCOUNT_PATH)
                    self.firebase_app = firebase_admin.initialize_app(cred, {
                        'projectId': FIREBASE_PROJECT_ID
                    })
                    print("✅ Firebase Admin SDK initialized successfully")
                else:
                    print(f"⚠️ Firebase service account file not found: {FIREBASE_SERVICE_ACCOUNT_PATH}")
                    print("   Authentication features will be limited")
            else:
                self.firebase_app = firebase_admin.get_app()
                print("✅ Firebase Admin SDK already initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            self.firebase_app = None
    
    def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user data"""
        try:
            if not self.firebase_app:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Firebase authentication not available"
                )
            
            # Verify the token with Firebase
            decoded_token = auth.verify_id_token(token)
            return decoded_token
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Firebase token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token for session management"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return encoded_jwt
    
    def verify_access_token(self, token: str) -> TokenData:
        """Verify JWT access token and return token data"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            uid: str = payload.get("sub")
            email: str = payload.get("email")
            if uid is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return TokenData(uid=uid, email=email)
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def create_user_from_firebase(self, firebase_data: Dict[str, Any]) -> User:
        """Create User object from Firebase user data"""
        now = datetime.utcnow()
        
        return User(
            uid=firebase_data.get('uid', ''),
            email=firebase_data.get('email'),
            display_name=firebase_data.get('name'),
            photo_url=firebase_data.get('picture'),
            phone_number=firebase_data.get('phone_number'),
            provider_id=firebase_data.get('firebase', {}).get('sign_in_provider', 'unknown'),
            email_verified=firebase_data.get('email_verified', False),
            created_at=now,
            last_login=now
        )

# Initialize Firebase Auth
firebase_auth = FirebaseAuth()

# Dependency functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    token_data = firebase_auth.verify_access_token(credentials.credentials)
    
    # In a real application, you'd fetch user data from your database
    # For now, we'll create a basic user object
    return User(
        uid=token_data.uid,
        email=token_data.email,
        display_name=token_data.email,
        provider_id="session",
        email_verified=True,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )

async def get_current_user_optional(request: Request) -> Optional[User]:
    """Optional dependency to get current user (doesn't raise exception if not authenticated)"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        token_data = firebase_auth.verify_access_token(token)
        
        return User(
            uid=token_data.uid,
            email=token_data.email,
            display_name=token_data.email,
            provider_id="session",
            email_verified=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
    except:
        return None

# Authentication routes functions
def login_with_firebase(login_request: LoginRequest) -> LoginResponse:
    """Login with Firebase ID token"""
    # Verify Firebase token
    firebase_data = firebase_auth.verify_firebase_token(login_request.firebase_token)
    
    # Create user object
    user = firebase_auth.create_user_from_firebase(firebase_data)
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = firebase_auth.create_access_token(
        data={"sub": user.uid, "email": user.email},
        expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

def logout_user():
    """Logout user (client should delete token)"""
    return {"message": "Successfully logged out"}

def get_user_profile(user: User) -> User:
    """Get current user profile"""
    return user
