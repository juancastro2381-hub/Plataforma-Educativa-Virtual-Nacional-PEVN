# PHASE 5 — BIGBLUEBUTTON STAGING VALIDATION PLAN
## Virtual Classrooms & Real-Time Meeting Delivery

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** External Meeting Provider Integration & Production Readiness  
**Status:** STAGING VALIDATION PLAN SPECIFICATION  
**Phase:** Phase 5 Initiation  
**Date:** 2026-08-23  

---

## 1. Executive Objective & Strategy

The objective of Phase 5 is to validate the already-implemented, verified, and frozen Phase 4 Virtual Classroom subsystem against BigBlueButton (BBB) staging environments and define the operational criteria for production readiness.

### Core Strategy
1. **Zero Architecture Drift:** No changes to Phase 3B or Phase 4 domain logic, database models, REST contracts, or security invariants.
2. **Provider Abstraction Integrity:** Validation operates exclusively through `IMeetingProvider` and `BBBAdapter`. REST controllers and frontend views remain decoupled from direct provider APIs.
3. **Defense-in-Depth Verification:** Multi-tenant isolation (Blind 404), SIMAT active enrollment gating, cryptographic checksum signing, zero-secret disclosure, and telemetry accuracy must hold under staging conditions.
4. **Distinction of Status:** Explicitly distinguish automated integration testing completed within the software harness from physical post-deployment staging cluster commissioning.

---

## 2. Staging Architecture & Environment Configuration

```
+-----------------------------------------------------------------------------------+
|                        PEVN STAGING ENVIRONMENT TOPOLOGY                          |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Frontend SPA (Vite / React 18) ]                                                |
|             │                                                                     |
|             │ HTTPS (JWT Bearer Auth)                                             |
|             ▼                                                                     |
|  [ PEVN Backend API Gateway (FastAPI + AsyncPG) ]                                 |
|             │                                                                     |
|             │ Internal Domain Services & Meeting Provider Factory                 |
|             ▼                                                                     |
|  [ BBBAdapter (SHA-1 / SHA-256 Checksum Engine) ]                                 |
|             │                                                                     |
|             │ Signed REST API Requests (HTTPS)                                    |
|             ▼                                                                     |
|  [ BigBlueButton Staging Server Cluster (v2.7+ / v3.0+) ]                          |
|    - NGINX Web Gateway                                                            |
|    - BBB Web / Akka Apps (Meeting Lifecycle Engine)                               |
|    - FreeSWITCH & Kurento/mediasoup (Audio/Video WebRTC Media Server)             |
|    - Scalelite Load Balancer (Optional Staging Cluster Frontend)                   |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Staging Environment Variables (`.env.staging`)
| Variable | Description | Example / Staging Format |
| :--- | :--- | :--- |
| `MEETING_PROVIDER_TYPE` | Active provider implementation | `bbb` |
| `BBB_API_URL` | Base BigBlueButton REST API endpoint | `https://bbb-staging.pevn.gov.co/bigbluebutton/api` |
| `BBB_SHARED_SECRET` | Cryptographic secret salt for request signing | `[SECURE_STAGING_SALT_MANAGED_IN_VAULT]` |
| `BBB_SIGNING_ALGORITHM` | Hashing algorithm for query verification | `sha256` (or `sha1`) |
| `BBB_TIMEOUT_SECONDS` | Network timeout for provider HTTP calls | `10.0` |

> [!CAUTION]
> **Secret Non-Disclosure Rule:** `BBB_SHARED_SECRET` must NEVER be committed to version control, exposed in client-side bundles, or returned in API response bodies. In production and staging, it is provisioned via encrypted environment variables or HashiCorp Vault.

---

## 3. Scope of Staging Validation

The staging validation encompasses 20 mandatory validation areas:

1. **Provider Connectivity & Handshake:** Network latency, TLS certificate validation, endpoint accessibility.
2. **Cryptographic Checksum Verification:** Validation of query string ordering, URL parameter escaping, and hash matching against BBB server secret.
3. **Meeting Provisioning (`create`):** Room instantiation, lock settings, breakout room configuration, max participant enforcement.
4. **Host / Moderator Join (`join`):** Moderator password verification, user role assignment, signed redirect URL generation.
5. **Student / Viewer Join (`join`):** SIMAT enrollment verification, viewer password resolution, safe client browser redirection (`noopener,noreferrer`).
6. **SIMAT Enrollment Authorization:** Rejection of students not actively enrolled in the assigned group (HTTP 403 `UNAUTHORIZED_MEETING_ACCESS`).
7. **Multi-Tenant Isolation (Blind 404):** Rejection of cross-tenant resource lookups with HTTP 404, strictly preventing tenant enumeration.
8. **Real-Time Attendance Telemetry:** Exact `joined_at` and `left_at` timestamp capture, duration computation in seconds.
9. **Meeting Termination (`end`):** Host-initiated room closure, BigBlueButton session termination, automatic closure of all open attendance records.
10. **Recording Ingestion & Synchronization (`getRecordings`):** Polling and webhook-based ingestion of processed meeting playback URLs and duration metrics.
11. **Recording Publication Visibility:** Gating recordings by publication flag (`is_published`), ensuring students only view approved materials.
12. **Recording Deletion:** Deletion of recording metadata within tenant scope.
13. **Provider Error Mapping:** Graceful translation of BBB XML error codes (`checksumError`, `notFound`, `invalidSecret`, `maxParticipantsReached`) to domain exceptions.
14. **Network & Timeout Resilience:** Handling HTTP 502/504 gateway errors and provider socket timeouts without corrupting transaction state.
15. **Secret Concealment:** Guaranteeing zero leakage of passwords, Argon2 hashes, or provider salts in API responses.
16. **Idempotent Operations:** Re-running launch, end, sync, and publish operations without creating orphaned records or duplicate state.
17. **Audit Event Logging:** Emitting and persisting `MEETING_LAUNCHED`, `MEETING_JOINED`, `RECORDING_SYNCED`, and `RECORDING_PUBLISHED` events.
18. **REST API Contract Adherence:** Strict validation against Pydantic schemas and OpenAPI v3 specifications.
19. **Frontend User Experience:** Smooth rendering, loading states, accessible modal workflows, and responsive status pills.
20. **Regression Preservation:** Ensuring 100% pass rates across all Phase 1–4 test suites.

---

## 4. Execution Methodology & Acceptance Criteria

### Automated Test Harness Verification
- Unit & integration tests validate `BBBAdapter` parameter generation, SHA-1/SHA-256 calculation, and XML response parsing using simulated HTTP transport fixtures.
- End-to-end multi-tenant suites validate the complete chain across database, domain services, controllers, and frontend.

### Staging Verification Gate
- To achieve formal production readiness, all 20 test areas must pass without defects, with zero regressions in the baseline test suite.
