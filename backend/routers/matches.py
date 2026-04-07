"""
matches.py — Step 5 router. Match results and flagging dashboard API.

Endpoints:
  GET  /api/matches/{video_id}          → all flagged URLs sorted by score
  GET  /api/matches/{video_id}/summary  → counts and stats
  POST /api/matches/{video_id}/report   → generate a full evidence report
"""

from fastapi import APIRouter, HTTPException
from utils.scraper_db import scraped_col
from utils.db import fingerprints_col
import datetime

router = APIRouter()


@router.get("/matches/{video_id}")
def get_matches(video_id: str, min_score: float = 0.0, flagged_only: bool = False):
    """
    Returns all fingerprinted URLs for a video, sorted by match score descending.

    Query params:
      min_score    : only return URLs with score >= this (default 0.0 = all)
      flagged_only : if true, only return flagged URLs
    """
    query = {"original_video_id": video_id, "status": "fingerprinted"}
    if flagged_only:
        query["flagged"] = True
    if min_score > 0:
        query["match_score"] = {"$gte": min_score}

    docs = list(scraped_col.find(query, {"_id": 0}).sort("match_score", -1))

    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"No fingerprinted results for video_id: {video_id}. Complete Step 4 first."
        )

    # Enrich each result with a risk label
    for doc in docs:
        score = doc.get("match_score") or 0
        wm    = doc.get("watermark_found", False)
        if wm or score >= 0.92:
            doc["risk_level"] = "critical"
            doc["risk_label"] = "Confirmed copy — watermark or very high similarity"
        elif score >= 0.82:
            doc["risk_level"] = "high"
            doc["risk_label"] = "Very likely unauthorized copy"
        elif score >= 0.65:
            doc["risk_level"] = "medium"
            doc["risk_label"] = "Possible copy — manual review recommended"
        else:
            doc["risk_level"] = "low"
            doc["risk_label"] = "No significant match"

    return {
        "video_id":   video_id,
        "total":      len(docs),
        "flagged":    sum(1 for d in docs if d.get("flagged")),
        "results":    docs,
    }


@router.get("/matches/{video_id}/summary")
def get_summary(video_id: str):
    """
    High-level summary for the dashboard header card.
    """
    all_docs = list(scraped_col.find(
        {"original_video_id": video_id},
        {"_id": 0, "status": 1, "match_score": 1,
         "flagged": 1, "platform": 1, "watermark_found": 1}
    ))

    if not all_docs:
        raise HTTPException(status_code=404, detail=f"No data for video_id: {video_id}")

    fingerprinted = [d for d in all_docs if d["status"] == "fingerprinted"]
    flagged       = [d for d in all_docs if d.get("flagged")]
    pending       = [d for d in all_docs if d["status"] == "pending_fingerprint"]
    failed        = [d for d in all_docs if d["status"] == "failed"]
    watermarked   = [d for d in all_docs if d.get("watermark_found")]

    scores = [d["match_score"] for d in fingerprinted if d.get("match_score") is not None]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    max_score = round(max(scores), 4) if scores else 0

    # Platform breakdown of flagged URLs
    platform_flags = {}
    for d in flagged:
        p = d.get("platform", "unknown")
        platform_flags[p] = platform_flags.get(p, 0) + 1

    # Original video info
    orig = fingerprints_col.find_one({"video_id": video_id}, {"_id": 0, "fingerprint": 0})

    return {
        "video_id":          video_id,
        "original_video":    orig,
        "total_urls_scraped":len(all_docs),
        "fingerprinted":     len(fingerprinted),
        "pending":           len(pending),
        "failed":            len(failed),
        "flagged":           len(flagged),
        "watermark_matches": len(watermarked),
        "avg_match_score":   avg_score,
        "max_match_score":   max_score,
        "flagged_by_platform": platform_flags,
        "risk_status": (
            "critical" if watermarked or any(d.get("match_score", 0) >= 0.92 for d in flagged)
            else "high"   if any(d.get("match_score", 0) >= 0.82 for d in flagged)
            else "medium" if flagged
            else "clean"
        ),
    }


@router.post("/matches/{video_id}/report")
def generate_report(video_id: str):
    """
    Generates a structured evidence report for all flagged URLs.
    This is what you'd send to a legal/compliance team.
    """
    flagged = list(scraped_col.find(
        {"original_video_id": video_id, "flagged": True},
        {"_id": 0}
    ).sort("match_score", -1))

    orig = fingerprints_col.find_one({"video_id": video_id}, {"_id": 0, "fingerprint": 0})

    report = {
        "report_generated_at": datetime.datetime.utcnow().isoformat(),
        "original_asset": {
            "video_id":    video_id,
            "filename":    orig.get("video_path", "unknown") if orig else "unknown",
            "fingerprinted_at": orig.get("created_at", "unknown") if orig else "unknown",
        },
        "total_violations": len(flagged),
        "violations": [
            {
                "url":             d.get("url"),
                "platform":        d.get("platform"),
                "match_score":     d.get("match_score"),
                "watermark_found": d.get("watermark_found"),
                "watermark_detail":d.get("watermark_detail"),
                "scraped_at":      d.get("scraped_at"),
                "fingerprinted_at":d.get("fingerprinted_at"),
                "risk_level": (
                    "critical" if d.get("watermark_found") or (d.get("match_score") or 0) >= 0.92
                    else "high"
                ),
            }
            for d in flagged
        ],
    }

    return report