# PHASE 4 — FINAL ARCHITECTURE SPECIFICATION
## Virtual Classrooms & Real-Time Collaboration Subsystem

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Virtual Classrooms, Real-Time Meeting Delivery, Attendance Telemetry & Recording Management  
**Status:** FROZEN & VERIFIED  
**Phase:** Phase 4 Final Closure  
**Date:** 2026-08-23  

---

## 1. Architectural Overview & Component Hierarchy

The Virtual Classroom subsystem delivers multi-tenant synchronous videoconferencing, participant access control anchored to Colombian academic assignments, automated attendance tracking, and server-side recording lifecycle management.

```
+-----------------------------------------------------------------------------------+
|                           FRONTEND APPLICATION LAYER                              |
|  - React 18 + Vite + TypeScript SPA                                               |
|  - Views: VirtualClassroomsView (Catalog, Launch, Join, End, Telemetry, Recs)      |
|  - Services: virtualClassroomApi (Axios Client with JWT Bearer Interceptors)      |
+-----------------------------------------------------------------------------------+
                                         │  HTTPS / REST + JSON
                                         ▼
+-----------------------------------------------------------------------------------+
|                           REST API GATEWAY (FastAPI)                             |
|  - /api/v1/virtual-classrooms (Lifecycle, Join URL Resolution, Telemetry)          |
|  - /api/v1/recordings (Sync, Publication Toggle, Deletion)                        |
|  - Tenant Extraction from JWT Context (Blind 404 Barrier on Tenant Mismatch)      |
|  - Correlation ID Tracing & Sensitive Field Exclusion                             |
+-----------------------------------------------------------------------------------+
                                         │  Async Service Invocation
                                         ▼
+-----------------------------------------------------------------------------------+
|                        AUTHORITATIVE DOMAIN SERVICES                              |
|  - VirtualClassroomService: Lifecycle State Machine & SIMAT Enrollment Gating     |
|  - AttendanceService: Real-Time Join/Leave Telemetry & Duration Computation       |
|  - RecordingService: Provider Synchronization & Publication Visibility Gating     |
|  - Audit Logging: IAuditService (MEETING_LAUNCHED, MEETING_JOINED, RECS, etc.)    |
+-----------------------------------------------------------------------------------+
                    │                                         │
                    ▼                                         ▼
+------------------------------------+   +------------------------------------------+
|      POSTGRESQL DATA PERSISTENCE   |   |        MEETING PROVIDER ABSTRACTION      |
|  - VirtualClassroom (UUID, Tenant) |   |  - IMeetingProvider Protocol             |
|  - MeetingAttendance (User, Time)  |   |  - BBBAdapter (SHA-1 / SHA-256 Checksum) |
|  - MeetingRecording (Playback URL) |   |  - MockMeetingProvider (Testing/Offline) |
|  - AcademicAssignment Anchoring    |   |  - get_meeting_provider() Factory        |
+------------------------------------+   +------------------------------------------+
                                                              │  Signed HTTP API Calls
                                                              ▼
                                         +------------------------------------------+
                                         |         BIGBLUEBUTTON CLUSTER            |
                                         |  - create, join, end, isMeetingRunning   |
                                         |  - getMeetingInfo, getRecordings         |
                                         +------------------------------------------+
```

---

## 2. Domain Models & Relational Architecture

### 1. `VirtualClassroom` (`virtual_classrooms`)
- **Primary Key:** `id` (`UUID`, default `uuid4`).
- **Tenant Scope:** `institution_id` (`UUID`, Foreign Key to `institutions.id`, Index).
- **Academic Anchor:** `academic_assignment_id` (`UUID`, Foreign Key to `academic_assignments.id`, Nullable).
- **Host Identity:** `host_user_id` (`UUID`, Foreign Key to `users.id`).
- **Meeting Identification:** `bbb_meeting_id` (`VARCHAR(120)`, Unique, format `pevn-{institution_id[:8]}-{uuid4()[:12]}`).
- **Cryptographic Security:** `moderator_password_hash` (`VARCHAR(255)`), `attendee_password_hash` (`VARCHAR(255)`).
- **Lifecycle State:** `status` (`Enum: SCHEDULED, RUNNING, ENDED, CANCELLED`).
- **Timestamps:** `scheduled_start_time`, `scheduled_end_time`, `actual_start_time`, `actual_end_time`, `created_at`, `updated_at`.
- **Feature Flags:** `is_recording_enabled` (`Boolean`), `is_breakout_enabled` (`Boolean`), `max_participants` (`Integer`).
- **Arbitrary Metadata:** `provider_metadata` (`JSONB`).

### 2. `MeetingAttendance` (`meeting_attendances`)
- **Primary Key:** `id` (`UUID`).
- **Room Scope:** `virtual_classroom_id` (`UUID`, Foreign Key to `virtual_classrooms.id`, Index).
- **Participant Scope:** `user_id` (`UUID`, Foreign Key to `users.id`, Index).
- **Participant Role:** `role` (`Enum: MODERATOR, VIEWER`).
- **Telemetry:** `joined_at` (`DateTime`), `left_at` (`DateTime`, Nullable), `duration_seconds` (`Integer`, Nullable).

