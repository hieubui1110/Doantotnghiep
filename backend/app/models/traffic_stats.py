from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class TrafficStat(Base):
    __tablename__ = "traffic_stats"

    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    hour = Column(DateTime(timezone=True), primary_key=True, nullable=False, index=True)
    total_vehicles = Column(Integer, nullable=False, default=0)
    car_count = Column(Integer, nullable=False, default=0)
    truck_count = Column(Integer, nullable=False, default=0)
    bus_count = Column(Integer, nullable=False, default=0)
    motorcycle_count = Column(Integer, nullable=False, default=0)
    bicycle_count = Column(Integer, nullable=False, default=0)
    violation_count = Column(Integer, nullable=False, default=0)
    avg_speed = Column(Float, nullable=True)

    # Relationships
    camera = relationship("Camera", backref="traffic_stats")
