from datetime import datetime, timezone
from bson import ObjectId


class RecordModel:
    """
    Schema for the `records` collection.

    {
        _id:        ObjectId
        user_id:    str   (owner – the admin who created it)
        amount:     float (always positive; type determines sign)
        type:       str   (income | expense)
        category:   str
        date:       datetime
        notes:      str   (optional)
        deleted:    bool  (soft-delete flag)
        created_at: datetime
        updated_at: datetime
    }
    """

    COLLECTION = "records"

    @staticmethod
    def build(user_id: str, amount: float, record_type: str,
              category: str, date: datetime,
              notes: str = "") -> dict:
        now = datetime.now(timezone.utc)
        return {
            "user_id":    user_id,
            "amount":     round(float(amount), 2),
            "type":       record_type,
            "category":   category,
            "date":       date,
            "notes":      notes or "",
            "deleted":    False,
            "created_at": now,
            "updated_at": now,
        }

    @staticmethod
    def to_dict(doc: dict) -> dict:
        return {
            "id":         str(doc["_id"]),
            "user_id":    doc["user_id"],
            "amount":     doc["amount"],
            "type":       doc["type"],
            "category":   doc["category"],
            "date":       doc["date"].strftime("%Y-%m-%d"),
            "notes":      doc.get("notes", ""),
            "created_at": doc["created_at"].isoformat(),
            "updated_at": doc["updated_at"].isoformat(),
        }
