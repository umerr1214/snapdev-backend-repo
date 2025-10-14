from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from datetime import datetime
from typing import Optional, Annotated
from enum import Enum
from bson import ObjectId

class UserType(str, Enum):
    ADMIN = "admin"
    USER = "user"

PyObjectId = Annotated[str, BeforeValidator(str)]

class User(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias='_id')
    email: EmailStr
    full_name: str
    hashed_password: str
    user_type: UserType = UserType.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ObjectId: str
        }

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            ObjectId: str
        }

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    user_type: UserType = UserType.USER

class UserResponse(BaseModel):
    id: Optional[PyObjectId] = Field(None, alias='_id')
    email: EmailStr
    full_name: str
    user_type: UserType = UserType.USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)