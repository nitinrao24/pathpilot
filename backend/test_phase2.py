"""Phase 2 tests — pytest test_phase2.py -v"""
import pytest, joblib, numpy as np
from pathlib import Path
from graph_utils import G, shortest_path
from predict import (_clf,_meta,FEATURE_COLS,LABEL_NAMES,CONGESTION_PENALTY,
                     predict_building,get_route_penalties,predict_all_buildings,
                     _build_feature_vector,current_hour_dow)

class TestModelFile:
    def test_exists(self): assert Path("congestion_model.pkl").exists()
    def test_accuracy_above_target(self): assert _meta["test_accuracy"]>=0.78
    def test_label_names(self): assert _meta["label_names"]==["low","medium","high"]
    def test_estimator_count(self): assert _clf.n_estimators>=200

class TestFeatureVector:
    def test_correct_length(self): assert len(_build_feature_vector("lecture",10.0,1,"central"))==len(FEATURE_COLS)
    def test_no_nan(self):
        for bt in ["lecture","lab","library","cafe","gym","landmark"]:
            assert not np.isnan(_build_feature_vector(bt,12.0,1,"central")).any()
    def test_weekend_flag(self):
        wd=dict(zip(FEATURE_COLS,_build_feature_vector("lab",10.0,2,"central")))
        we=dict(zip(FEATURE_COLS,_build_feature_vector("lab",10.0,5,"central")))
        assert wd["is_weekend"]==0; assert we["is_weekend"]==1
    def test_type_ohe(self):
        for bt in ["lecture","lab","library","cafe","gym","landmark"]:
            f=dict(zip(FEATURE_COLS,_build_feature_vector(bt,10.0,1,"central")))
            assert sum(v for k,v in f.items() if k.startswith("type_"))==1

class TestPredictBuilding:
    def test_required_keys(self):
        assert set(predict_building("lecture","central",10.0,1).keys())=={"label","level","penalty_m","probability"}
    def test_label_valid(self): assert predict_building("lab","engineering",14.0,2)["label"] in LABEL_NAMES
    def test_probability_sums_to_one(self): assert abs(sum(predict_building("gym","south",17.0,2)["probability"])-1.0)<1e-3
    def test_penalty_matches_level(self):
        r=predict_building("cafe","south",12.0,1); assert r["penalty_m"]==CONGESTION_PENALTY[r["level"]]

class TestPredictSanity:
    def test_lecture_tuesday_10am_high(self): assert predict_building("lecture","central",10.0,1)["label"]=="high"
    def test_lecture_sunday_7am_low(self): assert predict_building("lecture","central",7.0,6)["label"]=="low"
    def test_weekday_busier_than_weekend(self):
        wd=predict_building("lecture","central",10.0,1)
        we=predict_building("lecture","central",10.0,6)
        assert wd["level"]>=we["level"]

class TestGetRoutePenalties:
    def test_returns_dict(self):
        r=shortest_path("soda_hall","doe_library")
        assert isinstance(get_route_penalties(r["path"],10.0,1,G),dict)
    def test_all_non_negative(self):
        r=shortest_path("soda_hall","sproul_hall")
        assert all(v>=0 for v in get_route_penalties(r["path"],10.0,1,G).values())
    def test_graph_not_mutated(self):
        w=G["soda_hall"]["birge_hall"]["weight"]
        r=shortest_path("soda_hall","doe_library")
        get_route_penalties(r["path"],10.0,1,G)
        assert G["soda_hall"]["birge_hall"]["weight"]==w

class TestPhase1And2Integration:
    def test_congestion_aware_route_valid(self):
        base=shortest_path("soda_hall","sproul_hall")
        p=get_route_penalties(base["path"],10.0,1,G)
        aware=shortest_path("soda_hall","sproul_hall",congestion_weights=p)
        assert aware["path"][0]=="soda_hall"; assert aware["path"][-1]=="sproul_hall"
    def test_current_hour_dow_valid(self):
        h,d=current_hour_dow(); assert 0.0<=h<24.0; assert 0<=d<=6
