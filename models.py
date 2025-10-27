from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql.expression import text
from sqlalchemy import Column, Enum
from sqlalchemy.orm import relationship
from db import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AUTHOR = "author"

class BookStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.AUTHOR, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    books = relationship("Book", back_populates="owner", cascade="all, delete-orphan", lazy = "select")

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String, unique=True, index=True)
    title = Column(String, index=True, nullable=False)
    author = Column(String, index=True, nullable=False)
    publisher = Column(String, index=True, nullable=False)
    publication_date = Column(Date, index=True, nullable=False)
    print_length = Column(Integer, index=True, nullable=False)
    language = Column(String, index=True, nullable=False)
    front_cover_url = Column(String, index=True, nullable=False)
    back_cover_url = Column(String, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(BookStatus), default=BookStatus.PENDING, nullable=True)
    rejection_reason = Column(String, nullable=True)
    
    # Optional fields
    subtitle = Column(String, index=True, nullable=True)
    co_author = Column(String, index=True, nullable=True)
    synopsis = Column(String, index=True, nullable=True)
    copyright_info = Column(String, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    subcategory = Column(String, index=True, nullable=True)
    
    owner = relationship("User", back_populates="books", lazy = "select")