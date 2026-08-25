# ARQUITECTURA DE GESTIÓN ACADÉMICA — FASE 3A
# Plataforma Educativa Virtual Nacional (PEVN)

> **ESTADO DEL DOCUMENTO:** DISEÑO ARQUITECTÓNICO APROBADO EN FASE 3A  
> **ESTADO DE IMPLEMENTACIÓN:** **LA IMPLEMENTACIÓN DE LA FASE 3 NO HA COMENZADO (PHASE 3 IMPLEMENTATION HAS NOT STARTED).**  
> **LÍNEA BASE DE SEGURIDAD:** **LA ARQUITECTURA DE SEGURIDAD Y AUTORIZACIÓN DE LA FASE 2 PERMANECE CONGELADA Y APROBADA (FROZEN & APPROVED).**

---

## 1. Visión General y Propósito

La **Fase 3 (Gestión Académica)** de la Plataforma Educativa Virtual Nacional (PEVN) establece la estructura operativa, administrativa y curricular para las instituciones educativas públicas de Colombia. Su objetivo es modelar con fidelidad la realidad del sistema educativo colombiano (Ley General de Educación 115 de 1994, Decreto 1075 de 2015 y estándares del Sistema Integrado de Matrícula - SIMAT) sobre la base de aislamiento multi-institucional y control de acceso estricto consolidada en la Fase 2.

```
+-------------------------------------------------------------------------------+
|                       PEVN — CAPA DE GESTIÓN ACADÉMICA                        |
+-------------------------------------------------------------------------------+
|  +------------------------+  +------------------------+  +-----------------+  |
|  |  Estructura Curricular |  | Estructura Organizativa|  |  Matrícula y    |  |
|  |  (Grados, Asignaturas, |  | (Años, Períodos,       |  |  Afiliación     |  |
|  |   Áreas del Saber)     |  |  Sedes, Grupos)        |  |  (Estudiantes)  |  |
|  +------------------------+  +------------------------+  +-----------------+  |
|  +------------------------+  +------------------------+  +-----------------+  |
|  | Asignación Académica   |  | Historia y Trazabilidad|  | Conectividad    |  |
|  | (Docentes, Carga,      |  | (Cambios de Grupo,     |  | Fase 4          |  |
|  |  Directores de Grupo)  |  |  Historial Matrículas) |  | (BigBlueButton) |  |
|  +------------------------+  +------------------------+  +-----------------+  |
+-------------------------------------------------------------------------------+
|        INFRAESTRUCTURA DE SEGURIDAD Y AUTORIZACIÓN HEREDADA (FASE 2)          |
|  - Aislamiento Territorial DANE (scope_contains)                              |
|  - RBAC Centralizado Deny-by-Default (recurso:accion)                         |
|  - Auditoría Persistente Inmutable (DatabaseAuditService)                     |
|  - JWT HS256 en Memoria Volátil + Cookies HttpOnly Strict                     |
+-------------------------------------------------------------------------------+
```

---

## 2. Alineación con el Contexto Educativo Colombiano

El diseño arquitectónico de PEVN adopta formalmente la nomenclatura y jerarquía regulada por el Ministerio de Educación Nacional (MEN) de Colombia:

1. **Niveles Educativos Formales:**
   - **Preescolar:** Grados 00 (Transición / Grado Obligatorio), Jardín, Prejardín.
   - **Básica Primaria:** Grados 1° a 5°.
   - **Básica Secundaria:** Grados 6° a 9°.
   - **Media Académica / Técnica:** Grados 10° y 11° (y ciclo complementario de Normales Superiores 12° y 13° si aplica).
2. **Calendarios Académicos:**
   - **Calendario A:** Febrero a Noviembre (predominante en la mayoría del territorio nacional).
   - **Calendario B:** Septiembre a Junio (aplicado en zonas específicas y colegios bilingües/internacionales).
3. **Áreas Fundamentales y Asignaturas:**
   - Organización curricular por **Áreas del Conocimiento** (e.g., Matemáticas, Humanidades y Lengua Castellana, Ciencias Naturales) y **Asignaturas específicas** (e.g., Álgebra, Geometría, Biología, Química, Física).
4. **Identificación Institucional y Sedes:**
   - Uso obligatorio de códigos DANE institucionales de 12 dígitos para la Institución y códigos de sede DANE para cada Campus.

---

## 3. Principios Arquitectónicos de la Fase 3

1. **Herencia Estricta del Modelo de Tenancy:**  
   Ninguna entidad académica existe fuera del contexto institucional. Toda consulta, inserción o modificación hereda el filtro de `institution_id` (y `campus_id` donde aplique), evaluado por el motor `scope_contains` de Fase 2.
2. **Inmutabilidad de Registros Históricos:**  
   Las matrículas cursadas, calificaciones emitidas (Fase posterior) y asignaciones docentes de años lectivos pasados nunca se eliminan físicamente (`hard delete`). Se preservan como registros históricos inmutables.
3. **Unicidad de Matrícula Activa:**  
   Un estudiante únicamente puede tener **una (1) matrícula en estado ACTIVA** en todo el sistema nacional en un mismo año lectivo, previniendo duplicidades y fraudes de cobertura educativa.
4. **Desacoplamiento entre Identidad de Usuario y Rol Académico:**  
   Un usuario (`User`) mantiene una sola cuenta de acceso, pero sus roles específicos (`Student`, `Teacher`, `Guardian`, `Coordinator`, `Rector`) se modelan mediante perfiles académicos contextualizados.
5. **Compatibilidad con Aulas Virtuales (Fase 4):**  
   Los `Groups` y `SubjectAssignments` servirán como el ancla directa para las salas de conferencia de BigBlueButton en la Fase 4.

---

## 4. Estructura de Módulos de la Fase 3

```
backend/app/
├── models/
│   ├── academic_year.py      # Años lectivos y períodos académicos
│   ├── grade.py              # Grados y niveles educativos
│   ├── subject.py            # Áreas y asignaturas curriculares
│   ├── group.py              # Grupos (cursos/salones) por sede y grado
│   ├── student.py            # Perfil académico del estudiante
│   ├── teacher.py            # Perfil docente y escalafón
│   ├── guardian.py           # Perfil de acudiente / padre de familia
│   ├── enrollment.py         # Matrícula anual y vinculación a grupo
│   └── academic_assignment.py# Asignación docente (profesor-asignatura-grupo)
├── schemas/
│   └── academic/             # Schemas Pydantic v2 de request/response
├── services/
│   └── academic/             # Lógica de dominio y validación de reglas de negocio
└── api/v1/endpoints/
    └── academic/             # Controladores REST protegidos con RBAC y scope
```

---

## 5. Declaración de Parada

> **ESTADO:** DISEÑO ARQUITECTÓNICO APROBADO.  
> **PROHIBICIÓN:** NO SE DEBE IMPLEMENTAR CÓDIGO DE FASE 3 HASTA QUE ESTE DISEÑO HAYA SIDO REVISADO Y FORMALMENTE AUTORIZADO.
