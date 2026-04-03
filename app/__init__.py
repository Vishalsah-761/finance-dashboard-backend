from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

mongo = PyMongo()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app(config_object=None):
    app = Flask(__name__)

    if config_object:
        app.config.from_object(config_object)
    else:
        from app.config import Config
        app.config.from_object(Config)

    mongo.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.records import records_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(records_bp, url_prefix="/api/records")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")

    # Root + health check
    @app.get("/")
    def index():
        return {
            "name":    "Finance Dashboard API",
            "version": "1.0.0",
            "status":  "running",
            "docs":    {
                "auth":      "/api/auth",
                "users":     "/api/users",
                "records":   "/api/records",
                "dashboard": "/api/dashboard",
            },
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Ensure indexes on startup
    with app.app_context():
        _ensure_indexes()

    return app


def _ensure_indexes():
    """Create MongoDB indexes for performance and uniqueness."""
    try:
        mongo.db.users.create_index("email", unique=True)
        mongo.db.users.create_index("username", unique=True)
        mongo.db.records.create_index([("user_id", 1), ("date", -1)])
        mongo.db.records.create_index("category")
        mongo.db.records.create_index("type")
    except Exception:
        pass  # Indexes may already exist
