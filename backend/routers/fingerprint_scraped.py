"""
fingerprint_scraped.py — Step 4 router. Now saves to Firestore instead of MongoDB.
"""

from fastapi import APIRouter, HTTPException
from utils.scraper_db import get_pending_urls, update_url_status, get_all_scraped
from utils.frame_downloader import download_frames
from utils.clip_embedder import frames_to_fingerprint
from utils.watermark import verify_watermark
from utils.firebase_init import fingerprints_ref
from utils.db import qdrant_client, COLLECTION_NAME
from qdrant_client.models import PointStruct
import uuid, datetime, time
import numpy as np

router = APIRouter()
MATCH_THRESHOLD = 0.82


def _cosine_similarity(a: list, b: list) -> float:
    va, vb = np.array(a), np.array(b)
    na, nb = np.linalg.norm(va), np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(va, vb) / (na * nb))


def _get_original_fingerprint(video_id: str) -> list | None:
    """Gets the full 512-dim fingerprint from Firestore sub-collection."""
    try:
        doc = fingerprints_ref.document(video_id)\
                               .collection("vectors")\
                               .document("full").get()
        if doc.exists:
            return doc.to_dict().get("fingerprint")
    except Exception as e:
        print(f"[Firestore] Error fetching fingerprint: {e}")
    return None


@router.post("/fingerprint-scraped/{video_id}")
def fingerprint_scraped_urls(video_id: str, limit: int = 10):
    original_vector = _get_original_fingerprint(video_id)
    if not original_vector:
        raise HTTPException(status_code=404, detail=f"No fingerprint for: {video_id}. Run Step 2 first.")

    pending = get_pending_urls(video_id, limit=limit)
    if not pending:
        raise HTTPException(status_code=404, detail=f"No pending URLs for: {video_id}. Run Step 3 first.")

    print(f"\n[Step4] Processing {len(pending)} URLs for: {video_id}")
    results = {"processed": 0, "failed": 0, "flagged": 0, "details": []}

    for item in pending:
        url      = item.get("url", "")
        platform = item.get("platform", "unknown")
        print(f"\n[Step4] URL: {url[:70]}")

        entry = {
            "url": url, "platform": platform,
            "status": "failed", "match_score": None,
            "flagged": False, "watermark_found": False, "error": None,
        }

        try:
            # Download frames (full_res for watermark, clip for CLIP)
            # full_res_frames, clip_frames = download_frames(url, platform)
            frames = download_frames(url, platform)

            if not frames:
                if platform == "youtube":
                    from utils.frame_downloader import get_frames_requests
                    # full_res_r, clip_r = get_frames_requests(url)
                    frames = get_frames_requests(url)
                    if not frames:
                        print(f"[Step4] No frames downloaded for: {url[:50]}")
                        entry["error"] = "No frames could be downloaded"
                        entry["failed"] += 1
                        update_url_status(url, {"status": "failed", "error": "no_frames"})
                        results["details"].append(entry)
                        continue
                    # full_res_frames, clip_frames = full_res_r, clip_r

            # if not clip_frames:
            #     entry["error"] = "No frames downloaded"
            #     entry["failed"] += 1
            #     update_url_status(url, {"status": "failed", "error": "no_frames"})
            #     results["details"].append(entry)
            #     continue

            # Watermark check on full resolution
            wm_result = {"verified": False, "org_found": False,
                         "id_found": False, "char_match_pct": 0, "extracted_text": ""}
            for frame in frames[:3]:
                wm = verify_watermark(frame, video_id)
                if wm["verified"]:
                    wm_result = wm
                    break
                if wm.get("char_match_pct", 0) > wm_result.get("char_match_pct", 0):
                    wm_result = wm

            watermark_found = wm_result["verified"]
            print(f"[Step4] Watermark: {'FOUND' if watermark_found else 'not found'} | "
                  f"extracted='{wm_result.get('extracted_text','')}' | "
                  f"match={wm_result.get('char_match_pct',0)}%")

            # CLIP fingerprint
            scraped_vector = frames_to_fingerprint(frames)
            if not scraped_vector:
                entry["error"] = "CLIP embedding failed"
                results["failed"] += 1
                results["details"].append(entry)
                continue

            # Cosine similarity
            score   = _cosine_similarity(original_vector, scraped_vector)
            flagged = score >= MATCH_THRESHOLD or watermark_found
            print(f"[Step4] Score={score:.4f} | Flagged={flagged}")

            timestamp = datetime.datetime.utcnow().isoformat()

            # Save to Qdrant
            try:
                qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=[PointStruct(
                        id=str(uuid.uuid4()),
                        vector=scraped_vector,
                        payload={
                            "video_id": video_id, "url": url,
                            "platform": platform, "match_score": score,
                            "flagged": flagged, "watermark_found": watermark_found,
                            "source": "scraped", "created_at": timestamp,
                        }
                    )]
                )
            except Exception as qe:
                print(f"[Qdrant] Warning: {qe}")

            # Update Firestore
            update_url_status(url, {
                "status":            "fingerprinted",
                "match_score":       round(score, 4),
                "flagged":           flagged,
                "watermark_found":   watermark_found,
                "watermark_detail":  wm_result,
                "n_frames":          len(frames),
                "fingerprinted_at":  timestamp,
            })

            entry.update({
                "status":          "fingerprinted",
                "match_score":     round(score, 4),
                "flagged":         flagged,
                "watermark_found": watermark_found,
                "watermark_text":  wm_result.get("extracted_text", ""),
            })
            results["processed"] += 1
            if flagged:
                results["flagged"] += 1

        except Exception as e:
            print(f"[Step4] Error: {e}")
            entry["error"] = str(e)
            results["failed"] += 1
            update_url_status(url, {"status": "failed", "error": str(e)})

        results["details"].append(entry)
        time.sleep(5 if platform in ["youtube", "dailymotion"] else 1)

    flagged_urls = [d for d in results["details"] if d["flagged"]]
    return {
        "success":         True,
        "video_id":        video_id,
        "processed":       results["processed"],
        "failed":          results["failed"],
        "flagged_count":   results["flagged"],
        "match_threshold": MATCH_THRESHOLD,
        "flagged_urls":    flagged_urls,
        "all_results":     results["details"],
    }


@router.get("/fingerprint-scraped/{video_id}/summary")
def get_summary(video_id: str):
    docs = get_all_scraped(video_id)
    if not docs:
        raise HTTPException(status_code=404, detail=f"No data for: {video_id}")
    return {
        "video_id":   video_id,
        "total":      len(docs),
        "pending":    sum(1 for d in docs if d.get("status") == "pending_fingerprint"),
        "processed":  sum(1 for d in docs if d.get("status") == "fingerprinted"),
        "failed":     sum(1 for d in docs if d.get("status") == "failed"),
        "flagged":    sum(1 for d in docs if d.get("flagged")),
        "flagged_urls": [d for d in docs if d.get("flagged")],
    }