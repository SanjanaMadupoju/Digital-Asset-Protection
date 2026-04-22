"""
upload.py — Step 1 router. Saves video metadata to Firestore.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.file_handler import validate_video, save_video
from utils.firebase_init import set_video, get_video
import uuid
import datetime

router = APIRouter()


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    is_valid, error_msg = validate_video(file)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    video_id  = str(uuid.uuid4())
    file_path = await save_video(file, video_id)
    timestamp = datetime.datetime.utcnow().isoformat()
    
    # Save to Firestore
    set_video(video_id, {
        "video_id":    video_id,
        "filename":    file.filename,
        "saved_path":  file_path,
        "status":      "uploaded",
        "uploaded_at": timestamp,
        "fingerprinted": False,
        "watermarked":   False,
    })

    # print(f"[Firestore] Video metadata saved: {video_id}")

    return {
        "success":   True,
        "video_id":  video_id,
        "filename":  file.filename,
        "saved_path": file_path,
        "next_step": "Run POST /api/fingerprint/{video_id} (Step 2)"
    }


@router.get("/status/{video_id}")
def check_status(video_id: str):
    doc = get_video(video_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"No video found: {video_id}")
    return doc


@router.get("/videos")
def list_videos():
    from utils.firebase_init import videos_ref
    docs = [d.to_dict() for d in videos_ref.stream()]
    return {"total": len(docs), "videos": docs}