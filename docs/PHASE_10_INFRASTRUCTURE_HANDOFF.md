# PHASE 10 — INFRASTRUCTURE HANDOFF & OPERATIONAL COMMISSIONING PACKAGE
## Virtual Classrooms & BigBlueButton Subsystem Production Deployment

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** External Infrastructure Deployment, BigBlueButton Commissioning & Real-World UAT  
**Status:** IMPLEMENTATION-READY INFRASTRUCTURE HANDOFF PACKAGE  
**Software Baseline:** FROZEN & VERIFIED (109/109 Backend Pytest PASS, 25/25 Frontend Vitest PASS)  
**Classification:** `[B] PRODUCTION READY — EXTERNAL COMMISSIONING PENDING`  
**Date:** 2026-08-23  

---

## 1. Required Infrastructure

### A. BigBlueButton Server
- **Operating System:** Ubuntu 22.04 LTS (x86_64, clean base installation, no conflicting services on ports 80/443).
- **Compute Recommendations (Single Node Baseline):**
  - **CPU:** 16 vCPU (or 8 physical cores with multi-threading).
  - **RAM:** 32 GB memory (minimum 16 GB for testing, 32 GB recommended for 25+ concurrent rooms).
  - **Disk Storage:** 500 GB NVMe SSD (high IOPS required for concurrent recording ingestion and FreeSWITCH audio mixing).
  - **Swap:** 8 GB swap partition configured on SSD.
- **Network Interface:** 1 Gbps dedicated full-duplex network uplink with static public IPv4 address.
- **Domain & FQDN:** Dedicated public hostname (e.g. `bbb.pevn.gov.co` or `bbb-staging.pevn.gov.co`).
- **Software Version:** BigBlueButton v2.7.x or v3.0.x (latest stable release).

### B. Coturn STUN / TURN Server
- **Compute:** 4 vCPU, 8 GB RAM, 50 GB SSD (can be co-located on the BBB node for initial launch or deployed as a standalone relay cluster).
- **Public Network:** Dedicated public IPv4 address with direct internet routing (no NAT in front of Coturn server).
- **Domain & FQDN:** Dedicated hostname (e.g. `turn.pevn.gov.co`).
- **Network Ports:** TCP port 443 (for TLS TURN relay) and UDP port 3478 (for STUN).

