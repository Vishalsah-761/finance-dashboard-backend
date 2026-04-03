from datetime import datetime
from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from app.utils.constants import Role, RecordType, VALID_CATEGORIES, UserStatus


# ── Auth / User schemas ───────────────────────────────────────────────────────

class RegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=30))
    email    = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=72),
                          load_only=True)
    role     = fields.Str(load_default=Role.VIEWER,
                          validate=validate.OneOf(Role.ALL))

    @validates("username")
    def validate_username(self, value):
        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValidationError(
                "Username may only contain letters, numbers, hyphens, and underscores."
            )


class LoginSchema(Schema):
    email    = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UpdateUserSchema(Schema):
    role   = fields.Str(validate=validate.OneOf(Role.ALL))
    status = fields.Str(validate=validate.OneOf(UserStatus.ALL))


class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True, load_only=True)
    new_password     = fields.Str(required=True, load_only=True,
                                  validate=validate.Length(min=6, max=72))


# ── Record schemas ────────────────────────────────────────────────────────────

class RecordCreateSchema(Schema):
    amount   = fields.Float(required=True, validate=validate.Range(min=0.01))
    type     = fields.Str(required=True, validate=validate.OneOf(RecordType.ALL))
    category = fields.Str(required=True,
                          validate=validate.OneOf(VALID_CATEGORIES))
    date     = fields.Date(required=True)          # expects YYYY-MM-DD
    notes    = fields.Str(load_default="", validate=validate.Length(max=500))

    @post_load
    def convert_date(self, data, **kwargs):
        # Store as datetime at midnight UTC for aggregation consistency
        if isinstance(data.get("date"), datetime.date.__class__):
            data["date"] = datetime.combine(data["date"],
                                            datetime.min.time())
        return data


class RecordUpdateSchema(Schema):
    amount   = fields.Float(validate=validate.Range(min=0.01))
    type     = fields.Str(validate=validate.OneOf(RecordType.ALL))
    category = fields.Str(validate=validate.OneOf(VALID_CATEGORIES))
    date     = fields.Date()
    notes    = fields.Str(validate=validate.Length(max=500))

    @post_load
    def convert_date(self, data, **kwargs):
        if "date" in data and not isinstance(data["date"], datetime):
            data["date"] = datetime.combine(data["date"], datetime.min.time())
        return data
