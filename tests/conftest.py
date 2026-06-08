import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
import db as database


@pytest.fixture()
def app():
    test_app = create_app({
        "TESTING": True,
        "DATABASE": ":memory:",
    })
    ctx = test_app.app_context()
    ctx.push()
    database.init_db()
    yield test_app
    ctx.pop()


@pytest.fixture()
def client(app):
    return app.test_client()
