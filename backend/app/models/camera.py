import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from app.core.database import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    rtsp_url = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    intersection = Column(String(255), nullable=True)
    direction = Column(String(50), nullable=True)  # 'north', 'south', 'east', 'west', etc.
    status = Column(String(20), nullable=False, default="active")  # 'active', 'inactive', 'maintenance'
    config = Column(JSONB, nullable=False, default=dict)  # {"frame_skip": 5, "confidence_threshold": 0.5, "speed_limit": 60}
    vehicle_types = Column(ARRAY(String), nullable=False, default=list)  # ['car', 'truck', 'bus', 'motorcycle', 'bicycle']
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=lambda: datetime.now(timezone.utc))
