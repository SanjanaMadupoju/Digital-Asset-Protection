"""
frame_downloader.py — Downloads sample frames from a URL.

Strategy per platform:
  - YouTube / Dailymotion : yt-dlp downloads a short clip → OpenCV extracts frames
  - Twitter / X / Facebook: Playwright screenshots the page (video thumbnail visible)
  - Any other URL         : requests fetches the page → BeautifulSoup finds og:image
                            or Playwright screenshots as fallback

We only need 3-5 frames per URL — enough for a meaningful CLIP fingerprint.
We do NOT download the full video — just enough frames to compare.
"""

import os
import cv2
import uuid
import tempfile
import requests
import numpy as np
from bs4 import BeautifulSoup
import yt_dlp
import warnings
import urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()

# Temp folder for downloaded clips/screenshots
TEMP_DIR = "temp_frames"
os.makedirs(TEMP_DIR, exist_ok=True)

# Platforms handled by yt-dlp
YTDLP_PLATFORMS = ["youtube.com", "youtu.be", "dailymotion.com"]

# Platforms that need a real browser (JS rendered)
BROWSER_PLATFORMS = ["twitter.com", "x.com", "facebook.com", "fb.com"]

# How many frames to extract from a downloaded clip
TARGET_FRAMES = 5


def _is_platform(url: str, domains: list) -> bool:
    return any(d in url for d in domains)


# ── yt-dlp frame extraction ───────────────────────────────────────────────────

def _download_clip_ytdlp(url: str) -> str | None:
    """
    Downloads a short clip (first 30 seconds only) using yt-dlp.
    Returns the path to the downloaded file, or None on failure.
    """
    out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.avi")

    ydl_opts = {
        "quiet":          True,
        "no_warnings":    True,
        "format":         "worst[ext=mp4]/worst",
        "outtmpl":        out_path,
        "noplaylist":     True,
        "ignoreerrors":   True,
        "postprocessor_args": ["-ss", "0", "-t", "30"],
        "nocheckcertificate": True,
        # Rate limit fixes — prevents YouTube from blocking your IP
        "sleep_interval":        3,    # wait 3 sec between requests
        "max_sleep_interval":    6,    # random sleep up to 6 sec
        "sleep_interval_requests": 2,  # wait 2 sec between API calls
        "extractor_retries":     3,    # retry 3 times on failure
        # Use a browser-like User-Agent so YouTube doesn't flag as a bot
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception as e:
        print(f"[yt-dlp] Download failed for {url}: {e}")
    return None

def _extract_frames_from_clip(clip_path: str, n_frames: int = TARGET_FRAMES) -> list:
    cap = cv2.VideoCapture(clip_path)
    if not cap.isOpened():
        return []

    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total == 0:
        cap.release()
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    # frame_step = max(1, int(fps * 2))  # same as FRAME_INTERVAL_SECONDS = 2
    frame_step = max(1, int(fps * 5))

    frames = []
    frame_number = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, frame = cap.read()
        if not ok:
            break
        # frames.append(cv2.resize(frame, (224, 224)))
        frames.append(frame)
        frame_number += frame_step

    cap.release()

    # Clean up the temp clip to save disk space
    WATERMARKED_OUTPUT_DIR = r"C:\Users\MadupojuSanjana\Documents\llm\sports-fingerprint\backend\temp_frames"
    try:
        if WATERMARKED_OUTPUT_DIR not in clip_path:
            os.remove(clip_path)
    except Exception:
        pass

    return frames


def get_frames_ytdlp(url: str) -> list:
    """Full pipeline: download clip → extract frames → return numpy arrays."""
    print(f"[Downloader] yt-dlp: {url[:70]}...")
    clip_path = _download_clip_ytdlp(url)
    if not clip_path:
        return []
    frames = _extract_frames_from_clip(clip_path)
    print(f"[Downloader] yt-dlp extracted {len(frames)} frames")
    return frames


# ── Playwright screenshot (browser platforms) ─────────────────────────────────

def get_frames_playwright(url: str) -> list:
    """
    Takes a screenshot of the page using Playwright.
    Converts the screenshot to a numpy array (treated as one "frame").
    Used for Twitter, Facebook etc where we can see the video thumbnail.
    """
    print(f"[Downloader] Playwright screenshot: {url[:70]}...")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                ignore_https_errors=True,   # bypass corporate SSL in browser too
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = ctx.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)   # wait for thumbnails to load

            # Take screenshot as bytes
            screenshot_bytes = page.screenshot(full_page=False)
            browser.close()

        # Convert PNG bytes → numpy array → BGR (OpenCV format)
        nparr = np.frombuffer(screenshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        # Resize to 224x224 for CLIP
        # resized = cv2.resize(img, (224, 224))
        resized = img
        print(f"[Downloader] Playwright got 1 screenshot frame")
        return [resized]

    except Exception as e:
        print(f"[Downloader] Playwright failed for {url}: {e}")
        return []


# ── requests + BeautifulSoup (og:image fallback) ─────────────────────────────

def get_frames_requests(url: str) -> list:
    """
    Fetches the page with requests and extracts the og:image thumbnail.
    og:image is the preview image most video sites set — good enough for CLIP.
    Falls back to Playwright if no og:image found.
    """
    print(f"[Downloader] requests og:image: {url[:70]}...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=12, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Look for og:image meta tag
        og_image = soup.find("meta", property="og:image")
        if not og_image:
            og_image = soup.find("meta", attrs={"name": "twitter:image"})

        if og_image and og_image.get("content"):
            img_url = og_image["content"]
            img_resp = requests.get(img_url, timeout=10, verify=False)
            nparr = np.frombuffer(img_resp.content, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is not None:
                # resized = cv2.resize(img, (224, 224))
                print(f"[Downloader] og:image extracted 1 thumbnail frame")
                # return [resized]
                return img

    except Exception as e:
        print(f"[Downloader] requests failed for {url}: {e}")

    # Fallback to Playwright
    return get_frames_playwright(url)


# ── Main dispatcher ───────────────────────────────────────────────────────────

def download_frames(url: str, platform: str) -> list:
    """
    Routes to the right downloader based on platform.

    Args:
        url      : the URL to download frames from
        platform : platform string saved by scraper (youtube, twitter, etc)

    Returns:
        List of BGR numpy arrays (224x224), empty list on failure
    """
    if _is_platform(url, YTDLP_PLATFORMS) or platform in ["youtube", "dailymotion"]:
        frames = get_frames_ytdlp(url)
        if frames:
            return frames
        # yt-dlp failed → try og:image fallback
        return get_frames_requests(url)

    elif _is_platform(url, BROWSER_PLATFORMS) or platform in ["twitter", "x", "facebook"]:
        frames = get_frames_playwright(url)
        if frames:
            return frames
        # Playwright failed → try og:image
        return get_frames_requests(url)

    else:
        # Unknown platform → try requests first, Playwright as fallback
        return get_frames_requests(url)