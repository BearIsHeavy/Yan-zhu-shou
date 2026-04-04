import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from routes import users, question_banks, questions, mistake, feedback, blog, school_info

# Import AI analysis module routes
from knowledge.routes.knowledge import router as knowledge_router
from books.routes.books import router as books_router
from reports.routes.reports import router as reports_router
from rag.routes.rag import router as rag_router

from database import engine


# ==========================================
# Logging configuration
# ==========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)-7s | %(name)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ==========================================
# Application lifespan
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    logger.info("Starting YanZhuShou server")
    logger.info("Database engine initialized")

    yield

    # Shutdown
    logger.info("Shutting down YanZhuShou server")
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(lifespan=lifespan)

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
ALLOW_ALL = os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true"
if ALLOW_ALL:
    ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    # CORS spec: '*' with credentials is invalid — disable credentials when using '*'
    allow_credentials=not ALLOW_ALL,
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

# AI Analysis Module Routes
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(books_router, prefix="/api/books", tags=["Books"])
app.include_router(reports_router, prefix="/api/reports", tags=["Analysis Reports"])

# RAG Module Routes
app.include_router(rag_router, prefix="/api/rag", tags=["RAG"])


# ==========================================
# Health check endpoint
# ==========================================
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for infrastructure monitoring."""
    return {"status": "healthy"}