# PHASE 9 — OPERATIONAL ROLLBACK RUNBOOK
## Incident Remediation, Disaster Recovery & Fallback Procedures

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Site Reliability, Incident Response & Operational Rollback  
**Status:** SPECIFICATION COMPLETE & OPERATIONAL READY  
**Phase:** Phase 9 External Commissioning  
**Date:** 2026-08-23  

---

## 1. Scope & Emergency Principles

This runbook defines standard operating procedures (SOPs) for rolling back, mitigating, and resolving infrastructure failures during BigBlueButton commissioning and live production operations.

---

## 2. Incident Scenarios & Step-by-Step Rollback Procedures

### Scenario 1: BigBlueButton Node Outage / Catastrophic Cluster Failure
*Impact:* Live classes cannot launch or join on the primary BigBlueButton server.

**Step-by-Step Remediation:**
1. Switch to secondary standby BigBlueButton cluster (or temporary mock provider for maintenance):
   ```bash
   # In backend environment / Kubernetes ConfigMap:
   export BBB_API_URL="https://bbb-backup.pevn.gov.co/bigbluebutton/api"
   export BBB_SHARED_SECRET="[BACKUP_CLUSTER_SECRET_FROM_VAULT]"
   ```
2. Restart backend worker pods/containers:
   ```bash
   docker compose restart backend
   ```
3. Verify connectivity via health inspection:
   ```bash
   curl -X GET https://api.pevn.gov.co/api/v1/health/ready
   ```

---

### Scenario 2: Secret Salt Mismatch (`MeetingProviderAuthError: checksumError`)
*Impact:* API requests to BigBlueButton fail cryptographic signature verification.

**Step-by-Step Remediation:**
1. Log into the BigBlueButton host and re-verify the active server salt:
   ```bash
   sudo bbb-conf --secret
   ```
2. Compare the output with `BBB_SHARED_SECRET` in HashiCorp Vault.
3. Update `BBB_SHARED_SECRET` in the backend runtime configuration.
4. Restart the backend container: `docker compose restart backend`.
5. Test meeting launch on a staging room.

---

### Scenario 3: SSL/TLS Certificate Expiration or Invalidation
*Impact:* Client browsers block WebRTC media and API calls due to HTTPS certificate errors.

**Step-by-Step Remediation:**
1. Force renew Let's Encrypt certificate on BigBlueButton host:
   ```bash
   sudo certbot renew --force-renewal
   sudo systemctl restart nginx
   ```
2. Verify TLS certificate chain:
   ```bash
   curl -Iv https://bbb.pevn.gov.co/bigbluebutton/api
   ```

---

### Scenario 4: Coturn TURN Relay Failure (WebRTC 1007/1020 on CGNAT)
*Impact:* Users in rural schools behind restrictive firewalls cannot establish audio/video streams.

**Step-by-Step Remediation:**
1. Inspect Coturn service status on the TURN server:
   ```bash
   sudo systemctl status coturn
   ```
2. If crashed, restart Coturn:
   ```bash
   sudo systemctl restart coturn
   ```
3. Verify TCP port 443 is listening:
   ```bash
   sudo netstat -tlpn | grep 443
   ```
4. Verify BigBlueButton TURN integration: `sudo bbb-conf --check`.

---

### Scenario 5: Media Server Daemons Crash (FreeSWITCH / Mediasoup)
*Impact:* Meetings connect but audio or video fails to initialize.

**Step-by-Step Remediation:**
1. Execute full clean restart of BigBlueButton services:
   ```bash
   sudo bbb-conf --restart
   ```
2. Monitor system startup logs:
   ```bash
   sudo bbb-conf --watch
   ```
3. Run internal diagnostic check: `sudo bbb-conf --check`.
