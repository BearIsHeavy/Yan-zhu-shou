from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from routes import users, question_banks, questions

app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router, prefix="/users", tags=["User"])
app.include_router(question_banks.router, prefix="/question_banks", tags=["QuestionBank"])
app.include_router(questions.router, prefix="/upload", tags=["QuestionBank"])
# ==================== QuestionBank Endpoints ====================
