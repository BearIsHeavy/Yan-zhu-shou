# filepath: app/main.py
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import engine, Base, get_db, redis_client
from . import models
from .routers import auth, users, questions

# from .routers import errors # Temporarily commented out until errors.py is updated to the new schema

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Question Bank API",
    description="Scalable API documentation for user authentication and management.",
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
    try:
        redis_status = "connected" if redis_client.ping() else "disconnected"
    except Exception:
        redis_status = "disconnected"

    return {"status": "healthy", "database": "connected", "redis": redis_status}


# --- INCLUDE ROUTERS ---
# Plug the modular routers into the main app.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(questions.router)
# app.include_router(errors.router) # Uncomment once errors.py is updated

if __name__ == "__main__":
    # This block allows you to run the project directly using: python -m app.main
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)