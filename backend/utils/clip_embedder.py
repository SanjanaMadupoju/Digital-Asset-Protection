"""
clip_embedder.py — Runs CLIP ViT-B/32 on frames and produces a fingerprint.

What CLIP does here:
  - Takes each watermarked frame (224x224 BGR numpy array)
  - Converts BGR → RGB (CLIP expects RGB)
  - Applies CLIP's own preprocessing (normalise, tensor)
  - Runs through the Vision Transformer (ViT-B/32)
  - Outputs a 512-dimensional embedding vector per frame

Why mean-pool?
  - Each frame gives one 512-dim vector
  - Average all frame vectors → one 512-dim fingerprint for the whole video
  - This single vector represents the video's visual "identity"
  - Two copies of the same video will have very similar vectors (cosine > 0.92)
  - A completely different video will be far away (cosine < 0.5)

Note on speed:
  - CPU inference: ~1-3 seconds per frame
  - For a 1.7MB test video (~5-10 frames extracted) = ~10-30 seconds total
  - Totally fine for development
"""

import clip
import torch
import numpy as np
from PIL import Image
import cv2


# Load model once at module level — avoids reloading on every request
# ViT-B/32 = Vision Transformer, patch size 32, outputs 512 dims
# "cpu" = runs on your laptop without a GPU
print("[CLIP] Loading ViT-B/32 model... (first time takes ~1 min to download)")
MODEL, PREPROCESS = clip.load("ViT-B/32", device="cpu")
MODEL.eval()  # inference mode, not training
print("[CLIP] Model loaded and ready.")


def frames_to_fingerprint(frames: list) -> list:
    """
    Takes a list of watermarked BGR frames (numpy arrays),
    runs each through CLIP, returns the mean-pooled 512-dim fingerprint.

    Args:
        frames : list of np.ndarray, shape (224, 224, 3), dtype uint8, BGR

    Returns:
        list of 512 floats (the video fingerprint vector)
        Returns None if frames list is empty.
    """
    if not frames:
        print("[CLIP] No frames to process.")
        return None

    all_embeddings = []

    print(f"[CLIP] Processing {len(frames)} frames...")

    for i, frame_bgr in enumerate(frames):
        print("came here1")
        # Step 1: OpenCV uses BGR, PIL uses RGB — must convert
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        print("came here2")
        # Step 2: Convert numpy array to PIL Image (CLIP preprocessor needs PIL)
        pil_image = Image.fromarray(frame_rgb)

        # Step 3: Apply CLIP preprocessing (resize, normalise, tensorise)
        tensor = PREPROCESS(pil_image).unsqueeze(0)  # shape: (1, 3, 224, 224)

        # Step 4: Run through CLIP vision encoder
        with torch.no_grad():
            embedding = MODEL.encode_image(tensor)  # shape: (1, 512)

        # Step 5: Normalise to unit sphere (important for cosine similarity)
        embedding = embedding / embedding.norm(dim=-1, keepdim=True)

        # Convert to Python list and store
        all_embeddings.append(embedding.squeeze(0).cpu().numpy())

        if (i + 1) % 5 == 0:
            print(f"[CLIP] {i+1}/{len(frames)} frames done")

    # Step 6: Mean-pool all frame embeddings into one fingerprint
    stacked   = np.stack(all_embeddings, axis=0)   # shape: (N, 512)
    mean_vec  = np.mean(stacked, axis=0)            # shape: (512,)

    # Step 7: Re-normalise after averaging
    norm      = np.linalg.norm(mean_vec)
    if norm > 0:
        mean_vec = mean_vec / norm

    fingerprint = mean_vec.tolist()  # convert to plain Python list for MongoDB

    print(f"[CLIP] Fingerprint ready. Vector length: {len(fingerprint)}")
    return fingerprint
