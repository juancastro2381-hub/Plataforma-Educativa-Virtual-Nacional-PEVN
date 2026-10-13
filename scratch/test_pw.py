import sys
import os
sys.path.insert(0, os.path.abspath('backend'))
import asyncio
from app.db.session import get_session_factory
from sqlalchemy import text
from app.core.security.password import password_hasher

async def check():
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = (await session.execute(text("SELECT email, hashed_password FROM users WHERE email='rectoria@glenndoman.edu.co'"))).mappings().one_or_none()
        if user:
            print("Found user:", user['email'])
            # Test some standard passwords
            test_passwords = [
                "TestPass2026!*", "Admin2026!*", "Pevn2026!*", "Rector2026!*", 
                "Password123!", "PevnAdmin2026!*", "PevnDepartment2026!*", "Admin123456!*",
                "PevnDemo2026!*", "PevnSecure2026!*", "Colombia2026!*"
            ]
            for p in test_passwords:
                if password_hasher.verify(p, user['hashed_password']):
                    print("SUCCESS! Password is:", p)
                    return
            print("None of the standard passwords matched.")

asyncio.run(check())
