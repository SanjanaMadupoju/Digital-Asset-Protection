"""
fingerprint.py — FastAPI router for Step 2.

Pipeline order:
  1. Find uploaded video by video_id
  2. Extract frames every 2 seconds (OpenCV)
  3. Embed invisible DCT watermark (org pattern + video_id) into each frame
  4. Run each watermarked frame through CLIP ViT-B/32
  5. Mean-pool all embeddings -> one 512-dim fingerprint
  6. Save to MongoDB local
  7. Save to Qdrant cloud
"""

from fastapi import APIRouter, HTTPException
from utils.frame_extractor import extract_and_watermark_frames
from utils.clip_embedder import frames_to_fingerprint
from utils.db import videos_col, fingerprints_col, qdrant_client, COLLECTION_NAME
from qdrant_client.models import PointStruct
import os, uuid, datetime

router = APIRouter()
UPLOAD_DIR = "uploads"


def _find_video_file(video_id: str) -> str:
    for filename in os.listdir(UPLOAD_DIR):
        if filename.startswith(video_id):
            return os.path.join(UPLOAD_DIR, filename)
    raise HTTPException(
        status_code=404,
        detail=f"No video found for video_id: {video_id}. Complete Step 1 first."
    )


@router.post("/fingerprint/{video_id}")
async def generate_fingerprint(video_id: str):
    """
    Triggers the full Step 2 pipeline.
    Runs on CPU — expect 30-120 seconds for a short video.
    """

    # 1. Find the video
    video_path = _find_video_file(video_id)
    print(f"\n[Step2] Pipeline started for: {video_id}")
    #   Returns (full_res_frames, clip_frames)

    # 2+3. Extract frames and embed watermark
    output_path = None
    try:
        frames, output_path = extract_and_watermark_frames(video_path, video_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Frame extraction failed: {str(e)}")

    if not frames:
        raise HTTPException(status_code=422, detail="No frames extracted. Video may be corrupt.")

    # 4+5. CLIP embedding + mean pool
    try:
        fingerprint_vector = frames_to_fingerprint(frames)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLIP embedding failed: {str(e)}")

    if fingerprint_vector is None:
        raise HTTPException(status_code=500, detail="Fingerprint returned empty.")

    if(output_path==None):
        output_path = video_path
    
    print(f"storing {output_path} video to mongo")
     
    # 6. Save to MongoDB
    timestamp = datetime.datetime.utcnow().isoformat()
    mongo_doc = {
        "video_id":    video_id,
        "video_path":  output_path,
        "fingerprint": fingerprint_vector,
        "n_frames":    len(frames),
        "vector_dim":  len(fingerprint_vector),
        "watermarked": True,
        "created_at":  timestamp,
    }
    try:
        fingerprints_col.replace_one({"video_id": video_id}, mongo_doc, upsert=True)
        videos_col.update_one(
            {"video_id": video_id},
            {"$set": {"status": "fingerprinted", "fingerprinted_at": timestamp}},
            upsert=True
        )
        print(f"[MongoDB] Saved fingerprint for: {video_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MongoDB save failed: {str(e)}")

    # 7. Save to Qdrant cloud
    try:
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=fingerprint_vector,
                payload={"video_id": video_id, "video_path": video_path,
                         "created_at": timestamp, "source": "original"}
            )]
        )
        print(f"[Qdrant] Vector saved for: {video_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qdrant save failed: {str(e)}")

    return {
        "success":             True,
        "video_id":            video_id,
        "frames_processed":    len(frames),
        "vector_dimensions":   len(fingerprint_vector),
        "watermarked":         True,
        "saved_to":            ["MongoDB (local)", "Qdrant (cloud)"],
        "fingerprint_preview": fingerprint_vector[:5],
        "next_step":           "Proceed to Step 3 — web scraper"
    }


@router.get("/fingerprint/{video_id}")
def get_fingerprint(video_id: str):
    """Check if a fingerprint exists for a given video_id."""
    doc = fingerprints_col.find_one({"video_id": video_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"No fingerprint for: {video_id}")
    doc["fingerprint"] = doc["fingerprint"][:5]
    doc["note"] = "Showing first 5 of 512 values."
    return doc
