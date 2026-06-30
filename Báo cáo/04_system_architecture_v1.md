
---

## MỤC LỤC



---

## 1. Tổng Quan Kiến Trúc Hệ Thống

### 1.1 Mục Tiêu Kiến Trúc

Kiến trúc hệ thống cần đáp ứng **5 yêu cầu trọng tâm**:

| # | Yêu Cầu | Mô Tả | Chỉ Tiêu |
|---|---------|-------|-----------|
| 1 | **Real-time Processing** | Xử lý video từ camera và trả kết quả nhận diện trong thời gian thực | Latency < 500ms end-to-end |
| 2 | **Scalability** | Hỗ trợ mở rộng từ 5 → 50 camera mà không cần thay đổi kiến trúc | Horizontal scaling |
| 3 | **High Throughput** | Ghi nhận hàng triệu detection/ngày vào database | > 1000 writes/s |
| 4 | **Fault Tolerance** | Camera ngắt kết nối → hệ thống tự reconnect; Module lỗi → không ảnh hưởng toàn cục | Auto-recovery |
| 5 | **Security** | Chỉ operator đã xác thực mới truy cập dashboard và API | JWT + RBAC |

### 1.2 Kiến Trúc Phân Tầng (Layered Architecture)

Hệ thống được tổ chức theo **4 tầng chính**, mỗi tầng có trách nhiệm rõ ràng:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        TẦNG 1: DATA SOURCE (Nguồn Dữ Liệu)             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐         ┌──────────┐        │
│   │Camera IP │  │Camera IP │  │Camera IP │  . . .  │Camera IP │        │
│   │ (RTSP)   │  │ (RTSP)   │  │ (RTSP)   │         │ (RTSP)   │        │
│   │ cam_001  │  │ cam_002  │  │ cam_003  │         │ cam_N    │        │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘         └────┬─────┘        │
│        │              │              │                    │              │
└────────┼──────────────┼──────────────┼────────────────────┼──────────────┘
         │ RTSP         │ RTSP         │ RTSP              │ RTSP
         ▼              ▼              ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                   TẦNG 2: PROCESSING (Xử Lý AI + Logic)                 │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                    FastAPI Backend Server                        │   │
│   │  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │   │
│   │  │ Camera Stream  │  │  YOLO AI       │  │  Rules Engine    │   │   │
│   │  │ Manager        │  │  Inference     │  │  (Vi phạm)       │   │   │
│   │  │ (OpenCV)       │  │  Service       │  │                  │   │   │
│   │  └───────┬────────┘  └───────┬────────┘  └───────┬──────────┘   │   │
│   │          │                   │                    │              │   │
│   │  ┌───────▼───────────────────▼────────────────────▼──────────┐   │   │
│   │  │              Message Queue / Event Bus                    │   │   │
│   │  │         (asyncio.Queue / Redis Pub-Sub)                   │   │   │
│   │  └───────┬───────────────────┬────────────────────┬──────────┘   │   │
│   │          │                   │                    │              │   │
│   │  ┌───────▼────────┐  ┌──────▼─────────┐  ┌───────▼──────────┐   │   │
│   │  │  REST API      │  │  WebSocket     │  │  Background      │   │   │
│   │  │  Controller    │  │  Server        │  │  Task Runner     │   │   │
│   │  └───────┬────────┘  └──────┬─────────┘  └───────┬──────────┘   │   │
│   │          │                  │                     │              │   │
│   └──────────┼──────────────────┼─────────────────────┼──────────────┘   │
│              │                  │                     │                   │
└──────────────┼──────────────────┼─────────────────────┼──────────────────┘
               │                  │                     │
               ▼                  ▼                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     TẦNG 3: DATA STORAGE (Lưu Trữ)                      │
│                                                                          │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│   │   PostgreSQL     │  │   Redis Cache    │  │   File Storage       │  │
│   │   (Primary DB)   │  │   (Session,      │  │   (Evidence Images,  │  │
│   │   - Detections   │  │    Realtime      │  │    Video Snapshots)  │  │
│   │   - Violations   │  │    Stats Cache)  │  │                      │  │
│   │   - Cameras      │  │                  │  │                      │  │
│   │   - Operators    │  │                  │  │                      │  │
│   │   - Stats        │  │                  │  │                      │  │
│   └──────────────────┘  └──────────────────┘  └──────────────────────┘  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
               │                  │                     │
               ▼                  ▼                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    TẦNG 4: PRESENTATION (Hiển Thị)                       │
│                                                                          │
│   ┌──────────────────────────────────────────────────────────────────┐   │
│   │                    Dashboard Web Application                     │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐     │   │
│   │  │ Live Map │  │ Camera   │  │ Violation│  │ Statistics   │     │   │
│   │  │ (Cameras)│  │ Feed     │  │ Alerts   │  │ Charts       │     │   │
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────────┘     │   │
│   └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Sơ Đồ Kiến Trúc Tổng Thể

### 2.1 High-Level System Architecture

