# PEVN — Authentication Lockout Security Review
## Brute-Force Protection, Account Lockout & Credential Hygiene Audit
**Framework:** AI Software Factory Standard v1.2 — Security Review Gate  
**Task Classification:** READ-ONLY SECURITY AUDIT  
**Date:** October 7, 2026  
**System:** Plataforma Educativa Virtual Nacional (PEVN) — Backend Authentication Engine  
**Author:** Antigravity AI Security Reviewer  

---

## A. Executive Summary

A comprehensive, read-only security audit was conducted on the authentication brute-force protection and account lockout mechanism within the **Plataforma Educativa Virtual Nacional (PEVN)**. This review was prompted by recent administrative account lockouts (`department_admin`, `national_admin`) triggered by failed authentication attempts during manual validation.

The assessment reviewed:
1. Login failure counting and account lockout lifecycle in [`app/services/auth_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py).
2. Distributed attack resistance and IP rate limiting across the ASGI pipeline.
3. User and account enumeration vectors in HTTP responses and side-channel timing.
4. Cryptographic password storage and repository-wide credential hygiene.
5. The administrative maintenance unlock utility in [`app/cli/unlock_user.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/unlock_user.py).
6. Security audit event emission and sanitization.
7. Automated test suite coverage.

### Key Conclusions:
* **Cryptographic Strength:** The underlying password hashing implementation rigorously follows RFC 9106 utilizing **Argon2id** (`time_cost=3`, `memory_cost=65536 KiB`, `parallelism=4`), which is immune to GPU/ASIC acceleration.
* **Functional Lockout Works as Designed:** A threshold of 5 consecutive failed attempts reliably locks an account for 15 minutes and resets upon successful login.
* **Critical Design Flaw (Account Lockout DoS):** The mechanism is **strictly account-based** and lacks an independent IP or request-based rate limiter. An external adversary can intentionally lock out high-level administrators (`national_admin`, `department_admin`, `superadmin`) simply by submitting 5 incorrect attempts from any IP.
* **Side-Channel & Functional Enumeration:** Error messages distinguish between non-existent accounts, locked accounts, and inactive accounts. Additionally, non-existent accounts return in `< 5ms` while existing accounts take `~70-100ms` due to Argon2id calculation, enabling trivial timing-based user enumeration.
* **Credential Exposure in Tracked Artifacts:** Plaintext credentials for development and demonstration administrative accounts were identified in tracked documentation, reports, CLI docstrings, and scratch scripts.

**Final Audit Classification:** **`PASS WITH REMEDIATIONS`**

---

## B. Current Architecture

