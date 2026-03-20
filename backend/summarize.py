import io
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import pdfplumber
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from .auth import get_current_user
from .models import User, SummaryLog
from .database import get_db

router = APIRouter()

# ── Sumy config ───────────────────────────────────────────────────────────────
LANGUAGE        = "english"
MAX_INPUT_CHARS = 1800   # fixed window — same as before so the UI stat still makes sense
SUMMARY_SENTENCES = 5    # number of sentences to extract
# ─────────────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t.strip())
    return "\n".join(text_parts)


def summarize_text(text: str) -> str:
    truncated = text[:MAX_INPUT_CHARS]
    parser = PlaintextParser.from_string(truncated, Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)
    summarizer = LsaSummarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)
    sentences = summarizer(parser.document, SUMMARY_SENTENCES)
    return " ".join(str(s) for s in sentences)


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
