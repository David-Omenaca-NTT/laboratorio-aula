import subprocess

from aula_cli import verificacion


def test_s5_02_ignora_refactor_anterior_de_otro_modulo(monkeypatch):
    historial = "\n".join(
        [
            "a" * 40 + "|refactor: cambio antiguo de S1",
            "M\tsrc/aula/api/main.py",
            "b" * 40 + "|test: añadir caracterizacion del modulo legado",
            "A\ttests/test_caracterizacion_legado.py",
            "c" * 40 + "|feat: modificar calculadora legado",
            "M\tsrc/aula/legado/calculadora_expediente_v1.py",
        ]
    )
    monkeypatch.setattr(
        verificacion,
        "ejecutar",
        lambda comando: subprocess.CompletedProcess(comando, 0, historial, ""),
    )

    ok, detalle = verificacion.orden_refactor_legado_en_historial(
        "tests/test_caracterizacion_legado.py",
        "src/aula/legado/calculadora_expediente_v1.py",
    )

    assert ok is True, detalle


def _historial_s5(monkeypatch, *commits):
    lineas = []
    for numero, asunto, cambios in commits:
        lineas.append(f"{numero:040d}|{asunto}")
        lineas.extend(f"{estado}\t{ruta}" for estado, ruta in cambios)
    historial = "\n".join(lineas)
    monkeypatch.setattr(
        verificacion,
        "ejecutar",
        lambda comando: subprocess.CompletedProcess(comando, 0, historial, ""),
    )


def test_s5_02_falla_si_el_legado_se_modifica_antes_de_caracterizarlo(monkeypatch):
    _historial_s5(
        monkeypatch,
        (1, "baseline legado", [("A", "src/aula/legado/calculadora_expediente_v1.py")]),
        (2, "refactor temprano", [("M", "src/aula/legado/calculadora_expediente_v1.py")]),
        (3, "test: caracterizacion", [("A", "tests/test_caracterizacion_legado.py")]),
    )

    ok, detalle = verificacion.orden_refactor_legado_en_historial(
        "tests/test_caracterizacion_legado.py",
        "src/aula/legado/calculadora_expediente_v1.py",
    )

    assert ok is False
    assert "antes de la caracterizacion" in detalle


def test_s5_02_sin_refactor_del_legado_devuelve_estado_explicito(monkeypatch):
    _historial_s5(
        monkeypatch,
        (1, "baseline legado", [("A", "src/aula/legado/calculadora_expediente_v1.py")]),
        (2, "test: caracterizacion", [("A", "tests/test_caracterizacion_legado.py")]),
    )

    ok, detalle = verificacion.orden_refactor_legado_en_historial(
        "tests/test_caracterizacion_legado.py",
        "src/aula/legado/calculadora_expediente_v1.py",
    )

    assert ok is True
    assert detalle == "todavia no hay commits de refactor del legado"


def test_s5_02_ignora_refactors_de_otros_modulos(monkeypatch):
    _historial_s5(
        monkeypatch,
        (1, "test: caracterizacion", [("A", "tests/test_caracterizacion_legado.py")]),
        (2, "refactor: otro modulo", [("M", "src/aula/reglas/motor.py")]),
        (3, "feat: refactor legado", [("M", "src/aula/legado/calculadora_expediente_v1.py")]),
    )

    ok, detalle = verificacion.orden_refactor_legado_en_historial(
        "tests/test_caracterizacion_legado.py",
        "src/aula/legado/calculadora_expediente_v1.py",
    )

    assert ok is True, detalle