```
                    ┌──────────────────────────────────────────────────────┐
                    │              EXTERNAL LAYER                          │
                    │                                                      │
                    │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │
                    │  │ Camera 1 │ │ Camera 2 │ │ Camera N │             │
                    │  │ (RTSP)   │ │ (RTSP)   │ │ (RTSP)   │             │
                    │  └────┬─────┘ └────┬─────┘ └────┬─────┘             │
                    └───────┼────────────┼────────────┼────────────────────┘
                            │            │            │
                            ▼            ▼            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                          BACKEND CORE                                     │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                 INGESTION LAYER (Thu Nhận)                          │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐  │  │
│  │  │  Stream Manager  │  │  Frame Buffer  │  │  Health Monitor    │  │  │
│  │  │  (RTSP Connect)  │  │  (Queue)       │  │  (Camera Status)   │  │  │
│  │  └────────┬─────────┘  └───────┬────────┘  └────────────────────┘  │  │
│  └───────────┼────────────────────┼───────────────────────────────────┘  │
│              │                    │                                       │
│  ┌───────────▼────────────────────▼───────────────────────────────────┐  │
│  │                 AI INFERENCE LAYER (Nhận Diện)                      │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐  │  │
│  │  │  YOLO Service    │  │  Object        │  │  Post-Processing   │  │  │
│  │  │  (Model Manager) │  │  Tracker       │  │  (NMS, Filtering)  │  │  │
│  │  │                  │  │  (ByteTrack)   │  │                    │  │  │
│  │  └────────┬─────────┘  └───────┬────────┘  └────────┬───────────┘  │  │
│  └───────────┼────────────────────┼─────────────────────┼─────────────┘  │
│              │                    │                      │                │
│  ┌───────────▼────────────────────▼─────────────────────▼─────────────┐  │
│  │                 BUSINESS LOGIC LAYER (Xử Lý Nghiệp Vụ)            │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐  │  │
│  │  │  Violation       │  │  Traffic Flow  │  │  Evidence          │  │  │
│  │  │  Detector        │  │  Analyzer      │  │  Collector         │  │  │
│  │  │  (Rules Engine)  │  │  (Statistics)  │  │  (Screenshot)      │  │  │
│  │  └────────┬─────────┘  └───────┬────────┘  └────────┬───────────┘  │  │
│  └───────────┼────────────────────┼─────────────────────┼─────────────┘  │
│              │                    │                      │                │
│  ┌───────────▼────────────────────▼─────────────────────▼─────────────┐  │
│  │                 API & COMMUNICATION LAYER (Giao Tiếp)              │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐  │  │
│  │  │  REST API        │  │  WebSocket     │  │  Auth & Security   │  │  │
│  │  │  (CRUD, Query)   │  │  (Real-time)   │  │  (JWT, RBAC)       │  │  │
│  │  └────────┬─────────┘  └───────┬────────┘  └────────────────────┘  │  │
│  └───────────┼────────────────────┼───────────────────────────────────┘  │
│              │                    │                                       │
│  ┌───────────▼────────────────────▼───────────────────────────────────┐  │
│  │                 DATA ACCESS LAYER (Truy Cập Dữ Liệu)              │  │
│  │  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────┐  │  │
│  │  │  SQLAlchemy ORM  │  │  Redis Client  │  │  File I/O          │  │  │
│  │  │  (asyncpg)       │  │  (aioredis)    │  │  (aiofiles)        │  │  │
│  │  └────────┬─────────┘  └───────┬────────┘  └────────┬───────────┘  │  │
│  └───────────┼────────────────────┼─────────────────────┼─────────────┘  │
│              │                    │                      │                │
└──────────────┼────────────────────┼──────────────────────┼────────────────┘
               │                    │                      │
               ▼                    ▼                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                      DATA INFRASTRUCTURE                                 │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │   PostgreSQL 16  │  │   Redis 7      │  │   Local / S3 Storage   │   │
│  │   (Primary DB)   │  │   (Cache +     │  │   (Evidence images,    │   │
│  │                  │  │    Pub/Sub)    │  │    video snapshots)    │   │
│  └──────────────────┘  └────────────────┘  └────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Deployment Architecture (Docker Compose)

```
┌────────────────────── Docker Network (traffic-net) ──────────────────────┐
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │  nginx:latest    │  │  backend:custom  │  │  postgres:16-alpine  │   │
│  │  ──────────────  │  │  ──────────────  │  │  ──────────────────  │   │
│  │  Reverse Proxy   │  │  FastAPI App     │  │  PostgreSQL DB       │   │
│  │  SSL Termination │──│  + YOLO Model    │──│  + PostGIS           │   │
│  │  Port: 443/80    │  │  + Uvicorn       │  │  Port: 5432          │   │
│  │                  │  │  Port: 8000      │  │  Volume: pg_data     │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
│                                │                                         │
│                        ┌───────┴───────┐                                 │
│                        │               │                                 │
│  ┌─────────────────────▼──┐  ┌─────────▼────────────┐                   │
│  │  redis:7-alpine        │  │  evidence-storage     │                   │
│  │  ──────────────────    │  │  ──────────────────   │                   │
│  │  Cache + Pub/Sub       │  │  Volume: ./evidence/  │                   │
│  │  Port: 6379            │  │  (Ảnh bằng chứng)     │                   │
│  └────────────────────────┘  └──────────────────────┘                   │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Xác Định Các Module Backend

### 3.1 Tổng Quan Module

Backend được chia thành **8 module chính**, mỗi module chịu trách nhiệm riêng biệt và giao tiếp thông qua interface rõ ràng:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       BACKEND MODULES MAP                           │
│                                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ M1: Camera  │  │ M2: AI       │  │ M3: Rules    │               │
│  │ Ingestion   │──│ Inference    │──│ Engine       │               │
│  │ Module      │  │ Module       │  │ Module       │               │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘               │
│         │                │                  │                       │
│         ▼                ▼                  ▼                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ M4: Data    │  │ M5: Realtime │  │ M6: Auth     │               │
│  │ Persistence │  │ Communication│  │ & Security   │               │
│  │ Module      │  │ Module       │  │ Module       │               │
│  └──────┬──────┘  └──────┬───────┘  └──────────────┘               │
│         │                │                                          │
│         ▼                ▼                                          │
│  ┌─────────────┐  ┌──────────────┐                                  │
│  │ M7: API     │  │ M8: Task     │                                  │
│  │ Gateway     │  │ Scheduler    │                                  │
│  │ Module      │  │ Module       │                                  │
│  └─────────────┘  └──────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Chi Tiết 8 Module Backend

#### MODULE 1: Camera Ingestion Module — Thu Nhận Luồng Video

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Kết nối RTSP streams, giải mã frame, quản lý vòng đời camera |
| **Thành phần chính** | `StreamManager`, `FrameBuffer`, `CameraHealthChecker` |
| **Công nghệ** | OpenCV (`cv2.VideoCapture`), asyncio |
| **Input** | RTSP URL từ bảng `cameras` |
| **Output** | Numpy frames đưa vào Frame Buffer queue |

