import services
import auth

from fastapi import APIRouter, Depends, HTTPException, status

from sqlmodel import Session
from db import get_db_session

from schema.users import UserCreate
from models import User

from fastapi_cache.decorator import cache

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)


@router.post("", response_model=User)
@cache(expire=60)
async def create_user(user: UserCreate, db: Session = Depends(get_db_session)):
    db_user = services.get_user_by_email(db, email=user.email)
    
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    new_user = services.create_user(db=db, user=user)
    
    return new_user.model_dump(exclude=["hashed_password"])


@router.get("/me", response_model=User)
@cache(expire=60)
async def read_users_me(
    current_user: User = Depends(auth.get_current_active_user),
):
    return current_user.model_dump(exclude=["hashed_password"])
