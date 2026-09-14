import os

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "app.db")
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
client.__enter__()  # triggers startup -> loads alerts.json + clusters.json


def test_health():
    r = client.get("/")
    assert r.status_code == 200


def test_list_alerts():
    r = client.get("/api/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    assert len(body["alerts"]) >= 1


def test_get_alert_by_real_id():
    r_list = client.get("/api/alerts")
    first_alert = r_list.json()["alerts"][0]
    alert_id = first_alert["alert_id"]
    r = client.get(f"/api/alerts/{alert_id}")
    assert r.status_code == 200
    assert r.json()["alert_id"] == alert_id


def test_get_alert_404():
    r = client.get("/api/alerts/does-not-exist")
    assert r.status_code == 404


def test_list_clusters():
    r = client.get("/api/clusters")
    assert r.status_code == 200
    assert len(r.json()["clusters"]) >= 1


def test_graph_real_node():
    r = client.get("/api/graph/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa")
    assert r.status_code == 200
    body = r.json()
    assert len(body["nodes"]) >= 1


def test_graph_unknown_node_fallback():
    r = client.get("/api/graph/nonexistent-node")
    assert r.status_code == 200
    assert body_has_fallback_shape(r.json())


def body_has_fallback_shape(body):
    return "nodes" in body and "edges" in body


def test_live_feed():
    r = client.get("/api/live-feed")
    assert r.status_code == 200
    assert "events" in r.json()


def test_ingest_and_job_status():
    r = client.post("/api/ingest")
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    r2 = client.get(f"/api/jobs/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["status"] in ["running", "completed"]
