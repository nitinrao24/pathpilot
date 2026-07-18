"""graph_utils.py — Dijkstra routing with congestion hook"""
import pickle, math
from pathlib import Path
from typing import Optional
import networkx as nx

_GRAPH_PATH = Path(__file__).parent / "campus_graph.pkl"

def _load_graph():
    with open(_GRAPH_PATH,"rb") as f: return pickle.load(f)

G = _load_graph()

def shortest_path(source, target, congestion_weights=None):
    _validate_nodes(source,target)
    working = _apply_congestion(G, congestion_weights)
    try:
        path = nx.dijkstra_path(working,source,target,weight="weight")
        distance = nx.dijkstra_path_length(working,source,target,weight="weight")
    except nx.NetworkXNoPath:
        raise ValueError(f"No path found between {source!r} and {target!r}")
    return _build_result(path, distance, bool(congestion_weights))

def get_alternate_path(source, target, primary_path, congestion_weights=None):
    _validate_nodes(source,target)
    working = _apply_congestion(G, congestion_weights)
    penalized = working.copy()
    for u,v in zip(primary_path[:-1],primary_path[1:]):
        if penalized.has_edge(u,v): penalized[u][v]["weight"] += 10_000
    try:
        path = nx.dijkstra_path(penalized,source,target,weight="weight")
        distance = sum(G[u][v]["weight"] for u,v in zip(path[:-1],path[1:]))
    except nx.NetworkXNoPath:
        return None
    return None if path==primary_path else _build_result(path,distance,bool(congestion_weights))

def path_to_geojson(r):
    return {"type":"Feature","geometry":{"type":"LineString",
        "coordinates":[[lng,lat] for lat,lng in r["coordinates"]]},
        "properties":{k:r[k] for k in ["distance_m","walk_min","hops","path","names"]}}

def list_buildings():
    return sorted([{"id":n,"name":d["name"],"lat":d["lat"],"lng":d["lng"],
                    "type":d["type"],"area":d["area"],"abbr":d["abbr"]}
                   for n,d in G.nodes(data=True)], key=lambda b:b["name"])

def _validate_nodes(source,target):
    for nid,label in [(source,"source"),(target,"target")]:
        if nid not in G: raise ValueError(f"Unknown {label} building {nid!r}")
    if source==target: raise ValueError("source and target must be different buildings")

def _apply_congestion(graph, cw):
    if not cw: return graph
    working = graph.copy()
    for (u,v),pen in cw.items():
        if working.has_edge(u,v) and pen>0: working[u][v]["weight"]+=pen
    return working

def _walk_minutes(d): return max(1,round(d/80))

def _build_result(path,distance,cong):
    return {"path":path,"names":[G.nodes[n]["name"] for n in path],
            "coordinates":[[G.nodes[n]["lat"],G.nodes[n]["lng"]] for n in path],
            "distance_m":round(distance),"walk_min":_walk_minutes(distance),
            "hops":len(path)-1,"congestion_applied":cong}

def path_summary(r):
    return " -> ".join(r["names"]) + f"  {r['distance_m']}m ~{r['walk_min']}min"
