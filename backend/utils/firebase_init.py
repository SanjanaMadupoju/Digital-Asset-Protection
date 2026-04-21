import firebase_admin
from firebase_admin import credentials, firestore
import os

SERVICE_ACCOUNT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "firebase-service-account.json"
)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(SERVICE_ACCOUNT_PATH)

if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.abspath(SERVICE_ACCOUNT_PATH))
    firebase_admin.initialize_app(cred)
    print("[Firebase] Initialised successfully")

firestore_db = firestore.client()

videos_ref       = firestore_db.collection("videos")
fingerprints_ref = firestore_db.collection("fingerprints")
scraped_urls_ref = firestore_db.collection("scraped_urls")
reports_ref      = firestore_db.collection("reports")

def get_video(video_id: str) -> dict | None:
    doc = videos_ref.document(video_id).get()
    return doc.to_dict() if doc.exists else None

def set_video(video_id: str, data: dict):
    videos_ref.document(video_id).set(data, merge=True)

def get_fingerprint(video_id: str) -> dict | None:
    doc = fingerprints_ref.document(video_id).get()
    return doc.to_dict() if doc.exists else None

def set_fingerprint(video_id: str, data: dict):
    fingerprints_ref.document(video_id).set(data, merge=True)

def get_scraped_urls(video_id: str, status: str = None) -> list[dict]:
    query = scraped_urls_ref.where("original_video_id", "==", video_id)
    if status:
        query = query.where("status", "==", status)
    return [doc.to_dict() | {"_doc_id": doc.id} for doc in query.stream()]

def save_scraped_url(data: dict) -> str:
    import hashlib
    doc_id = hashlib.md5(data["url"].encode()).hexdigest()
    ref = scraped_urls_ref.document(doc_id)
    if not ref.get().exists:
        ref.set(data)
        return "saved"
    return "duplicate"

def update_scraped_url(url: str, updates: dict):
    import hashlib
    doc_id = hashlib.md5(url.encode()).hexdigest()
    scraped_urls_ref.document(doc_id).update(updates)