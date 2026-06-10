import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


def test_ops_password_in_config(app):
    assert app.config["OPS_PASSWORD"] == "testpass"
