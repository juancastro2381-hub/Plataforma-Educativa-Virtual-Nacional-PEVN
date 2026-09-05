# PEvN — Phase 11: Real-World Role Acceptance Matrix

**Date**: 2026-08-29  
**Audit Scope**: Acceptance verification of all 11 canonical roles across Authentication, Session Restoration, Refresh Rotation, Positive Domain Operations, Negative Security Gates, and Tenant Isolation.

---

## Canonical Role Acceptance Verification

| # | Canonical Role | Hierarchy Level | Authentication & Session (/auth/me) | Positive Authorized Operations | Negative Security Gate (Blocked) | Tenant Containment | Final Role Verdict |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | `superadmin` | Level 1 (National) | **PASS** (Login=200, Scope: `is_national=True`) | `GET /api/v1/institutions` (200 OK) | N/A (Root Administrator) | Cross-institution global access | **PASS** |
| **2** | `national_admin` | Level 2 (National) | **PASS** (Login=200, Scope: `is_national=True`) | `GET /api/v1/institutions` (200 OK) | `POST /teachers` without tenant (Blocked) | Cross-institution national scope | **PASS** |
| **3** | `department_admin` | Level 3 (Territorial) | **PASS** (Login=200, Scope: Department) | `GET /api/v1/analytics/territorial/summary` (200 OK) | `POST /api/v1/teachers` (403 Forbidden) | Confined to Department | **PASS** |
| **4** | `municipality_admin` | Level 4 (Territorial) | **PASS** (Login=200, Scope: Municipality) | `GET /api/v1/analytics/territorial/summary` (200 OK) | `POST /api/v1/teachers` (403 Forbidden) | Confined to Municipality | **PASS** |
| **5** | `rector` | Level 5 (Institutional) | **PASS** (Login=200, Scope: Institution A) | `POST /api/v1/academic-years` (201 Created), `POST /teachers` (201) | `POST /api/v1/institutions` (403 Forbidden) | Confined to Inst A (Inst B -> 403) | **PASS** |
| **6** | `institution_admin` | Level 6 (Institutional) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/groups` (200 OK) | `POST /api/v1/institutions` (403 Forbidden) | Confined to Inst A (Inst B -> 403) | **PASS** |
| **7** | `coordinator` | Level 7 (Campus) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/students` (200 OK) | `POST /rector-invitation` (403 Forbidden) | Confined to Inst A | **PASS** |
| **8** | `academic_coordinator` | Level 8 (Campus) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/academic-assignments` (200 OK) | `POST /rector-invitation` (403 Forbidden) | Confined to Inst A | **PASS** |
| **9** | `teacher` | Level 9 (Classroom) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/virtual-classrooms` (200 OK) | `POST /api/v1/teachers` (403 Forbidden) | Confined to Inst A | **PASS** |
| **10** | `student` | Level 10 (Individual) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/virtual-classrooms` (200 OK) | `POST /api/v1/teachers` (403 Forbidden) | Confined to Inst A | **PASS** |
| **11** | `guardian` | Level 11 (Individual) | **PASS** (Login=200, Scope: Institution A) | `GET /api/v1/auth/me` (200 OK) | `POST /api/v1/academic-years` (403 Forbidden) | Confined to Inst A | **PASS** |

---

## Summary Verdict

- Total Canonical Roles Audited: **11**
- Total Canonical Roles Accepted: **11**
- Acceptance Rate: **100%**
- Real-World Role Acceptance Verdict: **PASS**
