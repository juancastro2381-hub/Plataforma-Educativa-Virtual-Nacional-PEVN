# INFORME DE DIAGNÓSTICO FORENSE (READ-ONLY) — FASE H2
## DESFASE DE FECHA EN VISUALIZACIÓN DE ASISTENCIA ESCOLAR (PORTAL ESTUDIANTE)
**Plataforma Educativa Virtual Nacional (PEVN)**  
**Fecha:** 12 de septiembre de 2026  
**Carácter de la tarea:** EXCLUSIVAMENTE FORENSIC / READ-ONLY (Sin modificaciones de código ni datos)  
**Resultado del Gate:** `DIAGNOSIS_PASS`

---

## 1. OBJETIVO

Investigar de manera forense y en modo estrictamente **READ-ONLY** la inconsistencia detectada durante la Validación Funcional Humana H2 de Asistencia Escolar, donde un registro de asistencia tomado por el docente para el **12/09/2026** (Materia: *Matemáticas - Segundo*, Estudiante: *Samuel Rua*) aparece visualizado en el Portal Estudiante como correspondiente al **11/09/2026**.

Determinar con evidencia exacta la capa donde se origina el desfase (UI Docente, API Request, Backend, Base de Datos PostgreSQL, API Estudiante o Frontend Estudiante) y clasificar el hallazgo sin alterar código de producto, base de datos ni datos de prueba QA.

---

## 2. CONTEXTO DE LA INCIDENCIA

1. El usuario registró manualmente desde el **Portal Docente** una sesión de asistencia con:
   - **Fecha de sesión:** `12/09/2026`
   - **Grupo:** `Grupo 2`
   - **Materia:** `Matemáticas - Segundo`
   - **Estado:** Presente
2. La interfaz docente mostró la confirmación de guardado:
   > *"¡Asistencia escolar registrada y guardada exitosamente!"*
3. Al ingresar al **Portal Estudiante** con el usuario Samuel Rua y consultar la pestaña **"Mi Asistencia"**, el usuario reportó:
   - Las fechas visibles corresponden al `11/09/2026`.
   - No se observa la fila con la fecha esperada del `12/09/2026 — Matemáticas - Segundo — Presente`.
   - Se observaba además un registro previo con fecha `11/09/2026`.

---

## 3. EVIDENCIA OBSERVADA EN BASE DE DATOS (POSTGRESQL)

Se ejecutaron consultas de solo lectura en la base de datos PostgreSQL de desarrollo (`daily_attendances`):

### 3.1 Registros reales almacenados para Samuel Rua (`student_id: 2b049452-de46-48be-80b1-45291c9387d9`)

```sql
SELECT da.id, da.attendance_date::text, da.status, da.created_at, da.updated_at, s.name as subject_name
FROM daily_attendances da
LEFT JOIN subjects s ON da.subject_id = s.id
WHERE da.student_id = '2b049452-de46-48be-80b1-45291c9387d9'
ORDER BY da.created_at ASC;
```

**Resultado de la consulta:**

| ID Registro | `attendance_date` (DB) | Estado | Materia | `created_at` (UTC) | Hora local Colombia (UTC-5) |
|---|:---:|:---:|---|---|---|
| `03fb3bf3-cc94-4027-816f-3bf9973ae5a5` | **`2026-09-12`** | `ABSENT` | `None` (Jornada General) | `2026-09-12 14:29:20.863023+00:00` | 12/09/2026 09:29:20 AM |
| `4d09f4ea-b2b6-4231-8ae9-6f998d4912fd` | **`2026-09-12`** | `PRESENT` | `Matemáticas - Segundo` | `2026-09-13 00:08:24.622499+00:00` | 12/09/2026 07:08:24 PM |

### 3.2 Hallazgo Inmediato sobre los Datos
1. **La prueba recién ejecutada por el usuario SÍ EXISTE en la base de datos** bajo el ID `4d09f4ea-b2b6-4231-8ae9-6f998d4912fd`, fue creada a las 19:08:24 del 12/09/2026 (hora Colombia), con `status = PRESENT` y materia `Matemáticas - Segundo`.
2. **Ambos registros en la base de datos tienen `attendance_date = 2026-09-12`**.
3. **NO existe ningún registro en la base de datos con fecha `2026-09-11`**.
4. El "registro previo" que el usuario creía que era del 11/09/2026 (`03fb3bf3-...`) en realidad **también fue registrado para el 12/09/2026**, pero la interfaz de estudiante lo mostraba como 11/09/2026.
5. El nuevo registro (`4d09f4ea-...`) también fue almacenado como `2026-09-12`, pero la interfaz de estudiante lo muestra igualmente como 11/09/2026.

