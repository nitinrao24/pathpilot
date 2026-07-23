import time
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from graph_utils import G, shortest_path, path_to_geojson
from predict import get_route_penalties, current_hour_dow
from models.db import RouteQuery, get_db

router = APIRouter(prefix="/route", tags=["routing"])

class RouteResponse(BaseModel):
    source:str; target:str; path:list[str]; names:list[str]
    coordinates:list[list[float]]; distance_m:int; walk_min:int
    hops:int; congestion_applied:bool; geojson:dict; response_ms:float

class CompareResponse(BaseModel):
    source:str; target:str; fast:dict; smart:dict; saved_m:int; response_ms:float

@router.get("", response_model=RouteResponse)
def get_route(source:str=Query(...), target:str=Query(...),
              avoid_congestion:bool=Query(True),
              hour:float|None=Query(None), dow:int|None=Query(None),
              db:Session=Depends(get_db)):
    t0=time.perf_counter()
    if source not in G: raise HTTPException(404,f"Building {source!r} not found")
    if target not in G: raise HTTPException(404,f"Building {target!r} not found")
    if source==target:  raise HTTPException(400,"source and target must be different")
    now_hour,now_dow=current_hour_dow()
    h=hour if hour is not None else now_hour
    d=dow  if dow  is not None else now_dow
    penalties=None
    if avoid_congestion:
        base=shortest_path(source,target)
        penalties=get_route_penalties(base["path"],h,d,G)
    result=shortest_path(source,target,congestion_weights=penalties)
    db.add(RouteQuery(source_id=source,source_name=result["names"][0],
        target_id=target,target_name=result["names"][-1],
        distance_m=result["distance_m"],walk_min=result["walk_min"],
        hops=result["hops"],congestion_used=bool(penalties),hour=round(h,2),dow=d))
    db.commit()
    ms=round((time.perf_counter()-t0)*1000,1)
    return RouteResponse(source=source,target=target,geojson=path_to_geojson(result),
        response_ms=ms,**{k:result[k] for k in ["path","names","coordinates","distance_m","walk_min","hops","congestion_applied"]})

@router.get("/compare", response_model=CompareResponse)
def compare_routes(source:str=Query(...), target:str=Query(...),
                   hour:float|None=Query(None), dow:int|None=Query(None)):
    t0=time.perf_counter()
    if source not in G: raise HTTPException(404,f"Building {source!r} not found")
    if target not in G: raise HTTPException(404,f"Building {target!r} not found")
    if source==target:  raise HTTPException(400,"source and target must be different")
    now_hour,now_dow=current_hour_dow()
    h=hour if hour is not None else now_hour
    d=dow  if dow  is not None else now_dow
    fast=shortest_path(source,target)
    penalties=get_route_penalties(fast["path"],h,d,G)
    smart=shortest_path(source,target,congestion_weights=penalties)
    ms=round((time.perf_counter()-t0)*1000,1)
    return CompareResponse(source=source,target=target,
        fast={**fast,"geojson":path_to_geojson(fast)},
        smart={**smart,"geojson":path_to_geojson(smart)},
        saved_m=fast["distance_m"]-smart["distance_m"],response_ms=ms)
