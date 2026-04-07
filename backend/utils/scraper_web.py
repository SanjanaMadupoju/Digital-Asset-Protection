"""
scraper_web.py — Web search + Dailymotion URL collector.

Fixed:
  - Filters out social profile/channel pages (only keeps actual video URLs)
  - Google query uses "inurl:watch" to target video pages directly
  - Facebook: only keeps /video/ or /reel/ URLs, not profile pages
  - Twitter: only keeps /status/ URLs with actual tweet content
  - Dailymotion: only keeps /video/ URLs
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import warnings
import urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()

REQUEST_TIMEOUT = 12
POLITE_DELAY    = 1.5

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

# ── URL validators — only accept actual video pages ───────────────────────────

def _is_valid_youtube_url(url: str) -> bool:
    """Only accept youtube.com/watch?v=XXXXXXXXXXX (11-char ID)"""
    return bool(re.search(r'youtube\.com/watch\?v=[\w-]{11}', url))

def _is_valid_dailymotion_url(url: str) -> bool:
    """Only accept dailymotion.com/video/xxxxx"""
    return bool(re.search(r'dailymotion\.com/video/[\w]+', url))

def _is_valid_twitter_url(url: str) -> bool:
    """Only accept twitter.com/*/status/* or x.com/*/status/*"""
    return bool(re.search(r'(twitter\.com|x\.com)/\w+/status/\d+', url))

def _is_valid_facebook_url(url: str) -> bool:
    """Only accept facebook.com/*/video/* or facebook.com/reel/*"""
    return bool(
        re.search(r'facebook\.com/.+/video', url) or
        re.search(r'facebook\.com/reel/\d+', url) or
        re.search(r'facebook\.com/watch/?\?v=\d+', url)
    )

def _classify_video_url(url: str) -> str | None:
    """
    Returns the platform name if URL is a valid individual video page.
    Returns None if it's a channel, profile, homepage, or irrelevant page.
    """
    url = url.split("?")[0] if "youtube" not in url else url  # keep ?v= for YouTube

    if _is_valid_youtube_url(url):
        return "youtube"
    if _is_valid_dailymotion_url(url):
        return "dailymotion"
    if _is_valid_twitter_url(url):
        return "twitter"
    if _is_valid_facebook_url(url):
        return "facebook"
    if "vimeo.com/" in url and re.search(r'vimeo\.com/\d+', url):
        return "vimeo"
    if "rumble.com/v" in url:
        return "rumble"
    return None


# ── Fetchers ──────────────────────────────────────────────────────────────────

def _fetch_with_requests(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT, verify=False)
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"[WebScraper] requests failed: {e}")
    return None


def _fetch_with_playwright(url: str) -> str | None:
    try:
        from playwright.sync_api import sync_playwright
        print(f"[WebScraper] Playwright fallback for: {url[:60]}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            ctx = browser.new_context(ignore_https_errors=True)
            page = ctx.new_page()
            page.goto(url, timeout=20000, wait_until="domcontentloaded")
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"[WebScraper] Playwright failed: {e}")
    return None


def fetch_page(url: str) -> str | None:
    html = _fetch_with_requests(url)
    if html:
        return html
    return _fetch_with_playwright(url)


# ── Google search ─────────────────────────────────────────────────────────────

def google_search_video_urls(sport: str, keywords: str, max_results: int = 10) -> list[dict]:
    """
    Searches Google specifically for video pages using site: operators.
    Returns validated individual video URLs only.

    Uses multiple targeted queries:
      1. site:youtube.com/watch  → direct YouTube videos
      2. site:dailymotion.com/video → Dailymotion videos
      3. General keyword search  → any video platform
    """
    all_results = []
    seen = set()

    queries = [
        # Query 1: Direct YouTube video search
        f'site:youtube.com/watch "{sport}" "{keywords}"',
        # Query 2: Dailymotion
        f'site:dailymotion.com/video {sport} {keywords}',
        # Query 3: Broad video search across platforms
        f'{sport} {keywords} highlights video site:rumble.com OR site:vimeo.com',
    ]

    for query in queries:
        encoded = quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded}&num=10"
        print(f"[Google] Query: {query[:80]}")

        html = fetch_page(search_url)
        if not html:
            print("[Google] No response, trying Bing for this query...")
            # Try Bing for this query
            bing_url = f"https://www.bing.com/search?q={encoded}&count=10"
            html = fetch_page(bing_url)
            if not html:
                continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Handle Google's /url?q= redirect wrapper
            if "/url?q=" in href:
                href = href.split("/url?q=")[1].split("&")[0]

            # Skip Google internal links
            if "google.com" in href or "bing.com" in href:
                continue

            # Validate — must be an actual video page
            platform = _classify_video_url(href)
            if platform and href not in seen:
                seen.add(href)
                all_results.append({
                    "url":      href,
                    "platform": platform,
                    "source":   "google_search",
                    "sport":    sport,
                    "keywords": keywords,
                    "query":    query,
                })
                if len(all_results) >= max_results:
                    break

        time.sleep(POLITE_DELAY)

        if len(all_results) >= max_results:
            break

    print(f"[Google] Found {len(all_results)} valid video URLs")
    return all_results


def bing_search_video_urls(sport: str, keywords: str, max_results: int = 10) -> list[dict]:
    """
    Bing search targeting actual video URLs.
    """
    all_results = []
    seen = set()

    queries = [
        f'site:youtube.com/watch {sport} {keywords}',
        f'site:dailymotion.com/video {sport} {keywords}',
        f'{sport} {keywords} highlights video',
    ]

    for query in queries:
        encoded = quote_plus(query)
        search_url = f"https://www.bing.com/search?q={encoded}&count=10"
        print(f"[Bing] Query: {query[:80]}")

        html = fetch_page(search_url)
        if not html:
            continue

        soup = BeautifulSoup(html, "html.parser")

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "bing.com" in href or "microsoft.com" in href:
                continue

            platform = _classify_video_url(href)
            if platform and href not in seen:
                seen.add(href)
                all_results.append({
                    "url":      href,
                    "platform": platform,
                    "source":   "bing_search",
                    "sport":    sport,
                    "keywords": keywords,
                })
                if len(all_results) >= max_results:
                    break

        time.sleep(POLITE_DELAY)
        if len(all_results) >= max_results:
            break

    print(f"[Bing] Found {len(all_results)} valid video URLs")
    return all_results


def search_dailymotion(sport: str, keywords: str, max_results: int = 10) -> list[dict]:
    """Searches Dailymotion — only returns /video/ URLs."""
    query = f"{sport} {keywords}"
    encoded = quote_plus(query)
    search_url = f"https://www.dailymotion.com/search/{encoded}/videos"
    print(f"[Dailymotion] Searching: '{query}'")

    html = fetch_page(search_url)
    if not html:
        html = _fetch_with_playwright(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = urljoin("https://www.dailymotion.com", a["href"]).split("?")[0]
        if _is_valid_dailymotion_url(href) and href not in seen:
            seen.add(href)
            results.append({
                "url":      href,
                "title":    a.get_text(strip=True) or "Unknown",
                "platform": "dailymotion",
                "source":   "keyword_search",
                "sport":    sport,
                "keywords": keywords,
            })
            if len(results) >= max_results:
                break

    print(f"[Dailymotion] Found {len(results)} valid video URLs")
    return results


def search_twitter(sport: str, keywords: str, max_results: int = 10) -> list[dict]:
    """
    Finds Twitter/X video posts via Bing.
    Only returns /status/ URLs (actual tweets), not profile pages.
    """
    query = f'site:twitter.com OR site:x.com {sport} {keywords} video'
    encoded = quote_plus(query)
    search_url = f"https://www.bing.com/search?q={encoded}&count=20"
    print(f"[Twitter/X] Searching via Bing: '{query[:70]}'")

    html = fetch_page(search_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].split("?")[0]
        if _is_valid_twitter_url(href) and href not in seen:
            seen.add(href)
            results.append({
                "url":      href,
                "platform": "twitter",
                "source":   "bing_search",
                "sport":    sport,
                "keywords": keywords,
            })
            if len(results) >= max_results:
                break

    print(f"[Twitter/X] Found {len(results)} valid tweet URLs")
    return results