from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import Setting
import os

DATABASE_URL = (
    f"postgresql://{Setting.db_username}:{Setting.db_password}"
    f"@{Setting.db_hostname}:{Setting.db_port}/{Setting.db_name}"
)
os.environ["ALEMBIC_DATABASE_URL"] = DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, bind=engine, autoflush=False)

Base = declarative_base()

def get_db() -> SessionLocal:
    """Yield a database session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()