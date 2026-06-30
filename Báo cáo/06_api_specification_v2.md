# API Specification v2
# Hệ Thống Giám Sát Giao Thông Thông Minh Sử Dụng YOLOv26

> **Đồ Án Tốt Nghiệp** | API Specification v2
> Ngày tạo: 29/06/2026
> Backend: ASP.NET Core 8 Web API
> Database: SQL Server
> AI Detection: YOLOv26 (Python)

---

## MỤC LỤC

1. [Tổng Quan Kiến Trúc](#1-tổng-quan-kiến-trúc)
2. [Database Schema](#2-database-schema)
3. [Entity Models & EF Core Mapping](#3-entity-models--ef-core-mapping)
4. [DTOs (Data Transfer Objects)](#4-dtos-data-transfer-objects)
5. [RESTful API Specification](#5-restful-api-specification)
6. [Controllers & Services](#6-controllers--services)
7. [Repositories](#7-repositories)
8. [Error Handling & Validation](#8-error-handling--validation)

---

## 1. Tổng Quan Kiến Trúc

### 1.1 Kiến Trúc Hệ Thống

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  ReactJS    │         │ ASP.NET Core│         │  YOLOv26    │
│  Frontend   │◄───────►│   Backend   │◄───────►│   Python    │
│             │  JSON   │   Web API   │  JSON   │  Detection  │
└─────────────┘         └─────────────┘         └─────────────┘
                              │
                              │ EF Core
                              ▼
                        ┌─────────────┐
                        │ SQL Server  │
                        │  Database   │
                        └─────────────┘
```

### 1.2 Folder Structure

```
backend/aspnet/
├── Controllers/
│   ├── AuthController.cs
│   ├── CamerasController.cs
│   ├── UploadController.cs
│   ├── DetectionController.cs
│   ├── DetectionsController.cs
│   ├── DashboardController.cs
│   ├── StatisticsController.cs
│   └── SettingsController.cs
├── Services/
│   ├── IAuthService.cs
│   ├── AuthService.cs
│   ├── ICameraService.cs
│   ├── CameraService.cs
│   ├── IDetectionService.cs
│   ├── DetectionService.cs
│   ├── IUploadService.cs
│   ├── UploadService.cs
│   ├── IDashboardService.cs
│   ├── DashboardService.cs
│   ├── IStatisticsService.cs
│   └── StatisticsService.cs
├── Repositories/
│   ├── IRepository.cs
│   ├── Repository.cs
│   ├── ICameraRepository.cs
│   ├── CameraRepository.cs
│   ├── IDetectionRepository.cs
│   ├── DetectionRepository.cs
│   ├── IOperatorRepository.cs
│   └── OperatorRepository.cs
├── Models/
│   ├── Operator.cs
│   ├── Camera.cs
│   ├── Detection.cs
│   ├── DetectionResult.cs
│   ├── VehicleType.cs
│   └── SystemSettings.cs
├── DTOs/
│   ├── Auth/
│   │   ├── LoginRequest.cs
│   │   ├── AuthResponse.cs
│   │   └── UserProfileDto.cs
│   ├── Camera/
│   │   ├── CameraDto.cs
│   │   ├── CreateCameraRequest.cs
│   │   └── UpdateCameraRequest.cs
│   ├── Detection/
│   │   ├── DetectionDto.cs
│   │   ├── DetectionResultDto.cs
│   │   └── BoundingBoxDto.cs
│   ├── Upload/
│   │   ├── UploadRequest.cs
│   │   └── UploadResponse.cs
│   ├── Dashboard/
│   │   └── DashboardDto.cs
│   ├── Statistics/
│   │   ├── HourlyStatDto.cs
│   │   ├── DailyStatDto.cs
│   │   ├── MonthlyStatDto.cs
│   │   ├── VehicleTypeStatDto.cs
│   │   └── PieChartDto.cs
│   └── Settings/
│       ├── SettingsDto.cs
│       └── UpdateSettingsRequest.cs
├── Data/
│   └── TrafficMonitoringDbContext.cs
├── Program.cs
├── appsettings.json
└── TrafficMonitoring.csproj
```

---

## 2. Database Schema

### 2.1 SQL Server DDL

```sql
-- Bảng Operators (Nhân viên vận hành)
CREATE TABLE Operators (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
    Username NVARCHAR(50) NOT NULL UNIQUE,
    Email NVARCHAR(255) NOT NULL UNIQUE,
    PasswordHash NVARCHAR(255) NOT NULL,
    FullName NVARCHAR(255),
    Role NVARCHAR(20) NOT NULL DEFAULT 'operator', -- 'admin', 'operator'
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIMEOFFSET
);

-- Bảng Cameras (Camera giao thông)
CREATE TABLE Cameras (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
    CameraName NVARCHAR(255) NOT NULL,
    Location NVARCHAR(255),
    RtspUrl NVARCHAR(MAX) NOT NULL,
    Status NVARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'inactive', 'offline'
    Latitude FLOAT,
    Longitude FLOAT,
    IsOnline BIT NOT NULL DEFAULT 1,
    LastHeartbeat DATETIMEOFFSET,
    CreatedAt DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIMEOFFSET
);

-- Bảng Detections (Kết quả nhận diện)
CREATE TABLE Detections (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
    CameraId UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES Cameras(Id) ON DELETE CASCADE,
    VehicleType NVARCHAR(50) NOT NULL, -- 'car', 'motorcycle', 'bus', 'truck', 'bicycle'
    Confidence FLOAT NOT NULL,
    BboxJson NVARCHAR(MAX) NOT NULL, -- {"x1": int, "y1": int, "x2": int, "y2": int}
    ImageUrl NVARCHAR(MAX),
    MetadataJson NVARCHAR(MAX), -- thêm thông tin như speed, direction, ...
    DetectionTime DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE(),
    CreatedAt DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT FK_Detections_Cameras FOREIGN KEY (CameraId) REFERENCES Cameras(Id),
    CONSTRAINT CK_Detections_Confidence CHECK (Confidence >= 0 AND Confidence <= 1)
);

-- Bảng DetectionResults (Dữ liệu chi tiết từ YOLO)
CREATE TABLE DetectionResults (
    Id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
    DetectionId UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES Detections(Id) ON DELETE CASCADE,
    ClassId INT NOT NULL,
    ClassName NVARCHAR(50) NOT NULL,
    Confidence FLOAT NOT NULL,
    X1 INT NOT NULL,
    Y1 INT NOT NULL,
    X2 INT NOT NULL,
    Y2 INT NOT NULL,
    CreatedAt DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE()
);

-- Bảng VehicleTypes (Thống kê theo loại phương tiện)
CREATE TABLE VehicleTypes (
    Id INT PRIMARY KEY IDENTITY(1,1),
    TypeName NVARCHAR(50) NOT NULL UNIQUE, -- 'car', 'motorcycle', 'bus', 'truck'
    Label NVARCHAR(100),
    Description NVARCHAR(255)
);

-- Bảng SystemSettings (Cấu hình hệ thống)
CREATE TABLE SystemSettings (
    Id INT PRIMARY KEY IDENTITY(1,1),
    SettingKey NVARCHAR(100) NOT NULL UNIQUE,
    SettingValue NVARCHAR(MAX) NOT NULL,
    SettingType NVARCHAR(50), -- 'float', 'int', 'string', 'bool'
    UpdatedAt DATETIMEOFFSET NOT NULL DEFAULT GETUTCDATE()
);

-- Indexes
CREATE INDEX IDX_Detections_CameraId ON Detections(CameraId);
CREATE INDEX IDX_Detections_DetectionTime ON Detections(DetectionTime DESC);
CREATE INDEX IDX_Detections_VehicleType ON Detections(VehicleType);
CREATE INDEX IDX_Cameras_Status ON Cameras(Status);
CREATE INDEX IDX_DetectionResults_DetectionId ON DetectionResults(DetectionId);
```

---

## 3. Entity Models & EF Core Mapping

### 3.1 Operator Entity

```csharp
using System.ComponentModel.DataAnnotations;

namespace TrafficMonitoring.Models;

[Table("Operators")]
public class Operator
{
    [Key]
    public Guid Id { get; set; }

    [Required, MaxLength(50)]
    public string Username { get; set; } = null!;

    [Required, MaxLength(255)]
    public string Email { get; set; } = null!;

    [Required]
    public string PasswordHash { get; set; } = null!;

    public string? FullName { get; set; }

    [Required, MaxLength(20)]
    public string Role { get; set; } = "operator"; // 'admin', 'operator'

    public bool IsActive { get; set; } = true;

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset? UpdatedAt { get; set; }
}
```

### 3.2 Camera Entity

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TrafficMonitoring.Models;

[Table("Cameras")]
public class Camera
{
    [Key]
    public Guid Id { get; set; }

    [Required, MaxLength(255)]
    public string CameraName { get; set; } = null!;

    public string? Location { get; set; }

    [Required]
    public string RtspUrl { get; set; } = null!;

    [MaxLength(20)]
    public string Status { get; set; } = "active"; // 'active', 'inactive', 'offline'

    public double? Latitude { get; set; }
    public double? Longitude { get; set; }

    public bool IsOnline { get; set; } = true;

    public DateTimeOffset? LastHeartbeat { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset? UpdatedAt { get; set; }

    // Navigation
    [ForeignKey("CameraId")]
    public virtual ICollection<Detection> Detections { get; set; } = new List<Detection>();
}
```

### 3.3 Detection Entity

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TrafficMonitoring.Models;

[Table("Detections")]
public class Detection
{
    [Key]
    public Guid Id { get; set; }

    [ForeignKey("Camera")]
    public Guid CameraId { get; set; }

    [Required, MaxLength(50)]
    public string VehicleType { get; set; } = null!;

    [Range(0, 1)]
    public float Confidence { get; set; }

    public string? BboxJson { get; set; } // {"x1": 10, "y1": 20, "x2": 100, "y2": 150}

    public string? ImageUrl { get; set; }

    public string? MetadataJson { get; set; }

    public DateTimeOffset DetectionTime { get; set; } = DateTimeOffset.UtcNow;

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // Navigation
    public virtual Camera? Camera { get; set; }
    [ForeignKey("DetectionId")]
    public virtual ICollection<DetectionResult>? DetectionResults { get; set; } = new List<DetectionResult>();
}
```

### 3.4 DetectionResult Entity

```csharp
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace TrafficMonitoring.Models;

[Table("DetectionResults")]
public class DetectionResult
{
    [Key]
    public Guid Id { get; set; }

    [ForeignKey("Detection")]
    public Guid DetectionId { get; set; }

    public int ClassId { get; set; }

    [Required, MaxLength(50)]
    public string ClassName { get; set; } = null!;

    [Range(0, 1)]
    public float Confidence { get; set; }

    public int X1 { get; set; }
    public int Y1 { get; set; }
    public int X2 { get; set; }
    public int Y2 { get; set; }

    public DateTimeOffset CreatedAt { get; set; } = DateTimeOffset.UtcNow;

    // Navigation
    public virtual Detection? Detection { get; set; }
}
```

### 3.5 VehicleType & SystemSettings Entities

```csharp
using System.ComponentModel.DataAnnotations;

namespace TrafficMonitoring.Models;

[Table("VehicleTypes")]
public class VehicleType
{
    [Key]
    public int Id { get; set; }

    [Required, MaxLength(50)]
    public string TypeName { get; set; } = null!;

    public string? Label { get; set; }
    public string? Description { get; set; }
}

[Table("SystemSettings")]
public class SystemSettings
{
    [Key]
    public int Id { get; set; }

    [Required, MaxLength(100)]
    public string SettingKey { get; set; } = null!;

    [Required]
    public string SettingValue { get; set; } = null!;

    public string? SettingType { get; set; } // 'float', 'int', 'string', 'bool'

    public DateTimeOffset UpdatedAt { get; set; } = DateTimeOffset.UtcNow;
}
```

---

## 4. DTOs (Data Transfer Objects)

### 4.1 Authentication DTOs

```csharp
// LoginRequest.cs
public class LoginRequest
{
    public string Username { get; set; } = null!;
    public string Password { get; set; } = null!;
}

// AuthResponse.cs
public class AuthResponse
{
    public string AccessToken { get; set; } = null!;
    public string RefreshToken { get; set; } = null!;
    public UserProfileDto User { get; set; } = null!;
    public DateTimeOffset ExpiresAt { get; set; }
}

// UserProfileDto.cs
public class UserProfileDto
{
    public Guid Id { get; set; }
    public string Username { get; set; } = null!;
    public string Email { get; set; } = null!;
    public string? FullName { get; set; }
    public string Role { get; set; } = null!;
}
```

### 4.2 Camera DTOs

```csharp
// CameraDto.cs
public class CameraDto
{
    public Guid Id { get; set; }
    public string CameraName { get; set; } = null!;
    public string? Location { get; set; }
    public string RtspUrl { get; set; } = null!;
    public string Status { get; set; } = null!;
    public double? Latitude { get; set; }
    public double? Longitude { get; set; }
    public bool IsOnline { get; set; }
    public DateTimeOffset? LastHeartbeat { get; set; }
    public DateTimeOffset CreatedAt { get; set; }
}

// CreateCameraRequest.cs
public class CreateCameraRequest
{
    public string CameraName { get; set; } = null!;
    public string? Location { get; set; }
    public string RtspUrl { get; set; } = null!;
    public double? Latitude { get; set; }
    public double? Longitude { get; set; }
}

// UpdateCameraRequest.cs
public class UpdateCameraRequest
{
    public string? CameraName { get; set; }
    public string? Location { get; set; }
    public string? Status { get; set; }
    public double? Latitude { get; set; }
    public double? Longitude { get; set; }
}
```

### 4.3 Detection DTOs

```csharp
// DetectionDto.cs
public class DetectionDto
{
    public Guid Id { get; set; }
    public Guid CameraId { get; set; }
    public string VehicleType { get; set; } = null!;
    public float Confidence { get; set; }
    public BoundingBoxDto? BoundingBox { get; set; }
    public string? ImageUrl { get; set; }
    public DateTimeOffset DetectionTime { get; set; }
}

// BoundingBoxDto.cs
public class BoundingBoxDto
{
    public int X1 { get; set; }
    public int Y1 { get; set; }
    public int X2 { get; set; }
    public int Y2 { get; set; }
}

// DetectionResultDto.cs
public class DetectionResultDto
{
    public Guid Id { get; set; }
    public int ClassId { get; set; }
    public string ClassName { get; set; } = null!;
    public float Confidence { get; set; }
    public BoundingBoxDto BoundingBox { get; set; } = null!;
}
```

### 4.4 Upload DTOs

```csharp
// UploadRequest.cs
public class UploadRequest
{
    public IFormFile File { get; set; } = null!;
    public Guid? CameraId { get; set; }
}

// UploadResponse.cs
public class UploadResponse
{
    public bool Success { get; set; }
    public string? FileUrl { get; set; }
    public string? FileName { get; set; }
    public long FileSize { get; set; }
    public string Message { get; set; } = null!;
}
```

### 4.5 Dashboard & Statistics DTOs

```csharp
// DashboardDto.cs
public class DashboardDto
{
    public int TotalVehiclesDaily { get; set; }
    public int MotorcycleCount { get; set; }
    public int CarCount { get; set; }
    public int TruckCount { get; set; }
    public int BusCount { get; set; }
    public int OnlineCameras { get; set; }
    public int OfflineCameras { get; set; }
    public int TotalCameras { get; set; }
}

// HourlyStatDto.cs
public class HourlyStatDto
{
    public DateTime Hour { get; set; }
    public int TotalVehicles { get; set; }
    public Dictionary<string, int> VehiclesByType { get; set; } = new();
}

// VehicleTypeStatDto.cs
public class VehicleTypeStatDto
{
    public string VehicleType { get; set; } = null!;
    public int Count { get; set; }
    public float Percentage { get; set; }
}

// PieChartDto.cs
public class PieChartDto
{
    public string Name { get; set; } = null!;
    public int Value { get; set; }
}
```

### 4.6 Settings DTOs

```csharp
// SettingsDto.cs
public class SettingsDto
{
    public float ConfidenceThreshold { get; set; }
    public int DetectInterval { get; set; }
    public int Fps { get; set; }
}

// UpdateSettingsRequest.cs
public class UpdateSettingsRequest
{
    public float? ConfidenceThreshold { get; set; }
    public int? DetectInterval { get; set; }
    public int? Fps { get; set; }
}
```

---

## 5. RESTful API Specification

### 5.1 Authentication API

#### 5.1.1 Login

```
POST /api/login
```

**Request:**
```json
{
  "username": "admin",
  "password": "Password123!"
}
```

**Response (200 OK):**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "refreshToken": "refresh_token_value",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "email": "admin@example.com",
    "fullName": "Administrator",
    "role": "admin"
  },
  "expiresAt": "2026-06-29T15:30:00Z"
}
```

**Response (401 Unauthorized):**
```json
{
  "errors": [
    {
      "code": "INVALID_CREDENTIALS",
      "message": "Tên đăng nhập hoặc mật khẩu không đúng"
    }
  ]
}
```

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request (validation error)
- 401 Unauthorized
- 500 Internal Server Error

**Validation:**
- Username: required, max 50 chars
- Password: required, min 8 chars

---

#### 5.1.2 Logout

```
POST /api/logout
Authorization: Bearer {accessToken}
```

**Request:**
```json
{
  "refreshToken": "refresh_token_value"
}
```

**Response (204 No Content):**
```
(no body)
```

**HTTP Status Codes:**
- 204 No Content
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.1.3 Get Profile

```
GET /api/profile
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "email": "admin@example.com",
  "fullName": "Administrator",
  "role": "admin",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

**HTTP Status Codes:**
- 200 OK
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

### 5.2 Camera Management API

#### 5.2.1 Get All Cameras

```
GET /api/cameras?page=1&pageSize=10&status=active
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "cameraName": "Camera Gate 1",
      "location": "Ngã Tư Hàng Xanh",
      "rtspUrl": "rtsp://192.168.1.100:554/stream",
      "status": "active",
      "latitude": 10.762622,
      "longitude": 106.660172,
      "isOnline": true,
      "lastHeartbeat": "2026-06-29T14:30:00Z",
      "createdAt": "2026-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10
}
```

**Query Parameters:**
- `page`: int (default: 1)
- `pageSize`: int (default: 10)
- `status`: string (optional, 'active'|'inactive'|'offline')

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.2.2 Get Camera by ID

```
GET /api/cameras/{id}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cameraName": "Camera Gate 1",
  "location": "Ngã Tư Hàng Xanh",
  "rtspUrl": "rtsp://192.168.1.100:554/stream",
  "status": "active",
  "latitude": 10.762622,
  "longitude": 106.660172,
  "isOnline": true,
  "lastHeartbeat": "2026-06-29T14:30:00Z",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "errors": [
    {
      "code": "CAMERA_NOT_FOUND",
      "message": "Không tìm thấy camera"
    }
  ]
}
```

**HTTP Status Codes:**
- 200 OK
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

#### 5.2.3 Create Camera

```
POST /api/cameras
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "cameraName": "Camera Gate 2",
  "location": "Ngã Tư Bà Huyện",
  "rtspUrl": "rtsp://192.168.1.101:554/stream",
  "latitude": 10.776549,
  "longitude": 106.699788
}
```

**Response (201 Created):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "cameraName": "Camera Gate 2",
  "location": "Ngã Tư Bà Huyện",
  "rtspUrl": "rtsp://192.168.1.101:554/stream",
  "status": "active",
  "latitude": 10.776549,
  "longitude": 106.699788,
  "isOnline": false,
  "lastHeartbeat": null,
  "createdAt": "2026-06-29T14:30:00Z"
}
```

**Response (400 Bad Request):**
```json
{
  "errors": [
    {
      "field": "cameraName",
      "message": "Tên camera không được để trống"
    },
    {
      "field": "rtspUrl",
      "message": "URL RTSP không hợp lệ"
    }
  ]
}
```

**Validation:**
- cameraName: required, max 255 chars
- rtspUrl: required, valid URI format
- latitude: optional, range -90 to 90
- longitude: optional, range -180 to 180

**HTTP Status Codes:**
- 201 Created
- 400 Bad Request
- 401 Unauthorized
- 409 Conflict (duplicate name)
- 500 Internal Server Error

---

#### 5.2.4 Update Camera

```
PUT /api/cameras/{id}
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "cameraName": "Camera Gate 2 Updated",
  "location": "Ngã Tư Bà Huyện - Building A",
  "status": "inactive",
  "latitude": 10.776549,
  "longitude": 106.699788
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "cameraName": "Camera Gate 2 Updated",
  "location": "Ngã Tư Bà Huyện - Building A",
  "rtspUrl": "rtsp://192.168.1.101:554/stream",
  "status": "inactive",
  "latitude": 10.776549,
  "longitude": 106.699788,
  "isOnline": false,
  "lastHeartbeat": null,
  "createdAt": "2026-06-29T14:30:00Z"
}
```

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

#### 5.2.5 Delete Camera

```
DELETE /api/cameras/{id}
Authorization: Bearer {accessToken}
```

**Response (204 No Content):**
```
(no body)
```

**Response (404 Not Found):**
```json
{
  "errors": [
    {
      "code": "CAMERA_NOT_FOUND",
      "message": "Không tìm thấy camera"
    }
  ]
}
```

**HTTP Status Codes:**
- 204 No Content
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

### 5.3 Upload API

#### 5.3.1 Upload Image

```
POST /api/upload/image
Authorization: Bearer {accessToken}
Content-Type: multipart/form-data
```

**Request:**
```
Form Data:
  file: <binary image file (jpg, png, gif)>
  cameraId: "550e8400-e29b-41d4-a716-446655440000" (optional)
```

**Response (200 OK):**
```json
{
  "success": true,
  "fileUrl": "/uploads/images/image_20260629_143000.jpg",
  "fileName": "image_20260629_143000.jpg",
  "fileSize": 156432,
  "message": "Tải ảnh thành công"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Định dạng file không được hỗ trợ (chỉ jpg, png, gif)"
}
```

**Validation:**
- file: required, max 50MB
- formats: jpg, png, gif only
- cameraId: optional UUID

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 413 Payload Too Large
- 500 Internal Server Error

---

#### 5.3.2 Upload Video

```
POST /api/upload/video
Authorization: Bearer {accessToken}
Content-Type: multipart/form-data
```

**Request:**
```
Form Data:
  file: <binary video file (mp4, avi, mov)>
  cameraId: "550e8400-e29b-41d4-a716-446655440000" (optional)
```

**Response (200 OK):**
```json
{
  "success": true,
  "fileUrl": "/uploads/videos/video_20260629_143000.mp4",
  "fileName": "video_20260629_143000.mp4",
  "fileSize": 5242880,
  "message": "Tải video thành công"
}
```

**Validation:**
- file: required, max 500MB
- formats: mp4, avi, mov only

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 413 Payload Too Large
- 500 Internal Server Error

---

### 5.4 YOLOv26 Detection API

#### 5.4.1 Detect from Image

```
POST /api/detect/image
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "imageUrl": "/uploads/images/image_20260629_143000.jpg",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200 OK):**
```json
{
  "detectionId": "550e8400-e29b-41d4-a716-446655440002",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000",
  "imageUrl": "/uploads/images/image_20260629_143000.jpg",
  "detectionTime": "2026-06-29T14:30:00Z",
  "detections": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "classId": 1,
      "className": "car",
      "confidence": 0.95,
      "boundingBox": {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 450
      }
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440004",
      "classId": 3,
      "className": "motorcycle",
      "confidence": 0.87,
      "boundingBox": {
        "x1": 400,
        "y1": 200,
        "x2": 550,
        "y2": 500
      }
    }
  ],
  "summary": {
    "totalDetections": 2,
    "car": 1,
    "motorcycle": 1,
    "truck": 0,
    "bus": 0
  }
}
```

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

#### 5.4.2 Detect from Video

```
POST /api/detect/video
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "videoUrl": "/uploads/videos/video_20260629_143000.mp4",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000",
  "frameInterval": 5
}
```

**Response (200 OK):**
```json
{
  "jobId": "job_550e8400-e29b-41d4-a716-446655440005",
  "status": "processing",
  "videoUrl": "/uploads/videos/video_20260629_143000.mp4",
  "progress": 0,
  "estimatedTime": "2 minutes",
  "message": "Đang xử lý video..."
}
```

**Response (Polling - Job Status):**
```json
{
  "jobId": "job_550e8400-e29b-41d4-a716-446655440005",
  "status": "completed",
  "progress": 100,
  "totalFrames": 120,
  "detectedFrames": 45,
  "totalDetections": 156,
  "summary": {
    "car": 98,
    "motorcycle": 42,
    "truck": 12,
    "bus": 4
  },
  "resultUrl": "/api/detect/results/job_550e8400-e29b-41d4-a716-446655440005"
}
```

**HTTP Status Codes:**
- 200 OK (async task started)
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.4.3 Live Detection Stream

```
GET /api/detect/live?cameraId={cameraId}
Authorization: Bearer {accessToken}
```

**Response (200 OK - Server-Sent Events):**
```
event: detection
data: {
  "timestamp": "2026-06-29T14:30:00Z",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000",
  "detectionId": "550e8400-e29b-41d4-a716-446655440006",
  "className": "car",
  "confidence": 0.92,
  "boundingBox": {
    "x1": 100,
    "y1": 150,
    "x2": 300,
    "y2": 450
  }
}

event: detection
data: {
  "timestamp": "2026-06-29T14:30:01Z",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000",
  "detectionId": "550e8400-e29b-41d4-a716-446655440007",
  "className": "motorcycle",
  "confidence": 0.88,
  "boundingBox": {
    "x1": 400,
    "y1": 200,
    "x2": 550,
    "y2": 500
  }
}
```

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

### 5.5 Detection History API

#### 5.5.1 Get All Detections

```
GET /api/detections?page=1&pageSize=10&cameraId={cameraId}&vehicleType={type}&from={date}&to={date}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "cameraId": "550e8400-e29b-41d4-a716-446655440000",
      "vehicleType": "car",
      "confidence": 0.95,
      "boundingBox": {
        "x1": 100,
        "y1": 150,
        "x2": 300,
        "y2": 450
      },
      "imageUrl": "/uploads/images/image_20260629_143000.jpg",
      "detectionTime": "2026-06-29T14:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "pageSize": 10
}
```

**Query Parameters:**
- `page`: int (default: 1)
- `pageSize`: int (default: 10)
- `cameraId`: UUID (optional)
- `vehicleType`: string (optional, 'car'|'motorcycle'|'truck'|'bus')
- `from`: datetime (optional)
- `to`: datetime (optional)

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.5.2 Get Detection by ID

```
GET /api/detections/{id}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "cameraId": "550e8400-e29b-41d4-a716-446655440000",
  "vehicleType": "car",
  "confidence": 0.95,
  "boundingBox": {
    "x1": 100,
    "y1": 150,
    "x2": 300,
    "y2": 450
  },
  "imageUrl": "/uploads/images/image_20260629_143000.jpg",
  "detectionTime": "2026-06-29T14:30:00Z"
}
```

**HTTP Status Codes:**
- 200 OK
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

#### 5.5.3 Delete Detection

```
DELETE /api/detections/{id}
Authorization: Bearer {accessToken}
```

**Response (204 No Content):**
```
(no body)
```

**HTTP Status Codes:**
- 204 No Content
- 401 Unauthorized
- 404 Not Found
- 500 Internal Server Error

---

### 5.6 Dashboard API

#### 5.6.1 Get Dashboard Data

```
GET /api/dashboard
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "totalVehiclesDaily": 1256,
  "motorcycleCount": 456,
  "carCount": 598,
  "truckCount": 123,
  "busCount": 79,
  "onlineCameras": 8,
  "offlineCameras": 2,
  "totalCameras": 10
}
```

**HTTP Status Codes:**
- 200 OK
- 401 Unauthorized
- 500 Internal Server Error

---

### 5.7 Statistics API

#### 5.7.1 Get Hourly Statistics

```
GET /api/statistics/hourly?cameraId={cameraId}&date={date}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
[
  {
    "hour": "2026-06-29T08:00:00Z",
    "totalVehicles": 45,
    "vehiclesByType": {
      "car": 28,
      "motorcycle": 12,
      "truck": 3,
      "bus": 2
    }
  },
  {
    "hour": "2026-06-29T09:00:00Z",
    "totalVehicles": 62,
    "vehiclesByType": {
      "car": 38,
      "motorcycle": 18,
      "truck": 4,
      "bus": 2
    }
  }
]
```

**Query Parameters:**
- `cameraId`: UUID (optional)
- `date`: date (YYYY-MM-DD, default: today)

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.7.2 Get Daily Statistics

```
GET /api/statistics/daily?cameraId={cameraId}&month={month}&year={year}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
[
  {
    "date": "2026-06-01",
    "totalVehicles": 1245,
    "vehiclesByType": {
      "car": 745,
      "motorcycle": 345,
      "truck": 87,
      "bus": 68
    }
  },
  {
    "date": "2026-06-02",
    "totalVehicles": 1398,
    "vehiclesByType": {
      "car": 823,
      "motorcycle": 412,
      "truck": 96,
      "bus": 67
    }
  }
]
```

**Query Parameters:**
- `cameraId`: UUID (optional)
- `month`: int (1-12)
- `year`: int

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.7.3 Get Monthly Statistics

```
GET /api/statistics/monthly?cameraId={cameraId}&year={year}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
[
  {
    "month": "2026-01",
    "totalVehicles": 38456,
    "vehiclesByType": {
      "car": 23000,
      "motorcycle": 10500,
      "truck": 3200,
      "bus": 1756
    }
  },
  {
    "month": "2026-02",
    "totalVehicles": 35789,
    "vehiclesByType": {
      "car": 21456,
      "motorcycle": 9876,
      "truck": 2980,
      "bus": 1477
    }
  }
]
```

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.7.4 Get Vehicle Type Statistics

```
GET /api/statistics/vehicle-type?from={date}&to={date}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
[
  {
    "vehicleType": "car",
    "count": 5600,
    "percentage": 54.5
  },
  {
    "vehicleType": "motorcycle",
    "count": 3200,
    "percentage": 31.2
  },
  {
    "vehicleType": "truck",
    "count": 890,
    "percentage": 8.7
  },
  {
    "vehicleType": "bus",
    "count": 510,
    "percentage": 5.0
  }
]
```

**Query Parameters:**
- `from`: datetime (YYYY-MM-DD HH:mm:ss)
- `to`: datetime (YYYY-MM-DD HH:mm:ss)

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.7.5 Get Pie Chart Data

```
GET /api/statistics/pie?date={date}
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
[
  {
    "name": "Car",
    "value": 5600
  },
  {
    "name": "Motorcycle",
    "value": 3200
  },
  {
    "name": "Truck",
    "value": 890
  },
  {
    "name": "Bus",
    "value": 510
  }
]
```

**Query Parameters:**
- `date`: date (YYYY-MM-DD, default: today)

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 500 Internal Server Error

---

### 5.8 Settings API

#### 5.8.1 Get Settings

```
GET /api/settings
Authorization: Bearer {accessToken}
```

**Response (200 OK):**
```json
{
  "confidenceThreshold": 0.5,
  "detectInterval": 500,
  "fps": 30
}
```

**HTTP Status Codes:**
- 200 OK
- 401 Unauthorized
- 500 Internal Server Error

---

#### 5.8.2 Update Settings

```
PUT /api/settings
Authorization: Bearer {accessToken}
Content-Type: application/json
```

**Request:**
```json
{
  "confidenceThreshold": 0.6,
  "detectInterval": 1000,
  "fps": 24
}
```

**Response (200 OK):**
```json
{
  "confidenceThreshold": 0.6,
  "detectInterval": 1000,
  "fps": 24,
  "message": "Cập nhật cấu hình thành công"
}
```

**Response (400 Bad Request):**
```json
{
  "errors": [
    {
      "field": "confidenceThreshold",
      "message": "Giá trị phải nằm trong khoảng 0 đến 1"
    }
  ]
}
```

**Validation:**
- confidenceThreshold: float, range 0-1
- detectInterval: int, >= 100ms
- fps: int, range 1-60

**HTTP Status Codes:**
- 200 OK
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden (only admin)
- 500 Internal Server Error

---

## 6. Controllers & Services

### 6.1 AuthController Example

```csharp
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using TrafficMonitoring.DTOs.Auth;
using TrafficMonitoring.Services;

