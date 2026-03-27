#!/usr/bin/env python3
"""
Seed the initial owner/superadmin account for PulseSignal Pro.
Run inside the backend container:
  docker compose exec backend python /scripts/seed_owner.py

Or locally (with DB accessible):
  cd backend && python ../scripts/seed_owner.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# ─── Owner Credentials (change before going live) ────────────────────────────
OWNER_EMAIL    = "malik.g72@gmail.com"
OWNER_USERNAME = "owner"
OWNER_PASSWORD = "PulseOwner2025!"   # Change this after first login
OWNER_ROLE     = "superadmin"
# ─────────────────────────────────────────────────────────────────────────────

async def seed():
    from app.database import AsyncSessionFactory, create_tables
    from app.models.user import User
    from app.core.auth import get_password_hash, generate_api_key
    from sqlalchemy import select
    from uuid import uuid4
    from datetime import datetime, timezone

    print("Creating tables if not exist...")
    await create_tables()

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User).where(User.email == OWNER_EMAIL))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"[!] User already exists: {OWNER_EMAIL}")
            print(f"    Role:     {existing.role}")
            print(f"    Plan:     {existing.plan}")
            print(f"    API Key:  {existing.api_key}")
            return

        owner = User(
            id=uuid4(),
            email=OWNER_EMAIL,
            username=OWNER_USERNAME,
            password_hash=get_password_hash(OWNER_PASSWORD),
            role=OWNER_ROLE,
            plan="lifetime",
            is_active=True,
            is_verified=True,
            api_key=generate_api_key(),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        session.add(owner)
        await session.commit()
        await session.refresh(owner)

        print("\n" + "="*50)
        print("  ✅ Owner account created!")
        print("="*50)
        print(f"  Email:    {OWNER_EMAIL}")
        print(f"  Username: {OWNER_USERNAME}")
        print(f"  Password: {OWNER_PASSWORD}")
        print(f"  Role:     {OWNER_ROLE}")
        print(f"  Plan:     lifetime")
        print(f"  API Key:  {owner.api_key}")
        print("="*50)
        print("  ⚠️  Change your password after first login!")
        print("="*50 + "\n")


if __name__ == "__main__":
    asyncio.run(seed())
