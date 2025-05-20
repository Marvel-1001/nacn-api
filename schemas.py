from datetime import date
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True

# Update Book schemas to include owner_id
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
    
    # Optional fields
    subtitle: Optional[str] = None
    co_author: Optional[str] = None
    synopsis: Optional[str] = None
    copyright_info: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    owner_id: int
    
    class Config:
        from_attributes = True