"""
db.py — Central database connections.

MongoDB  : local (localhost:27017)
Qdrant   : cloud (paste your URL and API key below)

Note on verify=False:
  Corporate networks use SSL inspection (a proxy that re-signs certificates).
  Python's SSL library can't verify these re-signed certs by default.
  verify=False bypasses that check — safe to use on a trusted office network.
"""

import warnings
import urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os

# ─── MongoDB (local) ──────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB  = "sports_fingerprint"

mongo_client     = MongoClient(MONGO_URL)
db               = mongo_client[MONGO_DB]
videos_col       = db["videos"]
fingerprints_col = db["fingerprints"]
users_col = db["users"]

# ─── Qdrant (cloud) ───────────────────────────────────────────────────────────
# Replace these two values with your actual Qdrant cloud credentials
# Get them from: https://cloud.qdrant.io -> your cluster -> API Keys tab
QDRANT_URL     = os.getenv("QDRANT_URL",     "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

COLLECTION_NAME = "video_fingerprints"
VECTOR_SIZE     = 512

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    https=True,
    verify=False,   # needed for corporate SSL inspection proxies
    check_compatibility=False,  # suppresses the version mismatch warning
)


def ensure_qdrant_collection():
    """
    Creates the Qdrant collection if it does not already exist.
    Called once on backend startup.
    """
    try:
        existing = [c.name for c in qdrant_client.get_collections().collections]
        if COLLECTION_NAME not in existing:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                )
            )
            print(f"[Qdrant] Collection created: {COLLECTION_NAME}")
        else:
            print(f"[Qdrant] Collection already exists: {COLLECTION_NAME}")
    except Exception as e:
        print(f"[Qdrant] WARNING: Could not connect to Qdrant on startup: {e}")
        print("[Qdrant] Check your QDRANT_URL and QDRANT_API_KEY in utils/db.py")
        # Don't crash the whole server — Qdrant error is reported per-request