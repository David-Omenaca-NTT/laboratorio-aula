
"""Valida el despliegue efímero S7 a partir de sus evidencias."""

import argparse
import json
from pathlib import Path


def cargar_json(ruta: Path):
    return json.loads(ruta.read_text(encoding="utf-8"))


def cargar_eventos(ruta: Path):
    eventos = []

    for linea in ruta.read_text(encoding="utf-8").splitlines():
        try:
            dato = json.loads(linea)
        except json.JSONDecodeError:
            continue

        if isinstance(dato, dict) and "event" in dato:
            eventos.append(dato)

    return eventos


def validar(directorio: Path, version: str):
    health = cargar_json(directorio / "health.json")
    matricula = cargar_json(directorio / "matricula.json")
    eventos = cargar_eventos(directorio / "service.log")

    status = (directorio / "http-status.txt").read_text().strip()

    assert health["estado"] == "ok", "Healthcheck incorrecto"
    assert status == "201", "La matrícula no devolvió HTTP 201"

    assert matricula["estado"] == "validada", "Matrícula no validada"
    assert matricula["creditos_admitidos"] > 0, "Sin créditos admitidos"
    assert any(
        linea["codigo_asignatura"] == "MAT101"
        and linea["admitida"] is True
        for linea in matricula["lineas"]
    ), "No se admitió MAT101"

    creadas = [
        e for e in eventos
        if e.get("event") == "matricula.created"
    ]

    accesos = [
        e for e in eventos
        if e.get("event") == "http.access"
        and e.get("method") == "POST"
        and e.get("route") == "/matriculas"
        and e.get("status") == 201
    ]

    salud = [
        e for e in eventos
        if e.get("event") == "http.access"
        and e.get("method") == "GET"
        and e.get("route") == "/salud"
        and e.get("status") == 200
    ]

    assert len(creadas) == 1, "Se esperaba un único evento de matrícula"
    assert len(accesos) == 1, "No hay un único acceso POST 201"
    assert salud, "Falta el acceso HTTP del healthcheck"

    negocio = creadas[0]
    acceso = accesos[0]

    correlation_id = negocio.get("correlation_id")

    assert correlation_id, "Falta correlation ID"
    assert correlation_id == acceso.get("correlation_id"), (
        "Los correlation ID no coinciden"
    )

    assert negocio.get("version") == version, (
        "Versión incorrecta en evento de negocio"
    )
    assert acceso.get("version") == version, (
        "Versión incorrecta en acceso HTTP"
    )

    return {
        "validated": True,
        "healthcheck": "passed",
        "matricula": "passed",
        "observability": "passed",
        "version": version,
        "correlation_id": correlation_id,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()

    resultado_path = args.evidence / "validation.json"

    try:
        resultado = validar(args.evidence, args.version)
    except (AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        resultado = {
            "validated": False,
            "error": str(exc),
        }
        resultado_path.write_text(
            json.dumps(resultado, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"VALIDACIÓN FALLIDA: {exc}")
        raise SystemExit(1)

    resultado_path.write_text(
        json.dumps(resultado, indent=2) + "\n",
        encoding="utf-8",
    )
    print("S7: despliegue validado correctamente")


if __name__ == "__main__":
    main()
