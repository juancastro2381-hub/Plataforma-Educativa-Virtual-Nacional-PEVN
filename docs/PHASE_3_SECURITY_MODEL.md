# MODELO DE AMENAZAS Y SEGURIDAD ACADÉMICA — FASE 3A
# Plataforma Educativa Virtual Nacional (PEVN)

> **ESTADO:** DISEÑO ARQUITECTÓNICO — EXTENSIÓN STRIDE PARA GESTIÓN ACADÉMICA  
> **LÍNEA BASE DE SEGURIDAD:** PROTECCIÓN DE DATOS DE MENORES Y BLINDAJE MULTI-TENANT CON AUDITORÍA PERSISTENTE.

---

## 1. Análisis de Amenazas STRIDE en el Dominio Académico

```
+-------------------+----------------------------------------------------+----------------------------------------------------+
| AMENAZA (STRIDE)  | ESCENARIO DE ATAQUE POTENCIAL                      | CONTROL ARQUITECTÓNICO DE MITIGACIÓN               |
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Spoofing          | Un usuario suplanta a un docente para modificar    | Autenticación JWT en RAM + verificación de perfil  |
| (Suplantación)    | la asignación de grupos o información de alumnos.  | en Base de Datos vinculado a session_user_id.      |
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Tampering         | Modificación maliciosa del `group_id` o estado de  | Integridad transaccional ACID, llaves foráneas con |
| (Manipulación)    | matrícula para registrar estudiantes sin cupo.     | RESTRICT y validación de unicidad en base de datos.|
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Repudiation       | Un directivo niega haber retirado a un estudiante  | Registro obligatorio en `audit_logs` con IP,       |
| (Repudio)         | o alterado la carga académica de un docente.       | actor_id, target_id y timestamp inmutable.         |
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Information       | Fuga de información personal de menores de edad    | Filtros de aislamiento DANE (`scope_contains`),    |
| Disclosure        | (EPS, condición de discapacidad, acudientes).      | serialización Pydantic con exclusión de PII.       |
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Denial of Service | Envío masivo de inscripciones concurrentes para    | Transacciones con bloqueo a nivel de fila y        |
| (Denegación Serv.)| exceder la capacidad de cupos de un grupo.         | Rate Limiting distribuido.                         |
+-------------------+----------------------------------------------------+----------------------------------------------------+
| Elevation of      | Ataque IDOR/BOLA donde un directivo de la I.E. A   | Validación obligatoria de tenancy mediante el      |
| Privilege         | traslada estudiantes de la I.E. B alterando IDs.   | servicio `CentralizedAuthorizationService`.        |
+-------------------+----------------------------------------------------+----------------------------------------------------+
```

---

## 2. Mitigación de Vulnerabilidades Críticas de Acceso

### 2.1. Prevención de IDOR / BOLA (Insecure Direct Object Reference)
- **Problema:** Enviar `POST /api/v1/enrollments` con un `student_id` de otra institución o un `group_id` de otro colegio.
- **Defensa en Profundidad:**
  1. En el Service Layer, se recupera el registro `Group` y se extrae su `institution_id`.
  2. Se ejecuta `await auth_service.require(context, Permission("enrollments", "create"), target_scope=group_scope)`.
  3. Se valida que el `Student.institution_id` pertenezca exactamente a la misma institución del grupo. Si no coincide, se deniega la operación con `403 Forbidden` y se genera una alerta de seguridad auditada.

### 2.2. Protección Especial de Datos Sensibles de Menores de Edad (Habeas Data)
- En Colombia (Ley Estatutaria 1581 de 2012 de Protección de Datos Personales), los datos de niños, niñas y adolescentes tienen categoría de protección reforzada.
- **Reglas del Modelo:**
  - Los campos de salud (`eps`, `blood_type`, `has_disability`, `disability_type`) solo son accesibles por roles administrativos institucionales (`rector`, `coordinator`) y el propio estudiante/acudiente.
  - Los docentes solo tienen acceso a los datos pedagógicos y de contacto de emergencia de sus estudiantes asignados.
