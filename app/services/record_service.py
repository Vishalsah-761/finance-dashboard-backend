from datetime import datetime, timezone, date
from bson import ObjectId

from app import mongo
from app.models.record import RecordModel


class RecordService:

    @staticmethod
    def _col():
        return mongo.db[RecordModel.COLLECTION]

    # ── Internal helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _oid(record_id: str) -> ObjectId | None:
        try:
            return ObjectId(record_id)
        except Exception:
            return None

    @staticmethod
    def _base_query(include_deleted: bool = False) -> dict:
        if include_deleted:
            return {}
        return {"deleted": False}

    # ── CRUD ──────────────────────────────────────────────────────────────────

    @staticmethod
    def create(user_id: str, amount: float, record_type: str,
               category: str, record_date: datetime, notes: str = "") -> dict:
        doc = RecordModel.build(user_id, amount, record_type,
                                category, record_date, notes)
        result = RecordService._col().insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    @staticmethod
    def get_by_id(record_id: str) -> dict | None:
        oid = RecordService._oid(record_id)
        if not oid:
            return None
        return RecordService._col().find_one(
            {"_id": oid, **RecordService._base_query()}
        )

    @staticmethod
    def list_records(page: int, limit: int, skip: int,
                     record_type: str | None = None,
                     category: str | None = None,
                     date_from: str | None = None,
                     date_to: str | None = None,
                     search: str | None = None) -> tuple[list, int]:

        query = RecordService._base_query()

        if record_type:
            query["type"] = record_type
        if category:
            query["category"] = category

        # Date range filter
        date_filter: dict = {}
        if date_from:
            try:
                date_filter["$gte"] = datetime.strptime(date_from, "%Y-%m-%d")
            except ValueError:
                pass
        if date_to:
            try:
                date_filter["$lte"] = datetime.strptime(date_to, "%Y-%m-%d")
            except ValueError:
                pass
        if date_filter:
            query["date"] = date_filter

        # Simple text search on notes / category
        if search:
            query["$or"] = [
                {"notes":    {"$regex": search, "$options": "i"}},
                {"category": {"$regex": search, "$options": "i"}},
            ]

        col = RecordService._col()
        total = col.count_documents(query)
        docs = (
            col.find(query)
               .sort("date", -1)
               .skip(skip)
               .limit(limit)
        )
        return list(docs), total

    @staticmethod
    def update(record_id: str, updates: dict) -> tuple[dict | None, str | None]:
        oid = RecordService._oid(record_id)
        if not oid:
            return None, "Invalid record ID."

        record = RecordService._col().find_one(
            {"_id": oid, **RecordService._base_query()}
        )
        if not record:
            return None, "Record not found."

        allowed = {"amount", "type", "category", "date", "notes"}
        payload = {k: v for k, v in updates.items() if k in allowed}
        if not payload:
            return None, "No valid fields to update."

        if "amount" in payload:
            payload["amount"] = round(float(payload["amount"]), 2)

        payload["updated_at"] = datetime.now(timezone.utc)
        RecordService._col().update_one({"_id": oid}, {"$set": payload})
        return RecordService.get_by_id(record_id), None

    @staticmethod
    def soft_delete(record_id: str) -> tuple[bool, str]:
        oid = RecordService._oid(record_id)
        if not oid:
            return False, "Invalid record ID."
        result = RecordService._col().update_one(
            {"_id": oid, "deleted": False},
            {"$set": {"deleted": True,
                      "updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            return False, "Record not found."
        return True, "Record deleted."

    # ── Aggregations (used by dashboard) ──────────────────────────────────────

    @staticmethod
    def summary_totals(date_from: datetime | None = None,
                       date_to: datetime | None = None) -> dict:
        """Return total income, total expenses, and net balance."""
        match: dict = {"deleted": False}
        if date_from or date_to:
            date_filter: dict = {}
            if date_from:
                date_filter["$gte"] = date_from
            if date_to:
                date_filter["$lte"] = date_to
            match["date"] = date_filter

        pipeline = [
            {"$match": match},
            {"$group": {
                "_id":    "$type",
                "total":  {"$sum": "$amount"},
                "count":  {"$sum": 1},
            }},
        ]
        results = list(RecordService._col().aggregate(pipeline))

        income  = next((r for r in results if r["_id"] == "income"),  None)
        expense = next((r for r in results if r["_id"] == "expense"), None)

        total_income  = round(income["total"],  2) if income  else 0.0
        total_expense = round(expense["total"], 2) if expense else 0.0
        return {
            "total_income":   total_income,
            "total_expenses": total_expense,
            "net_balance":    round(total_income - total_expense, 2),
            "income_count":   income["count"]  if income  else 0,
            "expense_count":  expense["count"] if expense else 0,
        }

    @staticmethod
    def category_breakdown(record_type: str | None = None) -> list:
        """Return per-category totals, optionally filtered by type."""
        match: dict = {"deleted": False}
        if record_type:
            match["type"] = record_type
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id":   {"category": "$category", "type": "$type"},
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"total": -1}},
        ]
        return [
            {
                "category": r["_id"]["category"],
                "type":     r["_id"]["type"],
                "total":    round(r["total"], 2),
                "count":    r["count"],
            }
            for r in RecordService._col().aggregate(pipeline)
        ]

    @staticmethod
    def monthly_trends(year: int | None = None) -> list:
        """Return month-by-month income and expense totals."""
        match: dict = {"deleted": False}
        if year:
            match["date"] = {
                "$gte": datetime(year, 1, 1),
                "$lt":  datetime(year + 1, 1, 1),
            }
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {
                    "year":  {"$year":  "$date"},
                    "month": {"$month": "$date"},
                    "type":  "$type",
                },
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}},
        ]
        raw = list(RecordService._col().aggregate(pipeline))

        # Pivot into {year, month, income, expense} rows
        pivot: dict = {}
        for r in raw:
            key = (r["_id"]["year"], r["_id"]["month"])
            if key not in pivot:
                pivot[key] = {"year": key[0], "month": key[1],
                               "income": 0.0, "expense": 0.0}
            pivot[key][r["_id"]["type"]] = round(r["total"], 2)

        return sorted(pivot.values(), key=lambda x: (x["year"], x["month"]))

    @staticmethod
    def recent_activity(limit: int = 10) -> list:
        docs = (
            RecordService._col()
            .find({"deleted": False})
            .sort("created_at", -1)
            .limit(limit)
        )
        return list(docs)

    @staticmethod
    def weekly_trends(weeks: int = 8) -> list:
        """Return week-by-week totals for the last N weeks."""
        pipeline = [
            {"$match": {"deleted": False}},
            {"$group": {
                "_id": {
                    "year": {"$isoWeekYear": "$date"},
                    "week": {"$isoWeek":     "$date"},
                    "type": "$type",
                },
                "total": {"$sum": "$amount"},
            }},
            {"$sort": {"_id.year": -1, "_id.week": -1}},
            {"$limit": weeks * 2},
        ]
        raw = list(RecordService._col().aggregate(pipeline))

        pivot: dict = {}
        for r in raw:
            key = (r["_id"]["year"], r["_id"]["week"])
            if key not in pivot:
                pivot[key] = {
                    "year":    key[0],
                    "week":    key[1],
                    "income":  0.0,
                    "expense": 0.0,
                }
            pivot[key][r["_id"]["type"]] = round(r["total"], 2)

        return sorted(pivot.values(),
                      key=lambda x: (x["year"], x["week"]))[-weeks:]
