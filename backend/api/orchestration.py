from fastapi import APIRouter

from agents.orchestration_agent import run_daily_orchestration
from observability.arize_ax_setup import force_flush_traces
from services.bigquery_service import save_orchestration_run

router = APIRouter()


@router.get("/orchestration/daily")
def get_daily_orchestration():
    return run_daily_orchestration()


@router.post("/orchestration/daily-run")
def run_scheduled_daily_orchestration():
    run = run_daily_orchestration()
    run["trigger_source"] = "cloud_scheduler"
    run["run_id"] = save_orchestration_run(run)
    force_flush_traces()
    return run
