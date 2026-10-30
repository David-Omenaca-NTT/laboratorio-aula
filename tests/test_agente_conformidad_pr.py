import json

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