from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    books = relationship("Book", back_populates="owner")

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
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # Optional fields
    subtitle = Column(String, index=True, nullable=True)
    co_author = Column(String, index=True, nullable=True)
    synopsis = Column(String, index=True, nullable=True)
    copyright_info = Column(String, index=True, nullable=True)
    category = Column(String, index=True, nullable=True)
    subcategory = Column(String, index=True, nullable=True)
    
    owner = relationship("User", back_populates="books")