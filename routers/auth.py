import models
import schemas
import services
import auth

from contextlib import asynccontextmanager

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from db import get_db_session

from typing import List

from settings import ACCESS_TOKEN_EXPIRE_MINUTES


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


# Authentication routes
@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db_session)
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
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}