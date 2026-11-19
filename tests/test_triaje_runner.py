
from agentes.triaje import runner


def test_runner_entrega_evidencias_completas(monkeypatch, capsys):
    """El runner entrega JUnit y logs sin perder información."""

    evidencia = {
        "run_id": "123",
        "status": "completed",
        "conclusion": "failure",
        "logs": "AssertionError en media ponderada",
        "pytest": {
            "disponible": True,
            "total": 2,
            "passed": 1,
            "failed": 1,
            "errors": 0,
            "skipped": 0,
            "fallos": [
                {
                    "test": "test_media_ponderada",
                    "tipo": "AssertionError",
                    "mensaje": "Esperado 7.25, obtenido 116.00",
                    "categoria": "failure",
                }
            ],
        },
    }

    recibido = {}

    def analizar_simulado(run_id, contexto):
        recibido["run_id"] = run_id
        recibido["contexto"] = contexto
        return {
            "run_id": run_id,
            "clasificacion": "tests",
            "hipotesis": "Fallo de aserción",
            "spec_id": None,
            "handoff": None,
        }

    monkeypatch.setattr(
        runner,
        "resultado_tests",
        lambda args: evidencia,
    )
    monkeypatch.setattr(
        runner,
        "analizar",
        analizar_simulado,
    )

    resultado = runner.ejecutar("123")

    assert recibido["run_id"] == "123"
    assert recibido["contexto"]["resultado_tests"] == evidencia
    assert recibido["contexto"]["resultado_tests"]["logs"] == (
        "AssertionError en media ponderada"
    )
    assert recibido["contexto"]["resultado_tests"]["pytest"]["fallos"][0][
        "test"
    ] == "test_media_ponderada"

    assert resultado["clasificacion"] == "tests"

    salida = capsys.readouterr().out
    assert "EVIDENCIAS ESTRUCTURADAS:" in salida
    assert "RESULTADO DEL TRIAJE:" in salida
    assert "test_media_ponderada" in salida

def test_runner_no_ejecuta_agente_si_falla_recuperacion(monkeypatch):
    """No se debe analizar un run si no se recuperan sus metadatos."""

    def recuperar_simulado(args):
        return {
            "run_id": "123",
            "status": "error",
            "error": "No se pudo consultar GitHub Actions",
        }

    def analizar_simulado(*args, **kwargs):
        raise AssertionError(
            "El agente no debe ejecutarse si falla la recuperación"
        )

    monkeypatch.setattr(
        runner,
        "resultado_tests",
        recuperar_simulado,
    )
    monkeypatch.setattr(
        runner,
        "analizar",
        analizar_simulado,
    )

    import pytest

    with pytest.raises(
        RuntimeError,
        match="No se pudo consultar GitHub Actions",
    ):
        runner.ejecutar("123")

def test_runner_continua_sin_artifact_junit(monkeypatch, capsys):
    """El runner continúa si JUnit no está disponible."""

    evidencia = {
        "run_id": "123",
        "status": "completed",
        "conclusion": "failure",
        "logs": "FAILED tests/test_media.py::test_media",
        "pytest": {
            "disponible": False,
            "motivo": "Artifact no disponible",
        },
    }

    recibido = {}

    monkeypatch.setattr(
        runner,
        "resultado_tests",
        lambda args: evidencia,
    )

    def analizar_simulado(run_id, contexto):
        recibido["contexto"] = contexto
        return {
            "run_id": run_id,
            "clasificacion": "tests",
            "hipotesis": "Fallo detectado en logs",
            "spec_id": None,
            "handoff": None,
        }

    monkeypatch.setattr(runner, "analizar", analizar_simulado)

    resultado = runner.ejecutar("123")

    assert resultado["clasificacion"] == "tests"
    assert recibido["contexto"]["resultado_tests"] == evidencia
    assert evidencia["pytest"]["disponible"] is False

    salida = capsys.readouterr().out
    assert '"pytest_disponible": false' in salida
    assert "Artifact no disponible" in salida
    assert "RESULTADO DEL TRIAJE:" in salida