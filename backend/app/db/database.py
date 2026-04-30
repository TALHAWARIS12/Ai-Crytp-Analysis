from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import text
from app.core.config import settings
from app.db.models import Base

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300, # Recycle more often for serverless DBs like Neon
    pool_size=10,
    max_overflow=20,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    }
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

import time
import logging

logger = logging.getLogger(__name__)

def init_db():
    max_retries = 10
    base_delay = 2
    for attempt in range(max_retries):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                delay = min(base_delay * (2 ** attempt), 60)
                logger.info(f"Retrying database connection in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error("Could not connect to database after maximum retries.")
                logger.info("Database will be unavailable, but backend will continue running.")
