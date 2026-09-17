"""Regression: JSON columns round-trip dict payloads intact through the API path."""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models_db import Assessment
from app.services.persistence import save_assessment

INPUTS = {"revolving_utilization": 0.3, "age": 45, "dependents": 2}
OUTPUTS = {"probability": 0.123456, "risk_band": "low", "model_version": "model_a_v1"}


def test_inputs_outputs_roundtrip():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, expire_on_commit=False)()

    save_assessment(db, model_key="model_a", model_version="model_a_v1",
                    inputs=INPUTS, outputs=OUTPUTS, risk_band="low")
    row = db.scalar(select(Assessment))
    assert row.inputs == INPUTS
    assert row.outputs == OUTPUTS
