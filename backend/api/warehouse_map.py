from fastapi import APIRouter

from agents.map_agent import generate_warehouse_map

router = APIRouter()


@router.get("/map")
def get_warehouse_map():
    return generate_warehouse_map()