namespace TrafficMonitoring.Controllers;

[ApiController]
[Route("api")]
public class AuthController : ControllerBase
{
    private readonly IAuthService _authService;

    public AuthController(IAuthService authService)
    {
        _authService = authService;
    }

    [HttpPost("login")]
    public async Task<IActionResult> Login([FromBody] LoginRequest request)
    {
        if (!ModelState.IsValid)
            return BadRequest(ModelState);

        try
        {
            var response = await _authService.AuthenticateAsync(request);
            return Ok(response);
        }
        catch (UnauthorizedAccessException)
        {
            return Unauthorized(new { errors = new[] { new { code = "INVALID_CREDENTIALS", message = "Tên đăng nhập hoặc mật khẩu không đúng" } } });
        }
    }

    [HttpPost("logout")]
    [Authorize]
    public async Task<IActionResult> Logout()
    {
        await _authService.LogoutAsync(User.FindFirst("sub")?.Value);
        return NoContent();
    }

    [HttpGet("profile")]
    [Authorize]
    public async Task<IActionResult> GetProfile()
    {
        var userId = User.FindFirst("sub")?.Value;
        if (string.IsNullOrEmpty(userId))
            return Unauthorized();

        var profile = await _authService.GetProfileAsync(Guid.Parse(userId));
        return Ok(profile);
    }
}
```

### 6.2 IAuthService Example

```csharp
using TrafficMonitoring.DTOs.Auth;

