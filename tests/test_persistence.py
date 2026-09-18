"""DB-layer tests: save_assessment helper + cascade delete. No API involved."""
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models_db import Application, Assessment
from app.services.persistence import save_assessment, get_or_create_application

def _db():
    engine = create_engine("sqlite://")  # fresh in-memory DB per test
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def _make_application(db) -> Application:
    row = Application(
        applicant_name="Ilma Test", no_of_dependents=2, education="Graduate",
        self_employed="No", income_annum=9_600_000, loan_amount=29_900_000,
        loan_term=12, cibil_score=778, residential_assets_value=2_400_000,
        commercial_assets_value=17_600_000, luxury_assets_value=22_700_000,
        bank_asset_value=8_000_000,
    )
    db.add(row)
    db.commit()
    return row


def test_save_assessment_persists_row():
    db = _db()
    app_row = _make_application(db)
    saved = save_assessment(
        db, model_key="model_a", model_version="model_a_v1",
        inputs={"age": 45}, outputs={"probability": 0.12},
        risk_band="low", application_id=app_row.id,
    )
    assert saved.id is not None
    stored = db.scalar(select(Assessment).where(Assessment.model_key == "model_a"))
    assert stored.outputs["probability"] == 0.12
    assert stored.application_id == app_row.id


def test_save_assessment_without_application():
    db = _db()
    saved = save_assessment(
        db, model_key="model_b", model_version="model_b_v1",
        inputs={"cibil_score": 778}, outputs={"approval": "Approved"},
    )
    assert saved.application_id is None
    assert saved.risk_band is None


def test_cascade_delete():
    db = _db()
    app_row = _make_application(db)
    save_assessment(db, model_key="model_a", model_version="model_a_v1",
                    inputs={}, outputs={}, application_id=app_row.id)
    db.delete(app_row)
    db.commit()
    assert db.scalar(select(Assessment)) is None
    assert db.get(Application, app_row.id) is None


def test_thin_application_create_for_predict_linking():
    db = _db()
    row = Application(applicant_name="Thin Record")
    db.add(row)
    db.commit()
    assert row.id is not None
    assert row.cibil_score is None

def test_get_or_create_application_reuses_same_name():
    db = _db()
    first = get_or_create_application(db, applicant_name="Ilma")
    second = get_or_create_application(db, applicant_name="Ilma")
    assert first.id == second.id              # reused, NOT duplicated
    assert db.query(Application).count() == 1  # exactly one row exists


def test_get_or_create_application_creates_new_name():
    db = _db()
    row = get_or_create_application(db, applicant_name="New Person")
    assert row.id is not None
    assert row.cibil_score is None            # thin record: loan fields empty