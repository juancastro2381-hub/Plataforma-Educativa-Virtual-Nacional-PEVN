# PEVN — Fase 14C: Certificación y Guía de Validación Manual del Portal de Acudientes y Familias

**Documento:** Informe de Certificación de Frontend y Lista de Chequeo de Validación Manual  
**Fase:** Fase 14C — Portal de Acudientes y Familias (Frontend)  
**Ruta Principal:** `/guardian`  
**Estado:** ✅ **100% IMPLEMENTADO Y CERTIFICADO**  
**Fecha:** Septiembre 2026  

---

## 1. Resumen Ejecutivo de Implementación

En la **Fase 14C**, se implementó el **Portal de Acudientes y Familias** en el frontend de PEVN bajo una filosofía estricta de:
- **Seguridad primero y Aislamiento Multi-Inquilino**: El acudiente solo puede seleccionar y visualizar información de los estudiantes vinculados bajo su patria potestad o tutoría legal según el endpoint certificado `GET /api/v1/guardian/students`.
- **Acompañar, Monitorear y Comunicar (Rol Observador / Supervisor)**: Los padres y tutores supervisan el desempeño escolar, tareas, calificaciones, asistencia y clases sincrónicas, pero **no** tienen facultades de entrega de tareas, alteración de notas ni edición de registros.
- **Prevención de Fuga de Datos y Datos Obsoletos (Stale Data Prevention)**: Al alternar entre hijos, el estado local del hijo previo se purga inmediatamente antes de solicitar y renderizar la información del nuevo estudiante seleccionado.
- **Zero Mock / API-Consuming Only**: La interfaz consume exclusivamente los 8 contratos certificados de backend de la Fase 14A, con placeholders honestos para módulos previstos en la Fase 15 (Comunicados, Noticias, Convivencia).

---

## 2. Endpoints Backend Consumidos (Fase 14A)

El portal interactúa exclusivamente a través del servicio [`frontend/src/services/guardian.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/guardian.ts):

| Método | Endpoint Backend | Descripción |
| :--- | :--- | :--- |
| `GET` | `/api/v1/guardian/profile` | Información de identidad institucional, documento, contacto y total de tutorados. |
| `GET` | `/api/v1/guardian/students` | Directorio autorizado de estudiantes/hijos bajo tutoría legal del acudiente autenticado. |
| `GET` | `/api/v1/guardian/students/{student_id}/overview` | Métricas clave: asignaturas, promedio general, tareas pendientes, inasistencias y clases próximas. |
| `GET` | `/api/v1/guardian/students/{student_id}/activities` | Listado y detalle pedagógico de tareas, talleres y trabajos escolares asignados. |
| `GET` | `/api/v1/guardian/students/{student_id}/grades` | Libreta de calificaciones, evaluaciones formativas, escala cualitativa y feedback docente. |
| `GET` | `/api/v1/guardian/students/{student_id}/attendance` | Historial de asistencia, sesiones totales, porcentaje y desglose de inasistencias. |
| `GET` | `/api/v1/guardian/students/{student_id}/virtual-classrooms` | Agenda de clases sincrónicas y sesiones programadas. |
| `GET` | `/api/v1/guardian/students/{student_id}/virtual-classrooms/{classroom_id}` | Detalle institucional de la clase virtual y enlace de acompañamiento. |

---

## 3. Estructura de Navegación y Subvistas Implementadas

La navegación está construida con arquitectura **URL-Driven State** (`/guardian?tab=...&student_id=...`), permitiendo enlaces directos, persistencia de pestaña activa y navegación fluida entre 11 módulos:

1. **Inicio (`tab=dashboard`)**:
   - Cabecera institucional con datos del acudiente e institución educativa.
   - Selector contextual de hijos con avatar, grado, grupo y parentesco.
   - Banners de alerta para tareas por vencer, inasistencias acumuladas y clases de hoy.
   - 4 Tarjetas métricas KPI: Asignaturas Cursadas, Promedio General, Tareas Pendientes, Porcentaje de Asistencia.
   - Resumen rápido de tareas pendientes, clases virtuales de hoy y últimas calificaciones.
2. **Mis Hijos (`tab=students`)**:
   - Directorio completo de estudiantes vinculados con código SIMAT, sede, grado, grupo y estado de matrícula.
   - Botón directo para seleccionar y activar el monitoreo del hijo correspondiente.
3. **Rendimiento (`tab=academic`)**:
   - Promedio general acumulado con escala de desempeño institucional MEN.
   - Desglose por asignaturas, asignaciones evaluadas y retroalimentación docente.
4. **Tareas (`tab=tasks`)**:
   - Filtros por estado pedagógico: Todas, Pendientes, Entregadas, Calificadas, Vencidas.
   - Tarjetas informativas con asignatura, fecha límite, calificación obtenida y badge de estado.
   - Modal de detalle de tarea **100% de Solo Lectura** (instrucciones, recursos, feedback docente, sin inputs de entrega).
5. **Calificaciones (`tab=grades`)**:
   - Libreta oficial de notas con promedio de asignaturas, tipo de actividad y escala cuantitativa/cualitativa.
6. **Asistencia (`tab=attendance`)**:
   - Tarjetas de resumen: Porcentaje global, Asistencias, Inasistencias, Retardos, Excusadas.
   - Tabla cronológica de registros con estado de asistencia y observaciones docentes.
7. **Clases Virtuales (`tab=virtual-classes`)**:
   - Agenda cronológica de clases en vivo y sesiones programadas.
   - Modal de acompañamiento parental con identificador de sala e instrucciones de supervisión.
8. **Comunicados (`tab=communications`)**:
   - Vista controlada con banner "Módulo en Desarrollo • Fase 15" y descripción pedagógica.
9. **Noticias (`tab=news`)**:
   - Vista controlada con banner "Módulo en Desarrollo • Fase 15".
10. **Convivencia (`tab=incidents`)**:
    - Vista controlada con banner "Módulo en Desarrollo • Fase 15".
11. **Mi Perfil (`tab=profile`)**:
    - Identidad verificada de acudiente, documento oficial, teléfono, correo, dirección y total de estudiantes vinculados.

---

## 4. Resultados de Verificación Automatizada

### Pruebas Unitarias e Integración (`Vitest`)
- **Suite de Pruebas del Portal**: [`frontend/src/test/GuardianPortal.test.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/test/GuardianPortal.test.tsx)
- **13 de 13 pruebas aprobadas (100% Green)**
  1. `renders Guardian Header and Student Switcher with authorized children`
  2. `renders multi-child switcher with correct avatars, grade info and badges`
  3. `renders key performance metric cards on dashboard (Asignaturas, Promedio, Tareas, Asistencia)`
  4. `switches student context and fetches child-specific data when clicking a different child`
  5. `navigates to "Mis Hijos" view and displays full directory of children`
  6. `navigates to "Rendimiento" view and displays subject breakdown`
  7. `navigates to "Tareas" view and opens strictly READ-ONLY task detail modal (No submission buttons)`
  8. `navigates to "Calificaciones" view and displays evaluation list and average`
  9. `navigates to "Asistencia" view and displays summary statistics and log table`
  10. `navigates to "Clases Virtuales" view and renders agenda and session modal`
  11. `renders Phase 15 "Próximamente" placeholders for Comunicados, Noticias, and Convivencia`
  12. `navigates to "Mi Perfil" view and renders guardian contact info`
  13. `renders empty state gracefully when guardian has zero linked students`

