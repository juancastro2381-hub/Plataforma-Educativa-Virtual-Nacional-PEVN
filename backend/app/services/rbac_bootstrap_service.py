"""
PEVN Backend — RBAC & Canonical Role/Permission Bootstrap Service

Authoritative, idempotent catalog initialization for System Roles, Granular Permissions,
and Role-Permission associations according to docs/PHASE_3_RBAC_MATRIX.md and docs/AUTHORIZATION.md.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.security.interfaces import SystemRole
from app.models.role import Permission, Role, RolePermission

_logger = get_logger(__name__)

# ===========================================================================
# 1. Canonical Roles Definition
# ===========================================================================
CANONICAL_ROLES: list[dict[str, Any]] = [
    {
        "name": SystemRole.SUPERADMIN.value,  # "superadmin"
        "display_name": "Super Administrador",
        "level": 100,
        "description": "Operador técnico del Estado / Root. Acceso total a configuración y auditoría.",
    },
    {
        "name": SystemRole.NATIONAL_ADMIN.value,  # "national_admin"
        "display_name": "Administrador Nacional",
        "level": 90,
        "description": "Ministerio de Educación Nacional (MEN). Aprovisionamiento y gobierno nacional.",
    },
    {
        "name": SystemRole.DEPARTMENT_ADMIN.value,  # "department_admin"
        "display_name": "Administrador Departamental",
        "level": 80,
        "description": "Secretaría de Educación Departamental (SED). Jurisdicción departamental.",
    },
    {
        "name": SystemRole.MUNICIPALITY_ADMIN.value,  # "municipality_admin"
        "display_name": "Administrador Municipal",
        "level": 70,
        "description": "Secretaría de Educación Municipal (SEM). Jurisdicción municipal.",
    },
    {
        "name": SystemRole.RECTOR.value,  # "rector"
        "display_name": "Rector / Director",
        "level": 60,
        "description": "Rector / Director de la Institución Educativa. Gestión académica y administrativa del tenant.",
    },
    {
        "name": SystemRole.INSTITUTION_ADMIN.value,  # "institution_admin" (alias/compatibility)
        "display_name": "Administrador Institucional",
        "level": 60,
        "description": "Alias de compatibilidad institucional para Rector.",
    },
    {
        "name": "coordinator",  # "coordinator"
        "display_name": "Coordinador Académico / Sede",
        "level": 50,
        "description": "Coordinador Académico o de Sede. Gestión operativa de períodos, grupos y asignaciones.",
    },
    {
        "name": SystemRole.ACADEMIC_COORDINATOR.value,  # "academic_coordinator" (alias)
        "display_name": "Coordinador Académico",
        "level": 50,
        "description": "Coordinador Académico de la institución.",
    },
    {
        "name": SystemRole.TEACHER.value,  # "teacher"
        "display_name": "Docente",
        "level": 30,
        "description": "Docente de aula y titular de asignaturas y grupos asignados.",
    },
    {
        "name": SystemRole.STUDENT.value,  # "student"
        "display_name": "Estudiante",
        "level": 10,
        "description": "Estudiante matriculado. Acceso a sus propios cursos y calificaciones.",
    },
    {
        "name": "guardian",  # "guardian"
        "display_name": "Acudiente / Tutor",
        "level": 10,
        "description": "Padre / Madre / Acudiente legal. Acceso a registros de sus tutorados.",
    },
]

# ===========================================================================
# 2. Canonical Permissions Definition
# ===========================================================================
CANONICAL_PERMISSIONS: list[tuple[str, str, str]] = [
    # Wildcard
    ("*", "*", "Permiso comodín global irrestricto (Superadmin)"),
    # Institutions
    ("institutions", "read", "Consultar instituciones educativas"),
    ("institutions", "create", "Aprovisionar nuevas instituciones educativas"),
    ("institutions", "update", "Actualizar datos y estado operativo de instituciones"),
    ("institutions", "delete", "Eliminar o dar de baja instituciones educativas"),
    # Users
    ("users", "read", "Consultar usuarios del sistema"),
    ("users", "create", "Registrar nuevos usuarios en el sistema"),
    ("users", "create_rector", "Emitir invitación criptográfica para nuevo Rector"),
    ("users", "update", "Modificar datos de usuarios"),
    ("users", "delete", "Desactivar o eliminar usuarios"),
    # Academic Years
    ("academic_years", "read", "Consultar años lectivos"),
    ("academic_years", "create", "Crear nuevo año lectivo"),
    ("academic_years", "update", "Modificar configuración de año lectivo"),
    ("academic_years", "close", "Ejecutar cierre de año lectivo"),
    ("academic_years", "delete", "Eliminar año lectivo no cerrado"),
    # Academic Periods
    ("academic_periods", "read", "Consultar períodos académicos"),
    ("academic_periods", "create", "Crear períodos académicos"),
    ("academic_periods", "update", "Modificar períodos académicos"),
    ("academic_periods", "close", "Cerrar período académico"),
    # Grades
    ("grades", "read", "Consultar catálogo de grados curriculares"),
    ("grades", "write", "Registrar o calificar evaluaciones"),
    ("grades", "manage", "Administrar catálogo nacional de grados"),
    # Subjects
    ("subjects", "read", "Consultar plan de estudios y asignaturas"),
    ("subjects", "create", "Crear nueva asignatura institucional"),
    ("subjects", "update", "Modificar asignatura"),
    ("subjects", "delete", "Eliminar asignatura"),
    # Groups
    ("groups", "read", "Consultar grupos y salones de clase"),
    ("groups", "create", "Crear grupo académico"),
    ("groups", "update", "Modificar grupo académico"),
    ("groups", "delete", "Eliminar grupo académico"),
    ("groups", "assign_director", "Asignar docente director de grupo"),
    # Teachers
    ("teachers", "read", "Consultar cuerpo docente"),
    ("teachers", "create", "Vincular nuevo docente a la institución"),
    ("teachers", "update", "Modificar asignación o perfil de docente"),
    ("teachers", "delete", "Desvincular docente"),
    # Students
    ("students", "read", "Consultar estudiantes"),
    ("students", "create", "Registrar nuevo estudiante"),
    ("students", "update", "Modificar ficha de estudiante"),
    ("students", "delete", "Dar de baja estudiante"),
    # Guardians
    ("guardians", "read", "Consultar acudientes"),
    ("guardians", "create", "Registrar acudiente"),
    ("guardians", "update", "Modificar datos de acudiente"),
    ("guardians", "link_student", "Vincular estudiante a acudiente"),
    # Enrollments
    ("enrollments", "read", "Consultar matrículas"),
    ("enrollments", "create", "Matricular estudiante en grupo"),
    ("enrollments", "transfer", "Trasladar estudiante de grupo o sede"),
    ("enrollments", "withdraw", "Retirar estudiante"),
    ("enrollments", "delete", "Anular matrícula"),
    # Academic Assignments
    ("academic_assignments", "read", "Consultar asignaciones académicas"),
    ("academic_assignments", "create", "Asignar carga académica a docente"),
    ("academic_assignments", "update", "Modificar carga académica"),
    ("academic_assignments", "delete", "Eliminar carga académica"),
    # Virtual Classrooms
    ("virtual_classrooms", "read", "Consultar aulas virtuales"),
    ("virtual_classrooms", "create", "Crear sesión de clase virtual"),
    ("virtual_classrooms", "join", "Ingresar a sesión de clase virtual"),
    ("virtual_classrooms", "manage", "Modificar o finalizar sesión de aula virtual"),
    # Recordings
    ("recordings", "read", "Consultar y reproducir grabaciones de clases"),
    ("recordings", "manage", "Gestionar estado y visibilidad de grabaciones"),
    ("recordings", "delete", "Eliminar grabaciones de clases virtuales"),
    # Academic Activities (Teacher Portal Phase 13D.5)
    ("activities", "read", "Consultar actividades académicas y tareas"),
    ("activities", "create", "Crear actividades académicas para grupos asignados"),
    ("activities", "update", "Modificar actividades académicas"),
    ("activities", "publish", "Publicar actividades académicas para estudiantes"),
    ("activities", "close", "Cerrar actividades académicas finalizadas"),
    ("activities", "delete", "Eliminar actividades académicas no evaluadas"),
    # Student Submissions (Teacher & Student Portals Phase B3-H13)
    ("submissions", "read", "Consultar entregas de estudiantes y archivos adjuntos"),
    ("submissions", "create", "Crear borrador o registrar entrega formal de actividad"),
    ("submissions", "update", "Modificar borrador de entrega o gestionar adjuntos"),
    ("submissions", "return", "Devolver entrega de estudiante para corrección"),
    # Daily Attendance (Teacher Portal Phase 13D.5)
    ("attendance", "read", "Consultar registro de asistencia escolar"),
    ("attendance", "write", "Registrar y actualizar asistencia diaria de estudiantes"),
    # Curricular Planning (Teacher Portal Phase 13D.5)
    ("planning", "read", "Consultar planeaciones curriculares y unidades temáticas"),
    ("planning", "create", "Crear planeación curricular para asignaciones"),
    ("planning", "update", "Modificar planeación curricular"),
    ("planning", "delete", "Eliminar planeación curricular"),
    # Institutional Communications (Phase 15)
    ("communications", "read", "Consultar comunicados y circulares institucionales"),
    ("communications", "create", "Crear comunicados oficiales"),
    ("communications", "update", "Modificar comunicados"),
    ("communications", "publish", "Publicar comunicados oficiales"),
    ("communications", "delete", "Archivar o eliminar comunicados"),
    # Institutional News (Phase 15)
    ("news", "read", "Consultar noticias y eventos comunitarios"),
    ("news", "create", "Redactar noticias institucionales"),
    ("news", "update", "Modificar noticias institucionales"),
    ("news", "publish", "Publicar noticias institucionales"),
    ("news", "delete", "Eliminar o archivar noticias"),
    # School Coexistence & Student Incidents (Phase 15 Ley 1620)
    ("incidents", "read", "Consultar observador y situaciones de convivencia escolar"),
    ("incidents", "create", "Registrar situaciones de convivencia en el observador"),
    ("incidents", "update", "Actualizar descargos y compromisos de convivencia"),
    ("incidents", "close", "Resolver y cerrar situaciones de convivencia escolar"),
    # SIEE Evaluation, Period Grades & Report Cards (Phase 16C)
    ("siee_policies", "read", "Consultar políticas SIEE institucionales vigentes e históricas"),
    ("siee_policies", "manage", "Crear y versionar políticas SIEE institucionales"),
    ("evaluations", "read", "Consultar sábana de calificaciones y notas del período"),
    ("evaluations", "grade", "Asentar y guardar calificaciones del período académico"),
    ("evaluations", "adjust", "Ajustar notas individuales con justificación pedagógica"),
    ("evaluations", "close_period", "Cerrar y sellar período académico"),
    ("evaluations", "reopen_period", "Reabrir período académico cerrado (Dirección)"),
    ("evaluations", "recovery", "Registrar calificaciones de nivelación o recuperación"),
    ("report_cards", "read", "Consultar boletines de calificaciones propios o de tutorados"),
    ("report_cards", "read_group", "Consultar sábana consolidada y ranking de grupo (Directivos/Docentes)"),
    ("promotions", "preview", "Calcular y previsualizar propuesta de promoción de grupo"),
    ("promotions", "execute", "Asentar acta oficial de evaluación y promoción"),
    ("promotions", "read", "Consultar historial de actas de promoción y dictámenes"),
]

# ===========================================================================
# 3. Role to Permission Matrix (PHASE_3_RBAC_MATRIX.md)
# ===========================================================================
ROLE_PERMISSIONS_CONFIG: dict[str, list[str]] = {
    SystemRole.SUPERADMIN.value: ["*:*"],
    SystemRole.NATIONAL_ADMIN.value: [
        "institutions:read",
        "institutions:create",
        "institutions:update",
        "institutions:delete",
        "users:read",
        "users:create",
        "users:create_rector",
        "users:update",
        "users:delete",
        "academic_years:read",
        "academic_years:create",
        "academic_years:update",
        "academic_years:close",
        "academic_years:delete",
        "academic_periods:read",
        "academic_periods:create",
        "academic_periods:update",
        "academic_periods:close",
        "grades:read",
        "grades:write",
        "grades:manage",
        "subjects:read",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "groups:read",
        "groups:create",
        "groups:update",
        "groups:delete",
        "groups:assign_director",
        "teachers:read",
        "teachers:create",
        "teachers:update",
        "teachers:delete",
        "students:read",
        "students:create",
        "students:update",
        "students:delete",
        "guardians:read",
        "guardians:create",
        "guardians:update",
        "guardians:link_student",
        "enrollments:read",
        "enrollments:create",
        "enrollments:transfer",
        "enrollments:withdraw",
        "enrollments:delete",
        "academic_assignments:read",
        "academic_assignments:create",
        "academic_assignments:update",
        "academic_assignments:delete",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "communications:read",
        "communications:create",
        "communications:update",
        "communications:publish",
        "communications:delete",
        "news:read",
        "news:create",
        "news:update",
        "news:publish",
        "news:delete",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        "incidents:close",
    ],
    SystemRole.DEPARTMENT_ADMIN.value: [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_periods:read",
        "grades:read",
        "subjects:read",
        "groups:read",
        "teachers:read",
        "students:read",
        "guardians:read",
        "enrollments:read",
        "academic_assignments:read",
        "virtual_classrooms:read",
        "recordings:read",
        "communications:read",
        "news:read",
        "incidents:read",
    ],
    SystemRole.MUNICIPALITY_ADMIN.value: [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_periods:read",
        "grades:read",
        "subjects:read",
        "groups:read",
        "teachers:read",
        "students:read",
        "guardians:read",
        "enrollments:read",
        "academic_assignments:read",
        "virtual_classrooms:read",
        "recordings:read",
        "communications:read",
        "news:read",
        "incidents:read",
    ],
    SystemRole.RECTOR.value: [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_years:create",
        "academic_years:update",
        "academic_years:close",
        "academic_years:delete",
        "academic_periods:read",
        "academic_periods:create",
        "academic_periods:update",
        "academic_periods:close",
        "grades:read",
        "grades:write",
        "subjects:read",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "groups:read",
        "groups:create",
        "groups:update",
        "groups:delete",
        "groups:assign_director",
        "teachers:read",
        "teachers:create",
        "teachers:update",
        "teachers:delete",
        "students:read",
        "students:create",
        "students:update",
        "students:delete",
        "guardians:read",
        "guardians:create",
        "guardians:update",
        "guardians:link_student",
        "enrollments:read",
        "enrollments:create",
        "enrollments:transfer",
        "enrollments:withdraw",
        "enrollments:delete",
        "academic_assignments:read",
        "academic_assignments:create",
        "academic_assignments:update",
        "academic_assignments:delete",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "activities:read",
        "activities:create",
        "activities:update",
        "activities:publish",
        "activities:close",
        "activities:delete",
        "submissions:read",
        "attendance:read",
        "attendance:write",
        "planning:read",
        "planning:create",
        "planning:update",
        "planning:delete",
        "communications:read",
        "communications:create",
        "communications:update",
        "communications:publish",
        "communications:delete",
        "news:read",
        "news:create",
        "news:update",
        "news:publish",
        "news:delete",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        "incidents:close",
        # Phase 16C — SIEE Evaluation & Promotions
        "siee_policies:read",
        "siee_policies:manage",
        "evaluations:read",
        "evaluations:grade",
        "evaluations:adjust",
        "evaluations:close_period",
        "evaluations:reopen_period",
        "evaluations:recovery",
        "report_cards:read",
        "report_cards:read_group",
        "promotions:preview",
        "promotions:execute",
        "promotions:read",
    ],
    SystemRole.INSTITUTION_ADMIN.value: [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_years:create",
        "academic_years:update",
        "academic_years:close",
        "academic_years:delete",
        "academic_periods:read",
        "academic_periods:create",
        "academic_periods:update",
        "academic_periods:close",
        "grades:read",
        "grades:write",
        "subjects:read",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "groups:read",
        "groups:create",
        "groups:update",
        "groups:delete",
        "groups:assign_director",
        "teachers:read",
        "teachers:create",
        "teachers:update",
        "teachers:delete",
        "students:read",
        "students:create",
        "students:update",
        "students:delete",
        "guardians:read",
        "guardians:create",
        "guardians:update",
        "guardians:link_student",
        "enrollments:read",
        "enrollments:create",
        "enrollments:transfer",
        "enrollments:withdraw",
        "enrollments:delete",
        "academic_assignments:read",
        "academic_assignments:create",
        "academic_assignments:update",
        "academic_assignments:delete",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "activities:read",
        "activities:create",
        "activities:update",
        "activities:publish",
        "activities:close",
        "activities:delete",
        "submissions:read",
        "attendance:read",
        "attendance:write",
        "planning:read",
        "planning:create",
        "planning:update",
        "planning:delete",
        "communications:read",
        "communications:create",
        "communications:update",
        "communications:publish",
        "communications:delete",
        "news:read",
        "news:create",
        "news:update",
        "news:publish",
        "news:delete",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        "incidents:close",
        # Phase 16C — SIEE Evaluation & Promotions
        "siee_policies:read",
        "siee_policies:manage",
        "evaluations:read",
        "evaluations:grade",
        "evaluations:adjust",
        "evaluations:close_period",
        "evaluations:reopen_period",
        "evaluations:recovery",
        "report_cards:read",
        "report_cards:read_group",
        "promotions:preview",
        "promotions:execute",
        "promotions:read",
    ],
    "coordinator": [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_periods:read",
        "academic_periods:create",
        "academic_periods:update",
        "academic_periods:close",
        "grades:read",
        "grades:write",
        "subjects:read",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "groups:read",
        "groups:create",
        "groups:update",
        "groups:delete",
        "teachers:read",
        "teachers:create",
        "teachers:update",
        "students:read",
        "students:create",
        "students:update",
        "guardians:read",
        "guardians:create",
        "guardians:update",
        "guardians:link_student",
        "enrollments:read",
        "enrollments:create",
        "enrollments:transfer",
        "enrollments:withdraw",
        "academic_assignments:read",
        "academic_assignments:create",
        "academic_assignments:update",
        "academic_assignments:delete",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "activities:read",
        "activities:create",
        "activities:update",
        "activities:publish",
        "activities:close",
        "activities:delete",
        "submissions:read",
        "attendance:read",
        "attendance:write",
        "planning:read",
        "planning:create",
        "planning:update",
        "planning:delete",
        "communications:read",
        "communications:create",
        "communications:update",
        "communications:publish",
        "communications:delete",
        "news:read",
        "news:create",
        "news:update",
        "news:publish",
        "news:delete",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        "incidents:close",
        # Phase 16C — SIEE Evaluation & Promotions
        "siee_policies:read",
        "siee_policies:manage",
        "evaluations:read",
        "evaluations:grade",
        "evaluations:adjust",
        "evaluations:close_period",
        "evaluations:reopen_period",
        "evaluations:recovery",
        "report_cards:read",
        "report_cards:read_group",
        "promotions:preview",
        "promotions:execute",
        "promotions:read",
    ],
    SystemRole.ACADEMIC_COORDINATOR.value: [
        "institutions:read",
        "users:read",
        "academic_years:read",
        "academic_periods:read",
        "academic_periods:create",
        "academic_periods:update",
        "academic_periods:close",
        "grades:read",
        "grades:write",
        "subjects:read",
        "subjects:create",
        "subjects:update",
        "subjects:delete",
        "groups:read",
        "groups:create",
        "groups:update",
        "groups:delete",
        "teachers:read",
        "teachers:create",
        "teachers:update",
        "students:read",
        "students:create",
        "students:update",
        "guardians:read",
        "guardians:create",
        "guardians:update",
        "guardians:link_student",
        "enrollments:read",
        "enrollments:create",
        "enrollments:transfer",
        "enrollments:withdraw",
        "academic_assignments:read",
        "academic_assignments:create",
        "academic_assignments:update",
        "academic_assignments:delete",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "activities:read",
        "activities:create",
        "activities:update",
        "activities:publish",
        "activities:close",
        "activities:delete",
        "submissions:read",
        "attendance:read",
        "attendance:write",
        "planning:read",
        "planning:create",
        "planning:update",
        "planning:delete",
        "communications:read",
        "communications:create",
        "communications:update",
        "communications:publish",
        "communications:delete",
        "news:read",
        "news:create",
        "news:update",
        "news:publish",
        "news:delete",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        "incidents:close",
        # Phase 16C — SIEE Evaluation & Promotions
        "siee_policies:read",
        "siee_policies:manage",
        "evaluations:read",
        "evaluations:grade",
        "evaluations:adjust",
        "evaluations:close_period",
        "evaluations:reopen_period",
        "evaluations:recovery",
        "report_cards:read",
        "report_cards:read_group",
        "promotions:preview",
        "promotions:execute",
        "promotions:read",
    ],
    SystemRole.TEACHER.value: [
        "academic_years:read",
        "academic_periods:read",
        "grades:read",
        "grades:write",
        "subjects:read",
        "groups:read",
        "teachers:read",
        "students:read",
        "enrollments:read",
        "academic_assignments:read",
        "virtual_classrooms:read",
        "virtual_classrooms:create",
        "virtual_classrooms:join",
        "virtual_classrooms:manage",
        "recordings:read",
        "recordings:manage",
        "recordings:delete",
        "activities:read",
        "activities:create",
        "activities:update",
        "activities:publish",
        "activities:close",
        "activities:delete",
        "submissions:read",
        "submissions:return",
        "attendance:read",
        "attendance:write",
        "planning:read",
        "planning:create",
        "planning:update",
        "planning:delete",
        "communications:read",
        "news:read",
        "incidents:read",
        "incidents:create",
        "incidents:update",
        # Phase 16C — SIEE (Teacher scope only)
        "siee_policies:read",
        "evaluations:read",
        "evaluations:grade",
        "evaluations:adjust",
        "evaluations:recovery",
        "report_cards:read",
        "report_cards:read_group",
        "promotions:preview",
        "promotions:read",
    ],
    SystemRole.STUDENT.value: [
        "academic_years:read",
        "grades:read",
        "subjects:read",
        "students:read",
        "enrollments:read",
        "academic_assignments:read",
        "virtual_classrooms:read",
        "virtual_classrooms:join",
        "recordings:read",
        "activities:read",
        "submissions:read",
        "submissions:create",
        "submissions:update",
        "attendance:read",
        "planning:read",
        "communications:read",
        "news:read",
        "incidents:read",
        # Phase 16C — Student self-service report card
        "report_cards:read",
    ],
    "guardian": [
        "academic_years:read",
        "grades:read",
        "students:read",
        "guardians:read",
        "enrollments:read",
        "academic_assignments:read",
        "activities:read",
        "attendance:read",
        "communications:read",
        "news:read",
        "incidents:read",
        # Phase 16C — Guardian report card access for tutorados
        "report_cards:read",
    ],
}


class RbacBootstrapService:
    """
    Service responsible for idempotent initialization of roles and permissions in the database.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def seed_canonical_rbac_if_needed(self) -> dict[str, int]:
        """
        Ensure all canonical roles, permissions, and associations exist.
        Completely idempotent: does not duplicate or mutate existing IDs.

        Returns:
            Summary count of created roles, permissions, and links.
        """
        created_roles = 0
        created_perms = 0
        created_links = 0

        # 1. Seed Permissions
        perm_map: dict[str, Permission] = {}
        all_perms_stmt = select(Permission)
        existing_perms = (await self._session.execute(all_perms_stmt)).scalars().all()
        for p in existing_perms:
            perm_map[f"{p.resource}:{p.action}"] = p

        for res, act, desc in CANONICAL_PERMISSIONS:
            key = f"{res}:{act}"
            if key not in perm_map:
                perm = Permission(resource=res, action=act, description=desc)
                self._session.add(perm)
                await self._session.flush()
                perm_map[key] = perm
                created_perms += 1

        # 2. Seed Roles
        role_map: dict[str, Role] = {}
        all_roles_stmt = select(Role)
        existing_roles = (await self._session.execute(all_roles_stmt)).scalars().all()
        for r in existing_roles:
            role_map[r.name] = r

        for r_data in CANONICAL_ROLES:
            r_name = r_data["name"]
            if r_name not in role_map:
                role = Role(
                    name=r_name,
                    display_name=r_data["display_name"],
                    level=r_data["level"],
                    description=r_data["description"],
                )
                self._session.add(role)
                await self._session.flush()
                role_map[r_name] = role
                created_roles += 1

        # 3. Seed Role Permissions
        existing_rp_stmt = select(RolePermission)
        existing_rps = (await self._session.execute(existing_rp_stmt)).scalars().all()
        existing_rp_set: set[tuple[uuid.UUID, uuid.UUID]] = {
            (rp.role_id, rp.permission_id) for rp in existing_rps
        }

        for r_name, perm_keys in ROLE_PERMISSIONS_CONFIG.items():
            role_entity = role_map.get(r_name)
            if not role_entity:
                continue

            for p_key in perm_keys:
                if p_key == "*:*":
                    p_entity = perm_map.get("*:*")
                else:
                    p_entity = perm_map.get(p_key)

                if p_entity:
                    link_key = (role_entity.id, p_entity.id)
                    if link_key not in existing_rp_set:
                        rp = RolePermission(
                            role_id=role_entity.id,
                            permission_id=p_entity.id,
                        )
                        self._session.add(rp)
                        existing_rp_set.add(link_key)
                        created_links += 1

        if created_roles > 0 or created_perms > 0 or created_links > 0:
            await self._session.flush()
            _logger.info(
                "RBAC Bootstrap completed",
                created_roles=created_roles,
                created_permissions=created_perms,
                created_links=created_links,
            )

        return {
            "created_roles": created_roles,
            "created_permissions": created_perms,
            "created_links": created_links,
        }
