"""FastAPI entrypoint: app instance, CORS, router registration.

Run locally with:
    uvicorn app.main:app --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import APP_TITLE, APP_VERSION, CORS_ALLOW_ORIGINS
from app.routers import health, model_a

app = FastAPI(title=APP_TITLE, version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(model_a.router)

# Model B / C / full-assessment routers are added here by their owners:
# from app.routers import model_b, model_c, assessment
# app.include_router(model_b.router)
# app.include_router(model_c.router)
# app.include_router(assessment.router)
