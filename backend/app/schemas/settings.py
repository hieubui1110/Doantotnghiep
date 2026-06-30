from typing import Optional
from app.schemas.auth import BaseSchema


class SettingsDto(BaseSchema):
    """System settings response — maps from ASP.NET SettingsDto."""
    app_name: str
    api_version: str
    detection_threshold: float
    max_cameras: int
    retention_days: int


class UpdateSettingsRequest(BaseSchema):
    """Admin updates system settings — maps from ASP.NET UpdateSettingsRequest."""
    app_name: Optional[str] = None
    detection_threshold: Optional[float] = None
    max_cameras: Optional[int] = None
    retention_days: Optional[int] = None
