"""
Development seed — delegates to seed_schools.py.

Usage:
    docker compose run --rm api python scripts/seed_dev.py
"""
from seed_schools import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
