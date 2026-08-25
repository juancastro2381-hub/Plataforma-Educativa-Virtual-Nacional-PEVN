# PHASE 8 — PRODUCTION OPERATIONS & DEPLOYMENT RUNBOOK
## Virtual Classrooms & BigBlueButton Subsystem Operations

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** System Administration, Infrastructure Provisioning & Operational Governance  
**Status:** PRODUCTION OPERATOR RUNBOOK COMPLETE  
**Phase:** Phase 8 External Commissioning  
**Date:** 2026-08-23  

---

## 1. Scope & Operator Responsibility

This runbook provides step-by-step instructions for DevOps, Cloud, and Infrastructure Engineers responsible for deploying, commissioning, configuring, and maintaining the BigBlueButton media cluster and its integration with PEVN.

---

## 2. BigBlueButton Server Provisioning Runbook

### Step 1: Server Requirements & DNS Setup
- **OS:** Ubuntu 22.04 LTS (Fresh installation, no other services on port 80/443).
- **Compute:** 16 vCPU, 32 GB RAM, 500 GB NVMe SSD.
- **DNS:** Configure an `A` record pointing `bbb-staging.pevn.gov.co` (or production) to the server's public IPv4.

### Step 2: Automated Installation with TLS
Execute the official BigBlueButton automated installer with Let's Encrypt SSL:

```bash
wget -qO- https://ubuntu.bigbluebutton.org/bbb-install-2.7.sh | bash -s -- \
  -v focal-270 \
  -s bbb.pevn.gov.co \
  -e devops@pevn.gov.co \
  -a
```

### Step 3: Extract Server Credentials & Secret Salt
Retrieve the server API URL and shared security secret:

```bash
sudo bbb-conf --secret
```

Example Output (Masked):
```text
   URL: https://bbb.pevn.gov.co/bigbluebutton/
Secret: [PROTECTED_64_CHAR_SECRET_STRING]
```

> [!CAUTION]
> **Secret Non-Disclosure:** NEVER paste the shared secret into emails, public chat channels, or git repositories. Immediately store it in HashiCorp Vault or AWS Secrets Manager.

---

## 3. PEVN Backend Integration Configuration

In the PEVN production environment (or Kubernetes Secret / `.env.production`):

```ini
# ---- Virtual Classroom Subsystem Configuration ----
MEETING_PROVIDER_TYPE=bbb
BBB_API_URL=https://bbb.pevn.gov.co/bigbluebutton/api
BBB_SHARED_SECRET=[INJECTED_FROM_VAULT]
BBB_SIGNING_ALGORITHM=sha256
BBB_TIMEOUT_SECONDS=10.0
```

Restart the PEVN backend application containers to load the configuration:
```bash
docker compose restart backend
```

---

## 4. Health Checks & Verification Commands

### 1. Verify BigBlueButton System Health
```bash
sudo bbb-conf --check
```
*Expected Result:* All processes active, Green status, no configuration mismatch.

### 2. Verify PEVN Backend Adapter Resolution
Execute an API health inspection on the backend:
```bash
curl -X GET https://api.pevn.gov.co/api/v1/health/ready
```
*Expected Result:* `{"status":"ready","database":"connected","redis":"connected"}`.

---

## 5. Secret Rotation Procedure

To rotate the BigBlueButton security salt with zero classroom disruption:
1. Schedule a 15-minute maintenance window outside Colombian school hours (e.g. 10:00 PM COT).
2. Generate a new 64-character random hex string:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Update `/etc/bigbluebutton/bbb-web.properties` on the BBB server:
   ```ini
   securitySalt=[NEW_SECRET_STRING]
   ```
4. Restart BigBlueButton services: `sudo bbb-conf --restart`.
5. Update `BBB_SHARED_SECRET` in HashiCorp Vault / PEVN backend environment.
6. Restart backend containers: `docker compose restart backend`.
7. Verify room creation via `POST /api/v1/virtual-classrooms/{id}/launch`.

---

## 6. Incident Response & Troubleshooting

| Symptom / Alert | Root Cause | Operator Action |
| :--- | :--- | :--- |
| **`MeetingProviderAuthError: checksumError`** | Salt mismatch between PEVN and BBB | Compare `BBB_SHARED_SECRET` with `sudo bbb-conf --secret`. |
| **`MeetingProviderConnectionError` (Timeout)** | Network firewall blocking port 443 or server down | Verify BBB server status with `systemctl status bbb-web`. |
| **Students cannot join (HTTP 403)** | Student is not enrolled in SIMAT group | Verify academic enrollment record in PEVN database. |
| **WebRTC 1007 / 1020 on mobile clients** | UDP media blocked by cellular ISP/school firewall | Verify Coturn TURN service: `systemctl status coturn`. |
| **Disk usage > 85% on BBB server** | Large uncompressed recording video files | Configure recording retention script in `/var/bigbluebutton/recording/raw`. |
