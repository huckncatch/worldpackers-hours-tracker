# Admin Password Gate Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gate every `/ops` route behind a session-based password check so unauthenticated users are redirected to a login page.

**Architecture:** A `before_request` hook on the admin blueprint intercepts all `/ops` requests (exempting the login route itself), checks a Flask session flag, and redirects unauthenticated users to `/ops/login`. On correct password submission the flag is set and the user is forwarded to their original destination.

**Tech Stack:** Flask (sessions, blueprints), Python `hmac.compare_digest`, Jinja2 / Tailwind CSS

---

## Chunk 1: Backend + Tests

### File map

| File | Action | Purpose |
|---|---|---|
| `app.py` | Modify | Load `OPS_PASSWORD` from env; log startup warning if default |
| `routes/admin.py` | Modify | Add `before_request` hook + `login` GET/POST handler |
| `tests/conftest.py` | Modify | Add `OPS_PASSWORD` to test config; add `authed_client` fixture |
| `tests/test_admin_auth.py` | Create | Auth-specific tests (gate redirects, login flow, bad passwords, `next` sanitization) |
| `tests/test_routes.py` | Modify | Switch all existing `/ops` tests to use `authed_client` |

---

### Task 1: Add `OPS_PASSWORD` to app config

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_admin_auth.py` (create the file):

```python
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


def test_ops_password_in_config(app):
    assert app.config["OPS_PASSWORD"] == "testpass"
```

- [ ] **Step 2: Run to verify it fails**

```bash
.venv/bin/pytest tests/test_admin_auth.py::test_ops_password_in_config -v
```

Expected: `FAILED` — `KeyError: 'OPS_PASSWORD'`

- [ ] **Step 3: Update `conftest.py` to pass `OPS_PASSWORD` in test config**

In `tests/conftest.py`, update the `create_app` call inside the `app` fixture:

```python
test_app = create_app({
    "TESTING": True,
    "DATABASE": ":memory:",
    "OPS_PASSWORD": "testpass",
})
```

- [ ] **Step 4: Update `app.py` to load `OPS_PASSWORD`**

Add `import logging` at the top of `app.py` with the other imports. Then in `create_app()`, after `app.config.from_mapping(...)` and the `if config:` block, add:

```python
if "OPS_PASSWORD" not in app.config:
    app.config["OPS_PASSWORD"] = os.environ.get("OPS_PASSWORD", "changeme")
if app.config["OPS_PASSWORD"] == "changeme":
    logging.warning("OPS_PASSWORD is not set — using insecure default 'changeme'")
```

The `if "OPS_PASSWORD" not in app.config` guard lets tests inject a value via the config dict without it being overwritten by the env var.

- [ ] **Step 5: Run test to verify it passes**

```bash
.venv/bin/pytest tests/test_admin_auth.py::test_ops_password_in_config -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add app.py tests/conftest.py tests/test_admin_auth.py
git commit -m "feat: load OPS_PASSWORD into app config"
```

---

### Task 2: Add `before_request` hook and login route

**Files:**
- Modify: `routes/admin.py`

- [ ] **Step 1: Write failing tests for the auth gate**

Append to `tests/test_admin_auth.py`:

```python
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
    # Falls back to /ops, not /log/
    assert resp.headers["Location"].endswith("/ops") or \
           resp.headers["Location"].endswith("/ops/")
```

- [ ] **Step 2: Run to verify they fail**

```bash
.venv/bin/pytest tests/test_admin_auth.py -v
```

Expected: all new tests `FAILED` or `ERROR`; `test_ops_password_in_config` still passes.

- [ ] **Step 3: Implement `before_request` hook and login handler in `routes/admin.py`**

Add these imports at the top of `routes/admin.py`:

```python
import hmac
import logging
from urllib.parse import urlparse
from flask import session, current_app
```

Add the hook and login handler immediately after the `bp = Blueprint(...)` line (before the first route):

```python
@bp.before_request
def require_auth():
    if request.endpoint == "admin.login":
        return
    if not session.get("ops_authed"):
        return redirect(url_for("admin.login", next=request.path))


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        submitted = request.form.get("password", "")
        expected = current_app.config["OPS_PASSWORD"]
        if hmac.compare_digest(submitted, expected):
            session["ops_authed"] = True
            next_url = request.form.get("next") or request.args.get("next") or "/ops"
            parsed = urlparse(next_url)
            if parsed.scheme or parsed.netloc or not next_url.startswith("/ops"):
                next_url = "/ops"
            return redirect(next_url)
        error = "Wrong password"
    next_val = request.args.get("next", "")
    return render_template("admin_login.html", error=error, next=next_val)