namespace TrafficMonitoring.Services;

public interface IAuthService
{
    Task<AuthResponse> AuthenticateAsync(LoginRequest request);
    Task LogoutAsync(string? userId);
    Task<UserProfileDto> GetProfileAsync(Guid userId);
}
```

### 6.3 AuthService Implementation Example

```csharp
using TrafficMonitoring.Data;
using TrafficMonitoring.DTOs.Auth;
using TrafficMonitoring.Repositories;
using BCrypt.Net;

namespace TrafficMonitoring.Services;

public class AuthService : IAuthService
{
    private readonly IOperatorRepository _operatorRepository;
    private readonly TrafficMonitoringDbContext _db;

    public AuthService(IOperatorRepository operatorRepository, TrafficMonitoringDbContext db)
    {
        _operatorRepository = operatorRepository;
        _db = db;
    }

    public async Task<AuthResponse> AuthenticateAsync(LoginRequest request)
    {
        var operator_ = await _operatorRepository.GetByUsernameAsync(request.Username);
        
        if (operator_ == null || !BCrypt.Verify(request.Password, operator_.PasswordHash))
            throw new UnauthorizedAccessException();

        if (!operator_.IsActive)
            throw new UnauthorizedAccessException("Tài khoản đã bị vô hiệu hóa");

        var accessToken = GenerateAccessToken(operator_);
        var refreshToken = GenerateRefreshToken();

        return new AuthResponse
        {
            AccessToken = accessToken,
            RefreshToken = refreshToken,
            User = new UserProfileDto
            {
                Id = operator_.Id,
                Username = operator_.Username,
                Email = operator_.Email,
                FullName = operator_.FullName,
                Role = operator_.Role
            },
            ExpiresAt = DateTimeOffset.UtcNow.AddHours(1)
        };
    }

