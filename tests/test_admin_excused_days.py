from datetime import date
import models


def _make_packer(app, name="TestPacker"):
    with app.app_context():
        return models.create_packer(
            name, date(2026,6,1), date(2026,6,28),
            date(2026,6,1), date(2026,6,28)
        )


def test_excused_days_requires_auth(client):
    resp = client.get("/ops/excused-days")
    assert resp.status_code == 302
    assert "/ops/login" in resp.headers["Location"]


def test_excused_days_list_loads(authed_client):
    resp = authed_client.get("/ops/excused-days")
    assert resp.status_code == 200


def test_add_global_excused_day(authed_client):
    resp = authed_client.post("/ops/excused-days/new", data={
        "excused_date": "2026-06-10",
        "packer_id": "",
        "reason": "Host day off",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"All packers" in resp.data
    assert b"Host day off" in resp.data


def test_add_per_packer_excused_day(authed_client, app):
    pid = _make_packer(app, "Maria")
    resp = authed_client.post("/ops/excused-days/new", data={
        "excused_date": "2026-06-12",
        "packer_id": str(pid),
        "reason": "Personal travel",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Maria" in resp.data
    assert b"Personal travel" in resp.data


def test_delete_excused_day(authed_client, app):
    with app.app_context():
        excused_id = models.create_excused_day(packer_id=None, excused_date=date(2026, 6, 10),
                                                 reason="Host day off")
    resp = authed_client.post(f"/ops/excused-days/{excused_id}/delete", follow_redirects=True)
    assert resp.status_code == 200
    assert b"Host day off" not in resp.data


def test_excused_day_reduces_target_via_stats_api(client, app):
    pid = _make_packer(app)
    with app.app_context():
        # Excuse one day in week 1
        models.create_excused_day(packer_id=pid, excused_date=date(2026, 6, 3), reason="Travel")
    # No entries, today = start of week 2 -> week 1 fully missed
    resp = client.get(f"/api/packer/{pid}/stats?today=2026-06-08")
    assert resp.status_code == 200
    data = resp.json
    # Without the excused day, cumulative_balance would be -25.0; with one
    # excused day, week 1's target drops by 5h to 20.0
    assert data["cumulative_balance"] == -20.0
