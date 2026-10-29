"""Agente v0: punto de partida deliberadamente ingenuo para S4a."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFORME = "conforme"
NO_CONFORME = "no_conforme"
ETIQUETA_COBERTURA = re.compile(
    r"\bcubre:\s*(?P<spec>SPEC-\d+)/(?P<criterio>(?:CA|INV)-\d+)\b"
)


@dataclass
class Veredicto:
    pr: str
    spec: str
    veredicto: str
    criterios_declarados: list = field(default_factory=list)
    criterios_cubiertos: list = field(default_factory=list)
    criterios_sin_cubrir: list = field(default_factory=list)
    fuera_de_alcance: list = field(default_factory=list)
    hallazgos: list = field(default_factory=list)
    explicacion: str = ""

    def a_dict(self):
        return asdict(self)


def comprobar_cobertura(pr: dict, spec_id: str) -> tuple[list, list]:
    """Compara los criterios declarados con las etiquetas de los tests."""
    criterios_declarados = pr.get("criterios_declarados", [])
    tests = [
        fichero for fichero in pr.get("ficheros", [])
        if fichero.get("ruta", "").startswith("tests/")
    ]
    criterios_cubiertos = []
    for criterio in criterios_declarados:
        referencia = f"{spec_id}/{criterio}"
        if any(
            referencia in {
                f"{coincidencia.group('spec')}/{coincidencia.group('criterio')}"
                for coincidencia in ETIQUETA_COBERTURA.finditer(
                    fichero.get("contenido", "")
                )
            }
            for fichero in tests
        ):
            criterios_cubiertos.append(criterio)
    criterios_sin_cubrir = [
        criterio for criterio in criterios_declarados
        if criterio not in criterios_cubiertos
    ]
    return criterios_cubiertos, criterios_sin_cubrir


def comprobar_alcance(pr: dict, spec_id: str) -> list:
    """Devuelve las rutas modificadas que no autoriza la especificación."""
    directorio_specs = Path(__file__).resolve().parents[2] / "specs"
    especificaciones = sorted(directorio_specs.glob(f"{spec_id}-*.md"))
    if not especificaciones:
        raise FileNotFoundError(f"No existe la especificación {spec_id}")
    contenido = especificaciones[0].read_text(encoding="utf-8")
    coincidencia = re.search(
        r"^## Fuera de alcance\s*$.*?^Rutas:\s*(.+)$",
        contenido,
        re.MULTILINE | re.DOTALL,
    )
    if coincidencia is None:
        raise ValueError(f"La especificación {spec_id} no declara rutas autorizadas")
    rutas_permitidas = {
        ruta.strip() for ruta in coincidencia.group(1).split(",") if ruta.strip()
    }
    return [
        fichero.get("ruta", "")
        for fichero in pr.get("ficheros", [])
        if fichero.get("ruta", "") not in rutas_permitidas
    ]


def detectar_riesgos(pr: dict) -> list:
    """Detecta patrones acotados que pueden invalidar un test declarado."""
    hallazgos = []
    for fichero in pr.get("ficheros", []):
        ruta = fichero.get("ruta", "")
        if not ruta.startswith("tests/"):
            continue
        contenido = fichero.get("contenido", "")
        if re.search(r"@pytest\.mark\.skip(?:\b|\()", contenido):
            hallazgos.append(f"{ruta}: test omitido con pytest.mark.skip")
        if re.search(r"^\s*assert\s+True\s*(?:#.*)?$", contenido, re.MULTILINE):
            hallazgos.append(f"{ruta}: aserción que siempre se cumple")
        if re.search(
            r"^\s*assert\s+(?P<expresion>[A-Za-z_]\w*)\s*==\s*(?P=expresion)\s*(?:#.*)?$",
            contenido,
            re.MULTILINE,
        ):
            hallazgos.append(f"{ruta}: aserción tautológica")
        if re.search(r"^\s*except\s*:\s*$.*?^\s*pass\s*(?:#.*)?$", contenido, re.MULTILINE | re.DOTALL):
            hallazgos.append(f"{ruta}: excepción silenciada con except: y pass")
    return hallazgos


def evaluar(pr: dict, spec_id: str, juez=None) -> Veredicto:
    """Produce un veredicto determinista mediante reglas sin decisión del modelo."""
    criterios_declarados = pr.get("criterios_declarados", [])
    criterios_cubiertos, criterios_sin_cubrir = comprobar_cobertura(pr, spec_id)
    fuera_de_alcance = comprobar_alcance(pr, spec_id)
    riesgos = detectar_riesgos(pr)
    conforme = (
        bool(criterios_declarados)
        and not criterios_sin_cubrir
        and not fuera_de_alcance
        and not riesgos
    )
    hallazgos = [
        f"No existe un test que cubra {spec_id}/{criterio}"
        for criterio in criterios_sin_cubrir
    ]
    hallazgos.extend(
        f"El fichero {ruta} está fuera de alcance"
        for ruta in fuera_de_alcance
    )
    hallazgos.extend(riesgos)
    resultado = CONFORME if conforme else NO_CONFORME
    return Veredicto(
        pr=pr.get("id", "sin-id"), spec=spec_id, veredicto=resultado,
        criterios_declarados=criterios_declarados,
        criterios_cubiertos=criterios_cubiertos,
        criterios_sin_cubrir=criterios_sin_cubrir,
        fuera_de_alcance=fuera_de_alcance,
        hallazgos=hallazgos,
        explicacion="todos los criterios están cubiertos y los cambios están en alcance"
        if conforme else "la PR no cumple la cobertura o el alcance autorizado")


def principal(argv=None):
    parser = argparse.ArgumentParser(description="Agente de conformidad v0")
    parser.add_argument("--pr", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    entrada = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    veredicto = evaluar(entrada, args.spec)
    if args.json:
        print(json.dumps(veredicto.a_dict(), ensure_ascii=False, indent=2))
    else:
        print(veredicto.veredicto + ": " + veredicto.explicacion)
    return 1 if veredicto.veredicto == NO_CONFORME else 0


if __name__ == "__main__":
    raise SystemExit(principal())
