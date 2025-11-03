from datetime import date
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Annotated


# Update Book schemas to include owner_id
class BookCreate(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=17, pattern=r"^[0-9\-]+$")
    title: Annotated[str, Field(description="Title of the book")]
    author: Annotated[str, Field(description="Author of the book")]
    publisher: Annotated[str, Field(description="Publisher of the book")]
    publication_date: Annotated[date, Field(description="Publication date of the book")]
    print_length: Annotated[int, Field(..., gt=0, description="Print length of the book")]
    language: Annotated[str, Field(description="Language of the book")]
    front_cover_url: Annotated[str, Field(description="Front cover URL of the book")]
    back_cover_url: Annotated[str, Field(description="Back cover URL of the book")]

    # Optional fields
    subtitle: Annotated[Optional[str], Field(default=None, description="Subtitle of the book")]
    co_author: Annotated[Optional[str], Field(default=None, description="Co-author of the book")]
    synopsis: Annotated[Optional[str], Field(default=None, description="Synopsis of the book")]
    copyright_info: Annotated[Optional[str], Field(default=None, description="Copyright information of the book")]
    category: Annotated[Optional[str], Field(default=None, description="Category of the book")]
    subcategory: Annotated[Optional[str], Field(default=None, description="Subcategory of the book")]