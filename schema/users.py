from datetime import date
from pydantic import BaseModel, EmailStr, Field
from typing import Annotated


class UserCreate(BaseModel):
    email: EmailStr
    password: Annotated[str, Field()]