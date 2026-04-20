# """
# scraper_db.py — Saves collected URLs to MongoDB.

# Each URL collected by the scraper is saved as a document in the
# "scraped_urls" collection with status "pending_fingerprint".

# Step 4 will query this collection, download frames, and fingerprint them.

# Document structure:
# {
#     "url":                "https://www.youtube.com/watch?v=abc123",
#     "platform":           "youtube",
#     "source":             "keyword_search",
#     "sport":              "cricket",
#     "keywords":           "IPL 2024 highlights",
#     "original_video_id":  "9b332136-...",   <- the video we're protecting
#     "status":             "pending_fingerprint",
#     "scraped_at":         "2024-01-01T12:00:00",
#     "fingerprinted":      false,
#     "flagged":            false,
# }
# """

# from utils.db import db
# import datetime

# scraped_col = db["scraped_urls"]

# # Index on URL to prevent duplicates
# scraped_col.create_index("url", unique=True)


# def save_urls(urls: list[dict], original_video_id: str) -> dict:
#     """
#     Saves a list of collected URL dicts to MongoDB.
#     Skips duplicates silently (unique index on url).

#     Args:
#         urls              : list of dicts from any scraper function
#         original_video_id : the video_id from Step 1 we are protecting

#     Returns:
#         dict with counts: saved, skipped (duplicates), total
#     """
#     saved   = 0
#     skipped = 0
#     timestamp = datetime.datetime.utcnow().isoformat()

#     for item in urls:
#         doc = {
#             **item,
#             "original_video_id": original_video_id,
#             "status":            "pending_fingerprint",
#             "scraped_at":        timestamp,
#             "fingerprinted":     False,
#             "match_score":       None,
#             "flagged":           False,
#         }
#         try:
#             scraped_col.insert_one(doc)
#             saved += 1
#         except Exception:
#             # Duplicate URL — skip silently
#             skipped += 1

#     return {
#         "saved":   saved,
#         "skipped": skipped,
#         "total":   saved + skipped,
#     }


# def get_pending_urls(original_video_id: str = None, limit: int = 50) -> list[dict]:
#     """
#     Returns URLs that are pending fingerprinting.
#     Used by Step 4 to know what to process next.
#     """
#     query = {"status": "pending_fingerprint"}
#     if original_video_id:
#         query["original_video_id"] = original_video_id

#     docs = list(scraped_col.find(query, {"_id": 0}).limit(limit))
#     return docs


# def get_all_scraped(original_video_id: str = None) -> list[dict]:
#     """Returns all scraped URLs for a given original video."""
#     query = {}
#     if original_video_id:
#         query["original_video_id"] = original_video_id
#     return list(scraped_col.find(query, {"_id": 0})) 

"""
scraper_db.py — Saves scraped URLs to Firestore (was MongoDB).

Each URL document:
{
  "url":                "https://youtube.com/watch?v=xyz",
  "platform":           "youtube",
  "source":             "keyword_search",
  "sport":              "cricket",
  "keywords":           "IPL 2024 highlights",
  "original_video_id":  "9b332136-...",
  "status":             "pending_fingerprint",
  "scraped_at":         "2024-01-01T12:00:00",
  "fingerprinted":      false,
  "flagged":            false,
}

Document ID = MD5 of URL → auto-deduplication (same URL = same doc ID)
"""

from utils.firebase_init import (
    scraped_urls_ref, save_scraped_url,
    get_scraped_urls, update_scraped_url
)
import datetime


def save_urls(urls: list[dict], original_video_id: str) -> dict:
    """
    Saves collected URLs to Firestore.
    Duplicate URLs are skipped (doc ID = MD5 of URL).
    """
    saved   = 0
    skipped = 0
    timestamp = datetime.datetime.utcnow().isoformat()

    for item in urls:
        doc = {
            **item,
            "original_video_id": original_video_id,
            "status":            "pending_fingerprint",
            "scraped_at":        timestamp,
            "fingerprinted":     False,
            "match_score":       None,
            "flagged":           False,
        }
        result = save_scraped_url(doc)
        if result == "saved":
            saved += 1
        else:
            skipped += 1

    print(f"[Firestore] Scraped URLs — saved={saved} skipped={skipped}")
    return {"saved": saved, "skipped": skipped, "total": saved + skipped}


def get_pending_urls(original_video_id: str, limit: int = 50) -> list[dict]:
    """Returns URLs pending fingerprinting for a given video."""
    query = {"status": "pending_fingerprint"}
    if original_video_id:
        query["original_video_id"] = original_video_id
        
    all_docs = get_scraped_urls(original_video_id, status="pending_fingerprint")
    # return all_docs[:limit]
    return all_docs


def get_all_scraped(original_video_id: str) -> list[dict]:
    """Returns all scraped URLs for a given video."""
    return get_scraped_urls(original_video_id)


def update_url_status(url: str, updates: dict):
    """Updates a scraped URL document by URL."""
    update_scraped_url(url, updates)