from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.enums.roles import UserRole


class RegisterRequest(BaseModel):
    organization_id: UUID
    role: UserRole = UserRole.ADMIN
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    organization_id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime