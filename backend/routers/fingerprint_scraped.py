# """
# fingerprint_scraped.py — Step 4 router.

# Endpoint: POST /api/fingerprint-scraped/{video_id}

# For each URL in MongoDB with status "pending_fingerprint":
#   1. Download sample frames (yt-dlp / Playwright / requests)
#   2. Check for our watermark in the frames
#   3. Run CLIP → 512-dim vector
#   4. Compare against original fingerprint in Qdrant (cosine similarity)
#   5. Compare against local watermarked video fingerprint (cosine similarity)
#   6. Update MongoDB:
#        - status                  → "fingerprinted"
#        - match_score             → 0.0 to 1.0  (vs original)
#        - watermarked_match_score → 0.0 to 1.0  (vs local watermarked video)
#        - flagged                 → True if either score > threshold
#        - watermark_found         → True/False
# """

# from fastapi import APIRouter, HTTPException
# from utils.scraper_db import scraped_col, get_pending_urls
# from utils.frame_downloader import download_frames
# from utils.frame_downloader import _extract_frames_from_clip
# from utils.clip_embedder import frames_to_fingerprint
# # from utils.watermark import verify_watermark, build_watermark_text
# from utils.watermark import verify_watermark
# from utils.db import qdrant_client, fingerprints_col, COLLECTION_NAME
# from qdrant_client.models import PointStruct
# import uuid
# import datetime
# import numpy as np
# import time
# import os
# import cv2

# router = APIRouter()

# # Cosine similarity threshold — above this = flagged as a copy
# MATCH_THRESHOLD = 0.82   # slightly lower than Step 2's 0.92
#                           # because scraped frames are lower quality

# # Local watermarked video folder
# WATERMARKED_DIR = r"C:\Users\MadupojuSanjana\Documents\llm\sports-fingerprint\backend\temp_frames"


# def _cosine_similarity(vec_a: list, vec_b: list) -> float:
#     """Computes cosine similarity between two vectors. Returns 0.0 to 1.0."""
#     a = np.array(vec_a)
#     b = np.array(vec_b)
#     norm_a = np.linalg.norm(a)
#     norm_b = np.linalg.norm(b)
#     if norm_a == 0 or norm_b == 0:
#         return 0.0
#     return float(np.dot(a, b) / (norm_a * norm_b))


# def _get_original_fingerprint(video_id: str) -> list | None:
#     """Fetches the original video's fingerprint vector from MongoDB."""
#     doc = fingerprints_col.find_one({"video_id": video_id}, {"_id": 0})
#     if doc and "fingerprint" in doc:
#         print(f"path :{doc["video_path"]}")
#         return doc["fingerprint"]
#     return None

# def _get_local_watermarked_fingerprint(video_id: str):
#     watermarked_path = os.path.join(WATERMARKED_DIR, f"watermarked_{video_id}.avi")
#     if not os.path.exists(watermarked_path):
#         return None

#     cap = cv2.VideoCapture(watermarked_path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     frame_step = max(1, int(fps * 2))

#     full_res_frames = []  # for watermark checking
#     frame_number = 0

#     while True:
#         cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
#         ok, frame = cap.read()
#         if not ok:
#             break

#         full_res_frames.append(frame)                            # resized for CLIP
#         frame_number += frame_step

#     cap.release()

#     # ✅ Verify watermark on FULL RESOLUTION frames
#     watermark_result = {"verified": False, "org_match_pct": 0, "id_match_pct": 0}
#     for frame in full_res_frames[:2]:
#         wm = verify_watermark(frame, video_id)
#         if wm["verified"]:
#             watermark_result = wm
#             break
#     watermark_found = watermark_result["verified"]
#     print(f"[Step4] Watermark: {'FOUND' if watermark_found else 'not found'} "
#             f"(org={watermark_result['org_match_pct']}% "
#             f"id={watermark_result['id_match_pct']}%)")
    

# # def _get_local_watermarked_fingerprint(video_id: str):
# #     watermarked_path = os.path.join(WATERMARKED_DIR, f"watermarked_{video_id}.avi")
# #     if not os.path.exists(watermarked_path):
# #         return None

# #     cap = cv2.VideoCapture(watermarked_path)
# #     fps = cap.get(cv2.CAP_PROP_FPS)
# #     frame_step = max(1, int(fps * 2))
    
# #     print(f"FPS: {fps} | Frame step: {frame_step}")
# #     print(f"Expected watermark text: '{build_watermark_text(video_id)}'")
# #     print("-" * 60)

# #     frame_number = 0
# #     frame_count  = 0

# #     while frame_count < 5:   # check first 5 sampled frames
# #         cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
# #         ok, frame = cap.read()
# #         if not ok:
# #             break

# #         print(f"\nFrame {frame_number}:")
# #         result = verify_watermark(frame, video_id)

# #         # New watermark.py keys
# #         print(f"  Extracted text : '{result['extracted_text']}'")
# #         print(f"  Expected text  : '{result['expected_text']}'")
# #         print(f"  Org found      : {result['org_found']}")
# #         print(f"  ID found       : {result['id_found']}")
# #         print(f"  Char match     : {result['char_match_pct']}%")
# #         print(f"  Verified       : {result['verified']}")

# #         frame_number += frame_step
# #         frame_count  += 1

# #     cap.release()
# #     print("\nDone.")
    

# @router.post("/fingerprint-scraped/{video_id}")
# def fingerprint_scraped_urls(video_id: str, limit: int = 10):
#     """
#     Processes up to `limit` pending URLs for a given video_id.

#     Why limit? Each URL takes 30-120 seconds on CPU.
#     Run this multiple times to process all URLs in batches.

#     Args:
#         video_id : original video from Step 1
#         limit    : how many URLs to process in this run (default 10)
#     """

#     # 1. Get the original fingerprint to compare against
#     original_vector = _get_original_fingerprint(video_id)
#     if not original_vector:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No fingerprint found for video_id: {video_id}. Complete Step 2 first."
#         )

#     # 1b. Load local watermarked video fingerprint (once, before the loop)
#     _get_local_watermarked_fingerprint(video_id)
#     # watermarked_vector = _get_local_watermarked_fingerprint(video_id)
#     # if watermarked_vector:
#     #     print(f"[Step4] Local watermarked fingerprint loaded ✅")
#     # else:
#     #     print(f"[Step4] No local watermarked video found — skipping watermarked comparison")

#     # 2. Get pending URLs from MongoDB
#     pending = get_pending_urls(video_id, limit=limit)
#     if not pending:
#         raise HTTPException(
#             status_code=404,
#             detail=f"No pending URLs for video_id: {video_id}. Run Step 3 (scraper) first."
#         )

#     print(f"\n[Step4] Processing {len(pending)} URLs for video_id: {video_id}")

#     results = {
#         "processed": 0,
#         "failed":    0,
#         "flagged":   0,
#         "details":   []
#     }

#     for item in pending:
#         url      = item.get("url", "")
#         platform = item.get("platform", "unknown")

#         print(f"\n[Step4] Processing: {url[:70]}...")

#         result_entry = {
#             "url":                    url,
#             "platform":               platform,
#             "status":                 "failed",
#             "match_score":            None,
#             "watermarked_match_score": None,
#             "flagged":                False,
#             "watermark_found":        False,
#             "error":                  None,
#         }

#         try:
#             # Download frames from this URL
#             frames = download_frames(url, platform)

#             # If YouTube rate-limited → fall back to og:image thumbnail
#             if not frames and platform == "youtube":
#                 print(f"[Step4] YouTube rate-limited, trying og:image fallback...")
#                 from utils.frame_downloader import get_frames_requests
#                 frames = get_frames_requests(url)

#             if not frames:
#                 print(f"[Step4] No frames downloaded for: {url[:50]}")
#                 result_entry["error"] = "No frames could be downloaded"
#                 results["failed"] += 1
#                 scraped_col.update_one(
#                     {"url": url},
#                     {"$set": {"status": "failed", "error": "no_frames"}}
#                 )
#                 results["details"].append(result_entry)
#                 continue

#             # 4. Check for our watermark in the frames
#             watermark_result = {"verified": False, "org_match_pct": 0, "id_match_pct": 0}
#             for frame in frames[:2]:   # check first 2 frames only (faster)
#                 wm = verify_watermark(frame, video_id)
#                 if wm["verified"]:
#                     watermark_result = wm
#                     break

#             watermark_found = watermark_result["verified"]
#             print(f"[Step4] Watermark: {'FOUND' if watermark_found else 'not found'} "
#                   f"(org={watermark_result['org_match_pct']}% "
#                   f"id={watermark_result['id_match_pct']}%)")

#             # 5. Generate CLIP fingerprint for scraped frames
#             scraped_vector = frames_to_fingerprint(frames)
#             if not scraped_vector:
#                 result_entry["error"] = "CLIP embedding failed"
#                 results["failed"] += 1
#                 results["details"].append(result_entry)
#                 continue

#             # 6. Cosine similarity against original
#             score = _cosine_similarity(original_vector, scraped_vector)

