import pytest

from app.services import ipfs as ipfs_module
from app.services.ipfs import IPFSService


def test_ipfs_mock_mode_deterministic(monkeypatch, app):
    # ensure credentials are NOT set → mock mode
    monkeypatch.delenv("PINATA_API_KEY", raising=False)
    monkeypatch.delenv("PINATA_SECRET_API_KEY", raising=False)

    with app.app_context():
        svc = IPFSService()
        assert svc.enabled is False

        data = {"foo": "bar"}
        uri1 = svc.upload_json(data)
        uri2 = svc.upload_json(data)

    assert uri1.startswith("ipfs://Qm")
    # same input → same mock hash
    assert uri1 == uri2


def test_ipfs_with_credentials_uses_pinata(monkeypatch, app):
    monkeypatch.setenv("PINATA_API_KEY", "test-key")
    monkeypatch.setenv("PINATA_SECRET_API_KEY", "test-secret")

    # monkeypatch ONLY requests.post so exceptions stay available
    class DummyResponse:
        def __init__(self):
            self._json = {"IpfsHash": "QmFakeHash123"}

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    calls = {}

    def fake_post(url, json=None, headers=None):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        return DummyResponse()

    monkeypatch.setattr(ipfs_module.requests, "post", fake_post)

    with app.app_context():
        svc = IPFSService()
        assert svc.enabled is True

        uri = svc.upload_json({"hello": "world"}, pin_name="MyPin")

    assert uri == "ipfs://QmFakeHash123"
    assert "pinJSONToIPFS" in calls["url"]
    assert calls["json"]["pinataMetadata"]["name"] == "MyPin"


def test_get_gateway_url_conversion():
    svc = IPFSService()
    url = svc.get_gateway_url("ipfs://QmFakeHash")
    assert url.startswith("https://")
    assert "QmFakeHash" in url
    # passthrough for non-ipfs uris
    assert svc.get_gateway_url("https://example.com") == "https://example.com"