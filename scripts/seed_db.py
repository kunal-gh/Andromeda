#!/usr/bin/env python3
"""
scripts/seed_db.py — Manually reseed the database from synthetic_crm.json.

Useful after wiping the database or changing the seed data.
    python scripts/seed_db.py
    python scripts/seed_db.py --wipe  # drop all tables, recreate, reseed
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    parser = argparse.ArgumentParser(description="Seed Andromeda database")
    parser.add_argument("--wipe", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()

    from app.db.database import Base, SessionLocal, engine
    from app.db.seed import init_db, seed_if_empty

    if args.wipe:
        print("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("Recreating schema...")

    init_db()
    db = SessionLocal()
    try:
        seed_if_empty(db)
        from app.db.models import Customer, Order
        customer_count = db.query(Customer).count()
        order_count = db.query(Order).count()
        print(f"✅ Database ready: {customer_count} customers, {order_count} orders")
    finally:
        db.close()


if __name__ == "__main__":
    main()
