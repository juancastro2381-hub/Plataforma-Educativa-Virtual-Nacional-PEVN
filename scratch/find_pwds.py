import asyncio
from app.db.session import get_session_factory
from app.models.user import User
from app.core.security.password import Argon2PasswordHasher
from sqlalchemy import select

async def main():
    factory = get_session_factory()
    hasher = Argon2PasswordHasher()
    async with factory() as session:
        for email in ['rectoria@glenndoman.edu.co', 'profesor@glenndoman.edu.co', 'ramiro.rey@colegio.edu.co', 'admin@pevn.edu.co']:
            stmt = select(User).where(User.email == email)
            user = (await session.execute(stmt)).scalar_one_or_none()
            if not user:
                print(f"User {email} not found")
                continue
            for pwd in [
                "Password123!", "Admin123!", "pevn2026", "Pevn2026!", "Pevn123!",
                "password", "12345678", "Secret123!", "Estudiante2026!",
                "Rector2026!", "Docente2026!", "GlennDoman2026!", "Demo2026!",
                "Admin2026!", "SuperAdmin2026!", "Colombia2026!"
            ]:
                try:
                    if hasher.verify(user.hashed_password, pwd):
                        print(f"User {email} matches password: '{pwd}'")
                        break
                except Exception:
                    pass
            else:
                print(f"User {email} password not in tested list.")

if __name__ == '__main__':
    asyncio.run(main())
