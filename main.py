from fastapi import FastAPI, Depends, HTTPException, status

from routes import users, question_banks, questions

app = FastAPI()

# app.include_router(users.router, prefix="/users", tags=["User"])
# app.include_router(question_banks.router, prefix="/question_banks", tags=["QuestionBank"])
app.include_router(questions.router, prefix="/upload", tags=["QuestionBank"])
# ==================== QuestionBank Endpoints ====================
