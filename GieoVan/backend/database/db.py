import os
import logging
from sqlmodel import SQLModel, create_engine, Session, text

logger = logging.getLogger(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

engine = None
if DATABASE_URL:
    connect_args = {"sslmode": "require"} if "postgresql" in DATABASE_URL else {}
    try:
        engine = create_engine(
            DATABASE_URL, 
            echo=True, 
            connect_args=connect_args,
            pool_recycle=1800,
            pool_pre_ping=True
        )
    except Exception as e:
        logger.error(f"Failed to create SQLModel engine: {e}")
else:
    logger.warning("DATABASE_URL is not set in environment. Database connection will not be available.")

def init_db():
    if engine:
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            try:
                session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS hashed_password VARCHAR'))
                session.execute(text('ALTER TABLE "poem" ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE'))
                session.commit()
            except Exception as e:
                logger.error(f"Failed to migrate database (ensure hashed_password exists): {e}")
    else:
        logger.warning("init_db skipped: database engine is not initialized.")

def get_session():
    if not engine:
        raise RuntimeError("Database engine is not initialized. Check DATABASE_URL environment variable.")
    with Session(engine) as session:
        yield session
