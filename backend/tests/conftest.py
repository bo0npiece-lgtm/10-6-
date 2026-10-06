import os
import tempfile

# app 모듈을 import 하기 전에 테스트 전용 DB로 교체
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as c:  # lifespan: 테이블 + 샘플 방 생성
        yield c


@pytest.fixture
def make_user(client):
    def _make(nickname):
        r = client.post("/users", json={"nickname": nickname})
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _make


@pytest.fixture
def make_study(client):
    def _make(owner_id, capacity=4, title="스터디"):
        r = client.post("/studies", json={"owner_id": owner_id, "title": title, "capacity": capacity})
        assert r.status_code == 201, r.text
        return r.json()["id"]
    return _make


@pytest.fixture
def join(client):
    """신청 + 승인으로 멤버를 추가한다."""
    def _join(study_id, owner_id, user_id):
        a = client.post(f"/studies/{study_id}/applications", json={"user_id": user_id})
        assert a.status_code == 201, a.text
        r = client.post(f"/applications/{a.json()['id']}/approve", json={"user_id": owner_id})
        assert r.status_code == 200, r.text
    return _join
