"""Hook de rutas prohibidas. Determinista, no negociable con el agente.

Lo innegociable no se pide en lenguaje natural: se hace determinista. Este hook
es lo que convierte la seccion de limites de CLAUDE.md en un control real.
"""
import json
import sys
from pathlib import Path


def ruta_prohibida(ruta):
    partes = Path(ruta.replace("\\", "/")).parts
    if "manifiestos" in partes:
        return True
    if "labs" in partes and partes[-1] == "verificar.py":
        return True
    if any(
        partes[i] == "evals" and i + 1 < len(partes)
        and partes[i + 1].startswith("dorado")
        for i in range(len(partes))
    ):
        return True
    return any(
        partes[i:i + len(secuencia)] == secuencia
        for secuencia in (
            (".github", "workflows"),
            ("src", "aula", "legado"),
        )
        for i in range(len(partes) - len(secuencia) + 1)
    )


def main():
    try:
        entrada = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print("hook_rutas: entrada JSON invalida: %s" % error, file=sys.stderr)
        return 2
    entrada_herramienta = entrada.get("tool_input")
    if not isinstance(entrada_herramienta, dict):
        print("hook_rutas: falta tool_input en la entrada", file=sys.stderr)
        return 2
    ruta = entrada_herramienta.get("file_path")
    if not isinstance(ruta, str) or not ruta:
        print("hook_rutas: falta una ruta de archivo valida", file=sys.stderr)
        return 2
    if ruta_prohibida(ruta):
        print("bloqueado por hook_rutas: %s esta en la lista de limites de "
              "CLAUDE.md. Requiere aprobacion humana explicita." % ruta,
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
