
import json
import logging
from datetime import datetime
from datetime import timezone

import pytest
from fastapi.testclient import TestClient
from src.aula import auditoria
from src.aula.api import main as api
from src.aula.api.main import app

client = TestClient(app)
LOGGER_NAME = "aula.observabilidad"


@pytest.fixture(autouse=True)
def preparar_aplicacion(monkeypatch, tmp_path):
    monkeypatch.setenv("MATRICULA_INICIO", "2020-01-01T00:00:00Z")
    monkeypatch.setenv("MATRICULA_FIN", "2030-01-01T00:00:00Z")
    monkeypatch.setattr(auditoria, "RUTA_TRAZA", tmp_path / "auditoria.jsonl")
    with client:
        yield


def matricula_valida():
    return {
        "estudiante_id": "EST001",
        "curso_academico": "2026-2027",
        "codigos": ["MAT101"]
    }


@pytest.fixture
def eventos_log():
    eventos = []

    class Capturador(logging.Handler):
        def emit(self, registro):
            eventos.append(json.loads(registro.getMessage()))

    logger = logging.getLogger(LOGGER_NAME)
    capturador = Capturador()
    logger.addHandler(capturador)
    try:
        yield eventos
    finally:
        logger.removeHandler(capturador)


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
    assert app.state.matriculas == []
    assert app.state.expedientes == {}
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


@pytest.mark.parametrize(
    ("metodo", "ruta", "cuerpo", "status"),
    [
        ("get", "/salud", None, 200),
        ("post", "/matriculas", matricula_valida(), 201),
        ("get", "/ruta-inexistente", None, 404),
        ("post", "/matriculas", {**matricula_valida(), "codigos": ["NO-EXISTE"]}, 422),
        ("get", "/expedientes/EST001", None, 501),
    ],
)
def test_log_de_acceso_registra_metodo_ruta_y_status(
    eventos_log, metodo, ruta, cuerpo, status
):
    if cuerpo is None:
        respuesta = getattr(client, metodo)(ruta)
    else:
        respuesta = getattr(client, metodo)(ruta, json=cuerpo)

    assert respuesta.status_code == status
    accesos = [evento for evento in eventos_log if evento["event"] == "http.access"]
    assert len(accesos) == 1
    assert accesos[0]["method"] == metodo.upper()
    assert accesos[0]["status"] == status
    assert accesos[0]["route"] == (
        "/expedientes/{estudiante_id}"
        if ruta.startswith("/expedientes/")
        else "unmatched"
        if status == 404
        else ruta
    )
    assert respuesta.headers["X-Correlation-ID"] == accesos[0]["correlation_id"]


def test_log_de_acceso_registra_503(eventos_log, monkeypatch):
    monkeypatch.delenv("MATRICULA_INICIO")

    respuesta = client.post("/matriculas", json=matricula_valida())

    assert respuesta.status_code == 503
    acceso = next(
        evento for evento in eventos_log if evento["event"] == "http.access"
    )
    assert acceso["status"] == 503
    assert respuesta.headers["X-Correlation-ID"] == acceso["correlation_id"]


def test_matricula_exitosa_emite_un_evento_seguro_y_correlacionado(eventos_log):

    respuesta = client.post("/matriculas", json=matricula_valida())

    eventos = eventos_log
    creadas = [evento for evento in eventos if evento["event"] == "matricula.created"]
    acceso = next(evento for evento in eventos if evento["event"] == "http.access")
    assert respuesta.status_code == 201
    assert len(creadas) == 1
    assert creadas[0]["resultado"] == "validada"
    assert creadas[0]["plan"] == "PLAN-2024"
    assert creadas[0]["version_plan"] == "1.2.0"
    assert creadas[0]["numero_asignaturas"] == 1
    assert creadas[0]["creditos_admitidos"] == 6
    assert creadas[0]["correlation_id"] == acceso["correlation_id"]
    assert respuesta.headers["X-Correlation-ID"] == acceso["correlation_id"]
    logs = json.dumps(eventos)
    assert "EST001" not in logs
    assert "MAT101" not in logs
    assert "2026-2027" not in logs


def test_solicitud_rechazada_no_emite_evento_de_creacion(eventos_log):

    respuesta = client.post(
        "/matriculas",
        json={**matricula_valida(), "codigos": ["NO-EXISTE"]},
    )

    assert respuesta.status_code == 422
    assert not any(
        evento["event"] == "matricula.created" for evento in eventos_log
    )


def test_excepcion_inesperada_se_registra_sin_mensaje_sensible(
    eventos_log, monkeypatch
):
    secreto = "MENSAJE-SENSIBLE-DE-PRUEBA"

    def fallar_carga_plan(_codigo):
        raise RuntimeError(secreto)

    monkeypatch.setattr(api, "cargar_plan", fallar_carga_plan)
    respuesta = client.post("/matriculas", json=matricula_valida())

    eventos = eventos_log
    errores = [evento for evento in eventos if evento["event"] == "http.unhandled_error"]
    acceso = next(evento for evento in eventos if evento["event"] == "http.access")
    assert respuesta.status_code == 500
    assert respuesta.text == "Internal Server Error"
    assert respuesta.headers["X-Correlation-ID"] == acceso["correlation_id"]
    assert len(errores) == 1
    assert errores[0]["exception_type"] == "RuntimeError"
    assert errores[0]["traceback"]
    assert errores[0]["correlation_id"] == acceso["correlation_id"]
    logs = json.dumps(eventos)
    assert secreto not in logs
    assert "EST001" not in logs
    assert "MAT101" not in logs


def test_timestamps_de_logs_son_utc(eventos_log):

    client.get("/salud")

    evento = next(
        evento for evento in eventos_log if evento["event"] == "http.access"
    )
    timestamp = datetime.fromisoformat(evento["timestamp"].replace("Z", "+00:00"))
    assert timestamp.tzinfo == timezone.utc
    assert evento["timestamp"].endswith("Z")


@pytest.mark.parametrize(
    ("version_entorno", "esperada"),
    [("release-test-123", "release-test-123"), (None, app.version)],
)
def test_logs_identifican_version_de_entorno_o_fallback(
    eventos_log, monkeypatch, version_entorno, esperada
):
    if version_entorno is None:
        monkeypatch.delenv("AULA_VERSION", raising=False)
    else:
        monkeypatch.setenv("AULA_VERSION", version_entorno)

    client.get("/salud")

    evento = next(
        evento for evento in eventos_log if evento["event"] == "http.access"
    )
    assert evento["version"] == esperada
