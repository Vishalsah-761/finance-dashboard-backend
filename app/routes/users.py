from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.middleware.auth import require_role, require_active
from app.middleware.schemas import RegisterSchema, UpdateUserSchema
from app.services.user_service import UserService
from app.models.user import UserModel
from app.utils.constants import Role
from app.utils.responses import success, created, error, not_found, forbidden
from app.utils.pagination import get_pagination_params, paginate_response

users_bp = Blueprint("users", __name__)

_register_schema = RegisterSchema()
_update_schema   = UpdateUserSchema()


@users_bp.get("/")
@require_role(Role.ADMIN)
def list_users():
    page, limit, skip = get_pagination_params()
    role_filter   = request.args.get("role")
    status_filter = request.args.get("status")

    docs, total = UserService.list_users(page, limit, skip,
                                         role_filter, status_filter)
    return success(paginate_response(
        [UserModel.to_dict(d) for d in docs], total, page, limit
    ))


@users_bp.post("/")
@require_role(Role.ADMIN)
def create_user():
    """Admin can create users with any role including admin."""
    try:
        data = _register_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    user, err = UserService.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
        role=data.get("role", Role.VIEWER),
    )
    if err:
        return error(err, 409)

    return created(UserModel.to_dict(user), "User created.")


@users_bp.get("/<user_id>")
@require_role(Role.ADMIN)
def get_user(user_id):
    user = UserService.get_by_id(user_id)
    if not user:
        return not_found("User not found.")
    return success(UserModel.to_dict(user))


@users_bp.patch("/<user_id>")
@require_role(Role.ADMIN)
def update_user(user_id):
    """Admin can change a user's role or status."""
    try:
        data = _update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    # Prevent admin from deactivating themselves
    identity = get_jwt_identity()
    if identity["id"] == user_id and data.get("status") == "inactive":
        return forbidden("You cannot deactivate your own account.")

    user, err = UserService.update_user(user_id, data)
    if err:
        return not_found(err) if "not found" in err else error(err)
    return success(UserModel.to_dict(user), "User updated.")


@users_bp.delete("/<user_id>")
@require_role(Role.ADMIN)
def delete_user(user_id):
    identity = get_jwt_identity()
    if identity["id"] == user_id:
        return forbidden("You cannot delete your own account.")

    ok, msg = UserService.delete_user(user_id)
    if not ok:
        return not_found(msg)
    return success(message=msg)
