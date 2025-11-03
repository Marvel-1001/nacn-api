from datetime import datetime, timedelta
from typing import Optional, Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from jose import JWTError, jwt
from passlib.context import CryptContext

from sqlmodel import Session, select

from models import User
from schema.auth import TokenData

from db import get_db_session

from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def verify_password(plain_password: str, hashed_password: str):
    """Verify a password against its hashed version"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str):
    """Generate a password hash"""
    return pwd_context.hash(password)


def get_user(db: Annotated[Session, Depends(get_db_session)], email: str):
    """Get user by email from database"""

    statement = select(User).where(User.email == email)

    return db.exec(statement).first()


def authenticate_user(
    db: Annotated[Session, Depends(get_db_session)], email: str, password: str
):
    """Authenticate a user with email and password"""

    user = get_user(db, email)

    if not user:
        return False

    if not verify_password(password, user.hashed_password):  # type: ignore
        return False

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set and cannot be None")
    
    if not ALGORITHM:
        raise ValueError("ALGORITHM must be set and cannot be None")
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db_session)
):
    """Get the current authenticated user from the JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if not SECRET_KEY:
            raise ValueError("SECRET_KEY must be set and cannot be None")
        
        if not ALGORITHM or not isinstance(ALGORITHM, str):
            raise ValueError("ALGORITHM must be a non-empty string")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        
        if not isinstance(email, str):
            raise credentials_exception
        
        if email is None:
            raise credentials_exception
        
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    if token_data.email is None:
        raise credentials_exception
    
    user = get_user(db, email=token_data.email)
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the current active user (checks if user is active)"""
    
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    return current_user