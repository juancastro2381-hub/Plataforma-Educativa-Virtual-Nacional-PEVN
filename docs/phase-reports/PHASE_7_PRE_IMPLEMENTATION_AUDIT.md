# Informe Formal de Auditoría Pre-Implementación y Planificación — Fase 7
## Sucesión de Rectores, Onboarding de Acudientes, Remediación UX y Analítica Territorial

**Fecha:** 2026-08-27  
**Estado:** AUDITORÍA Y PLANIFICACIÓN PRE-IMPLEMENTACIÓN COMPLETADA  
**Modificaciones de Código:** 0  
**Modificaciones de Base de Datos:** 0  
**Mutaciones Canónicas:** 0  
**Gobernanza:** `PHASE_7_PLANNING_COMPLETE = TRUE` | `IMPLEMENTATION_EXECUTED = FALSE` | `FINAL_DECISION = NO-GO` | `PROMOTION_EXECUTED = FALSE` | `PROMOTION_AUTHORIZED = FALSE` | `AUTHORIZATION_REQUIRED = TRUE`  

---

## 1. Resumen Ejecutivo (Executive Summary)

El presente informe constituye la **Auditoría Pre-Implementación y Plan de Diseño Técnico de la Fase 7** de la Plataforma Educativa Virtual Nacional (PEvN). En estricto cumplimiento de las directrices de gobernanza de producción, **esta fase es exclusivamente de diseño, auditoría y análisis de brechas**, finalizando con **CERO (0) modificaciones en el código fuente, base de datos o definiciones canónicas**.

El objetivo es formalizar la arquitectura de solución para los requerimientos y oportunidades de mejora identificados en la auditoría de aceptación de la Fase 6:
1. **Flujo formal de Sucesión y Revocación de Rectores**: Procedimiento administrativo para revocar la titularidad de un rector saliente y habilitar de inmediato la emisión de una nueva invitación.
2. **Onboarding Seguro de Acudientes**: Mecanismo de auto-activación tokenizada para padres de familia vinculado a las matrículas escolares existentes sin romper la compatibilidad con acudientes offline/rurales.
3. **Remediación UX en AcademicHub**: Notificación informativa al usuario cuando navega directamente a una pestaña restringida para su rol, preservando la barrera de seguridad del backend.
4. **Recuperación Segura de Contraseña para Cuentas Activas**: Arquitectura de tokens criptográficos de un solo uso con protección anti-enumeración de usuarios.
5. **Tableros de Analítica Territorial**: Endpoints agregados basados en el modelo de datos DANE existente para líderes departamentales y municipales.

---

## 2. Auditoría de la Arquitectura Existente (Architecture Audit)

Se examinaron exhaustivamente los componentes centrales del sistema para garantizar la compatibilidad integral de los nuevos diseños:

- **Autenticación e Identidades ([User](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/user.py), [UserRole](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/role.py))**:
  - `User.is_active` y `UserRole.is_active` permiten separar la vigencia global de una cuenta de su pertenencia a una institución específica.
  - El hashing con **Argon2id** (`password_hasher`) y los tokens criptográficos de 48 bytes con SHA-256 (`tokens.py`) constituyen la base criptográfica estándar.
- **Invitaciones Criptográficas ([RectorInvitation](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/invitation.py))**:
  - Modelo probado de cero-conocimiento con resumen SHA-256 en base de datos, tiempo de expiración (48h), marca de uso único (`is_used`) y revocación explícita (`is_revoked`).
- **Modelo de Acudientes y Estudiantes ([Guardian](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/guardian.py), [StudentGuardian](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/guardian.py), [Student](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/models/student.py))**:
  - `Guardian` soporta identificación por documento de identidad civil (`document_type`, `document_number`), teléfono y correo opcional, con un enlace `user_id` opcional (decisión canónica `OPEN-DECISION-3A-01`).
