"""
storage.py — Firebase Cloud Storage helper.
Uploads watermarked video bytes and returns a public URL.
"""

from firebase_admin import storage
import os


def upload_watermarked_video(video_bytes: bytes, video_id: str) -> str:
    """
    Uploads watermarked video to Firebase Cloud Storage.
    Returns public download URL.
    """
    bucket_name = os.getenv(
        "FIREBASE_STORAGE_BUCKET",
        "sports-fingerprint-backend.firebasestorage.app"
    )
    bucket    = storage.bucket(bucket_name)
    blob_path = f"watermarked/{video_id}.mp4"
    blob      = bucket.blob(blob_path)

    blob.upload_from_string(video_bytes, content_type="video/mp4",timeout=300)
    blob.make_public()

    url = blob.public_url
    print(f"[Storage] Uploaded: {url}")
    return url


def get_watermarked_video_url(video_id: str) -> str | None:
    """Checks if watermarked video exists and returns its URL."""
    try:
        bucket_name = os.getenv(
            "FIREBASE_STORAGE_BUCKET",
            "sports-fingerprint-backend.firebasestorage.app"
        )
        bucket = storage.bucket(bucket_name)
        blob   = bucket.blob(f"watermarked/{video_id}.mp4")
        if blob.exists():
            blob.make_public()
            return blob.public_url
    except Exception as e:
        print(f"[Storage] Error: {e}")
    return None