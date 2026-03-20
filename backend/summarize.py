import io
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pdfplumber
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

from .auth import get_current_user
from .models import User, SummaryLog
from .database import get_db

router = APIRouter()

# ── T5-small config ──────────────────────────────────────────────────────────
MODEL_NAME = "t5-small"
# T5-small has a 512-token input limit. We stay well under that.
MAX_INPUT_CHARS = 1800   # ~450 tokens worth of chars — safe window for t5-small
MAX_NEW_TOKENS  = 200    # summary output length cap
# ─────────────────────────────────────────────────────────────────────────────

# Load model once at module import (cached after first cold start)
print("[model] Loading T5-small…")
tokenizer = T5Tokenizer.from_pretrained(MODEL_NAME)
model     = T5ForConditionalGeneration.from_pretrained(MODEL_NAME)
model.eval()
print("[model] T5-small ready.")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract plain text from a PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t.strip())
    return "\n".join(text_parts)


def summarize_text(text: str) -> str:
    """Run T5-small summarization on text (truncated to MAX_INPUT_CHARS)."""
    # Truncate to the fixed window
    truncated = text[:MAX_INPUT_CHARS]

    # T5 expects the "summarize: " prefix
    input_text = "summarize: " + truncated

    inputs = tokenizer.encode(
        input_text,
        return_tensors="pt",
        max_length=512,
        truncation=True
    )

    with torch.no_grad():
        summary_ids = model.generate(
            inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            num_beams=4,
            early_stopping=True
        )

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary


@router.post("/summarize")
async def summarize_pdf(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB hard limit
        raise HTTPException(status_code=413, detail="File too large. Max 10 MB.")

    # Extract text
    try:
        raw_text = extract_text_from_pdf(file_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {str(e)}")

    if not raw_text.strip():
        raise HTTPException(status_code=422, detail="PDF appears to have no extractable text (scanned image PDFs not supported).")

    # Summarize
    try:
        summary = summarize_text(raw_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

    # Log to DB
    log = SummaryLog(
        username=current_user.username,
        filename=file.filename,
        char_count=len(raw_text),
        summary_length=len(summary)
    )
    db.add(log)
    db.commit()

    return {
        "filename": file.filename,
        "extracted_chars": len(raw_text),
        "window_used_chars": min(len(raw_text), MAX_INPUT_CHARS),
        "window_limit_chars": MAX_INPUT_CHARS,
        "truncated": len(raw_text) > MAX_INPUT_CHARS,
        "summary": summary
    }