    public async Task LogoutAsync(string? userId)
    {
        // TODO: Implement logout logic (blacklist token, etc.)
        await Task.CompletedTask;
    }

    public async Task<UserProfileDto> GetProfileAsync(Guid userId)
    {
        var operator_ = await _operatorRepository.GetByIdAsync(userId);
        if (operator_ == null)
            throw new KeyNotFoundException("Không tìm thấy operator");

        return new UserProfileDto
        {
            Id = operator_.Id,
            Username = operator_.Username,
            Email = operator_.Email,
            FullName = operator_.FullName,
            Role = operator_.Role
        };
    }

    private string GenerateAccessToken(TrafficMonitoring.Models.Operator operator_)
    {
        // TODO: Implement JWT token generation
        return "token_" + Guid.NewGuid().ToString();
    }

    private string GenerateRefreshToken()
    {
        return Guid.NewGuid().ToString("N");
    }
}
```

### 6.4 IOperatorRepository Example

```csharp
using TrafficMonitoring.Models;

namespace TrafficMonitoring.Repositories;

public interface IOperatorRepository
{
    Task<Operator?> GetByIdAsync(Guid id);
    Task<Operator?> GetByUsernameAsync(string username);
    Task<IEnumerable<Operator>> GetAllAsync(int page = 1, int pageSize = 10);
    Task AddAsync(Operator entity);
    Task UpdateAsync(Operator entity);
    Task DeleteAsync(Guid id);
}
```

### 6.5 OperatorRepository Implementation Example

```csharp
using Microsoft.EntityFrameworkCore;
using TrafficMonitoring.Data;
using TrafficMonitoring.Models;

