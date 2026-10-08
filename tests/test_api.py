
from datetime import datetime

from fastapi.testclient import TestClient
from src.aula.api.main import app

client = TestClient(app)


def matricula_valida():
    return {
        "estudiante_id": "EST001",
        "curso_academico": "2026-2027",
        "codigos": ["MAT101", "LEN102"]
    }


# GET /salud

def test_salud_devuelve_200():
    response = client.get("/salud")
    assert response.status_code == 200


def test_salud_devuelve_estado_ok():
    response = client.get("/salud")
    assert response.json()["estado"] == "ok"


def test_salud_incluye_momento():
    response = client.get("/salud")
    assert "momento" in response.json()


def test_salud_momento_es_fecha_valida():
    response = client.get("/salud")
    momento = response.json()["momento"]
    fecha = datetime.fromisoformat(momento)
    assert fecha.tzinfo is not None


def test_salud_devuelve_json():
    response = client.get("/salud")
    assert response.headers["content-type"] == "application/json"


# POST /matriculas

def test_matricula_valida_devuelve_501():
    response = client.post("/matriculas", json=matricula_valida())
    assert response.status_code == 501


def test_matricula_devuelve_mensaje_pendiente():
    response = client.post("/matriculas", json=matricula_valida())
    assert response.json()["detail"] == "S1: alta de matricula pendiente"


def test_matricula_sin_estudiante_devuelve_422():
    datos = matricula_valida()
    del datos["estudiante_id"]

    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422


def test_matricula_sin_curso_devuelve_422():
    datos = matricula_valida()
    del datos["curso_academico"]

    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422


def test_matricula_sin_codigos_devuelve_422():
    datos = matricula_valida()
    del datos["codigos"]

    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422


def test_matricula_codigos_incorrectos_devuelve_422():
    datos = matricula_valida()
    datos["codigos"] = "MAT101"

    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422


def test_matricula_estudiante_numerico_devuelve_422():
    datos = matricula_valida()
    datos["estudiante_id"] = 123

    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422


# GET /expedientes

def test_expediente_devuelve_501():
    response = client.get("/expedientes/EST001")
    assert response.status_code == 501


def test_expediente_devuelve_mensaje_pendiente():
    response = client.get("/expedientes/EST001")
    assert response.json()["detail"] == "S2: consulta de expediente pendiente"


def test_ruta_inexistente_devuelve_404():
    response = client.get("/ruta-inexistente")
    assert response.status_code == 404
