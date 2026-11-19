from agentes.triaje.agente import analizar


def test_junit_prioriza_tests_sobre_cobertura_spec():
    evidencia = {
        "run_id": "123",
        "status": "completed",
        "conclusion": "failure",
        "logs": (
            "FAILED tests/test_media_expediente.py::test_media_ponderada\n"
            "AssertionError: resultado incorrecto\n"
            "SPEC-002\n"
            "cubre: SPEC-002"
        ),
        "pytest": {
            "disponible": True,
            "total": 102,
            "passed": 96,
            "failed": 6,
            "errors": 0,
            "skipped": 0,
            "fallos": [
                {
                    "test": "test_media_ponderada",
                    "tipo": "AssertionError",
                    "mensaje": "Media ponderada incorrecta",
                    "categoria": "failure",
                }
            ],
        },
    }

    resultado = analizar(
        "123",
        contexto={"resultado_tests": evidencia},
    )

    assert resultado["clasificacion"] == "tests"
    assert resultado["spec_id"] is None
    assert resultado["handoff"] is None

def test_sin_junit_utiliza_clasificacion_por_logs():
    """Sin JUnit, el agente conserva la clasificación por logs."""

    evidencia = {
        "run_id": "456",
        "status": "completed",
        "conclusion": "failure",
        "logs": (
            "FAILED tests/test_media_expediente.py::test_media_ponderada\n"
            "AssertionError: resultado incorrecto"
        ),
        "pytest": {
            "disponible": False,
            "motivo": "Artifact no disponible",
        },
    }

    resultado = analizar(
        "456",
        contexto={"resultado_tests": evidencia},
    )

    assert resultado["clasificacion"] == "tests"
    assert resultado["spec_id"] is None
    assert resultado["handoff"] is None

def test_cobertura_real_conserva_handoff_conformidad():
    """Una brecha real de cobertura mantiene el handoff."""

    evidencia = {
        "run_id": "789",
        "status": "completed",
        "conclusion": "failure",
        "logs": "SPEC-003: criterio sin prueba asociada",
        "pytest": {
            "disponible": False,
            "motivo": "Artifact no disponible",
        },
    }

    resultado = analizar(
        "789",
        contexto={
            "resultado_tests": evidencia,
            "trazabilidad": {
                "spec": "SPEC-003",
                "sin_cubrir": ["criterio-2"],
                "cobertura_pct": 75,
            },
        },
    )

    assert resultado["clasificacion"] == "cobertura_spec"
    assert resultado["spec_id"] == "SPEC-003"
    assert resultado["handoff"] == {
        "destino": "conformidad",
        "datos": ["SPEC-003"],
    }