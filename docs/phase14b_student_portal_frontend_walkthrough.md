# PEVN — Phase 14B: Student Portal Frontend Implementation Walkthrough & Forensic Architecture

**Status:** Certified & Verified  
**Date:** September 2026  
**Scope:** Complete implementation and verification of the Student Portal (`/student`) consuming the canonical Phase 14A backend API contract without modifications.

---

## 1. Executive Summary

Phase 14B delivers the complete student-facing experience for the **Plataforma Educativa Virtual Nacional (PEVN)**. Built strictly as an API-consuming, security-first frontend layer, it faithfully renders academic data, evaluation progress, attendance metrics, interactive task management, and virtual classroom workflows.

### Architectural Invariants Upheld:
1. **Zero Backend Contract Modification:** Consumes the certified Phase 14A backend endpoints (`/api/v1/student/*`) without altering schemas or business logic.
2. **Server-Side Identity & Anti-IDOR:** The frontend never transmits or requests `student_id` in URL parameters or request payloads. All data is scoped strictly to the authenticated student's JWT token identity.
3. **Canonical Status Source of Truth:** Dynamic status calculation (`PENDING`, `OVERDUE`, `SUBMITTED`, `GRADED`) is performed exclusively by the backend and consumed directly by UI components.
4. **Design System & Visual Excellence:** Reuses the existing PEVN design system, color tokens, dark/light theme support, accessible badges, skeleton loaders, and interactive modals.
5. **Quality Assurance:** 100% test pass rate (58/58 tests across 10 suites) and clean production bundle compilation (`tsc -b && vite build` passed with zero errors).

---

## 2. API Contract & Integration Mapping

The Student Portal consumes all 10 certified Phase 14A backend endpoints via `studentApi` ([`frontend/src/services/student.ts`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/services/student.ts)):

| # | Endpoint | Method | Frontend Method | Purpose |
|---|---|---|---|---|
| 1 | `/api/v1/student/profile` | `GET` | `studentApi.getProfile()` | Institutional identity, SIMAT code, enrollment status, group, and campus |
| 2 | `/api/v1/student/dashboard` | `GET` | `studentApi.getDashboard()` | Consolidated summary: KPI metrics, urgent tasks, next live class, recent evaluations |
| 3 | `/api/v1/student/subjects` | `GET` | `studentApi.listSubjects()` | Enrolled academic subjects with assigned educators and weekly workload hours |
| 4 | `/api/v1/student/activities` | `GET` | `studentApi.listActivities(filters)` | Comprehensive task directory with filtering by status and subject |
| 5 | `/api/v1/student/activities/{activity_id}` | `GET` | `studentApi.getActivity(id)` | Detailed instructions, pedagogical resources, submission status, score feedback |
| 6 | `/api/v1/student/grades` | `GET` | `studentApi.listGrades()` | Official evaluation records grouped by subject with score averages |
| 7 | `/api/v1/student/attendance` | `GET` | `studentApi.listAttendance(filters)` | Historical attendance logs and summary rates (`PRESENT`, `ABSENT`, `EXCUSED`, `LATE`) |
| 8 | `/api/v1/student/virtual-classes` | `GET` | `studentApi.listVirtualClassrooms(filters)` | Live and scheduled virtual classroom sessions |
| 9 | `/api/v1/student/virtual-classes/{id}` | `GET` | `studentApi.getVirtualClassroom(id)` | Direct video room entrance details and access metadata |
| 10 | `/api/v1/student/virtual-classes/{id}/recordings` | `GET` | `studentApi.listRecordings(id)` | Session archive recordings and playback resources |

---

## 3. UI Component Architecture

The module is organized under modular directories:
- **`frontend/src/types/student.ts`**: Strict TypeScript interfaces mapping 1:1 with Phase 14A Pydantic schemas.
- **`frontend/src/components/student/`**: Reusable atomic, molecular, and modal components.
- **`frontend/src/pages/student/`**: Cohesive subviews coordinated by `StudentPortal.tsx`.

