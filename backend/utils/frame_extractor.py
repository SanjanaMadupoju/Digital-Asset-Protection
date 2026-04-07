"""
frame_extractor.py — Extracts frames from a video file and applies the watermark.

Strategy:
  - Extract 1 frame every FRAME_INTERVAL seconds
  - Apply the DCT watermark to each frame
  - Return the watermarked frames as a list of numpy arrays

Why 1 frame every 2 seconds?
  - A 90-minute sports match = 2700 frames → fast enough locally
  - Captures enough visual diversity for a good CLIP fingerprint
  - Reduces redundancy (consecutive frames look almost identical)
"""

import cv2
import os
import numpy as np
from utils.watermark import embed_watermark

# Extract one frame every N seconds
FRAME_INTERVAL_SECONDS = 2

# Resize frames before CLIP — CLIP ViT-B/32 expects 224x224
# We resize here to save memory; CLIP's preprocessor will also resize,
# but doing it early reduces RAM usage on your laptop
CLIP_INPUT_SIZE = (224, 224)

WATERMARKED_OUTPUT_DIR = r"C:\Users\MadupojuSanjana\Documents\llm\sports-fingerprint\backend\temp_frames"


def extract_and_watermark_frames(video_path: str, video_id: str) -> list:
    """
    Opens the video, watermarks ALL frames and writes to disk in a single pass.
    Also collects sampled frames (every FRAME_INTERVAL_SECONDS) for CLIP.

    Args:
        video_path : full path to the video file in uploads/
        video_id   : UUID from Step 1, passed to the watermarker

    Returns:
        List of numpy arrays (BGR frames, 224x224, watermarked) for CLIP
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"OpenCV could not open video: {video_path}")

    # Get video properties
    fps          = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"[FrameExtractor] Video: {video_path}")
    print(f"[FrameExtractor] FPS: {fps:.1f}  |  Total frames: {total_frames}  |  Duration: {duration_sec:.1f}s")

    # ── Setup VideoWriter ─────────────────────────────────────────────────────
    os.makedirs(WATERMARKED_OUTPUT_DIR, exist_ok=True)
    output_filename = f"watermarked_{video_id}.avi"
    output_path = os.path.join(WATERMARKED_OUTPUT_DIR, output_filename)
    fourcc = cv2.VideoWriter_fourcc(*"FFV1")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # How many frames to skip between each CLIP sample
    frame_step = max(1, int(fps * FRAME_INTERVAL_SECONDS))

    watermarked_frames = []
    frame_number = 0

    # ── Single pass: watermark ALL frames, write to video AND collect samples ─
    print(f"[FrameExtractor] Writing watermarked video to: {output_path}")

    while True:
        success, frame = cap.read()
        if not success:
            break

        # 1. Apply invisible DCT watermark
        wm_frame = embed_watermark(frame, video_id)

        # 2. Write every frame to the output video file
        writer.write(wm_frame)

        # 3. Collect sampled frames for CLIP (every frame_step)
        if frame_number % frame_step == 0:
            resized = cv2.resize(wm_frame, CLIP_INPUT_SIZE, interpolation=cv2.INTER_LINEAR)
            watermarked_frames.append(resized)

        frame_number += 1

    writer.release()
    cap.release()

    print(f"[FrameExtractor] Watermarked video saved: {output_path}")
    print(f"[FrameExtractor] Extracted & watermarked {len(watermarked_frames)} frames for CLIP")

    return watermarked_frames, output_path