- **Pistas de Auditoría ([AuditEvent](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/backend/app/audit/interfaces.py))**:
  - Registro estructurado con `actor_id`, `actor_ip`, `target_id`, `institution_id`, `correlation_id` y metadatos JSON.

---

## 3. Diseño del Flujo de Sucesión de Rectores (Rector Succession Design)

### A. Contexto y Problema
Actualmente, `RectorOnboardingService.invite_rector` verifica si existe un Rector activo (`UserRole.is_active == True`). Si existe, rechaza la operación con `409 Conflict (RECTOR_ALREADY_EXISTS)`. No existe un endpoint para desvincular al rector saliente cuando este es trasladado, renuncia o concluye su período.

### B. Especificación del Flujo de Sucesión
1. **Autoridad Requerida**: Exclusivo para `superadmin` o `national_admin` (Ministerio de Educación Nacional).
2. **Permiso Atómico**: Requiere `users:create_rector` (o `institutions:update`) con alcance territorial nacional (`auth.scope.is_national()`).
3. **Endpoint Propuesto**:
   - `POST /api/v1/institutions/{institution_id}/rector/revoke`
   - Payload:
     ```json
     {
       "reason": "TRASLADO_DIRECTIVO",
       "justification": "Resolución MEN No. 4589 de 2026",
       "effective_date": "2026-08-30"
     }
     ```
4. **Comportamiento Transaccional Atómico**:
   - Se localiza el `UserRole` activo con rol `rector` para la institución (`SELECT ... FOR UPDATE`).
   - Se actualiza `UserRole.is_active = False`.
   - Se revocan todas las invitaciones de rector pendientes (`is_revoked = True`).
   - El `User` saliente conserva su historial y registros de auditoría (integridad referencial intacta).
   - Se registra el evento de auditoría `RECTOR_REVOKED`.
5. **Habilitación Inmediata de Sucesor**:
   - Al quedar la institución con 0 rectores activos, el Administrador Nacional puede ejecutar de inmediato `POST /api/v1/institutions/{id}/rector-invitation` para emitir el enlace seguro al nuevo Rector.
6. **Interfaz de Usuario en Frontend**:
   - En [InstitutionsView.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/admin/InstitutionsView.tsx), en colegios con rector activo, se mostrará la acción *"Reemplazar Rector / Declarar Vacancia"* que abre el modal de confirmación con registro de justificación oficial.

---

## 4. Diseño del Onboarding Seguro de Acudientes (Guardian Onboarding Design)

### A. Principios Rectores
1. **Preservación de `OPEN-DECISION-3A-01`**: Los acudientes pueden existir en la base de datos sin cuenta de usuario para trámites presenciales o rurales.
2. **Auto-Activación Tokenizada**: Un acudiente registrado en el colegio puede solicitar la creación de su acceso web validando la información de su hijo matriculado.

### B. Flujo de Auto-Activación
1. **Solicitud de Activación**:
   - Endpoint: `POST /api/v1/auth/guardians/request-activation`
   - Payload:
     - Documento del Acudiente (`document_type`, `document_number`).
     - Documento o Código de Matrícula del Estudiante.
     - Correo electrónico para entrega del token.
2. **Validación de Relación en Base de Datos**:
   - El sistema consulta `StudentGuardian` cruzando el documento del acudiente y del estudiante.
   - Si la relación es válida y activa, genera un token criptográfico de 48 bytes (validez: 24 horas) en `GuardianInvitation` (o tabla de tokens genérica).
3. **Definición de Credencial**:
   - El acudiente abre `/auth/accept-guardian-invitation?token={token}`.
   - Establece su contraseña con Argon2id.
   - El backend crea el `User` con rol canónico `guardian` y asocia `Guardian.user_id = user.id`.
4. **Protección Anti-Enumeración y Rate Limiting**:
   - Respuestas uniformes ante documentos no encontrados para evitar rastreo de identidades.
   - Límite estricto de 3 intentos por IP / hora.

---

## 5. Remediación UX en Portal Académico (AcademicHub UX Remediation)