```
frontend/src/
├── types/
│   └── student.ts
├── services/
│   └── student.ts
├── components/student/
│   ├── StudentStatusBadge.tsx       # Accessible status badges for tasks, attendance & classes
│   ├── StudentMetricCard.tsx        # KPI metric cards with icons and accent themes
│   ├── StudentHeader.tsx            # Official institutional banner with SIMAT & group badge
│   ├── StudentNavbar.tsx            # Navigation subtabs with task & class badges
│   ├── StudentEmptyState.tsx        # Reusable friendly empty states with action triggers
│   ├── StudentLoadingSkeleton.tsx   # Premium skeleton loaders for metrics, cards & tables
│   ├── StudentTaskCard.tsx          # Task card with due date countdown & submission badge
│   ├── StudentVirtualClassCard.tsx  # Virtual class card with "INGRESAR A CLASE" primary CTA
│   ├── StudentTaskDetailModal.tsx   # Detailed instructions & teacher feedback modal
│   └── StudentVirtualClassModal.tsx # Room access & recordings archive player modal
└── pages/student/
    ├── StudentDashboardView.tsx     # Consolidated home: alerts, KPIs, urgent tasks, evaluations
    ├── StudentSubjectsView.tsx      # Enrolled subjects directory & teacher profiles
    ├── StudentTasksView.tsx         # Task manager with search, status pills & subject filters
    ├── StudentGradesView.tsx        # Evaluation report grouped by subject with cumulative averages
    ├── StudentAttendanceView.tsx    # Attendance KPI summary & historical attendance table
    ├── StudentVirtualClassesView.tsx# Live/upcoming class scheduler & recording archive
    ├── StudentProfileView.tsx       # Official student identity & institutional enrollment record
    └── StudentPortal.tsx            # Master layout coordinator & tab synchronization engine
```

---

## 4. Subviews & Functional Highlights

### 1. Dashboard (`/student` / `tab=dashboard`)
- **Live / Upcoming Class Alert Banner:** Prominently displays the next active or upcoming virtual classroom with a high-visibility **"INGRESAR A CLASE"** button.
- **KPI Summary Grid:** Four metric cards showing Enrolled Subjects, Pending Tasks, Attendance Rate (%), and Cumulative Average Score.
- **Urgent Tasks Panel:** Displays pending assignments with time-remaining urgency badges.
- **Recent Evaluations:** Real-time feedback and scores awarded by teachers.

### 2. Mis Asignaturas (`/student/subjects` / `tab=subjects`)
- Complete directory of enrolled subjects for the active academic year.
- Details assigned teacher name, email, weekly hours (`h/sem`), knowledge area, and a direct shortcut to filter tasks for that subject.

### 3. Mis Tareas (`/student/tasks` / `tab=tasks`)
- **Action-Oriented Filter Pills:** Quick filters for `Todas`, `Pendientes`, `Vencidas`, `Entregadas`, and `Calificadas`.
- **Subject Filter Dropdown:** Refines tasks by specific course.
- **Search Bar:** Real-time title search.
- **Task Detail Modal:** Opens detailed instructions, attached resource links, submission timestamp, awarded score, and qualitative teacher feedback.
- *Graceful Read-Only Notice:* In accordance with Phase 14A design rules, clearly informs the student if digital submission is handled via in-class evaluation or scheduled for an upcoming release.

### 4. Mis Calificaciones (`/student/grades` / `tab=grades`)
- Evaluations grouped by academic subject.
- Subject average badges formatted on the standard `0.0 – 5.0` Colombian grading scale.
- Detailed evaluations table with activity type badges (`TALLER`, `EXAMEN`, `TAREA`, `PROYECTO`, `QUIZ`), max score bounds, and educator feedback.

### 5. Mi Asistencia (`/student/attendance` / `tab=attendance`)
- Summary KPI metric cards: Total Records, Present (`ASISTIÓ`), Absent (`INASISTENCIA`), Late (`RETARDO`), Excused (`EXCUSA`).
- Global attendance percentage badge.
- Chronological attendance logs table with status pills and teacher remarks.

### 6. Clases Virtuales (`/student/virtual-classes` / `tab=virtual-classes`)
- Prominent display of live and upcoming sessions.
- Primary **"INGRESAR A CLASE"** CTA triggers direct access to the meeting URL.
- Past sessions display a **"VER GRABACIÓN"** button, opening the recording player modal with playback links, duration, and access credentials.

### 7. Mi Perfil (`/student/profile` / `tab=profile`)
- Displays official institutional identity: Full Name, Document Type & Number, SIMAT Code badge.
- Academic status: Campus, Grade, Group, Academic Year, and active enrollment verification.

---

## 5. Routing & Navigation Integration