```
Camera Ingestion Module — Internal Structure
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌──────────────┐    ┌───────────────┐    ┌───────────┐  │
│  │ StreamManager│───►│ Frame Decoder │───►│ Frame     │  │
│  │ (RTSP Pool)  │    │ (OpenCV)      │    │ Buffer    │  │
│  │              │    │               │    │ (Queue)   │  │
│  └──────┬───────┘    └───────────────┘    └─────┬─────┘  │
│         │                                       │        │
│  ┌──────▼───────┐                               │        │
│  │ Health Check │  Reconnect on failure         │        │
│  │ (Heartbeat)  │◄──────────────────────────────┘        │
│  └──────────────┘                                        │
│                                                          │
│  Configs:                                                │
│  - frame_skip: 5 (xử lý 1/5 frame)                      │
│  - reconnect_interval: 5s                                │
│  - max_buffer_size: 30 frames                            │
│  - resolution: 640x480 (downscale từ camera)             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 2: AI Inference Module — Nhận Diện Phương Tiện

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Chạy YOLO inference, Object Tracking, Post-processing |
| **Thành phần chính** | `YOLOService`, `ObjectTracker`, `DetectionParser` |
| **Công nghệ** | Ultralytics YOLO, ByteTrack, `asyncio.to_thread()` |
| **Input** | Numpy frame từ Frame Buffer |
| **Output** | List[DetectionResult] — `{vehicle_type, confidence, bbox, track_id}` |

```
AI Inference Module — Pipeline
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Frame (numpy)                                           │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────────┐   Chạy trong ThreadPool                │
│  │ YOLO Model   │   (asyncio.to_thread)                  │
│  │ (best.pt)    │   → Không block event loop             │
│  └──────┬───────┘                                        │
│         │ Raw Detections                                 │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │ NMS Filter   │   Non-Maximum Suppression              │
│  │ (conf > 0.5) │   Loại bỏ bounding box trùng lặp      │
│  └──────┬───────┘                                        │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │ Object       │   Gán track_id cho mỗi xe              │
│  │ Tracker      │   Theo dõi xe qua nhiều frame          │
│  │ (ByteTrack)  │   → Cần thiết cho đo tốc độ           │
│  └──────┬───────┘                                        │
│         │                                                │
│         ▼                                                │
│  ┌──────────────┐                                        │
│  │ Detection    │   Parse → DetectionResult object       │
│  │ Parser       │   {vehicle_type, bbox, conf, track_id} │
│  └──────┬───────┘                                        │
│         │                                                │
│         ▼                                                │
│  Output: List[DetectionResult]                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 3: Rules Engine Module — Phát Hiện Vi Phạm

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Kiểm tra vi phạm giao thông dựa trên detection results |
| **Thành phần chính** | `ViolationChecker`, `ZoneManager`, `SpeedEstimator` |
| **Công nghệ** | Shapely (polygon), numpy (tính toán) |
| **Input** | DetectionResult + Camera Config (zones, rules) |
| **Output** | List[ViolationEvent] hoặc rỗng nếu không vi phạm |

```
Rules Engine — Violation Detection Flow
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  DetectionResult + Camera Config                         │
│       │                                                  │
│       ├──── Rule 1: Vượt đèn đỏ ────────────────────┐   │
│       │     - Kiểm tra xe ở vùng "stop zone"         │   │
│       │     - Trạng thái đèn = RED                   │   │
│       │     - Xe vẫn di chuyển qua vạch dừng         │   │
│       │                                              │   │
│       ├──── Rule 2: Đi sai làn đường ───────────────┐│   │
│       │     - Kiểm tra centroid xe nằm ngoài         ││   │
│       │       polygon "allowed_lane"                 ││   │
│       │                                              ││   │
│       ├──── Rule 3: Chạy quá tốc độ ───────────────┐││   │
│       │     - Dùng track_id theo dõi xe qua N frame  │││   │
│       │     - Tính pixel displacement → km/h         │││   │
│       │     - So sánh với speed_limit của camera      │││   │
│       │                                              │││   │
│       ├──── Rule 4: Không đội mũ bảo hiểm ─────────┐│││   │
│       │     - vehicle_type == "motorcycle"           ││││   │
│       │     - Sub-model detect helmet/no-helmet      ││││   │
│       │                                              ││││   │
│       ▼                                              ▼▼▼▼  │
│  ┌──────────────┐                                        │
│  │ Violation    │   Tổng hợp kết quả từ tất cả rules     │
│  │ Aggregator   │   → ViolationEvent (nếu có vi phạm)    │
│  └──────────────┘                                        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 4: Data Persistence Module — Quản Lý Dữ Liệu

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | CRUD operations, batch insert, query optimization |
| **Thành phần chính** | `DetectionRepository`, `ViolationRepository`, `StatsAggregator` |
| **Công nghệ** | SQLAlchemy 2.0 Async, asyncpg, Alembic (migrations) |
| **Input** | DetectionResult, ViolationEvent |
| **Output** | Persistent storage trong PostgreSQL |

```
Data Persistence Module
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌──────────────────┐                                    │
│  │ Detection Repo   │  Batch INSERT (mỗi 1-2 giây)      │
│  │                  │  → detections table                │
│  └──────────────────┘                                    │
│                                                          │
│  ┌──────────────────┐                                    │
│  │ Violation Repo   │  INSERT + Lưu evidence image URL   │
│  │                  │  → violations table                │
│  └──────────────────┘                                    │
│                                                          │
│  ┌──────────────────┐                                    │
│  │ Stats Aggregator │  Cron mỗi 5 phút:                 │
│  │                  │  Tổng hợp COUNT(*) GROUP BY hour   │
│  │                  │  → traffic_stats table             │
│  └──────────────────┘                                    │
│                                                          │
│  ┌──────────────────┐                                    │
│  │ Evidence Storage │  Lưu ảnh vi phạm vào disk/S3      │
│  │                  │  → /evidence/{date}/{camera_id}/   │
│  └──────────────────┘                                    │
│                                                          │
│  Performance Optimizations:                              │
│  - Batch INSERT (collect 50-100 records → 1 query)       │
│  - Connection Pool: 20 connections, 30 overflow          │
│  - Partial indexes trên status='active'                  │
│  - JSONB GIN indexes cho metadata queries                │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 5: Realtime Communication Module — Truyền Tin Tức Thì

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Quản lý WebSocket connections, broadcast events |
| **Thành phần chính** | `DashboardManager`, `EventBroadcaster`, `ChannelRouter` |
| **Công nghệ** | FastAPI WebSocket, Redis Pub/Sub (optional scaling) |
| **Input** | DetectionEvent, ViolationAlert, StatsUpdate |
| **Output** | JSON messages đẩy đến Dashboard clients |

