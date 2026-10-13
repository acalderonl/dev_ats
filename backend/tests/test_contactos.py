def test_contacto_aparece_tras_postular(client, reclutador_headers, unique_suffix, crear_cargo, crear_vacante):
    cargo = crear_cargo(unique_suffix)
    vacante = crear_vacante(cargo["id"])

    cedula = f"19{unique_suffix[:8]}"
    client.post(
        f"/api/v1/public/vacantes/{vacante['slug']}/postular",
        json={"nombres": "Luis", "apellidos": "Torres", "cedula": cedula, "email": "luis.torres@example.com"},
    )

    response = client.get("/api/v1/contactos", params={"q": "Luis Torres"}, headers=reclutador_headers)
    assert response.status_code == 200
    contactos = response.json()
    assert any(c["cedula"] == cedula for c in contactos)
    contacto = next(c for c in contactos if c["cedula"] == cedula)
    assert contacto["total_postulaciones"] == 1
    assert contacto["ultimo_estado_pipeline"] == "pendiente_autorizacion"
