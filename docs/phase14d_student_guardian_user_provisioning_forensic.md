# PEVN — Fase 14D: Informe Forense y Diseño de Aprovisionamiento, Ciclo de Vida y Administración de Cuentas de Estudiantes y Acudientes

**Documento:** Informe Forense y Especificación de Arquitectura  
**Fase:** Fase 14D — Aprovisionamiento y Ciclo de Vida de Cuentas de Estudiantes y Acudientes  
**Estado:** 🔍 **INFORME FORENSE COMPLETADO**  
**Fecha:** Septiembre 2026  

---

## 1. Hallazgos del Descubrimiento Forense

### 1.1. Lo que ya existe en el repositorio

1. **Modelo de Identidad Central (`User`)** ([`app/models/user.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/user.py)):
   - Entidad canónica de autenticación (`users` table).
   - Atributos de seguridad: `hashed_password` (Argon2id), `is_active`, `is_verified`, `must_change_password`, `failed_login_attempts`, `locked_until`, `last_login_at`.
   - Restricción única en `(document_type, document_number)` y `email`.
   - Relación con roles mediante `UserRole` y tokens mediante `RefreshToken` y `PasswordResetToken`.

2. **Modelo de Perfil Estudiantil (`Student`)** ([`app/models/student.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/student.py)):
   - Entidad pedagógica (`students` table) con vínculo 1:1 estricto e indexado a `User.id` (`user_id`).
   - Identificador nacional único SIMAT (`code_simat`).
   - Límite multi-inquilino estricto (`institution_id`).
   - Metadatos socio-demográficos e inclusión educativa (`birth_date`, `gender`, `blood_type`, `stratum`, `eps_health_provider`, `has_disability`, `disability_type`).

3. **Modelo de Acudiente Civil (`Guardian`)** ([`app/models/guardian.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/guardian.py)):
   - Entidad civil de tutela (`guardians` table).
   - Soporta acudientes rurales/offline sin cuenta interactiva mediante `user_id = NULL` (preservando [OPEN-DECISION-3A-01]).
   - Restricción única en `(institution_id, document_type, document_number)`.
   - `email` y `address` opcionales.

4. **Modelo de Asociación Estudiante-Acudiente (`StudentGuardian`)** ([`app/models/guardian.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/guardian.py)):
   - Tabla asociativa M:N (`student_guardians` table).
   - Soporta 1 estudiante → múltiples acudientes y 1 acudiente → múltiples estudiantes.
   - Atributos canónicos: `relationship_type` (PADRE, MADRE, ABUELO_A, TIO_A, TUTOR_LEGAL, OTRO), `is_primary_contact`, `is_authorized_pickup`.
   - Restricción única en `(student_id, guardian_id)`.

