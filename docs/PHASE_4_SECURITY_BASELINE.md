# PHASE 4 — SECURITY & TENANT ISOLATION BASELINE
## Virtual Classrooms & Real-Time Collaboration Subsystem

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Virtual Classrooms Security, RBAC, Tenant Isolation & Secret Concealment  
**Status:** FROZEN & VERIFIED  
**Phase:** Phase 4 Final Closure  
**Date:** 2026-08-23  

---

## 1. Security Architecture & Threat Model

The Virtual Classroom subsystem implements multi-layered defense-in-depth security principles across multi-tenancy, authentication, authorization, cryptographic signing, and data privacy.

```
+-----------------------------------------------------------------------------------+
|                        SECURITY DEFENSE IN DEPTH MATRIX                           |
+-----------------------------------------------------------------------------------+
| 1. Authentication Gate       | JWT Bearer Token validation, Argon2 password       |
|                              | verification, session lockout upon failure.        |
+------------------------------+----------------------------------------------------+
| 2. Multi-Tenant Barrier      | Institution ID derived strictly from auth context. |
|    (Blind 404 Behavior)      | Cross-tenant attempts return Blind 404 Not Found.  |
+------------------------------+----------------------------------------------------+
| 3. Academic Gating           | Active SIMAT enrollment required for student       |
|    (Enrollment Authority)    | viewer entry. Unenrolled rejected with HTTP 403.   |
+------------------------------+----------------------------------------------------+
| 4. Cryptographic Provider    | SHA-1 / SHA-256 server-side checksum calculation.  |
|    Signing (BigBlueButton)   | Secret salts never sent to frontend or logs.       |
+------------------------------+----------------------------------------------------+
| 5. Secret Concealment        | Moderator/Attendee password hashes and salts       |
|    (Zero-Leakage Policy)     | omitted from all Pydantic schemas and UI state.    |
+------------------------------+----------------------------------------------------+
| 6. Recording Privacy         | Students strictly restricted to published assets.  |
|    (Publication Gating)      | Staff permitted to manage publication visibility.  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Multi-Tenant Isolation & Blind 404 Enforcement

### Tenant Authority Resolution
1. Every API endpoint extracts the active tenant identity (`institution_id`) strictly from the authenticated JWT `User` entity (`current_user.institution_id`).
2. Client-supplied query parameters or body payloads are NEVER accepted as the authority for institutional context (except for explicit `SUPERADMIN` national operations).

### Blind 404 Guarantee
- Any attempt by a user from Institution A to query, launch, join, inspect, or delete a `VirtualClassroom`, `MeetingAttendance`, or `MeetingRecording` owned by Institution B triggers `VirtualClassroomNotFoundError` or `RecordingNotFoundError`.
- The API maps this directly to `HTTP 404 Not Found` (`code: "VIRTUAL_CLASSROOM_NOT_FOUND"` / `"RECORDING_NOT_FOUND"`).
- **Security Invariant:** The system strictly conceals the existence of cross-tenant resources. Under no circumstance is an `HTTP 403 Forbidden` response returned for cross-tenant resource lookups, preventing resource enumeration attacks.

---

## 3. Academic Anchoring & SIMAT Enrollment Authorization

When a Virtual Classroom is scheduled with an `academic_assignment_id`:
1. **Host Verification:** The host must be an authorized teacher or institutional staff member.
2. **Participant Role Resolution:**
   - Host Teacher / Rector / Academic Coordinator $\rightarrow$ Granted `MODERATOR` role.
   - Student $\rightarrow$ The domain service queries PostgreSQL for an `ACTIVE` SIMAT `Enrollment` record linking the student to the classroom's assigned `Group`.
   - **Enrolled Student:** Granted `VIEWER` role with signed entry link.
   - **Unenrolled Student:** Immediately blocked with `UnauthorizedMeetingAccessError` (HTTP 403). No meeting URL, credentials, or provider tokens are returned.

---

## 4. Cryptographic Provider Signing & Secret Concealment

### Provider Secret Protection
- The BigBlueButton shared secret (`BBB_SHARED_SECRET`) is stored exclusively in backend environment configurations (`Settings`).
- Checksums are calculated exclusively on the backend server:
  $$\text{checksum} = \text{HMAC/Hash}(\text{callName} + \text{queryString} + \text{sharedSecret})$$
- The frontend NEVER calculates checksums, receives the shared salt, or constructs BigBlueButton URLs directly.

### Zero-Leakage Policy
- Passwords (`moderator_password`, `attendee_password`) generated for meeting provisioning are hashed using Argon2 (`moderator_password_hash`, `attendee_password_hash`) in the database.
- Response Pydantic schemas (`VirtualClassroomResponse`, `MeetingRecordingResponse`, `JoinMeetingResponse`) strictly exclude:
  - `moderator_password` / `moderator_password_hash`
  - `attendee_password` / `attendee_password_hash`
  - `BBB_SHARED_SECRET`
  - Internal database session states.

---

## 5. Telemetry & Recording Privacy

1. **Telemetry:**
   - Participant join and leave timestamps are logged in `MeetingAttendance`.
   - Durations are calculated in integer seconds server-side, preventing client-side telemetry forgery.
   - Upon meeting termination by the host, all unclosed participant attendance records are safely and idempotently closed.
2. **Recording Visibility:**
   - Recordings discovered from the provider are ingested with `is_published = True` by default.
   - When a staff member sets `is_published = False`, student-scoped API queries (`GET /api/v1/recordings/classroom/{id}`) filter out unpublished recordings, returning `total = 0`.
   - Unauthorized attempts by students to modify publication or delete recordings are blocked by RBAC dependencies (`HTTP 403`).
