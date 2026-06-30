import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field
from app.schemas.auth import BaseSchema


class UserDto(BaseSchema):
    """Response DTO for user data — maps from ASP.NET UserDto."""
    id: uuid.UUID
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None


class CreateUserRequest(BaseSchema):
    """Admin creates a user — maps from ASP.NET CreateUserRequest."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = Field(None, validation_alias="fullName")
    role: Optional[str] = Field("operator", pattern=r"^(admin|operator)$")


class UpdateUserRequest(BaseSchema):
    """Admin updates a user — maps from ASP.NET UpdateUserRequest."""
    email: Optional[str] = None
    full_name: Optional[str] = Field(None, validation_alias="fullName")
    role: Optional[str] = Field(None, pattern=r"^(admin|operator)$")
    is_active: Optional[bool] = Field(None, validation_alias="isActive")
