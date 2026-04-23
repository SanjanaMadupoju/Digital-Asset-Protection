"""
frame_extractor.py — Extracts frames and applies watermark.
No longer imports CLIP — embedding handled by Google Vision AI.
Returns (full_res_frames, clip_frames) tuple for compatibility.
"""

import cv2
import os
import numpy as np
from utils.watermark import embed_watermark

# FRAME_INTERVAL_SECONDS = 2
FRAME_INTERVAL_SECONDS = 5
RESIZE_SIZE = (512, 512)   # larger than before since Vision API handles its own resize
TEMP_FRAMES_DIR = os.path.join(os.path.dirname(__file__), "..", "temp_frames")


def extract_and_watermark_frames(video_path: str, video_id: str) -> tuple:
    """
    Watermarks the full video and writes a playable output file.
    Also samples frames every 2 seconds for embedding.

    Returns:
        (full_res_frames, resized_frames, output_path)
        full_res_frames : sampled watermarked original-size frames
        resized_frames  : sampled watermarked 512x512 frames for Vision API
        output_path     : full watermarked video file path
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open: {video_path}")

    fps          = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / fps if fps > 0 else 0
    frame_step   = max(1, int(fps * FRAME_INTERVAL_SECONDS))
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    safe_fps     = fps if fps > 0 else 25.0

    print(f"[FrameExtractor] FPS={fps:.1f} | Frames={total_frames} | Duration={duration_sec:.1f}s")

    os.makedirs(os.path.abspath(TEMP_FRAMES_DIR), exist_ok=True)
    output_path = os.path.abspath(
        os.path.join(TEMP_FRAMES_DIR, f"watermarked_{video_id}.mp4")
    )
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, safe_fps, (width, height))

    full_res_frames = []
    resized_frames  = []
    frame_number    = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        if frame_number % frame_step == 0:
            wm_frame = embed_watermark(frame, video_id)  # watermark only at 5s intervals
            full_res_frames.append(wm_frame.copy())
            resized_frames.append(cv2.resize(wm_frame, RESIZE_SIZE))
        else:
            wm_frame = frame  # write original frame, no watermark
        frame_number += 1

        writer.write(wm_frame)

    writer.release()
    cap.release()
    print(f"[FrameExtractor] Extracted {len(full_res_frames)} frames")
    print(f"[FrameExtractor] Watermarked video saved: {output_path}")
    return full_res_frames, resized_frames, output_path
