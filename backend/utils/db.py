import warnings
import urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
import os

QDRANT_URL     = os.getenv("QDRANT_URL",     "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

COLLECTION_NAME = "video_fingerprints"
VECTOR_SIZE     = 1408   # Google Vision AI embedding size

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    https=True,
    verify=False,
    check_compatibility=False,
)


def ensure_qdrant_collection():
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
            print(f"[Qdrant] Collection created: {COLLECTION_NAME} (1408-dim)")
        else:
            print(f"[Qdrant] Collection exists: {COLLECTION_NAME}")
    except Exception as e:
        print(f"[Qdrant] WARNING: {e}")