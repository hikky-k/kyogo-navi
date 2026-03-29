"""ユーザー関連スキーマ"""

from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    notification_settings_json: dict | None = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    notification_settings_json: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
