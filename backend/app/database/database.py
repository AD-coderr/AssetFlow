import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Resolve the default DB next to the backend/ folder so it doesn't depend on
# the directory uvicorn is started from. Override with ASSETFLOW_DATABASE_URL.
BACKEND_DIR = Path(__file__).resolve().parents[2]
DATABASE_URL = os.getenv(
    "ASSETFLOW_DATABASE_URL",
    f"sqlite:///{BACKEND_DIR / 'assetflow.db'}",
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
