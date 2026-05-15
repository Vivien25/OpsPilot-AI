from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.health import router as health_router
from api.incident_ticket import router as incident_ticket_router
from api.orchestration import router as orchestration_router
from api.package import router as package_router
from api.warehouse_map import router as warehouse_map_router

app = FastAPI(title="OpsPilot AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(incident_ticket_router, prefix="/api", tags=["incident-ticket"])
app.include_router(orchestration_router, prefix="/api", tags=["orchestration"])
app.include_router(package_router, prefix="/api", tags=["package-recognition"])
app.include_router(warehouse_map_router, prefix="/api", tags=["warehouse-map"])
