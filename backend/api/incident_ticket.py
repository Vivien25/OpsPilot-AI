from fastapi import APIRouter, File, HTTPException, UploadFile

from agents.incident_ticket_agent import run_incident_ticket

router = APIRouter()


@router.post("/incident-ticket/create")
async def create_incident_ticket(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    image_bytes = await file.read()

    return run_incident_ticket(
        image_bytes=image_bytes,
        mime_type=file.content_type,
    )
