import os
from dotenv import load_dotenv
load_dotenv()

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

try:
    from scratch._safe_db import get_safe_test_db_url, mask_url_credentials
except ImportError:
    from _safe_db import get_safe_test_db_url, mask_url_credentials


async def test_connection():
    url = get_safe_test_db_url()
    masked = mask_url_credentials(url)
    print(f"Testing safe test database connection to {masked}...")
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT current_database(), current_user"))
            db, user = res.fetchone()
            print(f"SUCCESS: Connected to database='{db}' as user='{user}'")
    except Exception as e:
        print(f"FAILED connection to {masked}: {type(e).__name__}: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_connection())