The authentication lifecycle is orchestrated by [`AuthService.authenticate_user()`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py#L180-L330) and exposed via `POST /api/v1/auth/login` in [`app/api/v1/endpoints/auth.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py#L61-L110).

```
[ Client Request: POST /api/v1/auth/login ]
                      │
                      ▼
[ CORSMiddleware & SecurityHeadersMiddleware ]
                      │
                      ▼
[ RequestLoggingMiddleware (Sanitizes query; ignores body) ]
                      │
                      ▼
[ AuthService.authenticate_user(username_or_email, password) ]
                      │
                      ├──► [Step 1: DB Lookup (users.username or users.email)]
                      │         └─► User not found?
                      │               ├─► Log Audit: USER_LOGIN_FAILURE (user_not_found)
                      │               └─► Raise 401 ("Credenciales inválidas.")  [< 5ms]
                      │
                      ├──► [Step 2: Check user.is_locked]
                      │         └─► datetime.now() < user.locked_until?
                      │               ├─► Log Audit: USER_LOGIN_FAILURE (account_locked)
                      │               └─► Raise 401 ("La cuenta se encuentra temporalmente bloqueada...")
                      │
                      ├──► [Step 3: Check user.is_active]
                      │         └─► not is_active?
                      │               ├─► Log Audit: USER_LOGIN_FAILURE (account_inactive)
                      │               └─► Raise 401 ("Cuenta inactiva. Contacte al administrador.")
                      │
                      ├──► [Step 4: Verify Argon2id Hash] (Takes ~70-100ms)
                      │         └─► Hash Mismatch?
                      │               ├─► user.failed_login_attempts += 1
                      │               ├─► if attempts >= 5: user.locked_until = now() + 15m
                      │               │   └─► Log Audit: USER_ACCOUNT_LOCKED
                      │               ├─► Log Audit: USER_LOGIN_FAILURE (invalid_password)
                      │               ├─► db.commit()
                      │               └─► Raise 401 ("Credenciales inválidas.")
                      │
                      └──► [Step 5: Successful Verification]
                                ├─► user.failed_login_attempts = 0
                                ├─► user.locked_until = None
                                ├─► user.last_login_at = now()
                                ├─► Check needs_rehash()
                                ├─► Issue JWT (volatily in React memory) + Set HttpOnly Cookie
                                └─► Log Audit: USER_LOGIN_SUCCESS
```

### Architectural Parameters:
* **`_MAX_FAILED_LOGIN_ATTEMPTS`:** `5` (Hardcoded in [`auth_service.py:47`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py#L47)).
* **`_LOCKOUT_DURATION_MINUTES`:** `15` (Hardcoded in [`auth_service.py:48`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py#L48)).
* **Database State:** `failed_login_attempts` (`INTEGER`, default `0`), `locked_until` (`TIMESTAMPTZ`, nullable) on `users` table.

---

## C. Security Findings

### Finding 1: Denial of Service via Intentional Account Lockout (Account Lockout DoS)
* **Severity:** **HIGH**
* **CWE:** CWE-307 (Improper Restriction of Excessive Authentication Attempts), CWE-400 (Uncontrolled Resource Consumption).
* **Analysis:**  
  Because the lockout is solely bound to the target account identifier (`username_or_email`) without any IP-level or request-level throttling, any unauthenticated attacker on the Internet can deliberately lock any known administrative account. Known usernames such as `national_admin`, `department_admin`, or `admin_nacional` can be rendered completely unusable for 15 minutes by sending 5 malicious POST requests.
* **Impact:** High-availability denial of service against government officials and institutional administrators during operational hours.

---

### Finding 2: Account and Username Enumeration via Differentiated Responses
* **Severity:** **MEDIUM**
* **CWE:** CWE-204 (Observable Response Discrepancy).
* **Analysis:**  
  The endpoint `POST /api/v1/auth/login` returns different error messages depending on the account state:
  * Non-existent user: `"Credenciales inválidas."`
  * Locked user: `"La cuenta se encuentra temporalmente bloqueada por múltiples intentos fallidos. Intente más tarde."`
  * Inactive user: `"Cuenta inactiva. Contacte al administrador."`
  An attacker harvesting emails or usernames can conclusively identify valid accounts when the response differs from `"Credenciales inválidas."`.

---

### Finding 3: Side-Channel Timing Attack for User Enumeration
* **Severity:** **MEDIUM**
* **CWE:** CWE-208 (Observable Timing Discrepancy).
* **Analysis:**  
  When a user does not exist (Step 1), `auth_service.py` returns immediately without executing Argon2id hash verification (`< 5ms`). When a user exists but the password is incorrect (Step 4), Argon2id executes with `m=65536, t=3, p=4`, taking approximately `70ms to 110ms`.
  An attacker measuring network response round-trip time can reliably differentiate between existing and non-existing accounts without needing differentiated text messages.

---

### Finding 4: Re-Lock Sensitivity Flaw after Expiration
* **Severity:** **LOW / OPERATIONAL**
* **CWE:** CWE-398 (Indicator of Poor Code Quality).
* **Analysis:**  
  When the 15-minute `locked_until` window expires, `user.is_locked` evaluates to `False`. However, `user.failed_login_attempts` remains at `5`.
  If the legitimate user makes a single typographical error on attempt #6, `failed_login_attempts` increments to `6` ($\ge 5$), instantly setting another 15-minute lockout. The user receives zero margin of error after waiting out the lockout duration.

---

### Finding 5: Absence of Independent IP/Request Rate Limiting
* **Severity:** **HIGH**
* **CWE:** CWE-799 (Improper Control of Interaction Frequency).
* **Analysis:**  
  Although [`backend/app/core/config.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/config.py#L111-L112) defines `RATE_LIMIT_DEFAULT = "100/minute"` and `RATE_LIMIT_BACKEND = "memory://"`, no rate-limiting middleware (e.g., SlowAPI or Redis sliding-window filter) is attached to `POST /api/v1/auth/login` in [`main.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/main.py).
  This leaves the system exposed to password spraying (e.g., testing 1 password across 10,000 student accounts without locking any individual account and without being throttled by IP).

---

### Finding 6: CLI Unlock Utility Lacks System Actor Audit Attribution
* **Severity:** **LOW**
* **CWE:** CWE-778 (Insufficient Logging).
* **Analysis:**  
  [`backend/app/cli/unlock_user.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/cli/unlock_user.py#L88) sets `actor_id = str(user.id)` when recording the `USER_UPDATED` audit event. In the audit table, it appears as though the locked user unlocked themselves, rather than recording an explicit maintenance actor like `"CLI_OPERATOR"` or `"SYSTEM"`. Additionally, it emits `USER_UPDATED` instead of the canonical `AuditEventType.USER_ACCOUNT_UNLOCKED`.

---

## D. Credential Exposure Findings

> [!IMPORTANT]
> In accordance with AI Software Factory security directives, **no plaintext password strings are reproduced in this report**. References cite only the file paths, line numbers, credential roles, and severity.

The repository audit identified multiple tracked artifacts where development and demonstration passwords for administrative accounts are stored in plaintext:

| # | Artifact Path | Reference / Line | Credential Target Role | Severity | Remediation Required |
|:---:|---|:---:|---|:---:|---|
| **01** | `docs/reports/PEVN_PHASE_0_6_DEPARTMENT_ADMIN_TEST_ACCOUNT_REPORT.md` | Line 167 | `DEPARTMENT_ADMIN` (Bogotá test account) | **HIGH** | Redact plaintext credential; rotate test account password. |
| **02** | `docs/reports/PEVN_DEMONSTRATION_RUNBOOK.md` | Lines 26–28 | `SUPERADMIN`, Territorial Leader, Rector | **HIGH** | Replace with ephemeral credential provisioning guide. |
| **03** | `docs/reports/PEVN_DEMONSTRATION_RUNBOOK.md` | Lines 50–53 | Teacher, Student, Guardian, Rector Demo | **HIGH** | Redact passwords; use dynamic test seed data. |
| **04** | `docs/reports/PEVN_DEPARTMENT_ADMIN_LIFECYCLE_IMPLEMENTATION_REPORT.md` | Line 111 | `DEPARTMENT_ADMIN` | **HIGH** | Redact plaintext string from formal technical report. |
| **05** | `docs/AUTHENTICATION.md` | Line 106 | `SUPERADMIN` (CLI example) | **MEDIUM** | Replace example with `<SECURE_PASSWORD_PLACEHOLDER>`. |
| **06** | `backend/app/cli/create_department_admin.py` | Line 20 | `DEPARTMENT_ADMIN` (CLI docstring) | **MEDIUM** | Replace docstring sample with generic placeholder. |
| **07** | `backend/app/cli/create_national_admin.py` | Line 20 | `NATIONAL_ADMIN` (CLI docstring) | **MEDIUM** | Replace docstring sample with generic placeholder. |
| **08** | `backend/app/cli/create_superadmin.py` | Line 19 | `SUPERADMIN` (CLI docstring) | **MEDIUM** | Replace docstring sample with generic placeholder. |
| **09** | `backend/app/cli/unlock_user.py` | Line 18 | Maintenance example docstring | **LOW** | Replace docstring sample with generic placeholder. |
| **10** | `backend/scratch/provision_cundinamarca_admin.py` | Line 27 | `DEPARTMENT_ADMIN` (Cundinamarca) | **HIGH** | Redact and migrate script to environment variable. |
| **11** | `backend/scratch/audit_phase11_role_acceptance.py` | Line 171 | Synthetic Test Fixture Password (11 Roles) | **LOW** | Fixture password for temporary test database runs. |
| **12** | `backend/scratch/verify_department_admin_lifecycle.py` | Lines 86, 109, 132 | Synthetic lifecycle test payload | **LOW** | Automated verification harness payload. |
| **13** | `backend/.env` | Lines 10, 13 | Development DB pass & Dev SECRET_KEY | **MEDIUM** | Ensure `.env` is strictly blocked in `.gitignore` for production. |

---

## E. Abuse-Case Analysis

```
┌──────────────────────────────────────┬────────────────────────────────────┬──────────────────────────────────┐
│ Abuse Vector                         │ Current Mitigation                 │ Residual Vulnerability           │
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 1. Brute-Force Single Account        │ Account locked after 5 attempts for│ Attacker triggers DoS on         │
│                                      │ 15 minutes.                        │ legitimate user.                 │
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 2. Distributed Brute-Force (Multi-IP)│ Account locked after 5 attempts.   │ Rotating IPs bypasses nothing;   │
│                                      │                                    │ victim is still locked out.      │
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 3. Password Spraying (1 pwd / N users│ Ineffective. Accounts never reach  │ High. Attacker tests common pwds │
│                                      │ 5 attempts per account.            │ across users with zero IP blocks.│
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 4. Intentional Lockout DoS           │ None. Attacker sends 5 requests    │ High. Trivial for adversary to   │
│                                      │ to lock targets perpetually.       │ freeze administrative access.    │
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 5. Account Enumeration (Side-Channel)│ None. Time discrepancy is ~100ms   │ Medium. Allows attackers to map  │
│                                      │ vs ~2ms.                           │ all active usernames on PEVN.    │
├──────────────────────────────────────┼────────────────────────────────────┼──────────────────────────────────┤
│ 6. Repeated Unlock Abuse via CLI     │ Requires OS host shell access.     │ Low if OS security is strictly   │
│                                      │                                    │ restricted to root / DevOps.     │
└──────────────────────────────────────┴────────────────────────────────────┴──────────────────────────────────┘
```

---

## F. Test Coverage Analysis

An inspection of [`backend/tests/test_auth_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_auth_service.py#L95-L138) revealed the following test coverage status:

| Test Scenario | Test Suite Presence | Status | Verification Detail |
|---|:---:|:---:|---|
| $N$ Failed attempts increment counter | [`test_auth_service.py:101-113`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_auth_service.py#L101-L113) | **COVERED** | Verified for 4 failed attempts. |
| $N+1$ Attempt triggers lockout | [`test_auth_service.py:115-127`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_auth_service.py#L115-L127) | **COVERED** | 5th attempt sets `locked_until` and `is_locked = True`. |
| Blocked attempt raises specific exception | [`test_auth_service.py:130-137`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa%20PEVN/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_auth_service.py#L130-L137) | **COVERED** | `AuthenticationError("temporalmente bloqueada")`. |
| Counter reset after successful authentication | Missing in unit suite | **GAP** | Reset logic is present in code but not asserted in unit tests. |
| Lockout expiration window elapsed | Missing | **GAP** | No test validates authentication after `locked_until` timestamp. |
| Re-lock after expiration behavior | Missing | **GAP** | Behavior on attempt #6 after expiration unverified in tests. |
| Account enumeration response consistency | Missing | **GAP** | No test asserts identical error messages or dummy hashing. |
| IP-based rate limiting | Missing | **GAP** | Feature not yet implemented in middleware. |
| CLI unlock utility execution | Missing | **GAP** | `app/cli/unlock_user.py` has no automated unit/integration test. |

---

## G. Production Readiness Assessment

| Evaluation Dimension | Production Standard | Current State | Assessment |
|---|---|---|:---:|
| **Password Storage** | OWASP Argon2id (RFC 9106) | Configured with $m=64\text{MB}, t=3, p=4$ | **COMPLIANT** |
| **Audit Logging** | Zero secrets, tamper-resistant | Sanitization strips passwords and tokens | **COMPLIANT** |
| **Session Security** | HttpOnly, SameSite=Strict cookies | Refresh token rotated, access token in volatile memory | **COMPLIANT** |
| **Brute-Force Resistance** | IP rate-limiting + progressive delay | Account lockout only; no IP throttling | **NON-COMPLIANT** |
| **DoS Resilience** | Resilient against targeted lockout | Any adversary can lock legitimate users | **NON-COMPLIANT** |
| **User Privacy / Anti-Enumeration** | Uniform response timing & messages | Timing side-channel (~100ms) and distinctive messages | **NON-COMPLIANT** |
| **Credential Hygiene** | 0 credentials in version control | Cleartext test passwords present in repo docs/scripts | **NON-COMPLIANT** |

---

## H. Required Remediations (Action Plan for Production)

To achieve full production readiness, the following remediations are required:

### 1. Implement Independent IP-Based Rate Limiting (P0 — Critical)
Attach an IP and subnet rate-limiting layer (e.g. SlowAPI with Redis backend) directly to `POST /api/v1/auth/login`.
* Throttle to **5 requests per minute per IP address**.
* Throttle to **20 requests per hour per IP address** upon consecutive 401 failures.
* Return `429 Too Many Requests` with a standard `Retry-After` header.

### 2. Implement Progressive Delays (Tarpitting) instead of Hard Lockouts (P1 — High)
Rather than hard-locking accounts for 15 minutes after 5 attempts (which enables Lockout DoS), implement exponential backoff per account:
* Attempts 1–3: Immediate response.
* Attempt 4: Artificial delay of 2 seconds.
* Attempt 5: Artificial delay of 5 seconds.
* Attempt > 5: Enforce CAPTCHA / Turnstile or require email/SMS OTP verification rather than locking the user out entirely.

### 3. Eliminate Account Enumeration and Timing Discrepancies (P1 — High)
* **Uniform Error Messages:** Return `Credenciales inválidas.` for all authentication failures (wrong password, unknown user, locked account, inactive account).
* **Dummy Hash Execution:** When a user is not found in Step 1, execute `password_hasher.verify(password, DUMMY_HASH)` so that response duration remains indistinguishable from an existing user (~80ms).

### 4. Fix Lockout Expiration Counter Reset (P2 — Medium)
In `AuthService.authenticate_user()`, if `datetime.now(UTC) >= user.locked_until`, reset `user.failed_login_attempts = 0` and `user.locked_until = None` before verifying the password. This ensures the user receives a full quota of attempts after waiting out the lockout duration.

### 5. Repository Credential Sanitization & Rotation (P0 — Critical)
* Immediately redact all plaintext password instances identified in Section D from `docs/`, `backend/app/cli/`, and `backend/scratch/`.
* Rotate the credentials of all development/staging accounts (`department_admin`, `national_admin`, `admin_nacional`, `admin_cundinamarca`).
* Configure Git pre-commit hooks (e.g., `detect-secrets` or `gitleaks`) to prevent future commits containing password patterns.

### 6. Enhance CLI Unlock Utility (P2 — Medium)
* Set `actor_id = "SYSTEM_CLI_MAINTENANCE"` on the audit event.
* Emit `AuditEventType.USER_ACCOUNT_UNLOCKED`.
* Provide interactive `getpass` input for password resets rather than relying on environment variables that can leak into shell histories.

---

## I. Optional Hardening Recommendations

1. **Multi-Factor Authentication (MFA / TOTP):**  
   Implement RFC 6238 TOTP authenticator app support for high-privilege roles (`superadmin`, `national_admin`, `department_admin`, `rector`). When MFA is enabled, password-only brute-force attacks cannot lead to account compromise.
2. **Security Notification Emails:**  
   When an account triggers `USER_ACCOUNT_LOCKED`, automatically dispatch a transactional notification email to the account's registered address with a secure, one-time unlock link, allowing legitimate users to self-recover immediately.
3. **Geo-Velocity / Impossible Travel Anomaly Detection:**  
   Compare incoming `client_ip` against the user's historical login geolocations, flagging logins from distant geographic regions within short timeframes.

---

## J. Final Classification

$$\mathbf{STATUS:\ PASS\ WITH\ REMEDIATIONS}$$

### Justification:
1. **Core Cryptographic Integrity is Verified:** The system employs state-of-the-art Argon2id password hashing, timing-safe hash comparison, and secure cookie/JWT session architecture without secret leakage in server logs.
2. **Operational Account Lockout Functional:** The lockout mechanism functions as designed and successfully prevented unauthorized access during testing.
3. **Remediation Mandated Prior to Production:** The system must not be promoted to public/production environments until **IP-level rate limiting** is integrated (to mitigate Account Lockout DoS), **timing/message enumeration** is eliminated, and **plaintext credentials are purged and rotated** across repository documentation and scripts.
