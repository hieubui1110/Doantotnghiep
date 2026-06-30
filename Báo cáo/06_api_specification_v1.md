# Thiết Kế Chi Tiết API Specification — v1
# Hệ Thống Giám Sát Giao Thông Thông Minh Sử Dụng YOLO

> **Đồ Án Tốt Nghiệp** | API Specification v1
> Ngày tạo: 19/06/2026
> Phiên bản API: `v1` (tiền tố `/api/v1`)
> Định dạng truyền tải: JSON (UTF-8)

---

## MỤC LỤC

1. [Tổng Quan Thiết Kế (API Conventions)](#1-tổng-quan-thiết-kế-api-conventions)
2. [Cơ Chế Xác Thực & Phân Quyền (Authentication & RBAC)](#2-cơ-chế-xác-thực--phân-quyền-authentication--rbac)
3. [Định Dạng Lỗi Chuẩn (Error Responses)](#3-định-dạng-lỗi-chuẩn-error-responses)
4. [Tài Liệu Chi Tiết Các Endpoint (REST API)](#4-tài-liệu-chi-tiết-các-endpoint-rest-api)
   - [4.1 Module M6/M7: Auth (Xác Thực)](#41-module-m6m7-auth-xác-thực)
   - [4.2 Module M2/M7: Cameras (Quản Lý Camera)](#42-module-m2m7-cameras-quản-lý-camera)
   - [4.3 Module M3/M7: Detections (Nhận Diện YOLO)](#43-module-m3m7-detections-nhận-diện-yolo)
   - [4.4 Module M4/M7: Violations (Xử Lý Vi Phạm)](#44-module-m4m7-violations-xử-lý-vi-phạm)
   - [4.5 Module M5/M7: Stats & Charts (Thống Kê)](#45-module-m5m7-stats--charts-thống-kê)
5. [Đường Truyền Thời Gian Thực (WebSocket Specification)](#5-đường-truyền-thời-gian-thực-websocket-specification)

---

## 1. Tổng Quan Thiết Kế (API Conventions)

- **Kiến trúc**: RESTful API.
- **Tiền tố đường dẫn (Base URL)**: `http://localhost:8000/api/v1`
- **Mã hóa ký tự**: `application/json; charset=utf-8` (ngoại trừ luồng video và tệp tin).
- **HTTP Methods sử dụng**:
  - `GET`: Truy xuất thông tin (không làm thay đổi trạng thái hệ thống).
  - `POST`: Tạo mới tài nguyên hoặc thực hiện hành động (như đăng nhập).
  - `PUT`: Cập nhật toàn bộ/một phần tài nguyên hiện có.
  - `DELETE`: Xóa tài nguyên.

---

## 2. Cơ Chế Xác Thực & Phân Quyền (Authentication & RBAC)

Hệ thống sử dụng cơ chế xác thực kép dựa trên **JSON Web Token (JWT)**:
1. **Access Token**:
   - Truyền qua HTTP Header: `Authorization: Bearer <access_token>`
   - Thời gian hết hạn (TTL): 30 phút.
   - Chứa thông tin: ID nhân viên (`sub`) và vai trò (`role`).
2. **Refresh Token**:
   - Lưu trữ tại client dưới dạng **HttpOnly, Secure, SameSite=Lax Cookie**.
   - Thời gian hết hạn (TTL): 7 ngày.
   - Hash SHA-256 được lưu trong database để quản lý phiên và thu hồi (Logout).

### Phân Quyền Vai Trò (Role-Based Access Control)
- **`admin`**: Toàn quyền trên hệ thống (Quản lý camera, xem lịch sử, xử lý vi phạm, cấu hình hệ thống).
- **`operator`**: Quyền vận hành (Xem dashboard, giám sát trực tuyến camera, phê duyệt/xác nhận vi phạm, xem thống kê).

---

## 3. Định Dạng Lỗi Chuẩn (Error Responses)

Khi yêu cầu gặp lỗi, hệ thống sẽ trả về mã HTTP tương ứng kèm theo JSON payload chi tiết:

```json
{
  "detail": "Mô tả chi tiết nguyên nhân gây lỗi bằng Tiếng Việt"
}
```

### Các Mã Trạng Thái HTTP Thường Gặp:
- **`400 Bad Request`**: Dữ liệu gửi lên không đúng định dạng logic hoặc vi phạm ràng buộc.
- **`401 Unauthorized`**: Thiếu Access Token, token hết hạn, hoặc chữ ký token không hợp lệ.
- **`403 Forbidden`**: Token hợp lệ nhưng tài khoản không có quyền thực hiện hành động này (ví dụ: operator cố gắng xóa camera).
- **`404 Not Found`**: Không tìm thấy tài nguyên yêu cầu (ID không tồn tại).
- **`422 Unprocessable Entity`**: Lỗi xác thực dữ liệu từ Pydantic (thiếu trường bắt buộc, sai kiểu dữ liệu).
- **`500 Internal Server Error`**: Lỗi hệ thống phát sinh từ phía server.

---

## 4. Tài Liệu Chi Tiết Các Endpoint (REST API)

### 4.1 Module M6/M7: Auth (Xác Thực)

#### 4.1.1 Đăng Nhập Hệ Thống
- **Endpoint**: `POST /auth/login`
- **Quyền truy cập**: Public
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "password123"
  }
  ```
- **Response (200 OK)**:
  - Đồng thời thiết lập Cookie: `refresh_token=<token>; HttpOnly; Path=/; Max-Age=604800`
  - Body:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

#### 4.1.2 Làm Mới Phiên Đăng Nhập (Access Token)
- **Endpoint**: `POST /auth/refresh`
- **Quyền truy cập**: Public (Đọc cookie `refresh_token`)
- **Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.new...",
    "token_type": "bearer",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

#### 4.1.3 Đăng Xuất Hệ Thống
- **Endpoint**: `POST /auth/logout`
- **Quyền truy cập**: Đã đăng nhập (Bearer Token + Cookie)
- **Response (200 OK)**:
  ```json
  {
    "message": "Đăng xuất thành công"
  }
  ```

#### 4.1.4 Lấy Thông Tin Cá Nhân
- **Endpoint**: `GET /auth/me`
- **Quyền truy cập**: Đã đăng nhập (Bearer Token)
- **Response (200 OK)**:
  ```json
  {
    "id": "e305e94b-014c-474e-8cd2-54c7d0d0be00",
    "username": "nguyenvanan",
    "email": "an.nv@traffic.gov.vn",
    "full_name": "Nguyễn Văn An",
    "role": "operator",
    "is_active": true,
    "created_at": "2026-06-15T08:30:00Z",
    "updated_at": "2026-06-18T10:15:00Z"
  }
  ```

---

### 4.2 Module M2/M7: Cameras (Quản Lý Camera)

#### 4.2.1 Lấy Danh Sách Camera
- **Endpoint**: `GET /cameras`
- **Quyền truy cập**: `admin`, `operator` (Bearer Token)
- **Response (200 OK)**:
  ```json
  [
    {
      "id": "905ba213-90d2-432d-9477-7427cc789a01",
      "name": "Camera Ngã Tư Hàng Xanh - Hướng Bắc",
      "rtsp_url": "rtsp://192.168.1.100:554/stream1",
      "latitude": 10.801648,
      "longitude": 106.711802,
      "address": "Bình Thạnh, Thành phố Hồ Chí Minh",
      "intersection": "Ngã Tư Hàng Xanh",
      "direction": "north",
      "status": "active",
      "config": {
        "confidence_threshold": 0.55,
        "speed_limit": 60
      },
      "vehicle_types": ["car", "truck", "bus", "motorcycle"],
      "created_at": "2026-06-15T09:00:00Z",
      "updated_at": null
    }
  ]
  ```

#### 4.2.2 Thêm Camera Mới
- **Endpoint**: `POST /cameras`
- **Quyền truy cập**: `admin` (Bearer Token)
- **Request Body**:
  ```json
  {
    "name": "Camera Ngã Tư Hàng Xanh - Hướng Nam",
    "rtsp_url": "rtsp://192.168.1.101:554/stream1",
    "latitude": 10.801450,
    "longitude": 106.711802,
    "address": "Bình Thạnh, Thành phố Hồ Chí Minh",
    "intersection": "Ngã Tư Hàng Xanh",
    "direction": "south",
    "status": "active",
    "config": {
      "confidence_threshold": 0.50
    },
    "vehicle_types": ["car", "motorcycle"]
  }
  ```
- **Response (201 Created)**: Trả về object camera hoàn chỉnh kèm `id` và `created_at`.

#### 4.2.3 Cập Nhật Cấu Hình Camera
- **Endpoint**: `PUT /cameras/{id}`
- **Quyền truy cập**: `admin` (Bearer Token)
- **Request Body**: Các trường cần sửa đổi (hỗ trợ cập nhật một phần).
- **Response (200 OK)**: Object camera đã được cập nhật thành công.

#### 4.2.4 Luồng Xem Trực Tuyến (MJPEG Video Stream)
- **Endpoint**: `GET /cameras/{id}/stream`
- **Quyền truy cập**: `admin`, `operator`
- **Response (200 OK)**:
  - Header: `Content-Type: multipart/x-mixed-replace; boundary=frame`
  - Body: Luồng nhị phân các frame hình ảnh ảnh JPEG liên tiếp.

---

### 4.3 Module M3/M7: Detections (Nhận Diện YOLO)

#### 4.3.1 Truy Vấn Lịch Sử Nhận Diện (Detections Log)
- **Endpoint**: `GET /detections`
- **Quyền truy cập**: `admin`, `operator`
- **Query Parameters**:
  - `camera_id` (UUID, tùy chọn): Lọc theo camera.
  - `vehicle_type` (String, tùy chọn): `car`, `truck`, `bus`, `motorcycle`, `bicycle`.
  - `start_time` / `end_time` (ISO DateTime, tùy chọn): Khoảng thời gian.
  - `limit` (Int, default 20) / `offset` (Int, default 0): Phân trang.
- **Response (200 OK)**:
  ```json
  {
    "items": [
      {
        "id": "14f2e96d-3172-46db-ab61-cd185bb0eabc",
        "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
        "frame_id": 482010,
        "vehicle_type": "car",
        "confidence": 0.945,
        "bbox": {
          "x1": 150.2,
          "y1": 200.5,
          "x2": 350.8,
          "y2": 420.0
        },
        "metadata": {
          "color": "red",
          "speed_kmh": 55.4
        },
        "detected_at": "2026-06-19T08:00:15Z"
      }
    ],
    "total": 128503,
    "limit": 20,
    "offset": 0
  }
  ```

#### 4.3.2 Tải Ảnh Chạy Thử YOLO (Testing Upload)
- **Endpoint**: `POST /detections/detect`
- **Content-Type**: `multipart/form-data`
- **Quyền truy cập**: `admin`, `operator`
- **Request (Form Data)**:
  - `camera_id`: `905ba213-90d2-432d-9477-7427cc789a01`
  - `file`: (File ảnh JPEG/PNG)
- **Response (201 Created)**: Trả về mảng các đối tượng phương tiện được phát hiện trong ảnh.

---

### 4.4 Module M4/M7: Violations (Xử Lý Vi Phạm)

#### 4.4.1 Lấy Danh Sách Lịch Sử Vi Phạm
- **Endpoint**: `GET /violations`
- **Query Parameters**:
  - `camera_id` (UUID, tùy chọn)
  - `violation_type` (String, tùy chọn): `red_light`, `speeding`, `wrong_lane`, `no_helmet`.
  - `is_confirmed` (Boolean, tùy chọn): Đã duyệt hoặc chưa duyệt.
  - `limit` / `offset` (Phân trang)
- **Response (200 OK)**:
  ```json
  {
    "items": [
      {
        "id": "e280ff52-bcda-411a-829d-400908e2f001",
        "detection_id": "14f2e96d-3172-46db-ab61-cd185bb0eabc",
        "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
        "violation_type": "red_light",
        "vehicle_type": "motorcycle",
        "license_plate": "59A-999.99",
        "confidence": 0.88,
        "evidence_url": "/evidence/2026-06-19/cam_001/vio_red_light.jpg",
        "metadata": {
          "signal_state": "red",
          "lane_info": "lane_2"
        },
        "is_confirmed": false,
        "confirmed_by": null,
        "notes": null,
        "created_at": "2026-06-19T08:00:15Z"
      }
    ],
    "total": 412,
    "limit": 20,
    "offset": 0
  }
  ```

#### 4.4.2 Phê Duyệt / Xác Nhận Vi Phạm
- **Endpoint**: `PUT /violations/{id}/confirm`
- **Quyền truy cập**: `admin`, `operator`
- **Request Body**:
  ```json
  {
    "notes": "Biển số xe rõ ràng, xác nhận vượt đèn đỏ lúc tín hiệu đã đỏ được 2.5s."
  }
  ```
- **Response (200 OK)**: Trả về đối tượng vi phạm đã cập nhật trạng thái `"is_confirmed": true` và `"confirmed_by"` chứa ID của Operator vừa gọi API.

#### 4.4.3 Tìm Kiếm Vi Phạm Theo Biển Số Hoặc Ghi Chú
- **Endpoint**: `GET /violations/search`
- **Query Parameters**:
  - `q` (String, Bắt buộc): Từ khóa tìm kiếm (Biển số xe ví dụ `"59A"`, hoặc ghi chú).
  - `limit` / `offset` (Phân trang)
- **Response (200 OK)**: Trả về danh sách vi phạm khớp với từ khóa tìm kiếm (Sắp xếp theo thời gian giảm dần).

---

### 4.5 Module M5/M7: Stats & Charts (Thống Kê)

#### 4.5.1 Thống Kê Lưu Lượng Theo Giờ
- **Endpoint**: `GET /stats/traffic`
- **Query Parameters**:
  - `camera_id` (UUID, tùy chọn)
  - `start_time` / `end_time` (DateTime)
- **Response (200 OK)**:
  ```json
  [
    {
      "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
      "hour": "2026-06-19T08:00:00Z",
      "total_vehicles": 1240,
      "car_count": 820,
      "truck_count": 50,
      "bus_count": 30,
      "motorcycle_count": 330,
      "bicycle_count": 10,
      "violation_count": 5,
      "avg_speed": 42.5
    }
  ]
  ```

#### 4.5.2 Phân Tích Tổng Hợp Vi Phạm
- **Endpoint**: `GET /stats/violations`
- **Response (200 OK)**:
  ```json
  {
    "total_violations": 412,
    "by_type": {
      "red_light": 120,
      "speeding": 182,
      "wrong_lane": 80,
      "no_helmet": 30
    },
    "by_status": {
      "confirmed": 350,
      "unconfirmed": 62
    },
    "by_camera": {}
  }
  ```

#### 4.5.3 Dữ Liệu Tổng Quan Dashboard (Dashboard Metrics)
- **Endpoint**: `GET /stats/dashboard`
- **Response (200 OK)**: Trả về số lượng camera active, số lượng nhận diện/vi phạm trong ngày, phân bổ loại phương tiện và lịch sử vi phạm mới nhất để vẽ biểu đồ thời gian thực trên Frontend.

---

## 5. Đường Truyền Thời Gian Thực (WebSocket Specification)

Để hỗ trợ hiển thị dữ liệu và hình ảnh trực tiếp không độ trễ lên Dashboard giám sát, backend cung cấp luồng kết nối WebSocket bảo mật:

### 5.1 Kênh Tổng Quan Dashboard
- **URL**: `ws://localhost:8000/ws/dashboard?token=<access_token>`
- **Hướng truyền**: Server-to-Client (Push notification)
- **Danh sách Event phát từ Server**:

#### Event 1: Phát hiện phương tiện mới (`detection`)
```json
{
  "event": "detection",
  "data": {
    "id": "14f2e96d-3172-46db-ab61-cd185bb0eabc",
    "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
    "vehicle_type": "car",
    "confidence": 0.92,
    "bbox": {"x1": 150.2, "y1": 200.5, "x2": 350.8, "y2": 420.0},
    "detected_at": "2026-06-19T08:00:15Z"
  }
}
```

#### Event 2: Cảnh báo vi phạm giao thông (`violation_alert`)
```json
{
  "event": "violation_alert",
  "data": {
    "id": "e280ff52-bcda-411a-829d-400908e2f001",
    "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
    "violation_type": "red_light",
    "vehicle_type": "motorcycle",
    "license_plate": "59A-999.99",
    "evidence_url": "/evidence/2026-06-19/cam_001/vio_red_light.jpg",
    "created_at": "2026-06-19T08:00:15Z"
  }
}
```

#### Event 3: Thay đổi trạng thái camera (`camera_status`)
```json
{
  "event": "camera_status",
  "data": {
    "camera_id": "905ba213-90d2-432d-9477-7427cc789a01",
    "status": "inactive"
  }
}
```

---

### 5.2 Kênh Stream Camera Riêng Biệt
- **URL**: `ws://localhost:8000/ws/camera/{id}/stream?token=<access_token>`
- **Mục đích**: Truyền tải tọa độ bounding box hoặc luồng frame kết quả nhị phân trực tiếp cho một camera cụ thể được chọn.
