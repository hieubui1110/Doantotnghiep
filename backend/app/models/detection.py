import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Detection(Base):
    __tablename__ = "detections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    frame_id = Column(BigInteger, nullable=False)
    vehicle_type = Column(String(50), nullable=False, index=True)  # 'car', 'truck', 'bus', 'motorcycle', 'bicycle'
    confidence = Column(Float, nullable=False)
    bbox = Column(JSONB, nullable=False)  # {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)  # {"track_id": 1, "speed_kmh": 65}
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    camera = relationship("Camera", backref="detections")
