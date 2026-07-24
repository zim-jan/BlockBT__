
import pytest
from fastapi.testclient import TestClient

from app.db.session import get_session, init_db
from app.main import app
from app.models.orm import AppSetting
from app.models.user import User
from app.services.auth import hash_password


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_users():
    """Ensure users table is reset before each test and enable auth temporarily."""
    init_db()
    with get_session() as db:
        db.query(User).delete()
        setting = db.get(AppSetting, "auth_enabled")
        if not setting:
            db.add(AppSetting(key="auth_enabled", value="true"))
        else:
            setting.value = "true"
        db.commit()
    yield
    with get_session() as db:
        db.query(User).delete()
        setting = db.get(AppSetting, "auth_enabled")
        if setting:
            setting.value = "false"
        db.commit()


def test_auth_status_public(client):
    response = client.get("/api/auth/auth-status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "auth_enabled" in data["data"]


def test_login_success_and_me(client):
    # Seed user
    with get_session() as db:
        user = User(
            username="testuser",
            password_hash=hash_password("secret123"),
            role="user",
        )
        db.add(user)
        db.commit()

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "secret123"},
    )
    assert login_res.status_code == 200
    res_json = login_res.json()
    assert res_json["success"] is True
    token = res_json["data"]["access_token"]
    assert token is not None

    # Get /me with token
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()["data"]
    assert me_data["username"] == "testuser"
    assert me_data["role"] == "user"


def test_login_invalid_credentials(client):
    res = client.post(
        "/api/auth/login",
        json={"username": "nonexistent", "password": "bad"},
    )
    assert res.status_code == 401


def test_admin_user_crud(client):
    # Seed admin and regular user
    with get_session() as db:
        admin = User(username="admin1", password_hash=hash_password("adminpass"), role="admin")
        user = User(username="user1", password_hash=hash_password("userpass"), role="user")
        db.add_all([admin, user])
        db.commit()

    # Get admin token
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin1", "password": "adminpass"},
    )
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List users
    list_res = client.get("/api/auth/users", headers=headers)
    assert list_res.status_code == 200
    users = list_res.json()["data"]
    assert len(users) == 2

    # Create new user
    create_res = client.post(
        "/api/auth/users",
        headers=headers,
        json={"username": "user2", "password": "password123", "role": "user"},
    )
    assert create_res.status_code == 200
    created_id = create_res.json()["data"]["id"]

    # Update user
    update_res = client.put(
        f"/api/auth/users/{created_id}",
        headers=headers,
        json={"role": "admin"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["role"] == "admin"

    # Delete user
    delete_res = client.delete(f"/api/auth/users/{created_id}", headers=headers)
    assert delete_res.status_code == 200


def test_user_id_populated_on_strategy_and_job_creation(client):
    from app.models.orm import BacktestJob, Strategy
    
    # Create user
    with get_session() as db:
        user = User(username="quant", password_hash=hash_password("pass123"), role="user")
        db.add(user)
        db.commit()
        user_id = user.id

    # Login to get JWT
    res = client.post("/api/auth/login", json={"username": "quant", "password": "pass123"})
    token = res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create strategy via API with Bearer token
    strat_res = client.post(
        "/api/strategies/",
        headers=headers,
        json={"name": "My Quant Strat", "description": "Test", "code_content": "", "parameters": {}},
    )
    assert strat_res.status_code == 201
    strat_id = int(strat_res.json()["data"]["id"])

    # Verify user_id is populated in DB for Strategy
    with get_session() as db:
        strat = db.get(Strategy, strat_id)
        assert strat is not None
        assert strat.user_id == user_id

    # Trigger backtest via API with Bearer token
    bt_res = client.post(
        "/api/backtest/",
        headers=headers,
        json={"strategy_id": strat_id, "symbol": "AAPL"},
    )
    assert bt_res.status_code == 202
    job_id = bt_res.json()["data"]["job_id"]

    # Verify user_id is populated in DB for BacktestJob
    with get_session() as db:
        job = db.get(BacktestJob, job_id)
        assert job is not None
        assert job.user_id == user_id
