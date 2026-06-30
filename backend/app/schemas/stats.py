from datetime import datetime
from typing import Dict, List, Optional
from app.schemas.auth import BaseSchema

class HourlyStatDto(BaseSchema):
    hour: datetime
    total_vehicles: int
    vehicles_by_type: Dict[str, int]

class TimeSeriesStatDto(BaseSchema):
    timestamp: datetime
    total_vehicles: int
    car_count: int
    truck_count: int
    bus_count: int
    motorcycle_count: int
    bicycle_count: int
    violation_count: int

class ViolationStatDto(BaseSchema):
    violation_type: str
    count: int
    percentage: float

class DashboardOverviewDto(BaseSchema):
    total_vehicles_daily: int
    motorcycle_count: int
    car_count: int
    truck_count: int
    bus_count: int
    online_cameras: int
    offline_cameras: int
    total_cameras: int

class CameraLiveDto(BaseSchema):
    camera_id: str
    is_online: bool
    live_traffic_rate: float  # vehicles/min
    recent_detections_count: int
    recent_violations_count: int
