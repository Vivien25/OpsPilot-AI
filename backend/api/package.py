from fastapi import APIRouter, File, HTTPException, UploadFile

from agents.package_recognition_agent import run_package_recognition

router = APIRouter()


@router.post("/package/recognize")
async def recognize_package(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are supported")

    image_bytes = await file.read()

    return run_package_recognition(
        image_bytes=image_bytes,
        mime_type=file.content_type,
    )
