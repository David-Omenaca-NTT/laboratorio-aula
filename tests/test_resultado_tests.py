import json
from types import SimpleNamespace

from agentes.mcp_aula import servidor


def test_resultado_tests_devuelve_error_si_falla_la_descarga_de_logs(monkeypatch):
    respuestas = iter([
        SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"status": "completed", "conclusion": "failure"}),
            stderr="",
        ),
        SimpleNamespace(returncode=1, stdout="", stderr="no se pudo acceder al run"),
    ])
    monkeypatch.setattr(servidor.subprocess, "run", lambda *args, **kwargs: next(respuestas))

    resultado = servidor.resultado_tests({"run_id": "123"})

    assert resultado == {
        "run_id": "123",
        "status": "error",
        "error": "no se pudo acceder al run",
    }


def test_resultado_tests_acepta_logs_vacios_si_gh_termina_correctamente(monkeypatch):
    respuestas = iter([
        SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"status": "completed", "conclusion": "failure"}),
            stderr="",
        ),
        SimpleNamespace(returncode=0, stdout="", stderr=""),
    ])
    monkeypatch.setattr(servidor.subprocess, "run", lambda *args, **kwargs: next(respuestas))

    resultado = servidor.resultado_tests({"run_id": "123"})

    assert resultado["status"] == "completed"
    assert resultado["conclusion"] == "failure"
    assert resultado["logs"] == ""
    assert resultado["evidencia"] == ""
