# PEvN — Phase 11: User Lifecycle Validation Matrix

**Date**: 2026-08-29  
**Audit Scope**: Validation of complete lifecycles for critical institutional actor profiles: Rector, Teacher, Student, and Guardian.

---

## 1. Rector Onboarding Lifecycle

| Step | Operation / Action | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Invitation Generation** | Superadmin triggers `POST /api/v1/institutions/{id}/rector-invitation` | 201 Created with onboarding token | Token generated, invitation saved with timestamps | **PASS** |
| **2. Token Acceptance** | Rector candidate submits `POST /api/v1/auth/rector-onboarding` | 200 OK, User account created with `rector` role | User account activated with Dane alignment | **PASS** |
| **3. Succession Safety** | Attempt to create overlapping active rector | 400 Bad Request / Succession rules enforced | Blocked unless previous rector explicitly revoked | **PASS** |
| **4. First Authentication** | Rector authenticates via `/api/v1/auth/login` | 200 OK + HttpOnly cookie + JWT | Auth OK, scope bound to target institution | **PASS** |

---

## 2. Teacher Creation Lifecycle

| Step | Operation / Action | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Malformed UUID Protection** | Frontend / API client sends `"8788"` string | 422 Unprocessable Content | Client validation + Pydantic schema rejection | **PASS** |
| **2. Nonexistent User Handling** | Valid UUID not existing in database | 403 / 404 Privacy Boundary | Prevented cross-tenant probing & enumeration | **PASS** |
| **3. Cross-Tenant Containment** | User belonging to Inst B submitted to Inst A | 403 CROSS_TENANT_MISMATCH | Strictly rejected by `TeacherService` | **PASS** |
| **4. Valid Teacher Creation** | User belonging to Inst A submitted by Rector A | 201 Created | Teacher profile created, linked to User | **PASS** |
| **5. Duplicate Rejection** | Re-submitting existing Teacher User ID | 400 Bad Request | Unique constraint enforced | **PASS** |
| **6. Teacher Login & Scope** | Teacher logs in and calls `/api/v1/auth/me` | 200 OK, `roles=['teacher']` | Scoped to Institution A | **PASS** |

---

## 3. Student Creation & SIMAT Lifecycle

| Step | Operation / Action | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Profile Creation** | Rector/Coordinator submits `POST /api/v1/students` | 201 Created with SIMAT & inclusion data | Profile created and linked to institution | **PASS** |
| **2. Duplicate SIMAT Code** | Attempt to register duplicate SIMAT code | 400 / 403 Duplicate rejection | Rejected by unique constraints / domain service | **PASS** |
| **3. Student Query** | Query `GET /api/v1/students/{id}` with tenant token | 200 OK | Student detail returned with User and metadata | **PASS** |

---

## 4. Guardian Registration & Student Linking Lifecycle

| Step | Operation / Action | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Civil Profile Creation** | Submits `POST /api/v1/guardians` with civil identity | 201 Created | Guardian profile created per [OPEN-DECISION-3A-01] | **PASS** |
| **2. Student Association** | Submits `POST /api/v1/guardians/{gid}/students/{sid}` | 201 Created | Relationship linked (relationship_type, pickup) | **PASS** |
| **3. Verification Query** | Submits `GET /api/v1/students/{sid}/guardians` | 200 OK | Associated guardians listed with contact flags | **PASS** |

---

## Overall Lifecycle Verdict: PASS
