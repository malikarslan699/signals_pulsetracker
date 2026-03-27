#!/usr/bin/env python3
"""
Create initial admin user for PulseSignal Pro
Usage: python scripts/create_admin.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def create_admin():
    from app.database import AsyncSessionFactory, create_tables
    from app.models.user import User
    from app.core.auth import get_password_hash, generate_api_key
    from sqlalchemy import select
    from uuid import uuid4
    from datetime import datetime, timezone

    await create_tables()

    email = input("Admin email: ").strip()
    username = input("Admin username: ").strip()
    password = input("Admin password (min 8 chars): ").strip()

    if len(password) < 8:
        print("Password too short!")
        return

    async with AsyncSessionFactory() as session:
        # Check if email exists
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"User {email} already exists!")
            return

        admin = User(
            id=uuid4(),
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            role="admin",
            plan="lifetime",
            is_active=True,
            is_verified=True,
            api_key=generate_api_key(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        session.add(admin)
        await session.commit()

        print(f"\nAdmin user created!")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   API Key: {admin.api_key}")

if __name__ == "__main__":
    asyncio.run(create_admin())
