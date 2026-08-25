# ADR-003: Arquitectura de Dominio Académico, Matrícula y Aislamiento Multi-Tenant

**Estado:** APROBADO EN DISEÑO ARQUITECTÓNICO (FASE 3A)  
**Fecha:** 22 de Agosto de 2026  
**Autores:** Equipo de Arquitectura PEVN  
**Fase de Implementación:** Fase 3 (Gestión Académica)

---

## 1. Contexto

La Plataforma Educativa Virtual Nacional (PEVN) requiere modelar la estructura académica de las instituciones públicas de Colombia (años lectivos, períodos, grados, asignaturas, sedes, grupos, docentes, estudiantes, acudientes y matrículas).

Requisitos críticos del sistema:
1. Respetar el aislamiento multi-institucional estricto implementado en la Fase 2 mediante `scope_contains`.
2. Evitar fraudes de cobertura y duplicidades mediante la garantía de matrícula única activa por año lectivo.
3. Mantener inmutabilidad y trazabilidad histórica de los registros académicos.
4. Desacoplar la identidad del usuario (`User`) de sus perfiles académicos específicos (`Student`, `Teacher`, `Guardian`).
5. Preparar la estructura para servir de ancla en las aulas virtuales con BigBlueButton (Fase 4).

---

## 2. Decisión

Se aprueba la siguiente arquitectura para la Fase 3:

1. **Modelo de Tenancy y Alcance:**  
   Todas las entidades operativas (`academic_years`, `groups`, `subjects`, `teachers`, `students`, `enrollments`, `academic_assignments`) mantienen llaves foráneas explícitas hacia `institutions` (o `campuses`) y heredan el control de acceso de Fase 2.

2. **Invariante de Matrícula Activa Única (Índice Único Parcial):**  
   Se establece un **índice único parcial** a nivel de PostgreSQL:  
   `CREATE UNIQUE INDEX uq_enrollments_single_active_per_year ON enrollments (student_id, academic_year_id) WHERE status = 'ACTIVE';`  
   Esta solución previene a nivel de motor de base de datos la existencia de dos matrículas activas simultáneas para el mismo estudiante en un año lectivo (eliminando carreras concurrentes), permitiendo al mismo tiempo almacenar registros históricos inmutables en estados `WITHDRAWN`, `TRANSFERRED` o `GRADUATED`.

3. **Catálogo Nacional Estandarizado de Grados:**  
   La entidad `Grade` se modela como un **catálogo nacional compartido** sin `institution_id`, garantizando la estandarización curricular según los niveles del MEN (Preescolar, Básica Primaria, Básica Secundaria y Media), mientras que las asignaturas (`subjects`) y grupos (`groups`) mantienen su aislamiento institucional estricto.

4. **Perfiles Académicos Desacoplados:**  
   Se crean tablas de extensión de perfil `students`, `teachers` y `guardians` vinculadas mediante `user_id` a la tabla central `users`.

5. **Preservación del Motor de Seguridad:**  
   No se crean motores paralelos de autenticación ni de roles. Se utilizan los permisos granulares `recurso:accion` y la jerarquía numérica de roles (10 a 100).

6. **Inmutabilidad Histórica:**  
   Los registros académicos cerrados nunca se eliminan físicamente; se utilizan estados de ciclo de vida (`CLOSED`, `ARCHIVED`, `WITHDRAWN`, `TRANSFERRED`) y tablas de bitácora (`group_transfer_history`).

---

## 3. Consecuencias

### Positivas:
- Integración nativa y transparente con el modelo de seguridad de Fase 2.
- Cero riesgo de fuga de datos entre instituciones educativas distintas.
- Cumplimiento estricto con los lineamientos del Ministerio de Educación Nacional (MEN) y el SIMAT.
- Estructura lista para la integración con BigBlueButton en Fase 4 mediante `academic_assignments` y `groups`.

### Negativas / Retos:
- Las consultas que requieran vistas consolidadas a nivel departamental o nacional deben aplicar joins con las tablas territoriales (`departments`, `municipalities`). Se mitiga mediante índices B-Tree compuestos sobre llaves foráneas.

---

## 4. Estado de Implementación

- **Fase 3A:** Diseño arquitectónico y documental completado.
- **Fase 3B:** La implementación de código y migraciones **NO HA COMENZADO**.
