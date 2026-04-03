from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required
)
from marshmallow import ValidationError
from datetime import timedelta

from app.middleware.auth import require_active
from app.middleware.schemas import RegisterSchema, LoginSchema, ChangePasswordSchema
from app.services.user_service import UserService
from app.models.user import UserModel
from app.utils.responses import success, created, error, unauthorized, forbidden

auth_bp = Blueprint("auth", __name__)

_register_schema  = RegisterSchema()
_login_schema     = LoginSchema()
_change_pw_schema = ChangePasswordSchema()


@auth_bp.get("/ping")
def ping():
    return success({"message": "Server is working fine!"})


@auth_bp.post("/register")
def register():
    try:
        data = _register_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    user, err = UserService.create_user(
        username=data["username"],
        email=data["email"],
        password=data["password"],
        role=data.get("role", "viewer"),
    )
    if err:
        return error(err, 409)

    token = _make_token(user)

    return created(
        {"user": UserModel.to_dict(user), "access_token": token},
        "Account created successfully.",
    )


@auth_bp.post("/login")
def login():
    try:
        data = _login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    user = UserService.get_by_email(data["email"])
    if not user or not UserService.verify_password(user, data["password"]):
        return unauthorized("Invalid email or password.")

    if user["status"] != "active":
        return forbidden("Your account is inactive.")

    token = _make_token(user)

    return success(
        {"user": UserModel.to_dict(user), "access_token": token},
        "Login successful.",
    )


#  FIXED ROUTE
@auth_bp.get("/me")
@jwt_required()
@require_active
def me():
    user_id = get_jwt_identity()
    user = UserService.get_by_id(user_id)

    if not user:
        return error("User not found.", 404)

    return success(UserModel.to_dict(user))


@auth_bp.post("/change-password")
@jwt_required()
@require_active
def change_password():
    try:
        data = _change_pw_schema.load(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return error("Validation failed.", 422, exc.messages)

    user_id = get_jwt_identity()

    ok, msg = UserService.change_password(
        user_id,
        data["current_password"],
        data["new_password"],
    )

    if not ok:
        return error(msg, 400)

    return success(message=msg)


#  FINAL TOKEN GENERATION (BEST PRACTICE)
def _make_token(user: dict) -> str:
    return create_access_token(
        identity=str(user["_id"]),   # only ID
        additional_claims={
            "email": user["email"],
            "role": user["role"],
            "status": user["status"],
        },
        expires_delta=timedelta(hours=24),
    )
