"""ORM models: Application and Assessment (one Assessment row per model run)."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_name: Mapped[str] = mapped_column(String(120))
    no_of_dependents: Mapped[int] = mapped_column(Integer, default=0)
    education: Mapped[str] = mapped_column(String(20))            # Graduate / Not Graduate
    self_employed: Mapped[str] = mapped_column(String(5))         # Yes / No
    income_annum: Mapped[float] = mapped_column(Float)
    loan_amount: Mapped[float] = mapped_column(Float)
    loan_term: Mapped[int] = mapped_column(Integer)               # years
    cibil_score: Mapped[int] = mapped_column(Integer)
    residential_assets_value: Mapped[float] = mapped_column(Float, default=0.0)
    commercial_assets_value: Mapped[float] = mapped_column(Float, default=0.0)
    luxury_assets_value: Mapped[float] = mapped_column(Float, default=0.0)
    bank_asset_value: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # cascade="all, delete-orphan": deleting an Application removes its assessments
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int | None] = mapped_column(
        ForeignKey("applications.id"), nullable=True
    )
    model_key: Mapped[str] = mapped_column(String(20))        # model_a | model_b | model_c
    model_version: Mapped[str] = mapped_column(String(40))
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON)      # request payload
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON)     # probability / risk_band / approval / amount
    risk_band: Mapped[str | None] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["Application"] = relationship(back_populates="assessments")