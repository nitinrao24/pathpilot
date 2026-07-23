from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.db import init_db
from routers import routes, buildings, heatmap

app = FastAPI(title="PathPilot API", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(routes.router)
app.include_router(buildings.router)
app.include_router(heatmap.router)

@app.on_event("startup")
def on_startup():
    init_db()
    from graph_utils import G
    from predict import _clf
    from routers.heatmap import warm_cache
    print(f"[startup] Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"[startup] Model: {_clf.n_estimators} trees, accuracy {_clf.score}")
    warm_cache()

@app.get("/", tags=["health"])
def root():
    from graph_utils import G
    from predict import _meta
    return {"status":"ok","service":"PathPilot API",
            "buildings":G.number_of_nodes(),"edges":G.number_of_edges(),
            "model_accuracy":f"{_meta['test_accuracy']*100:.1f}%"}
