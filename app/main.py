from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, get_db, redis_client
from . import models
from .routers import auth, users, wrong_questions, reviews

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Yan-zhu-shou API",
    description="Backend API for the Smart Error Book application.",
    version="1.1.0"
)

# --- CORS CONFIGURATION ---
origins: list[str] = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SYSTEM ROUTES ---
@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    redis_status = "connected" if redis_client.ping() else "disconnected"
    return {"status": "healthy", "database": "connected", "redis": redis_status}

# --- INCLUDE ROUTERS ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(wrong_questions.router)
app.include_router(reviews.router)