```
Realtime Communication — WebSocket Architecture
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              DashboardManager                        │ │
│  │                                                     │ │
│  │  Channel "all"     ──►  [WS1, WS2, WS3, ...]       │ │
│  │  Channel "cam_001" ──►  [WS1]                       │ │
│  │  Channel "cam_002" ──►  [WS2, WS3]                  │ │
│  │  Channel "violations" ─► [WS1, WS2, WS3]           │ │
│  │                                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  Event Types:                                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ "detection"      → Phương tiện mới nhận diện     │    │
│  │ "violation_alert" → Cảnh báo vi phạm (priority)  │    │
│  │ "camera_status"  → Camera online/offline          │    │
│  │ "stats_update"   → Cập nhật biểu đồ thống kê     │    │
│  │ "system_alert"   → Cảnh báo hệ thống (disk, CPU) │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 6: Auth & Security Module — Xác Thực Bảo Mật

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | JWT token management, role-based access control, password hashing |
| **Thành phần chính** | `JWTManager`, `PasswordHasher`, `RBACMiddleware` |
| **Công nghệ** | python-jose (JWT), passlib/bcrypt, OAuth2PasswordBearer |
| **Roles** | `admin` (full access), `operator` (view + confirm violations) |

---

#### MODULE 7: API Gateway Module — Điều Phối API

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Route management, request validation, response serialization |
| **Thành phần chính** | `CameraRouter`, `DetectionRouter`, `ViolationRouter`, `StatsRouter`, `AuthRouter` |
| **Công nghệ** | FastAPI APIRouter, Pydantic v2 schemas |
| **API Versioning** | `/api/v1/` prefix |


API Endpoints Map
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  /api/v1/auth/                                           │
│    ├── POST /login          → Đăng nhập operator         │
│    ├── POST /logout         → Đăng xuất                  │
│    └── POST /refresh        → Làm mới Access Token       │
│                                                          │
│  /api/v1/cameras/                                        │
│    ├── GET    /             → Danh sách camera            │
│    ├── POST   /             → Thêm camera mới (admin)    │
│    ├── GET    /{id}         → Chi tiết 1 camera           │
│    ├── PUT    /{id}         → Cập nhật camera (admin)     │
│    ├── DELETE /{id}         → Xóa camera (admin)          │
│    └── GET    /{id}/stream  → Video stream (MJPEG)        │
│                                                          │
│  /api/v1/detections/                                     │
│    ├── GET    /             → Lịch sử detection (filter)  │
│    ├── POST   /detect       → Upload ảnh → YOLO detect   │
│    └── GET    /stats        → Thống kê detection          │
│                                                          │
│  /api/v1/violations/                                     │
│    ├── GET    /             → Danh sách vi phạm           │
│    ├── GET    /{id}         → Chi tiết vi phạm            │
│    ├── PUT    /{id}/confirm → Phê duyệt vi phạm          │
│    └── GET    /search       → Tìm kiếm theo biển số      │
│                                                          │
│  /api/v1/stats/                                          │
│    ├── GET    /traffic      → Lưu lượng theo giờ          │
│    ├── GET    /violations   → Thống kê vi phạm            │
│    └── GET    /dashboard    → Tổng hợp cho dashboard      │
│                                                          │
│  /ws/dashboard              → WebSocket real-time         │
│  /ws/camera/{id}/stream     → WebSocket stream 1 camera   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

#### MODULE 8: Task Scheduler Module — Tác Vụ Nền

| Thuộc Tính | Giá Trị |
|-----------|---------|
| **Trách nhiệm** | Chạy cron jobs, cleanup, aggregation |
| **Thành phần chính** | `StatsRollupJob`, `EvidenceCleanupJob`, `CameraHealthJob` |
| **Công nghệ** | FastAPI Background Tasks, APScheduler |

```
Scheduled Tasks
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Mỗi 5 phút:   Stats Rollup                        │  │
│  │                Tổng hợp detections → traffic_stats │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Mỗi 30 giây:  Camera Health Check                 │  │
│  │                Ping RTSP → cập nhật status         │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Mỗi ngày:     Evidence Cleanup                     │  │
│  │                Xóa ảnh bằng chứng > 90 ngày        │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │ Mỗi ngày:     Detection Archival                  │  │
│  │                Di chuyển detection cũ → archive     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 4. Thiết Kế Luồng Dữ Liệu

### 4.1 Luồng Chính: Camera → AI → Database → Dashboard

Đây là luồng dữ liệu **end-to-end** quan trọng nhất của hệ thống, mô tả hành trình của dữ liệu từ khi camera ghi nhận hình ảnh giao thông cho đến khi operator nhìn thấy kết quả trên dashboard.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    LUỒNG DỮ LIỆU CHÍNH (Main Data Pipeline)                     │
│                                                                                 │
│  PHASE 1                PHASE 2              PHASE 3              PHASE 4       │
│  ─────────              ─────────            ─────────            ─────────      │
│  THU NHẬN               NHẬN DIỆN            LƯU TRỮ             HIỂN THỊ       │
│  (Ingestion)            (AI Inference)       (Persistence)       (Presentation) │
│                                                                                 │
│  ┌─────────┐  RTSP   ┌──────────┐  Frame  ┌──────────┐  Result ┌──────────┐    │
│  │ Camera  │────────►│  Stream  │────────►│  YOLO    │────────►│  Rules   │    │
│  │ IP      │  Stream │  Manager │  Buffer │  Service │  Parse  │  Engine  │    │
│  │ (RTSP)  │         │ (OpenCV) │  Queue  │ (detect) │         │ (check)  │    │
│  └─────────┘         └──────────┘         └──────────┘         └─────┬────┘    │
│                                                                       │         │
│                                                          ┌────────────┤         │
│                                                          │            │         │
│                                                          ▼            ▼         │
│                                                   ┌──────────┐ ┌──────────┐    │
│                                                   │PostgreSQL│ │ Evidence │    │
│                                                   │          │ │ Storage  │    │
│                                                   │detections│ │ (images) │    │
│                                                   │violations│ │          │    │
│                                                   └────┬─────┘ └──────────┘    │
│                                                        │                        │
│                                              ┌─────────┤                        │
│                                              │         │                        │
│                                              ▼         ▼                        │
│                                        ┌──────────┐ ┌──────────┐               │
│                                        │WebSocket │ │ REST API │               │
│                                        │ Push     │ │ Query    │               │
│                                        └────┬─────┘ └────┬─────┘               │
│                                             │            │                      │
│                                             ▼            ▼                      │
│                                        ┌───────────────────────┐               │
│                                        │   DASHBOARD (Browser) │               │
│                                        │   ┌─────┐ ┌────────┐ │               │
│                                        │   │Alert│ │ Charts │ │               │
│                                        │   │     │ │        │ │               │
│                                        │   └─────┘ └────────┘ │               │
│                                        └───────────────────────┘               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Sequence Diagram — Chi Tiết Từng Bước

