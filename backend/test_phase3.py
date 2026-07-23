"""Phase 3 tests — pytest test_phase3.py -v"""
import pytest
from fastapi.testclient import TestClient
from main import app
client = TestClient(app)

class TestHealthCheck:
    def test_returns_200(self): assert client.get("/").status_code==200
    def test_has_fields(self):
        r=client.get("/").json(); assert r["status"]=="ok"; assert r["buildings"]==56
    def test_accuracy_above_target(self):
        assert float(client.get("/").json()["model_accuracy"].replace("%",""))>=78.0

class TestBuildingsList:
    def test_returns_200(self): assert client.get("/buildings").status_code==200
    def test_returns_all(self): assert len(client.get("/buildings").json())==56
    def test_sorted(self):
        r=client.get("/buildings").json(); assert [b["name"] for b in r]==sorted(b["name"] for b in r)
    def test_filter_area(self):
        r=client.get("/buildings?area=engineering").json()
        assert len(r)>0; assert all(b["area"]=="engineering" for b in r)
    def test_unknown_area_empty(self): assert client.get("/buildings?area=mars").json()==[]

class TestBuildingDetail:
    def test_known_200(self): assert client.get("/buildings/doe_library").status_code==200
    def test_unknown_404(self): assert client.get("/buildings/fake").status_code==404
    def test_sunday_7am_low(self): assert client.get("/buildings/wheeler_hall?hour=7&dow=6").json()["congestion_label"]=="low"
    def test_probability_sums(self): assert abs(sum(client.get("/buildings/soda_hall").json()["probability"])-1.0)<1e-3

class TestRoute:
    def test_returns_200(self): assert client.get("/route?source=soda_hall&target=doe_library").status_code==200
    def test_missing_source_422(self): assert client.get("/route?target=doe_library").status_code==422
    def test_unknown_source_404(self): assert client.get("/route?source=fake&target=doe_library").status_code==404
    def test_same_source_target_400(self): assert client.get("/route?source=soda_hall&target=soda_hall").status_code==400
    def test_path_correct(self):
        r=client.get("/route?source=soda_hall&target=sproul_hall").json()
        assert r["path"][0]=="soda_hall"; assert r["path"][-1]=="sproul_hall"
    def test_geojson_valid(self):
        r=client.get("/route?source=soda_hall&target=doe_library").json()
        assert r["geojson"]["type"]=="Feature"; assert r["geojson"]["geometry"]["type"]=="LineString"
    def test_congestion_true_default(self):
        r=client.get("/route?source=soda_hall&target=sproul_hall&hour=10&dow=1").json()
        assert r["congestion_applied"] is True

class TestRouteCompare:
    def test_returns_200(self): assert client.get("/route/compare?source=soda_hall&target=sproul_hall").status_code==200
    def test_has_fields(self):
        r=client.get("/route/compare?source=soda_hall&target=sproul_hall").json()
        assert {"source","target","fast","smart","saved_m","response_ms"}.issubset(r.keys())
    def test_peak_routes_differ(self):
        r=client.get("/route/compare?source=soda_hall&target=sproul_hall&hour=10&dow=1").json()
        assert r["fast"]["path"]!=r["smart"]["path"]

class TestHeatmap:
    def test_returns_200(self): assert client.get("/heatmap").status_code==200
    def test_returns_all_buildings(self): assert len(client.get("/heatmap").json()["buildings"])==56
    def test_stats_increments(self):
        before=client.get("/heatmap/stats").json()["total_queries"]
        client.get("/route?source=soda_hall&target=doe_library")
        after=client.get("/heatmap/stats").json()["total_queries"]
        assert after==before+1
