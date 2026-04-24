"""
matches.py — Step 5 router. Reads from Firestore instead of MongoDB.
"""

from fastapi import APIRouter, HTTPException
from utils.scraper_db import get_all_scraped
from utils.firebase_init import get_fingerprint, reports_ref
import datetime

router = APIRouter()


def _enrich(doc: dict) -> dict:
    score = doc.get("match_score") or 0
    wm    = doc.get("watermark_found", False)
    if wm and score >= 0.92:
        doc["risk_level"] = "critical"
        doc["risk_label"] = "Confirmed copy — watermark or very high similarity"
    elif wm and score >= 0.82:
        doc["risk_level"] = "high"
        doc["risk_label"] = "Very likely unauthorized copy"
    elif score >= 0.65:
        doc["risk_level"] = "medium"
        doc["risk_label"] = "Possible copy — manual review recommended"
    else:
        doc["risk_level"] = "low"
        doc["risk_label"] = "No significant match"
    return doc


@router.get("/matches/{video_id}")
def get_matches(video_id: str, min_score: float = 0.0, flagged_only: bool = False):
    all_docs = get_all_scraped(video_id)
    docs = [d for d in all_docs if d.get("status") == "fingerprinted"]

    if flagged_only:
        docs = [d for d in docs if d.get("flagged")]
    if min_score > 0:
        docs = [d for d in docs if (d.get("match_score") or 0) >= min_score]
    if not docs:
        raise HTTPException(status_code=404, detail=f"No fingerprinted results for: {video_id}")

    docs = sorted(docs, key=lambda d: d.get("match_score") or 0, reverse=True)
    docs = [_enrich(d) for d in docs]

    return {
        "video_id": video_id,
        "total":    len(docs),
        "flagged":  sum(1 for d in docs if d.get("flagged")),
        "results":  docs,
    }


@router.get("/matches/{video_id}/summary")
def get_summary(video_id: str):
    all_docs = get_all_scraped(video_id)
    if not all_docs:
        raise HTTPException(status_code=404, detail=f"No data for: {video_id}")

    fingerprinted = [d for d in all_docs if d.get("status") == "fingerprinted"]
    flagged       = [d for d in all_docs if d.get("flagged")]
    pending       = [d for d in all_docs if d.get("status") == "pending_fingerprint"]
    failed        = [d for d in all_docs if d.get("status") == "failed"]
    watermarked   = [d for d in all_docs if d.get("watermark_found")]

    scores    = [d["match_score"] for d in fingerprinted if d.get("match_score") is not None]
    avg_score = round(sum(scores) / len(scores), 4) if scores else 0
    max_score = round(max(scores), 4) if scores else 0

    platform_flags = {}
    for d in flagged:
        p = d.get("platform", "unknown")
        platform_flags[p] = platform_flags.get(p, 0) + 1

    orig = get_fingerprint(video_id)

    return {
        "video_id":            video_id,
        "original_video":      orig,
        "total_urls_scraped":  len(all_docs),
        "fingerprinted":       len(fingerprinted),
        "pending":             len(pending),
        "failed":              len(failed),
        "flagged":             len(flagged),
        "watermark_matches":   len(watermarked),
        "avg_match_score":     avg_score,
        "max_match_score":     max_score,
        "flagged_by_platform": platform_flags,
        "risk_status": (
            "critical" if watermarked or any((d.get("match_score") or 0) >= 0.92 for d in flagged)
            else "high"   if any((d.get("match_score") or 0) >= 0.82 for d in flagged)
            else "medium" if flagged
            else "clean"
        ),
    }


@router.post("/matches/{video_id}/report")
def generate_report(video_id: str):
    all_docs = get_all_scraped(video_id)
    flagged  = sorted(
        [d for d in all_docs if d.get("flagged")],
        key=lambda d: d.get("match_score") or 0, reverse=True
    )
    orig = get_fingerprint(video_id)
    timestamp = datetime.datetime.utcnow().isoformat()

    report = {
        "report_generated_at": timestamp,
        "original_asset": {
            "video_id":        video_id,
            "filename":        orig.get("video_path", "unknown") if orig else "unknown",
            "fingerprinted_at":orig.get("created_at", "unknown") if orig else "unknown",
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

    # Save report to Firestore
    reports_ref.add({**report, "video_id": video_id})
    print(f"[Firestore] Report saved for: {video_id}")

    return report