"""FastAPI entrypoint: app instance, CORS, router registration.

Run locally with:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_TITLE, APP_VERSION, CORS_ALLOW_ORIGINS
from app.db import init_db
from app.routers import health, model_a, applications, analytics

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()  # creates data/app.db + tables once, on server startup
    yield

#app = FastAPI(title=APP_TITLE, version=APP_VERSION)
app = FastAPI(title=APP_TITLE, version=APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(model_a.router)
app.include_router(applications.router)
app.include_router(analytics.router)

# Model B / C / full-assessment routers are added here by their owners:
# from app.routers import model_b, model_c, assessment
# app.include_router(model_b.router)
# app.include_router(model_c.router)
# app.include_router(assessment.router)
