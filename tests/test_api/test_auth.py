from fastapi.testclient import TestClient


class TestAuthAPI:
    REGISTER_URL = "/api/v1/auth/register"
    LOGIN_URL = "/api/v1/auth/login"
    ME_URL = "/api/v1/auth/me"

    def test_register_success(self, client: TestClient):
        resp = client.post(self.REGISTER_URL, json={
            "email": "nuevo@test.com",
            "password": "Secure123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["email"] == "nuevo@test.com"
        assert data["token_type"] == "bearer"

    def test_register_weak_password(self, client: TestClient):
        resp = client.post(self.REGISTER_URL, json={
            "email": "weak@test.com",
            "password": "123",
        })
        assert resp.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        resp = client.post(self.REGISTER_URL, json={
            "email": "no-es-email",
            "password": "Secure123",
        })
        assert resp.status_code == 422

    def test_register_duplicate_email(self, client: TestClient):
        payload = {"email": "dupe@test.com", "password": "Secure123"}
        resp1 = client.post(self.REGISTER_URL, json=payload)
        assert resp1.status_code == 200
        resp2 = client.post(self.REGISTER_URL, json=payload)
        assert resp2.status_code == 409

    def test_login_success(self, client: TestClient, test_user):
        resp = client.post(self.LOGIN_URL, data={
            "username": test_user.email,
            "password": "Test1234",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, test_user):
        resp = client.post(self.LOGIN_URL, data={
            "username": test_user.email,
            "password": "WrongPass1",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        resp = client.post(self.LOGIN_URL, data={
            "username": "noexiste@test.com",
            "password": "Test1234",
        })
        assert resp.status_code == 401

    def test_me_authenticated(self, client: TestClient, test_user, token):
        resp = client.get(self.ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == test_user.email
        assert data["activo"] is True

    def test_me_no_auth(self):
        from fastapi.testclient import TestClient
        from app.main import app
        app.dependency_overrides.clear()
        c = TestClient(app)
        resp = c.get(self.ME_URL)
        assert resp.status_code == 401

    def test_register_password_no_mayuscula(self, client: TestClient):
        resp = client.post(self.REGISTER_URL, json={
            "email": "test@test.com",
            "password": "solominusculas1",
        })
        assert resp.status_code == 400

    def test_register_password_no_digit(self, client: TestClient):
        resp = client.post(self.REGISTER_URL, json={
            "email": "test@test.com",
            "password": "SinDigitos",
        })
        assert resp.status_code == 400
