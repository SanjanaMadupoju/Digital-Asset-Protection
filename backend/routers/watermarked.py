"""
watermarked.py — GET endpoint to retrieve watermarked video URL.
"""

from fastapi import APIRouter, HTTPException
from utils.firebase_init import fingerprints_ref
from utils.storage import get_watermarked_video_url

from fastapi.responses import StreamingResponse
from firebase_admin import storage

router = APIRouter()


@router.get("/watermarked/{video_id}")
def get_watermarked_video(video_id: str):
    """
    Returns the watermarked video URL stored in Firebase Storage.
    Frontend uses this to show the video player + download button.
    """
    # Check Firestore first
    doc = fingerprints_ref.document(video_id).get()
    if doc.exists:
        data = doc.to_dict()
        url  = data.get("watermarked_video_url")
        if url:
            return {
                "video_id":              video_id,
                "watermarked_video_url": url,
                "filename":             f"watermarked_{video_id}.mp4",
                "n_frames":             data.get("n_frames"),
                "created_at":           data.get("created_at"),
            }

    # Fallback: check Storage directly
    url = get_watermarked_video_url(video_id)
    if url:
        return {
            "video_id":              video_id,
            "watermarked_video_url": url,
            "filename":             f"watermarked_{video_id}.mp4",
        }

    raise HTTPException(
        status_code=404,
        detail=f"No watermarked video for: {video_id}. Run Step 2 first."
    )

    
@router.get("/download/{video_id}")
def download_video(video_id: str):
    bucket = storage.bucket("sports-fingerprint-backend.firebasestorage.app")
    blob = bucket.blob(f"watermarked/{video_id}.mp4")
    
    if not blob.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_bytes = blob.download_as_bytes()

    if not video_bytes:
        raise HTTPException(status_code=404, detail="Video file is empty")
    
    return StreamingResponse(
        iter([video_bytes]),
        media_type="video/mp4",
        headers={"Content-Disposition": f"attachment; filename=watermarked_{video_id}.mp4"}
    )