```
  Camera       StreamMgr     FrameBuffer    YOLOService    RulesEngine    Database    WebSocket    Dashboard
    │              │              │              │              │            │            │            │
    │──RTSP───────►│              │              │              │            │            │            │
    │              │              │              │              │            │            │            │
    │         ┌────┴────┐        │              │              │            │            │            │
    │         │ OpenCV  │        │              │              │            │            │            │
    │         │ decode  │        │              │              │            │            │            │
    │         │ frame   │        │              │              │            │            │            │
    │         └────┬────┘        │              │              │            │            │            │
    │              │              │              │              │            │            │            │
    │              │──put(frame)─►│              │              │            │            │            │
    │              │              │              │              │            │            │            │
    │              │              │──get()──────►│              │            │            │            │
    │              │              │              │              │            │            │            │
    │              │              │         ┌────┴────┐        │            │            │            │
    │              │              │         │  YOLO   │        │            │            │            │
    │              │              │         │ predict │        │            │            │            │
    │              │              │         │ (GPU)   │        │            │            │            │
    │              │              │         └────┬────┘        │            │            │            │
    │              │              │              │              │            │            │            │
    │              │              │              │──detections─►│            │            │            │
    │              │              │              │              │            │            │            │
    │              │              │              │         ┌────┴────┐      │            │            │
    │              │              │              │         │ Check   │      │            │            │
    │              │              │              │         │ rules   │      │            │            │
    │              │              │              │         │ (zones) │      │            │            │
    │              │              │              │         └────┬────┘      │            │            │
    │              │              │              │              │            │            │            │
    │              │              │              │              │──INSERT───►│            │            │
    │              │              │              │              │ detection  │            │            │
    │              │              │              │              │            │            │            │
    │              │              │              │              │──INSERT───►│            │            │
    │              │              │              │              │ violation  │ (nếu có)   │            │
    │              │              │              │              │            │            │            │
    │              │              │              │              │────────────┼──broadcast►│            │
    │              │              │              │              │            │   event    │            │
    │              │              │              │              │            │            │──JSON─────►│
    │              │              │              │              │            │            │  alert     │
    │              │              │              │              │            │            │            │
```

### 4.3 Data Flow Timing — Ước Tính Latency

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     END-TO-END LATENCY BREAKDOWN                              │
│                                                                              │
│  Phase               │ Thao Tác                      │ Thời Gian Ước Tính   │
│  ────────────────────┼────────────────────────────────┼──────────────────── │
│  1. Frame Capture    │ OpenCV decode RTSP frame       │ ~10-30ms             │
│  2. Queue Transfer   │ asyncio.Queue put/get          │ ~1ms                 │
│  3. YOLO Inference   │ Model predict (GPU)            │ ~15-30ms (GPU)       │
│                      │                                │ ~100-200ms (CPU)     │
│  4. Post-Processing  │ NMS + Tracking + Parse         │ ~5-10ms              │
│  5. Rules Check      │ Zone check + Speed estimation  │ ~2-5ms               │
│  6. DB Insert        │ Batch INSERT (asyncpg)         │ ~5-15ms              │
│  7. WS Broadcast     │ WebSocket send_json            │ ~1-3ms               │
│  8. Client Render    │ Browser render update          │ ~10-50ms             │
│  ────────────────────┼────────────────────────────────┼──────────────────── │
│  TOTAL (GPU)         │                                │ ~50-150ms  ✅        │
│  TOTAL (CPU)         │                                │ ~150-350ms ⚠️       │
│                                                                              │
│  Target: < 500ms end-to-end ✅                                               │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 4.4 Luồng Phụ: Dashboard Query Flow (REST API)

```
  Dashboard           API Gateway         Auth Module         Database          Cache
    │                     │                    │                  │                │
    │──GET /api/v1/stats─►│                    │                  │                │
    │  + JWT Bearer Token │                    │                  │                │
    │                     │──validate token───►│                  │                │
    │                     │◄──operator info────│                  │                │
    │                     │                    │                  │                │
    │                     │──check cache──────────────────────────────────────────►│
    │                     │◄──cache hit? ─────────────────────────────────────────│
    │                     │                    │                  │                │
    │                     │ (Cache Miss)       │                  │                │
    │                     │──SELECT query──────────────────────►  │                │
    │                     │◄──result set ──────────────────────── │                │
    │                     │                    │                  │                │
    │                     │──set cache (TTL=60s)──────────────────────────────────►│
    │                     │                    │                  │                │
    │◄──JSON response─────│                    │                  │                │
    │                     │                    │                  │                │
```

---

## 5. Backend Module Diagram

### 5.1 Module Dependency Graph

