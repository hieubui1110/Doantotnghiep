from fastapi import APIRouter, Depends

from app.core.config import settings
from app.dependencies.auth import get_current_operator, require_admin
from app.models.operator import Operator
from app.schemas.settings import SettingsDto, UpdateSettingsRequest

router = APIRouter()

# In-memory settings override (in production, store in DB)
_settings_overrides: dict = {}


@router.get("", response_model=SettingsDto)
async def get_settings(
    current_operator: Operator = Depends(get_current_operator)
):
    """Lấy cấu hình hệ thống — tương đương GET /api/settings trong ASP.NET."""
    return SettingsDto(
        app_name=_settings_overrides.get("app_name", settings.APP_NAME),
        api_version=settings.APP_VERSION,
        detection_threshold=_settings_overrides.get(
            "detection_threshold", settings.YOLO_CONFIDENCE_THRESHOLD
        ),
        max_cameras=_settings_overrides.get("max_cameras", 100),
        retention_days=_settings_overrides.get("retention_days", 90)
    )


@router.put("", response_model=SettingsDto)
async def update_settings(
    request: UpdateSettingsRequest,
    current_operator: Operator = Depends(require_admin)
):
    """Admin cập nhật cấu hình — tương đương PUT /api/settings trong ASP.NET.
    NOTE: Lưu in-memory. Production nên lưu vào bảng settings trong DB."""
    update_data = request.model_dump(exclude_unset=True)
    _settings_overrides.update(update_data)

    return SettingsDto(
        app_name=_settings_overrides.get("app_name", settings.APP_NAME),
        api_version=settings.APP_VERSION,
        detection_threshold=_settings_overrides.get(
            "detection_threshold", settings.YOLO_CONFIDENCE_THRESHOLD
        ),
        max_cameras=_settings_overrides.get("max_cameras", 100),
        retention_days=_settings_overrides.get("retention_days", 90)
    )
