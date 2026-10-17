"""Database connection and session management for eSahaay."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sahaay.config import settings

# Engine configuration
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency helper for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Create all tables in the database."""
    from sahaay import models  # Ensure all models are imported
    Base.metadata.create_all(bind=engine)
