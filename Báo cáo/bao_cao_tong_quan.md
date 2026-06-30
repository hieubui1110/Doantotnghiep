# BÁO CÁO TỔNG QUAN NGHIÊN CỨU VÀ ĐỀ XUẤT KIẾN TRÚC BACKEND
# Hệ Thống Giám Sát Giao Thông Thông Minh Sử Dụng YOLO

> **Đồ Án Tốt Nghiệp** | Tổng Hợp Báo Cáo Nghiên Cứu 01, 02, 03  
> Ngày tạo: 07/06/2026  
> Người thực hiện: [Tên Sinh Viên]  
> Công nghệ đề xuất: FastAPI + YOLO + PostgreSQL + WebSockets + Docker  

---

## MỤC LỤC

1. [TỔNG QUAN ĐỀ TÀI](#tổng-quan-đề-tài)
2. [PHẦN 1: NGHIÊN CỨU SO SÁNH VÀ LỰA CHỌN WEB FRAMEWORK (Tóm tắt 01)](#phần-1-nghiên-cứu-so-sánh-và-lựa-chọn-web-framework-tóm-tắt-01)
    - [1.1 FastAPI và Flask](#11-fastapi-và-flask)
    - [1.2 Bảng So Sánh Chi Tiết](#12-bảng-so-sánh-chi-tiết)
    - [1.3 Lý Do Lựa Chọn FastAPI Cho Hệ Thống](#13-lý-do-lựa-chọn-fastapi-cho-hệ-thống)
3. [PHẦN 2: NGHIÊN CỨU SO SÁNH VÀ LỰA CHỌN CƠ SỞ DỮ LIỆU (Tóm tắt 02)](#phần-2-nghiên-cứu-so-sánh-và-lựa-chọn-cơ-sở-dữ-liệu-tóm-tắt-02)
    - [2.1 PostgreSQL và MySQL](#21-postgresql-và-mysql)
    - [2.2 Bảng So Sánh Đóng Góp Cho Giám Sát Giao Thông](#22-bảng-so-sánh-đóng-góp-cho-giám-sát-giao-thông)
    - [2.3 Lý Do Lựa Chọn PostgreSQL Cho Hệ Thống](#23-lý-do-lựa-chọn-postgresql-cho-hệ-thống)
4. [PHẦN 3: ĐỀ XUẤT KIẾN TRÚC VÀ CÁC THÀNH PHẦN CHỨC NĂNG (Tóm tắt 03)](#phần-3-đề-xuất-kiến-trúc-và-các-thành-phần-chức-năng-tóm-tắt-03)
    - [3.1 Mô Hình Kiến Trúc Tổng Thể](#31-mô-hình-kiến-trúc-tổng-thể)
    - [3.2 Luồng Hoạt Động Cốt Lõi](#32-luồng-hoạt-động-cốt-lõi)
    - [3.3 Thiết Kế Cơ Sở Dữ Liệu (Schema & ERD)](#33-thiết-kế-cơ-sở-dữ-liệu-schema-erd)
    - [3.4 Cấu Trúc Thư Mục Dự Án Chuẩn Hóa](#34-cấu-trúc-thư-mục-dự-án-chuẩn-hóa)
    - [3.5 Chiến Lược Triển Khai (Deployment)](#35-chiến-lược-triển-khai-deployment)
5. [KẾT LUẬN CHUNG](#kết-luận-chung)

---

## TỔNG QUAN ĐỀ TÀI

Đề tài **"Hệ thống giám sát giao thông thông minh sử dụng YOLO"** nhằm xây dựng một giải pháp tự động hóa quá trình nhận diện phương tiện, đo lường lưu lượng xe cộ, phát hiện các hành vi vi phạm giao thông (vượt đèn đỏ, đi sai làn, chạy quá tốc độ, không đội mũ bảo hiểm) thông qua dữ liệu camera IP công cộng. 

Để vận hành một hệ thống như vậy một cách ổn định, real-time và chính xác, kiến trúc **Backend** đóng vai trò xương sống với 3 nhiệm vụ trọng tâm:
1. **Xử lý luồng dữ liệu (Data Pipeline):** Thu nhận luồng video RTSP từ các camera giao thông, giải mã frame và đưa vào mô hình AI (YOLO) mà không gây trễ hoặc tràn bộ nhớ.
2. **Quản lý & Phân tích Dữ liệu:** Lưu trữ hàng triệu bản ghi nhận diện xe cộ mỗi ngày cùng thông tin tọa độ camera và hình ảnh bằng chứng vi phạm.
3. **Truyền dẫn Real-time:** Đẩy ngay lập tức các cảnh báo vi phạm và trạng thái lưu lượng trực tiếp lên Dashboard quản lý cho nhân viên vận hành (operators) qua WebSocket.

Báo cáo này tổng hợp kết quả nghiên cứu, so sánh công nghệ và đề xuất giải pháp kỹ thuật cụ thể dựa trên 3 tài liệu nghiên cứu chi tiết: [01_fastapi_vs_flask.md](./01_fastapi_vs_flask.md), [02_postgresql_vs_mysql.md](./02_postgresql_vs_mysql.md) và [03_backend_architecture.md](./03_backend_architecture.md).

---

## PHẦN 1: NGHIÊN CỨU SO SÁNH VÀ LỰA CHỌN WEB FRAMEWORK (Tóm tắt 01)

### 1.1 FastAPI và Flask
Khi xây dựng Backend API phục vụ các bài toán AI, hai lựa chọn phổ biến nhất trong hệ sinh thái Python là **FastAPI** và **Flask**:
* **Flask (WSGI):** Là micro-framework có tuổi đời lâu năm (từ 2010), thiết kế đồng bộ (synchronous). Flask cực kỳ đơn giản và linh hoạt nhưng gặp nhiều hạn chế khi xử lý I/O bất đồng bộ (RTSP streams từ camera) hoặc giữ kết nối WebSocket liên tục.
* **FastAPI (ASGI):** Là framework hiện đại (từ 2018) được xây dựng trên nền tảng **Starlette** (xử lý bất đồng bộ) và **Pydantic** (kiểm định dữ liệu). FastAPI hỗ trợ `async/await` native, cho phép xử lý hàng nghìn kết nối đồng thời với hiệu năng tương đương Node.js và Go.

### 1.2 Bảng So Sánh Chi Tiết

| Tiêu Chí | FastAPI | Flask | Tầm Quan Trọng Với Hệ Thống |
|----------|---------|-------|----------------------------|
| **Cơ chế xử lý** | Bất đồng bộ (Async/Await) | Đồng bộ (Sync - mặc định) | **Rất cao**: Cần xử lý đồng thời nhiều luồng camera mà không nghẽn. |
| **WebSocket** | Tích hợp sẵn (Native) | Cần extension (Flask-SocketIO) | **Cao**: Đẩy cảnh báo vi phạm real-time về dashboard. |
| **Kiểm định dữ liệu** | Pydantic (Validate & Type-safe) | Thủ công hoặc dùng extension | **Cao**: Đảm bảo dữ liệu bounding box, confidence từ YOLO gửi về đúng định dạng. |
| **Tự động sinh tài liệu** | OpenAPI/Swagger tự động ở `/docs` | Phải cấu hình thủ công | **Trung bình**: Giúp dễ dàng demo và tích hợp API. |
| **Background Tasks** | Hỗ trợ sẵn (Native background tasks) | Cần Celery/Redis phức tạp | **Cao**: Chạy YOLO inference hoặc lưu file bằng chứng ẩn dưới nền. |
| **Hiệu năng (I/O)** | Cực kỳ cao (~50k req/s) | Trung bình (~15k req/s) | **Rất cao**: Khi số lượng camera và lượng gửi tin tăng lên. |

### 1.3 Lý Do Lựa Chọn FastAPI Cho Hệ Thống
FastAPI được lựa chọn làm Web Framework cốt lõi vì:
1. **Xử lý song song không chặn (Non-blocking):** Nhờ cơ chế ASGI, khi một camera đang thực hiện việc giải mã hình ảnh hoặc ghi DB, CPU vẫn có thể xử lý luồng nhận diện từ camera khác mà không cần đợi.
2. **Tích hợp mô hình AI mượt mà:** Cho phép chạy YOLO inference bên trong ThreadPool thông qua `asyncio.to_thread` hoặc `run_in_executor`, tránh việc block event loop của server.
3. **Tương thích hoàn hảo với WebSockets:** Dễ dàng duy trì hàng trăm kết nối client giám sát dashboard và broadcast tín hiệu tức thì.

---

## PHẦN 2: NGHIÊN CỨU SO SÁNH VÀ LỰA CHỌN CƠ SỞ DỮ LIỆU (Tóm tắt 02)

### 2.1 PostgreSQL và MySQL
Hệ thống giám sát giao thông yêu cầu cơ sở dữ liệu (DBMS) phải đáp ứng tần suất ghi lớn, truy vấn thống kê phức tạp và hỗ trợ tốt các dạng dữ liệu đặc thù (vị trí GPS của camera, mảng dữ liệu xe cộ, metadata linh hoạt của YOLO).
* **MySQL:** Rất phổ biến, nhẹ, tối ưu cho các tác vụ đọc đơn giản. Tuy nhiên, khả năng hỗ trợ kiểu dữ liệu không cấu trúc (JSON) chỉ ở mức cơ bản (dạng text) và thiếu các extension địa lý mạnh mẽ.
* **PostgreSQL:** Là hệ quản trị cơ sở dữ liệu đối tượng - quan hệ (ORDBMS) tiên tiến. Hỗ trợ lưu trữ JSON nhị phân (`JSONB`), kiểu mảng (`ARRAY`), kiểu địa lý (`PostGIS`), và có cơ chế kiểm soát truy cập đồng thời đa phiên bản (`MVCC`) vượt trội.

### 2.2 Bảng So Sánh Đóng Góp Cho Giám Sát Giao Thông

| Tính năng yêu cầu | Giải pháp ở PostgreSQL | Giải pháp ở MySQL | Đánh giá ưu thế |
|-------------------|-------------------------|-------------------|:---------------:|
| **Metadata detection linh hoạt** | **JSONB** (Nhị phân, hỗ trợ đánh index GIN, truy vấn cực nhanh) | **JSON** (Lưu dạng text, không thể index sâu, chậm khi dữ liệu lớn) | **PostgreSQL vượt trội** |
| **Tọa độ vị trí Camera** | **PostGIS** (Tính khoảng cách địa lý, kiểm tra camera trong vùng định sẵn) | Spatial cơ bản (Hạn chế về hàm tính toán địa cầu thực tế) | **PostgreSQL vượt trội** |
| **Danh sách loại xe/vi phạm** | **ARRAY type** (Lưu dạng mảng `['car', 'bus']` trực tiếp trong ô dữ liệu) | Không hỗ trợ (Phải tách thành bảng phụ quan hệ nhiều-nhiều) | **PostgreSQL vượt trội** |
| **Độ chính xác thời gian** | **TIMESTAMPTZ** (Thời gian đi kèm thông tin timezone của camera) | TIMESTAMP / DATETIME (Hạn chế về đồng bộ múi giờ quốc tế) | **PostgreSQL tốt hơn** |
| **Ghi dữ liệu đồng thời** | **MVCC** (Camera ghi dữ liệu không chặn Dashboard đọc báo cáo) | InnoDB MVCC (Cơ bản nhưng dễ bị lock row khi tần suất ghi cực lớn) | **PostgreSQL tốt hơn** |
| **Tìm kiếm biển số vi phạm** | **Full-text search** (Đánh index GIN hỗ trợ tìm nhanh biển số, ghi chú) | Full-text search ở InnoDB (Hạn chế hơn trong cấu hình ngôn ngữ) | **PostgreSQL tốt hơn** |

### 2.3 Lý Do Lựa Chọn PostgreSQL Cho Hệ Thống
PostgreSQL được quyết định sử dụng nhờ các lý do cốt lõi:
1. **Lưu trữ JSONB tối ưu:** Mỗi phương tiện YOLO phát hiện ra sẽ có metadata khác nhau (xe máy cần thông tin mũ bảo hiểm; ô tô cần thông tin biển số, tốc độ). Lưu tất cả vào một trường `JSONB` giúp hệ thống không cần thay đổi cấu trúc bảng (schema) khi nâng cấp mô hình AI.
2. **Khả năng quản lý bản đồ với PostGIS:** Dễ dàng truy vấn tìm kiếm *"camera nào gần giao lộ X nhất"* hoặc *"thống kê lỗi vi phạm trong bán kính 1km từ điểm Y"*.
3. **Hiệu năng ghi đồng thời:** MVCC giúp hệ thống tiếp nhận luồng dữ liệu ghi liên tục từ 10-20 camera cùng lúc mà dashboard của điều phối viên vẫn cập nhật biểu đồ êm ái.

---

## PHẦN 3: ĐỀ XUẤT KIẾN TRÚC VÀ CÁC THÀNH PHẦN CHỨC NĂNG (Tóm tắt 03)

### 3.1 Mô Hình Kiến Trúc Tổng Thể
Hệ thống sử dụng kiến trúc phân tầng rõ ràng từ phần cứng camera, tầng xử lý trung gian, đến tầng lưu trữ và hiển thị:

```
┌────────────────────────────────────────────────────────┐
│                   IP CAMERAS (RTSP)                    │
│      [Camera 1]          [Camera 2]        [Camera N]  │
└──────────┬───────────────────┬───────────────────┬─────┘
           │ Video Stream      │                   │
           ▼                   ▼                   ▼
┌────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                     │
│  ┌──────────────────────────────────────────────────┐  │
│  │             Camera Stream Processors             │  │
│  │   - OpenCV Frame Capture (Không chặn)            │  │
│  │   - YOLO Inference (Thread Pool execution)       │  │
│  │   - Rules Engine (Phát hiện vượt đèn đỏ/tốc độ)  │  │
│  └───────────────────────┬──────────────────────────┘  │
│                          │                             │
│       ┌──────────────────┴──────────────────┐          │
│       ▼                                     ▼          │
│  ┌──────────────┐                     ┌─────────────┐  │
│  │  REST APIs   │                     │ WebSockets  │  │
│  │  (Operator,  │                     │ (Dashboard  │  │
│  │   Cameras,   │                     │  Real-time) │  │
│  │   Detections)│                     └──────▲──────┘  │
│  └────┬─────────┘                            │         │
│       │                                      │         │
│  ┌────▼──────────────────────────────────────┴──────┐  │
│  │           Data Access Layer (SQLAlchemy Async)   │  │
└──┴───────────────────────┬──────────────────────────┴──┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                  │
│   [Cameras]    [Detections]    [Violations]   [Stats]  │
└────────────────────────────────────────────────────────┘
```

### 3.2 Luồng Hoạt Động Cốt Lõi

1. **Luồng Nhận Diện YOLO (Inference Pipeline):**
   * OpenCV kết nối đến link RTSP của camera IP và lấy frame hình ảnh.
   * Frame được gửi đến service xử lý chạy YOLO (đã được bọc trong ThreadPool qua executor để đảm bảo server FastAPI không bị đơ).
   * YOLO trả ra tọa độ bounding box (`x1, y1, x2, y2`), độ tin cậy (`confidence`), và nhãn loại xe (`vehicle_type`).
2. **Luồng Lưu Trữ & Phân Tích Luật (Rules Engine):**
   * Hệ thống đối chiếu tọa độ xe với vùng ảo (Polygon) vẽ trên camera để kiểm tra vi phạm (vượt đèn đỏ khi đèn tín hiệu chuyển đỏ, đi sai làn đường quy định).
   * Dữ liệu nhận diện được lưu vào bảng `detections` (dữ liệu thô). Nếu có lỗi, một bản ghi được chèn vào bảng `violations` kèm theo URL ảnh bằng chứng.
3. **Luồng Cảnh Báo Real-time (WebSocket):**
   * Ngay khi ghi nhận vi phạm, `DashboardManager` sẽ thực hiện quét danh sách các WebSocket đang kết nối và đẩy bản tin cảnh báo xuống Web Browser của nhân viên giám sát trong thời gian `< 500ms`.

### 3.3 Thiết Kế Cơ Sở Dữ Liệu (Schema & ERD)

Thiết kế DB sử dụng tối đa sức mạnh kiểu dữ liệu của PostgreSQL để tối ưu dung lượng và tốc độ truy vấn:

* **Bảng `operators`:** Lưu tài khoản cán bộ vận hành, phân quyền `role` (operator/admin).
* **Bảng `cameras`:** Lưu thông tin camera, link RTSP, kinh độ/vĩ độ GPS, và mảng loại xe cần bắt `vehicle_types TEXT[]`.
* **Bảng `detections`:** Bảng chứa lượng dữ liệu lớn nhất. Sử dụng UUID làm khóa chính, bbox và metadata lưu dạng `JSONB`.
* **Bảng `violations`:** Lưu thông tin vi phạm, kết nối trực tiếp đến bảng `detections` và `cameras`. Đánh index Full-text Search trên biển số xe để tìm kiếm nhanh.
* **Bảng `traffic_stats`:** Bảng tổng hợp lưu lượng theo từng khung giờ (Hour-based rollup) của từng camera để vẽ biểu đồ lịch sử, giúp giảm tải việc phải `COUNT(*)` trên hàng triệu dòng dữ liệu thô.

```
┌─────────────────┐             ┌─────────────────┐
│     cameras     │             │    operators    │
├─────────────────┤             ├─────────────────┤
│ id (UUID, PK)   │             │ id (UUID, PK)   │
│ name            │             │ username        │
│ rtsp_url        │             │ role (auth)     │
│ latitude/longitude            │ is_active       │
│ status          │             └────────┬────────┘
└──────┬───┬──────┘                      │
       │   │                             │ phê duyệt
    1:N│   │1:N                          │ (confirms)
       │   └──────────────────────┐      ▼
       ▼                          ▼ ┌───────────────┐
┌──────────────┐                 │ │  violations   │
│traffic_stats │                 │ ├───────────────┤
├──────────────┤                 │ │ id (UUID, PK) │
│camera_id (FK)│                 │ │ detection_id  │
│hour (PK)     │                 │ │ camera_id (FK)│
│total_vehicles│                 │ │violation_type │
│avg_speed     │                 │ │license_plate  │
└──────────────┘                 │ │evidence_url   │
                                 │ │confirmed_by   │
                                 │ └────────▲──────┘
                               1:N│          │
                                 ▼          │ 1:1
                        ┌──────────────┐    │
                        │  detections  ├────┘
                        ├──────────────┤
                        │ id (UUID, PK)│
                        │ camera_id(FK)│
                        │ vehicle_type │
                        │ bbox (JSONB) │
                        │timestamp     │
                        └──────────────┘
```

### 3.4 Cấu Trúc Thư Mục Dự Án Chuẩn Hóa
Hệ thống được tổ chức theo cấu trúc module hóa chuẩn của FastAPI, tách biệt rõ ràng giữa models (database), schemas (validate dữ liệu) và services (xử lý logic):

```
traffic-monitoring/
├── 📁 app/
│   ├── 📄 main.py                    # Điểm khởi chạy FastAPI, Lifespan và Middleware CORS
│   ├── 📁 api/                       # Chứa các endpoint API chia theo phiên bản
│   │   └── 📁 v1/
│   │       ├── 📄 router.py          # Gom tất cả các router con
│   │       ├── 📄 auth.py            # API đăng nhập/đăng xuất/refresh JWT
│   │       ├── 📄 cameras.py         # API quản trị danh sách camera
│   │       ├── 📄 detections.py      # API nhận diện ảnh và lấy lịch sử detection
│   │       ├── 📄 violations.py      # API kiểm soát và phê duyệt vi phạm
│   │       ├── 📄 stats.py           # API lấy số liệu thống kê vẽ biểu đồ
│   │       └── 📄 websocket.py       # API kết nối WebSocket cho Dashboard
│   ├── 📁 core/                      # Cấu hình hệ thống, kết nối DB, cấu hình bảo mật
│   │   ├── 📄 config.py              # Đọc biến môi trường từ file .env qua Pydantic
│   │   ├── 📄 database.py            # Cài đặt Async engine (asyncpg) & sessionmaker
│   │   └── 📄 security.py            # Băm mật khẩu bcrypt, tạo/mã hóa JWT token
│   ├── 📁 models/                    # Khai báo các bảng dữ liệu SQLAlchemy ORM
│   ├── 📁 schemas/                   # Định nghĩa Pydantic schemas để validate đầu vào/ra
│   ├── 📁 services/                  # Nơi xử lý logic nghiệp vụ chính
│   │   ├── 📄 yolo_service.py        # Quản lý vòng đời load model YOLO và chạy inference
│   │   ├── 📄 camera_processor.py    # Xử lý kết nối RTSP và điều phối frame
│   │   └── 📄 violation_checker.py   # Thực hiện kiểm tra lỗi vi phạm giao thông
│   └── 📁 websocket/
│       └── 📄 manager.py             # Quản lý vòng đời kết nối WebSocket (DashboardManager)
├── 📁 yolo_models/                   # Thư mục lưu file weights của model YOLO (best.pt)
├── 📄 .env                           # File cấu hình cấu hình môi trường
├── 📄 requirements.txt               # Danh sách các thư viện Python cần cài đặt
└── 📄 docker-compose.yml             # Cấu hình container chạy DB Postgres và Backend
```

### 3.5 Chiến Lược Triển Khai (Deployment)
* **Chạy thử nghiệm (Staging/Demo):**
  * Triển khai nhanh cơ sở dữ liệu trên các dịch vụ Cloud Managed DB có hỗ trợ sẵn PostgreSQL miễn phí/chi phí thấp như **Supabase** hoặc **Neon**.
  * Chạy server backend FastAPI trên **Railway** (hỗ trợ deploy trực tiếp từ file Dockerfile rất tiện lợi).
* **Triển khai thực tế (Production):**
  * Sử dụng **Docker Compose** đóng gói toàn bộ hệ thống.
  * Cấu hình Nginx làm Reverse Proxy, mở port `443` (SSL) cho REST API và hỗ trợ upgrade giao thức lên WSS (WebSocket Secure).
  * **GPU Acceleration:** Sử dụng driver NVIDIA trong Docker (`nvidia-container-toolkit`) để cấp quyền truy cập GPU cho container FastAPI, nâng tốc độ chạy YOLO đạt ngưỡng tối đa (dưới `30ms/frame`).

---

## KẾT LUẬN CHUNG

Qua quá trình nghiên cứu và xây dựng báo cáo tổng quan, stack công nghệ **FastAPI + YOLO + PostgreSQL** được đánh giá là giải pháp hoàn thiện nhất cho **Hệ thống giám sát giao thông thông minh**:

1. **Về hiệu năng xử lý:** Sự kết hợp giữa khả năng lập trình bất đồng bộ (`async`) của FastAPI và khả năng tính toán song song của mô hình YOLO trên GPU đảm bảo hệ thống tiếp nhận luồng dữ liệu camera lớn liên tục mà không gây hiện tượng nghẽn cổ chai.
2. **Về khả năng quản trị dữ liệu:** PostgreSQL với extension PostGIS và cấu trúc dữ liệu JSONB giúp giải quyết triệt để hai bài toán phức tạp nhất là lưu trữ metadata nhận dạng động và quản lý định vị địa lý camera trên bản đồ.
3. **Về trải nghiệm người dùng:** Cơ chế truyền tin WebSocket giúp dashboard giám sát trực quan hóa các lỗi vi phạm ngay lập tức, hỗ trợ tối đa cho cảnh sát giao thông hoặc điều phối viên trong việc ra quyết định xử phạt kịp thời.

Bộ tài liệu chi tiết đính kèm:
* So sánh chi tiết web framework: [01_fastapi_vs_flask.md](./01_fastapi_vs_flask.md)
* So sánh chi tiết cơ sở dữ liệu: [02_postgresql_vs_mysql.md](./02_postgresql_vs_mysql.md)
* Bản thiết kế kiến trúc và mã nguồn mẫu: [03_backend_architecture.md](./03_backend_architecture.md)
