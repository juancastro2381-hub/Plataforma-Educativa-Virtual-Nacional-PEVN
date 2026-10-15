import asyncio
from app.db.session import get_session_factory
from app.models.user import User
from app.core.security.password import Argon2PasswordHasher
from sqlalchemy import select, update

async def main():
    factory = get_session_factory()
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("Estudiante2026!")
    async with factory() as session:
        stmt = update(User).where(User.email == 'ramiro.rey@colegio.edu.co').values(hashed_password=hashed, is_active=True, is_verified=True, must_change_password=False)
        await session.execute(stmt)
        await session.commit()
        print("Updated Ramiro password to 'Estudiante2026!'")

        # Also Samuel Rua
        hashed_samuel = hasher.hash("Estudiante2026!")
        stmt2 = update(User).where(User.email == 'samuel.rua@colegio.edu.co').values(hashed_password=hashed_samuel, is_active=True, is_verified=True, must_change_password=False)
        await session.execute(stmt2)
        await session.commit()
        print("Updated Samuel password to 'Estudiante2026!'")

if __name__ == '__main__':
    asyncio.run(main())
