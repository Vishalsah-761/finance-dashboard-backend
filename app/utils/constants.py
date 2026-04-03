"""
Shared constants for roles, record types, and categories.
"""

# ── Roles ────────────────────────────────────────────────────────────────────
class Role:
    VIEWER   = "viewer"
    ANALYST  = "analyst"
    ADMIN    = "admin"

    ALL = {VIEWER, ANALYST, ADMIN}

    # Ordered hierarchy: higher index → more permissions
    HIERARCHY = [VIEWER, ANALYST, ADMIN]

    @classmethod
    def has_at_least(cls, user_role: str, required_role: str) -> bool:
        try:
            return cls.HIERARCHY.index(user_role) >= cls.HIERARCHY.index(required_role)
        except ValueError:
            return False


# ── Record types ─────────────────────────────────────────────────────────────
class RecordType:
    INCOME  = "income"
    EXPENSE = "expense"
    ALL = {INCOME, EXPENSE}


# ── Categories ────────────────────────────────────────────────────────────────
VALID_CATEGORIES = {
    "salary", "freelance", "investment", "gift", "other_income",
    "food", "transport", "housing", "utilities", "healthcare",
    "entertainment", "education", "shopping", "travel", "other_expense",
}

# ── User status ───────────────────────────────────────────────────────────────
class UserStatus:
    ACTIVE   = "active"
    INACTIVE = "inactive"
    ALL = {ACTIVE, INACTIVE}
