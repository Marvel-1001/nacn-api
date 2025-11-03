from contextlib import asynccontextmanager

from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from redis import asyncio as aioredis

from db import create_tables

from routers import users, auth, books

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    create_tables()
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield


app = FastAPI(
    lifespan=lifespan,
    title="NACN API",
    description="API for National Arts Council of Namibia book management system",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)


app.include_router(users.router)
app.include_router(books.router)
app.include_router(auth.router)