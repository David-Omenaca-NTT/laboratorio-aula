import json
import subprocess
import sys
from pathlib import Path

from herramientas import orquestar_modernizacion as orquestador


def test_ejecutar_prueba_mapea_resultados_y_ausencia(tmp_path, monkeypatch):
    existente = tmp_path / "tests" / "test_ok.py"
    existente.parent.mkdir()
    existente.write_text("def test_ok(): pass\n", encoding="utf-8")
    resultados = iter([
        subprocess.CompletedProcess([], 0, "1 passed", ""),
        subprocess.CompletedProcess([], 1, "1 failed", "AssertionError"),
    ])
    monkeypatch.setattr(orquestador.subprocess, "run", lambda *args, **kwargs: next(resultados))

    assert orquestador.ejecutar_prueba("tests/test_ok.py", tmp_path)["status"] == "passed"
    assert orquestador.ejecutar_prueba("tests/test_ok.py", tmp_path)["status"] == "failed"
    assert orquestador.ejecutar_prueba("tests/missing.py", tmp_path)["status"] == "unknown"


def test_obtener_pr_requiere_un_head_abierto_unico(monkeypatch):
    sha = "a" * 40
    respuestas = [
        [{"state": "open", "number": 7, "head": {"sha": sha},
          "base": {"ref": "main"}, "title": "Refactor", "html_url": "https://example/pr/7"}],
        [{"state": "open", "number": 7, "head": {"sha": "b" * 40},
          "base": {"ref": "main"}}],
        [
            {"state": "open", "number": 7, "head": {"sha": sha}, "base": {"ref": "main"}},
            {"state": "open", "number": 8, "head": {"sha": sha}, "base": {"ref": "main"}},
        ],
    ]
    monkeypatch.setattr(
        orquestador.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            [], 0, json.dumps(respuestas.pop(0)), ""
        ),
    )

    pr, estado = orquestador.obtener_pr("org/repo", sha)
    assert pr["numero"] == 7
    assert estado == "verified"
    assert orquestador.obtener_pr("org/repo", sha) == (None, "none")
    assert orquestador.obtener_pr("org/repo", sha) == (None, "ambiguous")


def test_lee_bloque_json_de_desviaciones_o_rechaza_formato(tmp_path):
    ruta = tmp_path / "DESVIACIONES.md"
    assert orquestador.leer_desviaciones(ruta) == ([], "absent")
    ruta.write_text(
        '## Desviaciones\n```json\n[{"descripcion":"x","justificacion":"y"}]\n```\n',
        encoding="utf-8",
    )
    assert orquestador.leer_desviaciones(ruta) == (
        [{"descripcion": "x", "justificacion": "y"}],
        "valid",
    )
    ruta.write_text("D-01: algo sin formato estructurado\n", encoding="utf-8")
    assert orquestador.leer_desviaciones(ruta) == (None, "invalid")


def test_orquestar_no_emite_handoff_sin_pr(monkeypatch, tmp_path):
    monkeypatch.setattr(
        orquestador,
        "ejecutar_prueba",
        lambda ruta, raiz: {"status": "passed", "summary": "passed"},
    )
    monkeypatch.setattr(orquestador, "obtener_pr", lambda repo, sha: (None, "none"))
    monkeypatch.setattr(orquestador, "obtener_archivos_modificados", lambda *args: [])
    monkeypatch.setattr(orquestador, "leer_desviaciones", lambda ruta: ([], "absent"))
    monkeypatch.setattr(
        orquestador,
        "_llamar_agente",
        lambda entrada, raiz: {
            "ruta": entrada["ruta"],
            "decision": "aprobable",
            "spec_id": entrada["spec_id"],
            "caracterizacion_verde": True,
            "equivalencia_verde": True,
            "handoff": {"a": "conformidad", "spec_id": entrada["spec_id"]},
        },
    )

    resultado = orquestador.orquestar(
        raiz=tmp_path,
        ruta="src/aula/legado/calc.py",
        bateria="tests/test_caracterizacion_legado.py",
        spec_id="SPEC-002",
        sha="a" * 40,
        repo="org/repo",
        default_branch="main",
    )

    assert resultado["decision"] == "aprobable"
    assert resultado["pr"] is None
    assert resultado["handoff"] is None


def test_orquestar_enriquece_handoff_emitido_por_agente(monkeypatch, tmp_path):
    monkeypatch.setattr(
        orquestador,
        "ejecutar_prueba",
        lambda ruta, raiz: {"status": "passed", "summary": "passed"},
    )
    monkeypatch.setattr(
        orquestador,
        "obtener_pr",
        lambda repo, sha: (
            {"numero": 7, "base_ref": "main", "url": "https://example/pr/7"},
            "verified",
        ),
    )
    monkeypatch.setattr(orquestador, "obtener_archivos_modificados", lambda *args: [])
    monkeypatch.setattr(orquestador, "leer_desviaciones", lambda ruta: ([], "absent"))
    llamadas = []

    def llamar(entrada, raiz):
        llamadas.append(entrada)
        return {
            "decision": "aprobable",
            "spec_id": "SPEC-002",
            "handoff": {"a": "conformidad", "spec_id": "SPEC-002"},
        }

    monkeypatch.setattr(orquestador, "_llamar_agente", llamar)
    resultado = orquestador.orquestar(
        raiz=tmp_path,
        ruta="src/aula/legado/calc.py",
        bateria="tests/test_caracterizacion_legado.py",
        spec_id="SPEC-002",
        sha="a" * 40,
        repo="org/repo",
        default_branch="main",
    )

    assert llamadas[0]["contexto"]["pr"]["numero"] == 7
    assert resultado["handoff"] == {
        "a": "conformidad",
        "pr": 7,
        "spec_id": "SPEC-002",
    }


def test_diff_error_se_propaga(monkeypatch, tmp_path):
    monkeypatch.setattr(
        orquestador.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess([], 128, "", "base missing"),
    )

    try:
        orquestador.obtener_archivos_modificados(tmp_path, "a" * 40, "main")
    except RuntimeError as exc:
        assert "base missing" in str(exc)
    else:
        raise AssertionError("deberia propagar el error del diff")


def test_obtener_archivos_modificados_parsea_rutas_nul(monkeypatch, tmp_path):
    llamada = {}

    def ejecutar(comando, **kwargs):
        llamada["comando"] = comando
        return subprocess.CompletedProcess(
            comando, 0, "src/aula/legado/calc.py\0tests/test_caracterizacion_legado.py\0", ""
        )

    monkeypatch.setattr(orquestador.subprocess, "run", ejecutar)

    archivos = orquestador.obtener_archivos_modificados(
        tmp_path, "a" * 40, "feature/refactor"
    )

    assert archivos == [
        "src/aula/legado/calc.py",
        "tests/test_caracterizacion_legado.py",
    ]
    assert llamada["comando"][-1] == f"origin/feature/refactor...{'a' * 40}"


def test_equivalencia_ausente_se_mantiene_unknown_en_contexto(
    monkeypatch, tmp_path,
):
    resultados = []

    def ejecutar(ruta, raiz):
        resultado = (
            {"status": "unknown", "summary": f"No existe {ruta}."}
            if ruta == "tests/test_equivalencia_legado.py"
            else {"status": "passed", "summary": "9 passed"}
        )
        resultados.append((ruta, resultado))
        return resultado

    monkeypatch.setattr(orquestador, "ejecutar_prueba", ejecutar)
    monkeypatch.setattr(orquestador, "obtener_pr", lambda repo, sha: (None, "none"))
    monkeypatch.setattr(orquestador, "obtener_archivos_modificados", lambda *args: [])
    monkeypatch.setattr(orquestador, "leer_desviaciones", lambda ruta: ([], "absent"))
    llamada = {}

    def llamar(entrada, raiz):
        llamada["entrada"] = entrada
        return {
            "decision": "evidencia_insuficiente",
            "caracterizacion_verde": True,
            "equivalencia_verde": None,
            "handoff": None,
        }

    monkeypatch.setattr(orquestador, "_llamar_agente", llamar)
    resultado = orquestador.orquestar(
        raiz=tmp_path,
        ruta="src/aula/legado/calc.py",
        bateria="tests/test_caracterizacion_legado.py",
        spec_id="SPEC-002",
        sha="a" * 40,
        repo="org/repo",
        default_branch="main",
    )

    assert llamada["entrada"]["contexto"]["resultado_equivalencia"]["status"] == "unknown"
    assert resultado["equivalencia_verde"] is None
    assert resultado["handoff"] is None


def test_llamar_agente_usa_su_cli_real_y_contrato_status(tmp_path):
    raiz = Path(__file__).resolve().parents[1]
    entrada = {
        "ruta": "src/aula/legado/calculadora_expediente_v1.py",
        "bateria": "tests/test_caracterizacion_legado.py",
        "spec_id": "SPEC-002",
        "contexto": {
            "resultado_caracterizacion": {"status": "passed"},
            "resultado_equivalencia": {"status": "unknown"},
            "archivos_modificados": [],
            "desviaciones": [],
            "pr": None,
        },
    }

    resultado = orquestador._llamar_agente(entrada, raiz)

    assert resultado["decision"] == "evidencia_insuficiente"
    assert resultado["caracterizacion_verde"] is True
    assert resultado["equivalencia_verde"] is None
