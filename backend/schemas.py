"""
schemas.py
Pydantic models used for request validation and response shaping.
Kept separate from models.py (ORM) on purpose: the API contract
(schemas) and the DB structure (models) are allowed to evolve
independently — e.g. we never want to accidentally return
hashed_password in an API response just because it's a column on User.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------- Auth ----------

class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Documents ----------

class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    filename: str
    uploaded_at: datetime


# ---------- Chat ----------

class ChatRequest(BaseModel):
    document_id: int
    question: str


class ChatResponse(BaseModel):
    answer: str
    document_id: int


class ChatHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_id: int
    question: str
    answer: str
    timestamp: datetime
