from flask import jsonify


def success(data=None, message="Success", status=200):
    body = {"success": True, "message": message}
    if data is not None:
        body["data"] = data
    return jsonify(body), status


def created(data=None, message="Created"):
    return success(data, message, 201)


def error(message="An error occurred", status=400, errors=None):
    body = {"success": False, "message": message}
    if errors:
        body["errors"] = errors
    return jsonify(body), status


def not_found(message="Resource not found"):
    return error(message, 404)


def forbidden(message="Access denied"):
    return error(message, 403)


def unauthorized(message="Authentication required"):
    return error(message, 401)


def conflict(message="Resource already exists"):
    return error(message, 409)