namespace TrafficMonitoring.Repositories;

public class OperatorRepository : IOperatorRepository
{
    private readonly TrafficMonitoringDbContext _db;

    public OperatorRepository(TrafficMonitoringDbContext db)
    {
        _db = db;
    }

    public Task<Operator?> GetByIdAsync(Guid id) =>
        _db.Operators.FirstOrDefaultAsync(o => o.Id == id);

    public Task<Operator?> GetByUsernameAsync(string username) =>
        _db.Operators.FirstOrDefaultAsync(o => o.Username == username);

    public async Task<IEnumerable<Operator>> GetAllAsync(int page = 1, int pageSize = 10)
    {
        return await _db.Operators
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
    }

    public async Task AddAsync(Operator entity)
    {
        await _db.Operators.AddAsync(entity);
        await _db.SaveChangesAsync();
    }

    public async Task UpdateAsync(Operator entity)
    {
        _db.Operators.Update(entity);
        await _db.SaveChangesAsync();
    }

    public async Task DeleteAsync(Guid id)
    {
        var entity = await GetByIdAsync(id);
        if (entity != null)
        {
            _db.Operators.Remove(entity);
            await _db.SaveChangesAsync();
        }
    }
}
```

---

## 7. Repositories

### 7.1 Generic Repository Interface

```csharp
namespace TrafficMonitoring.Repositories;

