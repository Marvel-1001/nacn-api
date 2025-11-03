from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, Annotated, List
from datetime import date


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field()
    is_active: bool = Field(default=True)

    books: List["Book"] = Relationship(back_populates="owner")


class Book(SQLModel, table=True):
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)
    isbn: Optional[str] = Field(default=None, unique=True, index=True)
    title: str = Field(index=True)
    author: str = Field(index=True)
    publisher: str = Field(index=True)
    publication_date: date = Field(index=True)
    print_length: int = Field(index=True)
    language: str = Field(index=True)
    front_cover_url: str = Field(index=True)
    back_cover_url: str = Field(index=True)
    owner_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Optional fields from BookCreate schema
    subtitle: Optional[str] = Field(default=None)
    co_author: Optional[str] = Field(default=None)
    synopsis: Optional[str] = Field(default=None)
    copyright_info: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    subcategory: Optional[str] = Field(default=None)

    owner: Optional["User"] = Relationship(back_populates="books")