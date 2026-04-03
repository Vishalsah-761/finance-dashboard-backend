from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from flask_bcrypt import check_password_hash, generate_password_hash

from app import mongo, bcrypt
from app.models.user import UserModel
from app.utils.constants import Role, UserStatus


class UserService:

    @staticmethod
    def _col():
        return mongo.db[UserModel.COLLECTION]

    # ── Lookup helpers ────────────────────────────────────────────────────────

    @staticmethod
    def get_by_id(user_id: str) -> dict | None:
        try:
            oid = ObjectId(user_id)
        except Exception:
            return None
        return UserService._col().find_one({"_id": oid})

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        return UserService._col().find_one({"email": email.lower()})

    # ── Auth operations ───────────────────────────────────────────────────────

    @staticmethod
    def create_user(username: str, email: str, password: str,
                    role: str = Role.VIEWER) -> tuple[dict | None, str | None]:
        """
        Returns (user_doc, error_message).
        error_message is None on success.
        """
        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        doc = UserModel.build(username, email, hashed, role)
        try:
            result = UserService._col().insert_one(doc)
            doc["_id"] = result.inserted_id
            return doc, None
        except DuplicateKeyError as exc:
            if "email" in str(exc):
                return None, "A user with this email already exists."
            return None, "A user with this username already exists."

    @staticmethod
    def verify_password(user_doc: dict, password: str) -> bool:
        return bcrypt.check_password_hash(user_doc["password"], password)

    @staticmethod
    def change_password(user_id: str, current_pw: str,
                        new_pw: str) -> tuple[bool, str]:
        user = UserService.get_by_id(user_id)
        if not user:
            return False, "User not found."
        if not UserService.verify_password(user, current_pw):
            return False, "Current password is incorrect."
        new_hash = bcrypt.generate_password_hash(new_pw).decode("utf-8")
        UserService._col().update_one(
            {"_id": user["_id"]},
            {"$set": {"password": new_hash,
                      "updated_at": datetime.now(timezone.utc)}}
        )
        return True, "Password updated."

    # ── Admin operations ──────────────────────────────────────────────────────

    @staticmethod
    def list_users(page: int, limit: int, skip: int,
                   role_filter: str | None = None,
                   status_filter: str | None = None) -> tuple[list, int]:
        query: dict = {}
        if role_filter:
            query["role"] = role_filter
        if status_filter:
            query["status"] = status_filter

        col = UserService._col()
        total = col.count_documents(query)
        docs = list(col.find(query).sort("created_at", -1).skip(skip).limit(limit))
        return docs, total

    @staticmethod
    def update_user(user_id: str, updates: dict) -> tuple[dict | None, str | None]:
        user = UserService.get_by_id(user_id)
        if not user:
            return None, "User not found."

        allowed = {"role", "status"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return None, "No valid fields to update."

        payload["updated_at"] = datetime.now(timezone.utc)
        UserService._col().update_one({"_id": user["_id"]}, {"$set": payload})
        return UserService.get_by_id(user_id), None

    @staticmethod
    def delete_user(user_id: str) -> tuple[bool, str]:
        user = UserService.get_by_id(user_id)
        if not user:
            return False, "User not found."
        UserService._col().delete_one({"_id": user["_id"]})
        return True, "User deleted."
