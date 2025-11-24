import json

from app.routes.auth import INSTRUCTOR_WALLET


def test_connect_wallet_student_sets_session(client):
    addr = "0x1111111111111111111111111111111111111111"
    resp = client.post("/auth/connect-wallet", json={"address": addr})
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["success"] is True
    assert data["address"] == addr.lower()
    assert data["is_instructor"] is False
    assert data["redirect"] == "/student/portal"

    # session persisted
    with client.session_transaction() as sess:
        assert sess["wallet_address"] == addr.lower()
        assert sess["is_instructor"] is False


def test_connect_wallet_instructor_redirects_dashboard(client):
    resp = client.post("/auth/connect-wallet", json={"address": INSTRUCTOR_WALLET})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["is_instructor"] is True
    assert data["redirect"] == "/instructor/dashboard"

    with client.session_transaction() as sess:
        assert sess["wallet_address"] == INSTRUCTOR_WALLET.lower()
        assert sess["is_instructor"] is True


def test_connect_wallet_missing_address(client):
    resp = client.post("/auth/connect-wallet", json={})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "No wallet address provided" in data["error"]


def test_disconnect_wallet_clears_session(client):
    # seed session
    with client.session_transaction() as sess:
        sess["wallet_address"] = "0xabc"
        sess["is_instructor"] = True

    resp = client.post("/auth/disconnect")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True

    with client.session_transaction() as sess:
        assert "wallet_address" not in sess
        assert "is_instructor" not in sess


def test_check_session_not_connected(client):
    resp = client.get("/auth/check-session")
    data = resp.get_json()
    assert data["connected"] is False
    assert data["address"] is None
    assert data["is_instructor"] is False


def test_check_session_connected(client):
    with client.session_transaction() as sess:
        sess["wallet_address"] = "0xabc"
        sess["is_instructor"] = False

    resp = client.get("/auth/check-session")
    data = resp.get_json()
    assert data["connected"] is True
    assert data["address"] == "0xabc"
    assert data["is_instructor"] is False