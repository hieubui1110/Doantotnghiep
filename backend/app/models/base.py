# Import declarative Base and all models here
# This is used by Alembic's env.py to auto-generate migrations
from app.core.database import Base
from app.models.operator import Operator
from app.models.camera import Camera
from app.models.detection import Detection
from app.models.violation import Violation
from app.models.traffic_stats import TrafficStat
from app.models.refresh_token import RefreshToken
