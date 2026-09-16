"""
PEVN — Script de Preparación y Limpieza de Datos QA para Fase 15
Uso exclusivo para validación funcional humana local.

Uso:
  python backend/scratch/qa_seed_phase15.py --action seed
  python backend/scratch/qa_seed_phase15.py --action status
  python backend/scratch/qa_seed_phase15.py --action cleanup
"""

import argparse
import asyncio
import sys
import uuid
from datetime import UTC, datetime

# Ensure project root is in sys.path
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.communication import (
    CommunicationAudience,
    CommunicationCategory,
    CommunicationPriority,
    CommunicationReceipt,
    InstitutionalCommunication,
    PublishingStatus,
    TargetScopeType,
)
from app.models.coexistence_incident import (
    CoexistenceSituationType,
    IncidentFollowUp,
    IncidentStatus,
    StudentIncident,
)
from app.models.guardian import Guardian, StudentGuardian
from app.models.institution import Institution
from app.models.news import InstitutionalNews, NewsCategory
from app.models.student import Student
from app.models.user import User

QA_MARKER = "QA-F15-20260907"


async def resolve_context(session):
    """
    Dynamically resolve Ramiro Rey, institution, guardian, and author without hardcoded UUIDs.
    """
    # 1. Student User (Ramiro Rey)
    user_stmt = select(User).where(User.email.ilike("%ramiro%"))
    student_user = (await session.execute(user_stmt)).scalar_one_or_none()
    if not student_user:
        raise RuntimeError("No se encontró el usuario de Ramiro Rey en la base de datos.")

    # 2. Student entity
    student_stmt = select(Student).where(Student.user_id == student_user.id)
    student = (await session.execute(student_stmt)).scalar_one_or_none()
    if not student:
        raise RuntimeError("No se encontró el registro de estudiante para Ramiro Rey.")

    # 3. Institution
    inst_stmt = select(Institution).where(Institution.id == student.institution_id)
    institution = (await session.execute(inst_stmt)).scalar_one_or_none()
    if not institution:
        raise RuntimeError("No se encontró la institución asociada a Ramiro Rey.")

    # 4. Guardian (Alberto Mercado)
    guardian_stmt = (
        select(Guardian, User)
        .join(User, Guardian.user_id == User.id)
        .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
        .where(
            StudentGuardian.student_id == student.id,
            User.email.ilike("%alberto%") | User.first_name.ilike("%alberto%"),
        )
    )
    guardian_row = (await session.execute(guardian_stmt)).first()
    if not guardian_row:
        # Fallback to any linked guardian if Alberto has a different email
        fallback_stmt = (
            select(Guardian, User)
            .join(User, Guardian.user_id == User.id)
            .join(StudentGuardian, StudentGuardian.guardian_id == Guardian.id)
            .where(StudentGuardian.student_id == student.id)
        )
        guardian_row = (await session.execute(fallback_stmt)).first()

    if not guardian_row:
        raise RuntimeError("No se encontró un acudiente vinculado a Ramiro Rey.")

    guardian, guardian_user = guardian_row

    # 5. Author / Reporter (Rector / Directivo / Docente in same institution)
    author_stmt = (
        select(User)
        .where(
            User.institution_id == student.institution_id,
            User.id != student_user.id,
            User.id != guardian_user.id,
        )
        .order_by(User.email.ilike("%rector%").desc())
    )
    author_user = (await session.execute(author_stmt)).scalars().first()
    if not author_user:
        raise RuntimeError("No se encontró un usuario administrativo/docente en la institución.")

    return {
        "institution": institution,
        "student": student,
        "student_user": student_user,
        "guardian": guardian,
        "guardian_user": guardian_user,
        "author_user": author_user,
    }


