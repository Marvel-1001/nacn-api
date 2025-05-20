from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


SQLACHEMY_DATABASE_URL = "postgresql://book_user:Marvels101939@localhost:5432/NACN-DB"

engine = create_engine(SQLACHEMY_DATABASE_URL, pool_pre_ping=True)
# engine = create_engine(SQLACHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

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