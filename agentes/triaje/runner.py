
"""Punto de entrada del Triaje v2 desde GitHub Actions."""

import json
import os
import sys

from agentes.mcp_aula.servidor import resultado_tests
from agentes.triaje.agente import analizar


def ejecutar(run_id: str) -> dict:
    """Recupera evidencias y ejecuta el agente de triaje."""

    # 1. Invocar resultado_tests() para recuperar las evidencias.
    evidencia = resultado_tests({"run_id": run_id})

    if evidencia.get("status") == "error":
        raise RuntimeError(
            evidencia.get("error") or "Error recuperando evidencias"
        )

    # 2. Comprobar si existe JUnit y registrar un resumen estructurado.
    pytest = evidencia.get("pytest", {})
    disponible = pytest.get("disponible", False)

    resumen = {
        "run_id": run_id,
        "conclusion": evidencia.get("conclusion"),
        "pytest_disponible": disponible,
        "total": pytest.get("total") if disponible else None,
        "passed": pytest.get("passed") if disponible else None,
        "failed": pytest.get("failed") if disponible else None,
        "errors": pytest.get("errors") if disponible else None,
        "skipped": pytest.get("skipped") if disponible else None,
        "fallos": pytest.get("fallos", []) if disponible else [],
    }

    if not disponible:
        resumen["motivo"] = pytest.get(
            "motivo", "Evidencia JUnit no disponible"
        )

    print("EVIDENCIAS ESTRUCTURADAS:")
    print(json.dumps(resumen, ensure_ascii=False, indent=2))

    # 3. Invocar analizar() pasando todas las evidencias.
    resultado = analizar(
        run_id,
        contexto={"resultado_tests": evidencia},
    )

    print("RESULTADO DEL TRIAJE:")
    print(json.dumps(resultado, ensure_ascii=False, indent=2))

    return resultado


def main() -> int:
    """Punto de entrada para GitHub Actions."""
    run_id = os.environ.get("TRIAJE_RUN_ID", "").strip()

    if not run_id:
        print("ERROR: falta TRIAJE_RUN_ID", file=sys.stderr)
        return 1

    try:
        ejecutar(run_id)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
