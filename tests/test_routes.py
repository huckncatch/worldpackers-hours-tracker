def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json["status"] == "ok"

def test_dashboard_stub(client):
    resp = client.get("/")
    assert resp.status_code == 200
