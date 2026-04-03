"""
seed.py – Populate the database with an admin user and sample records.
Run: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
import random

from app import create_app, mongo, bcrypt
from app.models.user import UserModel
from app.models.record import RecordModel
from app.utils.constants import Role, RecordType, UserStatus

SAMPLE_RECORDS = [
    # (amount, type, category, days_ago, notes)
    (5000.00, "income",  "salary",        1,  "Monthly salary"),
    (1200.00, "income",  "freelance",     5,  "Website project"),
    (300.00,  "income",  "investment",    10, "Dividend payout"),
    (80.00,   "expense", "food",          2,  "Weekly groceries"),
    (45.00,   "expense", "transport",     3,  "Uber rides"),
    (1500.00, "expense", "housing",       1,  "Rent payment"),
    (120.00,  "expense", "utilities",     4,  "Electricity bill"),
    (60.00,   "expense", "entertainment", 6,  "Netflix + Spotify"),
    (200.00,  "expense", "shopping",      7,  "Clothing"),
    (4800.00, "income",  "salary",        32, "Monthly salary"),
    (90.00,   "expense", "healthcare",    15, "Doctor visit"),
    (500.00,  "expense", "travel",        20, "Weekend trip"),
    (150.00,  "income",  "gift",          25, "Birthday money"),
    (35.00,   "expense", "food",          8,  "Restaurant dinner"),
    (700.00,  "income",  "freelance",     18, "Logo design"),
]


def seed():
    app = create_app()
    with app.app_context():
        users_col   = mongo.db[UserModel.COLLECTION]
        records_col = mongo.db[RecordModel.COLLECTION]

        # Clear existing data
        users_col.delete_many({})
        records_col.delete_many({})
        print("Cleared existing data.")

        # Create users
        def make_user(username, email, password, role):
            hashed = bcrypt.generate_password_hash(password).decode("utf-8")
            doc = UserModel.build(username, email, hashed, role)
            result = users_col.insert_one(doc)
            doc["_id"] = result.inserted_id
            return doc

        admin   = make_user("admin",   "admin@finance.dev",   "admin123",   Role.ADMIN)
        analyst = make_user("analyst", "analyst@finance.dev", "analyst123", Role.ANALYST)
        viewer  = make_user("viewer",  "viewer@finance.dev",  "viewer123",  Role.VIEWER)
        print(f"Created users: admin, analyst, viewer")

        # Create sample records
        for amount, rtype, category, days_ago, notes in SAMPLE_RECORDS:
            record_date = datetime.utcnow() - timedelta(days=days_ago)
            doc = RecordModel.build(
                user_id=str(admin["_id"]),
                amount=amount,
                record_type=rtype,
                category=category,
                date=record_date,
                notes=notes,
            )
            records_col.insert_one(doc)

        print(f"Created {len(SAMPLE_RECORDS)} sample records.")
        print("\n── Seed complete ──────────────────────────────────")
        print("  Admin:    admin@finance.dev   / admin123")
        print("  Analyst:  analyst@finance.dev / analyst123")
        print("  Viewer:   viewer@finance.dev  / viewer123")


if __name__ == "__main__":
    seed()
