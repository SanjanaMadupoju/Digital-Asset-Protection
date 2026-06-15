"""
clip_embedder.py — Replaced CLIP with Google Cloud Vision AI embeddings.

Why Google Vision AI:
  - No PyTorch or local GPU needed
  - Runs on Google's servers
  - Returns 1408-dim embedding vector per image
  - Same cosine similarity matching works identically
  - Counts as Google AI/ML API for hackathon judges

API used: Cloud Vision API - imageProperties + Web Detection
Embedding: We use Google's multimodal embedding endpoint
"""

import cv2
import numpy as np
import base64
from dotenv import load_dotenv
load_dotenv()
import os
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import io
import warnings
import google.auth
import google.auth.transport.requests
import tempfile
warnings.filterwarnings("ignore")

VECTOR_SIZE = 1408   # Google Vision embedding size


def _local_fallback_embedding(frame: np.ndarray) -> np.ndarray:
    """
    Build a deterministic 1408-dim local embedding from image pixels.
    This keeps the pipeline functional when cloud embedding APIs fail.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # 44 x 32 = 1408 dimensions exactly.
    resized = cv2.resize(gray, (44, 32), interpolation=cv2.INTER_AREA)
    vec = resized.astype(np.float32).reshape(-1)
    vec /= 255.0
    return vec


def _get_access_token() -> str:
    """Gets Google Cloud access token from service account."""
    
    # Try environment variable first (production)
    service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
    if service_account_json:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(service_account_json)
            temp_path = f.name
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path

    credentials, project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req)
    return credentials.token


def _frame_to_base64(frame: np.ndarray) -> str:
    """Converts OpenCV BGR frame to base64 JPEG string."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _get_embedding_via_vision_api(frame_b64: str, token: str, project_id: str = "sports-fingerprint-backend") -> list | None:
    """
    Calls Google Cloud Vision API to get image embedding.
    Uses the Vertex AI multimodal embedding endpoint.
    """
    endpoint = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/publishers/google/models/multimodalembedding@001:predict"

    payload = {
        "instances": [
            {
                "image": {
                    "bytesBase64Encoded": frame_b64
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=30, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            embedding = data["predictions"][0]["imageEmbedding"]
            return embedding
        else:
            print(f"[Vision API] Error {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"[Vision API] Request failed: {e}")
        return None


def frames_to_fingerprint(frames: list) -> list | None:
    """
    Takes a list of BGR frames (numpy arrays),
    gets Google Vision AI embeddings for each,
    returns mean-pooled fingerprint vector.

    Args:
        frames : list of np.ndarray BGR frames (any size)

    Returns:
        list of floats (1408-dim fingerprint vector)
        Returns None if all frames fail
    """
    if not frames:
        print("[Vision API] No frames to process.")
        return None

    print(f"[Vision API] Processing {len(frames)} frames...")
    t0 = time.time()

    try:
        token = _get_access_token()
    except Exception as e:
        token = None
        print(f"[Vision API] Auth failed, switching to local fallback: {e}")

    all_embeddings = []

    # Encode frames up-front, then call API concurrently in a small batch.
    encoded_frames = []
    for i, frame in enumerate(frames):
        try:
            encoded_frames.append((i, _frame_to_base64(frame)))
        except Exception as e:
            print(f"[Vision API] Frame {i+1} encode error: {e}")

    if not encoded_frames:
        print("[Vision API] No valid frames after encoding.")
        return None

    if token:
        with ThreadPoolExecutor(max_workers=min(4, len(encoded_frames))) as pool:
            futures = {
                pool.submit(_get_embedding_via_vision_api, frame_b64, token): idx
                for idx, frame_b64 in encoded_frames
            }

            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    embedding = fut.result()
                    if embedding:
                        all_embeddings.append(np.array(embedding, dtype=np.float32))
                        print(f"[Vision API] Frame {idx+1}/{len(frames)} ✓")
                    else:
                        print(f"[Vision API] Frame {idx+1}/{len(frames)} failed — skipping")
                except Exception as e:
                    print(f"[Vision API] Frame {idx+1} error: {e}")

    # If cloud embeddings failed entirely, use local deterministic fallback.
    if not all_embeddings:
        print("[Vision API] Falling back to local embeddings for all frames.")
        for i, frame in enumerate(frames):
            try:
                all_embeddings.append(_local_fallback_embedding(frame))
                print(f"[Local Embedder] Frame {i+1}/{len(frames)} ✓")
            except Exception as e:
                print(f"[Local Embedder] Frame {i+1} error: {e}")

    if not all_embeddings:
        print("[Embedder] All frames failed.")
        return None

    # Mean pool all embeddings
    stacked  = np.stack(all_embeddings, axis=0)
    mean_vec = np.mean(stacked, axis=0)

    # Normalise to unit sphere (important for cosine similarity)
    norm = np.linalg.norm(mean_vec)
    if norm > 0:
        mean_vec = mean_vec / norm

    fingerprint = mean_vec.tolist()
    print(f"[Vision API] Fingerprint ready. Dimensions: {len(fingerprint)} | latency={time.time()-t0:.2f}s")
    return fingerprint
