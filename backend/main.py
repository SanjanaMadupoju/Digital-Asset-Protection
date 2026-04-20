# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from routers import upload, fingerprint, scraper, fingerprint_scraped, matches, auth_routes
# from utils.db import ensure_qdrant_collection
# import os

# app = FastAPI(
#     title="Sports Video Fingerprint API",
#     version="5.0.0",
#     description="Step 1-5: Upload | Fingerprint | Scrape | Fingerprint Scraped | Matches"
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:5173"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# os.makedirs("uploads", exist_ok=True)
# os.makedirs("temp_frames", exist_ok=True)

# @app.on_event("startup")
# def startup():
#     ensure_qdrant_collection()

# app.include_router(auth_routes.router,         prefix="/api", tags=["Auth"])
# app.include_router(upload.router,              prefix="/api", tags=["Step 1 - Upload"])
# app.include_router(fingerprint.router,         prefix="/api", tags=["Step 2 - Fingerprint"])
# app.include_router(scraper.router,             prefix="/api", tags=["Step 3 - Scrape"])
# app.include_router(fingerprint_scraped.router, prefix="/api", tags=["Step 4 - Fingerprint Scraped"])
# app.include_router(matches.router,             prefix="/api", tags=["Step 5 - Matches"])

# @app.get("/")
# def root():
#     return {"status": "Sports Fingerprint API running", "version": "5.0.0"} 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, fingerprint, scraper, fingerprint_scraped, matches
from utils.db import ensure_qdrant_collection
import os

app = FastAPI(
    title="Sports Video Fingerprint API",
    version="6.0.0",
    description="Firebase + Qdrant | Steps 1-6"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("temp_frames", exist_ok=True)

@app.on_event("startup")
def startup():
    ensure_qdrant_collection()

app.include_router(upload.router,              prefix="/api", tags=["Step 1 - Upload"])
app.include_router(fingerprint.router,         prefix="/api", tags=["Step 2 - Fingerprint"])
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