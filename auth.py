from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends
from fastapi.security import  OAuth2PasswordBearer
from sqlalchemy.orm import Session
from db import get_db
from dotenv import load_dotenv
import models
import os
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# JWT configuration - using environment variables with fallback values
ALGORITHM = "HS256"  # Hashing algorithm for JWT tokens
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

# Get secret key from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")

# Password hashing context using bcrypt algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 password bearer scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def verify_password(plain_password, hashed_password):
    """
    Verify a plain text password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        bool: True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    """
    Hash a password using bcrypt algorithm.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password
        
    Raises:
        HTTPException: If password exceeds bcrypt's 72-byte limit
    """
    # bcrypt has a limit of 72 bytes maximum for passwords
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long. Maximum length is 72 bytes."
        )
        # Note: The following line is unreachable due to the exception above
        password = password[:72]  # This would truncate password if reached
    return pwd_context.hash(password)

def create_access_token(data: dict): # type: ignore
    """
    Create a JWT access token with expiration time.
    
    Args:
        data: Dictionary containing token payload (typically user info)
        
    Returns:
        str: Encoded JWT token string
    """
    to_encode = data.copy()  # Create a copy to avoid modifying original data
    # Calculate expiration time (current UTC time + configured minutes)
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})  # Add expiration claim to payload
    # Encode the JWT token with secret key and algorithm
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string to verify
        credentials_exception: Exception to raise if verification fails
        
    Returns:
        str: Email extracted from token payload
        
    Raises:
        credentials_exception: If token is invalid or email is missing
    """
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract email from 'sub' (subject) claim in token payload
        email: str = payload.get("sub")  # type: ignore
        if email is None:
            raise credentials_exception  # No email in token
        return email
    except JWTError:
        # Token is invalid, expired, or malformed
        raise credentials_exception

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get the current authenticated user from JWT token.
    
    This is a FastAPI dependency that extracts the user from the JWT token
    and verifies they exist in the database.
    
    Args:
        token: JWT token from Authorization header
        db: Database session dependency
        
    Returns:
        models.User: The authenticated user object
        
    Raises:
        HTTPException: If token is invalid or user doesn't exist
    """
    # Create exception for authentication failures
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Verify token and extract email
    email = verify_token(token, credentials_exception)
    
    # Query database for user with the extracted email
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception  # User not found in database
        
    return user

# Role-based dependency functions
async def get_current_admin(
    current_user: models.User = Depends(get_current_user)
):
    """
    Dependency to ensure the current user is an admin.
    
    Args:
        current_user: The authenticated user from get_current_user dependency
        
    Returns:
        models.User: The admin user
        
    Raises:
        HTTPException: If user doesn't have admin role
    """
    # Check if user has ADMIN role (note: bool() is redundant here)
    if bool(current_user.role != models.UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )
    return current_user

async def get_current_author(
    current_user: models.User = Depends(get_current_user)
):
    """
    Dependency to ensure the current user is an author (or admin).
    
    Args:
        current_user: The authenticated user from get_current_user dependency
        
    Returns:
        models.User: The author or admin user
        
    Raises:
        HTTPException: If user doesn't have author or admin role
    """
    # Check if user has AUTHOR or ADMIN role
    if current_user.role not in [models.UserRole.AUTHOR, models.UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Author access required."
        )
    return current_user

def check_book_ownership(book: models.Book, user: models.User):
    """
    Check if user owns the book or is an admin.
    
    Args:
        book: The book object to check ownership of
        user: The user to verify ownership against
        
    Returns:
        bool: True if user owns the book or is admin, False otherwise
    """
    # User can access if they are ADMIN or if they own the book
    return user.role == models.UserRole.ADMIN or book.owner_id == user.id