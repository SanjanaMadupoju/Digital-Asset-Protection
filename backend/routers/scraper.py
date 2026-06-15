"""
scraper.py — Step 3 router. Collects actual video URLs only.

YouTube-only MVP using plugin architecture.
Searches YouTube with SearchContext filters for sports content narrowing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from utils.scraper_plugin import scraper_registry, SearchContext
from utils.scraper_db import save_urls, get_all_scraped
import time

router = APIRouter()


class ScrapeRequest(BaseModel):
    """Request to scrape YouTube for video URLs matching a given context."""
    video_id:            str
    sport:               str
    keywords:            str
    
    # SearchContext filters (all optional)
    duration_min:        Optional[int] = None      # Min duration in seconds
    duration_max:        Optional[int] = None      # Max duration in seconds
    min_view_count:      Optional[int] = None      # Min view count (e.g., 1000)
    uploaded_after:      Optional[datetime] = None # Only videos after this date
    channel_whitelist:   Optional[list[str]] = None # Only these channels
    channel_blacklist:   Optional[list[str]] = None # Exclude these channels
    
    max_results:         int       = 10


@router.post("/scrape")
def run_scraper(req: ScrapeRequest):
    """
    Runs enabled scrapers (YouTube MVP) and saves video URLs.
    
    Uses SearchContext to narrow YouTube search:
    - Sport type (e.g., cricket, football)
    - League/keywords (e.g., IPL, Premier League)
    - Duration range (e.g., 2-20 min for highlights)
    - Min view count (e.g., 1000+ to skip noise)
    - Upload date (e.g., last 7-30 days)
    - Channel whitelist/blacklist (official broadcasters)
    """
    all_results = []
    errors      = []

    print(f"\n[Step3] Scrape started | sport={req.sport} | keywords={req.keywords}")

    # Build SearchContext from request
    context = SearchContext(
        video_id=req.video_id,
        sport=req.sport,
        keywords=req.keywords,
        duration_min=req.duration_min,
        duration_max=req.duration_max,
        min_view_count=req.min_view_count,
        uploaded_after=req.uploaded_after,
        channel_whitelist=req.channel_whitelist,
        channel_blacklist=req.channel_blacklist,
        max_results=req.max_results,
    )

    # Run all enabled scrapers via plugin registry
    print(f"\n[Step3] Running enabled scrapers...")
    scraper_results = scraper_registry.search_all(context)
    
    # Flatten results from all scrapers
    for scraper_name, results in scraper_results.items():
        print(f"[Step3] {scraper_name}: {len(results)} results")
        # Convert ScraperResult Pydantic models to dict for saving
        all_results.extend([r.dict() for r in results])

    # Deduplicate by URL
    seen = set()
    unique = []
    for item in all_results:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)

    print(f"\n[Step3] Total unique valid video URLs: {len(unique)}")

    # Save to MongoDB
    save_stats = save_urls(unique, req.video_id) if unique else {"saved": 0, "skipped": 0}

    # Platform breakdown
    platform_counts = {}
    for item in unique:
        p = item.get("platform", "unknown")
        platform_counts[p] = platform_counts.get(p, 0) + 1

    return {
        "success":            True,
        "video_id":           req.video_id,
        "sport":              req.sport,
        "keywords":           req.keywords,
        "search_context": {
            "duration_min":      req.duration_min,
            "duration_max":      req.duration_max,
            "min_view_count":    req.min_view_count,
            "uploaded_after":    req.uploaded_after,
            "channel_whitelist": req.channel_whitelist,
            "channel_blacklist": req.channel_blacklist,
        },
        "total_found":        len(unique),
        "saved_to_mongo":     save_stats["saved"],
        "duplicates_skipped": save_stats["skipped"],
        "by_platform":        platform_counts,
        "sample_urls":        [u["url"] for u in unique[:5]],  # preview first 5
        "errors":             errors if errors else None,
        "next_step":          "Run POST /api/fingerprint-scraped/{video_id} (Step 4)"
    }


@router.get("/scrape/{video_id}")
def get_scraped_urls(video_id: str):
    results = get_all_scraped(video_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No scraped URLs for: {video_id}")

    pending      = [r for r in results if r["status"] == "pending_fingerprint"]
    fingerprinted = [r for r in results if r["status"] == "fingerprinted"]
    flagged      = [r for r in results if r.get("flagged")]

    return {
        "video_id": video_id,
        "total": len(results),
        "pending": len(pending),
        "fingerprinted": len(fingerprinted),
        "flagged": len(flagged),
        "urls": results,
    }
    