### Suite Global de Frontend
- **11 archivos de prueba, 71 pruebas ejecutadas y aprobadas (100% Green)**.
- **Compilación de Producción (`npm run build`)**: 0 errores de TypeScript (`tsc -b`), bundle generado exitosamente en 4.82s.

---

## 5. Lista de Chequeo para Validación Manual en Navegador

Para certificar visualmente la experiencia de usuario sin recurrir a automatizaciones de navegador:

### Paso 1: Autenticación con Rol Acudiente
- [ ] Iniciar sesión en la plataforma con una cuenta de rol `guardian` (o ingresar como `superadmin` / `institution_admin`).
- [ ] Verificar que en el menú superior aparezca el enlace **"Portal Acudiente"** y en el Dashboard la tarjeta **"Portal de Acudientes y Familias"**.
- [ ] Hacer clic en el enlace y comprobar la redirección a `/guardian`.

### Paso 2: Cabecera y Selector de Hijos
- [ ] Verificar que la cabecera muestre el nombre del acudiente, documento, teléfono, correo y nombre de la institución educativa.
- [ ] Comprobar que en el selector superior aparezcan los botones de cada hijo registrado con su nombre, grado, grupo y parentesco.
- [ ] Hacer clic en el segundo hijo y constatar que:
  - Las métricas se actualizan inmediatamente con los datos del segundo estudiante.
  - El selector resalta con borde oscuro y sombra al estudiante activo.
  - La URL se actualiza con `student_id=...`.

### Paso 3: Monitoreo de Tareas en Modo Solo Lectura
- [ ] Ir a la pestaña **Tareas** (`/guardian?tab=tasks`).
- [ ] Filtrar por "Pendientes" y "Calificadas".
- [ ] Abrir el modal de detalle de una tarea ("Ver Detalle de Tarea").
- [ ] Constatar que **NO exista ningún botón de "Cargar Archivo", "Enviar Tarea" ni campos editables**.
- [ ] Comprobar que se visualicen las instrucciones, fecha de entrega y feedback docente.

### Paso 4: Calificaciones, Rendimiento y Asistencia
- [ ] Ir a **Rendimiento** (`tab=academic`) y comprobar el promedio general y el desglose de materias.
- [ ] Ir a **Calificaciones** (`tab=grades`) y verificar la lista de evaluaciones formativas.
- [ ] Ir a **Asistencia** (`tab=attendance`) y validar el porcentaje global (ej. 90%) y la tabla histórica.

### Paso 5: Clases Virtuales y Placeholders Fase 15
- [ ] Ir a **Clases Virtuales** (`tab=virtual-classes`) y abrir el modal "Consultar Agenda de Clase".
- [ ] Ir a las pestañas **Comunicados**, **Noticias** y **Convivencia**:
  - Validar que cada una muestre el badge `Fase 15` en la barra de pestañas.
  - Verificar que el cuerpo de la vista indique honestamente el estado "Módulo en Desarrollo • Fase 15" con botón "Volver al Inicio".

### Paso 6: Mi Perfil
- [ ] Ir a **Mi Perfil** (`tab=profile`).
- [ ] Validar la visualización del badge "Acudiente Verificado", documento de identidad, teléfono, correo, dirección y total de estudiantes vinculados.
