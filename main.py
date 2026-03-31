import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from routes import users, question_banks, questions, mistake, feedback, blog, school_info

app = FastAPI()

# Configure CORS middleware
# Allow origins for development environment
# In production, set FRONTEND_URL environment variable
def get_allowed_origins():
    """Get allowed origins from environment variable or use defaults."""
    frontend_url = os.getenv("FRONTEND_URL")
    default_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    if frontend_url:
        # Support multiple URLs separated by comma
        custom_origins = [url.strip() for url in frontend_url.split(",")]
        return list(set(default_origins + custom_origins))
    return default_origins

ALLOWED_ORIGINS = get_allowed_origins()

# For development: allow all origins (NOT recommended for production)
# Set ALLOW_ALL_ORIGINS=true in .env for development
if os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["User"])
app.include_router(question_banks.router, prefix="/question_banks", tags=["QuestionBank"])
app.include_router(questions.router, prefix="/upload", tags=["QuestionBank"])
app.include_router(mistake.router, tags=["MistakeNotebook"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(blog.router)
app.include_router(school_info.router)