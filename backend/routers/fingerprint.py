"""
fingerprint.py — Step 2 router. Saves fingerprint to Firestore + Qdrant.
"""

from fastapi import APIRouter, HTTPException
from utils.frame_extractor import extract_and_watermark_frames
from utils.clip_embedder import frames_to_fingerprint
from utils.firebase_init import set_fingerprint, set_video, get_fingerprint, fingerprints_ref
from utils.db import qdrant_client, COLLECTION_NAME
from qdrant_client.models import PointStruct
import os, uuid, datetime

router = APIRouter()
# UPLOAD_DIR = "uploads"


# def _find_video_file(video_id: str) -> str:
#     for f in os.listdir(UPLOAD_DIR):
#         if f.startswith(video_id):
#             return os.path.join(UPLOAD_DIR, f)
#     raise HTTPException(status_code=404, detail=f"No video file for: {video_id}")


import tempfile
import requests
from utils.firebase_init import get_video

def _find_video_file(video_id: str) -> str:
    # Get storage URL from Firestore
    doc = get_video(video_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"No video found for: {video_id}")
    
    storage_url = doc.get("saved_path")
    if not storage_url:
        raise HTTPException(status_code=404, detail=f"No storage URL for: {video_id}")

    # Download to temp file for processing
    response = requests.get(storage_url, stream=True)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail=f"Could not download video: {storage_url}")

    ext = ".mp4"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        tmp.write(chunk)
    tmp.close()

    print(f"[Step2] Downloaded video to temp: {tmp.name}")
    return tmp.name


@router.post("/fingerprint/{video_id}")
async def generate_fingerprint(video_id: str):
    video_path = _find_video_file(video_id)
    print(f"\n[Step2] Starting for: {video_id}")

    # try:
    #     _full_res_frames, clip_frames, output_path, storage_url  = extract_and_watermark_frames(video_path, video_id)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Frame extraction failed: {e}")

    try:
        _full_res_frames, clip_frames, storage_url = extract_and_watermark_frames(video_path, video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame extraction failed: {e}")
    finally:
        # ✅ Delete temp file after use
        if os.path.exists(video_path):
            os.remove(video_path)
            print(f"[Step2] Temp file deleted: {video_path}")

    if not clip_frames:
        raise HTTPException(status_code=422, detail="No frames extracted.")

    try:
        fingerprint_vector = frames_to_fingerprint(clip_frames)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLIP embedding failed: {e}")

    if not fingerprint_vector:
        raise HTTPException(status_code=500, detail="Empty fingerprint.")
    
    # if not output_path:
    #     output_path = video_path

    print(f"storing {storage_url} video to firebase")

    timestamp = datetime.datetime.utcnow().isoformat()

    # ── Save to Firestore ──────────────────────────────────────────────────
    # Note: Firestore has a 1MB document limit
    # We store first 128 values as preview; full vector goes to Qdrant only
    set_fingerprint(video_id, {
        "video_id":           video_id,
        "video_path":         storage_url,
        "fingerprint_preview": fingerprint_vector[:128],  # partial for Firestore
        "n_frames":           len(clip_frames),
        "vector_dim":         len(fingerprint_vector),
        "watermarked":        True,
        "watermarked_video_url": storage_url,
        "created_at":         timestamp,
    })

    # Store full vector in a sub-collection to avoid doc size limit
    fingerprints_ref.document(video_id).collection("vectors").document("full").set({
        "fingerprint": fingerprint_vector,   # full 512 floats
        "created_at":  timestamp,
    })

    # Update video status
    set_video(video_id, {
        "status":          "fingerprinted",
        "fingerprinted":   True,
        "watermarked":     True,
        "watermarked_video_url": storage_url,
        "fingerprinted_at": timestamp,
    })

    print(f"[Firestore] Fingerprint saved for: {video_id}")

    # ── Save to Qdrant ─────────────────────────────────────────────────────
    try:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=fingerprint_vector,
                payload={
                    "video_id":   video_id,
                    "video_path": storage_url,
                    "created_at": timestamp,
                    "source":     "original",
                }
            )]
        )
        print(f"[Qdrant] Vector saved for: {video_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qdrant failed: {e}")

    return {
        "success":             True,
        "video_id":            video_id,
        "frames_processed":    len(clip_frames),
        "vector_dimensions":   len(fingerprint_vector),
        "watermarked":         True,
        "watermarked_video_url": storage_url,
        "saved_to":            ["Firestore", "Qdrant", "Firebase Storage"],
        "fingerprint_preview": fingerprint_vector[:5],
        "next_step":           "Step 3 — run the scraper"
    }


@router.get("/fingerprint/{video_id}")
def get_fingerprint_info(video_id: str):
    doc = get_fingerprint(video_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"No fingerprint for: {video_id}")
    doc.pop("fingerprint_preview", None)
    doc["note"] = "Full 512-dim vector stored in Firestore sub-collection + Qdrant."
    return doc