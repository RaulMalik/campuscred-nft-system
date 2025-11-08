def test_auth_html(client):
    r = client.get("/auth/test-html")
    assert r.status_code == 200
    assert b"CampusCred Test" in r.data

def test_verify_page(client):
    r = client.get("/verify/")
    assert r.status_code == 200
    assert b"Verify Credential" in r.data

def test_about_page(client):
    r = client.get("/about")
    assert r.status_code == 200