from app.services.storage import StorageService
def test_allowed_file_none():
    assert StorageService().allowed_file(None) is False

def test_file_exists_and_delete(tmp_path):
    s = StorageService(base_path=str(tmp_path))
    p = tmp_path / "x.txt"
    p.write_text("hi")
    assert s.file_exists(str(p)) is True
    assert s.delete_file(str(p)) is True
    assert s.file_exists(str(p)) is False
    # deleting non-existent should be False
    assert s.delete_file(str(p)) is False