async def seed_data():
    sf = get_session_factory()
    async with sf() as session:
        ctx = await resolve_context(session)
        inst_id = ctx["institution"].id
        student_id = ctx["student"].id
        author_id = ctx["author_user"].id

        print(f"[QA SEED] Contexto Resuelto:")
        print(f"  - Institución: {ctx['institution'].name} ({inst_id})")
        print(f"  - Estudiante: {ctx['student_user'].first_name} {ctx['student_user'].last_name} ({student_id})")
        print(f"  - Acudiente: {ctx['guardian_user'].first_name} {ctx['guardian_user'].last_name} ({ctx['guardian'].id})")
        print(f"  - Autor/Reportador: {ctx['author_user'].first_name} {ctx['author_user'].last_name} ({author_id})")

        created_records = {}

        # -------------------------------------------------------------
        # A. Comunicado Institucional
        # -------------------------------------------------------------
        comm_stmt = select(InstitutionalCommunication).where(
            InstitutionalCommunication.institution_id == inst_id,
            InstitutionalCommunication.title.contains(QA_MARKER),
        )
        existing_comm = (await session.execute(comm_stmt)).scalar_one_or_none()

        if existing_comm:
            print(f"[QA SEED] Comunicado ya existente (Idempotente): ID {existing_comm.id}")
            created_records["communication"] = existing_comm
        else:
            comm = InstitutionalCommunication(
                institution_id=inst_id,
                author_user_id=author_id,
                title=f"[{QA_MARKER}] Circular Oficial: Actividades Pedagógicas y Convivencia",
                summary="Comunicado oficial sintético para validación funcional humana de la Fase 15 (Portal Estudiante y Acudiente).",
                content="""### Estimada Comunidad Educativa

Este es un **comunicado oficial sintético de prueba** generado para la validación funcional humana de la **Fase 15 (Comunicaciones, Noticias y Convivencia)** de la Plataforma Educativa Virtual Nacional (PEVN).

#### Aspectos Clave de la Notificación:
1. **Verificación de Notificaciones:** Se comprueba la recepción en el Portal del Estudiante (**Ramiro Rey**) y en el Portal del Acudiente (**Alberto Mercado**).
2. **Confirmación de Lectura:** Este comunicado requiere confirmación de lectura formal y obligatoria.
3. **Validez Institucional:** Registro activo y vigente emitido por Rectoría.

*Nota de Seguridad QA: Registro sintético controlado bajo el identificador único QA-F15-20260907.*""",
                category=CommunicationCategory.CIRCULAR_OFICIAL,
                priority=CommunicationPriority.ALTA,
                target_scope=TargetScopeType.TODOS_INSTITUCION,
                attachment_url=None,
                requires_acknowledgment=True,
                status=PublishingStatus.PUBLICADO,
                published_at=datetime.now(UTC),
                expires_at=None,
            )
            session.add(comm)
            await session.flush()
            print(f"[QA SEED] Comunicado CREADO: ID {comm.id} - '{comm.title}'")
            created_records["communication"] = comm

        # -------------------------------------------------------------
        # B. Noticia Institucional
        # -------------------------------------------------------------
        news_stmt = select(InstitutionalNews).where(
            InstitutionalNews.institution_id == inst_id,
            InstitutionalNews.title.contains(QA_MARKER),
        )
        existing_news = (await session.execute(news_stmt)).scalar_one_or_none()

        if existing_news:
            print(f"[QA SEED] Noticia ya existente (Idempotente): ID {existing_news.id}")
            created_records["news"] = existing_news
        else:
            news = InstitutionalNews(
                institution_id=inst_id,
                author_user_id=author_id,
                title=f"[{QA_MARKER}] Logro Destacado en Feria de Ciencia e Innovación Escolar",
                summary="Nuestra institución obtuvo reconocimiento de excelencia en el encuentro regional de proyectos formativos.",
                content="""### Celebración del Compromiso Académico e Innovador

Nos complace compartir con toda la comunidad estudiantil y las familias este reporte especial de nuestra participación en el **Encuentro Regional de Ciencia e Innovación Educativa**.

#### Puntos Destacados:
- **Participación Estudiantil:** Los proyectos pedagógicos orientados durante el ciclo lectivo demostraron alto rigor investigativo.
- **Formación Integral:** Reconocimiento al esfuerzo conjunto entre estudiantes, docentes tutores y acudientes.
- **Próximos Pasos:** Las iniciativas seleccionadas participarán en el foro nacional de cierre curricular.

*Aviso QA: Registro sintético generado exclusivamente para la validación funcional del módulo Periódico Escolar y Novedades (Fase 15).*""",
                category=NewsCategory.LOGRO_ACADEMICO,
                cover_image_url=None,
                status=PublishingStatus.PUBLICADO,
                published_at=datetime.now(UTC),
            )
            session.add(news)
            await session.flush()
            print(f"[QA SEED] Noticia CREADA: ID {news.id} - '{news.title}'")
            created_records["news"] = news

        # -------------------------------------------------------------
        # C. Convivencia / Observador del Estudiante
        # -------------------------------------------------------------
        inc_stmt = (
            select(StudentIncident)
            .options(selectinload(StudentIncident.follow_ups))
            .where(
                StudentIncident.institution_id == inst_id,
                StudentIncident.student_id == student_id,
                StudentIncident.description.contains(QA_MARKER),
            )
        )
        existing_inc = (await session.execute(inc_stmt)).scalar_one_or_none()

        if existing_inc:
            print(f"[QA SEED] Incidente ya existente (Idempotente): ID {existing_inc.id}")
            created_records["incident"] = existing_inc
        else:
            incident = StudentIncident(
                institution_id=inst_id,
                student_id=student_id,
                reporter_user_id=author_id,
                situation_type=CoexistenceSituationType.TIPO_I,
                incident_date=datetime.now(UTC),
                location="Aula de Clases / Auditorio Principal",
                description=f"[{QA_MARKER}] Registro sintético formativo de convivencia escolar. Diálogo pedagógico preventivo sobre puntualidad y participación activa en actividades institucionales.",
                student_version="El estudiante manifiesta su compromiso con el cumplimiento de los acuerdos de convivencia y puntualidad escolar.",
                pedagogical_measures="Acompañamiento reflexivo pedagógico, orientación tutorial y acuerdo de seguimiento de convivencia.",
                commitments="Mantener puntualidad y participación constructiva en la jornada escolar.",
                status=IncidentStatus.EN_SEGUIMIENTO,
                is_visible_to_guardian=True,
                is_visible_to_student=True,
            )
            session.add(incident)
            await session.flush()

            print(f"[QA SEED] Incidente CREADO: ID {incident.id} - Visibilidad Estudiante: {incident.is_visible_to_student}, Acudiente: {incident.is_visible_to_guardian}")
            created_records["incident"] = incident

        await session.commit()
        print("\n[QA SEED] Operación completada exitosamente. Datos sembrados y confirmados en PostgreSQL.")
        return created_records


