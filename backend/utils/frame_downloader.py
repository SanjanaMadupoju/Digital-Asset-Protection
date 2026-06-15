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
from concurrent.futures import ThreadPoolExecutor
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

# def _download_clip_ytdlp(url: str) -> str | None:
#     """
#     Downloads a short clip (first 30 seconds only) using yt-dlp.
#     Returns the path to the downloaded file, or None on failure.
#     """
#     out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.avi")

#     ydl_opts = {
#         "quiet":          True,
#         "no_warnings":    True,
#         "format":         "worst[ext=mp4]/worst",
#         "outtmpl":        out_path,
#         "noplaylist":     True,
#         "ignoreerrors":   True,
#         "postprocessor_args": ["-ss", "0", "-t", "30"],
#         "nocheckcertificate": True,
#         "cookiesfrombrowser": ("chrome",),
#         # Rate limit fixes — prevents YouTube from blocking your IP
#         "sleep_interval":        3,    # wait 3 sec between requests
#         "max_sleep_interval":    6,    # random sleep up to 6 sec
#         "sleep_interval_requests": 2,  # wait 2 sec between API calls
#         "extractor_retries":     3,    # retry 3 times on failure
#         # Use a browser-like User-Agent so YouTube doesn't flag as a bot
#         "http_headers": {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#         }
#     }

#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
#         if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
#             return out_path
#     except Exception as e:
#         print(f"[yt-dlp] Download failed for {url}: {e}")
#     return None

def _download_clip_ytdlp(url: str, cookie_path: str = None) -> str | None:
    out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp4")
    os.makedirs(TEMP_DIR, exist_ok=True)

    ydl_opts = {
        "quiet":          True,
        "no_warnings":    True,
        "format":         "worst[ext=mp4]/worst",
        "outtmpl":        out_path,
        "noplaylist":     True,
        "ignoreerrors":   True,
        "postprocessor_args": ["-ss", "0", "-t", "30"],
        "nocheckcertificate": True,
        "sleep_interval":        3,
        "max_sleep_interval":    6,
        "sleep_interval_requests": 2,
        "extractor_retries":     3,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
    }

    # ✅ Use cookies if provided
    if cookie_path:
        ydl_opts["cookiefile"] = cookie_path

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

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    frame_step = max(1, int(fps * 5))

    # Select a small, evenly spaced set of frame indices.
    frame_indices = [min(total - 1, i * frame_step) for i in range(n_frames)]

    def _read_at(frame_index: int):
        local_cap = cv2.VideoCapture(clip_path)
        if not local_cap.isOpened():
            return None
        local_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = local_cap.read()
        local_cap.release()
        return frame if ok else None

    with ThreadPoolExecutor(max_workers=min(4, len(frame_indices))) as pool:
        frames = [f for f in pool.map(_read_at, frame_indices) if f is not None]

    cap.release()

    # Clean up the temp clip to save disk space
    WATERMARKED_OUTPUT_DIR = r"C:\Users\MadupojuSanjana\Documents\llm\sports-fingerprint\backend\temp_frames"
    try:
        if WATERMARKED_OUTPUT_DIR not in clip_path:
            os.remove(clip_path)
    except Exception:
        pass

    return frames

