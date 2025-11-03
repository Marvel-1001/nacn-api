from models import Book, User
from sqlmodel import Session, select

from schema.books import BookCreate
from schema.users import UserCreate

from fastapi import HTTPException, status

from auth import get_password_hash
from typing import Optional


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    statement = select(User).where(User.email == email)
    return db.exec(statement).first()


def create_book(db: Session, book_data: BookCreate, owner_id: int):
    """Create a new book with user association"""
    # Check for existing ISBN
    statement = select(Book).where(Book.isbn == book_data.isbn)
    if db.exec(statement).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book with this ISBN already exists",
        )

    db_book = Book(**book_data.model_dump(), owner_id=owner_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def get_books(
    db: Session, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None
):
    statement = select(Book)
    if owner_id is not None:
        statement = statement.where(Book.owner_id == owner_id)
    statement = statement.offset(skip).limit(limit)
    return db.exec(statement).all()


def get_book(db: Session, book_id: int, owner_id: Optional[int] = None):
    statement = select(Book).where(Book.id == book_id)
    if owner_id is not None:
        statement = statement.where(Book.owner_id == owner_id)
    return db.exec(statement).first()


def update_book(
    db: Session, book_id: int, book_data: BookCreate, owner_id: Optional[int] = None
):
    statement = select(Book).where(Book.id == book_id)
    if owner_id is not None:
        statement = statement.where(Book.owner_id == owner_id)

    db_book = db.exec(statement).first()

    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Get the current book data for comparison
    serialized_db_book = db_book.model_dump()

    # Only update fields that have changed and exist in the model
    book_data_dict = book_data.model_dump()
    for key, value in book_data_dict.items():
        if hasattr(db_book, key) and serialized_db_book.get(key) != value:
            setattr(db_book, key, value)

    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int, owner_id: Optional[int] = None):
    statement = select(Book).where(Book.id == book_id)
    if owner_id is not None:
        statement = statement.where(Book.owner_id == owner_id)

    db_book = db.exec(statement).first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")

    db.delete(db_book)
    db.commit()
    return db_book
