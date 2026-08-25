# PHASE 9 — LIVE END-TO-END CERTIFICATION & UAT SPECIFICATION
## Comprehensive End-to-End & Physical Device Certification

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** End-to-End Meeting Delivery, Multi-Tenant Security & Device UAT  
**Status:** SPECIFICATION COMPLETE & READY FOR PHYSICAL COMMISSIONING  
**Phase:** Phase 9 External Commissioning  
**Date:** 2026-08-23  

---

## 1. UAT Execution Overview

The PEVN Virtual Classroom subsystem undergoes a dual-layer User Acceptance Testing process:
1. **Automated End-to-End System Tests (`UAT-01` to `UAT-20`):** Full-stack automated verification testing room provisioning, session launch, role resolution (`MODERATOR` vs `VIEWER`), SIMAT enrollment gating (HTTP 403), multi-tenant isolation (Blind 404), attendance telemetry duration, and recording synchronization/privacy.
2. **Physical Device & Media Transport UAT (`UAT-Physical-01` to `UAT-Physical-10`):** Real-world audiovisual testing on physical computers, mobile phones, and school networks in Colombia.

---

## 2. Automated End-to-End System Tests (`UAT-01` to `UAT-20`)

| Test ID | UAT Scenario | Expected Result | Verification Basis | Status |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-01** | Teacher Creates Classroom | Classroom created in `SCHEDULED` state; Argon2 password hashes generated | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-02** | Teacher Launches Meeting | Provider `create` called; status transitions to `RUNNING` | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-03** | Teacher Joins as Moderator | Signed join URL returned with `MODERATOR` role | `test_virtual_classroom_full_lifecycle_and_join_authorization` | **[SOFTWARE VERIFIED]** |
| **UAT-04** | Enrolled Student Joins | Signed join URL returned with `VIEWER` role | `test_virtual_classroom_full_lifecycle_and_join_authorization` | **[SOFTWARE VERIFIED]** |
| **UAT-05** | Unauthorized Student Join Attempt | Blocked with HTTP 403 (`UNAUTHORIZED_MEETING_ACCESS`) | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-06** | Unauthorized Student Error Payload | JSON error code `UNAUTHORIZED_MEETING_ACCESS` with correlation ID | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-07** | Cross-Tenant Classroom Access | Returns HTTP 404 (`VIRTUAL_CLASSROOM_NOT_FOUND`) Blind 404 barrier | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-08** | Teacher Attendance Logging | `MeetingAttendance` record created with `joined_at` timestamp | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-09** | Student Attendance Logging | `MeetingAttendance` record created with `joined_at` timestamp | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-10** | Leave Timestamp Recorded | `/leave` endpoint records `left_at` timestamp | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-11** | Attendance Duration Calculation | `duration_seconds` calculated accurately as integer seconds | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-12** | Teacher Terminates Meeting | Provider `end` called; status transitions to `ENDED` | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-13** | Automatic Attendance Finalization | Open attendance records safely closed upon meeting termination | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-14** | Recording Processing Discovery | Ingestion endpoint polls provider and discovers new recording | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |
| **UAT-15** | Recording Synchronization | New `MeetingRecording` rows inserted into database with playback URLs | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |
| **UAT-16** | Unpublished Recording Privacy | Unpublished recordings strictly excluded from student queries | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |
| **UAT-17** | Staff Publishes Recording | `PATCH /publish` sets `is_published = True`; audit event logged | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |
| **UAT-18** | Student Visibility Post-Publish | Enrolled students can query and view published recording assets | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |
| **UAT-19** | Cross-Tenant Recording Isolation | Cross-tenant recording queries return HTTP 404 (Blind 404) | `test_complete_e2e_virtual_classroom_lifecycle` | **[SOFTWARE VERIFIED]** |
| **UAT-20** | Tenant-Scoped Recording Deletion | Staff can delete recordings; cross-tenant deletion returns 404 | `test_recordings_api_sync_publish_and_permissions` | **[SOFTWARE VERIFIED]** |

---

## 3. Physical Device & Media Transport Tests (`UAT-Physical-01` to `UAT-Physical-10`)

| Test ID | Physical Test Target | Test Hardware / Environment | Operational Status | Execution Prerequisite |
| :--- | :--- | :--- | :--- | :--- |
| **UAT-Phys-01** | Teacher Microphone Audio | Windows / macOS Laptop + Headset | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-02** | Teacher Webcam Broadcast | 720p / 1080p Integrated Camera | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-03** | Teacher Screen Sharing | Chrome / Firefox Desktop Browser | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-04** | Student Listen-Only Audio | Android / iOS / Laptop Speakers | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-05** | Student Microphone Speech | Mobile / Earbud Microphone | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-06** | Student Webcam Broadcast | Smartphone / Tablet Front Camera | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-07** | Interactive Whiteboard | Multi-user touch and stylus drawing | **[REQUIRES PHYSICAL UAT]** | Deploy physical BBB server cluster |
| **UAT-Phys-08** | Rural CGNAT Firewall Relay | School network behind restrictive NAT | **[REQUIRES PHYSICAL UAT]** | Deploy Coturn TURN on port 443 |
| **UAT-Phys-09** | Cellular 4G / 5G Connection | Mobile Network Operator SIM | **[REQUIRES PHYSICAL UAT]** | Conduct testing on live cellular carrier |
| **UAT-Phys-10** | Session Auto-Reconnection | Temporary network interruption (10s) | **[REQUIRES PHYSICAL UAT]** | Simulate Wi-Fi toggle during meeting |