### A. Diagnóstico del Problema
Cuando un usuario ingresa directamente a `/academic?tab=years` pero su rol (ej. Docente) no tiene el permiso `academic_years:read`, el componente [AcademicHub.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/academic/AcademicHub.tsx) filtra la pestaña y ejecuta una redirección automática y silenciosa hacia `academicTabs[0]` (ej. `assignments`). El usuario no comprende por qué no puede ver la sección solicitada.

### B. Solución Técnica Propuesta
- Implementar un estado `unauthorizedTabMessage: string | null` en `AcademicHub.tsx`.
- Si `searchParams.get('tab')` no coincide con ninguna pestaña en `academicTabs`, pero existe en el catálogo general `allTabs`:
  - Se activa un banner superior informativo:
    > ℹ️ *La sección **"{Nombre de la Pestaña}"** no se encuentra disponible para su rol institucional o nivel de permisos actual. Ha sido redirigido a su módulo predeterminado.*
  - El mensaje cuenta con botón de cierre (dismiss) y se limpia al cambiar de pestaña.

---

## 6. Recuperación Segura de Contraseña (Active Account Password Recovery)

### A. Diagnóstico
Actualmente, el cambio de contraseña solo es accesible cuando el usuario ya ha iniciado sesión en [Dashboard.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/Dashboard.tsx) (`changePassword`). Si un usuario activo olvida su contraseña, no existe un flujo de autoservicio desde `/login`.

### B. Arquitectura de Solución
1. **Modelo de Datos Propuesto**:
   - Tabla `password_reset_tokens`:
     - `id` (UUID), `user_id` (FK User), `token_hash` (String 64, SHA-256), `expires_at` (1 hora), `is_used` (Boolean), `created_at` (DateTime).
2. **Endpoints Backend**:
   - `POST /api/v1/auth/forgot-password`:
     - Recibe correo o documento.
     - Si el usuario existe y está activo, genera token de 48 bytes y simula/despacha correo.
     - **Respuesta siempre idéntica**: `200 OK` ("Si los datos coinciden con una cuenta activa, se ha enviado un correo con instrucciones").
   - `POST /api/v1/auth/reset-password`:
     - Recibe `token`, `password`, `password_confirmation`.
     - Valida vigencia y unicidad, actualiza `User.hashed_password` con Argon2id, revoca tokens previos y restablece contadores de bloqueo.
3. **Frontend UX**:
   - Enlace *"¿Olvidó su contraseña?"* en [Login.tsx](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/Login.tsx).
   - Vistas públicas `/auth/forgot-password` y `/auth/reset-password`.

---

## 7. Tableros de Analítica Territorial (Territorial Analytics)

### A. Viabilidad con el Modelo de Datos Existente
El modelo de datos actual cuenta con todos los atributos necesarios para alimentar analíticas agregadas:
- Tabla `institutions`: `department_code`, `municipality_code`, `sector`, `zone`, `calendar`, `is_active`.
- Tabla `campuses`: `is_active`, `dane_code`, `institution_id`.
- Tabla `enrollments`: `status`, `academic_year_id`, `group_id`.
- Tabla `groups`: `grade_id`, `shift`, `capacity_limit`.

### B. Especificación del Endpoint
- `GET /api/v1/analytics/territorial`
- **Permiso Requerido**: `institutions:read`
- **Contención de Alcance**:
  - `department_admin`: Filtrado automático por su `department_id`.
  - `municipality_admin`: Filtrado automático por su `municipality_id`.
  - `national_admin` / `superadmin`: Vista macro de los 33 departamentos y 1,122 municipios.
- **Métricas Retornadas**:
  - Total de instituciones activas vs suspendidas.
  - Total de sedes educativas operativas.
  - Matrícula total agregada por grado y sector (Oficial vs No Oficial).
  - Tasa de ocupación de cupos escolares.

---

## 8. Análisis de Seguridad y Regresión (Regression Safety)

