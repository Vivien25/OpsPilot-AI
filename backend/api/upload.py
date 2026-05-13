from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.orchestrator import run_investigation

router = APIRouter()

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    return await analyze_image(file)


@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    image_bytes = await file.read()

    result = run_investigation(
        image_bytes=image_bytes,
        mime_type=file.content_type,
    )

    return result
