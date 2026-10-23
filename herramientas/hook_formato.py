"""Hook de formato: normaliza el fichero editado. Silencioso si no hay nada que hacer."""
import json
import sys
from pathlib import Path


def main():
    try:
        entrada = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print("hook_formato: entrada JSON invalida: %s" % error, file=sys.stderr)
        return 2
    entrada_herramienta = entrada.get("tool_input")
    if not isinstance(entrada_herramienta, dict):
        print("hook_formato: falta tool_input en la entrada", file=sys.stderr)
        return 2
    ruta = entrada_herramienta.get("file_path")
    if not isinstance(ruta, str) or not ruta:
        print("hook_formato: falta una ruta de archivo valida", file=sys.stderr)
        return 2
    p = Path(ruta)
    if not p.exists() or p.suffix != ".py":
        return 0
    texto = p.read_text(encoding="utf-8")
    limpio = "\n".join(l.rstrip() for l in texto.splitlines())
    if not limpio.endswith("\n"):
        limpio += "\n"
    if limpio != texto:
        p.write_text(limpio, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
