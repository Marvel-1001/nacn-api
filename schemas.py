from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, date
from typing import Optional
from enum import Enum

# Enums for API
class UserRole(str, Enum):
    ADMIN = "admin"
    AUTHOR = "author"

class BookStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    # Note: role is not included here - users can only sign up as authors

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    created_at: datetime

class User(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=17, pattern=r'^[0-9\-]+$')
    title: str
    author: str
    publisher: str
    publication_date: date
    print_length: int = Field(..., gt=0)
    language: str
    front_cover_url: str
    back_cover_url: str
    subtitle: Optional[str] = None
    co_author: Optional[str] = None
    synopsis: Optional[str] = None
    copyright_info: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None


class BookCreate(BookBase):
    pass

class BookUpdate(BookBase):
    # When author updates a book, it goes back to pending status
    pass

class BookAdminUpdate(BaseModel):
    # Admin-specific update for status and rejection reason
    status: BookStatus
    rejection_reason: Optional[str] = None

class Book(BookBase):
    id: int
    owner_id: int
    owner: UserResponse
    status: BookStatus
    rejection_reason: Optional[str] = None

    class Config:
        from_attributes = True

class BookAdminResponse(Book):
    # Extended book response for admin with all details
    pass

