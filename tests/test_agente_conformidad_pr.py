import json
import subprocess
import sys
from pathlib import Path

from agentes.conformidad.agente import principal


def test_agente_emite_veredicto_json_conforme(tmp_path, capsys):
    """cubre: SPEC-003/CA-01"""
    entrada = {
        "id": "pr-prueba",
        "criterios_declarados": ["CA-01"],
        "ficheros": [
            {
                "ruta": "tests/test_agente_conformidad_pr.py",
                "contenido": '"""cubre: SPEC-003/CA-01"""',
            }
        ],
    }
    ruta_entrada = tmp_path / "pr.json"
    ruta_entrada.write_text(json.dumps(entrada), encoding="utf-8")

    codigo = principal([
        "--pr", str(ruta_entrada),
        "--spec", "SPEC-003",
        "--json",
    ])

    resultado = json.loads(capsys.readouterr().out)
    assert codigo == 0
    assert resultado["veredicto"] == "conforme"
    assert resultado["criterios_cubiertos"] == ["CA-01"]


def test_script_conformidad_importa_agente_desde_otro_directorio(tmp_path):
    script = Path(__file__).resolve().parents[1] / "herramientas" / "conformidad_pr.py"
    resultado = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert resultado.returncode == 0