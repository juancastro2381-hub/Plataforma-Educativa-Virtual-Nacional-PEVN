import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_session_factory
from app.models.subject import KnowledgeArea, Subject
from app.models.grade import Grade, EducationalLevel
from app.models.institution import Institution

STANDARD_SUBJECT_SPECS = [
    ("Matemáticas", "Matemáticas", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Lengua Castellana", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Inglés", 3),
    ("Ciencias Naturales y Educación Ambiental", "Ciencias Naturales y Educación Ambiental", 4),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Ciencias Sociales", 3),
    ("Educación Artística y Cultural", "Educación Artística", 2),
    ("Educación Ética y en Valores Humanos", "Ética y Valores", 1),
    ("Educación Física, Recreación y Deportes", "Educación Física, Recreación y Deporte", 2),
    ("Tecnología e Informática", "Tecnología e Informática", 2),
    ("Educación Religiosa", "Educación Religiosa", 1),
]

# Media level specialized subjects
MEDIA_SUBJECT_SPECS = [
    ("Matemáticas", "Cálculo y Trigonometría", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Lengua Castellana y Literatura", 4),
    ("Humanidades, Lengua Castellana e Idiomas Extranjeros", "Inglés Avanzado", 3),
    ("Ciencias Naturales y Educación Ambiental", "Física", 3),
    ("Ciencias Naturales y Educación Ambiental", "Química", 3),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Filosofía y Ciencias Políticas", 3),
    ("Ciencias Sociales, Historia, Geografía y Democracia", "Ciencias Económicas", 2),
    ("Educación Artística y Cultural", "Educación Artística", 2),
    ("Educación Ética y en Valores Humanos", "Ética y Valores", 1),
    ("Educación Física, Recreación y Deportes", "Educación Física, Recreación y Deporte", 2),
    ("Tecnología e Informática", "Tecnología e Informática", 2),
    ("Educación Religiosa", "Educación Religiosa", 1),
]

async def seed_subjects_for_institution(session, institution_id: uuid.UUID):
    # Check if subjects already exist
    stmt_existing = select(Subject).where(Subject.institution_id == institution_id)
    existing = (await session.execute(stmt_existing)).scalars().all()
    if existing:
        print(f"Institution {institution_id} already has {len(existing)} subjects.")
        return existing

    # Load Knowledge Areas
    kas = (await session.execute(select(KnowledgeArea))).scalars().all()
    ka_by_name = {ka.name: ka.id for ka in kas}

    # Load Grades
    grades = (await session.execute(select(Grade).order_by(Grade.ordinal_order))).scalars().all()

    created_subjects = []
    for g in grades:
        specs = MEDIA_SUBJECT_SPECS if g.level == EducationalLevel.MEDIA else STANDARD_SUBJECT_SPECS
        for ka_name, sub_name, hours in specs:
            ka_id = ka_by_name.get(ka_name)
            if not ka_id:
                # Find partial match
                for name, kid in ka_by_name.items():
                    if ka_name.lower() in name.lower() or name.lower() in ka_name.lower():
                        ka_id = kid
                        break
            if not ka_id:
                continue
            subject = Subject(
                institution_id=institution_id,
                knowledge_area_id=ka_id,
                grade_id=g.id,
                name=f"{sub_name} - {g.name}",
                weekly_hours=hours,
            )
            session.add(subject)
            created_subjects.append(subject)

    await session.flush()
    print(f"Seeded {len(created_subjects)} statutory subjects for institution {institution_id}.")
    return created_subjects

async def main():
    factory = get_session_factory()
    async with factory() as session:
        inst_id = uuid.UUID("f6efded7-e385-46e7-b224-a592ed942dbc") # COLEGIO AQUILEO PARRA
        subjects = await seed_subjects_for_institution(session, inst_id)
        await session.commit()

        # Check seeded subjects
        stmt = select(Subject).where(Subject.institution_id == inst_id).options(selectinload(Subject.grade), selectinload(Subject.knowledge_area))
        res = (await session.execute(stmt)).scalars().all()
        print(f"\nTotal subjects now in DB for Colegio Aquileo Parra: {len(res)}")
        for s in res[:10]:
            print(f" - {s.name} (Grade: {s.grade.name}, Hours: {s.weekly_hours}, ID: {s.id})")

if __name__ == "__main__":
    asyncio.run(main())
