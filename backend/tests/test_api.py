from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json()["status"] == "ok"

def test_search_known():
    d = client.get("/api/stocks/search", params={"q": "ambuja"}).json()
    assert any(r["symbol"] == "AMBUJACEM.NS" for r in d["results"])

def test_search_unknown():
    d = client.get("/api/stocks/search", params={"q": "zzz-no-such-stock"}).json()
    assert isinstance(d["results"], list)
    for r in d["results"]:
        assert r["symbol"] and r["name"] and r["exchange"]

def test_search_includes_registry_hit():
    d = client.get("/api/stocks/search", params={"q": "ambuja"}).json()
    hit = next(r for r in d["results"] if r["symbol"] == "AMBUJACEM.NS")
    assert hit["name"] and hit["exchange"]

def test_unknown_analysis_404():
    assert client.get("/api/data/nope").status_code == 404

def test_analyze_rejects_reversed_dates():
    r = client.post("/api/analyze", json={"symbol": "AMBUJACEM.NS", "start": "2026-03-31", "end": "2025-04-01"})
    assert r.status_code == 422

def test_analyze_rejects_bad_date_format():
    r = client.post("/api/analyze", json={"symbol": "AMBUJACEM.NS", "start": "01-04-2025", "end": "2026-03-31"})
    assert r.status_code == 422
