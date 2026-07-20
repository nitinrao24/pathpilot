"""predict.py — ML congestion predictions for PathPilot"""
import math, joblib
import numpy as np
from datetime import datetime
from pathlib import Path

_MODEL_PATH = Path(__file__).parent / "congestion_model.pkl"
_payload = joblib.load(_MODEL_PATH)
_clf = _payload["model"]
_meta = _payload["metadata"]
LABEL_NAMES = _meta["label_names"]
FEATURE_COLS = _meta["feature_cols"]

CONGESTION_PENALTY = {0: 0, 1: 120, 2: 320}

_CLASS_SLOTS = [(8,1.0),(9,1.5),(10,1.0),(11,1.5),(12,1.0),(13,1.5),
                (14,1.0),(15,1.5),(16,1.0),(17,1.5),(18,1.5)]

def _mins_until(h):
    for s,d in _CLASS_SLOTS:
        if s<=h<s+d: return 0.0
        if s>h: return (s-h)*60
    return 999.0

def _mins_since(h):
    e=999.0
    for s,d in _CLASS_SLOTS:
        end=s+d
        if end<=h: e=min(e,(h-end)*60)
    return e

def _in_class(h):
    for s,d in _CLASS_SLOTS:
        if s<=h<s+d: return True
    return False

def _soon(h): return int(0<_mins_until(h)<=15)

def _build_feature_vector(btype, hour, dow, area):
    hs=math.sin(2*math.pi*hour/24); hc=math.cos(2*math.pi*hour/24)
    types=["lecture","lab","library","cafe","gym","landmark"]
    areas=["engineering","chemistry","bioscience","central","south","northside","east"]
    fm={"hour":hour,"hour_sin":hs,"hour_cos":hc,"dow":dow,"is_weekend":int(dow>=5),
        "mins_to_class":min(_mins_until(hour),120),"mins_since_class":min(_mins_since(hour),120),
        "in_class_now":int(_in_class(hour)),"class_soon":_soon(hour),
        **{f"type_{t}":int(btype==t) for t in types},
        **{f"area_{a}":int(area==a) for a in areas}}
    return np.array([fm[c] for c in FEATURE_COLS], dtype=float)

def predict_building(btype, area, hour, dow):
    features = _build_feature_vector(btype, hour, dow, area)
    level = int(_clf.predict([features])[0])
    proba = _clf.predict_proba([features])[0].tolist()
    return {"label":LABEL_NAMES[level],"level":level,
            "penalty_m":CONGESTION_PENALTY[level],"probability":[round(p,3) for p in proba]}

def get_route_penalties(path, hour, dow, graph, lookahead_min=30):
    future_hour = min(hour + lookahead_min/60, 23.0)
    penalties = {}
    for u,v in zip(path[:-1],path[1:]):
        d = graph.nodes[v]
        pred = predict_building(d["type"],d["area"],future_hour,dow)
        if pred["penalty_m"]>0: penalties[(u,v)] = pred["penalty_m"]
    return penalties

def predict_all_buildings(hour, dow, graph):
    results = []
    for nid,data in graph.nodes(data=True):
        pred = predict_building(data["type"],data["area"],hour,dow)
        results.append({"building_id":nid,"name":data["name"],"lat":data["lat"],
                         "lng":data["lng"],**pred})
    return sorted(results, key=lambda x:x["name"])

def predict_heatmap(dow, graph):
    hour_slots = list(range(7,24))
    nodes = list(graph.nodes(data=True))
    rows = []
    for nid,data in nodes:
        for hour in hour_slots:
            rows.append(_build_feature_vector(data["type"],float(hour),dow,data["area"]))
    X = np.array(rows)
    levels = _clf.predict(X).astype(int)
    heatmap = {}
    idx = 0
    for nid,data in nodes:
        hours = []
        for hour in hour_slots:
            level = int(levels[idx])
            hours.append({"hour":float(hour),"label":LABEL_NAMES[level],"level":level})
            idx += 1
        heatmap[nid] = {"name":data["name"],"lat":data["lat"],"lng":data["lng"],"hours":hours}
    return heatmap

def current_hour_dow():
    now = datetime.now()
    return now.hour + now.minute/60, now.weekday()
