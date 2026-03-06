from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from routes import users, question_banks, questions

app = FastAPI()

# CORS middleware configuration for frontend-backend development
# Allows the frontend (e.g., React/Vite) to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Create React App default
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,  # Allow cookies and auth headers
    allow_methods=["*"],     # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allow all headers
)

app.include_router(users.router, prefix="/users", tags=["User"])
app.include_router(question_banks.router, prefix="/question_banks", tags=["QuestionBank"])
app.include_router(questions.router, prefix="/upload", tags=["QuestionBank"])
# ==================== QuestionBank Endpoints ====================
