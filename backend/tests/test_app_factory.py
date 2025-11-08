def test_app_factory_registers_blueprints(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    from app import create_app, db
    app = create_app()
    with app.app_context():
        # blueprints hit the __init__.py lines
        assert set(["home","auth","student","instructor","verify"]).issubset(app.blueprints.keys())
        # uses the temp DB, not your real one
        assert db.engine.url.database.endswith("test.db")