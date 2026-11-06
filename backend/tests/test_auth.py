def test_register_y_login(client, unique_suffix):
    email = f"nuevo_{unique_suffix}@example.com"
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Segura123!", "nombres": "Test", "apellidos": "User"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == email
    assert body["rol"] == "reclutador"

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": "Segura123!"})
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_login_credenciales_invalidas(client):
    response = client.post("/api/v1/auth/login", json={"email": "admin@atsdemo.com", "password": "clave-incorrecta"})
    assert response.status_code == 401


def test_registro_duplicado(client, unique_suffix):
    email = f"dup_{unique_suffix}@example.com"
    payload = {"email": email, "password": "Segura123!", "nombres": "Dup", "apellidos": "User"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400


def test_me_requiere_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_con_token(client, reclutador_headers):
    response = client.get("/api/v1/auth/me", headers=reclutador_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "reclutador@atsdemo.com"
