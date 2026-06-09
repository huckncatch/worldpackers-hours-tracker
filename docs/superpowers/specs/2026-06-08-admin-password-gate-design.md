# Admin Password Gate — Design Spec

**Date:** 2026-06-08
**Status:** Approved

## Goal

Protect the `/ops` admin area with a single shared password so that packers using the
dashboard cannot stumble into or modify admin data.

## Scope

Additive only. No existing routes or templates are modified. The gate is a hook + two new
route handlers + one new template.

## Password Storage

- Env var: `OPS_PASSWORD`
- Loaded in `create_app()` via `os.environ.get("OPS_PASSWORD", "changeme")` and stored in
  `app.config["OPS_PASSWORD"]`
- Immediately after loading (still inside `create_app()`), log a `WARNING` if the value
  equals `"changeme"` so the misconfiguration is visible at startup, not per-request

## Authentication Flow

1. User visits any `/ops/*` URL
2. Admin blueprint `before_request` hook fires
3. **Login route is always exempt** — if `request.endpoint == "admin.login"`, return
   immediately so the login page is reachable by unauthenticated users
4. If `session.get("ops_authed")` is falsy → `redirect(url_for("admin.login", next=request.path))`
5. If truthy → request proceeds normally

**Login:**
- `GET /ops/login` — render `admin_login.html`; pass any `?next=` param through to the form
- `POST /ops/login` — compare submitted password (from `request.form["password"]`, a `str`)
  with `current_app.config["OPS_PASSWORD"]` (also a `str`) using `hmac.compare_digest`.
  Both arguments must be the same type (`str`); do not encode either side to `bytes`.
  - **Match:** set `session["ops_authed"] = True`, sanitize and redirect to `next` or `/ops`
  - **No match:** re-render form with `error="Wrong password"`

**`next` param sanitization:** parse with `urllib.parse.urlparse`. Reject if the parsed
result has a non-empty `scheme` or `netloc` (catches absolute URLs and protocol-relative
URLs). Additionally require the path starts with `/ops`. If either check fails, fall back
to `/ops`.

## Template

`templates/admin_login.html` extends `base.html`.

- Centered card layout consistent with existing pages
- Single `<input type="password" name="password">` field
- Submit button styled with existing green Tailwind classes
- Optional red error message shown when `error` is passed

## Security Notes

- `hmac.compare_digest` used for constant-time comparison to prevent timing side-channels.
  Both operands must be `str` (not `bytes`) — mixing types raises `TypeError`.
- `next` param validated against both URL structure (no scheme/netloc) and path prefix
  (`/ops`) before redirect
- Flask session cookie is signed with `SECRET_KEY` (already configured in `app.py`)
- Session is browser-session only (`SESSION_COOKIE_PERMANENT` defaults to `False`).
  Note: browsers with session-restore (Chrome, Firefox) may persist session cookies across
  restarts — accepted limitation for a single-user personal tool.
- No CSRF protection — consistent with the rest of the app

## Files Touched

| File | Change |
|---|---|
| `app.py` | Load `OPS_PASSWORD` from env into `app.config`; warn at startup if default |
| `routes/admin.py` | Add `before_request` hook (with login exemption); add `login` GET/POST handler |
| `templates/admin_login.html` | New login form template |

## Out of Scope

- Logout route (session expires when browser closes / tab is discarded)
- Per-user accounts or roles
- Rate limiting on failed attempts
