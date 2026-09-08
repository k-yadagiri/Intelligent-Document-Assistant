"""
database.py
Sets up the SQLite database connection and session handling using SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./document_assistant.db"

# check_same_thread=False is needed only for SQLite, since FastAPI can
# use the same session across threads (each request gets a fresh
# session anyway via the dependency below).
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and guarantees it's
    closed after the request finishes, even if an exception is raised.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
