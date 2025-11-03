import services
import auth

from models import User, Book
from schema.books import BookCreate

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from db import get_db_session

from fastapi_cache.decorator import cache

from typing import List


router = APIRouter(
    prefix="/api/v1/books",
    tags=["Books"],
)


# Book routes (now protected)
@router.get("/books", response_model=List[Book])
@cache(expire=60)
async def get_all_books(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(auth.get_current_active_user),
):
    return services.get_books(db, skip=skip, limit=limit, owner_id=current_user.id)


@router.get("/{id}", response_model=Book)
@cache(expire=60)
async def get_book_by_id(
    id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(auth.get_current_active_user),
):
    book = services.get_book(db, id, owner_id=current_user.id)
    
    if not book:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    
    return book


@router.post("/books", response_model=Book)
@cache(expire=60)
async def create_new_book(
    book: BookCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(auth.get_current_active_user),
):
    return services.create_book(db, book, owner_id=current_user.id)


@router.put("/{id}", response_model=Book)
@cache(expire=60)
async def update_book(
    id: int,
    book: BookCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(auth.get_current_active_user),
):
    updated_book = services.update_book(db, id, book, owner_id=current_user.id)
    
    if not updated_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
        
    return updated_book


@router.delete("/{id}", response_model=Book)
@cache(expire=60)
async def delete_book(
    id: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(auth.get_current_active_user),
):
    deleted_book = services.delete_book(db, id, owner_id=current_user.id)
    
    if not deleted_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return deleted_book