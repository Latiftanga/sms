"""
Create a SUPERADMIN user.

Usage (interactive):
    docker compose run --rm api python scripts/create_superuser.py

Usage (non-interactive / CI):
    docker compose run --rm api python scripts/create_superuser.py \
        --email admin@ttek.gh --password Secret1234!
"""
import argparse
import asyncio
import getpass
import sys
import uuid
from pathlib import Path

# Ensure the project root (/app) is on sys.path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select


async def main(email: str, password: str) -> None:
    from app.core.db import AsyncSessionLocal
    from app.core.security import hash_password
    from app.models.user import User

    if len(password) < 8:
        print("Error: password must be at least 8 characters.")
        sys.exit(1)

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            print(f"User '{email}' already exists.")
            sys.exit(0)

        session.add(User(
            id=uuid.uuid4(),
            email=email,
            password_hash=hash_password(password),
            system_role="SUPERADMIN",
            is_active=True,
            is_verified=True,
        ))
        await session.commit()

    print(f"Superadmin '{email}' created successfully.")


def prompt() -> tuple[str, str]:
    email = input("Email: ").strip()
    if not email:
        print("Email cannot be empty.")
        sys.exit(1)
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)
    return email, password


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a SUPERADMIN user.")
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    args = parser.parse_args()

    if args.email and args.password:
        email, password = args.email, args.password
    else:
        email, password = prompt()

    asyncio.run(main(email, password))
