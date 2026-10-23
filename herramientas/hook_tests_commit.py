"""Ejecuta la suite antes de permitir un commit desde Claude Code."""
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COMANDO_COMMIT = re.compile(
    r"\bgit\b(?:\s+-C\s+\S+)?\s+commit(?:\s|$)"
)


def main():
    try:
        entrada = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print("hook_tests_commit: entrada JSON invalida: %s" % error,
              file=sys.stderr)
        return 2
    entrada_herramienta = entrada.get("tool_input")
    if not isinstance(entrada_herramienta, dict):
        print("hook_tests_commit: falta tool_input en la entrada",
              file=sys.stderr)
        return 2
    comando = entrada_herramienta.get("command")
    if not isinstance(comando, str):
        print("hook_tests_commit: falta el comando de Bash", file=sys.stderr)
        return 2
    if not COMANDO_COMMIT.search(comando):
        return 0

    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=RAIZ,
        text=True,
        capture_output=True,
        check=False,
    )
    if resultado.stdout:
        print(resultado.stdout, end="")
    if resultado.stderr:
        print(resultado.stderr, end="", file=sys.stderr)
    if resultado.returncode:
        print("hook_tests_commit: tests fallidos; commit bloqueado",
              file=sys.stderr)
    return resultado.returncode


if __name__ == "__main__":
    sys.exit(main())
