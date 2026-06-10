import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


def test_ops_password_in_config(app):
    assert app.config["OPS_PASSWORD"] == "testpass"


def test_ops_redirects_unauthenticated(client):
    resp = client.get("/ops/")
    assert resp.status_code == 302
    assert "/ops/login" in resp.headers["Location"]

def test_login_page_loads(client):
    resp = client.get("/ops/login")
    assert resp.status_code == 200
    assert b"password" in resp.data.lower()

def test_wrong_password_shows_error(client):
    resp = client.post("/ops/login", data={"password": "wrong"})
    assert resp.status_code == 200
    assert b"Wrong password" in resp.data

def test_correct_password_redirects_to_ops(client):
    resp = client.post("/ops/login", data={"password": "testpass"},
                       follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/ops") or \
           resp.headers["Location"].endswith("/ops/")

def test_authenticated_can_access_ops(client):
    client.post("/ops/login", data={"password": "testpass"})
    resp = client.get("/ops/")
    assert resp.status_code == 200

def test_next_param_respected_on_login(client):
    resp = client.post("/ops/login?next=/ops/packers/new",
                       data={"password": "testpass"}, follow_redirects=False)
    assert "/ops/packers/new" in resp.headers["Location"]

def test_next_param_sanitized_rejects_external_url(client):
    resp = client.post("/ops/login",
                       data={"password": "testpass", "next": "http://evil.com"},
                       follow_redirects=False)
    assert "evil.com" not in resp.headers["Location"]

def test_next_param_sanitized_rejects_non_ops_path(client):
    resp = client.post("/ops/login",
                       data={"password": "testpass", "next": "/log/"},
                       follow_redirects=False)
    assert resp.headers["Location"].endswith("/ops") or \
           resp.headers["Location"].endswith("/ops/")


def test_login_page_has_password_input(client):
    resp = client.get("/ops/login")
    assert b'type="password"' in resp.data
    assert b'name="password"' in resp.data

def test_login_page_no_error_by_default(client):
    resp = client.get("/ops/login")
    assert b"Wrong password" not in resp.data
