# PEVN — GUION DE DEMOSTRACIÓN GUBERNAMENTAL EN VIVO (RUNBOOK INTERNO)
## DOCUMENTO DE USO OPERATIVO INTERNO PARA EXPOSITORES — DETALLE COMPLETO DE EJECUCIÓN (FASE 0.1C)

> [!WARNING]
> **DOCUMENTO OPERATIVO INTERNO:**
> Este documento contiene los identificadores específicos y cuentas de ejecución del entorno de laboratorio para uso exclusivo del operador técnico de la sesión de demostración. No está destinado a distribución externa formal. Para el expediente institucional de entrega, remítase a `PEVN_GOVERNMENT_DEMONSTRATION_RUNBOOK.md` y su correspondiente PDF sanitizado.

**Destinatarios Internos:** Operadores Técnicos de la Demostración, Expositores Oficiales PEVN  
**Marco Metodológico:** AI Software Factory v1.2 — Internal Operational Runbook  
**Fecha:** 21 de Septiembre de 2026  
**Regla de Seguridad de Credenciales:** Todas las contraseñas se referencian como `[USE EXISTING DEMO CREDENTIAL]`. Ninguna contraseña real o hash es expuesto en este documento.  
**Regla de Datos:** Se utilizan **EXCLUSIVAMENTE los registros de demostración preexistentes en la base de datos**.  
**Protección de Datos de Menores:** Todos los registros corresponden a datos de demostración preexistentes en el entorno de pruebas. La presentación ante autoridades gubernamentales no expone datos personales reales de menores de edad (Ley 1581 de 2012 y Ley 1098 de 2006).

---

## 1. Inventario de Entidades y Datos de Demostración Preexistentes (Entorno Operativo)

| Tipo de Entidad | Registro Existente en Base de Datos | Identificador / Detalle Operativo |
| :--- | :--- | :--- |
| **Institución Educativa** | `COLEGIO GLENN DOMAN` | DANE: `311001088461` / UUID: `404c2ebe-478c-45a0-a9a2-453fc7fcecb3` |
| **Institución Secundaria** | `Institución Educativa Técnica Nacional` | DANE: `111001000001` (para demostración de aislamiento multi-tenant) |
| **Cuenta Rectoría** | `Sandra Chavez Guzman` | Email: `rectoria@glenndoman.edu.co` / Rol: `rector` |
| **Cuenta Coordinación** | Coordinación Académica / Convivencia | Email: `coordinacion@glenndoman.edu.co` / Rol: `coordinator` |
| **Cuenta Docente** | Docente Titular de Asignatura | Email: `profesor@glenndoman.edu.co` / Rol: `teacher` |
| **Cuenta Estudiante** | `Ramiro Rey` | Email: `ramiro.rey@colegio.edu.co` / UUID Estudiante: `09e7beab-090a-46b8-9f51-91cb402c103a` |
| **Cuenta Acudiente** | `Alberto Mercado` (Padre de Ramiro) | Email: `alberto@example.com` / UUID Acudiente: `f0a3f0dd-8750-4aea-8109-65fac72933fc` |
| **Grupo Académico Activo** | Grupo Escolar de Grado Activo | UUID: `e131b6a3-3990-44e8-be23-a36b913e26c3` |
| **Circular Existente** | Circular Oficial de Actividades y Convivencia | ID: `7e83e337-f130-4e0c-b831-4a0bd764c077` (`[QA-F15-20260907]`) |
| **Noticia Existente** | Logro Destacado en Feria de Ciencia | ID: `d2d33449-fb86-4f20-bf2e-3f392beda905` (`[QA-F15-20260907]`) |
| **Incidente Convivencia** | Registro Formativo Tipo I (Ley 1620) | ID: `8daf3c23-dae8-4eb7-8b7b-72845847b425` (`[QA-F15-20260907]`) |

---

## 2. Secuencia Operativa Paso a Paso (23 Hitos)

### Hito 1: Autenticación y Entrada Segura (Login)
- **Rol:** Cualquier rol institucional (inicio con Rector).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/login`.
- **Acción:** Ingresar credenciales institucionales y presionar "Iniciar Sesión".
- **Resultado Esperado:** HTTP 200, JWT en memoria volátil, cookie `pevn_refresh_token` (`HttpOnly`, `SameSite=Strict`), redirección a `/dashboard`.

### Hito 2: Estructura Institucional y Catálogo DANE/DUE
- **Rol:** Rector (`rectoria@glenndoman.edu.co`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.
- **Acción:** Inspeccionar sedes y código DANE (`311001088461`).

### Hito 3: Consola de Rectoría
- **Rol:** Rector (`rectoria@glenndoman.edu.co`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.

### Hito 4: Consola de Coordinación
- **Rol:** Coordinador (`coordinacion@glenndoman.edu.co`).
- **Cuenta Existente:** `coordinacion@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.

