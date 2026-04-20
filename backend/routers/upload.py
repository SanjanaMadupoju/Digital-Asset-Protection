# from fastapi import APIRouter, UploadFile, File, HTTPException
# from utils.file_handler import validate_video, save_video
# import uuid

# router = APIRouter()


# @router.post("/upload")
# async def upload_video(file: UploadFile = File(...)):
#     """
#     Receives a video file from the React frontend.
#     Validates it, saves it to disk, returns a unique video_id.

#     This video_id is used in ALL future steps:
#       - Step 2 uses it to find the file and generate the fingerprint
#       - Step 3 uses it as the key in Qdrant and MongoDB
#       - Step 5 and 6 use it to link matches back to the original
#     """

#     # 1. Check the file is a valid video format
#     is_valid, error_msg = validate_video(file)
#     if not is_valid:
#         raise HTTPException(status_code=400, detail=error_msg)

#     # 2. Generate a unique ID for this video (UUID4 = random, no collisions)
#     video_id = str(uuid.uuid4())

#     # 3. Save the file to the uploads/ folder
#     file_path = await save_video(file, video_id)

#     # 4. Return the video_id — the frontend will show this to the user
#     return {
#         "success": True,
#         "video_id": video_id,
#         "filename": file.filename,
#         "saved_path": file_path,
#         "next_step": "Use this video_id in Step 2 to generate the CLIP fingerprint"
#     }


# @router.get("/status/{video_id}")
# def check_status(video_id: str):
#     """
#     Check if a video exists on disk.
#     In later steps this will also return: fingerprinted, matched, flagged.
#     """
#     import os
#     all_files = os.listdir("uploads")
#     matches = [f for f in all_files if f.startswith(video_id)]

#     if not matches:
#         raise HTTPException(status_code=404, detail=f"No video found with id: {video_id}")

#     return {
#         "video_id": video_id,
#         "filename": matches[0],
#         "status": "uploaded",
#         "fingerprinted": False,   # Will be True after Step 2
#         "matched": False           # Will be True after Step 5
#     }


# @router.get("/videos")
# def list_videos():
#     """
#     List all uploaded videos.
#     Useful to confirm your upload worked before moving to Step 2.
#     """
#     import os
#     files = os.listdir("uploads")
#     return {
#         "total": len(files),
#         "videos": files
#     } 

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