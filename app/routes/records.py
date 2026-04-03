from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.middleware.auth import require_role, require_active
from app.middleware.schemas import RecordCreateSchema, RecordUpdateSchema
from app.services.record_service import RecordService
from app.models.record import RecordModel
from app.utils.constants import Role
from app.utils.responses import success, created, error, not_found
from app.utils.pagination import get_pagination_params, paginate_response

records_bp = Blueprint("records", __name__)

_create_schema = RecordCreateSchema()
_update_schema = RecordUpdateSchema()


# ✅ FIXED
@records_bp.get("/")
@jwt_required()
@require_active
def list_records():
    page, limit, skip = get_pagination_params()

    docs, total = RecordService.list_records(
        page=page, limit=limit, skip=skip,
        record_type=request.args.get("type"),
        category=request.args.get("category"),
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
        search=request.args.get("search"),
    )

    return success(paginate_response(
        [RecordModel.to_dict(d) for d in docs], total, page, limit
    ))


# ✅ FIXED
@records_bp.post("/")
@jwt_required()
@require_role(Role.ADMIN)
def create_record():
    try:
        data = _create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    user_id = get_jwt_identity()   # ✅ FIXED

    record_date = data["date"]
    if not isinstance(record_date, datetime):
        record_date = datetime(record_date.year, record_date.month, record_date.day)

    doc = RecordService.create(
        user_id=user_id,   # ✅ FIXED
        amount=data["amount"],
        record_type=data["type"],
        category=data["category"],
        record_date=record_date,
        notes=data.get("notes", ""),
    )

    return created(RecordModel.to_dict(doc), "Record created.")


# ✅ FIXED
@records_bp.get("/<record_id>")
@jwt_required()
@require_active
def get_record(record_id):
    doc = RecordService.get_by_id(record_id)
    if not doc:
        return not_found("Record not found.")
    return success(RecordModel.to_dict(doc))


# ✅ FIXED
@records_bp.patch("/<record_id>")
@jwt_required()
@require_role(Role.ADMIN)
def update_record(record_id):
    try:
        data = _update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    if "date" in data and not isinstance(data["date"], datetime):
        d = data["date"]
        data["date"] = datetime(d.year, d.month, d.day)

    doc, err = RecordService.update(record_id, data)

    if err:
        return not_found(err) if "not found" in err.lower() else error(err)

    return success(RecordModel.to_dict(doc), "Record updated.")


# ✅ FIXED
@records_bp.delete("/<record_id>")
@jwt_required()
@require_role(Role.ADMIN)
def delete_record(record_id):
    ok, msg = RecordService.soft_delete(record_id)

    if not ok:
        return not_found(msg)

    return success(message=msg)