import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import settings

os.makedirs("data", exist_ok=True)

database_url = settings.DATABASE_URL
if database_url.startswith("sqlite"):
    db_path = database_url.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) if "/" in db_path else ".", exist_ok=True)

engine = create_engine(
    database_url,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
