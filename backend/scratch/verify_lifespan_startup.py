import asyncio
from app.main import app, lifespan

async def test_startup():
    print("Executing lifespan startup...")
    async with lifespan(app):
        print("Application startup executed successfully inside lifespan context.")

if __name__ == "__main__":
    asyncio.run(test_startup())
