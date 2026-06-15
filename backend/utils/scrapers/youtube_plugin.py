"""
youtube_plugin.py — YouTube scraper plugin using yt-dlp with search context narrowing.

Features:
- Only returns individual watch?v= URLs
- SSL bypass for corporate networks
- Supports SearchContext filters: sport, league, duration, min_views, upload date, channel whitelist
- Channel scanning for suspicious content
"""

import yt_dlp
import re
from datetime import datetime
from typing import Optional, List
from utils.scraper_plugin import ScraperPlugin, SearchContext, ScraperResult


class YouTubePlugin(ScraperPlugin):
    """YouTube scraper using yt-dlp with sports-specific search narrowing."""
    
    def __init__(self):
        super().__init__()
        self.name = "youtube"
    
    def search(self, context: SearchContext) -> List[ScraperResult]:
        """
        Search YouTube with context filters to narrow results for sports content.
        
        Search narrowing strategy:
        - Add sport keywords and league/tournament to query
        - Filter by duration (e.g., 2-20 min for highlights)
        - Filter by min view count (e.g., 1k+ to skip noise)
        - Filter by upload date (e.g., last 7-30 days)
        - Optional channel whitelist (official broadcasters)
        """
        query = self._build_search_query(context)
        fetch_count = context.max_results * 3  # fetch more to compensate for filtering
        search_string = f"ytsearch{fetch_count}:{query}"
        
        print(f"[YouTube] Searching: '{query}'")
        if context.duration_min or context.duration_max:
            print(f"[YouTube] Duration filter: {context.duration_min}s - {context.duration_max}s")
        if context.min_view_count:
            print(f"[YouTube] Min views: {context.min_view_count}")
        if context.uploaded_after:
            print(f"[YouTube] Uploaded after: {context.uploaded_after.date()}")
        
        results = []
        try:
            with yt_dlp.YoutubeDL(self._build_opts()) as ydl:
                if not query.strip():
                    print("[YouTube] Empty query, returning no results")
                    return []
                
                info = ydl.extract_info(search_string, download=False)
                
                if not info or "entries" not in info:
                    print("[YouTube] No results returned")
                    return []
                
                for entry in info["entries"]:
                    if not entry:
                        continue
                    
                    # Validate URL format
                    clean_url = self._clean_video_url(entry)
                    if not clean_url:
                        continue
                    
                    # Apply search context filters
                    if not self._passes_filters(entry, context):
                        continue
                    
                    # Optional: check channel whitelist
                    if context.channel_whitelist:
                        channel = entry.get("uploader", "").lower()
                        if not any(wl.lower() in channel for wl in context.channel_whitelist):
                            continue
                    
                    # Optional: check channel blacklist
                    if context.channel_blacklist:
                        channel = entry.get("uploader", "").lower()
                        if any(bl.lower() in channel for bl in context.channel_blacklist):
                            continue
                    
                    results.append(ScraperResult(
                        url=clean_url,
                        title=entry.get("title", "Unknown"),
                        channel=entry.get("uploader", "Unknown"),
                        channel_url=entry.get("uploader_url", ""),
                        duration=entry.get("duration", 0),
                        view_count=entry.get("view_count", 0),
                        platform="youtube",
                        source="keyword_search",
                        sport=context.sport,
                        keywords=context.keywords,
                        uploaded_date=self._parse_upload_date(entry),
                    ))
                    
                    if len(results) >= context.max_results:
                        break
        
        except Exception as e:
            print(f"[YouTube] Search error: {e}")
        
        print(f"[YouTube] Got {len(results)} valid video URLs after filtering")
        return results
    
    def validate_url(self, url: str) -> bool:
        """Validate that URL is a YouTube watch?v= URL."""
        return bool(re.search(r'youtube\.com/watch\?v=[\w-]{11}', url))
    
    def _build_search_query(self, context: SearchContext) -> str:
        """Build yt-dlp search query from SearchContext."""
        # Base query: sport + keywords/league
        query_parts = [context.sport]
        if context.keywords:
            query_parts.append(context.keywords)
        
        # Add date filter if provided (e.g., "uploaded:>2024-01-15")
        if context.uploaded_after:
            date_str = context.uploaded_after.strftime("%Y-%m-%d")
            query_parts.append(f"uploaded:>{date_str}")
        
        # Exclude common false-positive keywords
        # (These make the query more sports-specific)
        exclude_keywords = [
            "-tutorial",
            "-review",
            "-gameplay",
            "-trailer",
        ]
        
        return " ".join(query_parts + exclude_keywords)
    
    def _passes_filters(self, entry: dict, context: SearchContext) -> bool:
        """Check if entry passes all SearchContext filters."""
        # Duration filter
        duration = entry.get("duration", 0)
        if context.duration_min and duration < context.duration_min:
            return False
        if context.duration_max and duration > context.duration_max:
            return False
        
        # View count filter
        if context.min_view_count:
            view_count = entry.get("view_count", 0) or 0
            if view_count < context.min_view_count:
                return False
        
        # Upload date filter
        if context.uploaded_after:
            upload_date = self._parse_upload_date(entry)
            if upload_date and upload_date < context.uploaded_after:
                return False
        
        return True
    
    def _parse_upload_date(self, entry: dict) -> Optional[datetime]:
        """Extract upload date from yt-dlp entry."""
        try:
            # yt-dlp uses 'upload_date' as YYYYMMDD string
            upload_date_str = entry.get("upload_date")
            if upload_date_str and len(upload_date_str) == 8:
                return datetime.strptime(upload_date_str, "%Y%m%d")
        except Exception:
            pass
        return None
    
    def _clean_video_url(self, entry: dict) -> Optional[str]:
        """Extract clean watch?v= URL from yt-dlp entry."""
        video_id = entry.get("id", "")
        if not video_id or len(video_id) != 11:
            return None
        if entry.get("_type", "") in ["playlist", "channel"]:
            return None
        return f"https://www.youtube.com/watch?v={video_id}"
    
    def _build_opts(self) -> dict:
        """yt-dlp options with corporate SSL bypass and optimizations for sports content."""
        return {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
            "ignoreerrors": True,
            "nocheckcertificate": True,  # ← bypasses SSL cert verification
            "legacy_server_connect": True,  # ← fixes SSL handshake on proxies
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
        }


# Create global instance
youtube_plugin = YouTubePlugin()
