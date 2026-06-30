import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import Field
from app.schemas.auth import BaseSchema

class CameraDto(BaseSchema):
    id: uuid.UUID

    name: str
    rtsp_url: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    intersection: Optional[str] = None
    direction: Optional[str] = None
    status: str
    config: Dict[str, Any] = Field(default_factory=dict)
    vehicle_types: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

class CreateCameraRequest(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    rtsp_url: str = Field(..., validation_alias="rtspUrl")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    intersection: Optional[str] = None
    direction: Optional[str] = None  # 'north', 'south', 'east', 'west', etc.
    status: Optional[str] = "active"
    config: Optional[Dict[str, Any]] = None
    vehicle_types: Optional[List[str]] = None

class UpdateCameraRequest(BaseSchema):
    name: Optional[str] = None
    rtsp_url: Optional[str] = Field(None, validation_alias="rtspUrl")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    intersection: Optional[str] = None
    direction: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    vehicle_types: Optional[List[str]] = None
