from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # drops dead connections (safe under container restarts)
    pool_size=10,
    max_overflow=20,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