async def status_data():
    sf = get_session_factory()
    async with sf() as session:
        comms = list((await session.execute(
            select(InstitutionalCommunication).where(InstitutionalCommunication.title.contains(QA_MARKER))
        )).scalars().all())

        news = list((await session.execute(
            select(InstitutionalNews).where(InstitutionalNews.title.contains(QA_MARKER))
        )).scalars().all())

        incidents = list((await session.execute(
            select(StudentIncident).options(selectinload(StudentIncident.follow_ups)).where(StudentIncident.description.contains(QA_MARKER))
        )).scalars().all())

        print(f"=== ESTADO ACTUAL DE DATOS QA ({QA_MARKER}) ===")
        print(f"Total Comunicados QA: {len(comms)}")
        for c in comms:
            print(f"  - ID: {c.id} | Título: {c.title} | Status: {c.status} | Scope: {c.target_scope}")

        print(f"\nTotal Noticias QA: {len(news)}")
        for n in news:
            print(f"  - ID: {n.id} | Título: {n.title} | Cat: {n.category} | Status: {n.status}")

        print(f"\nTotal Incidentes QA: {len(incidents)}")
        for i in incidents:
            print(f"  - ID: {i.id} | Estudiante: {i.student_id} | Status: {i.status} | Vis. Estudiante: {i.is_visible_to_student} | Vis. Acudiente: {i.is_visible_to_guardian}")
            for f in i.follow_ups:
                print(f"     -> Seguimiento ID: {f.id} | Notas: {f.notes[:60]}...")


async def cleanup_data():
    sf = get_session_factory()
    async with sf() as session:
        print(f"[QA CLEANUP] Eliminando exclusivamente registros con marcador '{QA_MARKER}'...")

        # 1. Incident follow-ups
        inc_ids_stmt = select(StudentIncident.id).where(StudentIncident.description.contains(QA_MARKER))
        inc_ids = list((await session.execute(inc_ids_stmt)).scalars().all())

        if inc_ids:
            del_fol = delete(IncidentFollowUp).where(IncidentFollowUp.incident_id.in_(inc_ids))
            res_fol = await session.execute(del_fol)
            print(f"  - Seguimientos eliminados: {res_fol.rowcount}")

        # 2. Incidents
        del_inc = delete(StudentIncident).where(StudentIncident.description.contains(QA_MARKER))
        res_inc = await session.execute(del_inc)
        print(f"  - Incidentes eliminados: {res_inc.rowcount}")

        # 3. Communication receipts and audiences
        comm_ids_stmt = select(InstitutionalCommunication.id).where(InstitutionalCommunication.title.contains(QA_MARKER))
        comm_ids = list((await session.execute(comm_ids_stmt)).scalars().all())

        if comm_ids:
            del_rcp = delete(CommunicationReceipt).where(CommunicationReceipt.communication_id.in_(comm_ids))
            res_rcp = await session.execute(del_rcp)
            print(f"  - Recibos de lectura eliminados: {res_rcp.rowcount}")

            del_aud = delete(CommunicationAudience).where(CommunicationAudience.communication_id.in_(comm_ids))
            res_aud = await session.execute(del_aud)
            print(f"  - Audiencias eliminadas: {res_aud.rowcount}")

        # 4. Communications
        del_comm = delete(InstitutionalCommunication).where(InstitutionalCommunication.title.contains(QA_MARKER))
        res_comm = await session.execute(del_comm)
        print(f"  - Comunicados eliminados: {res_comm.rowcount}")

        # 5. News
        del_news = delete(InstitutionalNews).where(InstitutionalNews.title.contains(QA_MARKER))
        res_news = await session.execute(del_news)
        print(f"  - Noticias eliminadas: {res_news.rowcount}")

        await session.commit()
        print(f"[QA CLEANUP] Limpieza finalizada exitosamente. Cero registros residuales de {QA_MARKER}.")


def main():
    parser = argparse.ArgumentParser(description="Script de datos QA para Fase 15 PEVN")
    parser.add_argument(
        "--action",
        choices=["seed", "status", "cleanup"],
        default="seed",
        help="Acción a realizar: seed (crear/asegurar), status (consultar), cleanup (eliminar exclusivamente QA)",
    )
    args = parser.parse_args()

    if args.action == "seed":
        asyncio.run(seed_data())
    elif args.action == "status":
        asyncio.run(status_data())
    elif args.action == "cleanup":
        asyncio.run(cleanup_data())


if __name__ == "__main__":
    main()
