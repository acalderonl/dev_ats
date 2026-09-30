import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.seed import DEMO_USERS


@pytest.fixture(scope="session", autouse=True)
def _crear_tablas():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def admin_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[0]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def reclutador_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[1]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def entrevistador_headers(client: TestClient) -> dict[str, str]:
    email, password, *_ = DEMO_USERS[2]
    token = login(client, email, password)
    return {"Authorization": f"Bearer {token}"}
