from typing import Optional, List
from models import Book, User, BookStatus, UserRole
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from sqlalchemy.orm import joinedload
import models
from schemas import BookCreate, BookUpdate, BookAdminUpdate


def create_book(db: Session, data: BookCreate, user_id: int):
    """
    Create a new book entry in the database.
    Books created by authors are automatically set to PENDING status.
    
    Args:
        db (Session): The database session.
        data (BookCreate): The book data to be created.
        user_id (int): The ID of the user who is submitting the book.
        
    Returns:
        Book: The created book object.
        
    Raises:
        HTTPException: If ISBN already exists or user not found
    """
    # Check if ISBN already exists in the database
    existing_book = db.query(Book).filter(Book.isbn == data.isbn).first()
    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A book with this ISBN {data.isbn} already exists."
        )

    # Get user to check their role for setting initial status
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Determine initial status based on user role:
    # - Admins: Books are automatically APPROVED
    # - Authors: Books start as PENDING (require admin approval)
    user_from_db = db.query(User).filter(User.id == user_id).first()
    if user_from_db is UserRole.ADMIN:
        initial_status = BookStatus.APPROVED
    else:
        initial_status = BookStatus.PENDING

    # Create a book instance linked to the current user with appropriate status
    book_instance = data.model_dump(exclude = {"owner_id", "status"})
    book_instance = Book(
        **data.model_dump(), 
        owner_id=user_id,  # Set the book owner
        status=initial_status  # Set initial status based on role
    )

    # Save to database
    db.add(book_instance)
    db.commit()
    db.refresh(book_instance)  # Refresh to get auto-generated fields like ID
    
    # Reload the book with owner relationship for complete response
    book_instance = db.query(Book).options(joinedload(Book.owner)).filter(Book.id == book_instance.id).first()

    return book_instance

def validate_isbn(isbn: str) -> bool:
    """
    Basic ISBN validation function.
    
    Args:
        isbn (str): ISBN string to validate
        
    Returns:
        bool: True if ISBN is valid (10 or 13 digits), False otherwise
    """
    # Remove hyphens and spaces for validation
    isbn = isbn.replace("-", "").replace(" ", "")
    
    # Valid ISBNs are either 10 or 13 digits
    return len(isbn) in [10, 13] and isbn.isdigit()

def get_books(db: Session, user: Optional[User] = None) -> List[Book]:
    """
    Retrieve books based on user role with appropriate permission filtering:
    - Admin: All books (all statuses, all owners)
    - Author: Only their own books (all statuses)
    - Public/Unauthenticated: Only approved books (any owner)
    
    Args:
        db (Session): Database session
        user (Optional[User]): Current user object (None for public access)
        
    Returns:
        List[Book]: List of books filtered by user permissions
    """
    print(f"=== get_books DEBUG ===")
    print(f"User: {user.id if user else 'None'}")
    print(f"User Role: {user.role if user else 'None'}")
    
    # Start with base query including owner relationship for eager loading
    query = db.query(Book).options(joinedload(Book.owner))

    # Apply filters based on user role
    if user is None:
        # Public access - only show approved books (regardless of owner)
        query = query.filter(Book.status == BookStatus.APPROVED)
        print(f"Public access - showing approved books only")

    elif user.role == UserRole.ADMIN:
        # Admin can see all books - no filter needed
        print(f"Admin access - showing ALL books")

    elif user.role == UserRole.AUTHOR:
        # Authors can see their own books regardless of status
        query = query.filter(Book.owner_id == user.id)
        print(f"Author access - showing books for user_id: {user.id}")
    else:
        print(f"Unknown role: {user.role}")
    
    # Execute query and get results
    results = query.all()
    print(f"Found {len(results)} books")
    
    # Debug: Show which books were found with details
    for book in results:
        print(f"  Book {book.id}: '{book.title}', Status: {book.status}, Owner: {book.owner_id}")
    
    return results