#             # 6b. Cosine similarity against local watermarked video
#             # watermarked_score = None
#             # if watermarked_vector:
#             #     watermarked_score = _cosine_similarity(watermarked_vector, scraped_vector)
#             #     print(f"[Step4] Watermarked video match score: {watermarked_score:.4f}")

#             flagged = (
#                 score >= MATCH_THRESHOLD
#             )

#             print(f"[Step4] Original score: {score:.4f} | "
#                   f"Threshold: {MATCH_THRESHOLD} | "
#                   f"Flagged: {flagged}")

#             # 7. Save scraped vector to Qdrant for future searches
#             try:
#                 qdrant_client.upsert(
#                     collection_name=COLLECTION_NAME,
#                     points=[PointStruct(
#                         id=str(uuid.uuid4()),
#                         vector=scraped_vector,
#                         payload={
#                             "video_id":               video_id,
#                             "url":                    url,
#                             "platform":               platform,
#                             "match_score":            score,
#                             "watermarked_match_score": 0,
#                             "flagged":                flagged,
#                             "watermark_found":        watermark_found,
#                             "source":                 "scraped",
#                             "created_at":             datetime.datetime.utcnow().isoformat(),
#                         }
#                     )]
#                 )
#             except Exception as qe:
#                 print(f"[Step4] Qdrant save warning: {qe}")

#             # 8. Update MongoDB status
#             watermarked_score = None
#             scraped_col.update_one(
#                 {"url": url},
#                 {"$set": {
#                     "status":                   "fingerprinted",
#                     "match_score":              round(score, 4),
#                     "watermarked_match_score":  round(watermarked_score, 4) if watermarked_score is not None else None,
#                     "flagged":                  flagged,
#                     "watermark_found":          watermark_found,
#                     "watermark_detail":         watermark_result,
#                     "n_frames":                 len(frames),
#                     "fingerprinted_at":         datetime.datetime.utcnow().isoformat(),
#                 }}
#             )

#             result_entry.update({
#                 "status":                  "fingerprinted",
#                 "match_score":             round(score, 4),
#                 "watermarked_match_score": round(watermarked_score, 4) if watermarked_score is not None else None,
#                 "flagged":                 flagged,
#                 "watermark_found":         watermark_found,
#             })

#             results["processed"] += 1
#             if flagged:
#                 results["flagged"] += 1

#         except Exception as e:
#             print(f"[Step4] Unexpected error for {url}: {e}")
#             result_entry["error"] = str(e)
#             results["failed"] += 1
#             scraped_col.update_one(
#                 {"url": url},
#                 {"$set": {"status": "failed", "error": str(e)}}
#             )

#         results["details"].append(result_entry)

#         # Wait between URLs to avoid YouTube rate limiting
#         if platform in ["youtube", "dailymotion"]:
#             print(f"[Step4] Sleeping 5s before next URL (YouTube rate limit protection)...")
#             time.sleep(5)
#         else:
#             time.sleep(1)

#     # Summary
#     flagged_urls = [d for d in results["details"] if d["flagged"]]

#     return {
#         "success":        True,
#         "video_id":       video_id,
#         "processed":      results["processed"],
#         "failed":         results["failed"],
#         "flagged_count":  results["flagged"],
#         "match_threshold":MATCH_THRESHOLD,
#         "flagged_urls":   flagged_urls,
#         "all_results":    results["details"],
#         "next_step":      "View results at GET /api/matches/{video_id} (Step 5 dashboard)"
#     }


# @router.get("/fingerprint-scraped/{video_id}/summary")
# def get_summary(video_id: str):
#     """Quick summary of all processed URLs for a video."""
#     all_docs = list(scraped_col.find(
#         {"original_video_id": video_id},
#         {"_id": 0, "url": 1, "platform": 1, "status": 1,
#          "match_score": 1, "watermarked_match_score": 1, "flagged": 1, "watermark_found": 1}
#     ))

#     if not all_docs:
#         raise HTTPException(status_code=404, detail=f"No data for video_id: {video_id}")

#     flagged   = [d for d in all_docs if d.get("flagged")]
#     pending   = [d for d in all_docs if d.get("status") == "pending_fingerprint"]
#     processed = [d for d in all_docs if d.get("status") == "fingerprinted"]
#     failed    = [d for d in all_docs if d.get("status") == "failed"]

#     return {
#         "video_id":   video_id,
#         "total_urls": len(all_docs),
#         "pending":    len(pending),
#         "processed":  len(processed),
#         "failed":     len(failed),
#         "flagged":    len(flagged),
#         "flagged_urls": flagged,
#     }
  

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