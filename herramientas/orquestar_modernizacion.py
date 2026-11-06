"""Recopila evidencias y adapta la salida del agente para F3."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _resumen(proceso: subprocess.CompletedProcess[str]) -> str:
    salida = "\n".join(parte for parte in (proceso.stdout, proceso.stderr) if parte)
    return salida.strip()[-4000:]


def ejecutar_prueba(ruta: str, raiz: Path) -> dict[str, str]:
    """Ejecuta una bateria existente; la ausencia o error de arranque es unknown."""
    ruta_resuelta = (raiz / ruta).resolve()
    try:
        ruta_resuelta.relative_to(raiz.resolve())
    except ValueError:
        return {"status": "unknown", "summary": "La ruta de pruebas sale del repositorio."}
    if not ruta_resuelta.is_file():
        return {"status": "unknown", "summary": f"No existe {ruta}."}

    try:
        proceso = subprocess.run(
            [sys.executable, "-m", "pytest", ruta, "-q"],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return {"status": "unknown", "summary": f"No se pudo iniciar pytest: {exc}"}
    return {
        "status": "passed" if proceso.returncode == 0 else "failed",
        "summary": _resumen(proceso),
    }


def obtener_archivos_modificados(
    raiz: Path, sha: str, base_ref: str,
) -> list[str]:
    """Devuelve rutas del diff entre la base y el commit evaluado."""
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", base_ref) or base_ref.startswith("-"):
        raise ValueError("La referencia base de Git no tiene un formato permitido.")
    proceso = subprocess.run(
        [
            "git", "diff", "--name-only", "-z",
            f"origin/{base_ref}...{sha}",
        ],
        cwd=raiz,
        capture_output=True,
        text=True,
        check=False,
    )
    if proceso.returncode != 0:
        raise RuntimeError(proceso.stderr.strip() or "No se pudo calcular el diff de Git.")
    return sorted(set(proceso.stdout.split("\0")[:-1]))


def obtener_pr(repo: str, sha: str) -> tuple[dict[str, Any] | None, str]:
    """Encuentra una unica PR abierta cuyo head coincida exactamente con sha."""
    try:
        proceso = subprocess.run(
            [
                "gh", "api",
                f"repos/{repo}/commits/{sha}/pulls",
                "-f", "per_page=100",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return None, f"unknown: no se pudo iniciar gh: {exc}"
    if proceso.returncode != 0:
        return None, f"unknown: {proceso.stderr.strip() or 'fallo en la API de GitHub'}"
    try:
        pull_requests = json.loads(proceso.stdout)
    except json.JSONDecodeError:
        return None, "unknown: la API devolvio una respuesta no JSON"
    if not isinstance(pull_requests, list):
        return None, "unknown: respuesta de PRs con formato inesperado"

    coincidencias = [
        pr for pr in pull_requests
        if isinstance(pr, dict)
        and pr.get("state") == "open"
        and isinstance(pr.get("head"), dict)
        and pr["head"].get("sha") == sha
        and isinstance(pr.get("number"), int)
        and isinstance(pr.get("base"), dict)
        and isinstance(pr["base"].get("ref"), str)
    ]
    if len(coincidencias) != 1:
        return None, "none" if not coincidencias else "ambiguous"
    pr = coincidencias[0]
    return {
        "numero": pr["number"],
        "titulo": pr.get("title"),
        "url": pr.get("html_url"),
        "base_ref": pr["base"]["ref"],
    }, "verified"


def leer_desviaciones(ruta: Path) -> tuple[list[dict[str, str]] | None, str]:
    """Lee la lista JSON declarada en un bloque ```json de DESVIACIONES.md."""
    if not ruta.exists():
        return [], "absent"
    texto = ruta.read_text(encoding="utf-8")
    bloque = re.search(r"```json\s*(.*?)```", texto, flags=re.IGNORECASE | re.DOTALL)
    if bloque is None:
        return None, "invalid"
    try:
        valor = json.loads(bloque.group(1))
    except json.JSONDecodeError:
        return None, "invalid"
    if not isinstance(valor, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("descripcion"), str)
        or not isinstance(item.get("justificacion"), str)
        for item in valor
    ):
        return None, "invalid"
    return valor, "valid"


def _llamar_agente(entrada: dict[str, Any], raiz: Path) -> dict[str, Any]:
    """Invoca el CLI publico del agente usando su contrato --entrada."""
    with tempfile.TemporaryDirectory() as temporal:
        ruta_entrada = Path(temporal) / "entrada-modernizacion.json"
        ruta_entrada.write_text(
            json.dumps(entrada, ensure_ascii=False),
            encoding="utf-8",
        )
        proceso = subprocess.run(
            [
                sys.executable, "-m", "agentes.modernizacion.agente",
                "--entrada", str(ruta_entrada),
            ],
            cwd=raiz,
            capture_output=True,
            text=True,
            check=False,
        )
    if proceso.returncode != 0:
        raise RuntimeError(_resumen(proceso) or "El CLI del agente fallo.")
    try:
        resultado = json.loads(proceso.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("El CLI del agente no devolvio JSON valido.") from exc
    if not isinstance(resultado, dict):
        raise RuntimeError("El CLI del agente no devolvio un objeto JSON.")
    return resultado


def orquestar(
    *,
    raiz: Path,
    ruta: str,
    bateria: str,
    spec_id: str,
    sha: str,
    repo: str,
    default_branch: str,
) -> dict[str, Any]:
    caracterizacion = ejecutar_prueba(bateria, raiz)
    ruta_equivalencia = "tests/test_equivalencia_legado.py"
    equivalencia = ejecutar_prueba(ruta_equivalencia, raiz)
    pr, estado_pr = obtener_pr(repo, sha)
    base_ref = pr["base_ref"] if pr else default_branch
    archivos = obtener_archivos_modificados(raiz, sha, base_ref)
    desviaciones, estado_desviaciones = leer_desviaciones(
        raiz / "src" / "aula" / "legado" / "DESVIACIONES.md"
    )

    entrada = {
        "ruta": ruta,
        "bateria": bateria,
        "spec_id": spec_id,
        "contexto": {
            "resultado_caracterizacion": caracterizacion,
            "resultado_equivalencia": equivalencia,
            "archivos_modificados": archivos,
            "desviaciones": desviaciones,
            "pr": pr,
        },
    }
    resultado = _llamar_agente(entrada, raiz)
    resultado["pr"] = pr["numero"] if pr else None
    resultado["pr_titulo"] = pr.get("titulo") if pr else None
    resultado["pr_url"] = pr.get("url") if pr else None
    resultado["pr_estado"] = estado_pr
    resultado["equivalencia_resumen"] = equivalencia.get("summary", "")
    resultado["desviaciones_estado"] = estado_desviaciones

    handoff = resultado.get("handoff")
    if handoff:
        resultado["handoff"] = (
            {
                "a": handoff.get("a", "conformidad"),
                "pr": pr["numero"],
                "spec_id": handoff.get("spec_id"),
            }
            if pr else None
        )
    return resultado


def escribir_summary(resultado: dict[str, Any], destino: Path) -> None:
    handoff = resultado.get("handoff")
    texto = "\n".join([
        "# Resultado de Modernización",
        "",
        f"- **Ruta:** `{resultado.get('ruta')}`",
        f"- **Spec:** `{resultado.get('spec_id')}`",
        f"- **Caracterización verde:** `{resultado.get('caracterizacion_verde')}`",
        f"- **Equivalencia verde:** `{resultado.get('equivalencia_verde')}`",
        f"- **Decisión:** `{resultado.get('decision')}`",
        f"- **PR:** `{resultado.get('pr')}` ({resultado.get('pr_estado')})",
        f"- **URL de PR:** {resultado.get('pr_url') or 'no disponible'}",
        f"- **Handoff:** `{json.dumps(handoff, ensure_ascii=False) if handoff else 'no'}`",
        "",
        "```json",
        json.dumps(resultado, ensure_ascii=False, indent=2),
        "```",
        "",
    ])
    with destino.open("a", encoding="utf-8") as archivo:
        archivo.write(texto)


def principal() -> int:
    raiz = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd())).resolve()
    resultado = orquestar(
        raiz=raiz,
        ruta=os.environ["MODERNIZACION_RUTA"],
        bateria=os.environ["MODERNIZACION_BATERIA"],
        spec_id=os.environ["MODERNIZACION_SPEC_ID"],
        sha=os.environ["GITHUB_SHA"],
        repo=os.environ["GITHUB_REPOSITORY"],
        default_branch=os.environ["DEFAULT_BRANCH"],
    )
    salida = json.dumps(resultado, ensure_ascii=False, indent=2)
    print(salida)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        escribir_summary(resultado, Path(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(principal())