```
┌──────────────────────────────────────────────────────────────────────┐
│                  MODULE DEPENDENCY GRAPH                              │
│                                                                      │
│                    ┌──────────────┐                                   │
│                    │  M7: API     │ ◄── Entry point cho mọi request  │
│                    │  Gateway     │                                   │
│                    └──────┬───────┘                                   │
│                           │ depends on                               │
│              ┌────────────┼────────────┐                              │
│              │            │            │                              │
│              ▼            ▼            ▼                              │
│      ┌───────────┐ ┌───────────┐ ┌───────────┐                      │
│      │ M6: Auth  │ │ M5: WS    │ │ M4: Data  │                      │
│      │ Security  │ │ Realtime  │ │ Persist.  │                      │
│      └───────────┘ └─────┬─────┘ └─────┬─────┘                      │
│                          │             │                             │
│                          │    ┌────────┘                             │
│                          │    │                                      │
│                          ▼    ▼                                      │
│                    ┌───────────────┐                                  │
│                    │  M3: Rules    │                                  │
│                    │  Engine       │                                  │
│                    └──────┬───────┘                                   │
│                           │                                          │
│                           ▼                                          │
│                    ┌───────────────┐                                  │
│                    │  M2: AI       │                                  │
│                    │  Inference    │                                  │
│                    └──────┬───────┘                                   │
│                           │                                          │
│                           ▼                                          │
│                    ┌───────────────┐                                  │
│                    │  M1: Camera   │                                  │
│                    │  Ingestion    │                                  │
│                    └───────────────┘                                  │
│                                                                      │
│         ┌───────────────┐                                            │
│         │  M8: Task     │ ─── runs independently (cron-based)        │
│         │  Scheduler    │ ─── depends on M4 (Data Persistence)       │
│         └───────────────┘                                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Module ↔ File Mapping

```
traffic-monitoring/
├── 📁 app/
│   ├── 📄 main.py                          # App entry point, lifespan
│   │
│   ├── 📁 api/v1/                          # ═══ M7: API Gateway ═══
│   │   ├── 📄 router.py                    #   Gom tất cả routes
│   │   ├── 📄 auth.py                      #   /auth endpoints
│   │   ├── 📄 cameras.py                   #   /cameras endpoints
│   │   ├── 📄 detections.py                #   /detections endpoints
│   │   ├── 📄 violations.py                #   /violations endpoints
│   │   ├── 📄 stats.py                     #   /stats endpoints
│   │   └── 📄 websocket.py                 #   /ws endpoints
│   │
│   ├── 📁 core/                            # ═══ M6: Auth & Security ═══
│   │   ├── 📄 config.py                    #   Pydantic Settings (.env)
│   │   ├── 📄 database.py                  #   Async engine + session
│   │   └── 📄 security.py                  #   JWT + bcrypt
│   │
│   ├── 📁 models/                          # ═══ M4: Data Persistence (ORM) ═══
│   │   ├── 📄 __init__.py
│   │   ├── 📄 operator.py                  #   Operator table
│   │   ├── 📄 camera.py                    #   Camera table
│   │   ├── 📄 detection.py                 #   Detection table
│   │   ├── 📄 violation.py                 #   Violation table
│   │   └── 📄 traffic_stat.py              #   TrafficStat table
│   │
│   ├── 📁 schemas/                         # ═══ M7: API Gateway (Validation) ═══
│   │   ├── 📄 auth.py                      #   Login/Token schemas
│   │   ├── 📄 camera.py                    #   Camera CRUD schemas
│   │   ├── 📄 detection.py                 #   Detection schemas
│   │   ├── 📄 violation.py                 #   Violation schemas
│   │   └── 📄 stats.py                     #   Stats response schemas
│   │
│   ├── 📁 services/                        # ═══ M1, M2, M3 (Core Logic) ═══
│   │   ├── 📄 camera_manager.py            #   M1: Stream management
│   │   ├── 📄 frame_buffer.py              #   M1: Frame queue
│   │   ├── 📄 yolo_service.py              #   M2: YOLO inference
│   │   ├── 📄 object_tracker.py            #   M2: ByteTrack tracking
│   │   ├── 📄 violation_checker.py         #   M3: Rules evaluation
│   │   ├── 📄 zone_manager.py              #   M3: Polygon zone management
│   │   └── 📄 speed_estimator.py           #   M3: Speed calculation
│   │
│   ├── 📁 repositories/                    # ═══ M4: Data Persistence (Queries) ═══
│   │   ├── 📄 detection_repo.py            #   Detection CRUD + batch
│   │   ├── 📄 violation_repo.py            #   Violation CRUD + search
│   │   ├── 📄 camera_repo.py               #   Camera CRUD
│   │   └── 📄 stats_repo.py               #   Stats aggregation queries
│   │
│   ├── 📁 websocket/                       # ═══ M5: Realtime Communication ═══
│   │   ├── 📄 manager.py                   #   DashboardManager
│   │   └── 📄 events.py                    #   Event type definitions
│   │
│   ├── 📁 tasks/                           # ═══ M8: Task Scheduler ═══
│   │   ├── 📄 stats_rollup.py              #   5-min stats aggregation
│   │   ├── 📄 camera_health.py             #   Camera health check
│   │   └── 📄 cleanup.py                   #   Evidence + detection cleanup
│   │
│   └── 📁 dependencies/                    # ═══ Shared Dependencies ═══
│       ├── 📄 auth.py                      #   get_current_operator()
│       └── 📄 database.py                  #   get_db()
│
├── 📁 yolo_models/                         # YOLO weight files
│   └── 📄 best.pt
│
├── 📁 evidence/                            # Ảnh bằng chứng vi phạm
├── 📁 migrations/                          # Alembic migrations
│   └── 📁 versions/
│
├── 📄 .env                                # Biến môi trường
├── 📄 requirements.txt                    # Python dependencies
├── 📄 Dockerfile                          # Container image
├── 📄 docker-compose.yml                  # Orchestration
└── 📄 alembic.ini                         # Migration config
```

---

## 6. Giao Tiếp Giữa Các Module

### 6.1 Communication Matrix

| Từ Module → | M1 Camera | M2 AI | M3 Rules | M4 Data | M5 WS | M6 Auth | M7 API | M8 Task |
|:-----------:|:---------:|:-----:|:--------:|:-------:|:-----:|:-------:|:------:|:-------:|
| **M1** Camera | — | Frame Queue | — | — | — | — | — | — |
| **M2** AI | — | — | DetectionResult | — | — | — | — | — |
| **M3** Rules | — | — | — | INSERT | Broadcast | — | — | — |
| **M4** Data | — | — | — | — | — | — | Query Result | — |
| **M5** WS | — | — | — | — | — | Token Validate | — | — |
| **M6** Auth | — | — | — | Lookup User | — | — | — | — |
| **M7** API | — | Detect API | — | CRUD | — | Validate | — | — |
| **M8** Task | Health Check | — | — | Aggregate | — | — | — | — |

### 6.2 Communication Protocols

```
┌────────────────────────────────────────────────────────────────────────┐
│                    INTER-MODULE COMMUNICATION                          │
│                                                                        │
│  ┌─────────┐  asyncio.Queue  ┌──────────┐                             │
│  │ M1      │ ═══════════════►│ M2       │  In-process, zero-copy      │
│  │ Camera  │  (numpy frame)  │ AI       │  Ultra-low latency (~1ms)   │
│  └─────────┘                 └──────────┘                             │
│                                                                        │
│  ┌─────────┐  Function Call  ┌──────────┐                             │
│  │ M2      │ ───────────────►│ M3       │  Direct method invocation   │
│  │ AI      │ (DetectionResult)│ Rules   │  Synchronous within async   │
│  └─────────┘                 └──────────┘                             │
│                                                                        │
│  ┌─────────┐  Async DB Call  ┌──────────┐                             │
│  │ M3/M7   │ ───────────────►│ M4       │  SQLAlchemy async session   │
│  │ Rules/  │  (ORM objects)  │ Data     │  Connection pool managed    │
│  │ API     │                 └──────────┘                             │
│  └─────────┘                                                          │
│                                                                        │
│  ┌─────────┐  WS send_json  ┌──────────┐                             │
│  │ M3/M8   │ ───────────────►│ M5       │  Async broadcast            │
│  │ Rules/  │  (JSON event)   │ WebSocket│  Non-blocking               │
│  │ Task    │                 └──────────┘                             │
│  └─────────┘                                                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Thiết Kế Non-Functional Requirements

### 7.1 Performance & Scalability