```

- [ ] **Step 4: Run auth tests**

```bash
.venv/bin/pytest tests/test_admin_auth.py -v
```

Expected: all 9 tests `PASSED`

- [ ] **Step 5: Update existing `/ops` tests to use `authed_client`**

The `before_request` hook now blocks all unauthenticated `/ops` access, so the existing admin tests in `tests/test_routes.py` will fail. Fix this by adding an `authed_client` fixture to `tests/conftest.py`:

```python
@pytest.fixture()
def authed_client(client):
    client.post("/ops/login", data={"password": "testpass"})
    return client
```

Then update every test in `tests/test_routes.py` that accesses `/ops/` to use `authed_client` instead of `client`. For each, rename the parameter in **both the function signature and every call site inside the body**:

- `test_admin_list(client)` → `test_admin_list(authed_client)` (update `client.get(...)` → `authed_client.get(...)`)
- `test_admin_create_packer(client)` → `test_admin_create_packer(authed_client)` (update `client.post(...)` → `authed_client.post(...)`)
- `test_admin_lock_packer(client, app)` → `test_admin_lock_packer(authed_client, app)` (update `client.post(...)` → `authed_client.post(...)`)
- `test_admin_hide_packer(client, app)` → `test_admin_hide_packer(authed_client, app)` (update `client.post(...)` → `authed_client.post(...)`)

Non-`/ops` tests (`test_health`, `test_dashboard_stub`, `test_log_*`, `test_api_*`, `test_dashboard_shows_active_packers`) need no changes.

- [ ] **Step 6: Run the full test suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all 40 tests `PASSED` (31 original + 9 new auth tests)

- [ ] **Step 7: Commit**

```bash
git add routes/admin.py tests/conftest.py tests/test_admin_auth.py tests/test_routes.py
git commit -m "feat: add /ops password gate with session auth"
```

---

## Chunk 2: Login Template

### Task 3: Create `admin_login.html`

**Files:**
- Create: `templates/admin_login.html`

- [ ] **Step 1: Write template test**

Append to `tests/test_admin_auth.py`:

```python
def test_login_page_has_password_input(client):
    resp = client.get("/ops/login")
    assert b'type="password"' in resp.data
    assert b'name="password"' in resp.data

def test_login_page_no_error_by_default(client):
    resp = client.get("/ops/login")
    assert b"Wrong password" not in resp.data
```

- [ ] **Step 2: Run to verify tests fail (or pass trivially — accept either)**

```bash
.venv/bin/pytest tests/test_admin_auth.py::test_login_page_has_password_input tests/test_admin_auth.py::test_login_page_no_error_by_default -v
```

- [ ] **Step 3: Create `templates/admin_login.html`**

```html
{% extends "base.html" %}
{% block title %}Admin Login{% endblock %}
{% block content %}
<div class="max-w-sm mx-auto mt-16">
  <div class="bg-white rounded-2xl shadow p-8">
    <h1 class="text-xl font-bold mb-6 text-center">Admin Access</h1>
    {% if error %}
    <p class="text-red-600 text-sm text-center mb-4">{{ error }}</p>
    {% endif %}
    <form method="post" action="{{ url_for('admin.login', next=next) }}">
      <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
      <input type="password" name="password" autofocus
             class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                    focus:outline-none focus:ring-2 focus:ring-green-600 mb-4">
      <button type="submit"
              class="w-full bg-green-700 text-white rounded-lg py-2 text-sm font-medium
                     hover:bg-green-800">
        Enter
      </button>
    </form>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Run template tests**

```bash
.venv/bin/pytest tests/test_admin_auth.py -v
```

Expected: all 11 auth tests `PASSED`

- [ ] **Step 5: Run full suite**

```bash
.venv/bin/pytest tests/ -v
```

Expected: all 42 tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add templates/admin_login.html tests/test_admin_auth.py
git commit -m "feat: add admin login template"
```

---

## Chunk 3: Smoke Test + TODO Update

### Task 4: Manual smoke test and wrap-up

- [ ] **Step 1: Start the dev server**

```bash
OPS_PASSWORD=secret .venv/bin/python app.py
```

- [ ] **Step 2: Verify the gate in browser**

1. Open `http://localhost:5050/ops/` — confirm redirect to `/ops/login`
2. Submit wrong password — confirm "Wrong password" error
3. Submit `secret` — confirm redirect to `/ops/` and packer list is visible
4. Open a new tab to `http://localhost:5050/ops/` — confirm no re-prompt (session persists in tab)

- [ ] **Step 3: Update `TODO.md`**

Mark the admin password gate item as complete with today's date:

```markdown
- [x] **Admin password gate** — (2026-06-09)
```

- [ ] **Step 4: Final commit**

```bash
git add TODO.md
git commit -m "chore: mark admin password gate complete in TODO"
```
