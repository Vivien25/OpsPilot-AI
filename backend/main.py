from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.orchestration import router as orchestration_router
from api.warehouse_map import router as warehouse_map_router
from observability.phoenix_setup import instrument_fastapi, setup_phoenix

setup_phoenix()
app = FastAPI(title="OpsPilot AI")
instrument_fastapi(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(orchestration_router, prefix="/api", tags=["orchestration"])
app.include_router(warehouse_map_router, prefix="/api", tags=["warehouse-map"])