def _get_cookies_via_playwright(url: str) -> str | None:
    """Gets cookies from Playwright and saves to temp file."""
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(
                ignore_https_errors=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = ctx.new_page()
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            cookies = ctx.cookies()
            browser.close()

        cookie_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_cookies.txt")
        os.makedirs(TEMP_DIR, exist_ok=True)

        with open(cookie_path, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            for cookie in cookies:
                domain = cookie.get("domain", "")
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = cookie.get("path", "/")
                secure = "TRUE" if cookie.get("secure") else "FALSE"
                expires = int(cookie.get("expires", 0))
                name = cookie.get("name", "")
                value = cookie.get("value", "")
                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        print(f"[Downloader] Playwright got {len(cookies)} cookies")
        return cookie_path

    except Exception as e:
        print(f"[Downloader] Playwright cookie fetch failed: {e}")
        return None

def get_frames_ytdlp(url: str) -> list:
    """Full pipeline: download clip → extract frames → return numpy arrays."""
    print(f"[Downloader] yt-dlp: {url[:70]}...")
    cookie_path = _get_cookies_via_playwright(url)
    clip_path = _download_clip_ytdlp(url, cookie_path=cookie_path)
    if cookie_path:
        try:
            os.remove(cookie_path)
        except:
            pass
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

# def get_frames_playwright(url: str) -> list:
#     print(f"[Downloader] Playwright screenshot: {url[:70]}...")
#     try:
#         from playwright.sync_api import sync_playwright
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             ctx = browser.new_context(
#                 ignore_https_errors=True,
#                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#             )
#             page = ctx.new_page()
#             page.goto(url, timeout=30000, wait_until="domcontentloaded")
#             page.wait_for_timeout(3000)

#             frames = []

#             # ✅ Seek to multiple timestamps and screenshot each
#             timestamps = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]  # every 5 seconds like yt-dlp

#             for t in timestamps:
#                 try:
#                     # Seek video to timestamp using JavaScript
#                     page.evaluate(f"""
#                         const video = document.querySelector('video');
#                         if (video) {{
#                             video.currentTime = {t};
#                             video.pause();
#                         }}
#                     """)
#                     page.wait_for_timeout(1000)  # wait for frame to render

#                     # Take screenshot
#                     screenshot_bytes = page.screenshot(full_page=False)

#                     # Convert to numpy array
#                     nparr = np.frombuffer(screenshot_bytes, np.uint8)
#                     img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
#                     if img is not None:
#                         frames.append(img)
#                         print(f"[Downloader] Playwright frame at {t}s ✓")
#                 except Exception as e:
#                     print(f"[Downloader] Playwright frame at {t}s failed: {e}")
#                     continue

#             browser.close()

#         if frames:
#             print(f"[Downloader] Playwright got {len(frames)} frames")
#             return frames

#         return []

#     except Exception as e:
#         print(f"[Downloader] Playwright failed for {url}: {e}")
#         return []

# def get_frames_playwright(url: str) -> list:
#     print(f"[Downloader] Playwright screenshot: {url[:70]}...")
#     try:
#         from playwright.sync_api import sync_playwright

#         video_url = None

#         def handle_request(request):
#             nonlocal video_url
#             # Intercept actual video stream requests
#             if any(ext in request.url for ext in ['.mp4', '.m3u8', '.ts', 'videoplayback']):
#                 if not video_url:
#                     video_url = request.url
#                     print(f"[Downloader] Intercepted video URL: {request.url[:70]}")

#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             ctx = browser.new_context(
#                 ignore_https_errors=True,
#                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
#             )
#             page = ctx.new_page()
#             page.on("request", handle_request)  # ✅ intercept requests
#             page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
#             # ✅ Click play to trigger video requests
#             try:
#                 page.evaluate("document.querySelector('video')?.play()")
#             except:
#                 pass
            
#             page.wait_for_timeout(5000)  # wait for video to start loading
#             browser.close()

#         if not video_url:
#             print(f"[Downloader] Playwright: no video URL intercepted")
#             return []

#         # ✅ Download and extract frames same as yt-dlp
#         out_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.mp4")
#         os.makedirs(TEMP_DIR, exist_ok=True)

#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
#             "Referer": url
#         }
#         resp = requests.get(video_url, headers=headers, stream=True, timeout=30, verify=False)

#         with open(out_path, "wb") as f:
#             for chunk in resp.iter_content(chunk_size=1024 * 1024):
#                 f.write(chunk)

#         if not os.path.exists(out_path) or os.path.getsize(out_path) < 1000:
#             print(f"[Downloader] Playwright: video download too small")
#             return []

#         # ✅ Same as yt-dlp!
#         frames = _extract_frames_from_clip(out_path)
#         print(f"[Downloader] Playwright extracted {len(frames)} frames")
#         return frames

#     except Exception as e:
#         print(f"[Downloader] Playwright failed for {url}: {e}")
#         return []

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
                return [img]

    except Exception as e:
        print(f"[Downloader] requests failed for {url}: {e}")

    # Fallback to Playwright
    return get_frames_playwright(url)

def _get_youtube_thumbnail_frames(url: str) -> list:
    """
    Gets YouTube video thumbnail as a frame.
    Works on Cloud Run — no download needed, just image fetch.
    YouTube provides multiple thumbnail qualities:
      maxresdefault.jpg (1280x720)
      hqdefault.jpg     (480x360)
      mqdefault.jpg     (320x180)
    """
    import re
    
    # Extract video ID from URL
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    if not match:
        print(f"[Downloader] Could not extract YouTube video ID from: {url}")
        return get_frames_requests(url)
    
    video_id = match.group(1)
    
    # Try thumbnails in order of quality
    thumbnail_urls = [
        f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg",
    ]
    
    frames = []
    for thumb_url in thumbnail_urls:
        try:
            resp = requests.get(thumb_url, timeout=10, verify=False)
            if resp.status_code == 200 and len(resp.content) > 1000:
                nparr = np.frombuffer(resp.content, np.uint8)
                img   = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                if img is not None:
                    print(f"[Downloader] YouTube thumbnail fetched: {thumb_url}")
                    frames.append(img)
        except Exception as e:
            print(f"[Downloader] Thumbnail fetch failed: {e}")
            continue

        if frames:
            print(f"[Downloader] Got {len(frames)} YouTube thumbnails")
            return frames
    
    # All thumbnails failed → og:image fallback
    return get_frames_requests(url)

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
    IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None
    
    if IS_CLOUD_RUN and (_is_platform(url, YTDLP_PLATFORMS) or platform in ["youtube", "dailymotion"]):
        print(f"[Downloader] Cloud Run — using YouTube thumbnail API")
        return _get_youtube_thumbnail_frames(url)

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