### 3. `MeetingRecording` (`meeting_recordings`)
- **Primary Key:** `id` (`UUID`).
- **Tenant Scope:** `institution_id` (`UUID`, Foreign Key to `institutions.id`, Index).
- **Room Scope:** `virtual_classroom_id` (`UUID`, Foreign Key to `virtual_classrooms.id`, Index).
- **External Asset:** `bbb_record_id` (`VARCHAR(120)`, Index), `playback_url` (`VARCHAR(500)`).
- **Asset Metrics:** `duration_seconds` (`Integer`), `file_size_bytes` (`BigInteger`, Nullable).
- **Publication Visibility:** `is_published` (`Boolean`, default `True`).
- **Timestamps:** `recorded_at` (`DateTime`), `created_at` (`DateTime`).

---

## 3. Meeting Provider Abstraction Layer

### Architecture
- **Protocol:** `IMeetingProvider` (`backend/app/core/meeting/interfaces.py`).
- **Contracts (DTOs):** `MeetingCreateOptions`, `MeetingInfo`, `JoinMeetingOptions`, `EndMeetingOptions`, `RecordingInfo`.
- **Concrete Implementations:**
  1. `BBBAdapter` (`backend/app/core/meeting/bbb_adapter.py`): Concrete client communicating with BigBlueButton REST APIs via signed query string checksums. Supports `sha1` and `sha256` signing algorithms.
  2. `MockMeetingProvider` (`backend/app/core/meeting/mock_provider.py`): In-memory stateful meeting simulation provider for zero-dependency CI/CD and offline verification.
- **Provider Factory:** `get_meeting_provider()` dynamically resolves the configured engine based on `MEETING_PROVIDER_TYPE` (`"bbb"` or `"mock"`).

---

## 4. Domain Services Layer & Business Rules

### 1. `VirtualClassroomService`
- **Creation & Provisioning:** Validates institutional existence and `AcademicAssignment` tenant match. Provisions secure cryptographic credentials.
- **Session Launch:** Invokes meeting provider `create_meeting`, transitions status from `SCHEDULED` $\rightarrow$ `RUNNING`, sets `actual_start_time`, and logs `MEETING_LAUNCHED` audit event.
- **Participant Authority & Join Resolution:**
  - If actor is the assigned Host Teacher or institutional Admin (Rector/Academic Coordinator) $\rightarrow$ Resolved as `MODERATOR`.
  - If session is anchored to an `AcademicAssignment`, checks that student has an `ACTIVE` SIMAT `Enrollment` in the assigned `Group`. If verified $\rightarrow$ Resolved as `VIEWER`.
  - If student is not actively enrolled in the assigned group $\rightarrow$ Raises `UnauthorizedMeetingAccessError` (HTTP 403).
  - Invokes provider `generate_join_url`, logs initial `joined_at` record in `AttendanceService`, and emits `MEETING_JOINED` audit event.
- **Termination:** Host or Admin terminates session via provider `end_meeting`, transitions status to `ENDED`, records `actual_end_time`, and triggers automatic closure of all open attendance records.

### 2. `AttendanceService`
- Records participant `joined_at` timestamp.
- Records participant `left_at` timestamp upon explicit exit and computes `duration_seconds = (left_at - joined_at).total_seconds()`.
- Idempotently terminates all open attendance records upon classroom conclusion without corrupting durations.

### 3. `RecordingService`
- Synchronizes processed recordings from meeting provider and persists metadata.
- Filters queries: Staff (teachers/rectors) see all recording assets; students are restricted exclusively to `is_published == True` assets.
- Toggles publication visibility and manages asset metadata deletion within tenant scope.

---

## 5. REST API & Gateway Layer

All endpoints operate under strict tenant isolation.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/virtual-classrooms` | Create & schedule virtual classroom |
| `GET` | `/api/v1/virtual-classrooms` | List classrooms (filterable by assignment/status) |
| `GET` | `/api/v1/virtual-classrooms/{id}` | Retrieve classroom by ID (Blind 404) |
| `POST` | `/api/v1/virtual-classrooms/{id}/launch` | Launch meeting session on provider |
| `POST` | `/api/v1/virtual-classrooms/{id}/join` | Generate signed join URL for participant |
| `POST` | `/api/v1/virtual-classrooms/{id}/end` | Terminate session & close attendances |
| `GET` | `/api/v1/virtual-classrooms/{id}/attendances` | List session attendance telemetry |
| `POST` | `/api/v1/virtual-classrooms/{id}/leave` | Record participant departure timestamp |
| `GET` | `/api/v1/recordings/classroom/{id}` | List session recordings (role-filtered) |
| `POST` | `/api/v1/recordings/classroom/{id}/sync` | Synchronize recordings from provider |
| `PATCH` | `/api/v1/recordings/{id}/publish` | Toggle recording publication visibility |
| `DELETE` | `/api/v1/recordings/{id}` | Delete recording metadata |

---

## 6. Frontend Application Layer

- **Routing:** `/virtual-classrooms` protected by `<RequireAuth>`.
- **Navigation:** Integrated into `RootLayout` navbar and `Dashboard` quick action cards.
- **Component Views:** `VirtualClassroomsView` provides catalog cards, status badges (`SCHEDULED`, `RUNNING`, `ENDED`, `CANCELLED`), room scheduling modal, launch/join/end actions, and attendance/recording telemetry tabs.
- **Secure Redirection:** Opens signed BBB join URLs in secure popup tabs (`noopener,noreferrer`) without exposing internal salts or secrets.