| Componente a Modificar en Fase 7 | Archivos Afectados | Permisos Involucrados | Riesgo de Regresión | Mitigación |
| :--- | :--- | :--- | :---: | :--- |
| **Sucesión de Rectores** | `institutions.py`, `rector_onboarding_service.py`, `InstitutionsView.tsx` | `users:create_rector`, `institutions:update` | **Bajo** | Aislamiento transaccional estricto con bloqueo de fila (`FOR UPDATE`). |
| **Onboarding de Acudientes** | `auth.py`, `guardian_service.py`, `AcceptGuardianInvitation.tsx` | `guardians:create`, `guardians:read` | **Bajo** | Flujo desacoplado que no afecta a acudientes offline existentes. |
| **Remediación UX AcademicHub** | `AcademicHub.tsx` | N/A (Solo presentación en frontend) | **Mínimo** | Preserva la lógica de filtrado `useMemo` y validación en backend. |
| **Recuperación de Contraseñas** | `auth.py`, `auth_service.py`, `Login.tsx`, `ResetPassword.tsx` | Público / Anti-enumeración | **Medio** | Tokens de un solo uso con caducidad corta (1h) y rate limiting. |
| **Analítica Territorial** | `analytics.py`, `analytics_service.py`, `TerritorialDashboard.tsx` | `institutions:read` | **Bajo** | Consultas agregadas de solo lectura con índices compuestos por DANE. |

---

## 9. Plan de Implementación por Sub-Fases (Implementation Phasing)

### Sub-Fase 7A — UX de Acceso, Experiencia de Acudientes y Recuperación de Clave
1. **Objetivo**: Elevar la usabilidad y autoservicio para la comunidad escolar (acudientes, estudiantes y docentes).
2. **Alcance**:
   - Banner informativo en `AcademicHub.tsx`.
   - Flujo de "Olvidé mi contraseña" en frontend y backend.
   - Endpoint de solicitud de auto-activación de acudientes vinculados.
3. **Criterios de Aceptación**:
   - Redirección con mensaje visible ante parámetros URL restringidos.
   - Recuperación de clave 100% funcional con Argon2id.
   - Pruebas unitarias de tokens y anti-enumeración superadas.

### Sub-Fase 7B — Gobernanza y Sucesión de Rectores
1. **Objetivo**: Habilitar el reemplazo formal y declaratoria de vacancia directiva por el Ministerio de Educación.
2. **Alcance**:
   - Endpoint `POST /api/v1/institutions/{id}/rector/revoke`.
   - Modal de sucesión y declaratoria de vacancia en `InstitutionsView.tsx`.
   - Evento de auditoría `RECTOR_REVOKED`.
3. **Criterios de Aceptación**:
   - Desactivación atómica de `UserRole` saliente.
   - Capacidad inmediata de emitir nueva invitación al rector entrante.
   - 100% de pruebas de aislamiento multi-inquilino aprobadas.

### Sub-Fase 7C — Analítica Territorial para Secretarías de Educación
1. **Objetivo**: Proveer tableros macroscópicos a Secretarías Departamentales y Municipales.
2. **Alcance**:
   - Endpoint agregado `GET /api/v1/analytics/territorial`.
   - Componente visual `TerritorialDashboard.tsx`.
3. **Criterios de Aceptación**:
   - Contención territorial estricta (Secretaría de Antioquia no puede ver datos de Cundinamarca).
   - Tiempo de respuesta de consulta agregada < 250ms.

---

## 10. Estado de Gobernanza y Cierre

```
PHASE_7_PLANNING_COMPLETE = TRUE
IMPLEMENTATION_EXECUTED = FALSE
CODE_MODIFICATIONS = 0
DATABASE_MODIFICATIONS = 0
CANONICAL_MUTATIONS = 0
FINAL_DECISION = NO-GO
PROMOTION_EXECUTED = FALSE
PROMOTION_AUTHORIZED = FALSE
AUTHORIZATION_REQUIRED = TRUE
```
