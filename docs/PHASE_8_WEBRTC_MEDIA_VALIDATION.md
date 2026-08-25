# PHASE 8 — WEBRTC MEDIA VALIDATION & QUALITY THRESHOLDS
## Real-Time Audio, Video, Screen Sharing & Media Signaling

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** WebRTC Audiovisual Transport & Network Resilience  
**Status:** SPECIFICATION COMPLETE & READY FOR PHYSICAL VALIDATION  
**Phase:** Phase 8 External Commissioning  
**Date:** 2026-08-23  

---

## 1. WebRTC Media Architecture & Signaling Topology

BigBlueButton utilizes an integrated WebRTC media architecture combining **FreeSWITCH** (for low-latency SIP audio mixing and Echo Cancellation) and **Kurento / mediasoup** (as a Selective Forwarding Unit for multi-party video and high-resolution screen sharing).

```
+-----------------------------------------------------------------------------------+
|                        PEVN WEBRTC MEDIA PIPELINE                                 |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  [ Browser Client (HTML5 / React SPA) ]                                           |
|         │                                                                         |
|         ├── WSS (WebSocket Secure :443) ──► [ NGINX / BBB WebRTC Signaling ]      |
|         │                                                                         |
|         ├── WebRTC Audio (Opus / DTLS-SRTP) ────────► [ FreeSWITCH Media Server ] |
|         ├── WebRTC Video (VP8 / H.264 DTLS-SRTP) ───► [ Mediasoup / Kurento SFU ] |
|         └── WebRTC Screen Share (VP8 / H.264) ──────► [ Mediasoup / Kurento SFU ] |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Codecs, Bitrates & Performance Thresholds

| Media Stream | Primary Codec | Sample Rate / Resolution | Bitrate Range | Target Latency / Quality Threshold |
| :--- | :--- | :--- | :--- | :--- |
| **Microphone Audio** | Opus | 48 kHz (Fullband) | 32–48 kbps | RTT < 200ms, Packet Loss < 2%, Jitter < 30ms |
| **Listen-Only Audio** | Opus | 48 kHz (Fullband) | 32–40 kbps | RTT < 250ms, Packet Loss < 3% |
| **Webcam Video (SD)** | VP8 / H.264 | 640x480 @ 15fps | 200–350 kbps | Dynamic down-scaling under packet loss |
| **Webcam Video (HD)** | VP8 / H.264 | 1280x720 @ 24fps | 500–800 kbps | Enabled selectively for presenter |
| **Screen Sharing** | VP8 / H.264 | 1920x1080 @ 5–10fps | 500–1200 kbps | Text clarity prioritized over frame rate |

---

## 3. ICE Candidate Negotiation & NAT Traversal Sequence

```
1. Host Candidate:
   Client attempts direct UDP peer connection within local LAN subnet.
   
2. Server Reflexive (STUN Candidate):
   Client discovers public IP/Port via STUN server (UDP 3478) and attempts direct WAN connection.
   
3. Relay (TURN Candidate):
   If symmetric NAT or institutional firewall blocks direct UDP ports (16384–32768),
   the client falls back to Coturn TURN relay over TCP port 443 with TLS encryption.
```

---

## 4. Browser Security & Media Permissions

1. **Secure Origin Enforcement:** Browsers strictly block `navigator.mediaDevices.getUserMedia()` on non-HTTPS origins. Both PEVN and BigBlueButton MUST run under trusted TLS certificates.
2. **Permission Prompts:** Clear UI prompts guide teachers and students to grant microphone and camera access.
3. **Graceful Degradation:** If camera permission is denied, participant joins in audio-only mode without breaking session connectivity.