public interface IRepository<T> where T : class
{
    Task<T?> GetByIdAsync(Guid id);
    Task<IEnumerable<T>> GetAllAsync(int page = 1, int pageSize = 10);
    Task AddAsync(T entity);
    Task UpdateAsync(T entity);
    Task DeleteAsync(Guid id);
}
```

### 7.2 Generic Repository Implementation

```csharp
using Microsoft.EntityFrameworkCore;
using TrafficMonitoring.Data;

namespace TrafficMonitoring.Repositories;

public class Repository<T> : IRepository<T> where T : class
{
    protected readonly TrafficMonitoringDbContext DbContext;
    protected readonly DbSet<T> DbSet;

    public Repository(TrafficMonitoringDbContext dbContext)
    {
        DbContext = dbContext;
        DbSet = dbContext.Set<T>();
    }

    public virtual async Task<T?> GetByIdAsync(Guid id)
    {
        return await DbSet.FindAsync(id);
    }

    public virtual async Task<IEnumerable<T>> GetAllAsync(int page = 1, int pageSize = 10)
    {
        return await DbSet.Skip((page - 1) * pageSize).Take(pageSize).ToListAsync();
    }

    public virtual async Task AddAsync(T entity)
    {
        await DbSet.AddAsync(entity);
        await DbContext.SaveChangesAsync();
    }