5. **Servicio y Modelo de Onboarding de Acudientes (`GuardianOnboardingService` & `GuardianInvitation`)** ([`app/services/guardian_onboarding_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/guardian_onboarding_service.py)):
   - Tabla `guardian_invitations` con almacenamiento de hash SHA-256 de token seguro de 48 bytes URL-safe (vigencia 24h).
   - Método `request_activation`: Valida matrícula SIMAT y tutela legal; revoca invitaciones previas no redimidas; genera token criptográfico y registra auditoría.
   - Método `verify_token`: Valida integridad, no revocación, no uso y vigencia del token.
   - Método `accept_activation`: Redime token, crea cuenta `User` con Argon2id, asigna rol canónico `guardian`, vincula `Guardian.user_id` y activa sesión.

6. **Servicio y Endpoints de Autenticación y Recuperación de Clave (`AuthService`)** ([`app/services/auth_service.py`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/services/auth_service.py)):
   - `request_password_reset`: Genera `PasswordResetToken` (SHA-256, 1h expiración, de un solo uso).
   - `confirm_password_reset`: Establece nueva clave con Argon2id y revoca sesiones previas.

7. **Patrón de Ciclo de Vida Docente Existente (`TeacherService` y `TeachersView.tsx`)**:
   - Implementado en Fase 13D.5 como estándar de oro del proyecto: `compute_account_status`, `provision_teacher_account`, `update_teacher_account_status`, `reset_teacher_password`, modal de entrega de credenciales / enlace temporal sin exponer contraseñas en claro.

8. **Auditoría e Infraestructura de Logs (`audit_service`)** ([`app/audit/`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/)):
   - Eventos disponibles: `STUDENT_CREATED`, `STUDENT_UPDATED`, `GUARDIAN_CREATED`, `GUARDIAN_UPDATED`, `GUARDIAN_ASSOCIATED`, `GUARDIAN_ACTIVATION_REQUESTED`, `GUARDIAN_ONBOARDING_COMPLETED`, `USER_CREATED`, `USER_ACTIVATED`, `USER_DEACTIVATED`, `USER_PASSWORD_RESET_REQUESTED`, `USER_PASSWORD_RESET_CONFIRMED`.

---

## 2. Lo que se debe Reutilizar y lo que NO se debe Duplicar

### 2.1. Reutilizaciones Obligatorias
- **Identidad Canónica**: `User` es la única entidad de cuenta/login.
- **Relaciones de Dominio**: `Student.user_id` (1:1) y `Guardian.user_id` (opcional 1:1).
- **Servicio de Onboarding de Acudientes**: `GuardianOnboardingService` y la tabla `guardian_invitations`.
- **Servicio de Contraseñas y Tokens**: `auth_service.request_password_reset` y `PasswordResetToken`.
- **RBAC**: Permisos existentes `students:create`, `students:update`, `students:read`, `guardians:create`, `guardians:update`, `guardians:read`, `guardians:link_student`.

### 2.2. Prohibiciones Estrictas
- ❌ **NO** crear modelos como `StudentUser` o `GuardianUser`.
- ❌ **NO** duplicar campos de contraseña ni credenciales dentro de las tablas `students` o `guardians`.
- ❌ **NO** crear un segundo mecanismo paralelo de activación de acudientes.
- ❌ **NO** modificar los contratos certificados de los portales `/student` y `/guardian`.
- ❌ **NO** exponer contraseñas en texto plano ni hashes en respuestas de API o logs.

---

## 3. Lo que Falta por Implementar

### 3.1. En Backend:

1. **Ciclo de Vida de Cuentas de Estudiantes en `StudentService`**:
   - `compute_account_status(student)`: Deriva `ACTIVA`, `INACTIVA`, `PENDING_SETUP` (si `must_change_password=True`), o `BLOQUEADA` (si `is_locked`).
   - `provision_student_account(student_id, institution_id, email, ...)`: Aprovisiona o activa la cuenta `User` del estudiante, asigna rol canónico `student`, marca `must_change_password = True`, genera token de configuración/reset inicial de un solo uso mediante `auth_service.request_password_reset`, y emite auditoría.
   - `update_student_account_status(student_id, institution_id, is_active, ...)`: Activa/suspende la cuenta del estudiante sin eliminar su historial académico ni notas. Revoca refresh tokens en caso de suspensión.
   - `reset_student_password(student_id, institution_id, ...)`: Genera token de restablecimiento de contraseña de un solo uso, marca `must_change_password = True`, y emite auditoría.

2. **Endpoints de Cuenta de Estudiante en `app/api/v1/endpoints/students.py`**:
   - `POST /api/v1/students/{student_id}/account/provision`
   - `POST /api/v1/students/{student_id}/account/status`
   - `POST /api/v1/students/{student_id}/account/reset-password`
   - Actualización de `StudentResponse` para incluir `account_status`, `account_email`, `has_account`, `reset_token`, `must_change_password`.

3. **Ciclo de Vida y Administración de Acudientes en `GuardianService`**:
   - `compute_account_status(guardian)`: Deriva `SIN_CUENTA` (si `user_id IS NULL`), `INVITADO / PENDIENTE` (si tiene `GuardianInvitation` vigente sin redimir), `ACTIVA` (si `user_id` existe y `user.is_active = True`), `INACTIVA` (si `user.is_active = False`).
   - `invite_guardian(guardian_id, institution_id, email, student_id, ...)`: Emite invitación con token seguro reutilizando `GuardianOnboardingService.request_activation`, o actualiza email y despacha invitación.
   - `revoke_invitation(guardian_id, institution_id, ...)`: Revoca invitaciones pendientes del acudiente.
   - `update_guardian_account_status(guardian_id, institution_id, is_active, ...)`: Activa o suspende la cuenta interactiva del acudiente si existe, revocando tokens en caso de desactivación.
   - `reset_guardian_password(guardian_id, institution_id, ...)`: Genera token de recuperación de clave para el acudiente con cuenta activa.
   - `get_guardian_students(guardian_id, institution_id, ...)`: Lista los estudiantes vinculados al acudiente dentro de la institución.

4. **Endpoints de Cuenta de Acudiente en `app/api/v1/endpoints/guardians.py`**:
   - `POST /api/v1/guardians/{guardian_id}/account/invite`
   - `POST /api/v1/guardians/{guardian_id}/account/revoke-invitation`
   - `POST /api/v1/guardians/{guardian_id}/account/status`
   - `POST /api/v1/guardians/{guardian_id}/account/reset-password`
   - `GET /api/v1/guardians/{guardian_id}/students`
   - Actualización de `GuardianResponse` para incluir `account_status`, `account_email`, `has_account`, `has_pending_invitation`, `invitation_expires_at`, `raw_activation_token`, `reset_token`, `linked_students_count`.

5. **Esquemas Pydantic en `app/schemas/academic.py`**:
   - `StudentAccountStatusEnum`: `ACTIVA`, `INACTIVA`, `PENDIENTE_CONFIGURACION`, `BLOQUEADA`.
   - `StudentAccountProvisionRequest`, `StudentAccountStatusUpdateRequest`, `StudentAccountActionResponse`.
   - `GuardianAccountStatusEnum`: `SIN_CUENTA`, `INVITADO`, `ACTIVA`, `INACTIVA`.
   - `GuardianAccountInviteRequest`, `GuardianAccountStatusUpdateRequest`, `GuardianAccountActionResponse`.

---

### 3.2. En Frontend:

1. **Tipos y Servicios**:
   - `frontend/src/types/index.ts`: Definición de enums y contratos para el ciclo de vida de cuentas de estudiantes y acudientes.
   - `frontend/src/services/academic.ts`: Métodos de API para aprovisionamiento, cambio de estado, reset de contraseña, invitación y consulta de tutorados.

2. **Vista de Administración de Estudiantes (`StudentsView.tsx`)**:
   - Columna **Estado de Cuenta** con badges visuales (`ACTIVA` verde, `PENDIENTE DE CLAVE` amarillo, `INACTIVA` gris, `BLOQUEADA` rojo).
   - Menú de acciones por estudiante: "Aprovisionar / Configurar Acceso", "Activar Cuenta", "Desactivar / Suspender Cuenta", "Restablecer Contraseña", "Ver Acudientes".
   - Modal de entrega de credenciales iniciales / enlace seguro temporal (sin contraseñas en claro).
   - Diálogos de confirmación para acciones destructivas/sensibles de seguridad.

3. **Vista de Administración de Acudientes (`GuardiansView.tsx`)**:
   - Columna **Estado de Cuenta** con badges visuales (`ACTIVA` verde, `INVITACIÓN PENDIENTE` amarillo, `INACTIVA` gris, `SIN CUENTA (OFFLINE)` azul pizarra).
   - Contador y visualización de estudiantes vinculados por acudiente.
   - Menú de acciones por acudiente: "Invitar / Activar Portal", "Reenviar Invitación", "Revocar Invitación", "Activar Cuenta", "Desactivar Cuenta", "Restablecer Contraseña", "Vincular Estudiante", "Ver Estudiantes Vinculados".
   - Modal de entrega de enlace de activación con copiado rápido y fecha de expiración.

---

## 4. Matriz de Autorización y Seguridad Multi-Tenant

| Rol del Actor | Aprovisionar Estudiante | Activar / Suspender Estudiante | Reset Clave Estudiante | Invitar Acudiente | Activar / Suspender Acudiente | Reset Clave Acudiente | Alcance Multi-Tenant |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Superadmin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Global / Cualquier Institución |
| **Administrador Nacional** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Global / Cualquier Institución |
| **Rector** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Estrictamente su Institución |
| **Admin Institucional** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Estrictamente su Institución |
| **Coordinador Académico** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Estrictamente su Institución |
| **Docente** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Denegado (403) |
| **Estudiante** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Denegado (403) |
| **Acudiente** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Denegado (403) |

- **Defensa Anti-IDOR**: Cada mutación valida que el estudiante o acudiente pertenezca a la institución del usuario autenticado. En caso de discrepancia inter-institucional, se retorna `404 Not Found` determinista para evitar enumeración.
