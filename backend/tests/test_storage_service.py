"""
Tests for storage service
"""
import pytest
from app.services.storage import StorageService
import io
import os


class TestStorageService:
    """Test file storage functionality"""

    @pytest.fixture
    def storage(self, tmp_path):
        """Create storage service with temp directory"""
        storage_path = tmp_path / "test_storage"
        storage_path.mkdir()
        return StorageService(base_path=str(storage_path))

    def test_allowed_file_valid(self, storage):
        """Test that valid file types are allowed"""
        assert storage.allowed_file('test.pdf') is True
        assert storage.allowed_file('test.png') is True
        assert storage.allowed_file('test.jpg') is True
        assert storage.allowed_file('test.doc') is True

    def test_allowed_file_invalid(self, storage):
        """Test that invalid file types are rejected"""
        assert storage.allowed_file('test.exe') is False
        assert storage.allowed_file('test.sh') is False
        assert storage.allowed_file('noextension') is False

    def test_save_evidence_file(self, storage):
        """Test saving a file"""

        # Create fake file
        class FakeFile:
            def __init__(self):
                self.filename = 'evidence.pdf'

            def save(self, path):
                with open(path, 'w') as f:
                    f.write('test content')

        fake_file = FakeFile()
        file_path, original_name = storage.save_evidence_file(fake_file, claim_id=1)

        assert file_path is not None
        assert original_name == 'evidence.pdf'
        assert os.path.exists(file_path)
        assert 'claim_1_' in file_path

    def test_save_invalid_file(self, storage):
        """Test saving invalid file returns None"""

        class FakeFile:
            def __init__(self):
                self.filename = 'malware.exe'

        fake_file = FakeFile()
        file_path, original_name = storage.save_evidence_file(fake_file, claim_id=1)

        assert file_path is None
        assert original_name is None