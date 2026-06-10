from datetime import date
import models


def _make_packer(app, name="TestPacker"):
    with app.app_context():
        return models.create_packer(
            name, date(2026,6,1), date(2026,6,28),
            date(2026,6,1), date(2026,6,28)
        )


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"

def test_dashboard_stub(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_admin_list(authed_client):
    resp = authed_client.get("/ops/")
    assert resp.status_code == 200


def test_admin_create_packer(authed_client):
    resp = authed_client.post("/ops/packers/new", data={
        "name": "Maria",
        "arrival_date": "2026-06-01",
        "departure_date": "2026-06-28",
        "tracking_start_date": "2026-06-02",
        "tracking_end_date": "2026-06-27",
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Maria" in resp.data


def test_admin_lock_packer(authed_client, app):
    pid = _make_packer(app)
    resp = authed_client.post(f"/ops/packers/{pid}/lock", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        packer = models.get_packer(pid)
        assert packer["locked"] == 1


def test_admin_hide_packer(authed_client, app):
    pid = _make_packer(app)
    resp = authed_client.post(f"/ops/packers/{pid}/hide", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        packer = models.get_packer(pid)
        assert packer["hidden"] == 1


def test_log_select_shows_active_packers(client, app):
    _make_packer(app, "Visible")
    resp = client.get("/log/")
    assert resp.status_code == 200
    assert b"Visible" in resp.data


def test_log_entry_form_get(client, app):
    pid = _make_packer(app)
    resp = client.get(f"/log/{pid}")
    assert resp.status_code == 200


def test_log_entry_submit_creates_entry(client, app):
    pid = _make_packer(app)
    resp = client.post(f"/log/{pid}", data={
        "entry_date": "2026-06-07",
        "start_time": "09:00",
        "end_time": "12:00",
        "task_description": "Weeding",
    }, follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        entries = models.get_entries_for_packer(pid)
        assert len(entries) == 1
        assert entries[0]["duration_minutes"] == 180
        assert entries[0]["task_description"] == "Weeding"


def test_log_entry_delete(client, app):
    pid = _make_packer(app)
    with app.app_context():
        eid = models.create_work_entry(pid, date(2026,6,7), "09:00", "10:00", 60, None)
    resp = client.post(f"/log/{pid}/entries/{eid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert len(models.get_entries_for_packer(pid)) == 0


def test_api_packer_stats(client, app):
    pid = _make_packer(app)
    with app.app_context():
        models.create_work_entry(pid, date(2026,6,1), "09:00", "12:00", 180, None)
    resp = client.get(f"/api/packer/{pid}/stats?today=2026-06-01")
    assert resp.status_code == 200
    data = resp.json
    assert "this_week_hours" in data
    assert "adjusted_target_this_week" in data
    assert "hours_by_day" in data
    assert data["this_week_hours"] == 3.0


def test_dashboard_shows_active_packers(client, app):
    _make_packer(app, "DashPacker")
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"DashPacker" in resp.data
