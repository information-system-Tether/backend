import os
import sys

# Set DATABASE_URL before importing config or database
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(backend_dir, "tether.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

pyth_dir = os.path.join(backend_dir, "pyth")
if pyth_dir not in sys.path:
    sys.path.insert(0, pyth_dir)

from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from auth.models import Base as AuthBase, usr
from auth.security import createtokenaccess, hashpass
from auth.database import engine as auth_engine, SessionLocal as AuthSessionLocal
from diary.models import Base as DiaryBase, bio, diarylist, entry
from diary.database import engine as diary_engine, SessionLocal as DiarySessionLocal, addcols
from diary.baseproducts import seedbase
from diary.main import app

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    AuthBase.metadata.create_all(bind=auth_engine)
    DiaryBase.metadata.create_all(bind=diary_engine)
    addcols()

    with DiarySessionLocal() as db:
        seedbase(db)

    # Use a unique test user to ensure isolated test data
    test_login = "test_analytics_user"
    with AuthSessionLocal() as db:
        user = db.query(usr).filter(usr.login == test_login).first()
        if not user:
            user = usr(login=test_login, email=f"{test_login}@example.com", password_hash=hashpass("pass123"))
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id

    # Clean existing diary sheets for this test user
    with DiarySessionLocal() as db:
        existing_sheets = db.query(diarylist).filter(diarylist.user_id == user_id).all()
        for s in existing_sheets:
            db.delete(s)
        existing_bio = db.query(bio).filter(bio.user_id == user_id).first()
        if existing_bio:
            db.delete(existing_bio)
        db.commit()

    return user_id

@pytest.fixture
def auth_headers(setup_database):
    user_id = setup_database
    token = createtokenaccess(user_id)
    return {"Authorization": f"Bearer {token}"}

def test_health_profile_and_recs_before_entries(auth_headers):
    # Setup health profile
    profile_data = {
        "gender": "m",
        "age": 25,
        "weight": 75.0,
        "height": 1.75,
        "activity_level": 3,
        "target_goal": 4,
        "target_steps": 10000
    }
    resp = client.post("/health/me", json=profile_data, headers=auth_headers)
    assert resp.status_code in (201, 409)

    # Check advice before any entries today
    res = client.get("/advice", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 3
    tags = [r["tag"] for r in data["recommendations"]]
    assert any("Старт" in t or "Питание" in t for t in tags)
    assert any("Вода" in t or "водный" in t.lower() for t in tags)

def test_weekly_stats_endpoint(auth_headers):
    # Add a water entry and a food entry for today
    today_str = date.today().isoformat()
    food_entry = {
        "title": "Куриная грудка с гречкой",
        "quantity_grams": 250.0,
        "calories": 350.0,
        "proteins": 45.0,
        "fats": 5.0,
        "carbs": 30.0,
        "product_type": "meatfish"
    }
    r1 = client.post(f"/sheets/me/{today_str}/entries", json=food_entry, headers=auth_headers)
    assert r1.status_code == 201

    water_entry = {
        "title": "Минеральная вода",
        "quantity_grams": 1000.0,
        "water": 1.0,
        "product_type": "beverages"
    }
    r2 = client.post(f"/sheets/me/{today_str}/entries", json=water_entry, headers=auth_headers)
    assert r2.status_code == 201

    # Test /stats/weekly
    res = client.get("/stats/weekly", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["days_recorded"] >= 1
    assert data["average_calories"] > 0
    assert data["average_proteins"] > 0
    assert data["average_water"] > 0
    assert len(data["days"]) == 7
    assert "water_completion_rate" in data
    assert "calorie_adherence_rate" in data

    # Test alias /diary/stats/weekly
    res_alias = client.get("/diary/stats/weekly", headers=auth_headers)
    assert res_alias.status_code == 200
    assert res_alias.json()["days_recorded"] == data["days_recorded"]

def test_summary_stats_endpoint(auth_headers):
    res = client.get("/stats/summary?period_days=14", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["period_days"] == 14
    assert data["total_entries_count"] >= 2
    assert "average_calories" in data
    assert "water_completion_rate" in data
    assert len(data["days"]) == 14

    # Test alias
    res_alias = client.get("/diary/stats/summary?period_days=7", headers=auth_headers)
    assert res_alias.status_code == 200
    assert res_alias.json()["period_days"] == 7

def test_advice_endpoint_with_entries(auth_headers):
    # Test /advice
    res = client.get("/advice", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["calories_consumed"] >= 350.0
    assert data["water_consumed"] >= 1.0

    recs = data["recommendations"]
    assert len(recs) >= 4
    categories = [r["category"] for r in recs]
    assert "hydration" in categories
    assert "nutrition" in categories
    assert "workout" in categories
    assert "recovery" in categories

    # Test aliases
    res_diary_advice = client.get("/diary/advice", headers=auth_headers)
    assert res_diary_advice.status_code == 200

    res_recommendations = client.get("/recommendations", headers=auth_headers)
    assert res_recommendations.status_code == 200

    res_diary_recs = client.get("/diary/recommendations", headers=auth_headers)
    assert res_diary_recs.status_code == 200
