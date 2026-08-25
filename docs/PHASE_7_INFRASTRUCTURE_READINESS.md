# PHASE 7 — INFRASTRUCTURE READINESS ASSESSMENT
## Virtual Classrooms & Real-Time Meeting Delivery

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Operational Infrastructure, Network Topology & Provider Governance  
**Status:** INFRASTRUCTURE SPECIFICATION COMPLETE & COMMISSIONING READY  
**Phase:** Phase 7 Final Commissioning  
**Date:** 2026-08-23  

---

## 1. Objective & Infrastructure Readiness Framework

This document defines the operational readiness assessment for deploying and commissioning the Plataforma Educativa Virtual Nacional (PEVN) Virtual Classroom subsystem against external BigBlueButton (BBB) and WebRTC streaming infrastructure.

To ensure transparent operational governance, every infrastructure component is evaluated across explicit readiness criteria without fabricating external connectivity.

---

## 2. Infrastructure Readiness Matrix

| Component | Technical Specification / Requirement | Available in Repo / Local Env | Verified by Automated Tests | Operational Status | Verification Evidence / Prerequisite |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PEVN Backend API Gateway** | FastAPI, Python 3.12+, AsyncPG, Pydantic v2 | **YES** (`backend/`) | **YES** (109/109 Pytest) | **READY** | Unit, integration, and E2E test suites pass with 0 errors. |
| **PEVN Frontend SPA** | React 18, Vite, TypeScript, PWA Service Worker | **YES** (`frontend/`) | **YES** (25/25 Vitest) | **READY** | Strict typecheck, linting, and production bundling verified. |
| **PostgreSQL 16 Database** | Multi-tenant schema, UUID keys, FK indexes | **YES** (`docker-compose.yml`, Alembic) | **YES** (Alembic migration) | **READY** | Schema migration `20260823_0001_phase4_virtual_classrooms.py` validated. |
| **Redis 7 Cache / Rate Limiting** | Key-value store, distributed locks, rate limiting | **YES** (`docker-compose.yml`) | **YES** (Rate limiter tests) | **READY** | Rate limiter tests (`test_rate_limiter.py`) validated. |
| **BBB Adapter Protocol Client** | SHA-1 / SHA-256 signing, XML response parser | **YES** (`backend/app/core/meeting/`) | **YES** (Adapter unit tests) | **READY** | Deterministic checksum tests and error translation verified. |
| **BigBlueButton Physical Server** | Dedicated Ubuntu 22.04 LTS, BBB v2.7+ / v3.0+ | **NO** (Requires External Target) | **NO** (Physical cluster) | **PENDING COMMISSIONING** | Requires provisioning live server/cluster with FQDN & HTTPS. |
| **Coturn STUN / TURN Server** | WebRTC NAT traversal, TCP port 443 / UDP 3478 | **NO** (Requires External Target) | **NO** (Physical network) | **PENDING COMMISSIONING** | Required for rural / restrictive CGNAT institutional firewalls. |
| **Scalelite Load Balancer** | Horizontal cluster balancer (50+ concurrent rooms) | **NO** (Optional at launch) | **NO** (Physical cluster) | **OPTIONAL AT INITIAL LAUNCH** | Required when concurrent classroom count exceeds single-node capacity. |
| **Public DNS & TLS Certificates** | Let's Encrypt / DigiCert FQDN certificates | **NO** (Deployment dependent) | **NO** (DNS records) | **PENDING DEPLOYMENT** | Requires DNS A/AAAA records for `api.pevn.gov.co` and `bbb.pevn.gov.co`. |

---

## 3. Environment Variable Configuration & Secret Governance

| Variable | Scope | Purpose | Staging / Production Value Policy |
| :--- | :--- | :--- | :--- |
| `MEETING_PROVIDER_TYPE` | Backend | Provider selection | Set to `bbb` in staging and production (`mock` in offline test runners). |
| `BBB_API_URL` | Backend | BigBlueButton API base URL | Must point to HTTPS endpoint (e.g. `https://bbb-staging.pevn.gov.co/bigbluebutton/api`). |
| `BBB_SHARED_SECRET` | Backend | Secret salt for cryptographic signing | **CRITICAL:** Provisioned via HashiCorp Vault or AWS Secrets Manager. Never in git. |
| `BBB_SIGNING_ALGORITHM` | Backend | Checksum algorithm | Set to `sha256` (or `sha1`). |
| `BBB_TIMEOUT_SECONDS` | Backend | Provider request timeout | Set to `10.0` (standard) or `15.0` (high-latency regions). |
| `CORS_ORIGINS` | Backend | Allowed browser origins | Exact frontend origin URL (e.g. `https://app.pevn.gov.co`). |
| `ALLOWED_HOSTS` | Backend | Host header whitelist | Exact API host header (e.g. `api.pevn.gov.co`). |

---

## 4. Hardware Sizing & Network Capacity Guidelines

### BigBlueButton Node Capacity Baseline (Single Server)
- **Recommended Hardware:** 16 vCPU, 32 GB RAM, 500 GB NVMe SSD, 1 Gbps dedicated uplink.
- **Recommended Concurrency:** 25–35 simultaneous active classrooms (max 800–1,000 active audio/video participants per physical node).
- **Multi-Node Cluster Scaling:** For 100+ concurrent classrooms (e.g. national peak hours), deploy 4–6 BigBlueButton worker nodes managed behind a Scalelite load balancer.

### Bandwidth Estimations
- **Audio Only (Listen Only / Mic):** ~40 kbps per participant.
- **Webcam (SD 480p @ 15fps):** ~250–350 kbps per active broadcaster.
- **Screen Sharing (1080p @ 5fps):** ~500–800 kbps per presenter.
- **Total School Uplink Requirement (Per Class of 35 Students):** ~10–15 Mbps downstream, ~2 Mbps upstream.
