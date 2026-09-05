# PEvN — Phase 12 Canonical Role Navigation Matrix
## Top Navigation Trees, Route Accessibility & Security Boundaries across All 11 Roles

---

| # | Role | Primary Landing Route | Top Navigation Bar Links | Authorized Routes & Tabs | Forbidden Direct Routes (Redirected / Blocked) |
| :-: | :--- | :--- | :--- | :--- | :--- |
| **1** | `superadmin` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales, Analítica Territorial, Instituciones | `/admin/institutions`, `/admin/catalog`, `/analytics/territorial`, all academic hubs | None (Root Level Access) |
| **2** | `national_admin` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales, Analítica Territorial, Instituciones | `/admin/institutions`, `/admin/catalog`, `/analytics/territorial`, `/institutions` | Local teacher/student creation on specific institution |
| **3** | `department_admin` | `/dashboard` | Dashboard, Analítica Territorial | `/analytics/territorial` (department-filtered) | `/admin/institutions`, `/academic` |
| **4** | `municipality_admin` | `/dashboard` | Dashboard, Analítica Territorial | `/analytics/territorial` (municipality-filtered) | `/admin/institutions`, `/academic` |
| **5** | `rector` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales | `/academic?tab=years`, `/academic?tab=periods`, `/academic?tab=groups`, `/academic?tab=teachers`, `/academic?tab=students`, `/academic?tab=guardians`, `/academic?tab=enrollments`, `/classrooms` | `/admin/institutions`, cross-tenant institutions |
| **6** | `institution_admin` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales | Same as Rector (Academic Hub, Classrooms) | `/admin/institutions`, cross-tenant institutions |
| **7** | `coordinator` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales | `/academic?tab=students`, `/academic?tab=groups`, `/academic?tab=enrollments`, `/academic?tab=transfers`, `/classrooms` | `/academic?tab=years`, `/admin/institutions` |
| **8** | `academic_coordinator` | `/dashboard` | Dashboard, Gestión Académica, Aulas Virtuales | `/academic?tab=assignments`, `/academic?tab=teachers`, `/academic?tab=subjects`, `/classrooms` | `/academic?tab=years` (close year), `/admin/institutions` |
| **9** | `teacher` | `/dashboard` | Dashboard, Aulas Virtuales | `/classrooms` (host meetings, view logs, recordings), `/academic?tab=students` (read roster) | `/academic?tab=years`, `/academic?tab=teachers` (creation), `/admin/institutions` |
| **10** | `student` | `/dashboard` | Dashboard, Aulas Virtuales | `/classrooms` (join meetings, view class schedules, attendance) | `/academic`, `/admin/institutions`, administrative actions |
| **11** | `guardian` | `/dashboard` | Dashboard, Seguimiento Familiar | `/guardian/students` (view dependent academic reports, pickup authorizations) | `/academic`, `/admin/institutions`, institutional administration |

---

### Direct Route Protection Invariants

1. **Client-Side Guarding**: `RequireAuth` and `RequirePermission` components enforce route guarding and redirect unauthorized roles to `/dashboard` with an informative warning notification.
2. **Server-Side Final Authority**: All REST API endpoints enforce `require_permission` and `_resolve_institution_id` on every HTTP request. Frontend route bypass attempts are strictly rejected with HTTP 403 Forbidden.
