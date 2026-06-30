# Thiết Kế Cơ Sở Dữ Liệu — v1
# Hệ Thống Giám Sát Giao Thông Thông Minh Sử Dụng YOLO

> **Đồ Án Tốt Nghiệp** | Database Design v1
> Ngày tạo: 19/06/2026
> Database: PostgreSQL 16
> ORM: SQLAlchemy 2.0 (Async)
> Tài liệu liên quan: [04 - System Architecture](./04_system_architecture_v1.md) | [03 - Backend Architecture](./Báo%20cáo/03_backend_architecture.md)

---

## MỤC LỤC

1. [ERD — Entity Relationship Diagram](#1-erd--entity-relationship-diagram)
2. [Database Schema (SQL DDL)](#2-database-schema-sql-ddl)
3. [Data Dictionary](#3-data-dictionary)
4. [Index Strategy](#4-index-strategy)
5. [Quan Hệ Giữa Các Bảng](#5-quan-hệ-giữa-các-bảng)
6. [Triển Khai Backend Cơ Bản](#6-triển-khai-backend-cơ-bản)
---
## 1. ERD — Entity Relationship Diagram

### 1.1 Mermaid ER Diagram

```mermaid
erDiagram
    operators {
        UUID id PK "gen_random_uuid()"
        VARCHAR_50 username UK "NOT NULL, UNIQUE"
        VARCHAR_255 email UK "NOT NULL, UNIQUE"
        VARCHAR_255 hashed_password "NOT NULL"
        VARCHAR_255 full_name "NULL"
        VARCHAR_20 role "NOT NULL, DEFAULT 'operator'"
        BOOLEAN is_active "NOT NULL, DEFAULT TRUE"
        TIMESTAMPTZ created_at "NOT NULL, DEFAULT NOW()"
        TIMESTAMPTZ updated_at "NULL"
    }

    cameras {
        UUID id PK "gen_random_uuid()"
        VARCHAR_255 name "NOT NULL"
        VARCHAR_255 intersection "NULL — Tên giao lộ"
        VARCHAR_50 direction "NULL — north/south/east/west"
        VARCHAR_20 status "NOT NULL, DEFAULT 'active'"
        JSONB config "DEFAULT '{}'"
        TEXT_ARRAY vehicle_types "DEFAULT '{}'"
        TIMESTAMPTZ created_at "NOT NULL, DEFAULT NOW()"
        TIMESTAMPTZ updated_at "NULL"
    }

    detections {
        UUID id PK "gen_random_uuid()"
        UUID camera_id FK "NOT NULL → cameras.id"
        BIGINT frame_id "NOT NULL"
        VARCHAR_50 vehicle_type "NOT NULL"
        FLOAT confidence "NOT NULL"
        JSONB bbox "NOT NULL — x1,y1,x2,y2"

    violations {
        UUID id PK "gen_random_uuid()"
        UUID detection_id FK "NULL → detections.id"
        UUID camera_id FK "NOT NULL → cameras.id"
        VARCHAR_50 violation_type "NOT NULL"
        VARCHAR_50 vehicle_type "NOT NULL"
        VARCHAR_20 license_plate "NULL"
        FLOAT confidence "NOT NULL"
        TEXT evidence_url "NULL"
        JSONB metadata "DEFAULT '{}'"
        BOOLEAN is_confirmed "NOT NULL, DEFAULT FALSE"
        UUID confirmed_by FK "NULL → operators.id"
        TEXT notes "NULL"
        TIMESTAMPTZ created_at "NOT NULL, DEFAULT NOW()"
    }

    traffic_stats {
        UUID camera_id PK_FK "NOT NULL → cameras.id"
        TIMESTAMPTZ hour PK "NOT NULL — Đầu mỗi giờ"
        INTEGER truck_count "DEFAULT 0"
        INTEGER bus_count "DEFAULT 0"
        INTEGER motorcycle_count "DEFAULT 0"
    }

    refresh_tokens {
        UUID operator_id FK "NOT NULL → operators.id"
        VARCHAR_255 token_hash UK "NOT NULL, UNIQUE"
        TIMESTAMPTZ expires_at "NOT NULL"
        TIMESTAMPTZ created_at "NOT NULL, DEFAULT NOW()"
    }

    operators ||--o{ violations : "confirms"
    operators ||--o{ refresh_tokens : "has"
    cameras ||--o{ detections : "produces"
    cameras ||--o{ violations : "records"
    cameras ||--o{ traffic_stats : "aggregates"
    detections ||--o| violations : "triggers"
```

### 1.2 Mô Tả Quan Hệ

| Quan Hệ | Loại | Mô Tả |
|----------|------|--------|
| `operators` → `violations` | 1:N (optional) | Operator xác nhận vi phạm (`confirmed_by`) |
| `operators` → `refresh_tokens` | 1:N | Operator sở hữu nhiều refresh token (multi-device) |
| `cameras` → `detections` | 1:N | Camera tạo ra nhiều detection records |
| `cameras` → `violations` | 1:N | Camera ghi nhận nhiều vi phạm |
| `cameras` → `traffic_stats` | 1:N | Camera có thống kê theo từng giờ |
| `detections` → `violations` | 1:0..1 | Một detection có thể dẫn đến một vi phạm |

---

## 2. Database Schema (SQL DDL)

### 2.1 Extensions Required

```sql
-- Bật extension tạo UUID (PostgreSQL 13+ có sẵn gen_random_uuid)
-- Nếu dùng PostgreSQL < 13:
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search (built-in, không cần extension)
```

### 2.2 Bảng `operators` — Nhân viên vận hành

```sql
CREATE TABLE operators (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username        VARCHAR(50)  NOT NULL,
    email           VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    role            VARCHAR(20)  NOT NULL DEFAULT 'operator',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ,

    CONSTRAINT uq_operators_username UNIQUE (username),
    CONSTRAINT uq_operators_email    UNIQUE (email),
    CONSTRAINT ck_operators_role     CHECK (role IN ('admin', 'operator'))
);

CREATE INDEX idx_operators_username ON operators(username);
CREATE INDEX idx_operators_active   ON operators(is_active) WHERE is_active = TRUE;
```

### 2.3 Bảng `cameras` — Camera giao thông

```sql
CREATE TABLE cameras (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    rtsp_url      TEXT         NOT NULL,
    latitude      DOUBLE PRECISION,
    longitude     DOUBLE PRECISION,
    address       TEXT,
    intersection  VARCHAR(255),
    direction     VARCHAR(50),
    status        VARCHAR(20)  NOT NULL DEFAULT 'active',
    config        JSONB        DEFAULT '{}',
    vehicle_types TEXT[]       DEFAULT '{}',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ,

    CONSTRAINT ck_cameras_status    CHECK (status IN ('active', 'inactive', 'maintenance')),
    CONSTRAINT ck_cameras_direction CHECK (direction IS NULL OR direction IN ('north', 'south', 'east', 'west', 'northeast', 'northwest', 'southeast', 'southwest'))
);

CREATE INDEX idx_cameras_status   ON cameras(status) WHERE status = 'active';
CREATE INDEX idx_cameras_location ON cameras(latitude, longitude);
```

### 2.4 Bảng `detections` — Kết quả nhận diện YOLO

```sql
CREATE TABLE detections (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id     UUID         NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    frame_id      BIGINT       NOT NULL,
    vehicle_type  VARCHAR(50)  NOT NULL,
    confidence    FLOAT        NOT NULL,
    bbox          JSONB        NOT NULL,
    metadata      JSONB        DEFAULT '{}',
    detected_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_detections_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT ck_detections_vehicle    CHECK (vehicle_type IN ('car', 'truck', 'bus', 'motorcycle', 'bicycle'))
);

CREATE INDEX idx_detections_camera   ON detections(camera_id, detected_at DESC);
CREATE INDEX idx_detections_type     ON detections(vehicle_type, detected_at DESC);
CREATE INDEX idx_detections_metadata ON detections USING GIN(metadata);
CREATE INDEX idx_detections_time     ON detections(detected_at DESC);
```

### 2.5 Bảng `violations` — Vi phạm giao thông

```sql
CREATE TABLE violations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_id    UUID         REFERENCES detections(id) ON DELETE SET NULL,
    camera_id       UUID         NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    violation_type  VARCHAR(50)  NOT NULL,
    vehicle_type    VARCHAR(50)  NOT NULL,
    license_plate   VARCHAR(20),
    confidence      FLOAT        NOT NULL,
    evidence_url    TEXT,
    metadata        JSONB        DEFAULT '{}',
    is_confirmed    BOOLEAN      NOT NULL DEFAULT FALSE,
    confirmed_by    UUID         REFERENCES operators(id) ON DELETE SET NULL,
    notes           TEXT,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_violations_type       CHECK (violation_type IN ('red_light', 'speeding', 'wrong_lane', 'no_helmet')),
    CONSTRAINT ck_violations_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)
);

CREATE INDEX idx_violations_camera      ON violations(camera_id, created_at DESC);
CREATE INDEX idx_violations_type        ON violations(violation_type, created_at DESC);
CREATE INDEX idx_violations_plate       ON violations(license_plate) WHERE license_plate IS NOT NULL;
CREATE INDEX idx_violations_unconfirmed ON violations(is_confirmed) WHERE is_confirmed = FALSE;

-- Full-text search cho biển số + ghi chú
CREATE INDEX idx_violations_search ON violations
    USING GIN(to_tsvector('simple', COALESCE(license_plate, '') || ' ' || COALESCE(notes, '')));
```

### 2.6 Bảng `traffic_stats` — Thống kê lưu lượng

```sql
CREATE TABLE traffic_stats (
    camera_id        UUID         NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    hour             TIMESTAMPTZ  NOT NULL,
    total_vehicles   INTEGER      DEFAULT 0,
    car_count        INTEGER      DEFAULT 0,
    truck_count      INTEGER      DEFAULT 0,
    bus_count        INTEGER      DEFAULT 0,
    motorcycle_count INTEGER      DEFAULT 0,
    bicycle_count    INTEGER      DEFAULT 0,
    violation_count  INTEGER      DEFAULT 0,
    avg_speed        FLOAT,

    PRIMARY KEY (camera_id, hour)
);

CREATE INDEX idx_traffic_stats_hour ON traffic_stats(hour DESC);
```

### 2.7 Bảng `refresh_tokens` — JWT Refresh Tokens

```sql
CREATE TABLE refresh_tokens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operator_id UUID         NOT NULL REFERENCES operators(id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) NOT NULL,
    expires_at  TIMESTAMPTZ  NOT NULL,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_refresh_tokens_hash UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_tokens_operator ON refresh_tokens(operator_id);
CREATE INDEX idx_refresh_tokens_expires  ON refresh_tokens(expires_at);
```

---

## 3. Data Dictionary

### 3.1 Bảng `operators` — Nhân viên vận hành hệ thống

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `id` | `UUID` | NO | `gen_random_uuid()` | Khóa chính, UUID tự sinh |
| 2 | `username` | `VARCHAR(50)` | NO | — | Tên đăng nhập, duy nhất toàn hệ thống |
| 3 | `email` | `VARCHAR(255)` | NO | — | Email, duy nhất toàn hệ thống |
| 4 | `hashed_password` | `VARCHAR(255)` | NO | — | Mật khẩu đã mã hóa bcrypt (cost=12) |
| 5 | `full_name` | `VARCHAR(255)` | YES | `NULL` | Họ tên đầy đủ (hiển thị trên dashboard) |
| 6 | `role` | `VARCHAR(20)` | NO | `'operator'` | Vai trò: `admin` (toàn quyền) hoặc `operator` (xem + xác nhận) |
| 7 | `is_active` | `BOOLEAN` | NO | `TRUE` | Trạng thái tài khoản. `FALSE` = bị vô hiệu hóa |
| 8 | `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | Thời điểm tạo tài khoản (UTC) |
| 9 | `updated_at` | `TIMESTAMPTZ` | YES | `NULL` | Thời điểm cập nhật gần nhất |

**Constraints:**
- `PK`: `id`
- `UNIQUE`: `username`, `email`
- `CHECK`: `role IN ('admin', 'operator')`

---

### 3.2 Bảng `cameras` — Camera giám sát giao thông

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `id` | `UUID` | NO | `gen_random_uuid()` | Khóa chính |
| 2 | `name` | `VARCHAR(255)` | NO | — | Tên camera (VD: "Camera Ngã Tư Bà Huyện") |
| 3 | `rtsp_url` | `TEXT` | NO | — | URL RTSP stream (VD: `rtsp://192.168.1.100:554/stream`) |
| 4 | `latitude` | `DOUBLE PRECISION` | YES | `NULL` | Vĩ độ GPS (VD: 10.762622) |
| 5 | `longitude` | `DOUBLE PRECISION` | YES | `NULL` | Kinh độ GPS (VD: 106.660172) |
| 6 | `address` | `TEXT` | YES | `NULL` | Địa chỉ đặt camera |
| 7 | `intersection` | `VARCHAR(255)` | YES | `NULL` | Tên giao lộ (VD: "Ngã Tư Hàng Xanh") |
| 8 | `direction` | `VARCHAR(50)` | YES | `NULL` | Hướng camera: `north`, `south`, `east`, `west`, `northeast`, `northwest`, `southeast`, `southwest` |
| 9 | `status` | `VARCHAR(20)` | NO | `'active'` | Trạng thái: `active` (hoạt động), `inactive` (tắt), `maintenance` (bảo trì) |
| 10 | `config` | `JSONB` | YES | `'{}'` | Cấu hình riêng: `{"frame_skip": 5, "confidence_threshold": 0.5, "speed_limit": 60}` |
| 11 | `vehicle_types` | `TEXT[]` | YES | `'{}'` | Loại xe thường gặp tại vị trí camera |
| 12 | `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | Thời điểm thêm camera vào hệ thống |
| 13 | `updated_at` | `TIMESTAMPTZ` | YES | `NULL` | Thời điểm cập nhật gần nhất |

**Constraints:**
- `PK`: `id`
- `CHECK`: `status IN ('active', 'inactive', 'maintenance')`
- `CHECK`: `direction IN (NULL, 'north', 'south', 'east', 'west', ...)`

---

### 3.3 Bảng `detections` — Kết quả nhận diện YOLO

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `id` | `UUID` | NO | `gen_random_uuid()` | Khóa chính |
| 2 | `camera_id` | `UUID` | NO | — | FK → `cameras.id`. Camera nào phát hiện |
| 3 | `frame_id` | `BIGINT` | NO | — | Số thứ tự frame trong video stream |
| 4 | `vehicle_type` | `VARCHAR(50)` | NO | — | Loại phương tiện: `car`, `truck`, `bus`, `motorcycle`, `bicycle` |
| 5 | `confidence` | `FLOAT` | NO | — | Độ tin cậy YOLO (0.0 → 1.0) |
| 6 | `bbox` | `JSONB` | NO | — | Bounding box: `{"x1": 100, "y1": 200, "x2": 300, "y2": 400}` |
| 7 | `metadata` | `JSONB` | YES | `'{}'` | Dữ liệu bổ sung: `{"track_id": 42, "speed_kmh": 65, "license_plate": "59A-123.45", "color": "red"}` |
| 8 | `detected_at` | `TIMESTAMPTZ` | NO | `NOW()` | Thời điểm phát hiện (UTC) |

**Constraints:**
- `PK`: `id`
- `FK`: `camera_id` → `cameras(id)` ON DELETE CASCADE
- `CHECK`: `confidence BETWEEN 0.0 AND 1.0`
- `CHECK`: `vehicle_type IN ('car', 'truck', 'bus', 'motorcycle', 'bicycle')`

**Lưu ý hiệu năng:** Bảng này sẽ có hàng triệu records/ngày. Cần:
- Partial indexes trên `detected_at DESC`
- GIN index trên `metadata` cho truy vấn JSONB
- Partition by range (`detected_at`) khi data lớn (Phase 2)

---

### 3.4 Bảng `violations` — Vi phạm giao thông

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `id` | `UUID` | NO | `gen_random_uuid()` | Khóa chính |
| 2 | `detection_id` | `UUID` | YES | `NULL` | FK → `detections.id`. Detection nào dẫn đến vi phạm |
| 3 | `camera_id` | `UUID` | NO | — | FK → `cameras.id`. Camera ghi nhận vi phạm |
| 4 | `violation_type` | `VARCHAR(50)` | NO | — | Loại vi phạm: `red_light` (vượt đèn đỏ), `speeding` (quá tốc độ), `wrong_lane` (sai làn), `no_helmet` (không mũ bảo hiểm) |
| 5 | `vehicle_type` | `VARCHAR(50)` | NO | — | Loại xe vi phạm |
| 6 | `license_plate` | `VARCHAR(20)` | YES | `NULL` | Biển số xe (nếu nhận diện được). VD: `"59A-123.45"` |
| 7 | `confidence` | `FLOAT` | NO | — | Độ tin cậy phát hiện vi phạm (0.0 → 1.0) |
| 8 | `evidence_url` | `TEXT` | YES | `NULL` | URL ảnh bằng chứng: `/evidence/2026-06-19/cam_001/vio_abc123.jpg` |
| 9 | `metadata` | `JSONB` | YES | `'{}'` | Chi tiết: `{"speed_kmh": 85, "speed_limit": 60, "signal_state": "red", "lane_info": "lane_3"}` |
| 10 | `is_confirmed` | `BOOLEAN` | NO | `FALSE` | Đã được operator xác nhận hay chưa |
| 11 | `confirmed_by` | `UUID` | YES | `NULL` | FK → `operators.id`. Operator nào xác nhận |
| 12 | `notes` | `TEXT` | YES | `NULL` | Ghi chú của operator khi xác nhận |
| 13 | `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | Thời điểm ghi nhận vi phạm |

**Constraints:**
- `PK`: `id`
- `FK`: `detection_id` → `detections(id)` ON DELETE SET NULL
- `FK`: `camera_id` → `cameras(id)` ON DELETE CASCADE
- `FK`: `confirmed_by` → `operators(id)` ON DELETE SET NULL
- `CHECK`: `violation_type IN ('red_light', 'speeding', 'wrong_lane', 'no_helmet')`
- `CHECK`: `confidence BETWEEN 0.0 AND 1.0`

---

### 3.5 Bảng `traffic_stats` — Thống kê lưu lượng giao thông

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `camera_id` | `UUID` | NO | — | FK + PK → `cameras.id` |
| 2 | `hour` | `TIMESTAMPTZ` | NO | — | Mốc thời gian đầu giờ (VD: `2026-06-19T14:00:00Z`) |
| 3 | `total_vehicles` | `INTEGER` | YES | `0` | Tổng số phương tiện phát hiện trong giờ |
| 4 | `car_count` | `INTEGER` | YES | `0` | Số lượng ô tô con |
| 5 | `truck_count` | `INTEGER` | YES | `0` | Số lượng xe tải |
| 6 | `bus_count` | `INTEGER` | YES | `0` | Số lượng xe buýt |
| 7 | `motorcycle_count` | `INTEGER` | YES | `0` | Số lượng xe máy |
| 8 | `bicycle_count` | `INTEGER` | YES | `0` | Số lượng xe đạp |
| 9 | `violation_count` | `INTEGER` | YES | `0` | Số lượng vi phạm trong giờ |
| 10 | `avg_speed` | `FLOAT` | YES | `NULL` | Tốc độ trung bình (km/h) |

**Constraints:**
- `PK`: (`camera_id`, `hour`) — Composite primary key
- `FK`: `camera_id` → `cameras(id)` ON DELETE CASCADE

**Lưu ý:** Dữ liệu này được tổng hợp từ bảng `detections` bởi Task Scheduler (cron mỗi 5 phút) hoặc trigger.

---

### 3.6 Bảng `refresh_tokens` — JWT Refresh Tokens

| # | Tên Cột | Kiểu Dữ Liệu | Nullable | Default | Mô Tả |
|---|---------|--------------|----------|---------|--------|
| 1 | `id` | `UUID` | NO | `gen_random_uuid()` | Khóa chính |
| 2 | `operator_id` | `UUID` | NO | — | FK → `operators.id`. Token thuộc operator nào |
| 3 | `token_hash` | `VARCHAR(255)` | NO | — | Hash SHA-256 của refresh token (không lưu token gốc) |
| 4 | `expires_at` | `TIMESTAMPTZ` | NO | — | Thời điểm hết hạn token |
| 5 | `created_at` | `TIMESTAMPTZ` | NO | `NOW()` | Thời điểm tạo token |

**Constraints:**
- `PK`: `id`
- `FK`: `operator_id` → `operators(id)` ON DELETE CASCADE
- `UNIQUE`: `token_hash`

---

## 4. Index Strategy

### 4.1 Tổng Hợp Indexes

| Bảng | Index | Loại | Mục Đích |
|------|-------|------|----------|
| `operators` | `idx_operators_username` | B-tree | Tìm kiếm nhanh khi login |
| `operators` | `idx_operators_active` | Partial B-tree | Lọc operator đang hoạt động |
| `cameras` | `idx_cameras_status` | Partial B-tree | Lọc camera đang active |
| `cameras` | `idx_cameras_location` | B-tree (composite) | Truy vấn theo vị trí GPS |
| `detections` | `idx_detections_camera` | B-tree (composite) | Truy vấn detection theo camera + thời gian |
| `detections` | `idx_detections_type` | B-tree (composite) | Lọc theo loại xe + thời gian |
| `detections` | `idx_detections_metadata` | GIN | Truy vấn JSONB (biển số, tốc độ, ...) |
| `detections` | `idx_detections_time` | B-tree | Sắp xếp theo thời gian mới nhất |
| `violations` | `idx_violations_camera` | B-tree (composite) | Vi phạm theo camera + thời gian |
| `violations` | `idx_violations_type` | B-tree (composite) | Lọc theo loại vi phạm |
| `violations` | `idx_violations_plate` | Partial B-tree | Tìm kiếm theo biển số |
| `violations` | `idx_violations_unconfirmed` | Partial B-tree | Lọc vi phạm chưa xác nhận |
| `violations` | `idx_violations_search` | GIN (tsvector) | Full-text search biển số + ghi chú |
| `traffic_stats` | `idx_traffic_stats_hour` | B-tree | Sắp xếp theo thời gian |
| `refresh_tokens` | `idx_refresh_tokens_operator` | B-tree | Tìm token theo operator |
| `refresh_tokens` | `idx_refresh_tokens_expires` | B-tree | Cleanup token hết hạn |

### 4.2 Giải Thích Chiến Lược Index

**Partial Indexes** (WHERE condition):
- Giảm kích thước index bằng cách chỉ index rows thỏa điều kiện
- VD: `idx_cameras_status WHERE status = 'active'` — chỉ index camera đang hoạt động
- VD: `idx_violations_unconfirmed WHERE is_confirmed = FALSE` — chỉ index vi phạm chưa xác nhận

**GIN Indexes** (Generalized Inverted Index):
- Tối ưu cho JSONB và full-text search
- `idx_detections_metadata` — truy vấn `metadata @> '{"license_plate": "59A-123.45"}'`
- `idx_violations_search` — truy vấn `to_tsvector('simple', ...) @@ to_tsquery('simple', '59A')`

**Composite Indexes**:
- Phục vụ query pattern phổ biến: "lấy detections của camera X, sắp xếp theo thời gian mới nhất"
- Thứ tự cột: equality column trước, range/sort column sau

---

## 5. Quan Hệ Giữa Các Bảng

### 5.1 Sơ Đồ Tóm Tắt Quan Hệ

```
                    ┌──────────────┐
                    │  operators   │
                    │  (Nhân viên) │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              │ 1:N        │ 1:N        │
              ▼            │            │
    ┌──────────────┐       │            │
    │refresh_tokens│       │            │
    │  (JWT Token) │       │            │
    └──────────────┘       │            │
                           │            │
                    ┌──────┴───────┐    │
                    │   cameras    │    │
                    │  (Camera IP) │    │
                    └──────┬───────┘    │
                           │            │
              ┌────────────┼────────────┤
              │            │            │
              │ 1:N        │ 1:N        │ confirmed_by
              ▼            ▼            ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ detections   │ │traffic_stats │ │ violations   │
    │ (YOLO Result)│ │ (Thống kê)   │ │ (Vi phạm)    │
    └──────┬───────┘ └──────────────┘ └──────────────┘
           │                                  ▲
           │ 1:0..1 (detection_id)            │
           └──────────────────────────────────┘
```

### 5.2 Cascading Rules

| Quan Hệ | ON DELETE | Lý Do |
|----------|-----------|-------|
| `cameras` → `detections` | CASCADE | Xóa camera → xóa tất cả detection |
| `cameras` → `violations` | CASCADE | Xóa camera → xóa tất cả vi phạm |
| `cameras` → `traffic_stats` | CASCADE | Xóa camera → xóa tất cả thống kê |
| `operators` → `refresh_tokens` | CASCADE | Xóa operator → xóa tất cả token |
| `detections` → `violations` | SET NULL | Xóa detection → giữ lại vi phạm, set detection_id = NULL |
| `operators` → `violations` | SET NULL | Xóa operator → giữ lại vi phạm, set confirmed_by = NULL |

---

### 5.3 Ước Tính Dung Lượng

---

## 6. Thiết kế cho ASP.NET Core 8 + SQL Server + EF Core

Tài liệu phía trên là bản thiết kế ban đầu cho PostgreSQL/SQLAlchemy. Dưới đây là cập nhật và chuyển đổi sang kiến trúc backend bằng ASP.NET Core 8 Web API sử dụng SQL Server và Entity Framework Core (EF Core) theo mô hình Clean Architecture (Controllers → Services → Repositories → DbContext → Models/Entities → DTOs).

### 6.1 Kiến trúc lớp (tóm tắt)
- Controllers: Nhận HTTP request, trả HTTP response, map DTO ↔ Entities qua Service.
- Services (Business layer): Logic nghiệp vụ, transaction orchestration, validation cao cấp.
- Repositories (Data access): Giao tiếp trực tiếp với `TrafficMonitoringDbContext`, phương thức async.
- DTOs: Request/Response models cho API (separate từ Entities).
- Models/Entities: Lớp EF Core mapping đến bảng SQL Server.
- DbContext: `TrafficMonitoringDbContext` chứa DbSet<TEntity> và cấu hình Fluent API.

### 6.2 Mapping chính giữa Entities và Bảng SQL Server
- `Operator` (table Operators) → `Operators` (table)
- `Camera` (table Cameras)
- `Detection` (table Detections)
- `Violation` (table Violations)
- `TrafficStat` (table TrafficStats)
- `RefreshToken` (table RefreshTokens)

Notes cho SQL Server & EF Core:
- UUID -> use `uniqueidentifier` with `NEWSEQUENTIALID()` or `NEWID()` depending performance/security.
- JSONB -> SQL Server `NVARCHAR(MAX)`; EF Core map các trường JSON thành `string` hoặc value object. Nếu cần query JSON, dùng SQL Server JSON functions (`JSON_VALUE`, `OPENJSON`).
- Arrays -> transform `vehicle_types` thành bảng phụ `CameraVehicleTypes` hoặc lưu JSON array trong `NVARCHAR(MAX)` nếu ít truy vấn.

### 6.3 Entities (ghi tắt, tên lớp C#)
- Operator { Guid Id; string Username; string Email; string PasswordHash; string FullName; string Role; bool IsActive; DateTimeOffset CreatedAt; DateTimeOffset? UpdatedAt }
- Camera { Guid Id; string Name; string RtspUrl; double? Latitude; double? Longitude; string Address; string Intersection; string Direction; string Status; string ConfigJson; string VehicleTypesJson; DateTimeOffset CreatedAt; DateTimeOffset? UpdatedAt }
- Detection { Guid Id; Guid CameraId; long FrameId; string VehicleType; float Confidence; string BboxJson; string MetadataJson; DateTimeOffset DetectedAt }
- Violation { Guid Id; Guid? DetectionId; Guid CameraId; string ViolationType; string VehicleType; string LicensePlate; float Confidence; string EvidenceUrl; string MetadataJson; bool IsConfirmed; Guid? ConfirmedBy; string Notes; DateTimeOffset CreatedAt }
- TrafficStat { Guid CameraId; DateTimeOffset Hour; int TotalVehicles; int CarCount; int TruckCount; int BusCount; int MotorcycleCount; int BicycleCount; int ViolationCount; float? AvgSpeed }
- RefreshToken { Guid Id; Guid OperatorId; string TokenHash; DateTimeOffset ExpiresAt; DateTimeOffset CreatedAt }

### 6.4 DbContext cơ bản (ghi tắt)
- class TrafficMonitoringDbContext : DbContext {
    public DbSet<Operator> Operators { get; set; }
    public DbSet<Camera> Cameras { get; set; }
    public DbSet<Detection> Detections { get; set; }
    public DbSet<Violation> Violations { get; set; }
    public DbSet<TrafficStat> TrafficStats { get; set; }
    public DbSet<RefreshToken> RefreshTokens { get; set; }
    protected override void OnModelCreating(ModelBuilder modelBuilder) { /* Fluent API: constraints, indexes, relations */ }
}

---

## 7. RESTful API Spec (Modules)

Nguyên tắc chung:
- Sử dụng chuẩn RESTful, trả JSON.
- Authentication: JWT (access token ngắn hạn, refresh token dài hạn). Endpoints bảo vệ bằng `[Authorize]`.
- Validation: FluentValidation hoặc DataAnnotations; trả 400 với mô tả lỗi.
- Pagination: `page`, `pageSize`. Filtering/Sorting qua query params.

Mỗi mục dưới đây liệt kê các endpoint chính.

**Module 1 — Authentication**
- `POST /api/v1/auth/login`
    - Method: POST
    - Chức năng: Đăng nhập, trả access token + refresh token
    - Request: `LoginRequest { string UsernameOrEmail; string Password }`
    - Response: `AuthResponse { string AccessToken; string RefreshToken; DateTimeOffset ExpiresAt; UserDto User }`
    - HTTP Status: 200, 400, 401
    - Validation: username/email required, password required
    - Entity: `Operator`, `RefreshToken`

- `POST /api/v1/auth/refresh`
    - Method: POST
    - Chức năng: Trao mới access token từ refresh token
    - Request: `RefreshRequest { string RefreshToken }`
    - Response: `AuthResponse`
    - Status: 200, 400, 401
    - Validation: token tồn tại, chưa hết hạn
    - Entity: `RefreshToken`, `Operator`

- `POST /api/v1/auth/logout`
    - Method: POST
    - Chức năng: Revoke refresh token
    - Request: `RevokeRequest { string RefreshToken }`
    - Response: 204 No Content
    - Status: 204, 400
    - Entity: `RefreshToken`

**Module 2 — User Management**
- `GET /api/v1/users` (Admin)
    - Method: GET
    - Chức năng: Lấy danh sách users (paging/filter)
    - Request: `page,pageSize,role,isActive`
    - Response: `PagedResult<UserDto>`
    - Status: 200, 403
    - Entity: `Operator`

- `GET /api/v1/users/{id}`
    - Method: GET
    - Chức năng: Lấy chi tiết user
    - Response: `UserDto`
    - Status: 200, 404
    - Entity: `Operator`

- `POST /api/v1/users` (Admin)
    - Method: POST
    - Chức năng: Tạo tài khoản mới
    - Request: `CreateUserRequest { Username, Email, Password, Role, FullName }`
    - Response: 201 Created + `UserDto`
    - Validation: unique username/email, password policy
    - Entity: `Operator`

- `PUT /api/v1/users/{id}`
    - Method: PUT
    - Chức năng: Cập nhật user
    - Request: `UpdateUserRequest`
    - Response: `UserDto`
    - Status: 200, 400, 404
    - Entity: `Operator`

- `POST /api/v1/users/{id}/change-password`
    - Method: POST
    - Chức năng: Đổi mật khẩu (self or admin reset)
    - Request: `ChangePasswordRequest { CurrentPassword?, NewPassword }`
    - Response: 204
    - Status: 204, 400, 403

**Module 3 — Camera Management**
- `GET /api/v1/cameras`
    - Method: GET
    - Chức năng: Lấy danh sách camera
    - Request: `page,pageSize,status,intersection`
    - Response: `PagedResult<CameraDto>`
    - Status: 200
    - Entity: `Camera`

- `GET /api/v1/cameras/{id}`
    - Method: GET
    - Chức năng: Lấy chi tiết camera
    - Response: `CameraDto`
    - Status: 200, 404

- `POST /api/v1/cameras`
    - Method: POST
    - Chức năng: Thêm camera
    - Request: `CreateCameraRequest { Name, RtspUrl, Latitude?, Longitude?, Address?, Intersection?, Direction?, Status?, Config?, VehicleTypes[] }`
    - Response: 201 + `CameraDto`
    - Validation: RtspUrl required
    - Entity: `Camera`

- `PUT /api/v1/cameras/{id}`
    - Method: PUT
    - Chức năng: Cập nhật camera
    - Response: `CameraDto`
    - Status: 200, 400, 404

- `DELETE /api/v1/cameras/{id}`
    - Method: DELETE
    - Chức năng: Xóa camera (xử lý cascade)
    - Response: 204
    - Status: 204, 404, 409

**Module 4 — Dashboard**
- `GET /api/v1/dashboard/overview`
    - Method: GET
    - Chức năng: Trả số liệu tổng quan
    - Request: optional `dateFrom`, `dateTo`
    - Response: `DashboardOverviewDto`
    - Status: 200
    - Entity: `Camera`, `Violation`, `TrafficStat`, `Detection`

- `GET /api/v1/dashboard/camera/{cameraId}/live-metrics`
    - Method: GET
    - Chức năng: Trả live metrics camera
    - Response: `CameraLiveDto`

**Module 5 — Detection History**
- `GET /api/v1/detections`
    - Method: GET
    - Chức năng: Lấy lịch sử detection (filter)
    - Request: `cameraId,vehicleType,from,to,minConfidence,page,pageSize`
    - Response: `PagedResult<DetectionDto>`
    - Status: 200
    - Validation: date range limits

- `GET /api/v1/detections/{id}`
    - Method: GET
    - Chức năng: Chi tiết detection
    - Response: `DetectionDto`
    - Status: 200, 404

**Module 6 — Statistics**
- `GET /api/v1/stats/traffic`
    - Method: GET
    - Chức năng: Thống kê lưu lượng theo khoảng thời gian
    - Request: `cameraId?,from,to,granularity=hour|day,vehicleType?`
    - Response: `TimeSeriesStatDto[]`
    - Status: 200
    - Entity: `TrafficStat`, `Detection`

- `GET /api/v1/stats/violations`
    - Method: GET
    - Chức năng: Thống kê vi phạm theo loại/camera/time
    - Response: `ViolationStatDto[]`

**Module 7 — Settings**
- `GET /api/v1/settings`
    - Method: GET
    - Chức năng: Lấy cấu hình hệ thống
    - Response: `SettingsDto`
    - Entity: `AppSettings` (table) hoặc storage khác

- `PUT /api/v1/settings`
    - Method: PUT
    - Chức năng: Cập nhật cấu hình (Admin only)
    - Request: `UpdateSettingsRequest`
    - Response: `SettingsDto`
    - Status: 200, 400, 403

---

## 8. Validation, Status Codes, Error Model
- Chuẩn trả lỗi: `{ "errors": [{ "field": "username", "message": "Required" }], "traceId": "..." }`
- 200 OK: thành công trả dữ liệu
- 201 Created: resource mới (kèm header `Location`)
- 204 No Content: hành động thành công không trả body
- 400 Bad Request: validation lỗi
- 401 Unauthorized: JWT invalid/expired
- 403 Forbidden: role-based access denied
- 404 Not Found: resource không tồn tại
- 409 Conflict: xung đột (ví dụ: delete khi tồn tại FK not allowed)
- 500 Internal Server Error: unexpected

---

## 9. Ghi chú triển khai & performance
- Bảng `Detections` rất lớn — dùng partitioning (by range on DetectedAt) hoặc sharding giải pháp lưu trữ.
- Retention policy: archive / delete cũ (>90 days) cho detections raw; lưu aggregated stats lâu hơn.
- Indexes: nonclustered index on (CameraId, DetectedAt DESC), filtered indexes cho boolean flags.
- Mapping JSON: nếu cần filter nhanh trên metadata, tách trường phổ biến (speed, license_plate) thành cột riêng.

## 10. Kết luận
Tài liệu trên cập nhật thiết kế database ban đầu (PostgreSQL) sang định hướng triển khai bằng SQL Server và EF Core, đồng thời bổ sung API spec cho 7 module theo chuẩn RESTful, SOLID và Clean Architecture. Nếu muốn, tôi sẽ:
- Tạo skeleton project ASP.NET Core 8 với folder structure Controllers/Services/Repositories/DTOs/Models/Infrastructure và một `TrafficMonitoringDbContext` sẵn sàng migration.
- Sinh class Entities + DTOs và Fluent API mapping.

Bạn muốn tôi tiếp tục tạo skeleton code và migrations không?

| Bảng | Records/Ngày | Records/Tháng | Kích Thước Ước Tính |
|------|-------------|--------------|-------------------|
| `operators` | — | ~10-50 | < 1 MB |
| `cameras` | — | ~10-50 | < 1 MB |
| `detections` | ~500K-2M | ~15M-60M | 5-20 GB/tháng |
| `violations` | ~100-1000 | ~3K-30K | < 100 MB/tháng |
| `traffic_stats` | ~240-1200 | ~7K-36K | < 50 MB/tháng |
| `refresh_tokens` | ~10-100 | cleanup | < 1 MB |

> **Lưu ý:** Bảng `detections` sẽ cần partitioning (PARTITION BY RANGE) khi data vượt 100M records (~2-3 tháng vận hành).

---

---

## 6. Triển Khai Backend Cơ Bản

Phần này mô tả các bước triển khai backend nền tảng cho hệ thống, từ thiết kế API đến cấu trúc dự án, kết nối cơ sở dữ liệu và tài liệu Swagger.

### 6.1 Thiết Kế API Specification

API của hệ thống được thiết kế theo phong cách RESTful, chia theo từng nhóm chức năng để dễ mở rộng và bảo trì. Mỗi nhóm API sử dụng các HTTP method phù hợp như `GET`, `POST`, `PUT`, `DELETE` và trả về dữ liệu theo định dạng JSON.

Các nhóm API chính bao gồm:

| Nhóm API | Mục Đích |
|----------|----------|
| `auth` | Đăng nhập, đăng xuất, làm mới token |
| `cameras` | Quản lý camera giám sát |
| `detections` | Lưu trữ và truy vấn kết quả nhận diện YOLO |
| `violations` | Quản lý và xác nhận vi phạm giao thông |
| `stats` | Thống kê lưu lượng và dữ liệu dashboard |

Khi thiết kế API, hệ thống tuân theo các nguyên tắc sau:

- URL rõ ràng, dễ hiểu, ví dụ: `/api/v1/cameras`, `/api/v1/detections`.
- Dữ liệu đầu vào và đầu ra được chuẩn hóa bằng Pydantic schema.
- Mỗi API đều có mã trạng thái HTTP phù hợp như `200`, `201`, `400`, `404`, `422`, `500`.
- Các endpoint được nhóm theo router để dễ quản lý theo module.

### 6.2 Tạo FastAPI Project Structure

Dự án được tổ chức theo mô hình phân lớp để tách biệt rõ ràng giữa phần khởi tạo ứng dụng, định tuyến API, logic xử lý, schema dữ liệu và mô hình database. Cấu trúc này giúp dự án dễ phát triển trong giai đoạn sau.

| Thư Mục / File | Vai Trò |
|----------------|---------|
| `app/main.py` | Khởi tạo FastAPI application và đăng ký router |
| `app/api/` | Chứa các router tổng |
| `app/api/endpoints/` | Chứa các endpoint theo từng chức năng |
| `app/core/` | Cấu hình, kết nối database, các tiện ích lõi |
| `app/models/` | Định nghĩa các bảng bằng SQLAlchemy |
| `app/schemas/` | Định nghĩa schema request/response bằng Pydantic |

Kiến trúc này giúp:

- Tách biệt logic rõ ràng giữa API, model và schema.
- Dễ mở rộng thêm module mới mà không ảnh hưởng đến phần còn lại của hệ thống.
- Dễ kiểm thử, bảo trì và tái sử dụng mã nguồn.

### 6.3 Kết Nối PostgreSQL

Hệ thống sử dụng PostgreSQL 16 làm cơ sở dữ liệu chính để lưu trữ dữ liệu camera, detection, violation, thống kê và token xác thực. SQLAlchemy được dùng như ORM để làm việc với database theo hướng object-oriented, giúp code dễ đọc và dễ bảo trì hơn.

Quy trình kết nối database được thực hiện như sau:

1. Khai báo biến môi trường `DATABASE_URL` trong file `.env`.
2. Tạo database engine từ chuỗi kết nối.
3. Tạo `SessionLocal` để quản lý phiên làm việc với database.
4. Cung cấp dependency `get_db()` cho các endpoint cần truy cập dữ liệu.

Việc sử dụng PostgreSQL phù hợp với hệ thống vì database này hỗ trợ tốt các kiểu dữ liệu như `JSONB`, `ARRAY`, index nâng cao và ràng buộc khóa ngoại, rất phù hợp với bài toán giám sát giao thông có dữ liệu quan hệ rõ ràng.

### 6.4 Tạo Swagger Cơ Bản

FastAPI hỗ trợ tự động sinh tài liệu API dựa trên router, kiểu dữ liệu Pydantic và phần khai báo endpoint. Nhờ đó, hệ thống có thể cung cấp giao diện Swagger UI để kiểm tra API trực tiếp mà không cần công cụ bên ngoài.

Hai giao diện tài liệu mặc định của FastAPI gồm:

- Swagger UI: `/docs`
- ReDoc: `/redoc`

Swagger được sử dụng để:

- Kiểm tra nhanh request và response của từng API.
- Xem danh sách endpoint theo từng nhóm chức năng.
- Tăng tính minh bạch và hỗ trợ quá trình phát triển, kiểm thử backend.

Từ cấu trúc dự án hiện tại, chỉ cần khai báo router và schema đúng chuẩn là FastAPI sẽ tự động sinh tài liệu API cơ bản cho toàn bộ hệ thống.

*Thiết kế cơ sở dữ liệu v1 | Hệ thống Giám sát Giao thông Thông minh | 19/06/2026*