### Hito 5: Portal Docente y Dashboard
- **Rol:** Docente (`profesor@glenndoman.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher`.

### Hito 6: Portal del Estudiante
- **Rol:** Estudiante (`ramiro.rey@colegio.edu.co`).
- **Cuenta Existente:** `ramiro.rey@colegio.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/student`.

### Hito 7: Portal del Acudiente y Selector de Hijos
- **Rol:** Acudiente (`alberto@example.com`).
- **Cuenta Existente:** `alberto@example.com` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian`.

### Hito 8: Matrícula SIMAT y Validación de Sobrecupo
- **Rol:** Rector (`rectoria@glenndoman.edu.co`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic/enrollments`.
- **Acción:** Consultar la matrícula activa en grupo (`e131b6a3-3990-44e8-be23-a36b913e26c3`).

### Hito 9: Asignación Académica Docente
- **Rol:** Rector o Coordinador.
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic/assignments`.

### Hito 10: Grupos y Salones Escolares
- **Rol:** Rector (`rectoria@glenndoman.edu.co`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic/groups`.

### Hito 11: Asignaturas y Áreas Fundamentales (Ley 115)
- **Rol:** Rector (`rectoria@glenndoman.edu.co`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic`.

### Hito 12: Creación y Edición de Actividades Académicas
- **Rol:** Docente (`profesor@glenndoman.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher/activities`.

### Hito 13: Entrega de Tareas por el Estudiante (Submissions)
- **Rol:** Estudiante (`ramiro.rey@colegio.edu.co`).
- **Cuenta Existente:** `ramiro.rey@colegio.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/student`.

### Hito 14: Calificación y Devolución Docente
- **Rol:** Docente (`profesor@glenndoman.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher/activities`.

### Hito 15: Planilla de Asistencia Diaria
- **Rol:** Docente (`profesor@glenndoman.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher/attendance`.

### Hito 16: Planilla SIEE y Consolidación Híbrida (Decreto 1290)
- **Rol:** Docente (`profesor@glenndoman.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/teacher/siee-evaluation`.

### Hito 17: Boletines Oficiales de Calificaciones
- **Rol:** Rector (`rectoria@glenndoman.edu.co`) o Acudiente (`alberto@example.com`).
- **Cuenta Existente:** `rectoria@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/academic` $\rightarrow$ *Evaluaciones SIEE* $\rightarrow$ *Boletín Oficial*.

### Hito 18: Observador del Estudiante y Convivencia Escolar (Ley 1620)
- **Rol:** Rector (`rectoria@glenndoman.edu.co`) y Acudiente (`alberto@example.com`).
- **Cuenta Existente:** `alberto@example.com` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ *Observador*.
- **Acción:** Inspeccionar registro `[QA-F15-20260907]` tipificado como Tipo I.

### Hito 19: Comunicaciones Institucionales y Circulares
- **Rol:** Estudiante (`ramiro.rey@colegio.edu.co`) o Acudiente (`alberto@example.com`).
- **Cuenta Existente:** `alberto@example.com` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ *Circulares*.
- **Acción:** Visualizar circular `[QA-F15-20260907]`.

### Hito 20: Firma de Acuse de Recibo Electrónico
- **Rol:** Acudiente (`alberto@example.com`).
- **Cuenta Existente:** `alberto@example.com` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/guardian` $\rightarrow$ Detalle de la circular.

### Hito 21: Aulas Virtuales Sincrónicas (Integración BigBlueButton)
- **Rol:** Docente (`profesor@glenndoman.edu.co`) y Estudiante (`ramiro.rey@colegio.edu.co`).
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Ruta de Navegación:** `/virtual-classrooms`.

### Hito 22: Auditoría Técnica y Censura de Secretos
- **Rol:** SuperAdmin o Auditor Técnico.
- **Cuenta Existente:** Inspección de tabla `audit_logs`.
- **Ruta de Navegación:** Consola/DB.

### Hito 23: Aislamiento Multi-Tenant y Barrera Anti-IDOR
- **Rol:** Docente o Estudiante de `COLEGIO GLENN DOMAN`.
- **Cuenta Existente:** `profesor@glenndoman.edu.co` / `[USE EXISTING DEMO CREDENTIAL]`.
- **Acción:** Intentar consultar recurso de otra institución (`Institución Educativa Técnica Nacional`, DANE `111001000001`).
- **Resultado Esperado:** Blind 404.

---

## 3. Resumen Operativo de Tiempos
- **Recorrido Completo (23 Hitos):** ~32 a 38 minutos.
- **Recorrido Sintético (11 Hitos):** ~15 a 18 minutos.
- **Recorrido Técnico Especializado (6 Hitos):** ~12 a 15 minutos.
