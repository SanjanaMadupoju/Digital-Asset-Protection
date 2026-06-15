"""
reports.py — Step 5+ router. Generate and deliver violation reports via email.

This completes the workflow: detection → report → action (email alert).
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from utils.scraper_db import get_all_scraped
from utils.email_service import email_service
import os

router = APIRouter()


class SendAlertRequest(BaseModel):
    """Request to send a violation alert email."""
    email: EmailStr  # Pydantic validates email format
    violation_filter: str = "all"  # "critical", "high", "all"


@router.post("/reports/{video_id}/send-email")
def send_violation_alert(video_id: str, req: SendAlertRequest):
    """
    Generate a violation report and send it via email.
    
    This is the final step that completes the action loop:
    Upload → Fingerprint → Scrape → Match → Report → Send Email
    
    Args:
        video_id: ID of the uploaded video
        req: SendAlertRequest with recipient email and filter options
    
    Returns:
        Status of email delivery
    """
    print(f"\n[Reports] Sending alert for video_id={video_id} to {req.email}")
    
    # Fetch all scraped URLs and their match results
    scraped_results = get_all_scraped(video_id)
    if not scraped_results:
        raise HTTPException(status_code=404, detail=f"No scraped data for video: {video_id}")
    
    # Extract violations (matches with sufficient score or watermark)
    violations = _extract_violations(scraped_results)
    
    if not violations:
        return {
            "success": True,
            "sent": False,
            "message": "No violations found to report",
            "video_id": video_id
        }
    
    # Get video title from uploaded metadata (or use default)
    video_title = _get_video_title(video_id)
    
    # Send email
    email_result = email_service.send_violation_alert(
        recipient_email=req.email,
        video_title=video_title,
        violations=violations,
        violation_filter=req.violation_filter
    )
    
    # Log the email delivery
    if email_result.get("sent"):
        _log_email_delivery(video_id, req.email, len(violations), req.violation_filter)
    
    return {
        "success": email_result.get("success", False),
        "sent": email_result.get("sent", False),
        "video_id": video_id,
        "recipient_email": req.email,
        "violations_count": len(violations),
        "violations_sent": len(violations),  # Could be filtered
        "filter_applied": req.violation_filter,
        "timestamp": datetime.now().isoformat(),
        "error": email_result.get("error"),
        "method": email_result.get("method"),
    }


@router.get("/reports/{video_id}")
def get_report(video_id: str):
    """
    Retrieve a violation report for a video.
    
    Returns: Summary of all matches found
    """
    scraped_results = get_all_scraped(video_id)
    if not scraped_results:
        raise HTTPException(status_code=404, detail=f"No report for video: {video_id}")
    
    violations = _extract_violations(scraped_results)
    
    # Categorize by risk level
    by_risk = {
        "critical": [v for v in violations if v.get("risk_level") == "critical"],
        "high": [v for v in violations if v.get("risk_level") == "high"],
        "medium": [v for v in violations if v.get("risk_level") == "medium"],
        "low": [v for v in violations if v.get("risk_level") == "low"],
    }
    
    return {
        "video_id": video_id,
        "report_generated_at": datetime.now().isoformat(),
        "total_violations": len(violations),
        "violations_by_risk": {
            "critical": len(by_risk["critical"]),
            "high": len(by_risk["high"]),
            "medium": len(by_risk["medium"]),
            "low": len(by_risk["low"]),
        },
        "violations": violations,
        "sample_urls": [v["url"] for v in violations[:5]],
    }


def _extract_violations(scraped_results: list) -> list[dict]:
    """
    Extract violation records from scraped results.
    A violation is a match with sufficient score or watermark detected.
    """
    violations = []
    for result in scraped_results:
        # Check if this is flagged as a violation
        if result.get("flagged"):
            violations.append({
                "url": result.get("url"),
                "title": result.get("title", "Unknown"),
                "platform": result.get("platform", "unknown"),
                "match_score": result.get("match_score", 0),
                "watermark_found": result.get("watermark_found", False),
                "watermark_detail": result.get("watermark_detail"),
                "risk_level": result.get("risk_level", "unknown"),
                "detected_at": result.get("detected_at"),
            })
    return violations


def _get_video_title(video_id: str) -> str:
    """
    Get the original video title from upload metadata.
    TODO: This would query Firestore for the video metadata.
    For now, return a generic title.
    """
    # TODO: Query Firestore collection 'uploaded_videos' with document ID = video_id
    # to get the original filename/title
    return f"Uploaded Video ({video_id})"


def _log_email_delivery(video_id: str, email: str, violation_count: int, filter_level: str):
    """
    Log that an email was delivered for audit trail.
    TODO: Save this to Firestore for tracking.
    """
    print(f"[Reports] Email sent: video_id={video_id}, email={email}, violations={violation_count}, filter={filter_level}")