def get_book(db: Session, book_id: int, user: Optional[User] = None):
    """
    Retrieve a specific book by its ID with comprehensive permission checks.
    
    Args:
        db (Session): Database session
        book_id (int): ID of the book to retrieve
        user (Optional[User]): Current user object (None for public access)
        
    Returns:
        Book: The requested book if found and accessible, None otherwise
    """
    # Query book with owner relationship eager loading
    book = db.query(Book).options(joinedload(Book.owner)).filter(Book.id == book_id).first()
    
    # Return None if book doesn't exist
    if not book:
        return None
    
    # Permission checks based on user type
    if user is None:
        # Public access - only show approved books
        if book.status != BookStatus.APPROVED:
            return None
    elif user.role == UserRole.ADMIN:
        # Admin can see all books regardless of status or ownership
        return book
    elif user.role == UserRole.AUTHOR: 
        # Authors can only see their own books (all statuses)
        if book.owner_id != user.id:
            return None
    else:
        # Unknown role - deny access as safety measure
        return None
    
    return book


def update_book(db: Session, book_data: BookUpdate, book_id: int, user: User):
    """
    Update a book entry in the database with permission checks.
    When authors update a book, it goes back to PENDING status (requires re-approval).
    
    Args:
        db (Session): Database session
        book_data (BookUpdate): Updated book data
        book_id (int): ID of the book to update
        user (User): Current user performing the update
        
    Returns:
        Book: Updated book object if successful, None if book not found
        
    Raises:
        HTTPException: If user doesn't have permission to update the book
    """
    # Find the book to update
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None
    
    # Check ownership: Authors can only update their own books
    if bool(user.role == UserRole.AUTHOR and book.owner_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this book"
        )
    
    # Update book fields with new data
    for key, value in book_data.model_dump().items():
        setattr(book, key, value)
    
    # If author updates a book, set status back to PENDING (requires admin re-approval)
    # This ensures any changes made by authors go through review process again
    if bool (user.role == UserRole.AUTHOR and book.status != BookStatus.PENDING): # 
        setattr(book, 'status', BookStatus.PENDING)
        setattr(book, 'rejection_reason', None)  # Clear previous rejection reason
        # book._status = BookStatus.PENDING
        # book._rejection_reason = None  # Clear previous rejection reason
    
    # Save changes to database
    db.commit()
    db.refresh(book)  # Refresh to get updated state from database
    return book


def update_book_status(db: Session, book_id: int, status_data: BookAdminUpdate, admin: User):
    """
    Admin function to update book status (approve/reject) and provide feedback.
    
    Args:
        db (Session): Database session
        book_id (int): ID of the book to update
        status_data (BookAdminUpdate): New status and optional rejection reason
        admin (User): Admin user performing the action
        
    Returns:
        Book: Updated book object if successful, None if book not found
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Verify the user is actually an admin
    if bool(admin.role != UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Find the book to update
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None
    
    # Update status (convert from enum value if needed)
    book.status = BookStatus(status_data.status.value)
    
    # Handle rejection reason: only set when rejecting, clear when approving
    if status_data.status == BookStatus.REJECTED:
        book.rejection_reason = status_data.rejection_reason  # Provide feedback to author
    else:
        book.rejection_reason = None  # Clear rejection reason if approved
    
    # Save changes
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int, user: User):
    """
    Delete a book entry from the database. Admin only operation.
    
    Args:
        db (Session): Database session
        book_id (int): ID of the book to delete
        user (User): User attempting to delete the book
        
    Returns:
        Book: The deleted book object (for response) if successful, None if book not found
        
    Raises:
        HTTPException: If user is not an admin
    """
    # Find the book to delete
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None
    
    # Only admins can delete books (safety measure)
    if bool(user.role != UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to delete books"
        )
    
    # Store the book data before deletion for response
    book_to_return = book
    
    # Perform deletion
    db.delete(book)
    db.commit()
    
    # Return the deleted book data (before deletion)
    return book_to_return