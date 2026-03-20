from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SummaryLog(Base):
    """Optional: log summaries for audit/history"""
    __tablename__ = "summary_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False)
    filename = Column(String(255))
    char_count = Column(Integer)
    summary_length = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
