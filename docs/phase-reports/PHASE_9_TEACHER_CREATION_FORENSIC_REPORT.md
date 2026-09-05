# INFORME FORENSE DE DIAGNÓSTICO Y REMEDIACIÓN — FASE 9A/9E
# ERROR HTTP 422 EN `POST /api/v1/teachers` (CREACIÓN DE PERFIL DOCENTE)

**Fecha:** 2026-08-29  
**Ambiente:** PEvN Pre-producción / PostgreSQL  
**Módulo:** Gestión Académica (`TeachersView.tsx` -> `POST /api/v1/teachers`)  
**Estado:** **DIAGNÓSTICO COMPLETO Y REMEDIACIÓN IMPLEMENTADA/VERIFICADA**

---

## 1. CAUSA RAÍZ FORENSE DEL ERROR HTTP 422

### Resumen del Hallazgo
Al registrar un perfil docente desde la interfaz web institucional, el formulario envió el valor `"8788"` en el campo de entrada `user_id`:
```json
{
  "user_id": "8788",
  "specialty_area": "Licenciatura en Ciencias Básicas",
  "contract_type": "PROPIEDAD",
  "escalafon_grade": "14"
}
```

### Contrato del Backend y Falla de Validación
- En `backend/app/schemas/academic.py`:
  ```python
  class TeacherCreateRequest(BaseModel):
      model_config = ConfigDict(extra="forbid")
      user_id: uuid.UUID = Field(..., description="User account ID")
      specialty_area: str | None = Field(default=None, max_length=150)
      contract_type: TeacherContractType = Field(default=TeacherContractType.PROPIEDAD)
      escalafon_grade: str | None = Field(default=None, max_length=50)
  ```
- **Pydantic Validation Error capturado:**
  - `loc`: `('user_id',)`
  - `type`: `uuid_parsing`
  - `msg`: `Input should be a valid UUID, invalid length: expected length 32 for simple format, found 4`
- **Respuesta HTTP emitida por FastAPI:** `HTTP 422 Unprocessable Content`.

### Defecto Frontend en la Experiencia de Usuario
1. El input de texto en `TeachersView.tsx` permitía enviar cualquier cadena arbitraria sin validación previa de formato UUID (`/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`).
2. El modal de creación no renderizaba alertas de error internas, y el normalizador de errores `normalizeError` de `client.ts` descartaba el array `detail` estructurado de FastAPI al no encontrar la clave `error` de nivel superior, retornando el mensaje genérico `"An unexpected error occurred. Please try again later."` / `"Error del servidor (422)"`.

---

## 2. MATRIZ DE VERIFICACIÓN DE REGLAS DE NEGOCIO DOCENTE

| Verificación | Regla Canónica | Comportamiento Backend | Estado |
| :--- | :--- | :--- | :--- |
| **Formato de `user_id`** | Debe ser un UUID v4 canónico (RFC 4122) | Pydantic valida `uuid.UUID` y rechaza cadenas no conformes con 422 | ✅ VERIFICADO |
| **Pertenencia Institucional (Tenant)** | El usuario debe pertenecer a `current_user.institution_id` | `TeacherService` valida `User.institution_id == target_institution_id`, retornando 403 `CROSS_TENANT_MISMATCH` si pertenece a otra sede o no existe | ✅ VERIFICADO |
| **Unicidad 1:1 Docente-Usuario** | Un usuario no puede tener más de 1 perfil docente | `TeacherService` valida `select(Teacher).where(Teacher.user_id == user_id)` y retorna 400 `ACADEMIC_DOMAIN_ERROR` si ya existe | ✅ VERIFICADO |
| **Tipo de Nombramiento** | Enum `TeacherContractType` (`PROPIEDAD`, `PERIODO_PRUEBA`, `PROVISIONAL`, `TEMPORAL`, `HORA_CATEDRA`) | Schema Pydantic valida estrictamente los valores del enum | ✅ VERIFICADO |
| **Grado de Escalafón** | Cadena de texto (Decretos 1278 / 2277, e.g. "14", "2A", "3D") | Almacenado como `str` nullable (máx 50 caracteres) | ✅ VERIFICADO |

---

## 3. REMEDIACIÓN MÍNIMA IMPLEMENTADA

1. **Frontend — Validación de Formato UUID y Renderizado de Error en Modal (`TeachersView.tsx` y `StudentsView.tsx`):**
   - Se añadió expresión regular estricta `UUID_REGEX` en el cliente.
   - Si el usuario ingresa un identificador no conforme (ej. `"8788"`), el formulario previene la llamada al backend y muestra de inmediato:
     `"El ID de Usuario Institucional debe ser un UUID válido de 36 caracteres (ej. 123e4567-e89b-12d3-a456-426614174000)."`
   - Se incorporó el componente `<Alert>` directamente dentro del modal para retroalimentación visual clara.
2. **Frontend — Normalización Inteligente de Errores FastAPI (`client.ts`):**
   - Se extendió `normalizeError` para extraer el arreglo `detail` de las respuestas 422 de FastAPI, mapeando campos y mensajes (ej. `user_id: Input should be a valid UUID`) al objeto `AppApiError` visible al usuario.

---

## 4. EVIDENCIA DE PRUEBAS EJECUTADAS

- **Prueba No-UUID:** `POST /api/v1/teachers` con `"user_id": "8788"` -> HTTP 422 con detalle estructurado `user_id`.
- **Prueba Cross-Tenant:** Intento de asociar docente de Institución B a Institución A -> HTTP 403 `CROSS_TENANT_MISMATCH`.
- **Prueba Exitosa:** Creación con UUID de usuario válido en Institución A -> HTTP 201 Created con entidad `Teacher` persistida.
- **Prueba Duplicada:** Creación repetida para el mismo usuario -> HTTP 400 `ACADEMIC_DOMAIN_ERROR`.
- **Frontend Typecheck & Vitest:** 0 errores TypeScript, 33/33 tests frontend exitosos.
