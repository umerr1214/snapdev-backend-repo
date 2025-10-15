from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
from typing import Optional

from database import get_users_collection
from models import User, UserCreate, UserResponse

router = APIRouter()

# Security
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Pydantic models
class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None

# Utility functions
def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

from models import UserType

async def get_admin_by_email(email: str):
    users_collection = get_users_collection()
    admin = await users_collection.find_one({"email": email, "user_type": UserType.ADMIN})
    return admin

async def authenticate_admin(email: str, password: str):
    admin = await get_admin_by_email(email)
    if not admin:
        return False
    if not verify_password(password, admin["hashed_password"]):
        return False
    return admin

async def get_current_admin(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    admin = await get_admin_by_email(email=token_data.email)
    if admin is None:
        raise credentials_exception
    return User(**admin)

# Routes
@router.post("/login", response_model=Token)
async def login_admin(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login admin and return access token"""
    admin = await authenticate_admin(form_data.username, form_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin["email"]}, expires_delta=access_token_expires
    )
    user_response = UserResponse(**admin)
    return {"access_token": access_token, "token_type": "bearer", "user": user_response.model_dump(by_alias=True)}

@router.get("/me", response_model=User)
async def read_admin_me(current_admin: User = Depends(get_current_admin)):
    """Get current admin information"""
    return current_admin

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user"""
    users_collection = get_users_collection()
    existing_user = await users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
    )
    
    await users_collection.insert_one(user.model_dump(by_alias=True))
    return user

@router.post("/logout")
async def logout_admin(current_admin: dict = Depends(get_current_admin)):
    """Logout admin (client should remove token)"""
    return {"message": "Successfully logged out"}