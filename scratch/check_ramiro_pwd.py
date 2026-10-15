import asyncio
from app.db.session import get_session_factory
from app.models.user import User
from app.core.security.password import Argon2PasswordHasher
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    hasher = Argon2PasswordHasher()
    async with factory() as session:
        stmt = select(User).where(User.email.ilike('%ramiro%'))
        user = (await session.execute(stmt)).scalar_one_or_none()
        print("Ramiro user email:", user.email)
        print("Username:", user.username)
        # Check standard dev passwords
        for pwd in ["Password123!", "Admin123!", "pevn2026", "Pevn2026!", "Pevn123!", "password", "12345678", "Secret123!", "Estudiante2026!", "Estudiante123!", "Colombia2026!"]:
            try:
                if hasher.verify(user.hashed_password, pwd):
                    print(f"Matched password: {pwd}")
                    break
            except Exception:
                pass
        else:
            print("Password hash:", user.hashed_password)

if __name__ == '__main__':
    asyncio.run(main())
