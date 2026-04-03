import pytest
from app import create_app
from app.config import TestingConfig


@pytest.fixture(scope="session")
def app():
    application = create_app(TestingConfig)
    application.config["TESTING"] = True
    yield application


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def clean_db(app):
    """Drop all collections before each test."""
    with app.app_context():
        from app import mongo
        mongo.db.users.drop()
        mongo.db.records.drop()
    yield
