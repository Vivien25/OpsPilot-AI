from fastapi import APIRouter

from agents.orchestration_agent import run_daily_orchestration

router = APIRouter()


@router.get("/orchestration/daily")
def get_daily_orchestration():
    return run_daily_orchestration()