### C. DNS & TLS/HTTPS
- **DNS Records:** Valid `A` records pointing to public IPv4 addresses of BBB and Coturn servers.
- **TLS Certificates:** Valid SSL/TLS certificates issued by a trusted Certificate Authority (Let's Encrypt / DigiCert) covering:
  - `https://bbb.pevn.gov.co`
  - `https://turn.pevn.gov.co`
  - `https://api.pevn.gov.co`
  - `https://app.pevn.gov.co`

---

## 2. PEVN → BigBlueButton Integration Specification

### A. Expected API Endpoint Format
The PEVN backend (`BBBAdapter`) expects the standard BigBlueButton API base URL ending with `/bigbluebutton/api` (without trailing slash):
$$\text{BBB\_API\_URL} = \text{https://<BBB\_HOST>/bigbluebutton/api}$$

Example: `https://bbb.pevn.gov.co/bigbluebutton/api`

### B. Environment Variables Matrix
| Variable Name | Description | Source / Ownership | Current Value Policy |
| :--- | :--- | :--- | :--- |
| `MEETING_PROVIDER_TYPE` | Active provider selection (`mock` or `bbb`) | Configured in repo / `.env` | Set to `bbb` in staging and production. |
| `BBB_API_URL` | Base BigBlueButton REST API URL | **Must be supplied by Infrastructure Admin** | Target HTTPS endpoint of the deployed server. |
| `BBB_SHARED_SECRET` | Secret security salt for HMAC checksums | **Must be supplied by Infrastructure Admin** | Extracted via `sudo bbb-conf --secret` on the BBB host. |
| `BBB_SIGNING_ALGORITHM` | Cryptographic signature algorithm (`sha1` or `sha256`) | Configured in repo / `.env` | Default is `sha256` (matches BBB standard). |
| `BBB_TIMEOUT_SECONDS` | HTTP request timeout for provider calls | Configured in repo / `.env` | Default is `10.0` seconds. |
| `DATABASE_URL` | PostgreSQL 16 connection string | Infrastructure Admin | Staging/Production PostgreSQL database cluster. |
| `REDIS_URL` | Redis 7 connection string | Infrastructure Admin | Staging/Production Redis cluster for rate limiting. |
| `CORS_ORIGINS` | Whitelist of allowed browser origins | Infrastructure Admin | Comma-separated list (e.g. `https://app.pevn.gov.co`). |
| `ALLOWED_HOSTS` | Whitelist of allowed HTTP Host headers | Infrastructure Admin | Comma-separated list (e.g. `api.pevn.gov.co`). |

---

## 3. Credential & Secret Handling Policy

> [!CAUTION]
> **CRITICAL SECRET GOVERNANCE RULES:**
> 1. **Zero Secret Leakage:** `BBB_SHARED_SECRET`, database passwords, and JWT secret keys must NEVER be committed to version control, pasted into issue trackers, or exposed in frontend JavaScript bundles.
> 2. **Runtime Secret Injection:** Inject `BBB_SHARED_SECRET` into container environments exclusively via HashiCorp Vault, AWS Secrets Manager, Kubernetes Secrets, or encrypted environment files (`.env.production`).
> 3. **Memory Protection:** The application explicitly redacts the secret in memory strings (`BBBAdapter.__repr__()` outputs `secret='[PROTECTED]'`).
> 4. **No Fake Secrets:** Do not generate or use fake production credentials.

---

## 4. DNS & TLS Configuration

### A. Required DNS Records
| Record Type | Hostname / FQDN | Value / Target | Purpose |
| :--- | :--- | :--- | :--- |
| `A` | `bbb.pevn.gov.co` | `[PUBLIC_IP_BBB_SERVER]` | BigBlueButton Web, NGINX, and API gateway |
| `A` | `turn.pevn.gov.co` | `[PUBLIC_IP_COTURN_SERVER]` | Coturn STUN and WebRTC TURN TLS relay |
| `A` | `api.pevn.gov.co` | `[PUBLIC_IP_PEVN_BACKEND]` | PEVN FastAPI REST API gateway |
| `A` | `app.pevn.gov.co` | `[PUBLIC_IP_PEVN_FRONTEND]` | PEVN React 18 Frontend SPA |

### B. TLS Certificate Validation Commands
```bash
# Verify BigBlueButton TLS Certificate
curl -Iv https://bbb.pevn.gov.co/bigbluebutton/api

# Detailed OpenSSL Handshake Inspection
openssl s_client -connect bbb.pevn.gov.co:443 -servername bbb.pevn.gov.co -tls1_3
```
*Expected Result:* `Verify return code: 0 (ok)`, HTTP status 200/302, valid certificate chain.

---

## 5. Firewall & Network Port Matrix

| Source | Destination | Protocol | Port / Range | Direction | Purpose | Required / Optional |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Internet Clients** | BigBlueButton Node | `TCP` | `80` | Inbound | HTTP to HTTPS redirect / ACME challenges | **REQUIRED** |
| **Internet Clients** | BigBlueButton Node | `TCP` | `443` | Inbound | HTTPS Web, API, WebSocket signaling (WSS) | **REQUIRED** |
| **Internet Clients** | Coturn Server | `UDP` | `3478` | Inbound | STUN server binding requests | **REQUIRED** |
| **Internet Clients** | Coturn Server | `TCP` | `443` | Inbound | TURN over TLS (CGNAT firewall bypass) | **REQUIRED** |
| **Internet Clients** | BigBlueButton Node | `UDP` | `16384–32768` | Inbound | WebRTC RTP audio, video, screen share streams | **REQUIRED** |
| **PEVN Backend** | BigBlueButton Node | `TCP` | `443` | Outbound | Signed REST API requests (`create`, `join`, `end`) | **REQUIRED** |
| **BigBlueButton Node**| Coturn Server | `UDP` | `49152–65535` | Bi-directional | Internal media relay allocations | **REQUIRED** |
| **Prometheus Exporter**| BigBlueButton Node | `TCP` | `9688` | Inbound | BBB metrics scraping (Private network only) | *OPTIONAL* |

---

## 6. BigBlueButton Server Validation Commands

Execute on the physical BigBlueButton Ubuntu 22.04 LTS host:

```bash
# 1. Complete System Configuration & Health Audit
sudo bbb-conf --check

# 2. Extract API Endpoint URL and Secret Salt (Mask in reports)
sudo bbb-conf --secret

# 3. Inspect Systemd Service Daemons
sudo systemctl status bbb-web
sudo systemctl status nginx
sudo systemctl status freeswitch
sudo systemctl status bbb-webrtc-sfu

# 4. Clean Service Restart
sudo bbb-conf --restart

# 5. Live Log Telemetry Stream
sudo bbb-conf --watch
```

---

## 7. Coturn STUN/TURN Validation Commands

Execute on the Coturn host / external network client:

```bash
# 1. Check Coturn Service Status
sudo systemctl status coturn

# 2. Verify Port Listening State
sudo netstat -tulpn | grep -E '3478|443'

# 3. Test External Relay Allocation
turnutils_uclient -v -t -u [USERNAME] -w [PASSWORD] -p 443 turn.pevn.gov.co
```
*Expected Result:* `Total allocation success count: 100%, 0 failures`.

---

## 8. Live End-to-End Commissioning Sequence

```
1. Infrastructure Provisioning
   - Deploy Ubuntu 22.04 LTS host (16 vCPU, 32GB RAM, 500GB NVMe SSD).
   - Configure public IPv4 and firewall security groups per Port Matrix.
   ↓
2. DNS Configuration
   - Register A records for bbb.pevn.gov.co and turn.pevn.gov.co.
   ↓
3. TLS Certificate Issuance
   - Issue Let's Encrypt / DigiCert certificates for all FQDNs.
   ↓
4. BigBlueButton Installation
   - Execute official automated installer:
     wget -qO- https://ubuntu.bigbluebutton.org/bbb-install-2.7.sh | bash -s -- -v focal-270 -s bbb.pevn.gov.co -e devops@pevn.gov.co -a
   ↓
5. BigBlueButton Health Audit
   - Run sudo bbb-conf --check (Verify zero configuration errors).
   ↓
6. Coturn Deployment & Integration
   - Install Coturn and configure turnserver.conf on TCP port 443.
   - Bind Coturn into /etc/bigbluebutton/turn-stun-servers.xml.
   ↓
7. Secret Extraction & PEVN Injection
   - Run sudo bbb-conf --secret to extract shared security salt.
   - Inject BBB_SHARED_SECRET and BBB_API_URL into PEVN backend environment via Vault.
   - Restart PEVN backend: docker compose restart backend.
   ↓
8. API Connectivity Validation
   - Verify PEVN backend initializes BBBAdapter and communicates with BBB API.
   ↓
9. Teacher / Host Meeting Creation & Launch
   - Teacher schedules virtual classroom in PEVN UI and clicks "Iniciar Clase".
   - Verify room instantiates on BBB server; status transitions to RUNNING.
   ↓
10. Teacher Moderator Join
    - Teacher clicks "Unirse a la Clase"; verifies MODERATOR role and signed entry.
    ↓
11. Enrolled Student Viewer Join
    - Active SIMAT enrolled student enters; verifies VIEWER role and signed entry.
    ↓
12. Real Audiovisual Media Verification (UAT-Physical-01 to 10)
    - Test microphone, webcam, speaker audio, screen sharing, and mobile responsiveness.
    ↓
13. Attendance Telemetry Validation
    - Verify joined_at, left_at, and duration_seconds logged accurately in PostgreSQL.
    ↓
14. Meeting Termination & Automatic Closure
    - Teacher clicks "Finalizar Clase"; verify meeting terminates on BBB and open attendances close.
    ↓
15. Recording Synchronization & Privacy Gating
    - Sync processed recordings; verify unpublished recordings remain hidden from students.
    - Publish recording; verify students can access playback link.
    ↓
16. Unauthorized Access & Multi-Tenant Negative Tests
    - Verify unenrolled student receives HTTP 403 (UNAUTHORIZED_MEETING_ACCESS).
    - Verify cross-tenant requests receive HTTP 404 (Blind 404 barrier).
    ↓
17. Final Operational Production Certification
    - Transition certification status to [A] PRODUCTION CERTIFIED — LIVE E2E VERIFIED.
```

---

## 9. Real-World User Acceptance Testing Matrix (UAT-Physical-01 to 10)

| Test ID | Objective | Preconditions | Exact Execution Steps | Expected Result | Evidence Required | PASS/FAIL Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-Phys-01** | **Teacher Microphone Audio** | Teacher logged into PEVN; Desktop with headset mic | 1. Teacher launches and enters room.<br>2. Selects "Microphone" in audio modal.<br>3. Completes echo test and speaks. | Audio stream connects via FreeSWITCH; voice is audible to all participants with clear quality. | Participant audio confirmation / recording audio check | Voice clear, RTT < 200ms, zero echo |
| **UAT-Phys-02** | **Teacher Webcam Video** | Teacher joined meeting; 720p/1080p webcam connected | 1. Teacher clicks "Share Webcam".<br>2. Selects camera and Medium/High quality.<br>3. Clicks "Start Sharing". | Video stream renders in BigBlueButton video grid; frame rate is stable (>15 fps). | Video tile visible in participant view | Video renders, no freeze, lip-sync intact |
| **UAT-Phys-03** | **Teacher Screen Sharing** | Chrome/Firefox/Edge on Desktop | 1. Teacher clicks "Share Screen".<br>2. Selects entire screen / browser tab.<br>3. Navigates between slides/content. | Screen sharing broadcasts to all students with high clarity and low latency (<1s). | Shared screen renders in student view | Text legible, resolution $\ge$ 1080p, latency < 1s |
| **UAT-Phys-04** | **Student Listen-Only Audio** | Student logged into PEVN; headphones connected | 1. Student joins active classroom.<br>2. Selects "Listen Only" mode in audio modal. | Student hears teacher voice immediately without needing microphone permission. | Student audio confirmation | Instant audio, zero clipping, no echo |
| **UAT-Phys-05** | **Student Microphone Participation** | Student in active meeting; microphone connected | 1. Student switches from Listen-Only to Microphone.<br>2. Completes echo test and speaks question. | Student voice is audible to teacher and peers; echo cancellation operates. | Two-way verbal interaction check | Two-way audio clear, echo cancelled |
| **UAT-Phys-06** | **Student Video Reception & Grid** | Student on desktop / mobile | 1. Student observes video area while multiple participants enable cameras. | Adaptive video grid dynamically adjusts layout; video streams scale smoothly. | Multi-tile video layout verified | All video tiles render without crashing |
| **UAT-Phys-07** | **Interactive Whiteboard & Chat** | Teacher & student connected | 1. Teacher turns on multi-user whiteboard.<br>2. Student draws and writes public chat message. | Whiteboard strokes and chat messages synchronize across clients in real time (<200ms). | Real-time chat & drawing verified | Real-time sync, zero message loss |
| **UAT-Phys-08** | **Restrictive CGNAT Traversal** | Student connecting from restrictive school network | 1. Student joins meeting from restrictive network.<br>2. Browser initiates WebRTC negotiation. | Coturn TURN relay over TCP port 443 allocates stream; media connects without 1007/1020 errors. | ICE candidate log showing `relay` candidate | Connection succeeds via TURN TLS relay |
| **UAT-Phys-09** | **Mobile Browser Usability** | Student on Android (Chrome) / iOS (Safari) | 1. Student logs into PEVN on mobile device.<br>2. Clicks "Unirse a la Clase" and opens BBB interface. | Mobile viewport adapts responsively; touch controls, audio, and slides operate smoothly. | Mobile screenshot / screen recording | Responsive layout, touch controls work |
| **UAT-Phys-10** | **Network Disconnect & Reconnect**| Participant in active session | 1. Disconnect network for 5–10 seconds.<br>2. Re-enable network connection. | BBB auto-reconnects session; PEVN attendance preserves original join record without duration corruption. | Telemetry inspection in database | Auto-reconnects, attendance continuous |

---

## 10. Failure Conditions Matrix

The operational commissioning must be declared **FAILED / BLOCKED** if any of the following conditions occur:

1. **BBB API Checksum Failure:** API requests return `<messageKey>checksumError</messageKey>` due to shared salt mismatch.
2. **TLS / HTTPS Failure:** SSL handshake fails, certificate is expired, or self-signed certificate causes browser WebRTC media blocks.
3. **DNS Resolution Failure:** FQDN does not resolve to the public IP address of the BigBlueButton host.
4. **Meeting Creation Failure:** Provider returns `<returncode>FAILED</returncode>` during room provisioning.
5. **Moderator Join Failure:** Teacher cannot obtain `MODERATOR` access or signed URL redirect fails.
6. **Student Join Failure:** Actively enrolled student cannot obtain `VIEWER` access or signed URL redirect fails.
7. **Microphone Failure:** Audio cannot be established due to FreeSWITCH crash or UDP port blocking.
8. **Camera Failure:** Webcam streams fail to negotiate or display in video grid due to mediasoup/Kurento SFU failure.
9. **Screen Sharing Failure:** Screen sharing fails to broadcast or disconnects immediately.
10. **Recording Ingestion Failure:** Processed recordings are not discovered or playback URLs are broken.
11. **TURN Relay Failure:** Clients behind CGNAT encounter WebRTC 1007/1020 errors because Coturn is unreachable on TCP 443.
12. **Unauthorized Access / Security Failure:** Unenrolled student gains meeting access (HTTP 200 instead of 403) or cross-tenant resource lookup returns 200/403 instead of Blind 404.

---

## 11. Rollback Reference

In the event of an infrastructure failure during commissioning, follow the approved standard operating procedures documented in:
[PHASE_9_ROLLBACK_RUNBOOK.md](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/docs/PHASE_9_ROLLBACK_RUNBOOK.md)

---

## 12. Final Certification Gate Criteria

To transition the subsystem status from:
$$\text{[B] PRODUCTION READY — EXTERNAL COMMISSIONING PENDING}$$
to:
$$\text{[A] PRODUCTION CERTIFIED — LIVE E2E VERIFIED}$$

**All the following conditions must be satisfied:**
1. Physical BigBlueButton server deployed and validated with `sudo bbb-conf --check` showing zero errors.
2. Coturn STUN/TURN server active on TCP port 443 with valid TLS certificate.
3. PEVN backend successfully launches real meetings using the extracted `BBB_SHARED_SECRET`.
4. All 10 physical device UAT scenarios (`UAT-Phys-01` through `UAT-Phys-10`) executed and passed with real hardware.
5. Multi-tenant Blind 404 barriers and SIMAT enrollment authorization verified live.
6. Recording ingestion, publication privacy, and deletion verified live.
7. 100% pass rate preserved across automated regression test suites (109 backend / 25 frontend).

---

## 13. Human Action Checklist

### A. AI / Software Stack Status (Completed & Verified)
- [x] Backend domain models, database migrations, and PostgreSQL constraints implemented and verified.
- [x] Meeting provider abstraction (`IMeetingProvider`), `BBBAdapter`, and mock provider implemented and verified.
- [x] Authoritative domain services (`VirtualClassroomService`, `AttendanceService`, `RecordingService`) implemented and verified.
- [x] REST API gateway endpoints and Pydantic v2 schemas implemented and verified.
- [x] Frontend React 18 / TypeScript views (`VirtualClassroomsView`) and navigation implemented and verified.
- [x] 109/109 Backend Pytest and 25/25 Frontend Vitest tests passing with 0 regressions.
- [x] Complete deployment runbooks, UAT matrices, and rollback procedures documented.

### B. Infrastructure Administrator Actions (Pending Execution)
- [ ] Provision Ubuntu 22.04 LTS physical server (16 vCPU, 32GB RAM, 500GB SSD) `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Configure DNS `A` records for `bbb.pevn.gov.co` and `turn.pevn.gov.co` `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Execute automated BigBlueButton installation script with Let's Encrypt TLS `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Deploy Coturn TURN server on TCP port 443 with TLS certificates `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Open firewall ports per Network Port Matrix (TCP 80, 443; UDP 16384–32768, 3478) `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Extract shared security salt via `sudo bbb-conf --secret` and inject into `BBB_SHARED_SECRET` in Vault `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Restart PEVN backend application containers to load live BBB configuration `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.

### C. Human Browser & Device UAT Actions (Pending Execution)
- [ ] Conduct live teacher moderator meeting launch and audio/video broadcast `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Conduct live student viewer join, listen-only audio, and question asking `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Test screen sharing from desktop browser `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Test join from mobile device (Android Chrome / iOS Safari) `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Test connection from restrictive school network / CGNAT `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
- [ ] Verify recording processing and student publication privacy `[REQUIRES INFRASTRUCTURE CONFIRMATION]`.
