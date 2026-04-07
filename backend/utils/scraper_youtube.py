"""
scraper_youtube.py — YouTube URL collector using yt-dlp.
Only returns individual watch?v= URLs. SSL bypass for corporate networks.
"""

import yt_dlp
import re


def _clean_video_url(entry: dict) -> str | None:
    """Returns a clean watch?v= URL or None if entry is not a valid video."""
    video_id = entry.get("id", "")
    if not video_id or len(video_id) != 11:
        return None
    if entry.get("_type", "") in ["playlist", "channel"]:
        return None
    return f"https://www.youtube.com/watch?v={video_id}"


def _build_opts() -> dict:
    """yt-dlp options with corporate SSL bypass."""
    return {
        "quiet":                 True,
        "no_warnings":           True,
        "extract_flat":          True,
        "skip_download":         True,
        "ignoreerrors":          True,
        "nocheckcertificate":    True,   # ← bypasses SSL cert verification
        "legacy_server_connect": True,   # ← fixes SSL handshake on proxies
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
    }


def search_youtube(sport: str, keywords: str, max_results: int = 10) -> list[dict]:
    """
    Searches YouTube for individual videos matching sport + keywords.
    Returns only watch?v= URLs — no channels, playlists, or profile pages.
    """
    query = f"{sport} {keywords}"
    fetch_count = max_results * 3   # fetch more to compensate for filtered-out channels
    search_string = f"ytsearch{fetch_count}:{query}"

    print(f"[YouTube] Searching: '{query}' (fetching {fetch_count}, filtering to {max_results})")

    results = []
    try:
        with yt_dlp.YoutubeDL(_build_opts()) as ydl:
            
            if query.trim() == "":
                print("[YouTube] No results returned.")
                return []
            
            info = ydl.extract_info(search_string, download=False)

            if not info or "entries" not in info:
                print("[YouTube] No results returned.")
                return []

            for entry in info["entries"]:
                if not entry:
                    continue
                clean_url = _clean_video_url(entry)
                if not clean_url:
                    print(f"[YouTube] Skipped non-video: id={entry.get('id','?')}")
                    continue

                results.append({
                    "url":         clean_url,
                    "title":       entry.get("title", "Unknown"),
                    "channel":     entry.get("uploader", "Unknown"),
                    "channel_url": entry.get("uploader_url", ""),
                    "duration":    entry.get("duration", 0),
                    "view_count":  entry.get("view_count", 0),
                    "platform":    "youtube",
                    "source":      "keyword_search",
                    "sport":       sport,
                    "keywords":    keywords,
                })

                if len(results) >= max_results:
                    break

    except Exception as e:
        print(f"[YouTube] Search error: {e}")

    print(f"[YouTube] Got {len(results)} valid video URLs")
    return results


def scan_channel(channel_url: str, sport: str, max_videos: int = 10) -> list[dict]:
    """
    Scans a suspicious YouTube channel for individual video URLs.
    Only returns watch?v= URLs.
    """
    print(f"[YouTube] Scanning channel: {channel_url}")
    results = []
    opts = {**_build_opts(), "playlistend": max_videos * 2}

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
        
            if not info:
                return []

            for entry in (info.get("entries") or []):
                if not entry:
                    continue
                clean_url = _clean_video_url(entry)
                if not clean_url:
                    continue
                results.append({
                    "url":         clean_url,
                    "title":       entry.get("title", "Unknown"),
                    "channel":     info.get("uploader", "Unknown"),
                    "channel_url": channel_url,
                    "duration":    entry.get("duration", 0),
                    "view_count":  entry.get("view_count", 0),
                    "platform":    "youtube",
                    "source":      "channel_scan",
                    "sport":       sport,
                    "keywords":    "",
                })
                if len(results) >= max_videos:
                    break

    except Exception as e:
        print(f"[YouTube] Channel scan error: {e}")

    print(f"[YouTube] Got {len(results)} valid video URLs from channel")
    return results