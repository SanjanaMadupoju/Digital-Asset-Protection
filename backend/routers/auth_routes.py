# routes/auth_routes.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
from auth import hash_password, verify_password, create_access_token, decode_token

# To (if auth.py is in the parent/backend folder):
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import hash_password, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

# ── DB connection (reuse your existing client if you have one) ──
client = MongoClient("mongodb://localhost:27017")
db = client["sports_fingerprint"]
users_col = db["users"]

# ── Schemas ──
class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ── Routes ──
@router.post("/register")
def register(body: RegisterRequest):
    if users_col.find_one({"email": body.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    users_col.insert_one({
        "username": body.username,
        "email": body.email,
        "password": hash_password(body.password),
    })
    return {"message": "User created successfully"}

@router.post("/login")
def login(body: LoginRequest):
    user = users_col.find_one({"email": body.email})
    if not user or not verify_password(body.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    return {"access_token": token, "token_type": "bearer", "username": user["username"]}

# ── Dependency: protect any route ──
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload