def test_metricas_dashboard(client, reclutador_headers):
    response = client.get("/api/v1/dashboard/metrics", headers=reclutador_headers)
    assert response.status_code == 200
    body = response.json()
    for campo in [
        "vacantes_activas",
        "vacantes_expiradas",
        "postulaciones_totales",
        "postulaciones_por_etapa",
        "postulaciones_por_origen",
        "entrevistas_pendientes",
    ]:
        assert campo in body
    assert isinstance(body["postulaciones_por_etapa"], list)