| Metric | Target | Giải Pháp |
|--------|--------|-----------|
| Throughput (cameras) | 10-20 concurrent | Async processing + Thread pool cho YOLO |
| Detection latency | < 50ms/frame (GPU) | YOLO optimized + Frame skip |
| DB write throughput | > 1000 ops/s | Batch INSERT + Connection pool (20) |
| WS broadcast latency | < 5ms | In-memory connection map |
| API response time | < 200ms (p95) | Redis cache + DB indexes |
| Dashboard refresh | < 1s | WebSocket push (không cần polling) |

### 7.2 Reliability & Monitoring

```
┌───────────────────────────────────────────────────────────┐
│              RELIABILITY MECHANISMS                        │
│                                                           │
│  ┌─────────────────────────┐  ┌────────────────────────┐  │
│  │ Camera Reconnection     │  │ Circuit Breaker        │  │
│  │ ─ Retry mỗi 5s          │  │ ─ Max 3 fails → stop   │  │
│  │ ─ Exponential backoff   │  │ ─ Auto-resume sau 60s  │  │
│  │ ─ Alert nếu offline >5m │  │ ─ Log tất cả failures  │  │
│  └─────────────────────────┘  └────────────────────────┘  │
│                                                           │
│  ┌─────────────────────────┐  ┌────────────────────────┐  │
│  │ DB Connection Pool      │  │ Graceful Shutdown       │  │
│  │ ─ pool_size: 20          │  │ ─ Stop camera streams   │  │
│  │ ─ max_overflow: 30       │  │ ─ Flush pending writes  │  │
│  │ ─ pool_pre_ping: True    │  │ ─ Close WS connections  │  │
│  └─────────────────────────┘  └────────────────────────┘  │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

### 7.3 Security Architecture

```
┌───────────────────────────────────────────────────────────┐
│              SECURITY LAYERS                               │
│                                                           │
│  Layer 1: Network                                         │
│  ─ Nginx reverse proxy (SSL/TLS termination)              │
│  ─ CORS whitelist (chỉ cho phép domain dashboard)         │
│  ─ Rate limiting (100 req/min per IP)                     │
│                                                           │
│  Layer 2: Authentication                                  │
│  ─ JWT Access Token (30 min TTL)                          │
│  ─ JWT Refresh Token (7 days, HttpOnly cookie)            │
│  ─ bcrypt password hashing (cost factor = 12)             │
│                                                           │
│  Layer 3: Authorization                                   │
│  ─ RBAC: admin (full) vs operator (read + confirm)        │
│  ─ Resource-level permissions                             │
│  ─ WebSocket auth via query param token                   │
│                                                           │
│  Layer 4: Data                                            │
│  ─ Input validation (Pydantic v2)                         │
│  ─ SQL injection prevention (SQLAlchemy ORM)              │
│  ─ UUID primary keys (non-guessable)                      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

---

## 8. Báo Cáo Nghiên Cứu: 2 Paper về Realtime Traffic Monitoring System

### 8.1 PAPER 1: "Intelligent Traffic Monitoring with YOLO26: A Case Study in Real-Time Vehicle Detection"

| Thuộc Tính | Chi Tiết |
|-----------|---------|
| **Nguồn** | IEEE International Conference on Communications and Computing Applications (ICCA), 2025 |
| **Tác giả** | Nghiên cứu nhóm từ IEEE ICCA |
| **Chủ đề** | Real-time traffic monitoring sử dụng YOLO26 kết hợp Object Tracking |
| **Link** | IEEE Xplore (DOI thông qua IEEE digital library) |

#### Tóm Tắt Nội Dung

Paper này trình bày một hệ thống giám sát giao thông thời gian thực sử dụng mô hình **YOLO26** — phiên bản mới nhất trong dòng YOLO với cải tiến đáng kể về **accuracy** và **inference speed**. Nghiên cứu kết hợp YOLO26 với các thuật toán tracking hiện đại như **BoT-SORT** và **ByteTrack** để duy trì identity của phương tiện qua nhiều frame liên tiếp.

#### Điểm Chính

1. **Object Detection**: YOLO26 đạt **mAP50 > 92%** trên bộ dữ liệu giao thông đô thị, vượt trội hơn YOLOv11 (~2-3% mAP).
2. **Multi-Object Tracking (MOT)**: Kết hợp BoT-SORT giúp theo dõi xe chính xác ngay cả khi bị che khuất (occlusion) — quan trọng cho bài toán đếm xe và đo tốc độ.
3. **Inference Speed**: YOLO26 medium đạt **~25ms/frame** trên GPU NVIDIA RTX 3060 — đủ nhanh cho xử lý real-time (40 FPS).
4. **Use Case**: Phát hiện và phân loại phương tiện (car, bus, truck, motorcycle, bicycle) trên camera giao thông.

#### Liên Hệ Với Đồ Án

| Điểm trong Paper | Áp Dụng cho Đồ Án |
|-----------------|-------------------|
| YOLO26 + BoT-SORT pipeline | Tham khảo cho module M2 (AI Inference) — Sử dụng YOLO26 cho accuracy và speed tối ưu |
| Multi-Object Tracking | Cần thiết cho module M3 (Rules Engine) — Tracking xe qua nhiều frame để đo tốc độ |
| Benchmark trên hardware cụ thể | Giúp ước tính latency cho hệ thống (Phase 3: YOLO Inference ~25ms) |
| Camera giao thông đô thị | Giống bối cảnh đề tài — camera IP tại giao lộ Việt Nam |

---

### 8.2 PAPER 2: "A Real-Time Traffic Violation Detection System on Highways Using Surveillance Cameras and Message-Oriented Middleware"

| Thuộc Tính | Chi Tiết |
|-----------|---------|
| **Nguồn** | IEEE Xplore, 2026 |
| **Tác giả** | Nghiên cứu nhóm IEEE |
| **Chủ đề** | Hệ thống phát hiện vi phạm giao thông real-time sử dụng camera giám sát kết hợp middleware phân tán |
| **Link** | IEEE Xplore (ieeexplore.ieee.org) |

#### Tóm Tắt Nội Dung

Paper này trình bày một **hệ thống phát hiện vi phạm giao thông trên cao tốc** hoàn chỉnh từ camera surveillance đến cảnh báo vi phạm. Điểm nổi bật là kiến trúc sử dụng **Message-Oriented Middleware (MOM)** — cụ thể là **Apache Kafka** — làm trung gian truyền tải sự kiện giữa các thành phần, cho phép hệ thống mở rộng linh hoạt (scalable) khi số lượng camera tăng.

#### Điểm Chính