    public virtual async Task UpdateAsync(T entity)
    {
        DbSet.Update(entity);
        await DbContext.SaveChangesAsync();
    }

    public virtual async Task DeleteAsync(Guid id)
    {
        var entity = await GetByIdAsync(id);
        if (entity != null)
        {
            DbSet.Remove(entity);
            await DbContext.SaveChangesAsync();
        }
    }
}
```

### 7.3 Camera Repository

```csharp
using Microsoft.EntityFrameworkCore;
using TrafficMonitoring.Data;
using TrafficMonitoring.Models;

namespace TrafficMonitoring.Repositories;

public interface ICameraRepository : IRepository<Camera>
{
    Task<IEnumerable<Camera>> GetByStatusAsync(string status, int page = 1, int pageSize = 10);
    Task<Camera?> GetByCameraNameAsync(string cameraName);
}

public class CameraRepository : Repository<Camera>, ICameraRepository
{
    public CameraRepository(TrafficMonitoringDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<IEnumerable<Camera>> GetByStatusAsync(string status, int page = 1, int pageSize = 10)
    {
        return await DbSet
            .Where(c => c.Status == status)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
    }

    public Task<Camera?> GetByCameraNameAsync(string cameraName)
    {
        return DbSet.FirstOrDefaultAsync(c => c.CameraName == cameraName);
    }
}
```

### 7.4 Detection Repository

```csharp
using Microsoft.EntityFrameworkCore;
using TrafficMonitoring.Data;
using TrafficMonitoring.Models;

namespace TrafficMonitoring.Repositories;

public interface IDetectionRepository : IRepository<Detection>
{
    Task<IEnumerable<Detection>> GetByCameraIdAsync(Guid cameraId, int page = 1, int pageSize = 10);
    Task<IEnumerable<Detection>> GetByVehicleTypeAsync(string vehicleType, int page = 1, int pageSize = 10);
    Task<IEnumerable<Detection>> GetByDateRangeAsync(DateTime from, DateTime to, int page = 1, int pageSize = 10);
}

public class DetectionRepository : Repository<Detection>, IDetectionRepository
{
    public DetectionRepository(TrafficMonitoringDbContext dbContext) : base(dbContext)
    {
    }

