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
        from sqlmodel import select
        from backend.app.models import User
        from backend.app.auth import get_password_hash
        
        SQLModel.metadata.create_all(engine)
        with Session(engine) as session:
            try:
                session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS hashed_password VARCHAR'))
            except Exception as e:
                logger.warning(f"Failed to migrate hashed_password (might already exist): {e}")
                
            try:
                session.execute(text('ALTER TABLE "poem" ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE'))
            except Exception as e:
                logger.warning(f"Failed to migrate is_public (might already exist): {e}")
                
            try:
                session.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE'))
            except Exception as e:
                logger.warning(f"Failed to migrate is_admin (might already exist): {e}")
                
            try:
                session.commit()
            except Exception as e:
                logger.error(f"Failed to commit database migrations: {e}")
                
            try:
                stmt = select(User).where(User.username == "admin")
                admin_user = session.exec(stmt).first()
                if not admin_user:
                    new_admin = User(
                        username="admin",
                        email="admin@gieovan.com",
                        hashed_password=get_password_hash("admin123"),
                        is_admin=True
                    )
                    session.add(new_admin)
                    session.commit()
                    logger.info("Default admin user seeded successfully.")
            except Exception as e:
                logger.error(f"Failed to seed default admin user: {e}", exc_info=True)
    else:
        logger.warning("init_db skipped: database engine is not initialized.")

def get_session():
    if not engine:
        raise RuntimeError("Database engine is not initialized. Check DATABASE_URL environment variable.")
    with Session(engine) as session:
        yield session
