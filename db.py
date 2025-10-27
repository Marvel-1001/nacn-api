import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# ✅ SECURE - Use environment variables
load_dotenv()
SQLACHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
# If the environment variable is not set, use a default value
if not SQLACHEMY_DATABASE_URL:
    # Fallback to SQLite
    SQLACHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fallback.db"  # simpler, safer fallback
)



# 

engine = create_engine(SQLACHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)