1. **Image Processing Pipeline**: Hệ thống sử dụng pipeline xử lý hình ảnh nhiều tầng — từ capture frame → vehicle detection → rule evaluation → alert generation.
2. **Violation Detection**: Phát hiện các hành vi vi phạm trên cao tốc:
   - Dừng/đỗ xe trái phép trên cao tốc (illegal stops)
   - Đi ngược chiều (reversing on highway)
   - Vượt tốc độ cho phép (speeding)
3. **Distributed Event-Driven Architecture**: Sử dụng **Apache Kafka** làm message broker:
   - Camera processors (producers) gửi detection events vào Kafka topics
   - Violation checker (consumer) nhận và xử lý events
   - Dashboard (consumer) nhận cảnh báo real-time
   - Kiến trúc này cho phép scale horizontally — thêm camera chỉ cần thêm producer
4. **Performance**: Hệ thống đạt **end-to-end latency < 300ms** từ camera capture đến hiển thị cảnh báo trên dashboard.

#### Liên Hệ Với Đồ Án

| Điểm trong Paper | Áp Dụng cho Đồ Án |
|-----------------|-------------------|
| Message-Oriented Middleware (Kafka) | Tham khảo cho scaling tương lai: thay thế asyncio.Queue bằng Redis Pub/Sub hoặc Kafka |
| Event-Driven Architecture | Đã áp dụng tương tự trong Module M5 (WebSocket broadcast events) |
| Violation detection rules | Tham khảo cho Module M3 (Rules Engine) — bổ sung thêm rules cho cao tốc |
| End-to-end latency < 300ms | Xác nhận target latency < 500ms của đồ án là khả thi |
| Distributed system design | Tham khảo khi cần scale hệ thống lên > 50 cameras |

### 8.3 So Sánh 2 Paper

| Tiêu Chí | Paper 1 (YOLO26 + Tracking) | Paper 2 (Violation + Kafka) |
|----------|------------------------------|----------------------------|
| **Trọng tâm** | AI Detection + Tracking | System Architecture + Violation |
| **Mô hình AI** | YOLO26 (state-of-the-art) | Image processing pipeline |
| **Kiến trúc** | Monolithic | Distributed (Kafka) |
| **Tracking** | BoT-SORT / ByteTrack | Không đề cập chi tiết |
| **Vi phạm** | Không (chỉ detection) | Có (illegal stops, speeding) |
| **Scale** | Single server | Multi-node via Kafka |
| **Giá trị cho đồ án** | Cải tiến Module M2 (AI) | Cải tiến Module M3 (Rules) + Scalability |

### 8.4 Tổng Hợp Bài Học Từ 2 Paper

```
┌─────────────────────────────────────────────────────────────────────┐
│           BÀI HỌC RÚT RA CHO ĐỒ ÁN TỐT NGHIỆP                    │
│                                                                     │
│  Từ Paper 1 (YOLO26):                                              │
│  ✅ Sử dụng YOLO version mới nhất (YOLO26) cho accuracy cao hơn    │
│  ✅ PHẢI kết hợp Object Tracking (ByteTrack) cho đo tốc độ         │
│  ✅ Benchmark inference time trên hardware thực tế                  │
│  ✅ Frame skip strategy (5-10 frames) để giảm tải GPU               │
│                                                                     │
│  Từ Paper 2 (Kafka + Violations):                                   │
│  ✅ Event-driven architecture là best practice cho traffic system    │
│  ✅ Phát hiện vi phạm cần pipeline riêng (không gộp với detection)  │
│  ✅ Message queue giúp decouple camera → processing → dashboard     │
│  ✅ Latency < 300ms là achievable với kiến trúc phù hợp             │
│                                                                     │
│  Áp dụng chung:                                                     │
│  ✅ Kiến trúc modular (tách biệt detection, tracking, violation)    │
│  ✅ Real-time dashboard là requirement bắt buộc                     │
│  ✅ Cần support horizontal scaling cho production                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 9. Kết Luận & Bước Tiếp Theo

### 9.1 Tóm Tắt Kiến Trúc v1

Bản thiết kế kiến trúc sơ bộ v1 bao gồm:

| Thành Phần | Trạng Thái |
|-----------|-----------|
| ✅ Sơ đồ kiến trúc tổng thể (4 tầng) | Hoàn thành |
| ✅ 8 Backend Modules xác định rõ ràng | Hoàn thành |
| ✅ Luồng dữ liệu Camera → AI → DB → Dashboard | Hoàn thành |
| ✅ Module dependency graph | Hoàn thành |
| ✅ API endpoints map | Hoàn thành |
| ✅ File structure mapping | Hoàn thành |
| ✅ Latency estimation | Hoàn thành |
| ✅ Security architecture | Hoàn thành |
| ✅ 2 Paper nghiên cứu liên quan | Hoàn thành |

### 9.2 Bước Tiếp Theo (Roadmap)

```
Phase 1: Foundation (Tuần 1-2)
├── [ ] Khởi tạo project FastAPI
├── [ ] Setup Docker Compose (PostgreSQL + Redis)
├── [ ] Implement Module M6 (Auth - JWT)
├── [ ] Implement Module M4 (Database models + Alembic migrations)
└── [ ] Implement Module M7 (Basic REST APIs - Camera CRUD)

Phase 2: AI Pipeline (Tuần 3-4)
├── [ ] Implement Module M1 (Camera Ingestion - OpenCV)
├── [ ] Implement Module M2 (YOLO Service)
├── [ ] Implement Module M3 (Basic Rules Engine)
└── [ ] Integration test: Camera → YOLO → DB

Phase 3: Real-time (Tuần 5-6)
├── [ ] Implement Module M5 (WebSocket Dashboard)
├── [ ] Implement Module M8 (Task Scheduler)
├── [ ] End-to-end test: Camera → AI → DB → Dashboard
└── [ ] Dashboard Web Application (Frontend)

Phase 4: Polish & Deploy (Tuần 7-8)
├── [ ] Violation detection rules refinement
├── [ ] Performance optimization
├── [ ] Docker production build
├── [ ] Documentation & Demo preparation
└── [ ] Báo cáo Đồ Án Tốt Nghiệp
```

---

> **Ghi chú phiên bản:**
> - v1: Thiết kế sơ bộ — focus vào High-Level Architecture, Module Identification, Data Flow
> - v2 (dự kiến): Chi tiết Database Schema + API Specs + Docker Compose file
> - v3 (dự kiến): Implementation + Testing + Deployment

*Thiết kế kiến trúc hệ thống v1 | Hệ thống Giám sát Giao thông Thông minh | 15/06/2026*
