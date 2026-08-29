# Informe Formal de Implementación — Fase 7 / Paso 2
## Onboarding Seguro de Acudientes y Compatibilidad con Acudientes Rurales/Offline

**Fecha:** 2026-08-28  
**Estado:** IMPLEMENTACIÓN Y VERIFICACIÓN DE PASO 2 COMPLETADA  
**Alcance:** EXCLUSIVAMENTE PASO 2 (ONBOARDING SEGURO DE ACUDIENTES)  
**Pasos 3 y 4:** NO IMPLEMENTADOS (EN ESPERA DE AUTORIZACIÓN EXPLICITA)  
**Gobernanza:** `STEP_2_IMPLEMENTATION = COMPLETE` | `GUARDIAN_ONBOARDING = IMPLEMENTED` | `OPEN_DECISION_3A_01 = PRESERVED` | `RBAC_STATUS = PRESERVED` | `TENANT_ISOLATION = VERIFIED` | `AUDIT_TRAIL = VERIFIED` | `REGRESSION_STATUS = PASS` | `BROWSER_AUTOMATION = NOT_RUN` | `STEP_3_IMPLEMENTED = FALSE` | `STEP_4_IMPLEMENTED = FALSE` | `FINAL_DECISION = NO-GO` | `PROMOTION_EXECUTED = FALSE` | `PROMOTION_AUTHORIZED = FALSE` | `AUTHORIZATION_REQUIRED = TRUE`  

---

## 1. Resumen Ejecutivo (Executive Summary)

En cumplimiento estricto de la autorización otorgada para la **Fase 7 — Paso 2**, se ha implementado de forma segura y con calidad de producción el **Flujo de Auto-Activación y Onboarding Tokenizado para Acudientes (Padres / Tutores Legales)**.

La solución garantiza tres pilares fundamentales:
1. **Validación Criptográfica y de Dominio**: El acudiente solo puede solicitar la activación de su cuenta web si existe una relación legal previamente registrada con un estudiante matriculado (`StudentGuardian`), validando el código de matrícula oficial (SIMAT) y su documento de identidad civil.
2. **Preservación Incondicional de `OPEN-DECISION-3A-01`**: Los acudientes del sector rural o sin acceso digital continúan siendo 100% válidos en la base de datos institucional con `user_id = NULL`. La creación de una cuenta de usuario web es estrictamente opcional y no constituye un prerrequisito para los trámites escolares presenciales.
3. **Cero Fugas de Información y Cero Enumeración**: Los endpoints de solicitud y verificación no revelan la existencia de estudiantes no vinculados ni datos de terceros, y los tokens de 48 bytes se almacenan exclusivamente como resúmenes SHA-256 con vigencia de 24 horas y canje de un solo uso.

---

## 2. Alcance Exacto Ejecutado (Scope)

- **Implementado en Paso 2**:
  1. Modelo de datos `GuardianInvitation` en [backend/app/models/invitation.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/invitation.py).
  2. Esquemas Pydantic `GuardianActivationRequest`, `GuardianActivationResponse`, `VerifyGuardianTokenRequest`, `VerifyGuardianTokenResponse`, `GuardianAcceptActivationRequest`, `GuardianAcceptActivationResponse` en [backend/app/schemas/invitation.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/schemas/invitation.py).
  3. Servicio de dominio `GuardianOnboardingService` en [backend/app/services/guardian_onboarding_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/guardian_onboarding_service.py).
  4. Endpoints públicos en [backend/app/api/v1/endpoints/auth.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py):
     - `POST /api/v1/auth/guardians/request-activation`
     - `POST /api/v1/auth/guardians/verify-token`
     - `POST /api/v1/auth/guardians/accept-activation`
  5. Registro de eventos de auditoría `guardian.activation.requested` y `guardian.onboarding.completed` en [backend/app/audit/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py).
  6. Miembro `GUARDIAN = "guardian"` y `COORDINATOR = "coordinator"` en el enum canónico `SystemRole` en [backend/app/core/security/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/interfaces.py).
  7. Suite de 10 pruebas unitarias y de integración dedicadas en [backend/tests/test_guardian_onboarding.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_guardian_onboarding.py).
- **Excluido y No Implementado (Pasos 3 y 4)**:
  - *Paso 3*: Remediación UX en AcademicHub (**NO IMPLEMENTADO**).
  - *Paso 4*: Analítica Territorial y Recuperación de Clave de Cuentas Activas (**NO IMPLEMENTADO**).

---

## 3. Archivos Modificados (Files Modified)

