# app/schemas/question.py
from pydantic import BaseModel
from typing import Optional, Any


class QuestionUploadResponse(BaseModel):
    status: str
    inserted_records: int