---

## 4. ARQUITECTURA DEL FLUJO DE FECHA

```
[ Docente en UI ]
  Selecciona fecha: 12/09/2026
  <input type="date"> -> value: "2026-09-12"
       │
       ▼
[ HTTP Request (POST) ]
  Payload JSON: {"attendance_date": "2026-09-12", "records": [...]}
       │
       ▼
[ Backend Controller & Pydantic ]
  DailyAttendanceBatchRequest: attendance_date = datetime.date(2026, 9, 12)
       │
       ▼
[ Servicio y ORM SQLAlchemy ]
  DailyAttendance(attendance_date=date(2026, 9, 12))
  Column type: Date (sin hora, sin zona horaria)
       │
       ▼
[ PostgreSQL Storage ]
  Tabla: daily_attendances
  Columna: attendance_date (tipo: date)
  Valor persistido: 2026-09-12
       │
       ▼
[ API Estudiante (GET /student/attendance) ]
  Query: select(DailyAttendance).where(student_id == ...)
  ORM: r.attendance_date = datetime.date(2026, 9, 12)
  Pydantic StudentAttendanceItemResponse: attendance_date: date
  Serialización JSON: "attendance_date": "2026-09-12"
       │
       ▼
[ Frontend Portal Estudiante ]
  item.attendance_date = "2026-09-12"
  Llamada: formatDate(item.attendance_date)
       │
       ▼ [!!! PUNTO DE FALLA / DESFASE !!!]
  formatDate("2026-09-12"):
  d = new Date("2026-09-12")  --> Interpreta como UTC Medianoche: 2026-09-12T00:00:00Z
  Intl.DateTimeFormat('es-CO') --> Evalúa en Zona Horaria Local (Colombia: UTC-5)
  2026-09-12T00:00:00Z - 5h   --> 2026-09-11T19:00:00 (11 de Septiembre, 7:00 PM)
  Resultado renderizado: "11 de septiembre de 2026"
```

---

## 5. TRAZABILIDAD UI → API → DB → API → UI Y VALORES REALES

| Capa | Componente / Archivo | Valor Inspeccionado | Estado |
|---|---|---|:---:|
| **1. Selección UI Docente** | `TeacherAttendanceView.tsx` (`<input type="date">`) | `"2026-09-12"` | ✅ Correcto |
| **2. Payload Enviado** | `POST /groups/{group_id}/attendance` | `{"attendance_date": "2026-09-12"}` | ✅ Correcto |
| **3. Backend Recibido** | `teacher_portal.py` / `DailyAttendanceBatchRequest` | `datetime.date(2026, 9, 12)` | ✅ Correcto |
| **4. Valor Persistido DB** | PostgreSQL `daily_attendances.attendance_date` | `2026-09-12` (tipo `date`) | ✅ Correcto |
| **5. API Estudiante (Respuesta)** | `GET /student/attendance` | `"attendance_date": "2026-09-12"` | ✅ Correcto |
| **6. Frontend Estudiante (Props)** | `StudentAttendanceView.tsx` | `item.attendance_date = "2026-09-12"` | ✅ Correcto |
| **7. Conversión `formatDate`** | `frontend/src/utils/index.ts:33` | `new Date("2026-09-12")` $\rightarrow$ UTC medianoche | ❌ **DESFASE** |
| **8. Fecha Renderizada en DOM** | `<td>{formatDate(item.attendance_date)}</td>` | **`"11 de septiembre de 2026"`** | ❌ **INCORRECTO** |

---

## 6. PUNTO EXACTO DEL DESFASE Y CAUSA RAÍZ

