import asyncio
from sqlalchemy import select

from hans.core.db import SessionLocal
from hans.core.auth import User, hash_password


async def seed_admin():
    async with SessionLocal() as db:
        result = await db.execute(
            select(User).where(User.username == "hans")
        )
        user = result.scalar_one_or_none()

        if user:
            print("Admin already exists.")
            return

        db.add(
            User(
                username="hans",
                email="hans@example.com",
                role="admin",
                hashed_password=hash_password("hans"),
            )
        )
        await db.commit()
        print("Admin created.")


if __name__ == "__main__":
    asyncio.run(seed_admin())