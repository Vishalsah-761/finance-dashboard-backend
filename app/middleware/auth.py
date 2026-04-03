from functools import wraps
from flask_jwt_extended import (
    get_jwt_identity,
    verify_jwt_in_request,
    get_jwt
)
from app.utils.constants import Role
from app.utils.responses import forbidden, unauthorized


def _get_current_user_id():
    return get_jwt_identity()


def _get_claims():
    return get_jwt()


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return unauthorized("A valid access token is required.")
        return f(*args, **kwargs)
    return decorated


def require_role(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return unauthorized("A valid access token is required.")

            claims = _get_claims()

            if claims.get("role") not in allowed_roles:
                return forbidden(
                    f"This action requires one of the following roles: "
                    f"{', '.join(allowed_roles)}."
                )

            return f(*args, **kwargs)
        return decorated
    return decorator


def require_active(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return unauthorized("A valid access token is required.")

        claims = _get_claims()

        if claims.get("status") != "active":
            return forbidden("Your account is inactive. Please contact an administrator.")

        return f(*args, **kwargs)
    return decorated