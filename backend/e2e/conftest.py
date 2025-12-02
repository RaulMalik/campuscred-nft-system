import pytest
import sys
import os
import threading
import time
from werkzeug.serving import make_server
from pathlib import Path

# add backend to path so we can import app
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import create_app, db
from app.models import Claim


# mock Blockchain Service, i would prefer we avoid real Web3 calls during UI tests
class MockBlockchainService:
    def mint_credential(self, recipient_address, metadata_uri):
        # Return fake token_id and tx_hash
        return 999, "0x" + "a" * 64

    def verify_credential(self, token_id):
        return {
            'exists': True,
            'owner': '0xabc...',
            'token_uri': 'ipfs://mock',
            'is_revoked': False
        }


@pytest.fixture(scope="session")
def mock_blockchain_service():
    # Patches the BlockchainService class in the app
    import app.services.blockchain as blockchain_module
    original = blockchain_module.BlockchainService
    blockchain_module.BlockchainService = MockBlockchainService
    yield
    blockchain_module.BlockchainService = original


@pytest.fixture(scope="session")
def base_url(mock_blockchain_service):
    """
    Starts the Flask server in a separate thread.
    Returns the localhost URL.
    """
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # Use in-memory DB
        "WTF_CSRF_ENABLED": False
    })

    # create an empty port (0 allows OS to pick one)
    port = 5001

    # Initialize DB
    with app.app_context():
        db.create_all()

    server = make_server('127.0.0.1', port, app)

    # server in thread
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    time.sleep(1)

    yield f"http://127.0.0.1:{port}"

    server.shutdown()
    thread.join()


@pytest.fixture(scope="function")
def context(browser):
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    yield page
    page.close()