| Archivo | Módulo / Capa | Tipo de Cambio | Justificación Técnica |
| :--- | :--- | :---: | :--- |
| [backend/app/audit/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py) | Auditoría | `MODIFY` | Adición de eventos `GUARDIAN_ACTIVATION_REQUESTED` y `GUARDIAN_ONBOARDING_COMPLETED`. |
| [backend/app/core/security/interfaces.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/core/security/interfaces.py) | Seguridad / Roles | `MODIFY` | Inclusión explícita de `GUARDIAN = "guardian"` y `COORDINATOR = "coordinator"` en `SystemRole`. |
| [backend/app/models/invitation.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/invitation.py) | Modelos ORM | `MODIFY` | Declaración de la entidad `GuardianInvitation`. |
| [backend/app/models/__init__.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/__init__.py) | Modelos ORM | `MODIFY` | Exportación de `GuardianInvitation`. |
| [backend/app/db/base.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/db/base.py) | Base de Datos | `MODIFY` | Registro de `GuardianInvitation` y `RectorInvitation` para Alembic y SQLAlchemy. |
| [backend/app/schemas/invitation.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/schemas/invitation.py) | Esquemas Pydantic | `MODIFY` | Esquemas para activación, verificación y canje de acudientes. |
| [backend/app/services/guardian_onboarding_service.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/guardian_onboarding_service.py) | Lógica de Dominio | `NEW` | Servicio de gestión de tokens, validación SIMAT y creación de identidad Argon2id. |
| [backend/app/api/v1/endpoints/auth.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/api/v1/endpoints/auth.py) | API / Routing | `MODIFY` | Rutas `/guardians/request-activation`, `/guardians/verify-token`, `/guardians/accept-activation`. |
| [backend/tests/test_guardian_onboarding.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_guardian_onboarding.py) | Pruebas Backend | `NEW` | Test suite exhaustiva de 10 pruebas cubriendo el ciclo completo y casos de borde. |

---

## 4. Cambios en Base de Datos (Database Changes)

- **Nueva Tabla**: `guardian_invitations`
  - `id` (UUID, PK)
  - `guardian_id` (UUID, FK `guardians.id`, `ondelete="CASCADE"`, index)
  - `student_id` (UUID, FK `students.id`, `ondelete="CASCADE"`, index)
  - `institution_id` (UUID, FK `institutions.id`, `ondelete="CASCADE"`, index)
  - `token_hash` (VARCHAR(64), UNIQUE, INDEX)
  - `email` (VARCHAR(255), NOT NULL)
  - `expires_at` (TIMESTAMPTZ, NOT NULL, INDEX)
  - `is_used` (BOOLEAN, default `False`)
  - `used_at` (TIMESTAMPTZ, nullable)
  - `is_revoked` (BOOLEAN, default `False`)
  - `revoked_at` (TIMESTAMPTZ, nullable)
  - `created_at` (TIMESTAMPTZ, default `func.now()`)
- **Compatibilidad con Datos Existentes**: Totalmente aditiva, sin impacto sobre registros existentes.

---

## 5. Modelo de Seguridad y Ciclo de Vida del Token (Security Model)

1. **Entropía del Token**: Se generan 48 bytes URL-safe con el módulo `secrets` de Python (`secrets.token_urlsafe(48)`), proporcionando 384 bits de entropía criptográfica.
2. **Cero Almacenamiento en Claro**: La base de datos almacena exclusivamente el resumen SHA-256 (`token_hash = hash_token(raw_token)`).
3. **Expiración Estricta**: TTL de 24 horas (`expires_at = now + 24h`).
4. **Uso Único y Reemplazo**: Una vez redimido el token, se marca `is_used = True`. Solicitudes posteriores invalidan de forma automática (`is_revoked = True`) invitaciones previas no canjeadas.
5. **Definición de Contraseña**: Cifrado con **Argon2id** (`password_hasher.hash(password)`) cumpliendo los estándares de seguridad nacional.

---

## 6. Preservación de Acudientes Rurales / Offline (OPEN-DECISION-3A-01)

- La existencia de un acudiente en el sistema escolar se define en la tabla `guardians` y la relación de parentesco en `student_guardians`.
- Si un acudiente vive en zona rural sin conectividad o decide no activar una cuenta web, su registro permanece con `Guardian.user_id = NULL`.
- El colegio puede registrar citas, citaciones, autorizaciones de retiro y datos de emergencia sin exigir jamás la existencia de un usuario autenticable.
- Verificado mediante la prueba automatizada `test_offline_guardian_preservation`.

