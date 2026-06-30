# Đề Xuất Kiến Trúc Backend — Hệ Thống Giám Sát Giao Thông Thông Minh
> **Đồ Án Tốt Nghiệp** | Backend Architecture Proposal
> Ngày tạo: 07/06/2026
> Stack: Python + FastAPI + PostgreSQL + YOLO + JWT + WebSocket

---

## Mục Lục

1. [Tổng quan Kiến trúc](#1-tổng-quan-kiến-trúc)
2. [Sơ đồ Kiến trúc Hệ thống](#2-sơ-đồ-kiến-trúc-hệ-thống)
3. [YOLO Inference Pipeline](#3-yolo-inference-pipeline)
4. [JWT Authentication](#4-jwt-authentication)
5. [WebSocket Dashboard Real-time](#5-websocket-dashboard-real-time)
6. [Database Schema](#6-database-schema)
7. [Cấu Trúc Thư Mục Dự Án](#7-cấu-trúc-thư-mục-dự-án)
8. [Cài Đặt Môi Trường](#8-cài-đặt-môi-trường)
9. [Code Mẫu (Proof of Concept)](#9-code-mẫu-proof-of-concept)
10. [API Design Guidelines](#10-api-design-guidelines)
11. [Deployment Strategy](#11-deployment-strategy)

---

## 1. Tổng Quan Kiến Trúc

### 1.1 Mô Hình Kiến Trúc

Kiến trúc đề xuất cho Hệ thống Giám sát Giao thông Thông minh sử dụng mô hình **Client-Server** kết hợp **AI Inference Pipeline**. Backend đóng vai trò trung tâm: nhận video từ camera, chạy YOLO detection, lưu kết quả, và cung cấp dashboard real-time qua WebSocket.

```
┌─────────────────┐          ┌──────────────────────────────────────────┐
│   IP Cameras    │  RTSP    │          FastAPI Backend                  │
│  (Giao thông)   │─────────►│                                          │
│  cam_001...N    │          │  ┌─────────────┐  ┌──────────────────┐  │
└─────────────────┘          │  │  YOLO       │  │  REST API        │  │
                             │  │  Inference  │  │  (HTTP/1.1)      │  │
┌─────────────────┐          │  │  Pipeline   │  └────────┬─────────┘  │
│                 │  HTTPS   │  └──────┬──────┘           │            │
│   Dashboard     │◄────────►│         │            ┌─────▼─────────┐  │
│   (Browser)     │  WS/WSS  │  ┌──────▼──────┐    │  WebSocket     │  │
│                 │◄────────►│  │  Detection  │    │  Server        │  │
└─────────────────┘          │  │  Processor  │    │  (Dashboard)   │  │
                             │  └──────┬──────┘    └───────┬────────┘  │
                             │         │                   │           │
                             │  ┌──────▼───────────────────▼────────┐  │
                             │  │        Data Access Layer           │  │
                             │  │   (SQLAlchemy ORM + asyncpg)      │  │
                             │  └──────────────┬────────────────────┘  │
                             └─────────────────│────────────────────────┘
                                               │
                             ┌─────────────────▼────────────────────────┐
                             │              PostgreSQL                   │
                             │  (Cameras, Detections, Violations, ...)  │
                             └──────────────────────────────────────────┘
```

### 1.2 Các Thành Phần Chính

| Thành Phần | Công Nghệ | Vai Trò |
|-----------|-----------|---------|
| **Web Framework** | FastAPI 0.110+ | Xử lý HTTP, routing, DI, WebSocket |
| **ASGI Server** | Uvicorn | Chạy ASGI app, async I/O |
| **AI Model** | YOLO (Ultralytics) | Phát hiện phương tiện, biển số |
| **Database** | PostgreSQL 16 | Lưu trữ detection, violations, cameras |
| **ORM** | SQLAlchemy 2.0 (async) | Object-Relational Mapping |
| **DB Driver** | asyncpg | Async PostgreSQL driver |
| **Migrations** | Alembic | Quản lý database schema |
| **Validation** | Pydantic v2 | Request/Response validation |
| **Authentication** | JWT (python-jose) | Token-based auth cho operators |
| **Password Hash** | bcrypt (passlib) | Mã hóa mật khẩu operator |
| **Video Processing** | OpenCV (cv2) | Đọc RTSP stream, xử lý frame |
| **WebSocket** | FastAPI WebSocket | Dashboard giám sát real-time |
| **Config** | pydantic-settings | Cấu hình từ .env |
| **CORS** | FastAPI Middleware | Cho phép frontend truy cập |
| **Testing** | pytest + httpx | Unit và Integration tests |

---

## 2. Sơ Đồ Kiến Trúc Hệ Thống

### 2.1 Request Flow — REST API

```
Operator (Dashboard Browser)
      │
      │ 1. HTTP Request + JWT Token (Header)
      ▼
┌──────────────────┐
│  CORS Middleware  │  ← Kiểm tra Origin cho phép
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Auth Middleware  │  ← Validate JWT token
└────────┬─────────┘
         │
┌────────▼─────────────────────┐
│     FastAPI Router            │
│  /api/v1/cameras/{id}        │
│  /api/v1/detections          │
│  /api/v1/violations          │
│  /api/v1/stats               │
└────────┬─────────────────────┘
         │
┌────────▼─────────┐
│   Dependency     │  ← get_db(), get_current_operator()
│   Injection      │
└────────┬─────────┘
         │
┌────────▼─────────┐
│  Route Handler   │  ← Business logic (detection, stats)
│  (Async func)    │
└────────┬─────────┘
         │
┌────────▼─────────┐
│   SQLAlchemy     │  ← Async ORM query
│   (asyncpg)      │
└────────┬─────────┘
         │
┌────────▼─────────┐
│   PostgreSQL      │
└──────────────────┘
         │
         │ Response (JSON)
         ▼
    Operator (Browser)
```

### 2.2 YOLO Detection Flow

```
IP Camera (RTSP)                  Backend                          DB
     │                              │                               │
     │── RTSP Video Stream ────────►│                               │
     │                              │                               │
     │                      ┌───────▼──────────┐                    │
     │                      │  Frame Extractor  │                    │
     │                      │  (OpenCV)         │                    │
     │                      └───────┬──────────┘                    │
     │                              │ Frame (numpy array)           │
     │                      ┌───────▼──────────┐                    │
     │                      │  YOLO Inference  │                    │
     │                      │  (detect vehicles)│                    │
     │                      └───────┬──────────┘                    │
     │                              │ Detection Results             │
     │                      ┌───────▼──────────┐                    │
     │                      │  Post-Processing │                    │
     │                      │  - Classify      │                    │
     │                      │  - Track (ID)    │                    │
     │                      │  - Check rules   │                    │
     │                      └───────┬──────────┘                    │
     │                              │                               │
     │                      ┌───────▼──────────┐  Save detection    │
     │                      │  Detection Saver │───────────────────►│
     │                      └───────┬──────────┘                    │
     │                              │                               │
     │                      ┌───────▼──────────┐  Nếu vi phạm      │
     │                      │  Violation Check │───────────────────►│
     │                      │  (red light,     │  Save violation    │
     │                      │   speeding, ...) │                    │
     │                      └───────┬──────────┘                    │
     │                              │                               │
     │                      ┌───────▼──────────┐                    │
     │                      │  WebSocket Push  │                    │
     │                      │  → Dashboard     │                    │
     │                      └──────────────────┘                    │
```

### 2.3 WebSocket Flow — Dashboard

```
Dashboard (Browser)            FastAPI Server                Detection Service
     │                              │                              │
     │── WS Handshake (+ JWT) ─────►│                              │
     │◄── 101 Switching Protocols ──│                              │
     │                              │                              │
     │                              │◄── New detection ────────────│
     │◄── JSON: detection event ────│                              │
     │                              │                              │
     │                              │◄── Violation detected! ─────│
     │◄── JSON: violation alert ────│                              │
     │                              │                              │
     │── Request: camera stats ────►│                              │
     │◄── JSON: stats response ─────│                              │
     │                              │                              │
     │── Close Frame ──────────────►│                              │
     │◄── Close Confirmed ──────────│                              │
```

---

## 3. YOLO Inference Pipeline

### 3.1 Tổng Quan

YOLO (You Only Look Once) là mô hình deep learning cho bài toán **Object Detection** thời gian thực. Trong hệ thống giám sát giao thông, YOLO được sử dụng để:
- **Phát hiện phương tiện**: car, truck, bus, motorcycle, bicycle
- **Nhận dạng biển số xe** (kết hợp OCR)
- **Phát hiện vi phạm**: vượt đèn đỏ, đi sai làn, vượt tốc độ

### 3.2 YOLO Service

```python
# services/yolo_service.py
import asyncio
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Optional
from datetime import datetime, timezone

class YOLOService:
    def __init__(self, model_path: str = "yolo_models/best.pt"):
        self.model = YOLO(model_path)
        self.vehicle_classes = ['car', 'truck', 'bus', 'motorcycle', 'bicycle']

    async def detect_frame(self, frame: np.ndarray) -> List[dict]:
        """Chạy YOLO inference trên 1 frame — async wrapper"""
        loop = asyncio.get_event_loop()
        # Chạy trong thread pool để không block event loop
        results = await loop.run_in_executor(None, lambda: self.model(frame))
        return self._parse_results(results)

    def _parse_results(self, results) -> List[dict]:
        detections = []
        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls)]
                if cls_name in self.vehicle_classes:
                    detections.append({
                        "vehicle_type": cls_name,
                        "confidence": round(float(box.conf), 4),
                        "bbox": {
                            "x1": float(box.xyxy[0][0]),
                            "y1": float(box.xyxy[0][1]),
                            "x2": float(box.xyxy[0][2]),
                            "y2": float(box.xyxy[0][3])
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        return detections

    async def detect_image(self, image_bytes: bytes) -> List[dict]:
        """Detect từ ảnh upload (API endpoint)"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return await self.detect_frame(frame)

yolo_service = YOLOService()
```

### 3.3 Camera Stream Processor

```python
# services/camera_processor.py
import cv2
import asyncio
from app.services.yolo_service import yolo_service
from app.websocket.manager import dashboard_manager

class CameraProcessor:
    def __init__(self, camera_id: str, rtsp_url: str):
        self.camera_id = camera_id
        self.rtsp_url = rtsp_url
        self.is_running = False
        self.frame_skip = 5  # Xử lý mỗi 5 frame (tiết kiệm tài nguyên)

    async def start_processing(self, db_session):
        """Bắt đầu xử lý video stream từ camera"""
        self.is_running = True
        cap = cv2.VideoCapture(self.rtsp_url)
        frame_count = 0

        while self.is_running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(1)
                cap = cv2.VideoCapture(self.rtsp_url)  # Reconnect
                continue

            frame_count += 1
            if frame_count % self.frame_skip != 0:
                continue

            # Chạy YOLO detection
            detections = await yolo_service.detect_frame(frame)

            if detections:
                # Lưu vào DB
                await self.save_detections(db_session, detections, frame_count)

                # Kiểm tra vi phạm
                violations = await self.check_violations(detections)

                # Push real-time đến dashboard qua WebSocket
                await dashboard_manager.broadcast({
                    "type": "detection",
                    "camera_id": self.camera_id,
                    "frame_id": frame_count,
                    "detections": detections,
                    "violations": violations,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

            await asyncio.sleep(0.01)  # Yield control

        cap.release()

    async def check_violations(self, detections: list) -> list:
        """Kiểm tra vi phạm giao thông từ kết quả detection"""
        violations = []
        for det in detections:
            # Ví dụ: kiểm tra vượt đèn đỏ (cần kết hợp logic đèn tín hiệu)
            # Ví dụ: kiểm tra tốc độ (cần tracking liên tục)
            pass
        return violations

    def stop(self):
        self.is_running = False
```

### 3.4 YOLO Detection API Endpoint

```python
# api/v1/detections.py
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/detections", tags=["Detections"])

@router.post("/detect")
async def detect_from_image(
    camera_id: str,
    file: UploadFile = File(...),
    current_operator = Depends(get_current_operator),
    db: AsyncSession = Depends(get_db)
):
    """Upload ảnh/frame → chạy YOLO → trả về kết quả detection"""
    contents = await file.read()
    detections = await yolo_service.detect_image(contents)

    # Lưu kết quả vào DB
    for det in detections:
        detection_record = Detection(
            camera_id=camera_id,
            vehicle_type=det["vehicle_type"],
            confidence=det["confidence"],
            bbox=det["bbox"],
            metadata=det
        )
        db.add(detection_record)
    await db.commit()

    return {"camera_id": camera_id, "count": len(detections), "detections": detections}

@router.get("/")
async def list_detections(
    camera_id: str = None,
    vehicle_type: str = None,
    min_confidence: float = 0.5,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Lấy danh sách detection với filter"""
    query = select(Detection).where(Detection.confidence >= min_confidence)
    if camera_id:
        query = query.where(Detection.camera_id == camera_id)
    if vehicle_type:
        query = query.where(Detection.vehicle_type == vehicle_type)
    query = query.order_by(Detection.detected_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/stats")
async def get_detection_stats(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """Thống kê detection trong N giờ qua"""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Đếm theo loại xe
    vehicle_stats = await db.execute(
        select(Detection.vehicle_type, func.count())
        .where(Detection.detected_at >= cutoff)
        .group_by(Detection.vehicle_type)
    )

    # Đếm theo camera
    camera_stats = await db.execute(
        select(Detection.camera_id, func.count())
        .where(Detection.detected_at >= cutoff)
        .group_by(Detection.camera_id)
    )

    return {
        "period_hours": hours,
        "by_vehicle_type": dict(vehicle_stats.all()),
        "by_camera": dict(camera_stats.all())
    }
```

---

## 4. JWT Authentication

### 4.1 Tổng Quan

JWT xác thực **operators** (nhân viên vận hành hệ thống giám sát). Không phải user thông thường — chỉ những người được cấp tài khoản mới truy cập dashboard và API.

### 4.2 Token Strategy

```
┌──────────────────────────────────────────────────────┐
│               Token Strategy                          │
├──────────────────────┬───────────────────────────────┤
│   Access Token       │   Refresh Token               │
├──────────────────────┼───────────────────────────────┤
│ Hết hạn: 30 phút     │ Hết hạn: 7 ngày              │
│ Dùng cho: API calls  │ Dùng cho: Lấy Access mới      │
│ Lưu: Memory/State    │ Lưu: HttpOnly Cookie          │
│ Gửi qua: Header      │ Gửi qua: Cookie (secure)      │
└──────────────────────┴───────────────────────────────┘
```

### 4.3 Auth Flow

```
1. ĐĂNG NHẬP
   Operator → POST /auth/login (username, password)
   Server: Verify → Tạo Access + Refresh Token
   Response: {"access_token": "...", "token_type": "bearer"}

2. TRUY CẬP DASHBOARD/API
   Operator → GET /api/v1/cameras
   Header: Authorization: Bearer <access_token>
   Server: Validate token → Return data

3. LÀM MỚI TOKEN
   Operator → POST /auth/refresh (cookie: refresh_token)
   Server: Validate → Access Token mới

4. ĐĂNG XUẤT
   Operator → POST /auth/logout
   Server: Xóa refresh token → Clear cookie
```

### 4.4 Implementation

```python
# core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_token(data: dict, expires_delta: timedelta, token_type: str) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc), "type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(operator_id: str, role: str) -> str:
    return create_token(
        data={"sub": operator_id, "role": role},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access"
    )

def create_refresh_token(operator_id: str) -> str:
    return create_token(
        data={"sub": operator_id},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh"
    )

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_operator(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Operator:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token không hợp lệ hoặc đã hết hạn",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise credentials_exception

    operator = await get_operator_by_id(db, payload.get("sub"))
    if not operator or not operator.is_active:
        raise credentials_exception
    return operator

async def require_admin(operator = Depends(get_current_operator)) -> Operator:
    """Chỉ admin mới được thêm/xóa camera, quản lý operator"""
    if operator.role != "admin":
        raise HTTPException(status_code=403, detail="Cần quyền admin")
    return operator
```

```python
# api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login")
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    operator = await get_operator_by_username(db, form_data.username)
    if not operator or not verify_password(form_data.password, operator.hashed_password):
        raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập")

    access_token = create_access_token(str(operator.id), operator.role)
    refresh_token = create_refresh_token(str(operator.id))

    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=True, samesite="lax",
        max_age=7 * 24 * 60 * 60
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"message": "Đăng xuất thành công"}
```

---

## 5. WebSocket Dashboard Real-time

### 5.1 Kiến Trúc

```
                    FastAPI WebSocket Server
                    ┌──────────────────────────────┐
Dashboard 1 ─WS───►│   DashboardManager           │
Dashboard 2 ─WS───►│   ┌────────────────────┐     │
Dashboard 3 ─WS───►│   │  connections: {    │     │
                    │   │    "all": [ws1-3], │     │
                    │   │    "cam_001": [ws1],│     │
                    │   │    "cam_002": [ws2],│     │
                    │   │  }                │     │
                    │   └────────────────────┘     │
                    └──────────────────────────────┘
                              ▲
                              │ Detection events
                    ┌─────────┴────────────┐
                    │  Camera Processors   │
                    │  (YOLO inference)     │
                    └──────────────────────┘
```

### 5.2 Dashboard Manager

```python
# websocket/manager.py
from fastapi import WebSocket
from typing import Dict, List
from datetime import datetime, timezone

class DashboardManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {"all": []}

    async def connect(self, websocket: WebSocket, camera_filter: str = None):
        await websocket.accept()
        self.connections["all"].append(websocket)
        if camera_filter:
            if camera_filter not in self.connections:
                self.connections[camera_filter] = []
            self.connections[camera_filter].append(websocket)

    def disconnect(self, websocket: WebSocket):
        for key in list(self.connections.keys()):
            if websocket in self.connections[key]:
                self.connections[key].remove(websocket)
            if key != "all" and not self.connections[key]:
                del self.connections[key]

    async def broadcast(self, message: dict):
        """Gửi đến tất cả dashboard"""
        for ws in self.connections.get("all", []):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)

    async def send_to_camera_subscribers(self, camera_id: str, message: dict):
        """Gửi đến dashboard đang xem camera cụ thể"""
        for ws in self.connections.get(camera_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(ws)

    async def broadcast_violation_alert(self, violation: dict):
        """Gửi cảnh báo vi phạm đến TẤT CẢ dashboard (ưu tiên cao)"""
        alert = {
            "type": "violation_alert",
            "priority": "high",
            "data": violation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.broadcast(alert)

dashboard_manager = DashboardManager()
```

### 5.3 WebSocket Endpoint

```python
# api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.manager import dashboard_manager
from app.core.security import decode_token

router = APIRouter()

@router.websocket("/ws/dashboard")
async def dashboard_ws(
    websocket: WebSocket,
    token: str = Query(default=None),
    camera_id: str = Query(default=None)
):
    """WebSocket cho dashboard giám sát giao thông"""
    # Xác thực operator
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001, reason="Unauthorized")
        return

    operator_id = payload.get("sub")
    await dashboard_manager.connect(websocket, camera_filter=camera_id)

    try:
        while True:
            command = await websocket.receive_json()

            if command.get("type") == "switch_camera":
                # Operator chuyển sang xem camera khác
                new_camera = command.get("camera_id")
                dashboard_manager.disconnect(websocket)
                await dashboard_manager.connect(websocket, camera_filter=new_camera)

            elif command.get("type") == "request_stats":
                # Operator yêu cầu thống kê
                stats = await get_realtime_stats()
                await websocket.send_json({"type": "stats", "data": stats})

            elif command.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)

@router.websocket("/ws/camera/{camera_id}/stream")
async def camera_stream_ws(
    websocket: WebSocket,
    camera_id: str,
    token: str = Query(default=None)
):
    """WebSocket stream kết quả detection real-time từ 1 camera"""
    if not token:
        await websocket.close(code=4001, reason="Token required")
        return
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await dashboard_manager.connect(websocket, camera_filter=camera_id)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        dashboard_manager.disconnect(websocket)
```

### 5.4 Client JavaScript (Dashboard)

```javascript
const accessToken = localStorage.getItem('access_token');
const ws = new WebSocket(
    `wss://api.traffic-system.com/ws/dashboard?token=${accessToken}`
);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);

    switch (data.type) {
        case 'detection':
            updateVehicleCount(data.detections);
            drawBoundingBoxes(data.camera_id, data.detections);
            break;

        case 'violation_alert':
            showViolationAlert(data.data);  // Hiện cảnh báo nổi bật
            playAlertSound();
            break;

        case 'stats':
            updateDashboardCharts(data.data);
            break;
    }
};

// Chuyển camera
function switchCamera(cameraId) {
    ws.send(JSON.stringify({type: 'switch_camera', camera_id: cameraId}));
}
```

---

## 6. Database Schema

### 6.1 Schema Chính

```sql
-- ============================================
-- OPERATORS TABLE (Nhân viên vận hành)
-- ============================================
CREATE TABLE operators (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255),
    role        VARCHAR(20) NOT NULL DEFAULT 'operator',  -- 'operator', 'admin'
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);

CREATE INDEX idx_operators_username ON operators(username);

-- ============================================
-- CAMERAS TABLE (Camera giao thông)
-- ============================================
CREATE TABLE cameras (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    rtsp_url      TEXT NOT NULL,
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    address       TEXT,
    intersection  VARCHAR(255),                    -- Tên giao lộ
    direction     VARCHAR(50),                     -- 'north', 'south', 'east', 'west'
    status        VARCHAR(20) NOT NULL DEFAULT 'active',  -- 'active', 'inactive', 'maintenance'
    config        JSONB DEFAULT '{}',              -- Cấu hình riêng (frame_skip, confidence_threshold)
    vehicle_types TEXT[] DEFAULT '{}',             -- Loại xe thường gặp tại giao lộ này
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ
);

CREATE INDEX idx_cameras_status ON cameras(status) WHERE status = 'active';
CREATE INDEX idx_cameras_location ON cameras(latitude, longitude);

-- ============================================
-- DETECTIONS TABLE (Kết quả phát hiện YOLO)
-- ============================================
CREATE TABLE detections (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id     UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    frame_id      BIGINT NOT NULL,
    vehicle_type  VARCHAR(50) NOT NULL,            -- 'car', 'truck', 'bus', 'motorcycle'
    confidence    FLOAT NOT NULL,
    bbox          JSONB NOT NULL,                  -- {"x1": 100, "y1": 200, "x2": 300, "y2": 400}
    metadata      JSONB DEFAULT '{}',              -- license_plate, speed, color, direction
    detected_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Partitioned by date cho hiệu năng (hàng triệu records/ngày)
-- CREATE TABLE detections ... PARTITION BY RANGE (detected_at);

CREATE INDEX idx_detections_camera    ON detections(camera_id, detected_at DESC);
CREATE INDEX idx_detections_type      ON detections(vehicle_type, detected_at DESC);
CREATE INDEX idx_detections_metadata  ON detections USING GIN(metadata);
CREATE INDEX idx_detections_time      ON detections(detected_at DESC);

-- ============================================
-- VIOLATIONS TABLE (Vi phạm giao thông)
-- ============================================
CREATE TABLE violations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id    UUID REFERENCES detections(id),
    camera_id       UUID NOT NULL REFERENCES cameras(id),
    violation_type  VARCHAR(50) NOT NULL,          -- 'red_light', 'speeding', 'wrong_lane', 'no_helmet'
    vehicle_type    VARCHAR(50) NOT NULL,
    license_plate   VARCHAR(20),
    confidence      FLOAT NOT NULL,
    evidence_url    TEXT,                          -- URL ảnh bằng chứng vi phạm
    metadata        JSONB DEFAULT '{}',            -- speed_kmh, signal_state, lane_info
    is_confirmed    BOOLEAN NOT NULL DEFAULT FALSE,  -- Đã xác nhận bởi operator
    confirmed_by    UUID REFERENCES operators(id),
    notes           TEXT,                          -- Ghi chú của operator
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_violations_camera   ON violations(camera_id, created_at DESC);
CREATE INDEX idx_violations_type     ON violations(violation_type, created_at DESC);
CREATE INDEX idx_violations_plate    ON violations(license_plate);
CREATE INDEX idx_violations_unconfirmed ON violations(is_confirmed) WHERE is_confirmed = FALSE;

-- Full-text search cho biển số
CREATE INDEX idx_violations_search ON violations
    USING GIN(to_tsvector('simple', COALESCE(license_plate, '') || ' ' || COALESCE(notes, '')));

-- ============================================
-- TRAFFIC_STATS TABLE (Thống kê lưu lượng theo giờ)
-- ============================================
CREATE TABLE traffic_stats (
    camera_id       UUID NOT NULL REFERENCES cameras(id),
    hour            TIMESTAMPTZ NOT NULL,          -- Đầu mỗi giờ
    total_vehicles  INTEGER DEFAULT 0,
    car_count       INTEGER DEFAULT 0,
    truck_count     INTEGER DEFAULT 0,
    bus_count       INTEGER DEFAULT 0,
    motorcycle_count INTEGER DEFAULT 0,
    bicycle_count   INTEGER DEFAULT 0,
    violation_count INTEGER DEFAULT 0,
    avg_speed       FLOAT,
    PRIMARY KEY (camera_id, hour)
);

CREATE INDEX idx_traffic_stats_hour ON traffic_stats(hour DESC);

-- ============================================
-- REFRESH TOKENS TABLE
-- ============================================
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 6.2 Sơ Đồ ERD

```
operators
  │─── id (UUID, PK)
  │─── username (UNIQUE)
  │─── role ('operator' / 'admin')
  │
  └──── confirms ──── violations
                        │─── id (UUID, PK)
                        │─── violation_type
                        │─── license_plate
                        │─── evidence_url
                        │─── is_confirmed
                        │
cameras ────────────────┤
  │─── id (UUID, PK)    │
  │─── name             │
  │─── rtsp_url         │
  │─── lat/lng          │
  │─── intersection     │
  │─── status           │
  │                     │
  ├──── 1:N ──── detections
  │                │─── id (UUID, PK)
  │                │─── vehicle_type
  │                │─── confidence
  │                │─── bbox (JSONB)
  │                │─── metadata (JSONB)
  │                └─── detected_at (TIMESTAMPTZ)
  │
  └──── 1:N ──── traffic_stats
                   │─── camera_id + hour (PK)
                   │─── total_vehicles
                   │─── car/truck/bus/moto count
                   └─── violation_count
```

---

## 7. Cấu Trúc Thư Mục Dự Án

```
traffic-monitoring/
├── 📁 app/
│   ├── 📄 main.py                    # FastAPI app, lifespan, middleware
│   ├── 📁 api/
│   │   └── 📁 v1/
│   │       ├── 📄 router.py          # Tập hợp tất cả routers
│   │       ├── 📄 auth.py            # /auth/login, /auth/logout
│   │       ├── 📄 cameras.py         # /cameras CRUD
│   │       ├── 📄 detections.py      # /detections, /detect
│   │       ├── 📄 violations.py      # /violations CRUD
│   │       ├── 📄 stats.py           # /stats thống kê lưu lượng
│   │       └── 📄 websocket.py       # WebSocket dashboard
│   │
│   ├── 📁 core/
│   │   ├── 📄 config.py              # Settings (Pydantic BaseSettings)
│   │   ├── 📄 database.py            # Async engine, session, get_db
│   │   └── 📄 security.py            # JWT, bcrypt
│   │
│   ├── 📁 models/                    # SQLAlchemy ORM Models
│   │   ├── 📄 operator.py
│   │   ├── 📄 camera.py
│   │   ├── 📄 detection.py
│   │   ├── 📄 violation.py
│   │   └── 📄 traffic_stats.py
│   │
│   ├── 📁 schemas/                   # Pydantic Schemas
│   │   ├── 📄 auth.py
│   │   ├── 📄 camera.py
│   │   ├── 📄 detection.py
│   │   ├── 📄 violation.py
│   │   └── 📄 stats.py
│   │
│   ├── 📁 services/                  # Business Logic
│   │   ├── 📄 yolo_service.py        # YOLO inference wrapper
│   │   ├── 📄 camera_processor.py    # Xử lý video stream
│   │   ├── 📄 violation_checker.py   # Logic phát hiện vi phạm
│   │   ├── 📄 stats_service.py       # Tổng hợp thống kê
│   │   └── 📄 alert_service.py       # Gửi cảnh báo vi phạm
│   │
│   ├── 📁 crud/                      # Database operations
│   │   ├── 📄 camera.py
│   │   ├── 📄 detection.py
│   │   └── 📄 violation.py
│   │
│   ├── 📁 dependencies/              # FastAPI Dependencies
│   │   ├── 📄 auth.py                # get_current_operator, require_admin
│   │   └── 📄 pagination.py
│   │
│   └── 📁 websocket/
│       └── 📄 manager.py             # DashboardManager
│
├── 📁 yolo_models/                   # YOLO model weights
│   ├── 📄 best.pt                    # Model đã train cho giao thông
│   └── 📄 README.md                  # Thông tin model
│
├── 📁 alembic/                       # Database Migrations
│   ├── 📄 env.py
│   └── 📁 versions/
│
├── 📁 tests/
│   ├── 📄 conftest.py
│   ├── 📄 test_auth.py
│   ├── 📄 test_detections.py
│   ├── 📄 test_cameras.py
│   └── 📄 test_violations.py
│
├── 📄 .env
├── 📄 .env.example
├── 📄 requirements.txt
├── 📄 alembic.ini
├── 📄 Dockerfile
├── 📄 docker-compose.yml
└── 📄 README.md
```

---

## 8. Cài Đặt Môi Trường

### 8.1 File .env

```env
# App
APP_NAME="Traffic Monitoring System"
APP_VERSION="1.0.0"
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/traffic_db

# JWT
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# YOLO
YOLO_MODEL_PATH=yolo_models/best.pt
YOLO_CONFIDENCE_THRESHOLD=0.5
YOLO_FRAME_SKIP=5

# URLs
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 8.2 File requirements.txt

```txt
# Core
fastapi==0.111.0
uvicorn[standard]==0.29.0

# Database
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1

# Validation & Settings
pydantic[email]==2.7.1
pydantic-settings==2.2.1

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI / YOLO
ultralytics>=8.2.0
opencv-python-headless>=4.9.0
numpy>=1.26.0
torch>=2.2.0

# Utils
python-multipart==0.0.9
httpx==0.27.0

# Testing
pytest==8.2.0
pytest-asyncio==0.23.6
```

### 8.3 Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: traffic_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: traffic_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    container_name: traffic_api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:password@postgres:5432/traffic_db
      YOLO_MODEL_PATH: /app/yolo_models/best.pt
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - .:/app
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1           # GPU cho YOLO inference
              capabilities: [gpu]

volumes:
  postgres_data:
```

---

## 9. Code Mẫu (Proof of Concept)

### 9.1 app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.services.yolo_service import yolo_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Tạo tables + Load YOLO model
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✅ YOLO model loaded: {settings.YOLO_MODEL_PATH}")
    print(f"✅ Database connected")
    yield
    # Shutdown
    await engine.dispose()
    print("🔴 Server shutdown")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API Backend cho Hệ thống Giám sát Giao thông Thông minh - Đồ Án Tốt Nghiệp",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "system": "Traffic Monitoring", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
```

### 9.2 Chạy Ứng Dụng

```bash
# 1. Tạo môi trường ảo
python -m venv venv
venv\Scripts\activate          # Windows

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Khởi động PostgreSQL
docker-compose up -d postgres

# 4. Chạy migrations
alembic upgrade head

# 5. Chạy server
uvicorn app.main:app --reload --port 8000

# 6. Mở tài liệu API
# Swagger UI: http://localhost:8000/docs
# ReDoc:      http://localhost:8000/redoc
```

---

## 10. API Design Guidelines

### 10.1 Naming Conventions

```
# Authentication
POST   /api/v1/auth/login        → Đăng nhập operator
POST   /api/v1/auth/logout       → Đăng xuất
POST   /api/v1/auth/refresh      → Làm mới token

# Cameras
GET    /api/v1/cameras           → Danh sách camera
GET    /api/v1/cameras/{id}      → Chi tiết camera
POST   /api/v1/cameras           → Thêm camera mới (admin)
PUT    /api/v1/cameras/{id}      → Cập nhật camera (admin)
DELETE /api/v1/cameras/{id}      → Xóa camera (admin)

# Detections
POST   /api/v1/detections/detect → Upload ảnh → YOLO detection
GET    /api/v1/detections        → Lịch sử detection (filter)
GET    /api/v1/detections/stats  → Thống kê detection

# Violations
GET    /api/v1/violations        → Danh sách vi phạm
GET    /api/v1/violations/{id}   → Chi tiết vi phạm
PATCH  /api/v1/violations/{id}   → Xác nhận/ghi chú vi phạm
GET    /api/v1/violations/search → Tìm kiếm theo biển số

# Statistics
GET    /api/v1/stats/traffic     → Lưu lượng giao thông theo giờ
GET    /api/v1/stats/violations  → Thống kê vi phạm
GET    /api/v1/stats/cameras     → Thống kê theo camera

# WebSocket
WS     /ws/dashboard             → Dashboard giám sát real-time
WS     /ws/camera/{id}/stream    → Stream detection từ 1 camera
```

### 10.2 Response Format

```json
// Detection Success
{
  "success": true,
  "data": {
    "camera_id": "cam_001",
    "count": 5,
    "detections": [
      {
        "vehicle_type": "car",
        "confidence": 0.97,
        "bbox": {"x1": 150, "y1": 200, "x2": 400, "y2": 500},
        "license_plate": "30A-12345"
      }
    ]
  }
}

// Violation Alert (WebSocket)
{
  "type": "violation_alert",
  "priority": "high",
  "data": {
    "camera_id": "cam_003",
    "violation_type": "red_light",
    "vehicle_type": "car",
    "license_plate": "51B-67890",
    "confidence": 0.92,
    "evidence_url": "/evidence/2026/06/07/cam003_123456.jpg"
  }
}

// Error Response
{
  "success": false,
  "error": {
    "code": "CAMERA_NOT_FOUND",
    "message": "Camera cam_999 không tồn tại"
  }
}
```

### 10.3 HTTP Status Codes

```
200 OK           → GET, PUT, PATCH thành công
201 Created      → POST tạo camera/operator mới
204 No Content   → DELETE thành công
400 Bad Request  → Dữ liệu đầu vào sai
401 Unauthorized → Token hết hạn / chưa đăng nhập
403 Forbidden    → Operator không có quyền admin
404 Not Found    → Camera/Detection không tồn tại
422 Unprocessable → Validation error (Pydantic)
500 Server Error → Lỗi YOLO inference hoặc DB
```

---

## 11. Deployment Strategy

### 11.1 Môi Trường

```
Development:  uvicorn --reload (local, CPU inference)
Staging:      Docker + PostgreSQL (VPS, GPU nếu có)
Production:   Docker + PostgreSQL + Nginx + GPU server
```

### 11.2 Nginx Config (Production)

```nginx
server {
    listen 443 ssl;
    server_name traffic-system.yourdomain.com;

    # REST API
    location /api/ {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 50M;     # Cho upload ảnh lớn
    }

    # WebSocket Dashboard
    location /ws/ {
        proxy_pass http://app:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # Swagger docs
    location /docs {
        proxy_pass http://app:8000;
    }
}
```

### 11.3 Free/Low-cost Hosting cho Đồ Án

| Service | Loại | Free Tier | Ghi chú |
|---------|------|-----------|---------|
| **Railway** | PaaS | 5$/tháng credit | Chạy được Docker |
| **Render** | PaaS | 512MB RAM | Sleep sau 15 phút |
| **Supabase** | PostgreSQL | 500MB DB | Managed PostgreSQL |
| **Neon** | PostgreSQL | 512MB DB | Serverless PostgreSQL |
| **Google Colab** | GPU | Miễn phí | Cho YOLO training/testing |

> **Khuyến nghị:** Backend → Railway; Database → Supabase; YOLO Training → Google Colab

---

## Tóm Tắt Kiến Trúc

```
┌──────────────────────────────────────────────────────────────────┐
│          STACK — HỆ THỐNG GIÁM SÁT GIAO THÔNG                    │
├────────────────────┬─────────────────────────────────────────────┤
│  Language          │  Python 3.11+                                │
│  Framework         │  FastAPI 0.111+ (ASGI + async)              │
│  ASGI Server       │  Uvicorn                                    │
│  AI Model          │  YOLO (Ultralytics) — Vehicle Detection    │
│  Video Processing  │  OpenCV (cv2) — RTSP stream, frame decode  │
│  Database          │  PostgreSQL 16 (JSONB, UUID, TIMESTAMPTZ)   │
│  ORM              │  SQLAlchemy 2.0 (async + asyncpg)            │
│  Migrations        │  Alembic                                    │
│  Auth              │  JWT (python-jose) + bcrypt                 │
│  Real-time         │  FastAPI WebSocket (dashboard)              │
│  Validation        │  Pydantic v2                                │
│  Testing           │  pytest + httpx                              │
│  Container         │  Docker + docker-compose (+GPU support)     │
│  Reverse Proxy     │  Nginx                                      │
└────────────────────┴─────────────────────────────────────────────┘
```

---

*Đề xuất Kiến trúc Backend | Hệ thống Giám sát Giao thông Thông minh | 07/06/2026*
