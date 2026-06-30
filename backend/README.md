# Smart Traffic Monitoring System — FastAPI Backend Skeleton

Hệ thống Giám sát Giao thông Thông minh sử dụng YOLO — Backend Foundation.

## Tech Stack
- **Framework**: FastAPI (Pydantic v2)
- **Database**: PostgreSQL 16 (Async SQLAlchemy + `asyncpg`)
- **Cache / WebSocket State**: Redis 7
- **Authentication**: JWT (Access Token + Refresh Token HttpOnly Cookie)
- **Migrations**: Alembic

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Dự Án

### 1. Chuẩn bị Môi trường
Sao chép file `.env` từ `.env.example` và điều chỉnh các giá trị phù hợp:
```bash
cp .env.example .env
```

### 2. Khởi chạy Database & Cache (Docker Compose)
Khởi chạy PostgreSQL và Redis:
```bash
docker compose up -d
```
Lệnh này sẽ chạy:
- PostgreSQL tại `localhost:5432` (Database: `traffic_monitoring`)
- Redis tại `localhost:6379`

### 3. Cài đặt Python Dependencies
Khởi tạo virtual environment và cài đặt các thư viện cần thiết:
```bash
python -m venv .venv
source .venv/bin/activate  # Trên Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Thiết lập migrations và chạy Database Migration
Áp dụng cấu trúc database hiện tại vào database PostgreSQL:
```bash
alembic upgrade head
```

### 5. Chạy Backend Server
Khởi chạy server Uvicorn ở chế độ phát triển (reload tự động):
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📌 Các Endpoint API Chính

Hệ thống cung cấp đầy đủ tài liệu API tương tác tại:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Danh sách Modules:
1. **Hệ thống (`/health`)**: Kiểm tra trạng thái kết nối Database & Redis.
2. **Xác thực (`/api/v1/auth`)**: Đăng nhập, đăng xuất, làm mới phiên đăng nhập (HttpOnly Cookie).
3. **Camera (`/api/v1/cameras`)**: Thêm, sửa, xóa, lấy thông tin camera và luồng video MJPEG.
4. **Nhận diện (`/api/v1/detections`)**: Lịch sử nhận diện YOLO, tải ảnh và chạy phân tích thử nghiệm.
5. **Vi phạm (`/api/v1/violations`)**: Danh sách vi phạm giao thông, phê duyệt/xác nhận bởi Operator, tìm kiếm biển số xe.
6. **Thống kê (`/api/v1/stats`)**: Báo cáo lưu lượng, vi phạm theo giờ, dữ liệu biểu đồ tổng quan (Dashboard).
7. **Thời gian thực (`/ws`)**: Kênh kết nối WebSocket gửi thông tin nhận diện trực tiếp.
