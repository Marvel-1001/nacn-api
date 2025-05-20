from models import Book, User
from sqlalchemy.orm import Session
from schemas import BookCreate, UserCreate
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
    return db.query(User).filter(User.email == email).first()

def create_book(db: Session, book_data: BookCreate, owner_id: int):
    """Create a new book with user association"""
    # Check for existing ISBN
    if db.query(Book).filter(Book.isbn == book_data.isbn).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Book with this ISBN already exists"
        )
    
    db_book = Book(**book_data.model_dump(), owner_id=owner_id)
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

def get_books(db: Session, skip: int = 0, limit: int = 100, owner_id: Optional[int] = None):
    query = db.query(Book)
    if owner_id is not None:
        query = query.filter(Book.owner_id == owner_id)
    return query.offset(skip).limit(limit).all()

def get_book(db: Session, book_id: int, owner_id: Optional[int] = None):
    query = db.query(Book).filter(Book.id == book_id)
    if owner_id is not None:
        query = query.filter(Book.owner_id == owner_id)
    return query.first()

def update_book(db: Session, book_id: int, book_data: BookCreate, owner_id: Optional[int] = None):
    query = db.query(Book).filter(Book.id == book_id)
    if owner_id is not None:
        query = query.filter(Book.owner_id == owner_id)
    
    db_book = query.first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    for key, value in book_data.model_dump().items():
        setattr(db_book, key, value)
    
    db.commit()
    db.refresh(db_book)
    return db_book

def delete_book(db: Session, book_id: int, owner_id: Optional[int] = None):
    query = db.query(Book).filter(Book.id == book_id)
    if owner_id is not None:
        query = query.filter(Book.owner_id == owner_id)
    
    db_book = query.first()
    if not db_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(db_book)
    db.commit()
    return db_book