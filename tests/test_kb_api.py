import os
import sys

# Set DATABASE_URL before importing config or database
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(backend_dir, "tether.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

pyth_dir = os.path.join(backend_dir, "pyth")
if pyth_dir not in sys.path:
    sys.path.insert(0, pyth_dir)

import pytest
from fastapi.testclient import TestClient

from kb.database import engine as kb_engine, SessionLocal as KbSessionLocal
from kb.models import Base as KbBase, kbarticle
from kb.seed_kb import seedkb
from kb.main import app

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_kb_database():
    KbBase.metadata.create_all(bind=kb_engine)
    with KbSessionLocal() as db:
        seedkb(db)

def test_kb_health_status():
    resp = client.get("/health/status")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "kb"}

def test_list_all_articles():
    resp = client.get("/kb")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 20

def test_filter_articles_by_category():
    resp = client.get("/kb?category=standards")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    for item in data:
        assert item["category"] == "standards"

def test_list_all_blocks():
    resp = client.get("/kb/blocks")
    assert resp.status_code == 200
    blocks = resp.json()
    assert isinstance(blocks, list)
    assert len(blocks) >= 6
    assert "Гидратация и питьевой режим" in blocks
    assert "Калории, энергетический баланс и метаболизм" in blocks

def test_filter_articles_by_block():
    target_block = "Гидратация и питьевой режим"
    resp = client.get(f"/kb?block={target_block}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 8
    for item in data:
        assert item["block"] == target_block

def test_search_with_block_filter():
    target_block = "Стандарты, маркировка и законы"
    resp = client.get(f"/kb/search?q=калорийность&block={target_block}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for item in data:
        assert item["block"] == target_block

def test_search_articles_single_keyword():
    resp = client.get("/kb/search?q=FDA")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("FDA" in item["answer"] or "FDA" in item["question"] or (item.get("tags") and "FDA" in item["tags"]) for item in data)

def test_search_articles_multi_keywords():
    resp = client.get("/kb/search?q=калорийность упаковка")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    # Check that the FDA / packaging question was matched
    questions = [item["question"] for item in data]
    assert any("упаковки" in q for q in questions)

def test_search_inedible_parts():
    resp = client.get("/kb/search?q=несъедобная часть")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any("несъедобную часть" in item["question"] for item in data)

def test_search_with_category_filter():
    resp = client.get("/kb/search?q=калорийность&category=standards")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    for item in data:
        assert item["category"] == "standards"

def test_get_article_by_id():
    resp = client.get("/kb/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "question" in data
    assert "answer" in data

def test_get_nonexistent_article():
    resp = client.get("/kb/999999")
    assert resp.status_code == 404
    assert "не найдена" in resp.json()["detail"]

def test_admin_auth_required():
    # Without admin key
    new_art = {
        "question": "Тестовый вопрос без ключа?",
        "answer": "Тестовый ответ",
        "category": "general"
    }
    resp = client.post("/kb", json=new_art)
    assert resp.status_code in (403, 422)

    # With invalid key
    resp = client.post("/kb", json=new_art, headers={"X-Admin-Key": "wrong_key"})
    assert resp.status_code == 403

def test_crud_article_admin():
    admin_headers = {"X-Admin-Key": "tester"}
    
    # 1. Create article
    new_article_data = {
        "question": "Какова калорийность чистого спирта (алкоголя)?",
        "answer": "Чистый этиловый спирт содержит примерно 7 ккал на 1 грамм. Это больше, чем у белков и углеводов (4 ккал/г), но меньше, чем у жиров (9 ккал/г).",
        "category": "calories",
        "tags": "алкоголь,спирт,калорийность,грамм"
    }
    create_resp = client.post("/kb", json=new_article_data, headers=admin_headers)
    assert create_resp.status_code == 201
    created = create_resp.json()
    art_id = created["id"]
    assert created["question"] == new_article_data["question"]
    assert created["category"] == "calories"

    # 2. Search for the newly created article
    search_resp = client.get("/kb/search?q=спирт алкоголь")
    assert search_resp.status_code == 200
    assert any(item["id"] == art_id for item in search_resp.json())

    # 3. Update article
    update_data = {
        "answer": "Чистый этиловый спирт содержит 7.1 ккал на 1 грамм. При этом эти калории называют «пустыми», так как спирт не содержит питательных веществ."
    }
    patch_resp = client.patch(f"/kb/{art_id}", json=update_data, headers=admin_headers)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert "пустыми" in updated["answer"]

    # 4. Delete article
    del_resp = client.delete(f"/kb/{art_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    # 5. Verify deleted
    get_resp = client.get(f"/kb/{art_id}")
    assert get_resp.status_code == 404

def test_articles_have_blocks_and_no_bullets_or_em_dashes():
    resp = client.get("/kb")
    assert resp.status_code == 200
    articles = resp.json()
    assert len(articles) >= 100
    valid_blocks = {
        "Гидратация и питьевой режим",
        "Стандарты, маркировка и законы",
        "Нутриенты, витамины и макроэлементы",
        "Методы взвешивания, расчёта и учёта",
        "Калории, энергетический баланс и метаболизм",
        "Общие вопросы питания, физиологии и психологии",
    }
    for a in articles:
        assert a["block"] in valid_blocks, f"Article {a['id']} has invalid or missing block: {a['block']}"
        assert "—" not in a["question"], f"Article {a['id']} has em-dash in question"
        assert "—" not in a["answer"], f"Article {a['id']} has em-dash in answer"
        assert "•" not in a["answer"], f"Article {a['id']} has bullet in answer"

def test_kb_root_redirect():
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code in (307, 308)
    assert resp.headers["location"] == "/docs"

def test_kb_pagination_headers_and_slices():
    # Page 1, size 5
    resp = client.get("/kb?page=1&page_size=5")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5
    assert int(resp.headers["X-Total-Count"]) >= 100
    assert resp.headers["X-Page"] == "1"
    assert resp.headers["X-Page-Size"] == "5"
    assert resp.headers["X-Has-Next"] == "true"
    assert resp.headers["X-Has-Prev"] == "false"
    first_page_ids = [item["id"] for item in data]

    # Page 2, size 5
    resp2 = client.get("/kb?page=2&page_size=5")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 5
    assert resp2.headers["X-Page"] == "2"
    assert resp2.headers["X-Has-Prev"] == "true"
    second_page_ids = [item["id"] for item in data2]

    # Verify no overlap
    assert set(first_page_ids).isdisjoint(set(second_page_ids))

def test_kb_offset_limit_pagination():
    resp = client.get("/kb?limit=3&offset=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert resp.headers["X-Page-Size"] == "3"

def test_kb_filter_block_with_pagination():
    block = "Гидратация и питьевой режим"
    resp = client.get(f"/kb?block={block}&page=1&page_size=3")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    assert resp.headers["X-Total-Count"] == "10"
    assert resp.headers["X-Total-Pages"] == "4"
    for item in data:
        assert item["block"] == block

def test_kb_filter_keywords_in_main_endpoint():
    # Search via /kb?q=
    resp = client.get("/kb?q=вода&page=1&page_size=4")
    assert resp.status_code == 200
    data = resp.json()
    assert 1 <= len(data) <= 4
    assert int(resp.headers["X-Total-Count"]) >= 1

    # Search via /kb?block=...&q=...
    block = "Гидратация и питьевой режим"
    resp2 = client.get(f"/kb?block={block}&q=вода")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) >= 1
    for item in data2:
        assert item["block"] == block

def test_kb_paginated_json_endpoint():
    resp = client.get("/kb/paginated?page=1&page_size=10")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert "page" in body
    assert "page_size" in body
    assert "total_pages" in body
    assert "has_next" in body
    assert "has_prev" in body

    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) == 10
    assert body["total"] >= 100
    assert body["total_pages"] >= 10
    assert body["has_next"] is True
    assert body["has_prev"] is False

    # Block filter with JSON paginated
    block = "Методы взвешивания, расчёта и учёта"
    resp_block = client.get(f"/kb/paginated?block={block}&page=1&page_size=5")
    assert resp_block.status_code == 200
    body_block = resp_block.json()
    assert len(body_block["items"]) <= 5
    for it in body_block["items"]:
        assert it["block"] == block

def test_kb_search_pagination():
    resp = client.get("/kb/search?q=калорийность&page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert resp.headers["X-Page"] == "1"
    assert resp.headers["X-Page-Size"] == "2"
    assert int(resp.headers["X-Total-Count"]) >= 2

def test_kb_validation_errors():
    # Empty query in /kb/search -> 422
    resp_empty_q = client.get("/kb/search?q=")
    assert resp_empty_q.status_code == 422

    # Non-integer aid in /kb/{aid} -> 422
    resp_str_aid = client.get("/kb/not_a_number")
    assert resp_str_aid.status_code == 422

    # Short question in POST -> 422
    admin_headers = {"X-Admin-Key": "tester"}
    resp_short_q = client.post("/kb", json={"question": "a", "answer": "valid"}, headers=admin_headers)
    assert resp_short_q.status_code == 422

    # Missing answer in POST -> 422
    resp_no_ans = client.post("/kb", json={"question": "Нормальный вопрос?"}, headers=admin_headers)
    assert resp_no_ans.status_code == 422

    # Negative page or page_size -> 422
    resp_bad_page = client.get("/kb?page=0")
    assert resp_bad_page.status_code == 422
    resp_bad_size = client.get("/kb?page_size=1000")
    assert resp_bad_size.status_code == 422

def test_kb_nonexistent_ids():
    admin_headers = {"X-Admin-Key": "tester"}
    # GET 404
    assert client.get("/kb/9999999").status_code == 404
    # PATCH 404
    assert client.patch("/kb/9999999", json={"answer": "abc"}, headers=admin_headers).status_code == 404
    # DELETE 404
    assert client.delete("/kb/9999999", headers=admin_headers).status_code == 404

