
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from src.aula import auditoria
from src.aula.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def preparar_aplicacion(monkeypatch, tmp_path):
    app.state.matriculas.clear()
    app.state.expedientes.clear()
    monkeypatch.setenv("MATRICULA_INICIO", "2020-01-01T00:00:00Z")
    monkeypatch.setenv("MATRICULA_FIN", "2030-01-01T00:00:00Z")
    monkeypatch.setattr(auditoria, "RUTA_TRAZA", tmp_path / "auditoria.jsonl")


def matricula_valida():
    return {
        "estudiante_id": "EST001",
        "curso_academico": "2026-2027",
        "codigos": ["MAT101"]
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

def test_matricula_valida_devuelve_201_y_se_guarda_en_memoria():
    """cubre: SPEC-001/INV-01; crea y conserva el resultado evaluado."""
    response = client.post("/matriculas", json=matricula_valida())
    assert response.status_code == 201
    assert response.json()["estado"] == "validada"
    assert response.json()["plan_aplicado"] == "PLAN-2024"
    assert response.json()["lineas"][0]["codigo_asignatura"] == "MAT101"
    assert len(app.state.matriculas) == 1
    assert app.state.matriculas[0].lineas[0].admitida is True


def test_matricula_registra_una_auditoria_con_plan_y_version():
    client.post("/matriculas", json=matricula_valida())
    entradas = auditoria.leer_traza()
    assert len(entradas) == 1
    assert entradas[0]["plan"] == "PLAN-2024"
    assert entradas[0]["version_plan"] == "1.2.0"


@pytest.mark.parametrize("variable", ["MATRICULA_INICIO", "MATRICULA_FIN"])
def test_matricula_sin_ventana_configurada_devuelve_503(monkeypatch, variable):
    monkeypatch.delenv(variable)
    response = client.post("/matriculas", json=matricula_valida())
    assert response.status_code == 503
    assert variable in response.json()["detail"]
    assert app.state.matriculas == []


@pytest.mark.parametrize("variable", ["MATRICULA_INICIO", "MATRICULA_FIN"])
def test_matricula_ventana_invalida_devuelve_503(monkeypatch, variable):
    monkeypatch.setenv(variable, "no-es-una-fecha")
    response = client.post("/matriculas", json=matricula_valida())
    assert response.status_code == 503
    assert "ISO-8601" in response.json()["detail"]
    assert app.state.matriculas == []


def test_matricula_fuera_de_ventana_se_rechaza_y_no_se_guarda():
    datos = matricula_valida()
    datos["momento"] = "2019-12-31T23:59:59Z"
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422
    assert response.json()["detail"] == "ventana de matricula cerrada"
    assert app.state.matriculas == []
    assert len(auditoria.leer_traza()) == 1


@pytest.mark.parametrize("momento", [
    "2019-12-31T23:59:59Z",
    "2030-01-01T00:00:01Z",
])
def test_matricula_antes_o_despues_de_ventana_devuelve_422(momento):
    datos = matricula_valida()
    datos["momento"] = momento
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422
    assert app.state.matriculas == []


@pytest.mark.parametrize("momento", [
    "2020-01-01T00:00:00Z",
    "2030-01-01T00:00:00Z",
])
def test_matricula_exactamente_en_limites_devuelve_201(momento):
    datos = matricula_valida()
    datos["momento"] = momento
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 201
    assert len(app.state.matriculas) == 1


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


def test_matricula_codigos_desconocidos_devuelve_422():
    datos = matricula_valida()
    datos["codigos"] = ["LEN102"]
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422
    assert app.state.matriculas == []


def test_matricula_codigos_repetidos_devuelve_422():
    datos = matricula_valida()
    datos["codigos"] = ["MAT101", "MAT101"]
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422
    assert app.state.matriculas == []


def test_matricula_momento_no_iso_devuelve_422():
    datos = matricula_valida()
    datos["momento"] = 123
    response = client.post("/matriculas", json=datos)
    assert response.status_code == 422
    assert app.state.matriculas == []


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
