from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import Setting
import os

# database URL set up
DATABASE_URL = (
    f"postgresql://{Setting.db_username}:{Setting.db_password}"
    f"@{Setting.db_hostname}:{Setting.db_port}/{Setting.db_name}"
)
os.environ["ALEMBIC_DATABASE_URL"] = DATABASE_URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, bind=engine, autoflush=False)

# Base class for models
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()