from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from .database import engine, Base
from .auth import router as auth_router
from .summarize import router as summarize_router
from .models import User
from .seed import seed_users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables and seed users on startup
    Base.metadata.create_all(bind=engine)
    seed_users()
    yield

app = FastAPI(
    title="PDF Summarizer API",
    description="Upload a PDF and get an AI-generated summary using T5",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In prod, restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(summarize_router, prefix="/api", tags=["summarize"])

@app.get("/")
def root():
    return {"message": "PDF Summarizer API is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
