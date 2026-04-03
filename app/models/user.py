from datetime import datetime, timezone
from bson import ObjectId
from app.utils.constants import Role, UserStatus


class UserModel:
    """
    Schema for the `users` collection.

    {
        _id:        ObjectId
        username:   str  (unique)
        email:      str  (unique)
        password:   str  (bcrypt hash)
        role:       str  (viewer | analyst | admin)
        status:     str  (active | inactive)
        created_at: datetime
        updated_at: datetime
    }
    """

    COLLECTION = "users"

    @staticmethod
    def build(username: str, email: str, hashed_password: str,
              role: str = Role.VIEWER) -> dict:
        now = datetime.now(timezone.utc)
        return {
            "username":   username.strip().lower(),
            "email":      email.strip().lower(),
            "password":   hashed_password,
            "role":       role,
            "status":     UserStatus.ACTIVE,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def to_dict(doc: dict) -> dict:
        """Serialize a MongoDB document, removing the password hash."""
        return {
            "id":         str(doc["_id"]),
            "username":   doc["username"],
            "email":      doc["email"],
            "role":       doc["role"],
            "status":     doc["status"],
            "created_at": doc["created_at"].isoformat(),
            "updated_at": doc["updated_at"].isoformat(),
        }
