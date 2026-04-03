from datetime import datetime
from flask import Blueprint, request

from app.middleware.auth import require_role, require_active
from app.services.record_service import RecordService
from app.models.record import RecordModel
from app.utils.constants import Role
from app.utils.responses import success, error

dashboard_bp = Blueprint("dashboard", __name__)


def _parse_date(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        return None


@dashboard_bp.get("/summary")
@require_role(Role.ANALYST, Role.ADMIN)
def summary():
    """
    Overall totals: total income, total expenses, net balance.
    Optional query params: date_from, date_to  (YYYY-MM-DD)
    """
    date_from = _parse_date(request.args.get("date_from"))
    date_to   = _parse_date(request.args.get("date_to"))
    data = RecordService.summary_totals(date_from, date_to)
    return success(data)


@dashboard_bp.get("/categories")
@require_role(Role.ANALYST, Role.ADMIN)
def categories():
    """
    Category-wise totals.
    Optional query param: type  (income | expense)
    """
    record_type = request.args.get("type")
    data = RecordService.category_breakdown(record_type)
    return success(data)


@dashboard_bp.get("/monthly-trends")
@require_role(Role.ANALYST, Role.ADMIN)
def monthly_trends():
    """
    Month-by-month income vs expense.
    Optional query param: year  (e.g. 2024)
    """
    year_str = request.args.get("year")
    year = None
    if year_str:
        try:
            year = int(year_str)
        except ValueError:
            return error("'year' must be an integer.", 400)

    data = RecordService.monthly_trends(year)
    return success(data)


@dashboard_bp.get("/weekly-trends")
@require_role(Role.ANALYST, Role.ADMIN)
def weekly_trends():
    """
    Week-by-week totals for the last N weeks.
    Optional query param: weeks  (default 8)
    """
    try:
        weeks = int(request.args.get("weeks", 8))
        if weeks < 1 or weeks > 52:
            raise ValueError
    except ValueError:
        return error("'weeks' must be an integer between 1 and 52.", 400)

    data = RecordService.weekly_trends(weeks)
    return success(data)


@dashboard_bp.get("/recent-activity")
@require_active
def recent_activity():
    """
    Last N records across all types.
    Accessible to all active users (viewer, analyst, admin).
    Optional query param: limit  (default 10, max 50)
    """
    try:
        limit = min(50, max(1, int(request.args.get("limit", 10))))
    except ValueError:
        limit = 10

    docs = RecordService.recent_activity(limit)
    return success([RecordModel.to_dict(d) for d in docs])
