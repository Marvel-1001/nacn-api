from fastapi.security.http import HTTPAuthorizationCredentials
from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_password_hash, 
    verify_password, get_current_user, get_current_admin, get_current_author
)
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import services, models, schemas
from datetime import timedelta
from db import get_db, engine
from typing import Optional
import os

# Create FastAPI application instance
app = FastAPI()

# ---------- Auth Endpoints ---------- #
@app.post("/login")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login endpoint for both admins and authors using OAuth2 password flow.
    
    Args:
        form_data: OAuth2 form containing username (email) and password
        db: Database session dependency
        
    Returns:
        dict: Access token, token type, and user role
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Query user by email (OAuth2PasswordRequestForm uses 'username' for email)
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail = "Incorrect Email or password",
        )
    
    # Create access token with expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data = {"sub": user.email}, expires_delta = access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_role": user.role  # Return user role for frontend to handle UI differently
    }

# ---------- User Endpoints ---------- #
@app.post("/register")
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. All new registrations are authors by default.
    Admins must be created manually via database or admin endpoints.
    
    Args:
        user_data: User registration data (email and password)
        db: Database session dependency
        
    Returns:
        dict: Success message and user details
        
    Raises:
        HTTPException: If email is already registered
    """
    # Check if user already exists by email
    existing_user = db.query(models.User).filter(
        (models.User.email == user_data.email)
    ).first()

    if existing_user: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user as AUTHOR (default role for self-registration)
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        email = user_data.email,
        hashed_password = hashed_password,
        role = models.UserRole.AUTHOR  # Default role for new registrations
    )

    # Save user to database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  # Refresh to get auto-generated fields like id and created_at

    return {
        "message": "User registered successfully as Author",
        "user_id": db_user.id,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at
    }

# Protected user endpoints
@app.get("/users/me")
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    """
    Get current authenticated user's profile information.
    
    Args:
        current_user: Authenticated user from dependency injection
        
    Returns:
        models.User: Current user object with all details
    """
    return current_user

# ---------- Public Book Endpoints ---------- #
@app.get("/books/", response_model=list[schemas.Book])
def get_all_books(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)  # ✅ Make optional for public access
):
    """
    Public endpoint - returns approved books for unauthenticated users.
    Protected endpoint - returns books based on role for authenticated users.
    
    Args:
        db: Database session dependency
        current_user: Optional user object (None for unauthenticated users)
        
    Returns:
        list[schemas.Book]: List of books filtered by user permissions
    """
    return services.get_books(db, current_user)  # Service handles permission-based filtering

@app.get("/books/{book_id}", response_model=schemas.Book)
def get_book_by_id(
    book_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user)  # ✅ Make optional for public access
):
    """
    Public endpoint - returns approved books for unauthenticated users.
    Protected endpoint - returns book based on permissions for authenticated users.
    
    Args:
        book_id: ID of the book to retrieve
        db: Database session dependency
        current_user: Optional user object (None for unauthenticated users)
        
    Returns:
        schemas.Book: Book details if found and accessible
        
    Raises:
        HTTPException: If book not found or user doesn't have permission
    """
    book = services.get_book(db, book_id, current_user)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")       
    return book

# ---------- Author Book Endpoints ---------- #
@app.post("/books/", response_model=schemas.Book)
def create_new_book(
    book: schemas.BookCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_author)  # Authors and admins can create books
):
    """
    Create a new book. 
    - Authors: Books are created with PENDING status (requires admin approval)
    - Admins: Books are created with APPROVED status (auto-approved)
    
    Args:
        book: Book creation data (title, description, etc.)
        db: Database session dependency
        current_user: Authenticated author or admin user
        
    Returns:
        schemas.Book: Created book object
    """
    return services.create_book(db, book, user_id = current_user.id)

@app.put("/books/{book_id}", response_model=schemas.Book)   
def update_book(
    book_id: int, 
    book: schemas.BookUpdate, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_author)
):
    """
    Update a book. Authors can only update their own books.
    When authors update a book, status changes to PENDING (requires re-approval).
    
    Args:
        book_id: ID of the book to update
        book: Book update data
        db: Database session dependency
        current_user: Authenticated author or admin user
        
    Returns:
        schemas.Book: Updated book object
        
    Raises:
        HTTPException: If book not found or user doesn't have permission
    """
    updated_book = services.update_book(db, book, book_id, current_user)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return updated_book

@app.get("/my-books/", response_model=list[schemas.Book])
def get_my_books(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_author)
):
    """
    Get books for the current author (all statuses) or all books for admin.
    
    Args:
        db: Database session dependency
        current_user: Authenticated author or admin user
        
    Returns:
        list[schemas.Book]: List of books owned by current user (or all for admin)
    """
    books = services.get_books(db, current_user)  # ✅ Service handles filtering by ownership
    return books

# ---------- Admin Book Management Endpoints ---------- #
@app.put("/admin/books/{book_id}/status", response_model=schemas.Book)
def update_book_status(
    book_id: int,
    status_data: schemas.BookAdminUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Admin only - approve or reject a book and add admin comments.
    
    Args:
        book_id: ID of the book to update status
        status_data: New status and optional admin comments
        db: Database session dependency
        current_user: Authenticated admin user
        
    Returns:
        schemas.Book: Updated book object
        
    Raises:
        HTTPException: If book not found
    """
    updated_book = services.update_book_status(db, book_id, status_data, current_user)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{book_id}", response_model=schemas.Book)
def delete_book(
    book_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)  # Only admins can delete
):
    """
    Delete a book. Admin only.
    
    Args:
        book_id: ID of the book to delete
        db: Database session dependency
        current_user: Authenticated admin user
        
    Returns:
        schemas.Book: Deleted book object (before deletion)
        
    Raises:
        HTTPException: If book not found
    """
    deleted_book = services.delete_book(db, book_id, current_user)
    if not deleted_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return deleted_book

# ---------- Admin User Management Endpoints ---------- #
@app.post("/admin/users/", response_model=schemas.UserResponse)
def create_admin_user(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """
    Admin only - create a new admin user.
    This is the only way to create admin users (self-registration creates authors).
    
    Args:
        user_data: User creation data (email and password)
        db: Database session dependency
        current_user: Authenticated admin user
        
    Returns:
        dict: Success message and admin user details
        
    Raises:
        HTTPException: If email is already registered
    """
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user_data.email)
    ).first()

    if existing_user: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user as ADMIN (only admins can create other admins)
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        email=user_data.email,
        hashed_password=hashed_password,
        role=models.UserRole.ADMIN
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "Admin user created successfully",
        "user_id": db_user.id,
        "email": db_user.email,
        "role": db_user.role,
        "created_at": db_user.created_at
    }