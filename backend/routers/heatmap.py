from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from graph_utils import G
from predict import predict_all_buildings, predict_heatmap, current_hour_dow
from models.db import RouteQuery, get_db

router = APIRouter(prefix="/heatmap", tags=["heatmap"])
_heatmap_cache: dict[int,dict] = {}

def warm_cache():
    import time
    print("[cache] Pre-computing heatmap for all 7 days...")
    t0=time.time()
    for dow in range(7): _heatmap_cache[dow]=predict_heatmap(dow,G)
    print(f"[cache] Heatmap cache ready in {round(time.time()-t0,1)}s")

class BuildingCongestion(BaseModel):
    building_id:str; name:str; lat:float; lng:float
    label:str; level:int; penalty_m:int; probability:list[float]

class HeatmapResponse(BaseModel):
    hour:float; dow:int; buildings:list[BuildingCongestion]

class StatsResponse(BaseModel):
    total_queries:int; unique_sources:int; unique_targets:int
    most_common_src:str|None; most_common_tgt:str|None; congestion_used_pct:float

@router.get("", response_model=HeatmapResponse)
def get_heatmap(hour:float|None=Query(None), dow:int|None=Query(None)):
    now_hour,now_dow=current_hour_dow()
    h=hour if hour is not None else now_hour
    d=dow  if dow  is not None else now_dow
    return HeatmapResponse(hour=round(h,2),dow=d,buildings=predict_all_buildings(h,d,G))

@router.get("/full")
def get_full_heatmap(dow:int=Query(1)):
    if dow in _heatmap_cache: return _heatmap_cache[dow]
    result=predict_heatmap(dow,G); _heatmap_cache[dow]=result; return result

@router.get("/stats", response_model=StatsResponse)
def get_stats(db:Session=Depends(get_db)):
    total=db.query(func.count(RouteQuery.id)).scalar() or 0
    unique_src=db.query(func.count(func.distinct(RouteQuery.source_id))).scalar() or 0
    unique_tgt=db.query(func.count(func.distinct(RouteQuery.target_id))).scalar() or 0
    src_row=(db.query(RouteQuery.source_name,func.count(RouteQuery.id).label("n"))
             .group_by(RouteQuery.source_name).order_by(func.count(RouteQuery.id).desc()).first())
    tgt_row=(db.query(RouteQuery.target_name,func.count(RouteQuery.id).label("n"))
             .group_by(RouteQuery.target_name).order_by(func.count(RouteQuery.id).desc()).first())
    cong_used=db.query(func.count(RouteQuery.id)).filter(RouteQuery.congestion_used==True).scalar() or 0
    cong_pct=round(cong_used/total*100,1) if total>0 else 0.0
    return StatsResponse(total_queries=total,unique_sources=unique_src,unique_targets=unique_tgt,
        most_common_src=src_row[0] if src_row else None,
        most_common_tgt=tgt_row[0] if tgt_row else None,congestion_used_pct=cong_pct)
