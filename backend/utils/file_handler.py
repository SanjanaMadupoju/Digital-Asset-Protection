import os
import aiofiles
from fastapi import UploadFile
from firebase_admin import storage

# UPLOAD_DIR = "uploads"

# Only these video formats are accepted
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# Max file size = 500MB (safety guard for your laptop)
MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024


def validate_video(file: UploadFile) -> tuple[bool, str]:
    """
    Two checks:
    1. File has a name
    2. Extension is in the allowed list
    Returns (True, "") if valid, (False, "reason") if not.
    """
    if not file.filename:
        return False, "No filename was provided."

    extension = os.path.splitext(file.filename)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        return False, f"File type '{extension}' is not supported. Allowed types: {allowed}"

    return True, ""


async def save_video(file: UploadFile, video_id: str) -> str:
    """
    Saves the video file to the uploads/ folder.

    Filename format on disk:  {video_id}.{ext}
    Example:                  a3f1c2d4-....mp4

    We read and write in 1MB chunks so large files don't eat your laptop RAM.
    Returns the path where the file was saved.
    """
    extension = os.path.splitext(file.filename)[-1].lower()
    filename = f"{video_id}{extension}"
    # full_path = os.path.join(UPLOAD_DIR, filename)

    chunk_size = 1024 * 1024  # 1 MB per chunk

    chunks = []

    # async with aiofiles.open(full_path, "wb") as output_file:
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        # await output_file.write(chunk)
        chunks.append(chunk)
    
    video_bytes = b"".join(chunks)

    # Upload to Firebase Storage
    storage_url = None
    try:
        bucket = storage.bucket("sports-fingerprint-backend.firebasestorage.app")
        blob = bucket.blob(f"uploads/{filename}")
        blob.upload_from_string(video_bytes, content_type=file.content_type or "video/mp4")
        blob.make_public()
        storage_url = blob.public_url
        print(f"[Storage] Uploaded: {storage_url}")
    except Exception as e:
        print(f"[Storage] Upload warning: {e}")

    return storage_url