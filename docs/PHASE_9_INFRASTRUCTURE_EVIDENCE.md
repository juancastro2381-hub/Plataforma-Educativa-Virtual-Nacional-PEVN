# PHASE 9 — INFRASTRUCTURE VALIDATION & EVIDENCE COMMANDS
## Operational Verification Commands & Diagnostic Protocols

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Infrastructure Diagnostics, Port Reachability & Protocol Validation  
**Status:** SPECIFICATION COMPLETE & COMMISSIONING READY  
**Phase:** Phase 9 External Commissioning  
**Date:** 2026-08-23  

---

## 1. Scope & Diagnostic Framework

This document defines the diagnostic commands and expected outputs for validating BigBlueButton server health, DNS resolution, TLS certificate validity, firewall reachability, and Coturn TURN relay allocation during operational deployment.

---

## 2. Infrastructure Diagnostic Commands & Expected Outputs

### 1. DNS Resolution Verification
```bash
dig +short bbb.pevn.gov.co
nslookup bbb.pevn.gov.co
```
*Expected Output:* Returns public IPv4 address of the BigBlueButton host (e.g. `200.x.x.x`).

---

### 2. HTTPS / TLS Certificate Verification
```bash
curl -Iv https://bbb.pevn.gov.co/bigbluebutton/api
```
*Expected Output:*
```text
* SSL connection using TLSv1.3 / AEAD-CHACHA20-POLY1305-SHA256
* Server certificate:
*  subject: CN=bbb.pevn.gov.co
*  start date: Aug 23 00:00:00 2026 GMT
*  expire date: Nov 21 23:59:59 2026 GMT
*  issuer: C=US, O=Let's Encrypt, CN=R3
*  SSL certificate verify ok.
< HTTP/2 200 (or HTTP/1.1 200 OK)
```

---

### 3. OpenSSL Detailed Handshake & Cipher Check
```bash
openssl s_client -connect bbb.pevn.gov.co:443 -servername bbb.pevn.gov.co -tls1_3
```
*Expected Output:* `Verify return code: 0 (ok)`.

---

### 4. BigBlueButton Internal Health Audit
Execute on the physical Ubuntu host:
```bash
sudo bbb-conf --check
```
*Expected Output:*
```text
BigBlueButton Server 2.7.x
                    IP: 200.x.x.x
               Version: 2.7.x
           Environment: Ubuntu 22.04 LTS
              Turn/Stun: Active (turn.pevn.gov.co)
...
** Potential problems described below **
None
```

---

### 5. BigBlueButton Secret Salt Extraction (Masked)
```bash
sudo bbb-conf --secret
```
*Expected Output:*
```text
   URL: https://bbb.pevn.gov.co/bigbluebutton/
Secret: [PROTECTED_HEX_STRING]
```

---

### 6. Firewall & WebRTC Port Reachability
```bash
# Test HTTPS API / Web Signaling
nc -zv bbb.pevn.gov.co 443

# Test Coturn STUN Port
nc -zuv turn.pevn.gov.co 3478

# Test Coturn TURN TLS Port
nc -zv turn.pevn.gov.co 443
```
*Expected Output:* `Connection to [host] [port] port [tcp/udp] succeeded!`.

---

### 7. Coturn Allocation Test (From External Network)
```bash
turnutils_uclient -v -t -u [USERNAME] -w [PASSWORD] -p 443 turn.pevn.gov.co
```
*Expected Output:* `Total allocation success count: 100%, 0 failures`.

---

### 8. PEVN Backend Application Health
```bash
curl -X GET https://api.pevn.gov.co/api/v1/health/ready
```
*Expected Output:*
```json
{
  "status": "ready",
  "database": "connected",
  "redis": "connected"
}
```