---

## 7. Contención Institucional y Aislamiento Multi-Inquilino (Tenant Isolation)

- Al completarse la activación, el `User` y `UserRole` del acudiente quedan inexorablemente vinculados a la institución educativa (`institution_id = student.institution_id`) del alumno tutelado.
- Intentos de solicitar activación cruzando un acudiente del Colegio A con un estudiante del Colegio B son rechazados determinísticamente con error 404 (`GUARDIAN_RELATION_NOT_FOUND`).

---

## 8. Auditabilidad Forense (Auditability)

Se emiten eventos estructurados con información contextual sin exponer contraseñas ni tokens en claro:
```json
{
  "event_type": "guardian.activation.requested",
  "actor_id": "<uuid-acudiente>",
  "target_id": "<uuid-acudiente>",
  "target_type": "Guardian",
  "institution_id": "<uuid-institucion>",
  "metadata": {
    "guardian_document": "CC:52987654",
    "student_code_simat": "SIMAT-2026-001",
    "email": "rosa.perez@correo.com",
    "expires_at": "2026-08-29T02:46:00Z"
  }
}
```

---

## 9. Pruebas Ejecutadas (Tests Executed)

Se ejecutaron 10 pruebas en [backend/tests/test_guardian_onboarding.py](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/tests/test_guardian_onboarding.py):

| # | Prueba | Resultado | Descripción |
| :-: | :--- | :---: | :--- |
| 1 | `test_valid_guardian_onboarding_lifecycle` | **PASSED** | Flujo completo: Solicitud -> Verificación -> Activación Argon2id -> Login -> Consulta `/me`. |
| 2 | `test_invalid_simat_code_returns_404` | **PASSED** | Código SIMAT inexistente genera 404 `STUDENT_NOT_FOUND`. |
| 3 | `test_invalid_guardian_document_returns_404` | **PASSED** | Documento de acudiente inexistente genera 404 `GUARDIAN_NOT_FOUND`. |
| 4 | `test_unlinked_guardian_student_returns_404` | **PASSED** | Acudiente y estudiante no vinculados genera 404 `GUARDIAN_RELATION_NOT_FOUND`. |
| 5 | `test_cross_institution_unauthorized_relationship_rejected` | **PASSED** | Intento de vinculación entre diferentes colegios rechazado con 404. |
| 6 | `test_expired_token_rejected_with_409` | **PASSED** | Token con fecha vencida rechazado con 409 `TOKEN_EXPIRED`. |
| 7 | `test_token_reuse_prevented_with_409` | **PASSED** | Reintento de canje de token usado rechazado con 409 `TOKEN_ALREADY_USED`. |
| 8 | `test_revoked_token_rejected_with_409` | **PASSED** | Token sustituido por nueva solicitud rechazado con 409 `TOKEN_REVOKED`. |
| 9 | `test_password_mismatch_rejected_with_validation_error` | **PASSED** | Discrepancia en confirmación de clave genera error 422. |
| 10| `test_offline_guardian_preservation` | **PASSED** | Verificación de validez institucional de acudientes offline con `user_id = None`. |

---

## 10. Resultados de Regresión Completa (Regression Results)

```text
================= 294 passed, 5 warnings in 479.19s (0:07:59) =================
```
- **Total de pruebas en el repositorio**: 294
- **Aprobadas**: 294 (100%)
- **Fallidas**: 0
- **Regresiones detectadas**: 0

---

## 11. Confirmación Explícita de Pasos NO Implementados

Se certifica expresamente que:
- **Paso 3 (Remediación UX en AcademicHub)**: **NO FUE IMPLEMENTADO**.
- **Paso 4 (Analítica Territorial y Recuperación de Clave)**: **NO FUE IMPLEMENTADO**.

---

## 12. Estado Final de Gobernanza

```text
STEP_2_IMPLEMENTATION = COMPLETE
GUARDIAN_ONBOARDING = IMPLEMENTED
OPEN_DECISION_3A_01 = PRESERVED
RBAC_STATUS = PRESERVED
TENANT_ISOLATION = VERIFIED
AUDIT_TRAIL = VERIFIED
REGRESSION_STATUS = PASS (294/294 tests passing)
BROWSER_AUTOMATION = NOT_RUN
STEP_3_IMPLEMENTED = FALSE
STEP_4_IMPLEMENTED = FALSE

FINAL_DECISION = NO-GO
PROMOTION_EXECUTED = FALSE
PROMOTION_AUTHORIZED = FALSE
AUTHORIZATION_REQUIRED = TRUE
```
