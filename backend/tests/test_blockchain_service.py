import pytest

from app.services.blockchain import BlockchainService


def test_initialize_requires_rpc_url(monkeypatch):
    monkeypatch.delenv("SEPOLIA_RPC_URL", raising=False)
    svc = BlockchainService()
    with pytest.raises(ValueError):
        svc.initialize()


def test_verify_credential_handles_contract_error(app):
    """
    verify_credential logs to current_app.logger, so we need an app context.
    We stub the contract so ownerOf().call() raises.
    """
    svc = BlockchainService()
    svc.w3 = object()  # prevents initialize() from running

    class DummyContract:
        class Functions:
            def ownerOf(self, token_id):
                class Call:
                    def call(self_inner):
                        raise Exception("boom")

                return Call()

        functions = Functions()

    svc.contract = DummyContract()

    with app.app_context():
        result = svc.verify_credential(1)

    assert result["exists"] is False
    assert "error" in result


def test_get_balance_uses_web3():
    """
    get_balance uses Web3.to_checksum_address and w3.eth.get_balance + from_wei.
    We supply a dummy Web3 and a valid-looking address.
    """

    class DummyEth:
        def get_balance(self, addr):
            # pretend they have 1 ether in wei
            return 10**18

    class DummyWeb3:
        def __init__(self):
            self.eth = DummyEth()

        def from_wei(self, value, unit):
            assert unit == "ether"
            return value // 10**18

    svc = BlockchainService()
    svc.w3 = DummyWeb3()

    # valid 20-byte hex address so Web3.to_checksum_address accepts it
    addr = "0x" + "1" * 40
    bal = svc.get_balance(addr)
    assert bal == 1