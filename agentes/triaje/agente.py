# PRUEBA TEMPORAL S6: caso negativo SHA incorrecto.
"""Agente de triaje para clasificar fallos de pipeline.

Entrada esperada:
    {"run_id": "12345"}

Salida:
    {
      "run_id": "12345",
      "clasificacion": "cobertura_spec",
      "hipotesis": "...",
      "spec_id": "SPEC-003",
      "handoff": {"destino": "conformidad", "datos": ["SPEC-003"]}
    }
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CATEGORIAS = {
    "cobertura_spec",
    "tests",
    "build",
    "infraestructura",
    "desconocido",
}


@dataclass
class Handoff:
    destino: str
    datos: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"destino": self.destino, "datos": self.datos}


@dataclass
class ResultadoTriaje:
    run_id: str
    clasificacion: str
    hipotesis: str
    spec_id: str | None = None
    handoff: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "clasificacion": self.clasificacion,
            "hipotesis": self.hipotesis,
            "spec_id": self.spec_id,
            "handoff": self.handoff,
        }


def _coerce_text(valor: Any) -> str:
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, (dict, list, tuple)):
        return json.dumps(valor, ensure_ascii=False, sort_keys=True)
    return str(valor)


def _normalizar_contexto(contexto: Any) -> dict[str, Any]:
    if contexto is None:
        return {}
    if isinstance(contexto, dict):
        return contexto
    if isinstance(contexto, str):
        texto = contexto.strip()
        if not texto:
            return {}
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            return {"run_id": texto}
    return {"run_id": str(contexto)}


def _spec_candidates(texto: str) -> list[str]:
    return sorted(set(re.findall(r"SPEC-\d+", texto, flags=re.IGNORECASE)))


def _detectar_spec_id(contexto: dict[str, Any]) -> str | None:
    spec_id = contexto.get("spec_id") or contexto.get("spec")
    if isinstance(spec_id, str) and re.fullmatch(r"SPEC-\d+", spec_id.strip(), flags=re.IGNORECASE):
        return spec_id.upper()
    texto = "\n".join(
        _coerce_text(v)
        for v in [
            contexto.get("resultado_tests"),
            contexto.get("trazabilidad"),
            contexto.get("hipotesis"),
            contexto.get("error"),
            contexto.get("summary"),
            contexto.get("logs"),
            contexto.get("tests"),
        ]
        if v is not None
    )
    candidatos = _spec_candidates(texto)
    if len(candidatos) == 1:
        return candidatos[0].upper()
    return None


def _trazabilidad_ha_cobertura_truncada(contexto: dict[str, Any], spec_id: str | None = None) -> bool:
    trazabilidad = contexto.get("trazabilidad")
    if not isinstance(trazabilidad, dict):
        return False
    if spec_id and trazabilidad.get("spec") == spec_id:
        return bool(trazabilidad.get("sin_cubrir")) or (trazabilidad.get("cobertura_pct", 100) < 100)
    if "sin_cubrir" in trazabilidad and trazabilidad["sin_cubrir"]:
        return True
    if "cobertura_pct" in trazabilidad and float(trazabilidad["cobertura_pct"]) < 100:
        return True
    return False


def _resumen_contexto(contexto: dict[str, Any]) -> str:
    piezas: list[str] = []
    for clave in ("error", "summary", "logs", "mensaje", "resultado_tests", "trazabilidad", "tests"):
        valor = contexto.get(clave)
        if valor is not None:
            piezas.append(_coerce_text(valor))
    return "\n".join(piezas).lower()


def _clasificacion_por_evidencia(texto: str, spec_id: str | None) -> tuple[str, str | None]:
    texto_normal = texto.lower()
    cobertura = (
        "cobertura" in texto_normal
        or "sin_cubrir" in texto_normal
        or "cubre:" in texto_normal
        or "spec-" in texto_normal
    )
    if cobertura and spec_id:
        return "cobertura_spec", spec_id

    if cobertura and not spec_id:
        return "cobertura_spec", None

    if any(token in texto_normal for token in [
        "build failed",
        "failed to build",
        "error while building",
        "compilation failed",
        "compilation error",
        "failed during compilation",
        "failed during build",
    ]):
        return "build", spec_id

    if any(token in texto_normal for token in [
        "assertionerror",
        "test failed",
        "tests failed",
        "failed test",
        "failed: test_",
        "error in test",
        "failed assertions",
    ]):
        return "tests", spec_id

    if any(token in texto_normal for token in [
        "docker",
        "network",
        "timeout",
        "runner",
        "permission denied",
        "no space left",
        "unavailable",
        "infraestructura",
        "service unavailable",
        "connection reset",
    ]):
        return "infraestructura", spec_id

    return "desconocido", spec_id

def _determinar_spec_id(contexto: dict[str, Any], texto: str) -> str | None:
    spec_id = _detectar_spec_id(contexto)
    if spec_id is not None:
        return spec_id
    candidatos = _spec_candidates(texto)
    if len(candidatos) == 1:
        return candidatos[0].upper()
    return None


def _hipotesis_por_categoria(categoria: str, spec_id: str | None, texto: str) -> str:
    if categoria == "cobertura_spec":
        if spec_id:
            return f"El fallo apunta a una brecha de cobertura en {spec_id}; la evidencia disponible sugiere que un criterio de la especificación no tiene prueba asociada."
        return "El fallo parece estar relacionado con cobertura de especificación, pero la evidencia no permite identificar un spec_id fiable."
    if categoria == "tests":
        return "La causa más probable es un fallo de pruebas: las aserciones o los casos ejecutados no están satisfaciendo la expectativa del pipeline."
    if categoria == "build":
        return "El fallo procede del proceso de construcción o compilación del proyecto antes de que las pruebas puedan validar el cambio."
    if categoria == "infraestructura":
        return "El fallo parece ser infraestructural: la ejecución del pipeline queda bloqueada por el entorno, la imagen o el runner, no por la lógica del cambio."
    return "La evidencia del fallo es insuficiente para atribuirlo a una causa determinista entre cobertura, pruebas, build o infraestructura."


def clasificar_fallo(run_id: str | dict | None, contexto: Any = None, **kwargs: Any) -> ResultadoTriaje:
    """Clasifica un fallo de pipeline y decide si procede handoff a Conformidad."""
    if isinstance(run_id, dict):
        payload = run_id
        run_id = payload.get("run_id") or payload.get("id") or "sin-run-id"
        contexto = payload if contexto is None else {**payload, **_normalizar_contexto(contexto)}
    elif contexto is not None:
        contexto = _normalizar_contexto(contexto)
    else:
        contexto = {}

    entrada = _normalizar_contexto(kwargs)
    contexto = {**contexto, **entrada}
    if isinstance(run_id, dict):
        raise TypeError("`run_id` no puede ser un diccionario anidado; usa `contexto` o un payload con `run_id`.")

    run_id = str(run_id or contexto.get("run_id") or "sin-run-id")
    texto = _resumen_contexto(contexto)
    if not texto and isinstance(contexto.get("resultado_tests"), dict):
        texto = _coerce_text(contexto["resultado_tests"])

    spec_id = _determinar_spec_id(contexto, texto)
    if spec_id is None and isinstance(contexto.get("trazabilidad"), dict):
        spec = contexto["trazabilidad"].get("spec")
        if isinstance(spec, str) and re.fullmatch(r"SPEC-\d+", spec.strip(), flags=re.IGNORECASE):
            spec_id = spec.upper()

    categoria, spec_id_confirmada = _clasificacion_por_evidencia(texto, spec_id)
    if spec_id_confirmada is not None:
        spec_id = spec_id_confirmada

    if categoria == "cobertura_spec" and spec_id is None:
        categoria = "desconocido"

    if categoria == "cobertura_spec" and spec_id is not None and _trazabilidad_ha_cobertura_truncada(contexto, spec_id):
        categoria = "cobertura_spec"
    elif categoria == "cobertura_spec" and spec_id is None:
        categoria = "desconocido"

    if categoria not in CATEGORIAS:
        categoria = "desconocido"

    hipotesis = _hipotesis_por_categoria(categoria, spec_id, texto)
    handoff = None
    if categoria == "cobertura_spec" and spec_id is not None:
        handoff = Handoff(destino="conformidad", datos=[spec_id]).to_dict()

    return ResultadoTriaje(
        run_id=run_id,
        clasificacion=categoria,
        hipotesis=hipotesis,
        spec_id=spec_id if categoria == "cobertura_spec" else None,
        handoff=handoff,
    )


def analizar(run_id: str | dict | None, contexto: Any = None, **kwargs: Any) -> dict[str, Any]:
    return clasificar_fallo(run_id, contexto=contexto, **kwargs).to_dict()


def principal(argv=None):
    parser = argparse.ArgumentParser(description="Agente de triaje para fallos del pipeline")
    parser.add_argument("--run-id", dest="run_id")
    parser.add_argument("--entrada", help="Ruta a un JSON con la entrada del agente")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    entrada = {}
    if args.entrada:
        entrada = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    if args.run_id:
        entrada = {**entrada, "run_id": args.run_id}
    if not entrada and not args.run_id:
        parser.error("Hace falta --run-id o --entrada.")

    resultado = clasificar_fallo(entrada.get("run_id") if isinstance(entrada, dict) else args.run_id, contexto=entrada)
    salida = resultado.to_dict()
    if args.json:
        print(json.dumps(salida, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(salida, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
