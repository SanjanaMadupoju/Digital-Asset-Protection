from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, fingerprint, scraper, fingerprint_scraped, matches, watermarked
from utils.db import ensure_qdrant_collection
import os

app = FastAPI(
    title="Sports Video Fingerprint API",
    version="6.0.0",
    description="Firebase + Qdrant | Steps 1-6"
)


ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# os.makedirs("uploads", exist_ok=True)
# os.makedirs("temp_frames", exist_ok=True)

@app.on_event("startup")
def startup():
    try:
        ensure_qdrant_collection()
    except Exception as e:
        print(f"[Startup] Qdrant unavailable: {e} — will retry on requests")

app.include_router(upload.router,              prefix="/api", tags=["Step 1 - Upload"])
app.include_router(fingerprint.router,         prefix="/api", tags=["Step 2 - Fingerprint"])
app.include_router(watermarked.router, prefix="/api", tags=["Watermarked Video"])
app.include_router(scraper.router,             prefix="/api", tags=["Step 3 - Scrape"])
app.include_router(fingerprint_scraped.router, prefix="/api", tags=["Step 4 - Fingerprint Scraped"])
app.include_router(matches.router,             prefix="/api", tags=["Step 5 - Matches"])

@app.get("/")
def root():
    return {
        "status":  "Sports Fingerprint API running",
        "version": "6.0.0",
        "storage": {"metadata": "Firebase Firestore", "vectors": "Qdrant Cloud"}
    }