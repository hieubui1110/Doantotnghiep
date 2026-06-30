# Báo Cáo: FastAPI vs Flask
> **Đồ Án Tốt Nghiệp** | Nghiên cứu Backend Framework cho Hệ Thống Giám Sát Giao Thông Thông Minh
> Ngày tạo: 07/06/2026

---

## Mục Lục

1. [Tổng quan về FastAPI](#1-tổng-quan-về-fastapi)
2. [Tổng quan về Flask](#2-tổng-quan-về-flask)
3. [So sánh Chi tiết](#3-so-sánh-chi-tiết)
4. [Benchmark Hiệu Năng](#4-benchmark-hiệu-năng)
5. [Tích Hợp với YOLO và Xử Lý Video](#5-tích-hợp-với-yolo-và-xử-lý-video)
6. [JWT Authentication](#6-jwt-authentication)
7. [WebSocket cho Dashboard Real-time](#7-websocket-cho-dashboard-real-time)
8. [Khuyến Nghị cho Hệ Thống Giám Sát Giao Thông](#8-khuyến-nghị-cho-hệ-thống-giám-sát-giao-thông)
9. [Kết Luận](#9-kết-luận)

---

## 1. Tổng Quan về FastAPI

### 1.1 Giới thiệu
FastAPI là một web framework hiện đại, hiệu năng cao cho Python, được xây dựng dựa trên **Starlette** (ASGI framework) và **Pydantic** (data validation). Ra mắt năm 2018 bởi Sebastián Ramírez, FastAPI nhanh chóng trở thành một trong những framework Python phổ biến nhất nhờ hiệu năng vượt trội và trải nghiệm developer tuyệt vời.

```
FastAPI = Starlette (ASGI/HTTP) + Pydantic (Validation) + Python Type Hints
```

### 1.2 Kiến Trúc

```
┌──────────────────────────────────────────────┐
│                  FastAPI App                  │
├──────────────────────────────────────────────┤
│  Route Layer     │  Pydantic Models          │
│  (Path Params,   │  (Request/Response        │
│   Query Params)  │   Validation & Serializ.) │
├──────────────────────────────────────────────┤
│          Starlette (ASGI Core)               │
│  (Middleware, WebSocket, Background Tasks)   │
├──────────────────────────────────────────────┤
│       Uvicorn / Hypercorn (ASGI Server)      │
└──────────────────────────────────────────────┘
```

**Giao thức:** ASGI (Asynchronous Server Gateway Interface) — hỗ trợ xử lý bất đồng bộ (async/await) và WebSocket native. Đây là yếu tố quan trọng khi hệ thống cần tiếp nhận và xử lý đồng thời nhiều luồng video từ các camera giao thông.

### 1.3 Tính Năng Nổi Bật

#### ✅ Tự động tạo tài liệu API (Auto-generated Docs)
FastAPI tự động tạo tài liệu tương tác dựa trên OpenAPI 3.0 mà không cần cấu hình thêm:
- **Swagger UI** tại `/docs`
- **ReDoc** tại `/redoc`

```python
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Traffic Monitoring API", version="1.0.0")

class DetectionResult(BaseModel):
    vehicle_type: str        # 'car', 'truck', 'motorcycle', 'bus'
    confidence: float        # 0.0 - 1.0
    bbox: List[float]        # [x1, y1, x2, y2]
    license_plate: str = None

@app.post("/api/v1/detections/", response_model=List[DetectionResult], tags=["Detections"])
async def submit_detection(camera_id: str, results: List[DetectionResult]):
    """
    Nhận kết quả phát hiện phương tiện từ YOLO model.
    - **camera_id**: ID camera giao thông
    - **results**: Danh sách phương tiện đã phát hiện
    """
    # Lưu kết quả vào DB
    return results
```
> Tài liệu trên sẽ tự động xuất hiện ở `/docs` với giao diện tương tác — rất hữu ích khi demo hệ thống giám sát.

#### ✅ Dependency Injection (DI)
Hệ thống DI tích hợp sẵn, giúp quản lý dependencies như database connection, authentication, và YOLO model instance:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_operator(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Xác thực nhân viên vận hành hệ thống giám sát"""
    operator = await verify_token(token, db)
    if not operator:
        raise HTTPException(status_code=401, detail="Không có quyền truy cập hệ thống")
    return operator

@app.get("/api/v1/cameras/")
async def list_cameras(current_operator = Depends(get_current_operator)):
    return await get_all_cameras()
```

#### ✅ Type Hints & Validation tự động
Python type hints kết hợp Pydantic để validate dữ liệu phát hiện giao thông:

```python
from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum

class VehicleType(str, Enum):
    car = "car"
    truck = "truck"
    motorcycle = "motorcycle"
    bus = "bus"
    bicycle = "bicycle"

class TrafficViolation(BaseModel):
    camera_id: str
    vehicle_type: VehicleType
    violation_type: str          # 'red_light', 'wrong_lane', 'speeding'
    license_plate: str
    confidence: float
    timestamp: datetime
    image_url: str

    @field_validator('confidence')
    def confidence_range(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence phải nằm trong khoảng 0.0 - 1.0')
        return v
```
> Nếu dữ liệu phát hiện sai định dạng → FastAPI tự động trả về lỗi 422 với thông báo chi tiết.

#### ✅ Hỗ trợ Async/Await Native
Xử lý bất đồng bộ là **yếu tố then chốt** khi hệ thống cần nhận dữ liệu từ hàng chục camera đồng thời:

```python
import asyncio

@app.get("/api/v1/traffic/stats")
async def get_traffic_stats(db: AsyncSession = Depends(get_db)):
    # Truy vấn song song — không block event loop
    vehicle_count, violation_count, active_cameras = await asyncio.gather(
        count_vehicles_today(db),
        count_violations_today(db),
        count_active_cameras(db)
    )
    return {
        "vehicles_detected": vehicle_count,
        "violations_today": violation_count,
        "active_cameras": active_cameras
    }
```

### 1.4 Ưu Điểm của FastAPI
| # | Ưu điểm | Ý nghĩa với Hệ thống Giám sát Giao thông |
|---|---------|------------------------------------------|
| 1 | **Hiệu năng cao** | Xử lý đồng thời nhiều luồng video từ camera |
| 2 | **Tự động docs** | Demo hệ thống dễ dàng khi bảo vệ đồ án |
| 3 | **Type safety** | Đảm bảo dữ liệu detection chính xác (bbox, confidence) |
| 4 | **DI tích hợp** | Quản lý YOLO model, DB connection sạch sẽ |
| 5 | **WebSocket native** | Dashboard giám sát real-time |
| 6 | **Background Tasks** | Xử lý video nền, gửi cảnh báo vi phạm |
| 7 | **Standards-based** | OpenAPI 3.0 chuẩn cho tích hợp với hệ thống khác |

### 1.5 Nhược Điểm của FastAPI
| # | Nhược điểm | Mô tả |
|---|-----------|-------|
| 1 | **Còn tương đối mới** | Ít tài liệu tiếng Việt, cộng đồng nhỏ hơn Flask |
| 2 | **Phức tạp hơn Flask** | Cần hiểu về async/await, ASGI |
| 3 | **Phụ thuộc Pydantic** | Cần học thêm Pydantic nếu chưa quen |
| 4 | **Debug khó hơn** | Async code đôi khi khó debug hơn sync code |

---

## 2. Tổng Quan về Flask

### 2.1 Giới thiệu
Flask là một **micro web framework** cho Python, ra mắt năm 2010 bởi Armin Ronacher. Triết lý thiết kế của Flask là "micro" — tức là giữ core đơn giản, nhỏ gọn, và để developer tự chọn các thành phần mở rộng theo nhu cầu.

```
Flask = Werkzeug (WSGI toolkit) + Jinja2 (Template Engine) + Click (CLI)
```

### 2.2 Kiến Trúc

```
┌──────────────────────────────────────────────┐
│                  Flask App                    │
├──────────────────────────────────────────────┤
│  Blueprints      │  Request Context          │
│  (Module-based   │  (g, request, session,    │
│   routing)       │   current_app globals)    │
├──────────────────────────────────────────────┤
│              Werkzeug (WSGI Core)            │
│  (Routing, Request/Response, DevServer)      │
├──────────────────────────────────────────────┤
│       Gunicorn / uWSGI (WSGI Server)         │
└──────────────────────────────────────────────┘
```

**Giao thức:** WSGI (Web Server Gateway Interface) — xử lý đồng bộ theo mặc định. Hạn chế khi cần tiếp nhận dữ liệu real-time từ nhiều camera giao thông đồng thời.

### 2.3 Tính Năng Nổi Bật

#### ✅ Đơn giản và nhanh để bắt đầu
```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/detections', methods=['POST'])
def submit_detection():
    data = request.get_json()
    # Xử lý kết quả detection từ YOLO
    return jsonify({"message": "Detection saved", "count": len(data)}), 201
```

#### ✅ Blueprints — Module hóa ứng dụng
```python
# cameras/routes.py
from flask import Blueprint

cameras_bp = Blueprint('cameras', __name__, url_prefix='/cameras')

@cameras_bp.route('/', methods=['GET'])
def list_cameras():
    ...

# app.py
from cameras.routes import cameras_bp
app.register_blueprint(cameras_bp)
```

#### ✅ Hệ sinh thái extension phong phú
- **Flask-SQLAlchemy** — ORM
- **Flask-JWT-Extended** — JWT Authentication
- **Flask-SocketIO** — WebSocket support (cần thêm thư viện)
- **Flask-CORS** — Cross-Origin Resource Sharing

### 2.4 Ưu Điểm của Flask
| # | Ưu điểm | Mô tả |
|---|---------|-------|
| 1 | **Dễ học** | Cú pháp đơn giản, tài liệu phong phú |
| 2 | **Linh hoạt** | Tự do chọn thư viện theo nhu cầu |
| 3 | **Cộng đồng lớn** | Nhiều tutorial, StackOverflow Q&A |
| 4 | **Ổn định** | 15 năm phát triển, battle-tested |
| 5 | **Debug dễ** | Werkzeug debugger tích hợp sẵn |

### 2.5 Nhược Điểm của Flask
| # | Nhược điểm | Ý nghĩa với Hệ thống Giám sát |
|---|-----------|-------------------------------|
| 1 | **Hiệu năng thấp hơn** | WSGI sync, khó xử lý nhiều camera đồng thời |
| 2 | **Không có validation tích hợp** | Phải tự validate dữ liệu detection |
| 3 | **WebSocket không native** | Cần Flask-SocketIO (phức tạp hơn) |
| 4 | **Async hạn chế** | Khó xử lý concurrent video streams |
| 5 | **Không tự tạo docs** | Phải cấu hình Swagger thủ công |

---

## 3. So Sánh Chi Tiết

### 3.1 Bảng So Sánh Toàn Diện

| Tiêu Chí | FastAPI | Flask | Kết Quả |
|----------|---------|-------|:-------:|
| **Hiệu năng (I/O)** | ⭐⭐⭐⭐⭐ (ASGI + async) | ⭐⭐⭐ (WSGI sync) | FastAPI |
| **Dễ học** | ⭐⭐⭐⭐ (cần biết async) | ⭐⭐⭐⭐⭐ (rất đơn giản) | Flask |
| **Tài liệu tự động** | ✅ Có sẵn (Swagger/ReDoc) | ❌ Phải cấu hình thêm | FastAPI |
| **Data Validation** | ✅ Pydantic (tích hợp) | ❌ Cần extension (Marshmallow) | FastAPI |
| **Type Safety** | ✅ Type hints bắt buộc | ⚠️ Tùy chọn | FastAPI |
| **Dependency Injection** | ✅ Tích hợp sẵn | ❌ Không có | FastAPI |
| **WebSocket** | ✅ Native (Starlette) | ⚠️ Qua Flask-SocketIO | FastAPI |
| **Async/Await** | ✅ Native, đầy đủ | ⚠️ Hỗ trợ từng phần (Flask 2.0+) | FastAPI |
| **Xử lý video stream** | ✅ Async streaming response | ⚠️ Blocking | FastAPI |
| **Background Tasks** | ✅ Tích hợp sẵn | ❌ Cần Celery | FastAPI |
| **Cộng đồng** | ⭐⭐⭐⭐ (đang tăng mạnh) | ⭐⭐⭐⭐⭐ (lớn, lâu đời) | Flask |
| **Ecosystem** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Flask |
| **Production Ready** | ✅ Netflix, Uber, Microsoft | ✅ Battle-tested 15 năm | Hòa |
| **AI/ML Integration** | ✅ Rất phù hợp (async inference) | ⚠️ Phù hợp | FastAPI |

### 3.2 So Sánh Cấu Trúc Project cho Hệ Thống Giám Sát

**Flask — Cấu trúc điển hình:**
```
traffic-flask/
├── app/
│   ├── __init__.py
│   ├── models/
│   │   ├── camera.py
│   │   └── detection.py
│   ├── routes/
│   │   ├── cameras.py          # Blueprint
│   │   ├── detections.py       # Blueprint
│   │   └── violations.py       # Blueprint
│   ├── services/
│   │   └── yolo_service.py     # YOLO inference
│   └── extensions.py
├── config.py
├── requirements.txt
└── run.py
```

**FastAPI — Cấu trúc điển hình:**
```
traffic-fastapi/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── v1/
│   │       ├── router.py       # APIRouter
│   │       ├── cameras.py
│   │       ├── detections.py
│   │       ├── violations.py
│   │       └── websocket.py    # Real-time dashboard
│   ├── core/
│   │   ├── config.py           # Pydantic BaseSettings
│   │   ├── security.py         # JWT utils
│   │   └── database.py         # Async DB engine
│   ├── models/
│   │   ├── camera.py           # SQLAlchemy models
│   │   ├── detection.py
│   │   └── violation.py
│   ├── schemas/
│   │   ├── camera.py           # Pydantic schemas
│   │   ├── detection.py
│   │   └── violation.py
│   ├── services/
│   │   ├── yolo_service.py     # YOLO inference service
│   │   └── alert_service.py    # Cảnh báo vi phạm
│   └── dependencies/
│       └── auth.py
├── yolo_models/                 # YOLO weights
├── tests/
├── requirements.txt
└── .env
```

---

## 4. Benchmark Hiệu Năng

### 4.1 Kết Quả Benchmark (Requests/giây)

Dựa trên benchmark từ **TechEmpower Framework Benchmarks** và các nguồn độc lập:

```
Framework       | Req/s (JSON)  | Req/s (DB Query) | Latency (ms)
----------------|---------------|------------------|-------------
FastAPI (async) | ~50,000       | ~30,000          | ~2ms
Flask (sync)    | ~15,000       | ~8,000           | ~6ms
Django          | ~12,000       | ~7,000           | ~8ms
Express (JS)    | ~55,000       | ~35,000          | ~1.8ms
```

### 4.2 Khi Nào Hiệu Năng Thực Sự Quan Trọng?

**Với hệ thống giám sát giao thông, FastAPI vượt trội rõ ràng khi:**
- Nhận dữ liệu detection từ **hàng chục camera đồng thời** (I/O-bound)
- **WebSocket connections** cho dashboard real-time (hàng trăm client)
- Gọi YOLO inference service **không đồng bộ** (không block các request khác)
- API trả về **streaming video** từ camera

**Flask đủ tốt khi:**
- Hệ thống chỉ có 1-3 camera
- Không cần dashboard real-time
- Prototype nhanh để demo ý tưởng

---

## 5. Tích Hợp với YOLO và Xử Lý Video

### 5.1 FastAPI — Async YOLO Inference

```python
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import asyncio

# YOLO model được load 1 lần khi startup
yolo_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global yolo_model
    from ultralytics import YOLO
    yolo_model = YOLO("yolo_models/best.pt")  # Model đã train cho giao thông
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/api/v1/detect/")
async def detect_vehicles(file: UploadFile = File(...)):
    """Nhận ảnh/frame từ camera và trả về kết quả detection"""
    contents = await file.read()

    # Chạy inference trong thread pool để không block event loop
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, lambda: yolo_model(contents))

    detections = []
    for r in results:
        for box in r.boxes:
            detections.append({
                "class": r.names[int(box.cls)],
                "confidence": float(box.conf),
                "bbox": box.xyxy[0].tolist()
            })

    return {"camera_id": "cam_001", "detections": detections}
```

### 5.2 FastAPI — Streaming Video từ Camera

```python
import cv2

async def generate_frames(camera_url: str):
    """Generator cho video stream từ camera RTSP"""
    cap = cv2.VideoCapture(camera_url)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Chạy YOLO detection trên mỗi frame
        results = yolo_model(frame)
        annotated = results[0].plot()  # Vẽ bounding boxes

        _, buffer = cv2.imencode('.jpg', annotated)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               buffer.tobytes() + b'\r\n')

    cap.release()

@app.get("/api/v1/cameras/{camera_id}/stream")
async def stream_camera(camera_id: str):
    camera = await get_camera(camera_id)
    return StreamingResponse(
        generate_frames(camera.rtsp_url),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )
```

### 5.3 Flask — Tương đương nhưng Đồng bộ

```python
# Flask không hỗ trợ async native — phức tạp hơn khi stream video
@app.route('/cameras/<camera_id>/stream')
def stream_camera(camera_id):
    camera = Camera.query.get(camera_id)
    return Response(
        generate_frames(camera.rtsp_url),  # Blocking!
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )
# Vấn đề: Mỗi stream chiếm 1 worker thread → khó scale nhiều camera
```

**So sánh:** FastAPI xử lý async nên có thể phục vụ nhiều camera stream cùng lúc mà không cần tăng số worker. Flask blocking nên mỗi stream chiếm 1 thread/worker.

---

## 6. JWT Authentication

### 6.1 Với FastAPI

FastAPI có hỗ trợ OAuth2 và JWT tích hợp rất gọn — phù hợp bảo vệ API giám sát:

```python
# core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# api/v1/auth.py
@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    operator = await authenticate_operator(db, form_data.username, form_data.password)
    if not operator:
        raise HTTPException(status_code=401, detail="Sai thông tin đăng nhập")

    return {
        "access_token": create_access_token({"sub": str(operator.id), "role": operator.role}),
        "token_type": "bearer"
    }
```

### 6.2 Với Flask

```python
from flask_jwt_extended import JWTManager, create_access_token, jwt_required

jwt = JWTManager(app)

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    operator = Operator.query.filter_by(username=data['username']).first()
    if not operator or not operator.check_password(data['password']):
        return jsonify({"error": "Sai thông tin đăng nhập"}), 401

    return jsonify({"access_token": create_access_token(identity=operator.id)})

@app.route('/cameras', methods=['GET'])
@jwt_required()
def list_cameras():
    ...
```

**So sánh:** FastAPI DI giúp code JWT clean và testable hơn. Flask cần extension nhưng Flask-JWT-Extended cũng hoàn thiện.

---

## 7. WebSocket cho Dashboard Real-time

### 7.1 FastAPI (Native) — Dashboard Giám Sát

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class DashboardManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_detection(self, detection: dict):
        """Gửi kết quả phát hiện đến tất cả dashboard đang mở"""
        for connection in self.active_connections:
            await connection.send_json(detection)

dashboard = DashboardManager()

@app.websocket("/ws/dashboard")
async def dashboard_ws(websocket: WebSocket):
    await dashboard.connect(websocket)
    try:
        while True:
            # Nhận lệnh điều khiển từ operator (zoom, pan, switch camera)
            command = await websocket.receive_json()
            await handle_operator_command(command)
    except WebSocketDisconnect:
        dashboard.disconnect(websocket)

# Khi YOLO phát hiện vi phạm → broadcast ngay đến dashboard
async def on_violation_detected(violation: dict):
    await dashboard.broadcast_detection({
        "type": "violation",
        "camera_id": violation["camera_id"],
        "vehicle_type": violation["vehicle_type"],
        "violation_type": violation["violation_type"],
        "license_plate": violation["license_plate"],
        "confidence": violation["confidence"],
        "timestamp": violation["timestamp"],
        "image_url": violation["image_url"]
    })
```

### 7.2 Flask (Flask-SocketIO)

```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    print("Dashboard client connected")

@socketio.on('request_camera')
def handle_camera_request(data):
    camera_id = data['camera_id']
    emit('camera_feed', get_camera_snapshot(camera_id))
```

**So sánh:** FastAPI WebSocket native, async, và nhẹ hơn. Flask-SocketIO dùng Socket.IO protocol (nặng hơn, nhưng có room/namespace support tốt).

---

## 8. Khuyến Nghị cho Hệ Thống Giám Sát Giao Thông

### 8.1 Phân Tích Yêu Cầu Đặc Thù

**Dự án: Hệ thống Giám sát Giao thông Thông minh sử dụng YOLO**
- Backend nhận **kết quả detection** từ YOLO model (nhiều camera đồng thời)
- Cần **streaming video** với bounding boxes từ camera → dashboard
- **WebSocket** cho dashboard real-time (hiển thị vi phạm, thống kê lưu lượng)
- **JWT Authentication** cho operator (nhân viên giám sát)
- **Background Tasks** xử lý video, lưu ảnh vi phạm, gửi cảnh báo
- Cần **xử lý đồng thời** nhiều camera mà không block

### 8.2 Lựa Chọn: **FastAPI** ✅

**Lý do chọn FastAPI cho Hệ thống Giám sát Giao thông:**

1. **Async/Await native** → Xử lý đồng thời dữ liệu từ nhiều camera mà không block
2. **WebSocket native** → Dashboard giám sát real-time, hiển thị vi phạm tức thì
3. **Streaming Response** → Stream video đã annotate (có bounding boxes) từ camera
4. **Background Tasks** → Xử lý YOLO inference, lưu ảnh vi phạm không đồng bộ
5. **Pydantic Validation** → Validate dữ liệu detection (bbox, confidence, vehicle_type)
6. **Swagger UI tự động** → Demo hệ thống dễ dàng khi bảo vệ đồ án
7. **DI tích hợp** → Quản lý YOLO model instance, DB connection sạch sẽ
8. **AI/ML friendly** → FastAPI là framework phổ biến nhất cho serving ML models

### 8.3 Khi Nào Chọn Flask?

- Hệ thống chỉ có 1-2 camera, không cần real-time
- Team đã quen Flask và không có thời gian học FastAPI
- Chỉ cần REST API đơn giản, không cần WebSocket hay streaming

---

## 9. Kết Luận

```
┌──────────────────────────────────────────────────────────────────┐
│  🏆 KHUYẾN NGHỊ: FastAPI cho Hệ thống Giám sát Giao thông      │
├──────────────────────────────────────────────────────────────────┤
│  ✅ Async xử lý đồng thời nhiều camera giao thông               │
│  ✅ WebSocket native cho dashboard giám sát real-time            │
│  ✅ Streaming Response cho video annotated từ YOLO               │
│  ✅ Background Tasks cho YOLO inference và gửi cảnh báo          │
│  ✅ Pydantic validation cho dữ liệu detection chính xác         │
│  ✅ Auto Swagger UI — demo hệ thống khi bảo vệ đồ án            │
│  ✅ Framework #1 cho AI/ML model serving (Netflix, Uber dùng)    │
└──────────────────────────────────────────────────────────────────┘
```

FastAPI là lựa chọn tối ưu cho backend hệ thống giám sát giao thông thông minh. Khả năng xử lý bất đồng bộ, WebSocket native, và streaming response đáp ứng hoàn hảo nhu cầu xử lý video real-time từ nhiều camera, chạy YOLO inference, và cung cấp dashboard giám sát cho nhân viên vận hành.

---

*Báo cáo nghiên cứu Backend Framework | Hệ thống Giám sát Giao thông Thông minh | 07/06/2026*
