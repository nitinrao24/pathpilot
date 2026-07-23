from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from graph_utils import G, list_buildings
from predict import predict_building, current_hour_dow

router = APIRouter(prefix="/buildings", tags=["buildings"])

class BuildingItem(BaseModel):
    id:str; name:str; lat:float; lng:float; type:str; area:str; abbr:str

class BuildingDetail(BuildingItem):
    congestion_label:str; congestion_level:int; congestion_penalty:int; probability:list[float]

@router.get("", response_model=list[BuildingItem])
def get_buildings(area:str|None=Query(None), type:str|None=Query(None)):
    b = list_buildings()
    if area: b=[x for x in b if x["area"]==area]
    if type: b=[x for x in b if x["type"]==type]
    return b

@router.get("/{building_id}", response_model=BuildingDetail)
def get_building(building_id:str, hour:float|None=Query(None), dow:int|None=Query(None)):
    if building_id not in G: raise HTTPException(status_code=404, detail=f"Building {building_id!r} not found")
    data = G.nodes[building_id]
    now_hour,now_dow = current_hour_dow()
    h = hour if hour is not None else now_hour
    d = dow  if dow  is not None else now_dow
    pred = predict_building(data["type"],data["area"],h,d)
    return BuildingDetail(id=building_id,name=data["name"],lat=data["lat"],lng=data["lng"],
        type=data["type"],area=data["area"],abbr=data["abbr"],
        congestion_label=pred["label"],congestion_level=pred["level"],
        congestion_penalty=pred["penalty_m"],probability=pred["probability"])