### 6.1 Punto Exacto
El desfase se produce **exclusivamente en la capa de presentación del Frontend**, dentro de la función utilitaria [`formatDate`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/utils/index.ts#L31-L40):

```typescript
// frontend/src/utils/index.ts (líneas 31-40)
export function formatDate(date: Date | string | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  if (!date) return ''
  const d = typeof date === 'string' ? new Date(date) : date  // <--- AQUÍ SE PRODUCE EL DESFASE
  return new Intl.DateTimeFormat('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  }).format(d)
}
```

### 6.2 Demostración Técnica y Mecanismo del Estándar ECMAScript
De acuerdo con la especificación oficial de ECMAScript (ECMA-262, Sección 21.4.1.15 *Date Time String Format*):
> *"When the time zone offset is absent, date-only forms (e.g. 'YYYY-MM-DD') are interpreted as a UTC time and date-time forms are interpreted as a local time."*

1. Cuando la API entrega `"2026-09-12"` (cadena ISO de solo fecha):
   `new Date("2026-09-12")` genera una instancia `Date` fijada en `2026-09-12T00:00:00.000Z` (medianoche UTC).
2. En la zona horaria de Colombia (`America/Bogota`, UTC-5):
   La medianoche UTC equivale a las **7:00 PM del día anterior**: `2026-09-11 19:00:00 GMT-0500`.
3. `Intl.DateTimeFormat('es-CO', { ... })`, al no tener especificada la opción `timeZone: 'UTC'`, formatea la fecha en la **zona horaria local del navegador**.
4. Dado que en la zona local la hora corresponde al 11 de septiembre a las 7:00 PM, extrae el día local `11`, mes `septiembre`, año `2026`.
5. Esto causa que **cualquier cadena `"YYYY-MM-DD"` se muestre con 1 día de atraso en cualquier navegador ubicado en zonas horarias de UTC-1 a UTC-12**.

### 6.3 Verificación en Entorno Node.js con `America/Bogota`
```javascript
process.env.TZ = 'America/Bogota';
const s = '2026-09-12';
const d = new Date(s);
// d.toISOString()               --> '2026-09-12T00:00:00.000Z'
// d.toString()                  --> 'Fri Sep 11 2026 19:00:00 GMT-0500'
// Intl.DateTimeFormat('es-CO')  --> '11 de septiembre de 2026'
```

---

## 7. CLASIFICACIÓN DEL HALLAZGO

El hallazgo se clasifica como:
* **D. PROBLEMA DE FRONTEND** combinado con **E. PROBLEMA DE TIMEZONE**:
  La base de datos y la API entregan la fecha exacta (`"2026-09-12"`), pero el frontend realiza una conversión implícita de zona horaria al instanciar `new Date("YYYY-MM-DD")` sin tratamiento de solo-fecha, desplazando la fecha un día hacia atrás en zonas horarias occidentales como Colombia (UTC-5).

---

## 8. IMPACTO FUNCIONAL

1. **Registro Diario de Asistencia:** **CERO IMPACTO**. La asistencia queda guardada correctamente en base de datos en la fecha exacta seleccionada por el docente (`2026-09-12`).
2. **Planilla del Portal Docente:** **CERO IMPACTO**. El portal docente trabaja con el valor directo `"YYYY-MM-DD"` del selector de fecha y consulta por el query param `attendance_date=2026-09-12`.
3. **Portal Acudiente (Guardian Portal):** **CERO IMPACTO**. En `GuardianAttendanceView.tsx` (línea 202), la fecha se renderiza directamente como texto `{rec.attendance_date}` (`"2026-09-12"`), por lo que no sufre el desfase.
4. **Métricas y Estadísticas de Asistencia:** **CERO IMPACTO**. Los porcentajes de asistencia (`attendance_rate`), total de sesiones, fallas y tardanzas se calculan en el backend en `StudentPortalService.list_attendance` basándose en los registros reales.
5. **SIEE y Criterios de Promoción Escolar:** **CERO IMPACTO**. El motor SIEE evalúa el porcentaje de asistencia directamente en base de datos.
6. **Portal Estudiante (Visualización):** **IMPACTO VISUAL EXCLUSIVO**. En la tabla de historial de asistencia del estudiante, el texto de la columna "FECHA" muestra `11 de septiembre de 2026` en lugar de `12 de septiembre de 2026`.

---

## 9. RIESGO Y REGRESIÓN POTENCIAL EN OTROS MÓDULOS

Se realizó una auditoría estática de todos los usos de `formatDate` y `formatDateTime` en el frontend:

| Componente | Línea | Campo Formateado | Formato de Entrada | Riesgo / Diagnóstico |
|---|:---:|---|---|---|
| `StudentAttendanceView.tsx` | 258 | `item.attendance_date` | `"YYYY-MM-DD"` (solo fecha) | ⚠️ **Desfase confirmado (-1 día)** |
| `StudentProfileView.tsx` | 129 | `profile.birth_date` | `"YYYY-MM-DD"` (solo fecha) | ⚠️ **Desfase potencial (-1 día en fecha de nacimiento)** |
| `StudentGradesView.tsx` | 521 | `g.graded_at` | `"YYYY-MM-DDTHH:MM:SSZ"` | ✅ Sin desfase (usa `formatDateTime` con hora ISO) |
| `StudentTaskDetailModal.tsx` | 409 | `activity.due_date` | `"YYYY-MM-DDTHH:MM:SSZ"` | ✅ Sin desfase (usa `formatDateTime` con hora ISO) |
| `TeacherSubmissionsModal.tsx` | 400 | `submitted_at` | `"YYYY-MM-DDTHH:MM:SSZ"` | ✅ Sin desfase (usa `formatDateTime` con hora ISO) |
| `VirtualClassroomsView.tsx` | Varios | `scheduled_start_time` | `"YYYY-MM-DDTHH:MM:SSZ"` | ✅ Sin desfase (usa `formatDateTime` con hora ISO) |

---

## 10. ARCHIVOS Y COMPONENTES INVOLUCRADOS

* **Archivo causante del desfase:**
  [`frontend/src/utils/index.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/utils/index.ts) (función `formatDate`, líneas 31-40).
* **Componente de visualización afectado:**
  [`frontend/src/pages/student/StudentAttendanceView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentAttendanceView.tsx) (línea 258).
* **Componente secundario con riesgo idéntico:**
  [`frontend/src/pages/student/StudentProfileView.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/student/StudentProfileView.tsx) (línea 129).

---

## 11. RECOMENDACIÓN DE CORRECCIÓN (NO IMPLEMENTADA)

> [!NOTE]
> En cumplimiento estricto de las reglas innegociables de esta tarea, **NO se ha modificado ningún archivo**. La siguiente corrección se presenta como recomendación técnica para cuando sea autorizada explícitamente:

Ajustar la función utilitaria `formatDate` en `frontend/src/utils/index.ts` para que, cuando el valor recibido sea una cadena de solo fecha con formato `"YYYY-MM-DD"`, se interprete como fecha del calendario local en lugar de forzarse a UTC medianoche:

```typescript
export function formatDate(date: Date | string | null | undefined, options?: Intl.DateTimeFormatOptions): string {
  if (!date) return ''
  let d: Date
  if (typeof date === 'string') {
    // Si es formato solo fecha YYYY-MM-DD, descomponer en partes locales para evitar desfase de zona horaria
    const dateOnlyMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(date)
    if (dateOnlyMatch) {
      const [, year, month, day] = dateOnlyMatch
      d = new Date(Number(year), Number(month) - 1, Number(day))
    } else {
      d = new Date(date)
    }
  } else {
    d = date
  }
  return new Intl.DateTimeFormat('es-CO', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    ...options,
  }).format(d)
}
```

Esta solución es 100% retrocompatible:
- Si recibe un string `"2026-09-12"`, construye `new Date(2026, 8, 12)` en hora local $\rightarrow$ formatea como `"12 de septiembre de 2026"`.
- Si recibe un timestamp ISO con hora `"2026-09-12T18:30:00Z"`, continúa usando `new Date(date)` con conversión de zona horaria estándar.
- Corrige simultáneamente `StudentAttendanceView` y `StudentProfileView`.

---

## 12. PRUEBAS RECOMENDADAS TRAS UNA EVENTUAL CORRECCIÓN

1. **Prueba unitaria en Frontend:**
   Verificar que `formatDate('2026-09-12')` devuelva `"12 de septiembre de 2026"` en cualquier zona horaria (incluyendo `America/Bogota`, UTC-5).
2. **Prueba en navegador:**
   Ingresar a Samuel Rua $\rightarrow$ **Mi Asistencia**, y verificar que ambas filas muestren `12 de septiembre de 2026`.
3. **Prueba de regresión TypeScript:**
   `npm run typecheck` en frontend.

---

## 13. ELEMENTOS FUERA DE ALCANCE

- Modificaciones en base de datos o migraciones (esquema verificado e intacto).
- Modificaciones en endpoints backend de asistencia (funcionamiento 100% correcto y verificado).
- Modificaciones a cualquier componente fuera de la visualización de fechas.

---

## 14. CONCLUSIÓN Y VEREDICTO DE GATE

El diagnóstico forense ha determinado con evidencia concluyente, trazabilidad matemática y pruebas de base de datos que:
1. El backend y la base de datos PostgreSQL persistieron de forma **íntegra e inalterada** el registro de asistencia del usuario con fecha `2026-09-12`.
2. El registro esperado existe y contiene `status = PRESENT` y `subject = Matemáticas - Segundo`.
3. El desfase visual es ocasionado exclusivamente por la interpretación UTC en `new Date("YYYY-MM-DD")` dentro de `formatDate` en el frontend, la cual resta 5 horas para la zona horaria de Colombia proyectando la fecha al 11 de septiembre a las 19:00 horas.
4. No se realizó ninguna modificación de código ni de datos durante este procedimiento.

* **Resultado del Gate H2:** **`DIAGNOSIS_PASS`**
