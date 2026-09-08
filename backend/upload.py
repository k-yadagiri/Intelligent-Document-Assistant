"""
upload.py
Handles saving uploaded files to disk and extracting raw text
from PDF / DOCX / TXT so it can later be chunked and embedded
(that part comes in Module 3 - RAG Pipeline).
"""

import os
import uuid

from fastapi import UploadFile, HTTPException
from PyPDF2 import PdfReader
from docx import Document as DocxDocument

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def save_upload_file(file: UploadFile, user_id: int) -> str:
    """
    Saves the uploaded file to disk with a unique name (so two users
    uploading 'resume.pdf' don't overwrite each other) and returns
    the path it was saved to.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    unique_name = f"user{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, unique_name)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    return filepath


def extract_text(filepath: str) -> str:
    """
    Reads a PDF, DOCX, or TXT file from disk and returns its plain
    text content. This raw text is what gets chunked + embedded
    in Module 3.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        return _extract_from_pdf(filepath)
    elif ext == ".docx":
        return _extract_from_docx(filepath)
    elif ext == ".txt":
        return _extract_from_txt(filepath)
    else:
        raise HTTPException(status_code=400, detail=f"Cannot extract text from '{ext}' files")


def _extract_from_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    text = "\n".join(text_parts)
    if not text.strip():
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in PDF (it may be a scanned/image-only PDF)",
        )
    return text


def _extract_from_docx(filepath: str) -> str:
    doc = DocxDocument(filepath)
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not text.strip():
        raise HTTPException(status_code=422, detail="No extractable text found in DOCX")
    return text


def _extract_from_txt(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    if not text.strip():
        raise HTTPException(status_code=422, detail="TXT file is empty")
    return text
