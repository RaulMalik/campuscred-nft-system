from datetime import datetime
import time

import pytest

from app import db
from app.models import Claim
from app.routes import verify as verify_module


@pytest.fixture
def minted_claim(app):
    """
    Create a fully-minted claim used by /verify routes.

    We return a simple dict of identifiers instead of a live SQLAlchemy object,
    to avoid DetachedInstanceError outside the app context.
    """
    with app.app_context():
        verify_module.verifier_links.clear()

        claim = Claim(
            student_name="Alice",
            student_email="alice@example.com",
            credential_type="micro-credential",
            course_code="02369",
            description="Test credential",
            status="minted",
            student_address="0xabc1234567890123456789012345678901234567",
            token_id=123,
            evidence_file_hash="a" * 64,
            evidence_file_name="evidence.pdf",
            transaction_hash="0x" + "1" * 64,
        )
        claim.minted_at = datetime.utcnow()
        claim.evidence_file_path = "dummy/path.pdf"
        db.session.add(claim)
        db.session.commit()

        return {
            "id": claim.id,
            "token_id": claim.token_id,
            "wallet": claim.student_address,
        }


class DummyBlockchain:
    def __init__(self, exists=True, revoked=False):
        self.exists = exists
        self.revoked = revoked

    def verify_credential(self, token_id):
        if not self.exists:
            return {"exists": False}
        return {
            "exists": True,
            "owner": "0xabc1234567890123456789012345678901234567",
            "token_uri": "ipfs://test",
            "is_revoked": self.revoked,
            "token_id": token_id,
        }


def test_verify_credential_happy_path(client, minted_claim, monkeypatch):
    # stub out real Web3 calls
    monkeypatch.setattr(
        verify_module, "BlockchainService", lambda: DummyBlockchain(exists=True)
    )

    resp = client.get(f"/verify/credential/{minted_claim['token_id']}")
    assert resp.status_code == 200
    assert b"Verified Credential" in resp.data
    assert str(minted_claim["token_id"]).encode() in resp.data
    # course code we set in the fixture
    assert b"02369" in resp.data


def test_verify_credential_not_found_db(client):
    resp = client.get("/verify/credential/999999")
    assert resp.status_code == 200
    assert b"not found" in resp.data.lower()


def test_generate_verifier_link_success(client, minted_claim):
    resp = client.post(
        f"/verify/generate-verifier-link/{minted_claim['token_id']}",
        json={"wallet_address": minted_claim["wallet"]},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["expires_in"] == 900
    assert data["verifier_url"].startswith("/verify/private/")

    token = data["verifier_url"].split("/")[-1]
    assert token in verify_module.verifier_links
    stored = verify_module.verifier_links[token]
    assert stored["token_id"] == minted_claim["token_id"]
    assert stored["claim_id"] == minted_claim["id"]


def test_generate_verifier_link_wrong_owner_forbidden(client, minted_claim):
    resp = client.post(
        f"/verify/generate-verifier-link/{minted_claim['token_id']}",
        json={"wallet_address": "0xdeadbeef"},
    )
    assert resp.status_code == 403
    data = resp.get_json()
    assert data["success"] is False
    assert "Only credential owner" in data["error"]


def _get_verifier_token(client, minted_claim):
    resp = client.post(
        f"/verify/generate-verifier-link/{minted_claim['token_id']}",
        json={"wallet_address": minted_claim["wallet"]},
    )
    return resp.get_json()["verifier_url"].split("/")[-1]


def test_view_private_credential_with_valid_token(client, minted_claim):
    token = _get_verifier_token(client, minted_claim)

    resp = client.get(f"/verify/private/{token}")
    assert resp.status_code == 200
    # private info should be present
    assert b"Private Information Disclosed" in resp.data
    assert b"alice@example.com" in resp.data
    assert b"evidence.pdf" in resp.data


def test_view_private_credential_expired_token(client, minted_claim):
    token = _get_verifier_token(client, minted_claim)

    # Force-expire the token
    verify_module.verifier_links[token]["expires_at"] = time.time() - 10

    resp = client.get(f"/verify/private/{token}")
    assert resp.status_code == 200
    assert b"expired" in resp.data.lower()
    # token should be cleaned up
    assert token not in verify_module.verifier_links


def test_download_evidence_pdf_signed(client, minted_claim, monkeypatch):
    # create a valid verifier token
    token = _get_verifier_token(client, minted_claim)

    class DummyStorage:
        def get_file(self, path):
            # minimal but valid-ish PDF bytes
            return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

    class DummySigner:
        def __init__(self):
            self.last_metadata = None

        def sign_pdf(self, content, metadata=None):
            self.last_metadata = metadata
            return content + b"SIGNED"

    dummy_storage = DummyStorage()
    dummy_signer = DummySigner()

    monkeypatch.setattr(verify_module, "storage_service", dummy_storage)
    monkeypatch.setattr(verify_module, "pdf_signer", dummy_signer)

    resp = client.get(f"/verify/download-evidence/{token}")
    assert resp.status_code == 200
    assert resp.mimetype == "application/pdf"
    assert resp.data.endswith(b"SIGNED")
    # metadata passed to signer
    assert dummy_signer.last_metadata is not None
    assert "Academic Credential Evidence" in dummy_signer.last_metadata.get(
        "subject", ""
    )


def test_download_evidence_invalid_token(client):
    resp = client.get("/verify/download-evidence/not-a-real-token")
    assert resp.status_code == 403