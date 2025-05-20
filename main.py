from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db import get_db
import models
import schemas
import services
import auth
from typing import List

from settings import ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()

# Add this temporary endpoint for testing
# @app.get("/test-token")
# async def test_token():
#     test_token = auth.create_access_token({"sub": "test@example.com"})
#     return {"test_token": test_token}

# Add this temporary endpoint for testing
# @app.get("/test-users")
# def test_get_users(db: Session = Depends(get_db)):
#     users = db.query(models.User).all()
#     return {"count": len(users), "users": users}

# # Add this temporary endpoint for testing
# @app.get("/test-user/{email}")
# def test_get_user(email: str, db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.email == email).first()
#     return {"user_exists": user is not None}

# Authentication routes
@app.post("/token/", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Create token with user email as subject
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email},  # Important: must include "sub" claim
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = services.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.create_user(db=db, user=user)

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user

# Book routes (now protected)
@app.get("/books/", response_model=List[schemas.Book])
def get_all_books(
    skip: int = 0, 
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    return services.get_books(db, skip=skip, limit=limit, owner_id=current_user.id)

@app.get("/books/{id}/", response_model=schemas.Book)
def get_book_by_id(
    id: int, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    book = services.get_book(db, id, owner_id=current_user.id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.post("/books/", response_model=schemas.Book)
def create_new_book(
    book: schemas.BookCreate, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    return services.create_book(db, book, owner_id=current_user.id)

@app.put("/books/{id}/", response_model=schemas.Book)   
def update_book(
    id: int, 
    book: schemas.BookCreate, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    updated_book = services.update_book(db, id, book, owner_id=current_user.id)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{id}/", response_model=schemas.Book)
def delete_book(
    id: int, 
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_active_user)
):
    deleted_book = services.delete_book(db, id, owner_id=current_user.id)
    if not deleted_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return deleted_book