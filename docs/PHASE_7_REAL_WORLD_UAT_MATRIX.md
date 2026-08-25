# PHASE 7 — REAL-WORLD USER ACCEPTANCE TESTING (UAT) MATRIX
## Physical Devices, WebRTC Media Streaming & Network Traversal

**System:** Plataforma Educativa Virtual Nacional (PEVN)  
**Domain:** Real-World Audiovisual Streaming & In-Browser User Acceptance Testing  
**Status:** UAT SPECIFICATION READY FOR PHYSICAL COMMISSIONING  
**Phase:** Phase 7 Final Commissioning  
**Date:** 2026-08-23  

---

## 1. Objective & Methodology

This document outlines the real-world User Acceptance Testing (UAT) matrix for validating physical audiovisual streaming, browser permission prompts, WebRTC media connectivity, and NAT/firewall traversal across diverse client hardware and institutional networks in Colombia.

---

## 2. Real-World User Acceptance Testing Matrix

| Test ID | UAT Scope / Workflow | Target Role | Hardware / Network Precondition | Acceptance Criteria | Operational Readiness | Execution Method |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **UAT-01** | **Moderator Microphone Audio** | Teacher | Desktop / Laptop with USB/built-in microphone | Audio stream connects via FreeSWITCH WebRTC; voice is audible to all participants without distortion or echo. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-02** | **Moderator Camera Broadcast** | Teacher | Integrated webcam (720p/1080p) | Video stream renders in BigBlueButton video grid; frame rate is stable (>15 fps). | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-03** | **Moderator Screen Sharing** | Teacher | Chrome / Firefox / Edge on Windows / macOS / Linux | Screen/Window share dialog prompts; selected screen is broadcast to all participants with low latency (<1s). | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-04** | **Student Audio Reception** | Student | Smartphone / Tablet / Laptop with speakers or headphones | Student joins in Listen-Only mode; teacher voice is crisp and synchronized with shared whiteboard. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-05** | **Student Microphone Participation** | Student | In-ear headset / built-in microphone | Student unmutes; audio input passes echo cancellation and is audible to moderator and peers. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-06** | **Student Video Reception** | Student | Mobile/Desktop browser on 4G/Wi-Fi | Teacher video and whiteboard slides render smoothly; adaptive bitrate scales down during packet loss without disconnect. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-07** | **Interactive Whiteboard / Chat** | Student & Teacher | Touchscreen tablet / mouse | Multi-user whiteboard drawings, annotations, and public/private text messages update in real time. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-08** | **Strict NAT / CGNAT Traversal** | Student | Rural school connection behind restrictive CGNAT or ISP firewall | Coturn TURN server relays WebRTC UDP packets over TCP port 443; media stream connects successfully without 1007/1020 WebRTC errors. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-09** | **Mobile Network (4G / 5G)** | Student | Mobile Chrome on Android / Safari on iOS | Meeting interface adapts to portrait/landscape; responsive touch controls operate seamlessly. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |
| **UAT-10** | **Session Reconnection & Recovery**| Student | Temporary Wi-Fi disconnect (5-10s loss) | BigBlueButton client auto-reconnects; attendance tracking preserves original join record without telemetry corruption. | **REQUIRES MANUAL DEVICE UAT** | Execute during physical staging commissioning |

---

## 3. UAT Execution Prerequisites

Before conducting the physical device UAT sessions:
1. Deploy and configure the physical BigBlueButton server cluster with active FreeSWITCH / mediasoup media services.
2. Install and bind a valid SSL/TLS wildcard certificate (`*.pevn.gov.co`) to eliminate browser insecure media origin restrictions.
3. Configure Coturn TURN server listening on TCP port 443 with secret authentication.
4. Prepare test user accounts across distinct Colombian school network types (Urban fiber optic, rural satellite/cellular 4G, and institutional proxy networks).
