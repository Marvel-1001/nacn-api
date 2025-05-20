import os
from dotenv import load_dotenv
from typing import Union

load_dotenv()

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL")

# Authentication settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# Convert string to integer for token expiration
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
except (TypeError, ValueError):
    ACCESS_TOKEN_EXPIRE_MINUTES = 30  # default fallback

# CORS settings
X_FRAME_OPTIONS = 'SAMEORIGIN'
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:8000",
#     'http://localhost:8080'
# ]
 
# CORS_ALLOW_CREDENTIALS = True
# CORS_ALLOW_HEADERS = (
#     "authorization",
#     "content-type",
#     "x-frame-options",
#     "x-requested-with",
#     "x-csrftoken",
#     "x-allowed-origins",
#     "x-allowed-headers",
#     "x-allowed-methods",
#     "x-allowed-credentials",
# )