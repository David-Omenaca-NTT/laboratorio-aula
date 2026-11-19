"""Servidor MCP del proyecto Aula.

Expone el contexto del repositorio como herramientas consultables por cualquier
agente. Implementa el transporte stdio de MCP con JSON-RPC 2.0 en biblioteca
estandar: sin SDK, para que el student vea el protocolo por dentro antes de
usar una abstraccion que se lo oculte.

Arranque:
    python3 -m agentes.mcp_aula.servidor

Registro en Claude Code (.mcp.json):
    {"mcpServers": {"aula-contexto": {"command": "python3",
     "args": ["-m", "agentes.mcp_aula.servidor"]}}}
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PROTOCOLO = "2024-11-05"

HERRAMIENTAS = [
    {
        "name": "listar_specs",
        "description": "Devuelve el catalogo de especificaciones del proyecto con su estado y version.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "obtener_spec",
        "description": "Devuelve una spec completa con sus criterios de aceptacion, invariantes y alcance.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "Identificador, por ejemplo SPEC-002"}},
            "required": ["id"],
        },
    },
    {
        "name": "trazabilidad",
        "description": "Para una spec, devuelve que criterios estan cubiertos por test y cuales no.",
        "inputSchema": {
            "type": "object",
            "properties": {"spec_id": {"type": "string"}},
            "required": ["spec_id"],
        },
    },
    {
        "name": "resultado_tests",
        "description": "Ejecuta la suite o consulta un run_id de GitHub Actions y devuelve el resultado agregado y los tests fallidos.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string", "description": "Identificador del run de GitHub Actions"},
                "ruta": {"type": "string", "description": "Subconjunto opcional de tests"},
            },
            "required": [],
        },
    },
    {
        "name": "version_plan",
        "description": "Devuelve la version vigente de un plan de estudios y sus parametros normativos.",
        "inputSchema": {
            "type": "object",
            "properties": {"codigo": {"type": "string"}},
            "required": ["codigo"],
        },
    },
]


# --- logica de las herramientas ----------------------------------------------

def _specs():
    return sorted((RAIZ / "specs").glob("SPEC-*.md"))


def _id_de(ruta: Path) -> str:
    return ruta.name.split("-")[0] + "-" + ruta.name.split("-")[1]


def _campo(texto: str, patron: str, defecto="desconocido") -> str:
    m = re.search(patron, texto, re.M)
    return m.group(1).strip() if m else defecto


def criterios_de(texto: str) -> list:
    """Extrae los identificadores CA-nn e INV-nn declarados en la spec."""
    return sorted(set(re.findall(r"\b(?:CA|INV)-\d{2}\b", texto)))


def listar_specs(_=None) -> dict:
    salida = []
    for ruta in _specs():
        texto = ruta.read_text(encoding="utf-8")
        salida.append({
            "id": _id_de(ruta),
            "titulo": _campo(texto, r"^#\s+SPEC-\d+:\s*(.+)$"),
            "version": _campo(texto, r"Versi[oó]n:\s*(v[\d.]+)"),
            "estado": _campo(texto, r"Estado:\s*(\w+)"),
            "criterios": len(criterios_de(texto)),
            "ruta": str(ruta.relative_to(RAIZ)),
        })
    return {"specs": salida}


def obtener_spec(args: dict) -> dict:
    ident = args["id"].upper()
    for ruta in _specs():
        if _id_de(ruta) == ident:
            texto = ruta.read_text(encoding="utf-8")
            return {"id": ident, "criterios": criterios_de(texto), "contenido": texto}
    return {"error": "spec %s no encontrada" % ident}


def _cubiertos() -> dict:
    """Mapea criterio -> lista de tests que lo declaran mediante `cubre:`."""
    mapa = {}
    for ruta in (RAIZ / "tests").rglob("test_*.py"):
        texto = ruta.read_text(encoding="utf-8")
        for bloque in re.finditer(r"def (test_\w+)\(.*?\):\s*(?:\"\"\"(.*?)\"\"\")?",
                                  texto, re.S):
            nombre, doc = bloque.group(1), bloque.group(2) or ""
            for etiqueta in re.findall(r"cubre:\s*([^\n\"]+)", doc):
                for ref in re.findall(r"(SPEC-\d+|LEG)[/-]((?:CA|INV|CAR|EQU)[-\w]*)", etiqueta):
                    clave = "%s/%s" % (ref[0], ref[1])
                    mapa.setdefault(clave, []).append("%s::%s" % (ruta.name, nombre))
    return mapa


def trazabilidad(args: dict) -> dict:
    ident = args["spec_id"].upper()
    spec = obtener_spec({"id": ident})
    if "error" in spec:
        return spec
    mapa = _cubiertos()
    cubiertos, huerfanos = {}, []
    for criterio in spec["criterios"]:
        clave = "%s/%s" % (ident, criterio)
        if clave in mapa:
            cubiertos[criterio] = mapa[clave]
        else:
            huerfanos.append(criterio)
    total = len(spec["criterios"])
    return {
        "spec": ident,
        "criterios_totales": total,
        "cubiertos": cubiertos,
        "sin_cubrir": huerfanos,
        "cobertura_pct": round(100.0 * (total - len(huerfanos)) / total, 1) if total else 0.0,
    }

def _descargar_junit(run_id: str) -> dict:
    """Recupera el XML de pytest publicado en un run de GitHub Actions."""
    identificador = str(run_id)

    if not identificador.isdecimal() or int(identificador) <= 0:
        return {
            "disponible": False,
            "motivo": "run_id no valido",
        }

    try:
        with tempfile.TemporaryDirectory() as directorio:
            comando = [
                "gh", "run", "download", identificador,
                "--repo", "David-Omenaca-NTT/laboratorio-aula",
                "--name", "pytest-results",
                "--dir", directorio,
            ]

            proceso = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if proceso.returncode != 0:
                return {
                    "disponible": False,
                    "motivo": "No se pudo recuperar el artifact pytest-results",
                    "codigo_salida": proceso.returncode,
                    "tipo_error": (
                        "autenticacion"
                        if proceso.returncode in (4, 77)
                        else "descarga_fallida"
                    ),
                }
            ruta_xml = Path(directorio) / "pytest-results.xml"

            if not ruta_xml.is_file():
                return {
                    "disponible": False,
                    "motivo": "El artifact no contiene pytest-results.xml",
                }

            if ruta_xml.stat().st_size > 5_000_000:
                return {
                    "disponible": False,
                    "motivo": "El XML supera el limite de 5 MB",
                }

            return {
                "disponible": True,
                "xml": ruta_xml.read_text(encoding="utf-8"),
            }

    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        return {
            "disponible": False,
            "motivo": "Error al recuperar o leer las evidencias",
        }

def _interpretar_junit(xml: str) -> dict:
    """Convierte un informe JUnit XML en evidencias estructuradas."""

    raiz = ET.fromstring(xml)

    suites = (
        [raiz] if raiz.tag == "testsuite"
        else raiz.findall(".//testsuite")
    )

    if not suites:
        raise ValueError("El XML no contiene suites de pytest")

    casos = []
    fallos = []

    for suite in suites:
        for caso in suite.findall("testcase"):
            nombre = caso.get("name", "")
            clase = caso.get("classname", "")
            archivo = caso.get("file", "")

            casos.append(caso)

            for etiqueta in ("failure", "error"):
                for fallo in caso.findall(etiqueta):
                    fallos.append({
                        "test": nombre,
                        "clase": clase,
                        "archivo": archivo,
                        "tipo": fallo.get("type", ""),
                        "mensaje": fallo.get("message", ""),
                        "detalle": (fallo.text or "").strip()[:4000],
                        "categoria": etiqueta,
                    })

    total = len(casos)
    failed = sum(
        1 for caso in casos
        if caso.find("failure") is not None
    )
    errors = sum(
        1 for caso in casos
        if caso.find("error") is not None
    )
    skipped = sum(
        1 for caso in casos
        if caso.find("skipped") is not None
    )

    return {
        "disponible": True,
        "total": total,
        "passed": total - failed - errors - skipped,
        "failed": failed,
        "errors": errors,
        "skipped": skipped,
        "fallos": fallos,
    }

def resultado_tests(args: dict) -> dict:
    run_id = args.get("run_id")
    ruta = args.get("ruta")

    if run_id:
        try:
            resumen = subprocess.run(
                ["gh", "run", "view", str(run_id), "--json", "name,conclusion,status,displayTitle,url,workflowName,headBranch,headSha"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if resumen.returncode != 0:
                return {
                    "run_id": str(run_id),
                    "status": "error",
                    "error": resumen.stderr.strip() or "gh no disponible",
                }
            payload = json.loads(resumen.stdout or "{}")
            logs = subprocess.run(
                ["gh", "run", "view", str(run_id), "--log-failed"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if logs.returncode != 0:
                payload["logs_error"] = (
                    logs.stderr.strip()
                    or "No se pudieron recuperar los logs del run"
                )
                payload["logs"] = ""
            else:
                payload["logs"] = logs.stdout.strip() if logs.stdout else ""

            payload["run_id"] = str(run_id)
            payload["evidencia"] = payload.get("logs", "")

            # Recuperar las evidencias estructuradas de pytest.
            artifact = _descargar_junit(str(run_id))

            if artifact["disponible"]:
                try:
                    payload["pytest"] = _interpretar_junit(artifact["xml"])
                except (ValueError, ET.ParseError) as exc:
                    payload["pytest"] = {
                        "disponible": False,
                        "motivo": f"No se pudo interpretar el XML: {exc}",
                    }
            else:
                payload["pytest"] = artifact

            return payload
        except Exception as exc:
            return {"run_id": str(run_id), "status": "error", "error": str(exc)}

    comando = [sys.executable, "-m", "pytest", "-q"]
    if ruta:
        comando.append(ruta)
    proceso = subprocess.run(comando, capture_output=True, text=True, timeout=180)
    salida = (proceso.stdout or "") + (proceso.stderr or "")
    return {
        "status": "passed" if proceso.returncode == 0 else "failed",
        "returncode": proceso.returncode,
        "ruta": ruta,
        "summary": salida.strip()[-4000:],
        "evidencia": salida.strip(),
    }


def version_plan(args: dict) -> dict:
    raise NotImplementedError("S4a: exponer version y parametros del plan")


IMPLEMENTACION = {
    "listar_specs": listar_specs,
    "obtener_spec": obtener_spec,
    "trazabilidad": trazabilidad,
    "resultado_tests": resultado_tests,
    "version_plan": version_plan,
}


# --- transporte JSON-RPC sobre stdio ------------------------------------------

def manejar(mensaje: dict):
    metodo = mensaje.get("method")
    ident = mensaje.get("id")

    if metodo == "tools/list":
        return _ok(ident, {"tools": HERRAMIENTAS})

    if metodo == "initialize":
        return _ok(ident, {
            "protocolVersion": PROTOCOLO,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "aula-contexto",
                "version": "1.0.0"
            }
        })

    if metodo == "tools/call":
        nombre = mensaje["params"]["name"]
        args = mensaje["params"].get("arguments", {})

        if nombre not in IMPLEMENTACION:
            return _error(
                ident,
                -32601,
                "herramienta desconocida: %s" % nombre
            )

        try:
            resultado = IMPLEMENTACION[nombre](args)
        except Exception as exc:
            return _ok(ident, {
                "content": [
                    {
                        "type": "text",
                        "text": "error: %s" % exc
                    }
                ],
                "isError": True
            })

        return _ok(ident, {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(
                        resultado,
                        ensure_ascii=False,
                        indent=2
                    )
                }
            ]
        })

    if metodo == "notifications/initialized":
        return None

    return _error(ident, -32601, "Método no soportado")

def _ok(ident, resultado):
    return {"jsonrpc": "2.0", "id": ident, "result": resultado}


def _error(ident, codigo, mensaje):
    return {"jsonrpc": "2.0", "id": ident, "error": {"code": codigo, "message": mensaje}}


def principal():
    """Bucle principal del servidor MCP."""
    for linea in sys.stdin:
        try:
            mensaje = json.loads(linea)
        except Exception as exc:
            sys.stderr.write("error parseando JSON: %s\n" % exc)
            continue

        respuesta = manejar(mensaje)
        if respuesta is not None:
            sys.stdout.write(json.dumps(respuesta, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    principal()