    public async Task<IEnumerable<Detection>> GetByCameraIdAsync(Guid cameraId, int page = 1, int pageSize = 10)
    {
        return await DbSet
            .Where(d => d.CameraId == cameraId)
            .OrderByDescending(d => d.DetectionTime)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
    }

    public async Task<IEnumerable<Detection>> GetByVehicleTypeAsync(string vehicleType, int page = 1, int pageSize = 10)
    {
        return await DbSet
            .Where(d => d.VehicleType == vehicleType)
            .OrderByDescending(d => d.DetectionTime)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
    }

    public async Task<IEnumerable<Detection>> GetByDateRangeAsync(DateTime from, DateTime to, int page = 1, int pageSize = 10)
    {
        return await DbSet
            .Where(d => d.DetectionTime >= from && d.DetectionTime <= to)
            .OrderByDescending(d => d.DetectionTime)
            .Skip((page - 1) * pageSize)
            .Take(pageSize)
            .ToListAsync();
    }
}
```

---

## 8. Error Handling & Validation

### 8.1 Standard Error Response Format

```json
{
  "errors": [
    {
      "code": "ERROR_CODE",
      "field": "fieldName (optional)",
      "message": "Error message in Vietnamese"
    }
  ],
  "traceId": "0HN1GHEFP7:00000001"
}
```

### 8.2 Common Error Codes

| Code | HTTP Status | Message |
|------|------------|---------|
| INVALID_CREDENTIALS | 401 | Tên đăng nhập hoặc mật khẩu không đúng |
| UNAUTHORIZED | 401 | Chưa xác thực |
| FORBIDDEN | 403 | Không có quyền truy cập |
| NOT_FOUND | 404 | Không tìm thấy tài nguyên |
| VALIDATION_ERROR | 400 | Dữ liệu nhập không hợp lệ |
| CONFLICT | 409 | Xung đột dữ liệu |
| INTERNAL_ERROR | 500 | Lỗi máy chủ nội bộ |

### 8.3 Validation Examples

**Username Validation:**
- Required: true
- Max length: 50 characters
- Pattern: alphanumeric, underscore, hyphen

**Password Validation:**
- Required: true
- Min length: 8 characters
- Must contain: uppercase, lowercase, digit, special char

**Email Validation:**
- Required: true
- Valid email format
- Max length: 255 characters

**Confidence Validation:**
- Type: float
- Range: 0.0 - 1.0

---

## 9. Kết Luận

Tài liệu này cung cấp đầy đủ thiết kế RESTful API, database schema, entities, DTOs, controllers, services và repositories cho hệ thống giám sát giao thông thông minh sử dụng YOLOv26.

**Các bước triển khai tiếp theo:**
1. Tạo các controllers cho tất cả API
2. Implement các services với business logic
3. Implement các repositories
4. Cấu hình Dependency Injection trong Program.cs
5. Tạo migrations và apply schema
6. Implement JWT authentication
7. Thêm validation và error handling
8. Viết unit tests
9. Setup CI/CD pipeline

---

*API Specification v2 | Hệ Thống Giám Sát Giao Thông Thông Minh | 29/06/2026*
