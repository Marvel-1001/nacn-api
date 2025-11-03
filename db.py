import os
from dotenv import load_dotenv

from sqlmodel import create_engine, SQLModel, Session

from functools import lru_cache

load_dotenv()


@lru_cache(maxsize=1) # Cache the engine to avoid recreating it multiple times
def get_engine():
    return create_engine(os.getenv("SQLALCHEMY_DATABASE_URL"), pool_pre_ping=True)


def get_db_session():
    with Session(get_engine()) as session:
        yield session


def create_tables():
    SQLModel.metadata.create_all(get_engine())