1. **Route Registration ([`frontend/src/App.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/App.tsx)):**
   - Registered `/student` and `/student/*` protected with `<RequireAuth>`.
2. **Top Navigation Bar ([`frontend/src/layouts/RootLayout.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/layouts/RootLayout.tsx)):**
   - Added **"Portal Estudiante"** link with distinct graduate cap icon (`🎓`).
3. **Role Dashboard Hub ([`frontend/src/pages/Dashboard.tsx`](file:///c:/Users/juanc/OneDrive/Documentos/Desarrollo%20proyectos/Plataforma%20Educativa/Plataforma%20Educativa%20Virtual%20Nacional%20PEVN/frontend/src/pages/Dashboard.tsx)):**
   - Added first-class **"Portal del Estudiante"** access card for authenticated students and multi-role users.

---

## 6. Test & Quality Verification

### Frontend Test Suite Results (`npm test`):
```
Test Files  10 passed (10)
     Tests  58 passed (58)
  Duration  16.37s
```

#### Test Suite Breakdown:
1. `src/test/StudentPortal.test.tsx` (4 tests) — **100% Passed**
   - Renders student header identity, SIMAT badge, and dashboard metrics.
   - Switches between all 7 subtabs (`Inicio`, `Mis Asignaturas`, `Mis Tareas`, `Mis Calificaciones`, `Mi Asistencia`, `Clases Virtuales`, `Mi Perfil`).
   - Opens Task Detail modal with instructions and score feedback.
   - Opens Virtual Class modal with videoconference entrance.
2. `src/test/TeacherPortal.test.tsx` (7 tests) — **100% Passed**
3. `src/test/Academic.test.tsx` (13 tests) — **100% Passed**
4. `src/test/RoleNavigationFunctional.test.tsx` (12 tests) — **100% Passed**
5. `src/test/VirtualClassrooms.test.tsx` (6 tests) — **100% Passed**
6. `src/test/Auth.test.tsx` (6 tests) — **100% Passed**
7. `src/test/PasswordRecovery.test.tsx` (3 tests) — **100% Passed**
8. `src/test/TerritorialAnalytics.test.tsx` (1 test) — **100% Passed**
9. `src/test/App.test.tsx` (4 tests) — **100% Passed**
10. `src/test/SingleFlightRefresh.test.ts` (2 tests) — **100% Passed**

### Build Verification (`npm run build`):
```
> tsc -b && vite build
✓ 154 modules transformed.
dist/index.html                   2.60 kB │ gzip:  1.04 kB
dist/assets/index-DEHBlYKk.css   21.23 kB │ gzip:  5.21 kB
dist/assets/http-CzApALvg.js     48.54 kB │ gzip: 18.63 kB
dist/assets/router-CCBe3_4u.js  206.76 kB │ gzip: 67.57 kB
dist/assets/index-DzaFAvPZ.js   421.81 kB │ gzip: 78.81 kB
✓ built in 7.76s with 0 errors
```

---

## 7. Manual Validation Checklist for User Browser Testing

Since browser automation is avoided to optimize token usage, use the following manual checklist to test the Student Portal in a web browser:

1. **Authentication & Access:**
   - Log into the platform with student credentials (e.g. `carlos.gomez@santander.edu.co`).
   - Verify that the top navigation shows **"Portal Estudiante"** and the home dashboard contains the student access card.
   - Navigate to `/student`.
2. **Dashboard Validation:**
   - Confirm that the student header displays the student's name, SIMAT code pill, grade, group, and institution name.
   - Verify the 4 metric cards (Materias, Tareas Pendientes, % Asistencia, Promedio General).
   - If a live class is active or upcoming, confirm the blue banner with **"INGRESAR A CLASE"** is visible.
3. **Mis Asignaturas:**
   - Click on the **"Mis Asignaturas"** tab.
   - Verify all assigned subjects render with teacher name, knowledge area, and hours per week.
4. **Mis Tareas & Modal:**
   - Click on the **"Mis Tareas"** tab.
   - Test clicking the status pills (`Todas`, `Pendientes`, `Vencidas`, `Entregadas`, `Calificadas`).
   - Click **"Ver Detalle de Tarea"** on any task card and verify the modal displays instructions, due date, score, and teacher feedback.
5. **Mis Calificaciones:**
   - Click on the **"Mis Calificaciones"** tab.
   - Verify grades are grouped by subject with calculated average scores.
6. **Mi Asistencia:**
   - Click on the **"Mi Asistencia"** tab.
   - Verify KPI counts for Presentes, Inasistencias, and Retardos, as well as the historical attendance table.
7. **Clases Virtuales:**
   - Click on the **"Clases Virtuales"** tab.
   - Verify scheduled classes display **"INGRESAR A CLASE"** and past classes display **"VER GRABACIÓN"**.
   - Click **"VER GRABACIÓN"** to verify the recording modal opens.
8. **Mi Perfil:**
   - Click on the **"Mi Perfil"** tab.
   - Verify the identity details, document number, SIMAT code, and active enrollment status match the institutional record.
