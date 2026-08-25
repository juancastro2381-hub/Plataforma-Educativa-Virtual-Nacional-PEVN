# PHASE 8 — NETWORK & COTURN TURN/STUN VALIDATION
## NAT Traversal & Institutional Firewall Compatibility

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Network Engineering, Coturn STUN/TURN Relay & CGNAT Traversal  
**Status:** SPECIFICATION COMPLETE & READY FOR DEPLOYMENT  
**Phase:** Phase 8 External Commissioning  
**Date:** 2026-08-23  

---

## 1. Colombian Educational Network Challenges & Threat Model

In Colombia, many public educational institutions, rural schools, and mobile LTE connections operate behind **Carrier-Grade NAT (CGNAT)** or restrictive school firewalls that:
- Drop inbound UDP packets across high-range ports (`16384–32768`).
- Block direct UDP hole punching between clients and WebRTC media servers.
- Restrict outbound traffic exclusively to standard web ports (`TCP 80` and `TCP 443`).

Without a dedicated **Coturn TURN (Traversal Using Relays around NAT)** server listening on `TCP 443`, users in these networks experience **WebRTC Error 1007 (ICE Negotiation Failed)** or **WebRTC Error 1020 (Media Transport Unavailable)**.

---

## 2. Coturn Deployment Architecture & Topology

```
+-----------------------------------------------------------------------------------+
|                        COTURN STUN/TURN RELAY ARCHITECTURE                        |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Rural School Behind Restrictive Firewall / CGNAT ]                             |
|         │                                                                         |
|         ├── Direct UDP (16384-32768) ──► [ BLOCKED BY SCHOOL FIREWALL ]           |
|         │                                                                         |
|         └── Encrypted TLS Relay (TCP :443) ──► [ Coturn TURN Server ]             |
|                                                       │                           |
|                                                       └── Internal UDP Media ──►  |
|                                                           [ BigBlueButton Node ]  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Recommended `turnserver.conf` Configuration Template

```ini
# ============================================================
# PEVN — Coturn TURN Server Configuration
# ============================================================

# Network listening ports
listening-port=3478
tls-listening-port=443

# Listening IPs (bind to external public IP)
listening-ip=0.0.0.0
external-ip=[PUBLIC_SERVER_IP]

# Realm and authentication
realm=turn.pevn.gov.co
use-auth-secret
static-auth-secret=[SECURE_RANDOM_TURN_SECRET_MANAGED_IN_VAULT]

# SSL/TLS Certificates
cert=/etc/letsencrypt/live/turn.pevn.gov.co/fullchain.pem
pkey=/etc/letsencrypt/live/turn.pevn.gov.co/privkey.pem

# Security and performance options
min-port=49152
max-port=65535
fingerprint
lt-cred-mech
no-cli
no-tcp-relay
no-multicast-peers
denied-peer-ip=10.0.0.0-10.255.255.255
denied-peer-ip=172.16.0.0-172.31.255.255
denied-peer-ip=192.168.0.0-192.168.255.255
```

---

## 4. BigBlueButton TURN Integration

BigBlueButton connects to Coturn via `/etc/bigbluebutton/turn-stun-servers.xml`:

```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans
       http://www.springframework.org/schema/beans/spring-beans.xsd">

    <bean id="stun0" class="org.bigbluebutton.web.services.turn.StunServer">
        <constructor-arg index="0" value="stun:turn.pevn.gov.co:3478"/>
    </bean>

    <bean id="turn0" class="org.bigbluebutton.web.services.turn.TurnServer">
        <constructor-arg index="0" value="[SECURE_RANDOM_TURN_SECRET]"/>
        <constructor-arg index="1" value="turns:turn.pevn.gov.co:443?transport=tcp"/>
        <constructor-arg index="2" value="86400"/>
    </bean>
</beans>
```

---

## 5. WebRTC Error Code Diagnostic Guide

| Error Code | Root Cause | Remediation Action |
| :--- | :--- | :--- |
| **1001** | WebSocket disconnected | Check network stability or NGINX reverse proxy timeout. |
| **1002** | Could not make WebSocket call | Verify client firewall allows outgoing WSS connection. |
| **1007** | ICE negotiation failed | Check Coturn TURN configuration; ensure TCP port 443 is open. |
| **1020** | Media could not reach server | Ensure UDP ports 16384–32768 or Coturn relay are functional. |
