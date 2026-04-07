"""
scraper.py — Step 3 router. Collects actual video URLs only.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from utils.scraper_youtube import search_youtube, scan_channel
from utils.scraper_web import (
    google_search_video_urls,
    bing_search_video_urls,
    search_dailymotion,
    search_twitter
)
from utils.scraper_db import save_urls, get_all_scraped
import time

router = APIRouter()


class ScrapeRequest(BaseModel):
    video_id:            str
    sport:               str
    keywords:            str
    suspicious_channels: list[str] = []
    max_results:         int       = 10


@router.post("/scrape")
def run_scraper(req: ScrapeRequest):
    """
    Runs all scrapers and saves ONLY individual video URLs to MongoDB.
    Channel pages, profile pages, homepages are all filtered out.
    """
    all_results = []
    errors      = []

    print(f"\n[Step3] Scrape started | sport={req.sport} | keywords={req.keywords}")

    # 1. YouTube keyword search (yt-dlp) — only watch?v= URLs
    print("\n[Step3] Source 1: YouTube yt-dlp search")
    try:
        yt = search_youtube(req.sport, req.keywords, req.max_results)
        all_results.extend(yt)
    except Exception as e:
        errors.append(f"YouTube: {e}")

    time.sleep(2)
    print(req.suspicious_channels)
    # 2. Suspicious channel scan
    if req.suspicious_channels:
        print(f"\n[Step3] Source 2: Scanning {len(req.suspicious_channels)} channels")
        for ch in req.suspicious_channels:
            try:
                ch_res = scan_channel(ch, req.sport, req.max_results)
                all_results.extend(ch_res)
                time.sleep(2)
            except Exception as e:
                errors.append(f"Channel {ch}: {e}")

    # 3. Google search (site:youtube.com/watch, site:dailymotion.com/video etc.)
    print("\n[Step3] Source 3: Google targeted video search")
    try:
        google_res = google_search_video_urls(req.sport, req.keywords, req.max_results)
        all_results.extend(google_res)
        if not google_res:
            print("[Step3] Google returned nothing, trying Bing...")
            bing_res = bing_search_video_urls(req.sport, req.keywords, req.max_results)
            all_results.extend(bing_res)
    except Exception as e:
        errors.append(f"Google/Bing: {e}")

    time.sleep(1)

    # 4. Dailymotion
    print("\n[Step3] Source 4: Dailymotion")
    try:
        dm = search_dailymotion(req.sport, req.keywords, req.max_results)
        all_results.extend(dm)
    except Exception as e:
        errors.append(f"Dailymotion: {e}")

    time.sleep(1)

    # 5. Twitter/X
    print("\n[Step3] Source 5: Twitter/X")
    try:
        tw = search_twitter(req.sport, req.keywords, req.max_results)
        all_results.extend(tw)
    except Exception as e:
        errors.append(f"Twitter: {e}")

    # Deduplicate
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
    